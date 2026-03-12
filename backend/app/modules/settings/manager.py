# -*- coding: utf-8 -*-
"""
系統設定管理器 - 單例模式
負責從資料庫載入設定並提供記憶體快取
"""
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models.system_setting import SystemSetting


class SettingsManager:
    """
    設定管理器 - 單例模式
    負責從資料庫載入設定並覆蓋 config.py 中的預設值
    """
    _instance: Optional["SettingsManager"] = None
    _settings_cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def load_from_db(self, db: AsyncSession):
        """
        從資料庫載入所有設定

        Args:
            db: 資料庫 session
        """
        try:
            stmt = select(SystemSetting)
            result = await db.execute(stmt)
            db_settings = result.scalars().all()

            count = 0
            for setting in db_settings:
                # 轉換值為對應類型
                typed_value = self._convert_value(setting.value, setting.value_type)
                self._settings_cache[setting.setting_key] = typed_value
                count += 1

            logger.info(f"✅ 已從資料庫載入 {count} 個系統設定到記憶體快取")
        except Exception as e:
            logger.error(f"❌ 載入系統設定失敗: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取設定值

        Args:
            key: 設定鍵
            default: 預設值

        Returns:
            設定值或預設值
        """
        return self._settings_cache.get(key, default)

    def set(self, key: str, value: Any):
        """
        設定值(僅更新快取,不寫入資料庫)

        Args:
            key: 設定鍵
            value: 設定值
        """
        self._settings_cache[key] = value

    def _convert_value(self, value: str, value_type: str) -> Any:
        """
        轉換字串值為對應類型

        Args:
            value: 字串值
            value_type: 值類型

        Returns:
            轉換後的值
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


# 全局實例
settings_manager = SettingsManager()
