# -*- coding: utf-8 -*-
"""
Markdown 轉法規 JSON 轉換器

將 Markdown 格式的法規文件轉換為符合 RegulationDocument Schema 的 JSON 格式

抽取自: backend/scripts/convert_md_to_regulation_json.py
"""
import re
from typing import Dict, Any, Optional
from loguru import logger


class MarkdownToRegulationConverter:
    """Markdown 轉法規 JSON 轉換器"""

    def __init__(self, law_name: str, law_code: str,
                 last_updated: Optional[str] = None,
                 source_url: Optional[str] = None):
        """
        初始化轉換器

        Args:
            law_name: 法規名稱
            law_code: 法規編號
            last_updated: 法規最後修正日期（ISO 格式，例如 "2021-05-19"）
            source_url: 來源網址
        """
        self.law_name = law_name
        self.law_code = law_code
        self.last_updated = last_updated or "未知"
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
                "last_updated": self.last_updated,
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
                # ✅ FIX BUG 1: 處理 pending_content（在保存條文之前）
                if pending_content is not None and current_article:
                    current_article['content'] = pending_content
                    pending_content = None

                # 保存上一個條到上一個章
                if current_article and current_chapter:
                    current_chapter['articles'].append(current_article)
                    current_article = None
                # 保存上一個章到結果
                if current_chapter:
                    result['chapters'].append(current_chapter)

                # ✅ FIX BUG 2: 解析新的章（支援 "第 X 章之一" 格式）
                chapter_match = re.match(r'^## 第\s+(.+?)\s+章(?:之.+?)?\s+(.+)$', line)
                if chapter_match:
                    chapter_display_raw = chapter_match.group(1).strip()
                    chapter_name = chapter_match.group(2).strip()

                    # 提取純數字部分用於主章節編號
                    chapter_num_match = re.match(r'^([一二三四五六七八九十百千]+)', chapter_display_raw)
                    if chapter_num_match:
                        chapter_num_chinese = chapter_num_match.group(1)
                        chapter_num = self._chinese_to_arabic(chapter_num_chinese)
                    else:
                        chapter_num_chinese = chapter_display_raw
                        chapter_num = 1  # 備用值

                    # 檢查是否有 "之X" 後綴（如 "第 四 章之一" → "4-1"）
                    suffix_match = re.search(r'章(之.+?)\s', line)
                    if suffix_match:
                        suffix = suffix_match.group(1)  # "之一"
                        # 提取後綴中的數字部分
                        suffix_num_match = re.match(r'^之([一二三四五六七八九十百千]+)', suffix)
                        if suffix_num_match:
                            suffix_num_chinese = suffix_num_match.group(1)
                            suffix_num = self._chinese_to_arabic(suffix_num_chinese)
                            chapter_num = f"{chapter_num}-{suffix_num}"
                        else:
                            chapter_num = str(chapter_num)
                    else:
                        chapter_num = str(chapter_num)

                    # 提取完整的章節顯示（包含 "之一" 等後綴）
                    full_line_match = re.match(r'^## (第.+?章(?:之.+?)?)\s+.+$', line)
                    if full_line_match:
                        chapter_display = full_line_match.group(1)
                    else:
                        chapter_display = f"第{chapter_display_raw}章"

                    current_chapter = {
                        "chapter_num": str(chapter_num),
                        "chapter_name": chapter_name,
                        "chapter_display": chapter_display,
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
