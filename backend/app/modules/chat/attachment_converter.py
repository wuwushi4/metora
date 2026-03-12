# -*- coding: utf-8 -*-
"""
附件轉換服務

負責將附件資訊轉換為 Graph 所需的格式（Base64 編碼）。
"""
from typing import List, Dict, Any
from loguru import logger

from app.modules.chat.file_processors import ProcessorFactory




class AttachmentConverter:
    """
    附件轉換服務

    將資料庫儲存的附件資訊轉換為 Graph 可消費的格式。
    """

    def __init__(self, settings):
        """
        Args:
            settings: 應用設定物件
        """
        self.settings = settings

    async def convert_to_graph_format(
        self,
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批次轉換附件為 Graph 格式

        Args:
            attachments: 附件資訊列表（來自檔案處理器）

        Returns:
            Graph 格式的附件列表（包含 Base64 編碼內容）
        """
        if not attachments:
            return []

        graph_attachments = []

        for attachment_info in attachments:
            try:
                # 使用處理器轉換為 Graph 格式 (Base64)
                processor = ProcessorFactory.get_processor(
                    attachment_info["original_filename"],
                    self.settings
                )
                graph_format = await processor.to_graph_format(attachment_info)
                graph_attachments.append(graph_format)

                logger.debug(
                    f"附件轉換成功: {attachment_info['original_filename']}",
                    extra={
                        "attachment_id": attachment_info["id"],
                        "attachment_type": attachment_info["type"],
                    }
                )

            except Exception as e:
                logger.error(
                    f"轉換附件為 Graph 格式失敗: {attachment_info.get('original_filename', 'unknown')}",
                    extra={
                        "attachment_id": attachment_info.get("id"),
                        "error": str(e),
                    },
                    exc_info=True
                )
                # 繼續處理其他附件，不中斷整個流程

        return graph_attachments
