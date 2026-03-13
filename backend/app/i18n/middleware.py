# -*- coding: utf-8 -*-
"""
Locale 中介軟體
從 Accept-Language header 解析語系並設入 ContextVar
"""
from fastapi import Request, Response

from app.i18n import SUPPORTED_LOCALES, DEFAULT_LOCALE, set_locale


def parse_accept_language(header: str) -> str:
    """
    解析 Accept-Language header，回傳最佳匹配的 locale

    範例:
        "zh-TW,zh;q=0.9,en;q=0.8" -> "zh-TW"
        "en-US,en;q=0.9" -> "en"
        "ja,en;q=0.8" -> "zh-TW" (fallback)
    """
    if not header:
        return DEFAULT_LOCALE

    # 解析並按 quality 排序
    locales_with_quality: list[tuple[str, float]] = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q)
            except ValueError:
                quality = 0.0
        else:
            lang = part
            quality = 1.0
        locales_with_quality.append((lang.strip(), quality))

    # 按 quality 降序排序
    locales_with_quality.sort(key=lambda x: x[1], reverse=True)

    # 找到第一個匹配的 locale
    for lang, _ in locales_with_quality:
        # 精確匹配
        if lang in SUPPORTED_LOCALES:
            return lang
        # 前綴匹配 (e.g. "en-US" -> "en")
        prefix = lang.split("-")[0]
        for supported in SUPPORTED_LOCALES:
            if supported.split("-")[0] == prefix:
                return supported

    return DEFAULT_LOCALE


async def locale_middleware(request: Request, call_next) -> Response:
    """FastAPI middleware: 從 Accept-Language 解析 locale 並設入 ContextVar"""
    accept_language = request.headers.get("Accept-Language", "")
    locale = parse_accept_language(accept_language)
    set_locale(locale)
    response = await call_next(request)
    return response
