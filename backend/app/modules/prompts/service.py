# -*- coding: utf-8 -*-
"""
提示詞服務層
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models.prompt_template import PromptTemplate
from app.modules.prompts.schemas import (
    PromptTemplateCreateRequest,
    PromptTemplateUpdateRequest
)


class PromptTemplateService:
    """提示詞模板服務"""

    @staticmethod
    async def get_user_templates(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> tuple[List[PromptTemplate], int]:
        """
        取得使用者的提示詞列表

        Args:
            db: 資料庫 session
            user_id: 使用者 ID
            skip: 跳過筆數
            limit: 限制筆數
            active_only: 是否僅查詢啟用的提示詞

        Returns:
            (提示詞列表, 總數)
        """
        # 構建查詢條件
        conditions = [PromptTemplate.user_id == user_id]
        if active_only:
            conditions.append(PromptTemplate.is_active == True)

        # 查詢總數
        count_stmt = select(func.count()).select_from(PromptTemplate).where(and_(*conditions))
        total = await db.scalar(count_stmt) or 0

        # 查詢列表
        stmt = (
            select(PromptTemplate)
            .where(and_(*conditions))
            .order_by(PromptTemplate.is_favorite.desc(), PromptTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        templates = list(result.scalars().all())

        return templates, total

    @staticmethod
    async def get_template_by_id(
        db: AsyncSession,
        template_id: UUID,
        user_id: int
    ) -> Optional[PromptTemplate]:
        """取得單一提示詞（驗證權限）"""
        stmt = select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.user_id == user_id,
                PromptTemplate.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_template(
        db: AsyncSession,
        user_id: int,
        data: PromptTemplateCreateRequest
    ) -> PromptTemplate:
        """建立提示詞模板"""
        # 建立新提示詞
        template = PromptTemplate(
            user_id=user_id,
            name=data.name,
            content=data.content,
            description=data.description,
            is_favorite=data.is_favorite
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)

        logger.info(
            f"建立提示詞模板成功",
            extra={
                "template_id": str(template.id),
                "user_id": user_id,
                "name": data.name,
                "is_favorite": data.is_favorite
            }
        )

        return template

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: UUID,
        user_id: int,
        data: PromptTemplateUpdateRequest
    ) -> Optional[PromptTemplate]:
        """更新提示詞模板"""
        template = await PromptTemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return None

        # 更新欄位
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await db.commit()
        await db.refresh(template)

        logger.info(
            f"更新提示詞模板成功",
            extra={"template_id": str(template_id), "updated_fields": list(update_data.keys())}
        )

        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: UUID,
        user_id: int
    ) -> bool:
        """刪除提示詞模板（軟刪除）"""
        template = await PromptTemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return False

        template.is_active = False
        template.is_favorite = False
        await db.commit()

        logger.info(
            f"刪除提示詞模板成功",
            extra={"template_id": str(template_id), "user_id": user_id}
        )

        return True

    @staticmethod
    async def toggle_favorite(
        db: AsyncSession,
        template_id: UUID,
        user_id: int
    ) -> Optional[PromptTemplate]:
        """切換收藏狀態"""
        template = await PromptTemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return None

        # 切換收藏狀態
        template.is_favorite = not template.is_favorite
        await db.commit()
        await db.refresh(template)

        logger.info(
            f"切換收藏狀態成功",
            extra={
                "template_id": str(template_id),
                "user_id": user_id,
                "is_favorite": template.is_favorite
            }
        )

        return template
