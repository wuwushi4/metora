"""
PDF 處理器 - 使用 pypdfium2 將 PDF 轉換為圖片

使用套件: pypdfium2 (Apache 2.0 授權)
功能:
- 驗證 PDF 格式和大小
- 限制 PDF 頁數
- 將每頁轉換為圖片
- 壓縮圖片並儲存
"""

import base64
from loguru import logger
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

from .base import BaseFileProcessor
from .exceptions import FileValidationError, FileSizeExceededError, FileProcessingError




class PDFProcessor(BaseFileProcessor):
    """
    PDF 處理器

    功能:
    - 將 PDF 每一頁轉換為圖片
    - 支援多頁 PDF (限制最大頁數)
    - 壓縮轉換後的圖片
    - 每頁作為獨立附件返回
    """

    async def validate(self, file: UploadFile) -> None:
        """
        驗證 PDF 檔案

        檢查項目:
        1. 功能是否啟用
        2. pypdfium2 套件是否安裝
        3. 檔案大小
        4. PDF Magic Number
        5. 頁數限制
        """
        # 1. 檢查功能是否啟用
        if not self.settings.CHAT_PDF_ENABLED:
            raise FileValidationError(
                "PDF 上傳功能尚未啟用",
                details={"message": "請在 .env 中設定 CHAT_PDF_ENABLED=True"},
            )

        # 2. 檢查 pypdfium2 是否安裝
        if pdfium is None:
            raise FileProcessingError(
                "PDF 處理套件未安裝",
                details={"message": "請執行: uv pip install pypdfium2"},
            )

        # 3. 驗證檔案大小
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        max_size = self.settings.CHAT_PDF_MAX_SIZE
        if file_size > max_size:
            raise FileSizeExceededError(file_size, max_size, file.filename)

        # 4. 驗證 PDF Magic Number
        header = await file.read(4)
        file.file.seek(0)

        if header != b'%PDF':
            raise FileValidationError(
                "不是有效的 PDF 檔案",
                details={
                    "filename": file.filename,
                    "detected_header": header.decode('utf-8', errors='ignore'),
                },
            )

        # 5. 驗證頁數
        # 讀取完整 PDF 內容以驗證頁數
        pdf_content = await file.read()
        file.file.seek(0)

        try:
            # 使用 BytesIO 讀取 PDF
            pdf = pdfium.PdfDocument(pdf_content)
            page_count = len(pdf)
            pdf.close()

            max_pages = self.settings.CHAT_PDF_MAX_PAGES
            if page_count > max_pages:
                raise FileValidationError(
                    f"PDF 頁數超過限制 (最多 {max_pages} 頁)",
                    details={
                        "filename": file.filename,
                        "page_count": page_count,
                        "max_pages": max_pages,
                    },
                )

            logger.info(f"PDF 驗證通過: {file.filename}, 共 {page_count} 頁")

        except Exception as e:
            if isinstance(e, FileValidationError):
                raise
            raise FileProcessingError(
                f"PDF 讀取失敗: {str(e)}",
                details={"filename": file.filename},
            )

    async def process(self, file: UploadFile, save_dir: Path) -> List[Dict[str, Any]]:
        """
        處理 PDF: 轉換每一頁為圖片

        流程:
        1. 驗證檔案
        2. 讀取 PDF 內容
        3. 使用 pypdfium2 渲染每頁
        4. 壓縮圖片
        5. 儲存為 JPEG
        6. 返回每頁的附件資訊

        Returns:
            附件資訊列表,每頁一個字典:
            - id: 附件 ID
            - type: "pdf_page"
            - page_number: 頁碼 (1-based)
            - total_pages: 總頁數
            - file_path: 該頁圖片的儲存路徑
            - original_filename: 來源 PDF 檔名
            - file_size: 圖片檔案大小
            - mime_type: "image/jpeg"
            - extra_data: 包含 width, height, parent_pdf 等
        """
        # 1. 驗證
        await self.validate(file)

        # 2. 讀取 PDF 內容
        pdf_content = await file.read()
        file.file.seek(0)

        # 3. 使用 pypdfium2 開啟 PDF
        try:
            pdf = pdfium.PdfDocument(pdf_content)
            total_pages = len(pdf)

            logger.info(f"開始處理 PDF: {file.filename}, 共 {total_pages} 頁")

            # 4. 準備檔名前綴 (移除副檔名)
            pdf_stem = Path(file.filename).stem
            safe_stem = self._sanitize_filename(pdf_stem)

            # 5. 渲染並儲存每一頁
            results = []
            dpi = self.settings.CHAT_PDF_RENDER_DPI
            scale = dpi / 72  # DPI 轉換為 scale factor

            for page_index in range(total_pages):
                try:
                    # 獲取頁面
                    page = pdf.get_page(page_index)

                    # 渲染為位圖
                    bitmap = page.render(scale=scale)

                    # 轉換為 PIL Image
                    pil_image = bitmap.to_pil()

                    # 取得原始尺寸
                    original_width, original_height = pil_image.size

                    # 壓縮圖片 (重用 ImageProcessor 邏輯)
                    if self.settings.CHAT_IMAGE_COMPRESS_ENABLED:
                        pil_image = await self._compress_image(pil_image)

                    # 轉換為 RGB (JPEG 不支援 RGBA)
                    if pil_image.mode == "RGBA":
                        bg = Image.new("RGB", pil_image.size, (255, 255, 255))
                        bg.paste(pil_image, mask=pil_image.split()[3])
                        pil_image = bg
                    elif pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")

                    # 生成檔名: {pdf_name}_page_{N}.jpg
                    page_number = page_index + 1
                    img_filename = f"{safe_stem}_page_{page_number}.jpg"
                    img_path = self._get_storage_path(img_filename, save_dir)

                    # 儲存為 JPEG
                    pil_image.save(
                        img_path,
                        "JPEG",
                        quality=self.settings.CHAT_IMAGE_QUALITY,
                        optimize=True,
                    )

                    # 取得壓縮後的資訊
                    file_size = img_path.stat().st_size
                    compressed_width, compressed_height = pil_image.size

                    # 生成附件資訊
                    attachment_id = str(uuid4())
                    attachment_info = {
                        "id": attachment_id,
                        "type": "pdf_page",
                        "file_path": str(img_path),
                        "original_filename": file.filename,
                        "file_size": file_size,
                        "mime_type": "image/jpeg",
                        "extra_data": {
                            "page_number": page_number,
                            "total_pages": total_pages,
                            "parent_pdf": file.filename,
                            "width": compressed_width,
                            "height": compressed_height,
                            "original_width": original_width,
                            "original_height": original_height,
                        }
                    }

                    results.append(attachment_info)

                    logger.info(
                        f"PDF 頁面處理完成: {file.filename} 第 {page_number}/{total_pages} 頁",
                        extra={
                            "file_size": file_size,
                            "dimensions": f"{compressed_width}x{compressed_height}",
                        },
                    )

                    # 釋放頁面資源
                    page.close()

                except Exception as e:
                    logger.error(
                        f"處理 PDF 第 {page_index + 1} 頁失敗: {str(e)}",
                        exc_info=True,
                    )
                    # 繼續處理下一頁,不中斷整個流程
                    continue

            # 6. 關閉 PDF
            pdf.close()

            if not results:
                raise FileProcessingError(
                    "PDF 處理失敗: 沒有成功轉換任何頁面",
                    details={"filename": file.filename},
                )

            logger.info(
                f"PDF 處理完成: {file.filename}, 成功轉換 {len(results)}/{total_pages} 頁"
            )

            return results

        except Exception as e:
            if isinstance(e, (FileValidationError, FileProcessingError)):
                raise
            raise FileProcessingError(
                f"PDF 處理失敗: {str(e)}",
                details={"filename": file.filename},
            )

    async def _compress_image(self, img: Image.Image) -> Image.Image:
        """
        壓縮圖片 (等比例縮放)

        重用 ImageProcessor 的壓縮邏輯

        Args:
            img: PIL Image 物件

        Returns:
            壓縮後的 Image 物件
        """
        max_width = self.settings.CHAT_IMAGE_MAX_WIDTH
        max_height = self.settings.CHAT_IMAGE_MAX_HEIGHT

        # 使用 thumbnail 方法進行等比例縮放
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        return img

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理檔名,移除非法字元

        Args:
            filename: 原始檔名

        Returns:
            清理後的檔名
        """
        # 移除非法字元
        import re
        # 只保留字母、數字、底線、連字號
        sanitized = re.sub(r'[^\w\-]', '_', filename)
        # 限制長度
        return sanitized[:100]

    async def to_graph_format(self, attachment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換 PDF 頁面為 Graph 格式

        因為已轉為圖片,格式與 ImageProcessor 相同。
        """
        # 讀取圖片並轉為 base64
        file_path = Path(attachment_info["file_path"])

        if not file_path.exists():
            from .exceptions import FileProcessingError

            raise FileProcessingError(
                f"PDF 頁面圖片不存在: {file_path}",
                details={"attachment_id": attachment_info["id"]},
            )

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        return {
            "id": attachment_info["id"],
            "type": "image",  # 對 LLM 來說,就是圖片
            "content": base64_data,
            "metadata": {
                "source": "pdf",
                "page": attachment_info.get("page_number"),
                "total_pages": attachment_info.get("total_pages"),
                "parent_pdf": attachment_info.get("parent_pdf"),
                "width": attachment_info.get("width"),
                "height": attachment_info.get("height"),
            },
        }
