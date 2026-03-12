# -*- coding: utf-8 -*-
"""
法規爬蟲模組

從全國法規資料庫爬取法規並轉換為 Markdown 格式

抽取自: backend/scripts/scrape_law_to_markdown.py
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from loguru import logger


class LawScraper:
    """全國法規資料庫爬蟲"""

    BASE_URL = "https://law.moj.gov.tw/LawClass/LawAll.aspx"
    ALLOWED_DOMAINS = ["law.moj.gov.tw"]
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB

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

        Raises:
            requests.RequestException: 網路請求錯誤
        """
        # 二次驗證 pcode 格式（安全措施）
        if not re.match(r'^[A-Z]\d{7}$', self.pcode):
            logger.error(f"無效的法規編號格式: {self.pcode}")
            return False

        try:
            logger.debug(f"正在獲取網頁：{self.BASE_URL}?pcode={self.pcode}")
            response = requests.get(
                self.BASE_URL,
                params={'pcode': self.pcode},
                timeout=30
            )

            # 檢查回應大小
            content_length = int(response.headers.get('content-length', 0))
            if content_length > self.MAX_RESPONSE_SIZE:
                logger.error(f"法規文件過大: {content_length} bytes")
                return False

            response.encoding = 'utf-8'
            response.raise_for_status()  # 拋出 HTTP 錯誤

            self.soup = BeautifulSoup(response.text, 'html.parser')
            logger.success("網頁獲取成功")
            return True

        except requests.RequestException as e:
            logger.error(f"無法獲取網頁：{e}")
            raise

    def extract_metadata(self) -> Dict[str, str]:
        """
        提取法規元數據

        Returns:
            包含 name 和 date 的字典
        """
        logger.debug("正在提取法規元數據...")
        metadata = {}

        # 法規名稱（優先使用 id 選擇器）
        law_name = None

        # 方法 1: 優先使用 id="hlLawName"（最精確）
        law_name_tag = self.soup.find('a', id='hlLawName')
        if law_name_tag and law_name_tag.text.strip():
            law_name = law_name_tag.text.strip()

        # 方法 2: 備用選擇器 - h1 > a
        if not law_name:
            h1_tag = self.soup.find('h1')
            if h1_tag:
                a_tag = h1_tag.find('a')
                if a_tag and a_tag.text.strip():
                    law_name = a_tag.text.strip()

        # 方法 3: 最後備用
        if not law_name:
            law_name_tag = (
                self.soup.find('span', class_='h1') or
                self.soup.find('a', string=lambda text: text and '法' in text)
            )
            if law_name_tag:
                law_name = law_name_tag.text.strip()

        if law_name:
            metadata['name'] = law_name
            logger.info(f"法規名稱：{metadata['name']}")
        else:
            metadata['name'] = "未知法規"
            logger.warning("無法提取法規名稱")

        # 修正日期（優先使用 id 選擇器）
        date_iso = None

        # 方法 1: 使用 id="trLNNDate" 精確定位
        date_row = self.soup.find('tr', id='trLNNDate')
        if date_row:
            date_td = date_row.find('td')
            if date_td:
                date_text = date_td.text.strip()
                # 解析民國日期並轉換為 ISO 格式
                date_iso = self._parse_roc_date(date_text)

        # 方法 2: 備用 - 文字搜尋
        if not date_iso:
            date_text_elem = self.soup.find(string=lambda text: text and '修正日期' in str(text))
            if date_text_elem:
                date_parent = date_text_elem.find_parent()
                if date_parent:
                    date_iso = self._parse_roc_date(date_parent.text.strip())

        metadata['date'] = date_iso or "未知"
        logger.debug(f"修正日期：{metadata['date']}")

        return metadata

    def parse_content(self) -> List[dict]:
        """
        解析法規內容

        Returns:
            包含章節和條文的列表
        """
        logger.debug("正在解析法規內容...")
        content = []

        # 找到法規內容容器（可能有多種 ID）
        law_container = (
            self.soup.find('div', id='pnLawFla') or
            self.soup.find('div', class_='law-reg-content') or
            self.soup.find('div', id='lawmenu')
        )

        if not law_container:
            logger.error("無法找到法規內容容器")
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
                    logger.debug(f"發現章節：{text}")

            # 識別條文
            elif 'row' in classes:
                article = self._parse_article(element, current_chapter)
                if article:
                    article_count += 1
                    content.append(article)

        logger.success(f"解析完成：{chapter_count} 章，{article_count} 條")
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

    def _parse_roc_date(self, date_text: str) -> Optional[str]:
        """
        解析民國日期並轉換為 ISO 格式

        Args:
            date_text: 民國日期文字，例如 "民國 110 年 05 月 19 日" 或 "修正日期：民國 110 年 05 月 19 日"

        Returns:
            ISO 格式日期字串（例如 "2021-05-19"），解析失敗則返回 None
        """
        try:
            # 使用正則表達式提取民國年、月、日
            # 匹配格式：民國 110 年 05 月 19 日 或 民國110年5月19日
            pattern = r'民國\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日'
            match = re.search(pattern, date_text)

            if match:
                roc_year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))

                # 民國年轉西元年：民國年 + 1911
                ad_year = roc_year + 1911

                # 格式化為 ISO 日期（YYYY-MM-DD）
                iso_date = f"{ad_year:04d}-{month:02d}-{day:02d}"
                logger.debug(f"日期轉換成功：{date_text} → {iso_date}")
                return iso_date
            else:
                logger.warning(f"無法解析民國日期格式：{date_text}")
                return None

        except (ValueError, AttributeError) as e:
            logger.error(f"日期解析錯誤：{e}")
            return None

    def to_markdown(self, content: List[dict], metadata: Dict[str, str]) -> str:
        """
        轉換為 Markdown 格式

        Args:
            content: 解析後的內容列表
            metadata: 法規元數據

        Returns:
            Markdown 格式的字串
        """
        logger.debug("正在轉換為 Markdown 格式...")
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

        logger.success("Markdown 轉換完成")
        return "\n".join(lines)

    def scrape(self) -> Tuple[str, Dict[str, str]]:
        """
        執行完整爬取流程（不儲存檔案）

        Returns:
            (markdown_content, metadata)

        Raises:
            Exception: 爬取失敗時
        """
        if not self.fetch():
            raise Exception("無法獲取網頁")

        metadata = self.extract_metadata()
        content = self.parse_content()

        if not content:
            raise Exception("無法解析任何內容")

        markdown = self.to_markdown(content, metadata)
        return markdown, metadata
