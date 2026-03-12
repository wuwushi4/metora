# -*- coding: utf-8 -*-
"""
Collection 管理服務層
處理 Collection CRUD 的業務邏輯
"""
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.collection import Collection
from app.db.models.user import User
from app.modules.collections.schemas import CollectionCreate, CollectionUpdate, CollectionListParams
from app.utils.exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
)


class CollectionService:
    """Collection 管理服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化 Collection 服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def get_collections(
        self,
        params: CollectionListParams,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Tuple[List[Collection], int]:
        """
        獲取 Collection 列表(支援分頁與篩選)

        Args:
            params: 查詢參數(分頁與篩選條件)
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            (Collection 列表, 總筆數)
        """
        # 使用查詢預載入 selectinload 避免 N+1 查詢問題
        stmt = select(Collection).options(selectinload(Collection.datasets))

        # 篩選條件
        filters = []

        # 權限控制：非管理員只能查看自己的 Collection
        if not is_admin:
            if user_id is None:
                raise ValidationError("使用者 ID 不能為空")
            filters.append(Collection.user_id == user_id)

        # name 模糊搜尋
        if params.name:
            filters.append(Collection.name.ilike(f"%{params.name}%"))

        # chunking_strategy 精確搜尋
        if params.chunking_strategy:
            filters.append(Collection.chunking_strategy == params.chunking_strategy)

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

        # 排序:依照更新時間降序排列
        stmt = stmt.order_by(Collection.updated_at.desc())

        # 執行查詢
        result = await self.db.execute(stmt)
        collections = result.scalars().all()

        return list(collections), total

    async def get_collection_by_id(
        self,
        collection_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Collection:
        """
        根據 ID 獲取 Collection

        Args:
            collection_id: Collection ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            Collection 物件

        Raises:
            ResourceNotFoundError: 若 Collection 不存在時
            ValidationError: 若無權限存取時
        """
        stmt = select(Collection).options(
            selectinload(Collection.datasets)
        ).where(Collection.id == collection_id)

        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()

        if not collection:
            raise ResourceNotFoundError("集合", str(collection_id))

        # 權限檢查：非管理員只能查看自己的 Collection
        if not is_admin and collection.user_id != user_id:
            raise ValidationError("無權限存取此集合")

        return collection

    async def create_collection(
        self,
        request: CollectionCreate,
        user_id: int
    ) -> Collection:
        """
        建立新 Collection

        Args:
            request: Collection 建立資料
            user_id: 所有者 ID

        Returns:
            新建立的 Collection 物件

        Raises:
            DuplicateResourceError: 若同一使用者下已存在相同名稱的 Collection
            ValidationError: 若分塊策略不支援
        """
        # 檢查同一使用者下名稱是否重複
        stmt = select(Collection).where(
            Collection.user_id == user_id,
            Collection.name == request.name
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateResourceError(
                resource="集合",
                field="名稱",
                value=request.name
            )

        # 驗證分塊策略（可選：這裡可以呼叫 ChunkerFactory 驗證策略是否存在）
        from app.modules.datasets.chunking.chunker_factory import ChunkerFactory
        available_strategies = ChunkerFactory.list_strategies()
        if request.chunking_strategy not in available_strategies:
            raise ValidationError(
                f"不支援的分塊策略：{request.chunking_strategy}。"
                f"可用策略：{', '.join(available_strategies)}"
            )

        # 建立新 Collection
        now = datetime.now(timezone.utc)
        new_collection = Collection(
            name=request.name,
            description=request.description,
            user_id=user_id,
            chunking_strategy=request.chunking_strategy,
            created_at=now,
            updated_at=now,
        )

        self.db.add(new_collection)
        await self.db.commit()
        await self.db.refresh(new_collection)

        # 重新載入關聯資訊
        await self.db.refresh(new_collection, ["datasets"])

        return new_collection

    async def update_collection(
        self,
        collection_id: int,
        request: CollectionUpdate,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Collection:
        """
        更新 Collection 資訊

        Args:
            collection_id: Collection ID
            request: Collection 更新資料
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Returns:
            更新後的 Collection 物件

        Raises:
            ResourceNotFoundError: 若 Collection 不存在時
            DuplicateResourceError: 若更新的名稱已存在時
            ValidationError: 若無權限更新時
        """
        # 獲取 Collection
        collection = await self.get_collection_by_id(collection_id, user_id, is_admin)

        # 如果更新名稱,檢查是否重複
        if request.name and request.name != collection.name:
            stmt = select(Collection).where(
                Collection.user_id == collection.user_id,
                Collection.name == request.name
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise DuplicateResourceError(
                    resource="集合",
                    field="名稱",
                    value=request.name
                )

        # 只更新有提供的欄位(部分更新)
        if request.name is not None:
            collection.name = request.name

        if request.description is not None:
            collection.description = request.description

        # 更新時間
        collection.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(collection)

        # 重新載入關聯資訊
        await self.db.refresh(collection, ["datasets"])

        return collection

    async def delete_collection(
        self,
        collection_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> bool:
        """
        刪除 Collection（硬刪除，會級聯刪除相關 Dataset）

        Args:
            collection_id: Collection ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Returns:
            是否成功刪除

        Raises:
            ResourceNotFoundError: 若 Collection 不存在時
            ValidationError: 若無權限刪除時
        """
        # 獲取 Collection（包含權限檢查）
        collection = await self.get_collection_by_id(collection_id, user_id, is_admin)

        # 1. 刪除所有關聯 Dataset 的實體檔案
        # 注意：PostgreSQL CASCADE 只會刪除資料庫記錄，不會觸發應用層的檔案刪除
        for dataset in collection.datasets:
            try:
                if os.path.exists(dataset.file_path):
                    os.remove(dataset.file_path)
            except Exception as e:
                # 檔案刪除失敗不應阻止整體刪除流程
                pass

        # 2. 刪除相關的向量資料（從 ChromaDB）
        from app.modules.datasets.vectorization import delete_collection_vectors
        await delete_collection_vectors(collection.id)

        # 3. 刪除 Collection（會級聯刪除相關 Dataset 的資料庫記錄）
        await self.db.delete(collection)
        await self.db.commit()

        # 4. 觸發 BM25 索引失效（新架構）
        from app.core.dependencies import get_resources
        resources = get_resources()
        if resources.bm25_retriever:
            await resources.bm25_retriever.invalidate_collection(collection_id)

        return True

    def _is_admin(self, user: User) -> bool:
        """
        檢查使用者是否為管理員

        Args:
            user: 使用者物件

        Returns:
            是否為管理員
        """
        if user.is_superuser:
            return True

        # 檢查是否有 admin 角色
        return any(role.name == "admin" for role in user.roles)
