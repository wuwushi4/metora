# -*- coding: utf-8 -*-
"""
Markdown 轉 法規 JSON 轉換器 (重寫版本)

將 Markdown 格式的法規文件轉換為符合 RegulationDocument Schema 的 JSON 格式

使用方法：
    python scripts/convert_md_to_regulation_json.py \
        --input data/regulations/Act_on_Wildlife_Conservation.md \
        --output data/regulations/animal_protection_law.json \
        --name "動物保護法" \
        --code "M0060027"
"""
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


class MarkdownToRegulationConverter:
    """Markdown 轉法規 JSON 轉換器 (重寫版本)"""

    def __init__(self, law_name: str, law_code: str, source_url: Optional[str] = None):
        """
        初始化轉換器

        Args:
            law_name: 法規名稱
            law_code: 法規編號
            source_url: 來源網址
        """
        self.law_name = law_name
        self.law_code = law_code
        self.source_url = source_url or f"https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={law_code}"

    def convert(self, markdown_content: str) -> Dict[str, Any]:
        """
        轉換 Markdown 為法規 JSON

        Args:
            markdown_content: Markdown 內容

        Returns:
            符合 RegulationDocument Schema 的字典
        """
        lines = markdown_content.split('\n')

        # 初始化結果結構
        result = {
            "law_metadata": {
                "name": self.law_name,
                "code": self.law_code,
                "source_url": self.source_url,
                "last_updated": "2025-01-10",
                "category": "其他",
                "status": "現行"
            },
            "chapters": []
        }

        # 狀態變數
        current_chapter = None
        current_article = None
        current_item = None
        pending_content = None  # 用於暫存可能是引言的內容

        for line in lines:
            line = line.rstrip()

            # 跳過空行和第一層標題（法規名稱）
            if not line or (line.startswith('# ') and not line.startswith('## ')):
                continue

            # ==================== 章：## 第 X 章 章名 ====================
            if line.startswith('## 第'):
                # 保存上一個條到上一個章
                if current_article and current_chapter:
                    current_chapter['articles'].append(current_article)
                    current_article = None
                # 保存上一個章到結果
                if current_chapter:
                    result['chapters'].append(current_chapter)

                # 解析新的章
                chapter_match = re.match(r'^## 第\s+([一二三四五六七八九十百千]+)\s+章\s+(.+)$', line)
                if chapter_match:
                    chapter_num_chinese = chapter_match.group(1).strip()
                    chapter_name = chapter_match.group(2).strip()
                    chapter_num = self._chinese_to_arabic(chapter_num_chinese)

                    current_chapter = {
                        "chapter_num": str(chapter_num),
                        "chapter_name": chapter_name,
                        "chapter_display": f"第{chapter_num_chinese}章",
                        "articles": []
                    }
                    current_article = None
                    current_item = None
                    pending_content = None

            # ==================== 條：### 第 X 條 ====================
            elif line.startswith('### 第'):
                # 處理上一個條的 pending_content
                if pending_content is not None and current_article:
                    current_article['content'] = pending_content
                    pending_content = None

                # 保存上一個條
                if current_article and current_chapter:
                    current_chapter['articles'].append(current_article)

                # 解析新的條（支援帶連字號，如 4-1）
                article_match = re.match(r'^### 第\s+(\d+(?:-\d+)?)\s+條$', line)
                if article_match:
                    article_num = article_match.group(1)

                    current_article = {
                        "article_num": article_num,
                        "article_display": f"第{article_num}條",
                        "content": "",
                        "items": [],
                        "references": {
                            "raw_text": [],
                            "resolved": [],
                            "forward_refs": [],
                            "backward_refs": []
                        },
                        "note": None,
                        "scenarios": [],
                        "article_url": f"https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode={self.law_code}&flno={article_num}"
                    }
                    current_item = None
                    pending_content = None

            # ==================== 款：###### 中文數字、內容 ====================
            elif line.startswith('######'):
                content = line.lstrip('#').strip()

                # 解析款（格式：一、內容）
                subitem_match = re.match(r'^([一二三四五六七八九十百千]+)、\s*(.+)$', content)

                if subitem_match and current_article:
                    # 如果有 pending_content，先將其設為 article.content
                    if pending_content is not None:
                        current_article['content'] = pending_content
                        pending_content = None

                    subitem_display = subitem_match.group(1)
                    subitem_content = subitem_match.group(2)
                    subitem_num = str(self._chinese_to_arabic(subitem_display))

                    subitem = {
                        "subitem_num": subitem_num,
                        "subitem_display": subitem_display,
                        "content": subitem_content
                    }

                    if current_item:
                        # 情況 1: 款在項下（第 5 條）
                        current_item['subitems'].append(subitem)
                    else:
                        # 情況 2: 款直接在條下（第 3 條）
                        # 將款包裝成 item
                        item_wrapper = {
                            "item_num": subitem_num,
                            "item_display": subitem_display,
                            "content": subitem_content,
                            "subitems": []
                        }
                        current_article['items'].append(item_wrapper)

            # ==================== 項：##### 數字. 內容 或 ##### 內容 ====================
            elif line.startswith('#####'):
                content = line.lstrip('#').strip()

                # 判斷是否為項（格式：1. 內容）
                item_match = re.match(r'^(\d+)\.\s+(.+)$', content)

                if item_match and current_article:
                    # 有項號 → 創建項
                    if pending_content is not None:
                        # 之前的 pending_content 確定不是引言，而是獨立的條文內容
                        current_article['content'] = pending_content
                        pending_content = None

                    item_num = item_match.group(1)
                    item_content = item_match.group(2)

                    current_item = {
                        "item_num": item_num,
                        "item_display": self._arabic_to_chinese(int(item_num)),
                        "content": item_content,
                        "subitems": []
                    }
                    current_article['items'].append(current_item)

                elif current_article:
                    # 無項號 → 可能是條文內容或引言
                    # 暫存到 pending_content，等待下一行判斷
                    if pending_content is None:
                        pending_content = content
                    else:
                        # 如果已有 pending_content，說明有多段內容，需要合併
                        if current_article['content']:
                            current_article['content'] += '\n' + pending_content + '\n' + content
                        else:
                            current_article['content'] = pending_content + '\n' + content
                        pending_content = None

        # ==================== 收尾處理 ====================
        # 處理最後的 pending_content
        if pending_content is not None and current_article:
            current_article['content'] = pending_content

        # 保存最後一個條和章
        if current_article and current_chapter:
            current_chapter['articles'].append(current_article)
        if current_chapter:
            result['chapters'].append(current_chapter)

        return result

    def _chinese_to_arabic(self, chinese_num: str) -> int:
        """
        將中文數字轉換為阿拉伯數字（修正版）

        Args:
            chinese_num: 中文數字，如 "一", "十", "十一", "二十三"

        Returns:
            阿拉伯數字
        """
        chinese_numbers = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
            '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '十': 10, '百': 100, '千': 1000
        }

        # 特殊情況：單個字
        if len(chinese_num) == 1:
            return chinese_numbers.get(chinese_num, 1)

        # 從左到右處理（改用正向處理）
        result = 0
        temp_num = 0

        for char in chinese_num:
            if char not in chinese_numbers:
                continue

            value = chinese_numbers[char]

            if value >= 10:  # 十、百、千
                if temp_num == 0:
                    temp_num = 1  # 處理「十」開頭的情況（如「十一」）
                result += temp_num * value
                temp_num = 0
            else:  # 0-9
                temp_num = temp_num * 10 + value

        # 加上最後的個位數
        result += temp_num

        return result if result > 0 else 1

    def _arabic_to_chinese(self, num: int) -> str:
        """
        將阿拉伯數字轉換為中文數字（用於項號、款號顯示）

        Args:
            num: 阿拉伯數字

        Returns:
            中文數字
        """
        if num <= 0:
            return "零"
        elif num <= 10:
            return ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][num]
        elif num < 20:
            ones = num - 10
            if ones == 0:
                return '十'
            return '十' + ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'][ones]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            tens_char = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'][tens]
            if ones == 0:
                return tens_char + '十'
            else:
                ones_char = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'][ones]
                return tens_char + '十' + ones_char
        else:
            # 100 以上直接返回阿拉伯數字
            return str(num)


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='將 Markdown 格式的法規轉換為 JSON')
    parser.add_argument('--input', required=True, help='輸入 Markdown 檔案路徑')
    parser.add_argument('--output', required=True, help='輸出 JSON 檔案路徑')
    parser.add_argument('--name', required=True, help='法規名稱')
    parser.add_argument('--code', required=True, help='法規編號')
    parser.add_argument('--source-url', help='來源網址')

    args = parser.parse_args()

    # 讀取 Markdown 檔案
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[錯誤] 檔案不存在：{input_path}")
        return

    print(f"[1/4] 讀取 Markdown 檔案：{input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 轉換
    print(f"[2/4] 開始轉換...")
    converter = MarkdownToRegulationConverter(
        law_name=args.name,
        law_code=args.code,
        source_url=args.source_url
    )
    result = converter.convert(markdown_content)

    # 統計資訊
    chapter_count = len(result['chapters'])
    article_count = sum(len(chapter['articles']) for chapter in result['chapters'])
    item_count = sum(
        len(article['items'])
        for chapter in result['chapters']
        for article in chapter['articles']
    )
    subitem_count = sum(
        len(item['subitems'])
        for chapter in result['chapters']
        for article in chapter['articles']
        for item in article['items']
    )

    print(f"[OK] 轉換完成")
    print(f"   - 法規名稱：{result['law_metadata']['name']}")
    print(f"   - 章數：{chapter_count}")
    print(f"   - 條數：{article_count}")
    print(f"   - 項數：{item_count}")
    print(f"   - 款數：{subitem_count}")

    # 儲存 JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[3/4] 儲存 JSON...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已儲存至：{output_path}")

    # 提取測試條文進行驗證
    print(f"\n[4/4] 提取測試條文（第 1, 3, 4-1, 5 條）...")
    test_articles = {}
    for chapter in result['chapters']:
        for article in chapter['articles']:
            if article['article_num'] in ['1', '3', '4-1', '5']:
                test_articles[article['article_num']] = article

    # 輸出測試條文的簡化結構
    for article_num in ['1', '3', '4-1', '5']:
        if article_num in test_articles:
            article = test_articles[article_num]
            print(f"\n第 {article_num} 條:")
            print(f"  - content 長度: {len(article['content'])}")
            print(f"  - items 數量: {len(article['items'])}")
            if article['items']:
                for idx, item in enumerate(article['items'][:3]):  # 只顯示前 3 項
                    print(f"    - 項 {item['item_num']} ({item['item_display']}): subitems={len(item['subitems'])}")
                if len(article['items']) > 3:
                    print(f"    - ... 還有 {len(article['items']) - 3} 項")

    print(f"\n[完成] 您現在可以使用前端的 Collection 管理功能上傳此 JSON 檔案。")


if __name__ == '__main__':
    main()
