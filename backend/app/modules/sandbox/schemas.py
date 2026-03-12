# -*- coding: utf-8 -*-
"""
Sandbox 模組的資料模型定義
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class InputFile(BaseModel):
    """輸入檔案（注入到 Sandbox 容器）"""
    host_path: str = Field(..., description="後端磁碟上的檔案路徑")
    filename: str = Field(..., description="容器中使用的檔案名稱（原始檔名）")


class CodeExecutionRequest(BaseModel):
    """程式碼執行請求"""
    code: str = Field(..., description="要執行的 Python 程式碼")
    timeout: int = Field(default=60, ge=1, le=300, description="執行超時秒數")
    input_files: List[InputFile] = Field(default_factory=list, description="輸入檔案列表")


class OutputFile(BaseModel):
    """輸出檔案"""
    filename: str = Field(..., description="檔案名稱")
    content_base64: str = Field(..., description="檔案內容（Base64 編碼）")
    mime_type: str = Field(default="application/octet-stream", description="MIME 類型")
    size: int = Field(..., description="檔案大小（bytes）")


class CodeExecutionResult(BaseModel):
    """程式碼執行結果"""
    success: bool = Field(..., description="是否執行成功")
    stdout: str = Field(default="", description="標準輸出")
    stderr: str = Field(default="", description="標準錯誤")
    exit_code: int = Field(default=0, description="退出碼")
    output_files: List[OutputFile] = Field(default_factory=list, description="輸出檔案列表")
    execution_time: float = Field(default=0.0, description="執行時間（秒）")
    error_message: Optional[str] = Field(None, description="錯誤訊息（容器層級）")
