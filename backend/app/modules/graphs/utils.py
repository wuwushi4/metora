# -*- coding: utf-8 -*-
"""
Graph 輔助函數：提供多模態處理、JSON 解析等通用功能
"""
import json
from typing import Optional, List, Dict, Any, Tuple, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger


def extract_text_content(content: Union[str, List, None]) -> str:
    """
    從 AIMessage.content 中提取純文字內容。

    langchain-google-genai 4.x 中，Gemini 模型的 AIMessage.content
    可能是列表格式（包含 thinking parts、text parts 等），而非純字串。
    此函數統一處理兩種格式，確保回傳字串。

    Args:
        content: AIMessage.content，可能是 str、list 或 None

    Returns:
        提取後的純文字字串
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "".join(text_parts)
    return str(content)


def ensure_system_message_first(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    確保 SystemMessage 在 messages 列表的最前面。

    部分 LLM（如 Qwen3.5）的 chat template 嚴格要求
    system message 必須在對話開頭，否則會回傳錯誤。
    此函數提取所有 SystemMessage 並將第一個移到列表最前面，
    確保相容於所有 LLM 後端。

    Args:
        messages: LangChain BaseMessage 列表

    Returns:
        重新排列後的 messages 列表
    """
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    if not system_msgs:
        return messages
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
    return [system_msgs[0]] + other_msgs


def prepare_multimodal_message(
    user_query: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    message_prefix: str = ""
) -> HumanMessage:
    """
    準備使用者訊息（支援多模態：文字 + 圖片）

    根據 LangChain 標準格式構建訊息內容，支援純文字或文字+圖片組合。

    Args:
        user_query: 使用者問題文字
        attachments: 附件列表，格式：
            [
                {
                    "type": "image",
                    "content": "base64_encoded_string",
                    "metadata": {"mime_type": "image/jpeg", ...}
                },
                ...
            ]
        message_prefix: 訊息前綴（如："使用者問題："），預設為空

    Returns:
        HumanMessage: LangChain 訊息對象

    Examples:
        >>> # 純文字訊息
        >>> msg = prepare_multimodal_message("你好")
        >>> print(msg.content)
        "你好"

        >>> # 多模態訊息
        >>> attachments = [{"type": "image", "content": "...", "metadata": {...}}]
        >>> msg = prepare_multimodal_message("這是什麼？", attachments)
        >>> print(msg.content[0])
        {"type": "text", "text": "這是什麼？"}
    """
    # 構建完整的訊息內容
    full_message = f"{message_prefix}{user_query}" if message_prefix else user_query

    # 過濾出圖片類型附件（file 類型不嵌入 LLM 訊息，由 Sandbox 處理）
    image_attachments = [
        a for a in (attachments or [])
        if a.get("type") == "image"
    ]

    if image_attachments:
        # 多模態訊息：文字 + 圖片
        content_parts = []

        # 添加文字內容
        if full_message:
            content_parts.append({
                "type": "text",
                "text": full_message
            })

        # 添加圖片內容（Base64 格式）
        for attachment in image_attachments:
            # 從 metadata 取得 mime_type，預設為 image/jpeg
            mime_type = attachment.get("metadata", {}).get("mime_type", "image/jpeg")
            base64_content = attachment.get("content", "")

            # 構建 image_url 格式（OpenAI/LangChain 標準）
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_content}"
                }
            })

        return HumanMessage(content=content_parts)
    else:
        # 純文字訊息
        return HumanMessage(content=full_message)


def clean_json_response(content: str) -> str:
    """
    清理 LLM 回應中的 Markdown 代碼塊標記

    許多 LLM 會將 JSON 包裹在 ```json ... ``` 或 ``` ... ``` 中，
    此函數會移除這些標記，返回純 JSON 字串。

    Args:
        content: LLM 原始回應內容

    Returns:
        str: 清理後的 JSON 字串

    Examples:
        >>> clean_json_response('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'

        >>> clean_json_response('```\\n{"key": "value"}\\n```')
        '{"key": "value"}'

        >>> clean_json_response('{"key": "value"}')
        '{"key": "value"}'
    """
    content = content.strip()

    # 移除開頭的 Markdown 標記
    if content.startswith("```json"):
        content = content[7:]  # 移除 "```json"
    elif content.startswith("```"):
        content = content[3:]  # 移除 "```"

    # 移除結尾的 Markdown 標記
    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def validate_and_fix_target_articles(articles: List) -> List[str]:
    """
    驗證並修復 target_articles 格式

    自動修復常見的格式錯誤：
    - "第3條" → "3"
    - "動物保護法第3條" → "3"
    - "第3-5條" → "3-5"
    - "3" → "3" (保持不變)

    Args:
        articles: 原始的 target_articles 列表

    Returns:
        修復後的純數字字串列表

    Examples:
        >>> validate_and_fix_target_articles(["第3條", "第15條"])
        ["3", "15"]

        >>> validate_and_fix_target_articles(["動物保護法第3條、第15條"])
        ["3", "15"]

        >>> validate_and_fix_target_articles(["3", "5"])
        ["3", "5"]
    """
    import re

    fixed = []
    for article in articles:
        if not isinstance(article, str):
            continue

        # 移除「第」、「條」等文字，只保留數字
        # 支援格式：
        # - "第3條" → "3"
        # - "動物保護法第3條" → "3"
        # - "第3-5條" → "3-5"
        # - "3" → "3"
        # 使用 findall 處理多條文的情況（如 "第3條、第15條"）
        matches = re.findall(r'第?(\d+(?:-\d+)?)條?', article)
        fixed.extend(matches)

    return fixed


