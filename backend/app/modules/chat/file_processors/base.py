"""
檔案處理器抽象基類
"""

import secrets
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import UploadFile

from .exceptions import FileProcessingError


class BaseFileProcessor(ABC):
    """
    檔案處理器抽象基類

    所有檔案處理器必須繼承此類別並實作以下方法:
    - validate(): 驗證檔案
    - process(): 處理並儲存檔案
    - to_graph_format(): 轉換為 Graph 可用的格式
    """

    def __init__(self, settings):
        """
        初始化處理器

        Args:
            settings: 應用配置物件
        """
        self.settings = settings

    @abstractmethod
    async def validate(self, file: UploadFile) -> None:
        """
        驗證檔案格式和大小

        Args:
            file: 上傳的檔案

        Raises:
            FileValidationError: 驗證失敗時拋出
        """
        pass

    @abstractmethod
    async def process(self, file: UploadFile, save_dir: Path) -> Dict[str, Any]:
        """
        處理檔案並儲存到本地

        Args:
            file: 上傳的檔案
            save_dir: 儲存目錄

        Returns:
            處理後的檔案資訊字典,包含:
            - id: 唯一標識符 (UUID)
            - type: 檔案類型 (image | pdf_page)
            - file_path: 儲存路徑 (用於資料庫記錄)
            - original_filename: 原始檔案名稱
            - file_size: 檔案大小
            - mime_type: MIME 類型
            - created_at: 建立時間
            - ... 其他類型特定欄位

        Raises:
            FileProcessingError: 處理失敗時拋出
        """
        pass

    @abstractmethod
    async def to_graph_format(self, attachment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換為 Graph 可用的格式

        此方法將處理後的附件資訊轉換為 Graph 節點可使用的格式。
        重要: 不應包含檔案路徑,僅包含內容 (如 Base64)。

        Args:
            attachment_info: process() 返回的附件資訊

        Returns:
            Graph 需要的格式字典:
            {
                "id": "...",
                "type": "image" | "pdf_page",
                "content": "base64...",  # 或其他內容表示
                "metadata": {...}  # 額外資訊 (尺寸、頁碼等)
            }
        """
        pass

    def _generate_safe_filename(self, original_filename: str) -> str:
        """
        生成安全的檔案名稱

        使用隨機字串避免檔案名稱衝突和安全問題。

        Args:
            original_filename: 原始檔案名稱

        Returns:
            安全的檔案名稱 (格式: timestamp_random.ext)
        """
        # 清理檔案名稱 (移除路徑穿越字元)
        safe_name = Path(original_filename).name

        # 取得副檔名
        ext = Path(safe_name).suffix.lower()

        # 生成隨機檔案名稱 (timestamp + 隨機字串)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = secrets.token_hex(8)
        return f"{timestamp}_{random_str}{ext}"

    def _get_storage_path(self, filename: str, save_dir: Path) -> Path:
        """
        取得檔案儲存路徑

        Args:
            filename: 檔案名稱
            save_dir: 儲存目錄

        Returns:
            絕對路徑

        Raises:
            FileProcessingError: 路徑驗證失敗
        """
        # 按日期分類 (避免單一目錄檔案過多)
        date_dir = datetime.now().strftime("%Y/%m/%d")

        # 組合完整路徑
        full_path = save_dir / date_dir / filename

        # 驗證路徑是否在允許範圍內 (防止路徑穿越)
        try:
            resolved_path = full_path.resolve()
            resolved_base = save_dir.resolve()

            if not str(resolved_path).startswith(str(resolved_base)):
                raise FileProcessingError(
                    "路徑驗證失敗: 檔案路徑超出允許範圍",
                    details={"filename": filename},
                )
        except Exception as e:
            raise FileProcessingError(f"路徑處理失敗: {str(e)}")

        # 確保目錄存在
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        return resolved_path
