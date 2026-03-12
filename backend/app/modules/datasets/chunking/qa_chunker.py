# -*- coding: utf-8 -*-
"""
QA 多重表徵分塊器
"""
import json
from typing import List, Dict, Any
from .base import BaseChunker


class QAMultiRepresentationChunker(BaseChunker):
    """
    QA 雙表徵分塊策略
    
    為每個 QA 對生成兩種表徵：
    1. Question + Answer（完整內容）- 用於向量存儲
    2. Question only（僅問題）- 用於檢索匹配
    
    支援兩種輸入格式：
    
    格式一（簡單格式）：
    [
        {"question": "什麼是 RAG?", "answer": "RAG 是..."},
        {"question": "如何使用向量資料庫?", "answer": "使用方法..."}
    ]
    
    格式二（進階格式，包含 metadata）：
    {
        "metadata": {
            "version": "1.0",
            "created_at": "2025-01-20",
            "description": "知識庫描述"
        },
        "qa_pairs": [
            {
                "question": "什麼是 RAG?",
                "answer": "RAG 是...",
                "category": "分類",
                "keywords": ["關鍵字1", "關鍵字2"]
            }
        ]
    }
    """
    
    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        解析 QA JSON 格式並生成雙表徵
        
        Args:
            content: JSON 字串，支援簡單格式（陣列）或進階格式（包含 metadata）
            
        Returns:
            List[Dict]: 分塊結果，每個 QA 對產生 2 個分塊
            
        Raises:
            ValueError: 當 JSON 格式錯誤或不符合 QA 格式時
        """
        # 解析 JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"QA 檔案格式錯誤，必須是有效的 JSON：{str(e)}")
        
        # 提取 QA 對列表和 metadata
        qa_pairs, file_metadata = self._parse_json_format(data)
        
        # 驗證 QA 對列表
        if len(qa_pairs) == 0:
            raise ValueError("QA 檔案不能為空，至少需要一個 QA 對")
        
        # 生成分塊
        chunks = []
        for idx, qa in enumerate(qa_pairs):
            # 驗證單個 QA 對
            if not self._validate_qa_pair(qa):
                # 跳過格式不正確的 QA 對，但記錄警告
                print(f"警告：跳過第 {idx + 1} 個 QA 對，格式不正確")
                continue
            
            question = qa["question"].strip()
            answer = qa["answer"].strip()

            # 提取 qa_id (使用者自訂的 ID)
            qa_id = qa.get("id")

            # 提取 QA 層級的 metadata
            qa_metadata = qa.get("metadata", {})

            # 提取額外的 metadata（如 category, keywords 等,但排除 id 和 metadata）
            extra_metadata = {
                k: v for k, v in qa.items()
                if k not in ["question", "answer", "id", "metadata"]
            }

            # 表徵 1: Question + Answer（完整內容）
            full_content = f"Q: {question}\nA: {answer}"
            full_metadata = {
                "chunk_index": idx,
                "representation": "full",
                "qa_id": qa_id,  # 使用者自訂的 QA ID
                "question": question,
                "answer": answer,
                "qa_metadata": qa_metadata,  # QA 層級的 metadata
                **extra_metadata  # 包含 category, keywords 等
            }
            
            # 如果有檔案層級的 metadata，也加入
            if file_metadata:
                full_metadata["file_metadata"] = file_metadata
            
            chunks.append({
                "content": full_content,
                "type": "qa_full",
                "metadata": full_metadata
            })
            
            # 表徵 2: Question only（僅問題，用於檢索）
            question_metadata = {
                "chunk_index": idx,
                "representation": "question",
                "qa_id": qa_id,  # 使用者自訂的 QA ID
                "question": question,
                "answer": answer,  # 保留 answer 用於檢索後回填
                "qa_metadata": qa_metadata,  # QA 層級的 metadata
                **extra_metadata
            }
            
            if file_metadata:
                question_metadata["file_metadata"] = file_metadata
            
            chunks.append({
                "content": question,
                "type": "question_only",
                "metadata": question_metadata
            })
        
        if len(chunks) == 0:
            raise ValueError("沒有有效的 QA 對可以處理")
        
        return chunks
    
    def validate(self, content: str) -> bool:
        """
        驗證是否為有效的 QA JSON 格式（支援兩種格式）
        
        Args:
            content: 待驗證的內容
            
        Returns:
            bool: True 表示格式正確，False 表示格式錯誤
        """
        try:
            data = json.loads(content)
            
            # 提取 QA 對列表
            qa_pairs, _ = self._parse_json_format(data)
            
            # 檢查是否至少有一個 QA 對
            if len(qa_pairs) == 0:
                return False
            
            # 驗證每個 QA 對的格式
            for qa in qa_pairs:
                if not self._validate_qa_pair(qa):
                    return False
            
            return True
            
        except (json.JSONDecodeError, TypeError, KeyError, ValueError):
            return False
    
    def _parse_json_format(self, data: Any) -> tuple[List[Dict[str, Any]], Dict[str, Any] | None]:
        """
        解析 JSON 格式，支援簡單格式和進階格式
        
        Args:
            data: 解析後的 JSON 資料
            
        Returns:
            (qa_pairs, file_metadata): QA 對列表和檔案層級的 metadata（如果有）
            
        Raises:
            ValueError: 當格式不符合任何一種時
        """
        # 格式一：簡單陣列格式 [{question, answer}, ...]
        if isinstance(data, list):
            return data, None
        
        # 格式二：進階格式 {metadata: {...}, qa_pairs: [...]}
        if isinstance(data, dict):
            # 必須包含 qa_pairs 欄位
            if "qa_pairs" not in data:
                raise ValueError(
                    "進階格式的 JSON 必須包含 'qa_pairs' 欄位。"
                    "支援的格式：1) 陣列格式 [{question, answer}, ...] "
                    "2) 物件格式 {metadata: {...}, qa_pairs: [...]}"
                )
            
            qa_pairs = data["qa_pairs"]
            
            # 驗證 qa_pairs 是否為陣列
            if not isinstance(qa_pairs, list):
                raise ValueError("'qa_pairs' 欄位必須是陣列格式")
            
            # 提取 metadata（可選）
            file_metadata = data.get("metadata", None)
            
            return qa_pairs, file_metadata
        
        # 不支援的格式
        raise ValueError(
            "不支援的 JSON 格式。"
            "支援的格式：1) 陣列格式 [{question, answer}, ...] "
            "2) 物件格式 {metadata: {...}, qa_pairs: [...]}"
        )
    
    def _validate_qa_pair(self, qa: Any) -> bool:
        """
        驗證單個 QA 對的格式
        
        Args:
            qa: QA 對字典
            
        Returns:
            bool: True 表示格式正確
        """
        return (
            isinstance(qa, dict) and
            "question" in qa and
            "answer" in qa and
            isinstance(qa["question"], str) and
            isinstance(qa["answer"], str) and
            len(qa["question"].strip()) > 0 and
            len(qa["answer"].strip()) > 0
        )
    
    def get_strategy_name(self) -> str:
        """返回策略名稱"""
        return "qa_multi_representation"

    def supported_file_types(self) -> List[str]:
        """QA 策略僅支援 JSON 格式"""
        return [".json"]