def parse_json_with_fallback(
    response_content: str,
    fallback_value: Any,
    context: str = "",
    user_query: Optional[str] = None
) -> Tuple[Any, bool]:
    """
    解析 JSON 回應，失敗時返回 fallback 值

    此函數會自動清理 Markdown 標記，並提供詳細的錯誤日誌。

    Args:
        response_content: LLM 原始回應內容
        fallback_value: 解析失敗時的備用值
        context: 上下文描述（用於日誌，如："意圖判別"、"查詢重構"）
        user_query: 使用者問題（可選，用於日誌）

    Returns:
        Tuple[Any, bool]: (解析結果, 是否成功)
            - 成功: (parsed_data, True)
            - 失敗: (fallback_value, False)

    Examples:
        >>> result, success = parse_json_with_fallback(
        ...     '```json\\n{"need_rag": true}\\n```',
        ...     {"need_rag": False},
        ...     context="意圖判別"
        ... )
        >>> print(result)
        {"need_rag": true}
        >>> print(success)
        True
    """
    try:
        logger.debug(f"{context}原始回應: {response_content[:200]}")

        # 清理 Markdown 標記
        cleaned_content = clean_json_response(response_content)

        # 解析 JSON
        result = json.loads(cleaned_content)

        # 修復 target_articles 格式
        if "target_articles" in result and isinstance(result["target_articles"], list):
            original_articles = result["target_articles"]
            fixed_articles = validate_and_fix_target_articles(original_articles)
            if fixed_articles != original_articles:
                logger.info(
                    f"{context}自動修復 target_articles: {original_articles} → {fixed_articles}"
                )
                result["target_articles"] = fixed_articles

        logger.info(f"{context}解析成功: {result}")
        return result, True

    except json.JSONDecodeError as e:
        # 構建詳細的錯誤日誌
        log_extra = {
            "context": context,
            "response_content": response_content[:200],  # 只記錄前 200 字元
            "error_type": type(e).__name__,
            "error_position": f"line {e.lineno}, col {e.colno}" if hasattr(e, 'lineno') else "unknown"
        }

        if user_query:
            log_extra["user_query"] = user_query[:100]

        logger.warning(
            f"{context}解析失敗: {e}，使用 fallback 值",
            extra=log_extra,
            exc_info=True  # 記錄完整堆疊
        )

        return fallback_value, False


def format_retrieval_results(
    results: List[Dict[str, Any]],
    include_scores: bool = True
) -> str:
    """
    格式化檢索結果為易讀的文字格式

    將檢索到的文檔列表格式化為結構化的文字，供 LLM 使用。

    Args:
        results: 檢索結果列表，格式：
            [
                {
                    "id": "doc_id",
                    "content": "文檔內容",
                    "metadata": {"filename": "file.txt", ...},
                    "score": 0.95
                },
                ...
            ]
        include_scores: 是否包含相關性分數

    Returns:
        str: 格式化後的文字

    Examples:
        >>> results = [
        ...     {
        ...         "content": "Python 是一種程式語言",
        ...         "metadata": {"filename": "python.txt"},
        ...         "score": 0.95
        ...     }
        ... ]
        >>> print(format_retrieval_results(results))
        【來源 1】
        文件：python.txt
        內容：Python 是一種程式語言
        相關性分數：0.95
    """
    formatted_text = ""
    url_references = {}  # 收集所有 URL：{顯示名稱: URL}

    for i, result in enumerate(results, 1):
        formatted_text += f"\n【來源 {i}】\n"

        # 文件名稱
        metadata = result.get("metadata", {})
        filename = metadata.get("dataset_filename", "Unknown")
        formatted_text += f"文件：{filename}\n"

        # 內容
        content = result.get("content", "")
        formatted_text += f"內容：{content}\n"

        # 相關性分數（可選）
        if include_scores and "score" in result:
            score = result.get("score", 0)
            formatted_text += f"相關性分數：{score:.2f}\n"

        # 收集 URL（用於後續參考連結清單）
        if metadata.get("article_url"):
            law_name = metadata.get("law_name", "")
            article_display = metadata.get("article_display", "")
            if law_name and article_display:
                article_key = f"{law_name} {article_display}"
                url_references[article_key] = metadata["article_url"]

    # 附加 Markdown 格式的參考連結清單
    if url_references:
        formatted_text += "\n【參考連結】\n"
        for article_key, url in url_references.items():
            # 生成 Markdown 超連結格式
            formatted_text += f"• [{article_key}]({url})\n"

    return formatted_text


def validate_attachments(
    attachments: Optional[List[Dict[str, Any]]]
) -> Tuple[bool, Optional[str]]:
    """
    驗證附件格式是否正確

    檢查附件列表的結構和內容是否符合預期格式。

    Args:
        attachments: 附件列表

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)
            - 有效: (True, None)
            - 無效: (False, "錯誤原因")

    Examples:
        >>> attachments = [{"type": "image", "content": "base64...", "metadata": {...}}]
        >>> is_valid, error = validate_attachments(attachments)
        >>> print(is_valid)
        True
    """
    if attachments is None:
        return True, None

    if not isinstance(attachments, list):
        return False, "attachments 必須是列表類型"

    for i, attachment in enumerate(attachments):
        if not isinstance(attachment, dict):
            return False, f"附件 {i} 必須是字典類型"

        # 檢查必需欄位
        if "type" not in attachment:
            return False, f"附件 {i} 缺少 'type' 欄位"

        if attachment["type"] == "image":
            if "content" not in attachment:
                return False, f"圖片附件 {i} 缺少 'content' 欄位"

            # 檢查 content 是否為字串（Base64）
            if not isinstance(attachment["content"], str):
                return False, f"圖片附件 {i} 的 'content' 必須是字串"

        elif attachment["type"] == "file":
            if "file_path" not in attachment:
                return False, f"檔案附件 {i} 缺少 'file_path' 欄位"

    return True, None
