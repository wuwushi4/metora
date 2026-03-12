"""
檔案處理器例外類別
"""


class FileProcessingError(Exception):
    """檔案處理錯誤基類"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(FileProcessingError):
    """檔案驗證錯誤"""

    pass


class UnsupportedFileTypeError(FileValidationError):
    """不支援的檔案類型"""

    def __init__(self, file_type: str, supported_types: list[str]):
        super().__init__(
            message=f"不支援的檔案類型: {file_type}",
            details={
                "file_type": file_type,
                "supported_types": supported_types,
            },
        )


class FileSizeExceededError(FileValidationError):
    """檔案大小超過限制"""

    def __init__(self, file_size: int, max_size: int, filename: str = None):
        size_mb = max_size / 1024 / 1024
        super().__init__(
            message=f"檔案大小超過限制 (最大 {size_mb:.1f}MB)",
            details={
                "file_size": file_size,
                "max_size": max_size,
                "size_mb": file_size / 1024 / 1024,
                "filename": filename,
            },
        )
