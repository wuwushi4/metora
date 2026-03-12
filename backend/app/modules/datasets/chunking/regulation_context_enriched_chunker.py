# -*- coding: utf-8 -*-
"""
情境增強法規分塊器

在階層式法規分塊器的基礎上，使用 LLM 為每條法規生成情境描述，
創建雙重表徵（原始條文 + 情境描述）以提升檢索召回率。
"""
from typing import List, Dict, Any
import json
from loguru import logger

from .regulation_hierarchical_chunker import RegulationHierarchicalChunker
from app.utils.schemas.regulation_schema import (
    RegulationDocument,
    validate_regulation_json
)
from app.utils.context_generator import ContextGenerator
from app.core.resource_manager import get_resource_manager


class RegulationContextEnrichedChunker(RegulationHierarchicalChunker):
    """
    情境增強法規分塊器

    分塊邏輯：
    - 繼承階層式分塊器的功能
    - 為每條法規生成 2 個分塊：
      1. 原始條文分塊（與階層式相同）
      2. LLM 生成的情境描述分塊

    雙重表徵的優勢：
    - 原始條文：保留完整法規內容，適合精確匹配
    - 情境描述：自然語言描述，適合情境化查詢
    """

    def __init__(self, **kwargs):
        """初始化分塊器"""
        super().__init__()
        self.name = "regulation_context_enriched"
        self.description = "情境增強法規分塊器，使用 LLM 生成情境描述，支援雙重表徵檢索"
        self.context_generator = None  # 延遲初始化

    def _get_context_generator(self) -> ContextGenerator:
        """
        獲取情境生成器（延遲初始化）

        Returns:
            ContextGenerator: 情境生成器實例

        Raises:
            RuntimeError: 如果無法獲取 LLM Provider
        """
        if self.context_generator is None:
            try:
                # 從 ResourceManager 獲取 LLM Provider
                rm = get_resource_manager()
                llm_provider = rm.llm_provider

                if llm_provider is None:
                    raise RuntimeError("LLM Provider 未初始化")

                # 創建情境生成器
                self.context_generator = ContextGenerator(
                    llm_provider=llm_provider,
                    temperature=0.3  # 較低溫度確保穩定輸出
                )

                logger.info("[RegulationContextEnrichedChunker] 情境生成器已初始化")

            except Exception as e:
                logger.error(f"[RegulationContextEnrichedChunker] 無法初始化情境生成器：{e}")
                raise RuntimeError(f"無法初始化情境生成器：{e}")

        return self.context_generator

    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        將法規 JSON 分塊（含情境增強）

        Args:
            content: 法規 JSON 字串，符合 RegulationDocument Schema

        Returns:
            List[Dict[str, Any]]: 分塊列表，每條法規生成 2 個分塊：
                1. 原始條文分塊
                2. 情境描述分塊

        Raises:
            ValueError: JSON 格式不正確或不符合 Schema
            RuntimeError: LLM 服務不可用
        """
        try:
            # 解析 JSON
            data = json.loads(content)
            regulation = validate_regulation_json(data)

            # 先生成階層式分塊（原始條文）
            logger.info(
                f"[RegulationContextEnrichedChunker] 開始處理：{regulation.law_metadata.name}"
            )

            hierarchical_chunks = await super().chunk(content)

            logger.info(
                f"[RegulationContextEnrichedChunker] 階層式分塊完成，共 {len(hierarchical_chunks)} 個分塊"
            )

            # 準備條文列表（用於批量生成情境）
            articles = []
            for chapter in regulation.chapters:
                for article in chapter.articles:
                    # 組合完整內容（含項款）
                    content_parts = [article.content] if article.content else []

                    if article.items:
                        for item in article.items:
                            # 項的內容
                            content_parts.append(f"{item.item_display}、{item.content}")

                            # 款的內容
                            if item.subitems:
                                for subitem in item.subitems:
                                    subitem_text = f"  ({subitem.get('subitem_display', '')}) {subitem.get('content', '')}"
                                    content_parts.append(subitem_text)

                    article_content = "\n".join(content_parts)

                    articles.append({
                        "article_num": article.article_num,
                        "article_display": article.article_display,
                        "content": article_content
                    })

            # 批量生成情境描述
            logger.info(
                f"[RegulationContextEnrichedChunker] 開始生成情境描述，共 {len(articles)} 條"
            )

            context_generator = self._get_context_generator()
            contexts = await context_generator.generate_contexts_batch(
                articles=articles,
                law_name=regulation.law_metadata.name,
                max_concurrent=5  # 並行數
            )

            logger.info(
                f"[RegulationContextEnrichedChunker] 情境描述生成完成"
            )

            # 創建情境描述分塊
            context_chunks = []
            for i, (article, context) in enumerate(zip(articles, contexts)):
                if context:  # 只為成功生成情境的條文創建分塊
                    context_chunk = self._create_context_chunk(
                        regulation=regulation,
                        article=article,
                        context=context,
                        chunk_index=len(hierarchical_chunks) + i,
                        original_chunk=hierarchical_chunks[i] if i < len(hierarchical_chunks) else None
                    )
                    context_chunks.append(context_chunk)

            # 合併所有分塊
            all_chunks = hierarchical_chunks + context_chunks

            logger.info(
                f"[RegulationContextEnrichedChunker] 完成：{regulation.law_metadata.name}, "
                f"原始分塊 {len(hierarchical_chunks)} 個，情境分塊 {len(context_chunks)} 個，"
                f"總計 {len(all_chunks)} 個"
            )

            return all_chunks

        except json.JSONDecodeError as e:
            logger.error(f"[RegulationContextEnrichedChunker] JSON 解析失敗：{e}")
            raise ValueError(f"無效的 JSON 格式：{e}")
        except Exception as e:
            logger.error(f"[RegulationContextEnrichedChunker] 分塊失敗：{e}")
            raise

    def _create_context_chunk(
        self,
        regulation: RegulationDocument,
        article: Dict[str, Any],
        context: str,
        chunk_index: int,
        original_chunk: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        創建情境描述分塊

        Args:
            regulation: 法規文件
            article: 條文字典
            context: LLM 生成的情境描述
            chunk_index: 分塊索引
            original_chunk: 對應的原始條文分塊

        Returns:
            Dict[str, Any]: 情境描述分塊
        """
        # 從原始分塊中獲取元數據（如果有）
        if original_chunk:
            original_metadata = original_chunk.get("metadata", {})
        else:
            original_metadata = {}

        # 組合內容：情境描述
        content_parts = []
        content_parts.append(f"【情境描述】{article['article_display']}")
        content_parts.append("")
        content_parts.append(context)

        content = "\n".join(content_parts)

        # Metadata
        metadata = {
            # 法規資訊
            "law_name": regulation.law_metadata.name,
            "law_code": regulation.law_metadata.code,
            "law_category": regulation.law_metadata.category,

            # 條文資訊（從原始分塊複製或使用當前數據）
            "chapter_num": original_metadata.get("chapter_num", ""),
            "chapter_name": original_metadata.get("chapter_name", ""),
            "chapter_display": original_metadata.get("chapter_display", ""),
            "article_num": article["article_num"],
            "article_display": article["article_display"],

            # 階層路徑
            "hierarchy_path": original_metadata.get("hierarchy_path", ""),
            "full_path": f"{regulation.law_metadata.name}/{article['article_display']}",

            # 引用關係（從原始分塊複製）
            "references_to": original_metadata.get("references_to", []),
            "referenced_by": original_metadata.get("referenced_by", []),
            "has_references": original_metadata.get("has_references", False),

            # 分塊資訊
            "chunk_index": chunk_index,
            "representation": "context",  # 標記為情境表徵
            "chunk_type": "regulation_context",
            "linked_article": article["article_num"],  # 關聯到原始條文
            "generated_by": "llm",

            # 來源資訊
            "source_url": regulation.law_metadata.source_url,
            "article_url": article.get("article_url"),
            "last_updated": regulation.law_metadata.last_updated,
        }

        return {
            "content": content,
            "type": "regulation_context",
            "metadata": metadata
        }

    def get_strategy_name(self) -> str:
        """返回策略名稱"""
        return self.name

    def get_description(self) -> str:
        """返回策略描述"""
        return self.description

    def get_example_input(self) -> str:
        """返回範例輸入（與階層式相同）"""
        return super().get_example_input()
