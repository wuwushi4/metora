# -*- coding: utf-8 -*-
"""
Regulation 管理服務層
處理 Regulation CRUD 的業務邏輯
"""
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, defer
from sqlalchemy.exc import IntegrityError
from loguru import logger
import json

from app.db.models.regulation import Regulation
from app.modules.regulations.schemas import (
    RegulationUploadRequest,
    RegulationUpdateRequest,
    RegulationListParams,
    RegulationContent,
)
from app.utils.exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
)


class RegulationService:
    """Regulation 管理服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化 Regulation 服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def get_regulations(
        self,
        params: RegulationListParams,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Tuple[List[Regulation], int]:
        """
        獲取 Regulation 列表(支援分頁與篩選)

        Args:
            params: 查詢參數(分頁與篩選條件)
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            (Regulation 列表, 總筆數)
        """
        logger.info(
            f"獲取法規列表 - user_id={user_id}, is_admin={is_admin}, "
            f"page={params.page}, page_size={params.page_size}"
        )

        try:
            # 使用 defer() 避免載入大型 JSONB 欄位，提升列表查詢效能
            stmt = select(Regulation).options(
                defer(Regulation.content),  # 列表查詢不載入完整內容
                joinedload(Regulation.user)  # 多對一關係使用 joinedload 更高效
            )

            # 篩選條件
            filters = []

            # 權限控制：非管理員只能查看自己的 Regulation
            if not is_admin:
                if user_id is None:
                    raise ValidationError("使用者 ID 不能為空")
                filters.append(Regulation.user_id == user_id)

            # law_name 模糊搜尋
            if params.law_name:
                filters.append(Regulation.law_name.ilike(f"%{params.law_name}%"))

            # category 精確搜尋
            if params.category:
                filters.append(Regulation.category == params.category)

            # status 精確搜尋
            if params.status:
                filters.append(Regulation.status == params.status)

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
            stmt = stmt.order_by(Regulation.updated_at.desc())

            # 執行查詢
            result = await self.db.execute(stmt)
            # 使用 unique() 去重（因為使用了 joinedload）
            regulations = result.unique().scalars().all()

            logger.info(f"查詢成功 - 共 {total} 筆資料，當前頁 {len(regulations)} 筆")
            return list(regulations), total

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"獲取法規列表失敗: {str(e)}")
            raise

    async def get_regulation_by_id(
        self,
        regulation_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Regulation:
        """
        根據 ID 獲取 Regulation（包含完整內容）

        Args:
            regulation_id: Regulation ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員（管理員可查看所有資料）

        Returns:
            Regulation 物件

        Raises:
            ResourceNotFoundError: 若 Regulation 不存在時
            ValidationError: 若無權限存取時
        """
        logger.info(f"獲取法規詳情 - regulation_id={regulation_id}, user_id={user_id}")

        try:
            stmt = select(Regulation).options(
                joinedload(Regulation.user)
            ).where(Regulation.id == regulation_id)

            result = await self.db.execute(stmt)
            regulation = result.scalar_one_or_none()

            if not regulation:
                logger.warning(f"法規不存在 - regulation_id={regulation_id}")
                raise ResourceNotFoundError("法規", str(regulation_id))

            # 權限檢查：非管理員只能查看自己的 Regulation
            if not is_admin and regulation.user_id != user_id:
                logger.warning(
                    f"無權限存取法規 - regulation_id={regulation_id}, "
                    f"owner_id={regulation.user_id}, requester_id={user_id}"
                )
                raise ValidationError("無權限存取此法規")

            logger.info(f"查詢成功 - {regulation.law_name}")
            return regulation

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"獲取法規詳情失敗: {str(e)}")
            raise

    async def create_regulation(
        self,
        request: RegulationUploadRequest,
        user_id: int
    ) -> Regulation:
        """
        建立新 Regulation

        Args:
            request: Regulation 上傳資料
            user_id: 所有者 ID

        Returns:
            新建立的 Regulation 物件

        Raises:
            DuplicateResourceError: 若法規代碼已存在
            ValidationError: 若資料驗證失敗
        """
        logger.info(f"創建法規 - user_id={user_id}")

        try:
            # 提取 law_metadata
            law_metadata = request.content.law_metadata
            law_code = law_metadata.code

            # 建立新 Regulation
            now = datetime.now(timezone.utc)

            # 將 Pydantic 模型轉換為字典
            content_dict = request.content.model_dump()

            new_regulation = Regulation(
                law_code=law_code,
                law_name=law_metadata.name,
                category=law_metadata.category,
                status=law_metadata.status,
                last_updated=law_metadata.last_updated,
                content=content_dict,
                user_id=user_id,
                created_at=now,
                updated_at=now,
            )

            self.db.add(new_regulation)

            try:
                await self.db.commit()
            except IntegrityError as e:
                await self.db.rollback()
                # 檢查是否為 law_code 重複
                if "law_code" in str(e.orig):
                    logger.warning(f"法規代碼已存在 - law_code={law_code}")
                    raise DuplicateResourceError(
                        resource="法規",
                        field="法規代碼",
                        value=law_code
                    )
                # 其他完整性錯誤
                logger.error(f"資料庫完整性錯誤: {str(e)}")
                raise ValidationError(f"資料庫完整性錯誤: {str(e)}")

            await self.db.refresh(new_regulation)

            # 重新載入關聯資訊
            await self.db.refresh(new_regulation, ["user"])

            logger.info(
                f"法規創建成功 - regulation_id={new_regulation.id}, "
                f"law_code={law_code}, law_name={law_metadata.name}"
            )
            return new_regulation

        except (DuplicateResourceError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"創建法規失敗: {str(e)}")
            await self.db.rollback()
            raise

    async def update_regulation(
        self,
        regulation_id: int,
        request: RegulationUpdateRequest,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Regulation:
        """
        更新 Regulation（主要更新 scenarios）

        Args:
            regulation_id: Regulation ID
            request: 更新資料
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Returns:
            更新後的 Regulation 物件

        Raises:
            ResourceNotFoundError: 若 Regulation 不存在
            ValidationError: 若無權限或驗證失敗
        """
        logger.info(f"更新法規 - regulation_id={regulation_id}, user_id={user_id}")

        try:
            # 獲取現有 Regulation
            regulation = await self.get_regulation_by_id(
                regulation_id=regulation_id,
                user_id=user_id,
                is_admin=is_admin
            )

            # 驗證 law_code 是否匹配（防止替換不同法規）
            old_law_code = self._get_law_code_from_content(regulation.content)
            new_law_code = request.content.law_metadata.code
            if old_law_code != new_law_code:
                raise ValidationError(
                    f"法規代碼不匹配：原始={old_law_code}, 新={new_law_code}。"
                    "不允許更換法規代碼，請刪除後重新上傳。"
                )

            # 驗證結構一致性（確保只更新 scenarios）
            content_dict = request.content.model_dump()
            self._validate_structure_consistency(regulation.content, content_dict)

            # 更新內容
            regulation.content = content_dict
            regulation.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(regulation)

            logger.info(f"法規更新成功 - regulation_id={regulation_id}")
            return regulation

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"更新法規失敗: {str(e)}")
            await self.db.rollback()
            raise

    async def delete_regulation(
        self,
        regulation_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> None:
        """
        刪除 Regulation

        Args:
            regulation_id: Regulation ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Raises:
            ResourceNotFoundError: 若 Regulation 不存在
            ValidationError: 若無權限
        """
        logger.info(f"刪除法規 - regulation_id={regulation_id}, user_id={user_id}")

        try:
            # 獲取並驗證權限
            regulation = await self.get_regulation_by_id(
                regulation_id=regulation_id,
                user_id=user_id,
                is_admin=is_admin
            )

            # 刪除
            await self.db.delete(regulation)
            await self.db.commit()

            logger.info(
                f"法規刪除成功 - regulation_id={regulation_id}, "
                f"law_code={regulation.law_code}"
            )

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"刪除法規失敗: {str(e)}")
            await self.db.rollback()
            raise

    async def export_regulation_json(
        self,
        regulation_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """
        導出 Regulation 為 JSON 格式

        Args:
            regulation_id: Regulation ID
            user_id: 當前使用者 ID（非管理員時必須提供）
            is_admin: 是否為管理員

        Returns:
            完整的 JSON 內容（content 欄位）

        Raises:
            ResourceNotFoundError: 若 Regulation 不存在
            ValidationError: 若無權限
        """
        logger.info(f"導出法規 JSON - regulation_id={regulation_id}, user_id={user_id}")

        try:
            regulation = await self.get_regulation_by_id(
                regulation_id=regulation_id,
                user_id=user_id,
                is_admin=is_admin
            )

            # 透過 Schema 正規化內容，確保欄位一致
            content_model = RegulationContent(**regulation.content)
            normalized_content = content_model.model_dump()

            # 檢查內容大小（防止記憶體溢出）
            content_json = json.dumps(normalized_content, ensure_ascii=False)
            content_size_mb = len(content_json.encode('utf-8')) / (1024 * 1024)

            if content_size_mb > 50:  # 限制 50MB
                logger.warning(
                    f"法規內容過大 - regulation_id={regulation_id}, "
                    f"size={content_size_mb:.2f}MB"
                )
                raise ValidationError(
                    f"法規內容過大（{content_size_mb:.2f}MB），無法導出。"
                    "請聯繫管理員。"
                )

            logger.info(f"法規導出成功 - {regulation.law_name}, size={content_size_mb:.2f}MB")
            return normalized_content

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"導出法規 JSON 失敗: {str(e)}")
            raise

    def _validate_structure_consistency(
        self,
        old_content: Dict[str, Any],
        new_content: Dict[str, Any]
    ) -> None:
        """
        驗證法規結構一致性（確保只更新 scenarios）

        Args:
            old_content: 原始內容
            new_content: 新內容

        Raises:
            ValidationError: 若結構不一致
        """
        old_chapters = old_content.get('chapters', [])
        new_chapters = new_content.get('chapters', [])

        # 驗證章節數量
        if len(old_chapters) != len(new_chapters):
            raise ValidationError(
                f"章節數量不一致：原始={len(old_chapters)}, "
                f"新={len(new_chapters)}。不允許修改法規結構。"
            )

        # 驗證每個章節
        for i, (old_ch, new_ch) in enumerate(zip(old_chapters, new_chapters)):
            # 驗證章節編號
            if old_ch.get('chapter_num') != new_ch.get('chapter_num'):
                raise ValidationError(
                    f"第 {i+1} 章的編號不一致：原始={old_ch.get('chapter_num')}, "
                    f"新={new_ch.get('chapter_num')}。不允許修改章節編號。"
                )

            # 驗證條文數量
            old_articles = old_ch.get('articles', [])
            new_articles = new_ch.get('articles', [])
            if len(old_articles) != len(new_articles):
                raise ValidationError(
                    f"第 {i+1} 章的條文數量不一致：原始={len(old_articles)}, "
                    f"新={len(new_articles)}。不允許修改法規結構。"
                )

            # 驗證每個條文
            for j, (old_art, new_art) in enumerate(zip(old_articles, new_articles)):
                # 驗證條文編號
                if old_art.get('article_num') != new_art.get('article_num'):
                    raise ValidationError(
                        f"第 {i+1} 章第 {j+1} 條的編號不一致：原始={old_art.get('article_num')}, "
                        f"新={new_art.get('article_num')}。不允許修改條文編號。"
                    )

                # 驗證條文內容
                if old_art.get('content') != new_art.get('content'):
                    raise ValidationError(
                        f"第 {i+1} 章第 {j+1} 條的內容不一致。不允許修改條文內容，"
                        "僅允許更新 scenarios。"
                    )

        logger.info("法規結構驗證通過 - 僅更新 scenarios")

    @staticmethod
    def _get_law_code_from_content(content: Dict[str, Any]) -> Optional[str]:
        """從 content 中提取法規代碼，兼容舊欄位"""
        if not content:
            return None
        metadata = content.get('law_metadata', {}) or {}
        return metadata.get('code') or metadata.get('pcode')
