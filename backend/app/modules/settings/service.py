# -*- coding: utf-8 -*-
"""
系統設定服務層
處理設定管理的業務邏輯
"""
from typing import Dict, List, Any
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.system_setting import SystemSetting, SystemSettingAudit
from app.modules.settings.schemas import (
    SettingResponse,
    SettingsGroupResponse,
    SettingUpdate,
)
from app.modules.settings.manager import settings_manager
from app.utils.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from loguru import logger


class SettingsService:
    """系統設定服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化設定服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def get_all_settings(self) -> SettingsGroupResponse:
        """
        獲取所有設定,按分類組織

        Returns:
            SettingsGroupResponse: 分類的設定回應
        """
        # 查詢所有非敏感設定
        stmt = select(SystemSetting).where(
            SystemSetting.is_sensitive == False
        ).order_by(SystemSetting.category, SystemSetting.id)

        result = await self.db.execute(stmt)
        settings = result.scalars().all()

        # 按分類組織
        categorized: Dict[str, List[SettingResponse]] = {
            'auth': [],
            'rag': [],
            'chat': [],
            'upload': []
        }

        for setting in settings:
            if setting.category in categorized:
                setting_response = self._to_response(setting)
                categorized[setting.category].append(setting_response)

        return SettingsGroupResponse(**categorized)

    async def get_setting_by_key(self, key: str) -> SettingResponse:
        """
        根據 key 獲取單一設定

        Args:
            key: 設定鍵

        Returns:
            SettingResponse: 設定回應

        Raises:
            ResourceNotFoundError: 設定不存在
        """
        stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            raise ResourceNotFoundError("設定", key)

        return self._to_response(setting)

    async def update_setting(
        self,
        key: str,
        request: SettingUpdate,
        user_id: int
    ) -> SettingResponse:
        """
        更新單一設定

        Args:
            key: 設定鍵
            request: 更新請求
            user_id: 當前使用者 ID

        Returns:
            SettingResponse: 更新後的設定

        Raises:
            ResourceNotFoundError: 設定不存在
            ValidationError: 驗證失敗
        """
        # 1. 查詢設定
        stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            raise ResourceNotFoundError("設定", key)

        # 2. 驗證值
        self._validate_value(request.value, setting)

        # 3. 記錄審計日誌
        old_value = setting.value
        await self._create_audit_log(setting, old_value, str(request.value), user_id)

        # 4. 更新設定
        setting.value = str(request.value)
        setting.updated_by = user_id
        setting.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(setting)

        # 5. 更新記憶體快取
        typed_value = self._convert_value(str(request.value), setting.value_type)
        settings_manager.set(key, typed_value)

        logger.info(f"設定 {key} 已更新: {old_value} -> {request.value} (使用者: {user_id})")

        return self._to_response(setting)

    def _validate_value(self, value: Any, setting: SystemSetting):
        """
        驗證設定值

        Args:
            value: 要驗證的值
            setting: 設定模型

        Raises:
            ValidationError: 驗證失敗
        """
        value_type = setting.value_type

        # 類型驗證
        if value_type == "int":
            if not isinstance(value, int):
                raise ValidationError(f"{setting.display_name} 必須是整數")

            if setting.min_value is not None and value < setting.min_value:
                raise ValidationError(
                    f"{setting.display_name} 不能小於 {int(setting.min_value)}"
                )

            if setting.max_value is not None and value > setting.max_value:
                raise ValidationError(
                    f"{setting.display_name} 不能大於 {int(setting.max_value)}"
                )

        elif value_type == "float":
            if not isinstance(value, (int, float)):
                raise ValidationError(f"{setting.display_name} 必須是數字")

            if setting.min_value is not None and value < setting.min_value:
                raise ValidationError(
                    f"{setting.display_name} 不能小於 {setting.min_value}"
                )

            if setting.max_value is not None and value > setting.max_value:
                raise ValidationError(
                    f"{setting.display_name} 不能大於 {setting.max_value}"
                )

        elif value_type == "bool":
            if not isinstance(value, bool):
                raise ValidationError(f"{setting.display_name} 必須是布林值")

        elif value_type == "string":
            if not isinstance(value, str):
                raise ValidationError(f"{setting.display_name} 必須是字串")

    async def _create_audit_log(
        self,
        setting: SystemSetting,
        old_value: str,
        new_value: str,
        user_id: int
    ):
        """
        建立審計日誌

        Args:
            setting: 設定模型
            old_value: 舊值
            new_value: 新值
            user_id: 使用者 ID
        """
        audit = SystemSettingAudit(
            setting_key=setting.setting_key,
            old_value=old_value,
            new_value=new_value,
            changed_by=user_id,
            changed_at=datetime.now(timezone.utc)
        )
        self.db.add(audit)

    def _to_response(self, setting: SystemSetting) -> SettingResponse:
        """
        轉換 ORM 模型為 Response Schema

        Args:
            setting: 設定模型

        Returns:
            SettingResponse: 設定回應
        """
        # 轉換值為對應類型
        typed_value = self._convert_value(setting.value, setting.value_type)

        return SettingResponse(
            id=setting.id,
            category=setting.category,
            setting_key=setting.setting_key,
            value=typed_value,
            value_type=setting.value_type,
            default_value=self._convert_value(
                setting.default_value, setting.value_type
            ) if setting.default_value else None,
            display_name=setting.display_name,
            description=setting.description,
            min_value=setting.min_value,
            max_value=setting.max_value,
            requires_restart=setting.requires_restart,
            is_sensitive=setting.is_sensitive,
            updated_at=setting.updated_at,
            updated_by=setting.updated_by,
        )

    def _convert_value(self, value: str, value_type: str) -> Any:
        """
        轉換字串值為對應類型

        Args:
            value: 字串值
            value_type: 值類型

        Returns:
            Any: 轉換後的值
        """
        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ('true', '1', 'yes')
        elif value_type == "array":
            import json
            return json.loads(value)
        return value
