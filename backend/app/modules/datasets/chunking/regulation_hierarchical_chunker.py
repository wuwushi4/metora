# -*- coding: utf-8 -*-
"""
階層式法規分塊器

以「條」為基本分塊單位，保留完整的法規階層結構（章/條/項/款），
並自動解析引用關係。

支援格式：
- JSON 格式的法規文件，符合 RegulationDocument Schema
"""
from typing import List, Dict, Any
import json
from loguru import logger

from .base import BaseChunker
from app.utils.schemas.regulation_schema import (
    RegulationDocument,
    validate_regulation_json
)
from app.utils.regulation_utils import (
    extract_hierarchy_path,
    build_reference_graph
)


class RegulationHierarchicalChunker(BaseChunker):
    """
    階層式法規分塊器

    分塊邏輯：
    - 以「條」為基本分塊單位
    - 每個分塊包含：
      - 完整條文內容（包含項和款）
      - 章節資訊
      - 引用關係
      - 階層路徑
    """

    def __init__(self, **kwargs):
        """初始化分塊器"""
        self.name = "regulation_hierarchical"
        self.description = "階層式法規分塊器，以條為單位，保留完整結構和引用關係"

    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        將法規 JSON 分塊

        Args:
            content: 法規 JSON 字串，符合 RegulationDocument Schema

        Returns:
            List[Dict[str, Any]]: 分塊列表，每個分塊包含：
                - content: 條文完整內容（含項款）
                - type: "regulation_article"
                - metadata: 條文的元數據

        Raises:
            ValueError: JSON 格式不正確或不符合 Schema
        """
        try:
            # 解析 JSON
            data = json.loads(content)
            regulation = validate_regulation_json(data)

            # 收集所有條號（用於引用解析）
            all_article_nums = []
            all_articles = []
            for chapter in regulation.chapters:
                for article in chapter.articles:
                    all_article_nums.append(article.article_num)
                    all_articles.append({
                        "article_num": article.article_num,
                        "content": article.content
                    })

            # 建立引用關係圖
            reference_graph = build_reference_graph(all_articles, all_article_nums)

            # 生成分塊
            chunks = []
            chunk_index = 0

            for chapter in regulation.chapters:
                for article in chapter.articles:
                    chunk = self._create_article_chunk(
                        regulation=regulation,
                        chapter=chapter,
                        article=article,
                        chunk_index=chunk_index,
                        reference_graph=reference_graph
                    )
                    chunks.append(chunk)
                    chunk_index += 1

            logger.info(
                f"[RegulationHierarchicalChunker] 成功分塊：{regulation.law_metadata.name}, "
                f"共 {len(chunks)} 個分塊（{regulation.count_chapters()} 章 {regulation.count_articles()} 條）"
            )

            return chunks

        except json.JSONDecodeError as e:
            logger.error(f"[RegulationHierarchicalChunker] JSON 解析失敗：{e}")
            raise ValueError(f"無效的 JSON 格式：{e}")
        except Exception as e:
            logger.error(f"[RegulationHierarchicalChunker] 分塊失敗：{e}")
            raise ValueError(f"分塊失敗：{e}")

    def _create_article_chunk(
        self,
        regulation: RegulationDocument,
        chapter: Any,
        article: Any,
        chunk_index: int,
        reference_graph: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        創建條文分塊

        Args:
            regulation: 法規文件
            chapter: 章節對象
            article: 條文對象
            chunk_index: 分塊索引
            reference_graph: 引用關係圖

        Returns:
            Dict[str, Any]: 條文分塊
        """
        # 組合條文內容
        content_parts = []

        # 標題部分：【章名】條號
        header = f"【{chapter.chapter_display} {chapter.chapter_name}】{article.article_display}"
        content_parts.append(header)
        content_parts.append("")  # 空行

        # 條文內容
        content_parts.append(article.content)

        # 項的內容
        if article.items:
            content_parts.append("")  # 空行
            for item in article.items:
                item_text = f"{item.item_display}、{item.content}"
                content_parts.append(item_text)

                # 款的內容
                if item.subitems:
                    for subitem in item.subitems:
                        subitem_text = f"  ({subitem.get('subitem_display', '')}) {subitem.get('content', '')}"
                        content_parts.append(subitem_text)

        # 引用關係
        refs = reference_graph.get(article.article_num, {})
        if refs.get("forward_refs") or refs.get("backward_refs"):
            content_parts.append("")  # 空行
            content_parts.append("[引用關係]")

            if refs.get("forward_refs"):
                ref_list = "、".join([f"第{num}條" for num in refs["forward_refs"]])
                content_parts.append(f"• 本條引用：{ref_list}")

            if refs.get("backward_refs"):
                ref_list = "、".join([f"第{num}條" for num in refs["backward_refs"]])
                content_parts.append(f"• 引用本條：{ref_list}")

        # 備註
        if article.note:
            content_parts.append("")
            content_parts.append(f"[備註] {article.note}")

        # 合併內容
        content = "\n".join(content_parts)

        # 階層路徑
        hierarchy_path = extract_hierarchy_path(
            chapter.chapter_num,
            chapter.chapter_name,
            article.article_num,
            use_chinese=False
        )

        # Metadata
        metadata = {
            # 法規資訊
            "law_name": regulation.law_metadata.name,
            "law_code": regulation.law_metadata.code,
            "law_category": regulation.law_metadata.category,

            # 章節資訊
            "chapter_num": chapter.chapter_num,
            "chapter_name": chapter.chapter_name,
            "chapter_display": chapter.chapter_display,

            # 條文資訊
            "article_num": article.article_num,
            "article_display": article.article_display,
            "has_items": len(article.items) > 0,
            "item_count": len(article.items),

            # 階層路徑
            "hierarchy_path": hierarchy_path,
            "full_path": f"{regulation.law_metadata.name}/{hierarchy_path}",

            # 引用關係
            "references_to": refs.get("forward_refs", []),
            "referenced_by": refs.get("backward_refs", []),
            "has_references": len(refs.get("forward_refs", [])) > 0 or len(refs.get("backward_refs", [])) > 0,

            # 分塊資訊
            "chunk_index": chunk_index,
            "representation": "full",
            "chunk_type": "regulation_article",

            # 來源資訊
            "source_url": regulation.law_metadata.source_url,
            "article_url": article.article_url if article.article_url else None,
            "last_updated": regulation.law_metadata.last_updated,
        }

        return {
            "content": content,
            "type": "regulation_article",
            "metadata": metadata
        }

    def validate(self, content: str) -> bool:
        """
        驗證內容是否為有效的法規 JSON

        Args:
            content: 待驗證的內容

        Returns:
            bool: 是否有效
        """
        try:
            # 嘗試解析 JSON
            data = json.loads(content)

            # 驗證 Schema
            validate_regulation_json(data)

            return True

        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.debug(f"[RegulationHierarchicalChunker] 驗證失敗：{e}")
            return False

    def get_strategy_name(self) -> str:
        """返回策略名稱"""
        return self.name

    def get_description(self) -> str:
        """返回策略描述"""
        return self.description

    def get_supported_formats(self) -> List[str]:
        """返回支援的格式"""
        return ["json"]

    def supported_file_types(self) -> List[str]:
        """法規階層式策略僅支援 JSON 格式"""
        return [".json"]

    def get_example_input(self) -> str:
        """返回範例輸入"""
        return """{
  "law_metadata": {
    "name": "長期照顧服務法",
    "code": "L0070040",
    "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0070040",
    "last_updated": "2024-01-01",
    "category": "衛生福利類",
    "status": "現行"
  },
  "chapters": [
    {
      "chapter_num": "1",
      "chapter_name": "總則",
      "chapter_display": "第一章",
      "articles": [
        {
          "article_num": "3",
          "article_display": "第3條",
          "content": "本法用詞，定義如下：",
          "items": [
            {
              "item_num": "1",
              "item_display": "一",
              "content": "長期照顧：指身心失能持續已達或預期達六個月以上...",
              "subitems": []
            }
          ],
          "references": null,
          "note": null
        }
      ]
    }
  ]
}"""
