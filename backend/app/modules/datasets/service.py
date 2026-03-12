# -*- coding: utf-8 -*-
"""
Dataset 管理服務層
處理 Dataset CRUD 和檔案上傳、向量化的業務邏輯
"""
import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.dataset import Dataset
from app.db.models.collection import Collection
from app.modules.datasets.schemas import DatasetListParams
from app.core.config import settings
from app.utils.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


class DatasetService:
    """Dataset 管理服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化 Dataset 服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def get_datasets(
        self,
        params: DatasetListParams,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Tuple[List[Dataset], int]:
        """
        獲取 Dataset 列表(支援分頁與篩選)

        Args:
            params: 查詢參數(分頁與篩選條件)
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            (Dataset 列表, 總筆數)
        """
        # 建立基本查詢
        stmt = select(Dataset).options(selectinload(Dataset.collection))

        # 篩選條件
        filters = []

        # 權限控制：非管理員只能查看自己 Collection 下的 Dataset
        if not is_admin:
            if user_id is None:
                raise ValidationError("使用者 ID 不能為空")
            # JOIN Collection 表以檢查所有權
            stmt = stmt.join(Dataset.collection).filter(Collection.user_id == user_id)

        # collection_id 精確搜尋
        if params.collection_id:
            filters.append(Dataset.collection_id == params.collection_id)

        # vectorized 精確搜尋
        if params.vectorized is not None:
            filters.append(Dataset.vectorized == params.vectorized)

        # original_filename 模糊搜尋
        if params.original_filename:
            filters.append(Dataset.original_filename.ilike(f"%{params.original_filename}%"))

        # 套用所有篩選條件
        if filters:
            stmt = stmt.filter(*filters)

        # 計算總筆數
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分頁
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        # 排序:依照建立時間降序排列
        stmt = stmt.order_by(Dataset.created_at.desc())

        # 執行查詢
        result = await self.db.execute(stmt)
        datasets = result.scalars().all()

        return list(datasets), total

    async def get_dataset_by_id(
        self,
        dataset_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Dataset:
        """
        根據 ID 獲取 Dataset

        Args:
            dataset_id: Dataset ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            Dataset 物件

        Raises:
            ResourceNotFoundError: 若 Dataset 不存在時
            ValidationError: 若無權限存取時
        """
        stmt = select(Dataset).options(
            selectinload(Dataset.collection)
        ).where(Dataset.id == dataset_id)

        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ResourceNotFoundError("資料集", str(dataset_id))

        # 權限檢查：非管理員只能查看自己的 Dataset
        if not is_admin and dataset.collection.user_id != user_id:
            raise ValidationError("無權限存取此資料集")

        return dataset

    async def upload_dataset(
        self,
        collection_id: int,
        file: UploadFile,
        user_id: int,
        is_admin: bool = False
    ) -> Dataset:
        """
        上傳檔案並建立 Dataset

        Args:
            collection_id: 所屬 Collection ID
            file: 上傳的檔案
            user_id: 當前使用者 ID
            is_admin: 是否為管理員

        Returns:
            新建立的 Dataset 物件

        Raises:
            ResourceNotFoundError: 若 Collection 不存在
            ValidationError: 若檔案驗證失敗或無權限
        """
        # 1. 驗證 Collection 存在且有權限
        collection = await self._get_collection(collection_id, user_id, is_admin)

        # 2. 驗證檔案（含副檔名、大小）
        self._validate_file(file)

        # 3. 驗證檔案類型與分塊策略的相容性
        self._validate_file_strategy_compatibility(file, collection.chunking_strategy)

        # 4. 生成儲存路徑（按年/月分層）
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        upload_dir = Path(settings.UPLOAD_FILES_ROOT) / year_month
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 5. 生成唯一檔名（保留副檔名）
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename

        # 6. 儲存檔案
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise ValidationError(f"檔案儲存失敗：{str(e)}")
        finally:
            await file.close()

        # 7. 獲取檔案大小
        file_size = os.path.getsize(file_path)

        # 8. 建立 Dataset 記錄
        new_dataset = Dataset(
            collection_id=collection_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext,
            chunk_count=0,
            vectorized=False,
            vectorization_error=None,
            created_at=now,
            updated_at=now,
        )

        self.db.add(new_dataset)
        await self.db.commit()
        await self.db.refresh(new_dataset)

        # 重新載入關聯資訊
        await self.db.refresh(new_dataset, ["collection"])

        return new_dataset

    async def vectorize_dataset(
        self,
        dataset_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        """
        向量化 Dataset（背景任務）

        Args:
            dataset_id: Dataset ID
            chunk_size: 使用者指定的分塊大小（僅 recursive_text 策略適用）
            chunk_overlap: 使用者指定的重疊大小（僅 recursive_text 策略適用）

        說明:
        - 此方法將由 BackgroundTasks 呼叫
        - 讀取檔案 -> 分塊 -> 生成向量 -> 存入 ChromaDB
        - 更新 Dataset 狀態（vectorized=True 或記錄錯誤）
        """
        dataset = None
        try:
            # 1. 獲取 Dataset
            dataset = await self.get_dataset_by_id(dataset_id, is_admin=True)

            # 2. 讀取檔案內容（依檔案類型選擇對應 Reader）
            from app.modules.datasets.readers.reader_factory import ReaderFactory
            reader = ReaderFactory.get_reader(dataset.file_type)
            content = await reader.read(dataset.file_path)

            # 3. 獲取 Collection 以取得分塊策略
            collection = dataset.collection

            # 4. 呼叫分塊器（傳入使用者指定的分塊參數）
            from app.modules.datasets.chunking.chunker_factory import ChunkerFactory
            chunker = ChunkerFactory.get_chunker(
                collection.chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            # 驗證內容格式
            if not chunker.validate(content):
                raise ValidationError(f"檔案格式不符合 {collection.chunking_strategy} 策略要求")

            # 執行分塊
            chunks = await chunker.chunk(content)

            # 5. 冪等性處理：先清理舊向量（若重複向量化）
            from app.modules.datasets.vectorization import delete_dataset_vectors
            await delete_dataset_vectors(dataset.id, collection.id)

            # 6. 生成向量並存入向量資料庫
            from app.modules.datasets.vectorization import vectorize_chunks
            from app.core.dependencies import get_resources

            # 獲取全局資源
            resources = get_resources()
            embedding_model = resources.embedding_model
            vector_store = resources.vector_store

            if embedding_model is None or vector_store is None:
                raise RuntimeError("Embedding 模型或向量資料庫尚未初始化")

            # 執行向量化
            await vectorize_chunks(
                collection_id=collection.id,
                collection_name=collection.name,
                dataset_id=dataset.id,
                dataset_filename=dataset.original_filename,
                chunks=chunks,
                embedding_model=embedding_model,
                vector_store=vector_store
            )

            # 7. 更新 Dataset 狀態
            dataset.chunk_count = len(chunks)
            dataset.vectorized = True
            dataset.vectorization_error = None
            dataset.updated_at = datetime.now(timezone.utc)

            await self.db.commit()

            # 8. 觸發 BM25 索引失效（新架構）
            if resources.bm25_retriever:
                await resources.bm25_retriever.invalidate_collection(collection.id)

        except ValidationError as e:
            # 格式驗證錯誤：保留檔案，記錄錯誤
            if dataset:
                dataset.vectorization_error = f"格式驗證失敗: {str(e)}"
                dataset.vectorized = False
                dataset.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
            raise

        except Exception as e:
            # 向量化錯誤：清理部分插入的向量，記錄錯誤
            if dataset:
                # 清理可能部分插入的向量
                from app.modules.datasets.vectorization import delete_dataset_vectors
                await delete_dataset_vectors(dataset.id, dataset.collection_id)

                dataset.vectorization_error = f"向量化失敗: {str(e)}"
                dataset.vectorized = False
                dataset.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
            raise

    async def delete_dataset(
        self,
        dataset_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> bool:
        """
        刪除 Dataset（包含檔案和向量資料）

        Args:
            dataset_id: Dataset ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Returns:
            是否成功刪除

        Raises:
            ResourceNotFoundError: 若 Dataset 不存在時
            ValidationError: 若無權限刪除時
        """
        # 1. 獲取 Dataset（包含權限檢查）
        dataset = await self.get_dataset_by_id(dataset_id, user_id, is_admin)

        # 2. 刪除實體檔案
        try:
            if os.path.exists(dataset.file_path):
                os.remove(dataset.file_path)
        except Exception as e:
            # 檔案刪除失敗不應阻止資料庫記錄刪除
            pass

        # 3. 刪除向量資料（從 ChromaDB）
        if dataset.vectorized:
            from app.modules.datasets.vectorization import delete_dataset_vectors
            await delete_dataset_vectors(dataset.id, dataset.collection_id)

        # 4. 刪除資料庫記錄
        await self.db.delete(dataset)
        await self.db.commit()

        # 5. 觸發 BM25 索引失效（新架構）
        from app.core.dependencies import get_resources
        resources = get_resources()
        if resources.bm25_retriever:
            await resources.bm25_retriever.invalidate_collection(dataset.collection_id)

        return True

    async def _get_collection(
        self,
        collection_id: int,
        user_id: int,
        is_admin: bool
    ) -> Collection:
        """
        內部方法：獲取 Collection 並檢查權限

        Args:
            collection_id: Collection ID
            user_id: 當前使用者 ID
            is_admin: 是否為管理員

        Returns:
            Collection 物件

        Raises:
            ResourceNotFoundError: 若 Collection 不存在
            ValidationError: 若無權限
        """
        stmt = select(Collection).where(Collection.id == collection_id)
        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()

        if not collection:
            raise ResourceNotFoundError("集合", str(collection_id))

        # 權限檢查
        if not is_admin and collection.user_id != user_id:
            raise ValidationError("無權限上傳檔案到此集合")

        return collection

    def _validate_file(self, file: UploadFile) -> None:
        """
        驗證上傳的檔案

        Args:
            file: 上傳的檔案

        Raises:
            ValidationError: 若檔案驗證失敗
        """
        # 檢查檔案名稱
        if not file.filename:
            raise ValidationError("檔案名稱不能為空")

        # 檢查副檔名
        file_ext = Path(file.filename).suffix.lstrip(".")
        allowed_extensions = settings.UPLOAD_ALLOWED_EXTENSIONS_LIST
        if file_ext not in allowed_extensions:
            raise ValidationError(
                f"不支援的檔案類型：{file_ext}。"
                f"允許的類型：{', '.join(allowed_extensions)}"
            )

        # 檢查檔案大小（如果可用）
        if hasattr(file, "size") and file.size:
            if file.size > settings.UPLOAD_MAX_FILE_SIZE:
                max_size_mb = settings.UPLOAD_MAX_FILE_SIZE / (1024 * 1024)
                raise ValidationError(f"檔案大小不能超過 {max_size_mb} MB")

    def _validate_file_strategy_compatibility(
        self, file: UploadFile, chunking_strategy: str
    ) -> None:
        """
        驗證檔案類型與分塊策略的相容性

        Args:
            file: 上傳的檔案
            chunking_strategy: Collection 的分塊策略名稱

        Raises:
            ValidationError: 若檔案類型與策略不相容
        """
        from app.modules.datasets.chunking.chunker_factory import ChunkerFactory

        try:
            chunker = ChunkerFactory.get_chunker(chunking_strategy)
        except ValueError:
            raise ValidationError(f"不支援的分塊策略：{chunking_strategy}")

        supported = chunker.supported_file_types()
        if not supported:
            return

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in supported:
            raise ValidationError(
                f"檔案類型 {file_ext} 與分塊策略 {chunking_strategy} 不相容。"
                f"此策略支援的檔案類型：{', '.join(supported)}"
            )
