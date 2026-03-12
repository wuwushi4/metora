# -*- coding: utf-8 -*-
"""
手動情境法規分塊器

基於人工定義的情境描述（scenarios），為每條法規創建多重表徵分塊：
1. 原始條文分塊（完整內容）
2. N 個情境描述分塊（每個 scenario 獨立）

這種策略相比 LLM 自動生成更可控，適合核心條文的精準檢索。
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


class RegulationManualScenarioChunker(BaseChunker):
    """
    手動情境法規分塊器

    分塊邏輯：
    - 以「條」為基本分塊單位
    - 每條法規生成 1 + N 個分塊：
      1. 原始條文分塊（與階層式相同）
      2. N 個情境描述分塊（每個 scenario 獨立）

    優勢：
    - 人工可控，品質穩定
    - 針對核心條文可精心設計多種情境
    - 情境描述與原始條文獨立檢索，互不干擾
    """

    def __init__(self, **kwargs):
        """初始化分塊器"""
        self.name = "regulation_manual_scenario"
        self.description = "手動情境法規分塊器，基於人工定義的情境描述，支援多重表徵檢索"

    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        將法規 JSON 分塊（含手動情境）

        Args:
            content: 法規 JSON 字串，符合 RegulationDocument Schema

        Returns:
            List[Dict[str, Any]]: 分塊列表，包含原始條文分塊和情境描述分塊

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

                    # 準備傳遞給 build_reference_graph 的條文數據
                    article_data = {
                        "article_num": article.article_num,
                        "content": article.content
                    }

                    # 如果有 references 欄位，一併傳遞（優先使用 JSON 中的引用數據）
                    if hasattr(article, 'references') and article.references:
                        # 將 Pydantic 對象轉換為字典
                        article_data["references"] = {
                            "raw_text": article.references.raw_text,
                            "resolved": article.references.resolved,
                            "forward_refs": article.references.forward_refs,
                            "backward_refs": article.references.backward_refs
                        }

                    all_articles.append(article_data)

            # 建立引用關係圖
            reference_graph = build_reference_graph(all_articles, all_article_nums)

            # 生成分塊
            chunks = []
            chunk_index = 0

            for chapter in regulation.chapters:
                for article in chapter.articles:
                    # 1. 創建原始條文分塊
                    original_chunk = self._create_article_chunk(
                        regulation=regulation,
                        chapter=chapter,
                        article=article,
                        chunk_index=chunk_index,
                        reference_graph=reference_graph
                    )
                    chunks.append(original_chunk)
                    chunk_index += 1

                    # 2. 創建情境描述分塊（如果有定義 scenarios）
                    if article.scenarios:
                        for scenario_idx, scenario_text in enumerate(article.scenarios):
                            scenario_chunk = self._create_scenario_chunk(
                                regulation=regulation,
                                chapter=chapter,
                                article=article,
                                scenario_text=scenario_text,
                                scenario_index=scenario_idx,
                                chunk_index=chunk_index,
                                reference_graph=reference_graph
                            )
                            chunks.append(scenario_chunk)
                            chunk_index += 1

            # 統計
            original_count = regulation.count_articles()
            scenario_count = chunk_index - original_count

            logger.debug(
                f"[RegulationManualScenarioChunker] 成功分塊：{regulation.law_metadata.name}, "
                f"原始分塊 {original_count} 個，情境分塊 {scenario_count} 個，"
                f"總計 {len(chunks)} 個"
            )

            return chunks

        except json.JSONDecodeError as e:
            logger.error(f"[RegulationManualScenarioChunker] JSON 解析失敗：{e}")
            raise ValueError(f"無效的 JSON 格式：{e}")
        except Exception as e:
            logger.error(f"[RegulationManualScenarioChunker] 分塊失敗：{e}")
            raise

    def _create_article_chunk(
        self,
        regulation: RegulationDocument,
        chapter: Any,
        article: Any,
        chunk_index: int,
        reference_graph: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        創建原始條文分塊（與階層式分塊器邏輯相同）

        Args:
            regulation: 法規文件
            chapter: 章節對象
            article: 條文對象
            chunk_index: 分塊索引
            reference_graph: 引用關係圖

        Returns:
            Dict[str, Any]: 原始條文分塊
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
            "representation": "full",  # 原始條文
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

    def _create_scenario_chunk(
        self,
        regulation: RegulationDocument,
        chapter: Any,
        article: Any,
        scenario_text: str,
        scenario_index: int,
        chunk_index: int,
        reference_graph: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        創建情境描述分塊

        Args:
            regulation: 法規文件
            chapter: 章節對象
            article: 條文對象
            scenario_text: 情境描述文字
            scenario_index: 情境索引（第幾個 scenario）
            chunk_index: 分塊索引
            reference_graph: 引用關係圖

        Returns:
            Dict[str, Any]: 情境描述分塊
        """
        # 組合內容：情境描述 + 關聯條文資訊
        content_parts = []
        content_parts.append(f"【適用情境】{article.article_display}")
        content_parts.append("")
        content_parts.append(scenario_text)
        content_parts.append("")
        content_parts.append(f"→ 相關法條：{regulation.law_metadata.name} {article.article_display}")

        content = "\n".join(content_parts)

        # 階層路徑
        hierarchy_path = extract_hierarchy_path(
            chapter.chapter_num,
            chapter.chapter_name,
            article.article_num,
            use_chinese=False
        )

        # 引用關係
        refs = reference_graph.get(article.article_num, {})

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

            # 階層路徑
            "hierarchy_path": hierarchy_path,
            "full_path": f"{regulation.law_metadata.name}/{hierarchy_path}",

            # 引用關係
            "references_to": refs.get("forward_refs", []),
            "referenced_by": refs.get("backward_refs", []),
            "has_references": len(refs.get("forward_refs", [])) > 0 or len(refs.get("backward_refs", [])) > 0,

            # 分塊資訊
            "chunk_index": chunk_index,
            "representation": f"scenario_{scenario_index}",  # 情境表徵
            "chunk_type": "regulation_scenario",
            "scenario_text": scenario_text,  # 保存原始情境文字
            "linked_article": article.article_num,  # 關聯到原始條文

            # 來源資訊
            "source_url": regulation.law_metadata.source_url,
            "article_url": article.article_url if article.article_url else None,
            "last_updated": regulation.law_metadata.last_updated,
        }

        return {
            "content": content,
            "vectorization_text": scenario_text,  # 純情境文字（供向量編碼）
            "type": "regulation_scenario",
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
            data = json.loads(content)
            validate_regulation_json(data)
            return True
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.debug(f"[RegulationManualScenarioChunker] 驗證失敗：{e}")
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
        """手動情境法規策略僅支援 JSON 格式"""
        return [".json"]

    def get_example_input(self) -> str:
        """返回範例輸入"""
        return """{
  "law_metadata": {
    "name": "動物保護法",
    "code": "D0040027",
    "source_url": "https://law.moj.gov.tw/...",
    "last_updated": "2025-01-10",
    "category": "其他",
    "status": "現行"
  },
  "chapters": [
    {
      "chapter_num": "2",
      "chapter_name": "動物之一般保護",
      "chapter_display": "第二章",
      "articles": [
        {
          "article_num": "6",
          "article_display": "第6條",
          "content": "任何人不得騷擾、虐待或傷害動物。",
          "items": [],
          "references": null,
          "note": null,
          "scenarios": [
            "有人用棍子、石頭等物品毆打路邊的流浪貓狗",
            "看到有人踢打、拖行、摔打寵物或動物",
            "發現有人用刀具、電擊棒等工具傷害動物"
          ]
        }
      ]
    }
  ]
}"""
