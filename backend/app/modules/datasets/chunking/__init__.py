# -*- coding: utf-8 -*-
"""
分塊策略模組

提供多種文件分塊策略的統一介面
"""
from .base import BaseChunker
from .qa_chunker import QAMultiRepresentationChunker
from .regulation_hierarchical_chunker import RegulationHierarchicalChunker
from .regulation_context_enriched_chunker import RegulationContextEnrichedChunker
from .regulation_manual_scenario_chunker import RegulationManualScenarioChunker
from .recursive_text_chunker import RecursiveTextChunker
from .chunker_factory import ChunkerFactory

__all__ = [
    "BaseChunker",
    "QAMultiRepresentationChunker",
    "RegulationHierarchicalChunker",
    "RegulationContextEnrichedChunker",
    "RegulationManualScenarioChunker",
    "RecursiveTextChunker",
    "ChunkerFactory",
]
