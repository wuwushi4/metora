# -*- coding: utf-8 -*-
"""
i18n 國際化模組
提供後端多語言翻譯支援
"""
import json
from contextvars import ContextVar
from pathlib import Path
from typing import Any

# 當前請求的 locale
_current_locale: ContextVar[str] = ContextVar("current_locale", default="zh-TW")

# 已載入的翻譯字典
_translations: dict[str, dict[str, Any]] = {}

# 支援的語系
SUPPORTED_LOCALES = ("zh-TW", "en")
DEFAULT_LOCALE = "zh-TW"


def load_translations() -> None:
    """啟動時載入所有翻譯 JSON 檔案"""
    locales_dir = Path(__file__).parent / "locales"
    for locale in SUPPORTED_LOCALES:
        filepath = locales_dir / f"{locale}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                _translations[locale] = json.load(f)


def get_locale() -> str:
    """取得當前請求的 locale"""
    return _current_locale.get()


def set_locale(locale: str) -> None:
    """設定當前請求的 locale"""
    if locale in SUPPORTED_LOCALES:
        _current_locale.set(locale)
    else:
        _current_locale.set(DEFAULT_LOCALE)


def t(key: str, **kwargs: Any) -> str:
    """
    翻譯函式

    支援 dot notation 存取巢狀 key，以及字串插值。

    範例:
        t("auth.login.success")
        t("errors.notFound", resource="使用者", id="123")
    """
    locale = get_locale()
    data = _translations.get(locale, _translations.get(DEFAULT_LOCALE, {}))

    # dot notation 存取
    value: Any = data
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is None:
        # fallback 到預設語系
        if locale != DEFAULT_LOCALE:
            fallback = _translations.get(DEFAULT_LOCALE, {})
            value = fallback
            for part in key.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

    if value is None:
        return key  # 找不到翻譯時回傳 key 本身

    if not isinstance(value, str):
        return key

    # 字串插值
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value

    return value
