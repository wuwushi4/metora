# -*- coding: utf-8 -*-
"""
分塊策略工廠
"""
from typing import List
from .base import BaseChunker
from .qa_chunker import QAMultiRepresentationChunker
from .regulation_hierarchical_chunker import RegulationHierarchicalChunker
from .regulation_context_enriched_chunker import RegulationContextEnrichedChunker
from .regulation_manual_scenario_chunker import RegulationManualScenarioChunker
from .recursive_text_chunker import RecursiveTextChunker


class ChunkerFactory:
    """
    分塊策略工廠
    
    使用策略模式，根據策略名稱獲取對應的分塊器實例
    未來可輕鬆擴展其他分塊策略（如：固定長度、語義分塊等）
    """
    
    # 註冊所有可用的分塊策略
    _strategies = {
        "qa_multi_representation": QAMultiRepresentationChunker,
        "regulation_hierarchical": RegulationHierarchicalChunker,
        "regulation_context_enriched": RegulationContextEnrichedChunker,
        "regulation_manual_scenario": RegulationManualScenarioChunker,
        "recursive_text": RecursiveTextChunker,
    }
    
    @classmethod
    def get_chunker(cls, strategy: str, **kwargs) -> BaseChunker:
        """
        根據策略名稱獲取分塊器實例
        
        Args:
            strategy: 策略名稱（如：qa_multi_representation）
            **kwargs: 傳遞給分塊器建構子的參數（如 chunk_size, chunk_overlap）
            
        Returns:
            BaseChunker: 分塊器實例
            
        Raises:
            ValueError: 當策略名稱不存在時
        """
        chunker_class = cls._strategies.get(strategy)
        
        if not chunker_class:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(
                f"不支援的分塊策略：{strategy}。"
                f"可用策略：{available}"
            )
        
        return chunker_class(**kwargs)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        列出所有可用的分塊策略
        
        Returns:
            List[str]: 策略名稱列表
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def is_valid_strategy(cls, strategy: str) -> bool:
        """
        檢查策略名稱是否有效
        
        Args:
            strategy: 策略名稱
            
        Returns:
            bool: True 表示策略存在
        """
        return strategy in cls._strategies
