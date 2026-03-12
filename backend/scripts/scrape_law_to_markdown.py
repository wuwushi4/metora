# -*- coding: utf-8 -*-
"""
全國法規資料庫爬蟲

從全國法規資料庫爬取法規並轉換為 Markdown 格式

使用方法：
    python scripts/scrape_law_to_markdown.py \
        --pcode M0060027 \
        --output data/regulations/Act_on_Wildlife_Conservation_scraped.md
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import argparse
from pathlib import Path


class LawScraper:
    """全國法規資料庫爬蟲"""

    BASE_URL = "https://law.moj.gov.tw/LawClass/LawAll.aspx"

    def __init__(self, pcode: str):
        """
        初始化爬蟲

        Args:
            pcode: 法規編號（例如：M0060027）
        """
        self.pcode = pcode
        self.soup = None

    def fetch(self) -> bool:
        """
        獲取網頁內容

        Returns:
            是否成功獲取
        """
        try:
            print(f"[1/5] 正在獲取網頁：{self.BASE_URL}?pcode={self.pcode}")
            response = requests.get(self.BASE_URL, params={'pcode': self.pcode}, timeout=30)
            response.encoding = 'utf-8'
            self.soup = BeautifulSoup(response.text, 'html.parser')
            print("[OK] 網頁獲取成功")
            return True
        except requests.RequestException as e:
            print(f"[錯誤] 無法獲取網頁：{e}")
            return False

    def extract_metadata(self) -> Dict[str, str]:
        """
        提取法規元數據

        Returns:
            包含 name 和 date 的字典
        """
        print("[2/5] 正在提取法規元數據...")
        metadata = {}

        # 法規名稱（多種可能的選擇器）
        law_name = (
            self.soup.find('span', class_='h1') or
            self.soup.find('h1') or
            self.soup.find('a', string=lambda text: text and '法' in text)
        )

        if law_name:
            metadata['name'] = law_name.text.strip()
            print(f"   - 法規名稱：{metadata['name']}")
        else:
            metadata['name'] = "未知法規"
            print("   - [警告] 無法提取法規名稱")

        # 修正日期（嘗試多種方式）
        date_text = self.soup.find(string=lambda text: text and '修正日期' in str(text))
        if date_text:
            # 從包含「修正日期」的文本中提取
            date_parent = date_text.find_parent()
            if date_parent:
                metadata['date'] = date_parent.text.strip()
        else:
            metadata['date'] = "未知"

        print(f"   - 修正日期：{metadata.get('date', '未知')}")
        print("[OK] 元數據提取完成")

        return metadata

    def parse_content(self) -> List[dict]:
        """
        解析法規內容

        Returns:
            包含章節和條文的列表
        """
        print("[3/5] 正在解析法規內容...")
        content = []

        # 找到法規內容容器（可能有多種 ID）
        law_container = (
            self.soup.find('div', id='pnLawFla') or
            self.soup.find('div', class_='law-reg-content') or
            self.soup.find('div', id='lawmenu')
        )

        if not law_container:
            print("[錯誤] 無法找到法規內容容器")
            return content

        current_chapter = None
        article_count = 0
        chapter_count = 0

        # 遍歷所有元素
        for element in law_container.find_all(['div'], recursive=True):
            classes = element.get('class', [])

            # 識別章節
            if 'h3' in classes or ('char-2' in classes and element.name == 'div'):
                text = element.text.strip()
                # 確認是章節格式（第 X 章）
                if '第' in text and '章' in text:
                    current_chapter = text
                    chapter_count += 1
                    content.append({
                        'type': 'chapter',
                        'text': text
                    })
                    print(f"   - 發現章節：{text}")

            # 識別條文
            elif 'row' in classes:
                article = self._parse_article(element, current_chapter)
                if article:
                    article_count += 1
                    content.append(article)

        print(f"[OK] 解析完成：{chapter_count} 章，{article_count} 條")
        return content

    def _parse_article(self, row_element, chapter: Optional[str]) -> Optional[Dict]:
        """
        解析單一條文

        Args:
            row_element: 條文的 row div 元素
            chapter: 當前章節名稱

        Returns:
            條文字典，包含 type、chapter、number、paragraphs
        """
        # 提取條號
        col_no = row_element.find('div', class_='col-no')
        if not col_no:
            return None

        article_link = col_no.find('a')
        if not article_link:
            return None

        article_num = article_link.text.strip()

        # 提取條文內容
        col_data = row_element.find('div', class_='col-data')
        if not col_data:
            return None

        law_article = col_data.find('div', class_='law-article')
        if not law_article:
            return None

        # 解析項和款
        paragraphs = []
        current_paragraph = None

        for div in law_article.find_all('div', recursive=False):
            classes = div.get('class', [])
            text = div.text.strip()

            if not text:  # 跳過空內容
                continue

            # 判斷是項（line-0000）還是款（line-0004, line-0006）
            if 'line-0000' in classes:
                # 這是項
                has_number = 'show-number' in classes
                current_paragraph = {
                    'text': text,
                    'numbered': has_number,
                    'subparagraphs': []
                }
                paragraphs.append(current_paragraph)

            elif 'line-0004' in classes or 'line-0006' in classes:
                # 這是款
                if current_paragraph is None:
                    # 款直接在條下（如第 3 條），創建虛擬項
                    current_paragraph = {
                        'text': '',
                        'numbered': False,
                        'subparagraphs': []
                    }
                    paragraphs.append(current_paragraph)

                current_paragraph['subparagraphs'].append(text)

        return {
            'type': 'article',
            'chapter': chapter,
            'number': article_num,
            'paragraphs': paragraphs
        }

    def to_markdown(self, content: List[dict], metadata: Dict[str, str]) -> str:
        """
        轉換為 Markdown 格式

        Args:
            content: 解析後的內容列表
            metadata: 法規元數據

        Returns:
            Markdown 格式的字串
        """
        print("[4/5] 正在轉換為 Markdown 格式...")
        lines = []

        # 法規標題
        lines.append(f"# {metadata.get('name', '')}")
        lines.append("")

        for item in content:
            if item['type'] == 'chapter':
                # 章節
                lines.append(f"## {item['text']}")
                lines.append("")

            elif item['type'] == 'article':
                # 條號
                lines.append(f"### {item['number']}")

                # 項和款
                para_counter = 1
                for para in item['paragraphs']:
                    # 項的內容
                    if para['text']:
                        if para['numbered']:
                            # 需要編號的項
                            lines.append(f"##### {para_counter}. {para['text']}")
                            para_counter += 1
                        else:
                            # 不編號的項（前言）
                            lines.append(f"##### {para['text']}")

                    # 款
                    for sub in para['subparagraphs']:
                        lines.append(f"###### {sub}")

                lines.append("")

        print("[OK] Markdown 轉換完成")
        return "\n".join(lines)

    def save(self, output_path: str) -> bool:
        """
        執行完整爬取流程並保存

        Args:
            output_path: 輸出檔案路徑

        Returns:
            是否成功
        """
        # 1. 獲取網頁
        if not self.fetch():
            return False

        # 2. 提取元數據
        metadata = self.extract_metadata()

        # 3. 解析內容
        content = self.parse_content()

        if not content:
            print("[錯誤] 無法解析任何內容")
            return False

        # 4. 轉換為 Markdown
        markdown = self.to_markdown(content, metadata)

        # 5. 保存檔案
        try:
            print(f"[5/5] 正在儲存至：{output_path}")
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)

            print(f"[完成] 已成功儲存至：{output_path}")
            print(f"\n統計資訊：")
            print(f"   - 總行數：{len(markdown.splitlines())}")
            print(f"   - 檔案大小：{len(markdown.encode('utf-8'))} bytes")

            return True

        except Exception as e:
            print(f"[錯誤] 儲存失敗：{e}")
            return False


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='從全國法規資料庫爬取法規並轉換為 Markdown')
    parser.add_argument('--pcode', required=True, help='法規編號（例如：M0060027）')
    parser.add_argument('--output', required=True, help='輸出 Markdown 檔案路徑')

    args = parser.parse_args()

    # 創建爬蟲並執行
    scraper = LawScraper(args.pcode)
    success = scraper.save(args.output)

    if not success:
        print("\n[失敗] 爬取過程中發生錯誤")
        exit(1)

    print("\n[成功] 爬取完成！")


if __name__ == "__main__":
    main()
