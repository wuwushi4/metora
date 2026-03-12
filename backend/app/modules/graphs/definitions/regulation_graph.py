# -*- coding: utf-8 -*-
"""
法規查詢和分析 Graph

專門針對法規查詢優化的 Graph，支援：
- 條文精確查詢
- 情境化查詢
- 引用關係追蹤
- 法規條文比對

流程：START → intent_analysis → query_rewrite → regulation_search →
      reference_expansion → response_generation → END
"""
from typing import TypedDict, List, Dict, Any
try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python < 3.11

import json
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.modules.graphs.utils import (
    prepare_multimodal_message,
    parse_json_with_fallback,
    format_retrieval_results,
    extract_text_content,
)
from app.utils.regulation_utils import sort_article_nums


class RegulationGraphState(TypedDict):
    """法規 Graph 狀態"""
    # 對話歷史
    messages: List[BaseMessage]
    rewrite_context: List[BaseMessage]

    # 使用者輸入
    user_query: str
    collection_ids: List[int]
    attachments: NotRequired[List[Dict[str, Any]]]

    # 意圖分析
    is_regulation_query: bool
    query_type: str  # "article_lookup"(條文查詢), "scenario"(情境查詢), "comparison"(對比查詢), "interpretation"(解釋查詢)
    intent_reason: str

    # 查詢重構
    rewritten_queries: List[str]
    target_articles: List[str]  # 明確指定的條文編號

    # 檢索結果
    retrieval_results: List[Dict[str, Any]]

    # 最終輸出
    final_response: str
    cited_articles: List[str]  # 回應中引用的條文

    # 自訂提示詞
    custom_system_prompt: NotRequired[str]  # 自訂系統提示詞 - 非必需欄位


def create_regulation_graph(
    settings,
    llm_provider,
    retrieval_service
) -> CompiledStateGraph:
    """
    建立法規查詢 Graph

    Args:
        settings: 應用設定
        llm_provider: LLM Provider 實例
        retrieval_service: 檢索服務實例

    Returns:
        CompiledStateGraph: 編譯後的 Graph
    """
    llm = llm_provider.to_langchain_llm()

    # ==================== 節點定義 ====================

    async def intent_analysis_node(state: RegulationGraphState) -> RegulationGraphState:
        """
        意圖分析節點：判斷查詢類型

        查詢類型：
        - article_lookup: 直接查詢條文（如"第3條是什麼"）
        - scenario: 情境查詢（如"有人在夜市裡買了一隻在籠中打鬥的雞來賭博，這個行為違反哪條？"）
        - comparison: 對比查詢（如"第3條和第8條的關係"）
        - interpretation: 解釋查詢（如"第3條怎麼理解"）
        """
        system_prompt = """你是法規查詢分析專家。請分析使用者的問題，判斷查詢類型。

查詢類型：
1. article_lookup（條文查詢）：
   - 直接詢問特定條文的內容
   - 例如："第3條是什麼"、"第10條的規定"

2. scenario（情境查詢）：
   - 描述具體情境，詢問適用哪條法規
   - 例如："我家貓咪在夜裡從四樓窗戶跳出受傷，我沒有立即帶去獸醫，會觸法嗎？"、"有人在街上看到有人用棍子揍流浪貓，請問那個人可能觸犯哪條？"

3. comparison（對比查詢）：
   - 比較多個條文的關係或差異
   - 例如："第3條和第8條有什麼關係"、"這兩條的區別"

4. interpretation（解釋查詢）：
   - 詢問條文的含義或如何理解
   - 例如："第3條怎麼理解"、"這條是什麼意思"

請以 JSON 格式回答：
{
    "is_regulation_query": true/false,
    "query_type": "article_lookup/scenario/comparison/interpretation",
    "reason": "繁體中文判斷理由"
}"""

        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["rewrite_context"])
        messages.append(prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments")
        ))

        response = await llm.ainvoke(messages)
        result, success = parse_json_with_fallback(
            extract_text_content(response.content),
            fallback_value={
                "is_regulation_query": True,
                "query_type": "scenario",
                "reason": "預設為情境查詢"
            },
            context="意圖分析",
            user_query=state["user_query"]
        )

        logger.info(
            f"[RegulationGraph] 意圖分析：{result.get('query_type', 'scenario')}, "
            f"理由：{result.get('reason', '')}"
        )

        return {
            **state,
            "is_regulation_query": result.get("is_regulation_query", True),
            "query_type": result.get("query_type", "scenario"),
            "intent_reason": result.get("reason", "")
        }

    async def query_rewrite_node(state: RegulationGraphState) -> RegulationGraphState:
        """
        查詢重構節點：針對法規優化查詢

        根據查詢類型重構查詢：
        - article_lookup: 提取條文編號
        - scenario: 提取關鍵情境和法律概念
        - comparison: 提取要比較的條文
        - interpretation: 確定要解釋的條文
        """
        query_type = state["query_type"]

        if query_type == "article_lookup":
            system_prompt = """你的任務是從使用者問題中提取條文編號。

這是「單純條文內容查詢」，只需要找到條文本身的內容，不需要額外的解釋或比較。

規則：
1. 提取所有明確的條文編號（如"第3條"、"第10條"）
2. queries 設為空數組 []（因為只需要條文本身的內容）
3. 如果沒有明確編號，則不填 target_articles，改用 queries 生成檢索關鍵詞

範例 1（單個條文）：
問題：「動物保護法第3條是什麼？」
回答：{"target_articles": ["3"], "queries": []}

範例 2（多個條文）：
問題：「第3條、第5條和第8條的內容是什麼？」
回答：{"target_articles": ["3", "5", "8"], "queries": []}

範例 3（無明確條文）：
問題：「關於虐待動物的規定是什麼？」
回答：{"target_articles": [], "queries": ["虐待動物規定", "動物保護法相關條文"]}

以 JSON 格式回答：
{
    "target_articles": ["3"],  // 條文編號列表（純數字字串）
    "queries": []  // 對於單純條文查詢，設為空數組
}"""

        elif query_type == "scenario":
            system_prompt = """你的任務是將使用者的問題改寫為完整的情境描述，最少一個，最多三個，用於檢索法規資料庫中的情境範例。

這是「情境查詢」，使用者描述了具體的場景或行為，詢問適用的法規。

【重要原則】
資料庫中儲存的是「完整的情境描述句子」（平均 15-30 字），例如：
- 「寵物受傷後沒有立即送醫治療，飼主會不會違法？」
- 「看到有人用棍子打流浪狗，這算不算虐待動物？」
- 「養的貓生病了但沒錢看醫生，會不會觸犯法律？」

你的查詢必須生成類似格式的完整句子，才能匹配到這些情境。

【改寫規則】
1. **保持完整語意上下文**（15-30 字）
   ✓ 正確：「寵物受傷後沒有立即送醫治療，飼主會不會違法？」
   ✗ 錯誤：「帶去獸醫」「責任」「受傷」（過短的關鍵詞無法匹配）

2. **使用口語化、生活化的表達**
   - 保留「人、動物、行為、場景」的完整要素
   - 使用日常用語，避免過度法律術語
   - 可以用疑問句或陳述句

3. **從不同角度改寫 1-3 個變體**
   - 變體 1：保持使用者原問題的核心表述
   - 變體 2：換個角度或換個說法
   - 變體 3：擴展或簡化場景細節

4. **保留場景細節和具體對象**
   - ✓ 保留：「流浪狗」「寵物」「貓」「受傷」「生病」「打」「關籠子」
   - ✗ 移除：過度抽象化為「動物」「飼養」「義務」

5. **條文編號處理**
   - target_articles 通常設為空數組（情境查詢很少直接提到條文）
   - 如果問題明確提到條文編號，才提取純數字（如 ["3", "5"]）

【範例】

✓ 正確示範：
問題：「我家的狗受傷了，但我沒有馬上帶去看醫生，這樣會違法嗎？」
{
    "target_articles": [],
    "queries": [
        "寵物受傷後沒有立即送醫治療，飼主會不會違法？",
        "動物生病或受傷時，主人有義務帶去獸醫嗎？",
        "家裡的貓或狗受傷了，如果不馬上處理會有法律責任嗎？"
    ]
}

✗ 錯誤示範（過短的關鍵詞）：
{
    "target_articles": [],
    "queries": ["帶去獸醫", "責任", "受傷"]  // 太短，無法匹配情境描述
}

輸出格式：
{
    "target_articles": [],  // 純數字條文編號，如 ["3", "5"]
    "queries": ["完整情境描述1（15-30字）", "完整情境描述2", "完整情境描述3"]
}"""

        elif query_type == "comparison":
            system_prompt = """你的任務是提取要比較的條文，並生成比較的角度。

這是「條文比對查詢」，需要找到多個條文並理解它們之間的關係。

規則：
1. 提取所有要比較的條文編號
2. 生成有助於理解比較角度的查詢詞（如：差異、關係、適用範圍等）

範例：
問題：「第3條和第5條有什麼不同？」
回答：{"target_articles": ["3", "5"], "queries": ["條文差異", "適用範圍比較"]}

以 JSON 格式回答：
{
    "target_articles": ["3", "5"],  // 要比較的條文編號
    "queries": ["條文差異", "適用範圍"]  // 比較的角度
}"""

        else:  # interpretation
            system_prompt = """你的任務是確定要解釋的條文，並生成解釋的角度。

這是「法規解釋查詢」，需要深入理解條文的含義、適用情境或實際應用。

規則：
1. 提取要解釋的條文編號
2. 根據問題生成解釋的角度（如：適用情境、實際案例、法律意義等）

範例 1（適用範圍）：
問題：「第3條適用於哪些情況？」
回答：{"target_articles": ["3"], "queries": ["適用情境", "適用範圍"]}

範例 2（實際案例）：
問題：「第5條在實務上如何應用？」
回答：{"target_articles": ["5"], "queries": ["實際案例", "實務應用"]}

以 JSON 格式回答：
{
    "target_articles": ["3"],  // 要解釋的條文編號
    "queries": ["適用情境", "實際案例"]  // 解釋的角度
}"""

        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["rewrite_context"])
        messages.append(prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments")
        ))

        response = await llm.ainvoke(messages)
        result, success = parse_json_with_fallback(
            extract_text_content(response.content),
            fallback_value={"target_articles": [], "queries": [state["user_query"]]},
            context="查詢重構",
            user_query=state["user_query"]
        )

        # 限制查詢數量（最多 3 個）
        if "queries" in result and isinstance(result["queries"], list):
            if len(result["queries"]) > 3:
                logger.warning(
                    f"[RegulationGraph] 查詢數量超過限制 ({len(result['queries'])} > 3)，截取前 3 個"
                )
                result["queries"] = result["queries"][:3]

        logger.info(
            f"[RegulationGraph] 查詢重構：目標條文 {result.get('target_articles', [])}, "
            f"查詢 {result.get('queries', [])}"
        )

        return {
            **state,
            "target_articles": result.get("target_articles", []),
            "rewritten_queries": result.get("queries", [state["user_query"]])
        }

    async def regulation_search_node(state: RegulationGraphState) -> RegulationGraphState:
        """
        法規檢索節點：根據查詢類型選擇最優檢索策略

        策略：
        1. 明確條文編號 → 使用 get_articles_by_nums()（快速精確，避免誤匹配）
        2. 情境查詢 → 使用 cross_collection_search()（向量檢索）
        """
        collection_ids = state["collection_ids"]
        target_articles = state.get("target_articles", [])
        queries = state.get("rewritten_queries", [])

        all_results = []

        # 策略1: 精確條文查詢（使用 metadata 直接查詢）
        if target_articles:
            logger.info(f"[RegulationGraph] 精確檢索條文（使用 get_articles_by_nums）：{target_articles}")
            documents = await retrieval_service.get_articles_by_nums(
                article_nums=target_articles,
                collection_ids=collection_ids,
                chunk_type="regulation_article"
            )
            all_results = [doc.to_dict() for doc in documents]

        # 策略2: 情境查詢（使用向量檢索）
        elif queries:
            logger.info(f"[RegulationGraph] 情境檢索（使用向量檢索）：{queries}")
            for query in queries:
                documents = await retrieval_service.cross_collection_search(
                    queries=[query],
                    collection_ids=collection_ids,
                    top_k=settings.RAG_RETRIEVER_TOP_K
                )
                results = [doc.to_dict() for doc in documents]
                all_results.extend(results)

            # 去重（根據 article_num）
            seen_articles = set()
            unique_results = []
            for result in all_results:
                metadata = result.get("metadata", {})
                article_num = metadata.get("article_num")
                if article_num and article_num not in seen_articles:
                    seen_articles.add(article_num)
                    unique_results.append(result)
                elif not article_num:
                    unique_results.append(result)

            all_results = unique_results

        logger.info(f"[RegulationGraph] 檢索完成：共 {len(all_results)} 個結果")

        return {
            **state,
            "retrieval_results": all_results[:10]  # 限制結果數量
        }

    # ==================== 已停用：引用擴展功能 ====================
    # 停用原因：增加上下文複雜度，導致 LLM 回答不穩定、出現幻覺
    # 停用日期：2025-11-13
    # 決策依據：多次測試發現簡化上下文後回答更穩定準確
    #
    # async def reference_expansion_node(state: RegulationGraphState) -> RegulationGraphState:
    #     """
    #     引用關係擴展節點：根據引用關係找到相關條文
    #
    #     對於檢索到的每個條文：
    #     - 查找它引用的其他條文（forward_refs）
    #     - 查找引用它的其他條文（backward_refs）
    #     """
    #     retrieval_results = state.get("retrieval_results", [])
    #     collection_ids = state["collection_ids"]
    #     related_articles = []
    #
    #     # 收集所有需要擴展的條文編號
    #     referenced_article_nums = set()
    #
    #     for result in retrieval_results:
    #         metadata = result.get("metadata", {})
    #         forward_refs = metadata.get("references_to", [])
    #         backward_refs = metadata.get("referenced_by", [])
    #
    #         # 防禦性處理：確保引用列表是正確的類型
    #         # 雖然檢索層應該已經處理了反序列化，這裡作為雙重保險
    #         if isinstance(forward_refs, str):
    #             try:
    #                 forward_refs = json.loads(forward_refs) if forward_refs.strip() else []
    #                 logger.warning(
    #                     f"[RegulationGraph] references_to 為字串(已解析為列表): {forward_refs}"
    #                 )
    #             except (json.JSONDecodeError, ValueError):
    #                 logger.error(
    #                     f"[RegulationGraph] references_to JSON 解析失敗: {forward_refs}"
    #                 )
    #                 forward_refs = []
    #
    #         if isinstance(backward_refs, str):
    #             try:
    #                 backward_refs = json.loads(backward_refs) if backward_refs.strip() else []
    #                 logger.warning(
    #                     f"[RegulationGraph] referenced_by 為字串(已解析為列表): {backward_refs}"
    #                 )
    #             except (json.JSONDecodeError, ValueError):
    #                 logger.error(
    #                     f"[RegulationGraph] referenced_by JSON 解析失敗: {backward_refs}"
    #                 )
    #                 backward_refs = []
    #
    #         # 確保是列表類型
    #         if not isinstance(forward_refs, list):
    #             logger.error(
    #                 f"[RegulationGraph] references_to 類型異常: {type(forward_refs)}"
    #             )
    #             forward_refs = []
    #
    #         if not isinstance(backward_refs, list):
    #             logger.error(
    #                 f"[RegulationGraph] referenced_by 類型異常: {type(backward_refs)}"
    #             )
    #             backward_refs = []
    #
    #         referenced_article_nums.update(forward_refs)
    #         referenced_article_nums.update(backward_refs)
    #
    #     # 過濾無效的條文編號
    #     def is_valid_article_num(num) -> bool:
    #         """
    #         驗證條文編號是否有效
    #
    #         支援格式：
    #         - 純數字：3, 10, 25
    #         - 分支條文：3-1, 25-1, 6-2
    #
    #         不支援格式：
    #         - 空值、負數、零
    #         - 包含非法字符
    #         """
    #         if not num:
    #             return False
    #
    #         # 轉換為字串並清理
    #         num_str = str(num).strip()
    #
    #         if not num_str:
    #             return False
    #
    #         try:
    #             # 檢查是否為分支條文格式 (如 "25-1", "6-1")
    #             if "-" in num_str:
    #                 parts = num_str.split("-")
    #                 # 必須恰好有兩部分
    #                 if len(parts) != 2:
    #                     return False
    #
    #                 # 兩部分都必須是正整數
    #                 main_num = int(parts[0])
    #                 sub_num = int(parts[1])
    #
    #                 return main_num > 0 and sub_num > 0
    #
    #             # 檢查純數字格式
    #             if num_str.isdigit():
    #                 return int(num_str) > 0
    #
    #             # 其他格式一律拒絕
    #             return False
    #
    #         except (ValueError, AttributeError):
    #             logger.warning(
    #                 f"[RegulationGraph] 條文編號驗證失敗: {num_str}"
    #             )
    #             return False
    #
    #     valid_article_nums = {num for num in referenced_article_nums if is_valid_article_num(num)}
    #
    #     if len(referenced_article_nums) != len(valid_article_nums):
    #         invalid_nums = referenced_article_nums - valid_article_nums
    #         logger.warning(
    #             f"[RegulationGraph] 引用擴展：過濾掉 {len(invalid_nums)} 個無效條文編號：{invalid_nums}"
    #         )
    #
    #     # 檢索相關條文
    #     if valid_article_nums:
    #         logger.debug(
    #             f"[RegulationGraph] 引用擴展：檢索 {len(valid_article_nums)} 個有效相關條文"
    #         )
    #
    #         # ✅ 使用直接 metadata 查詢，避免完整的向量檢索流程
    #         # 效能：約 2ms/條文（vs 向量檢索的 200ms/條文）
    #         # ✅ 使用排序確保每次選擇相同的引用條文（條文編號最小的前 5 個）
    #         sorted_article_nums = sort_article_nums(list(valid_article_nums))
    #         documents = await retrieval_service.get_articles_by_nums(
    #             article_nums=sorted_article_nums[:5],  # 限制數量：取條文編號最小的前 5 個
    #             collection_ids=collection_ids,
    #             chunk_type="regulation_article"
    #         )
    #
    #         # 將 Document 對象轉換為字典格式
    #         related_articles = [doc.to_dict() for doc in documents]
    #
    #     logger.info(f"[RegulationGraph] 引用擴展完成：找到 {len(related_articles)} 個相關條文")
    #
    #     return {
    #         **state,
    #         "related_articles": related_articles
    #     }
    # ==================== 已停用結束 ====================

    async def response_generation_node(state: RegulationGraphState) -> RegulationGraphState:
        """
        回應生成節點：基於檢索結果生成專業回應

        回應要求：
        - 法規問題：引用具體條文並提供法律依據
        - 非法規問題：禮貌地說明系統僅能回答法規相關問題
        """
        # 取得狀態資訊
        query_type = state.get("query_type", "scenario")
        is_regulation_query = state.get("is_regulation_query", True)
        retrieval_results = state.get("retrieval_results", [])

        # 格式化檢索結果
        main_context = format_retrieval_results(retrieval_results)
        has_retrieval = bool(retrieval_results)

        # 構建系統提示詞
        if state.get("custom_system_prompt"):
            # 使用自訂提示詞作為基礎
            system_prompt = state["custom_system_prompt"]

            # 如果有檢索結果，附加到自訂提示詞後面
            if has_retrieval:
                system_prompt += f"\n\n---\n\n檢索到的條文：\n{main_context}"
        else:
            # 使用預設提示詞
            # 根據查詢類型調整 system prompt
            if not is_regulation_query:
                # 非法規問題：禮貌回覆
                system_prompt = """您好，我是專門用於法規查詢的 AI 助理。

很抱歉，我目前只能回答與法規相關的問題，例如：
- 查詢特定法規條文的內容
- 解釋法規條文的含義和適用情境
- 分析具體情境是否觸犯法規
- 比較不同條文之間的關係

如果您有任何法規相關的問題，歡迎隨時向我提問！"""
            else:
                # 法規問題：正常處理
                if query_type == "article_lookup":
                    task_instruction = "請提供該條文的完整內容，並說明其適用情境。"
                elif query_type == "scenario":
                    task_instruction = "請根據使用者描述的情境，說明適用哪些法規條文，並引用具體條文內容作為法律依據。"
                elif query_type == "comparison":
                    task_instruction = "請比較相關條文的內容，說明它們之間的關係或差異。"
                else:  # interpretation
                    task_instruction = "請解釋條文的含義，並說明其適用情境和實際應用。"

                system_prompt = f"""你是專業的法規諮詢專家。請基於檢索到的法規條文回答使用者的問題。

{task_instruction}

回答要求：
1. **引用條文**: 必須引用具體的條文（格式：根據【法規名稱】第X條...）
2. **語言風格**: 用清晰、專業但易懂的語言解釋
3. **檢索結果不足**: 如果檢索結果不足以回答，請誠實說明

---

**【重要】參考連結規範**：

在回答的最後，必須附上參考連結區塊：

**參考連結區塊**（必須）
   - 來源：從「檢索到的條文」中提取
   - 選擇邏輯：
     * 優先選擇在正文中**直接引用**的條文
     * 按條文編號**升序排列**（如第3條 → 第5條 → 第10條）
     * 最多列出 **5 條**
   - 格式：直接複製檢索結果中的【參考連結】區塊（保持 Markdown 格式不變）

**注意事項**：
- 不要憑空創造條文編號或連結
- 參考連結必須使用檢索結果中提供的完整 URL

---

回答格式範例：
根據您描述的情境，此行為違反動物保護法第10條...（正文內容）

【參考連結】
• [動物保護法 第3條](https://law.moj.gov.tw/...)
• [動物保護法 第10條](https://law.moj.gov.tw/...)

---

檢索到的條文：
{main_context}
"""
        logger.debug(f"[RegulationGraph] 系統最終提示詞: {system_prompt}")
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["messages"])
        messages.append(prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments")
        ))

        response = await llm.ainvoke(messages)

        logger.info(f"[RegulationGraph] 回應生成完成")

        return {
            **state,
            "final_response": extract_text_content(response.content),
            "cited_articles": []  # TODO: 從回應中提取引用的條文
        }

    # ==================== 條件路由函數 ====================

    def route_after_intent(state: RegulationGraphState) -> str:
        """
        根據意圖分析結果決定路由

        Returns:
            - "response_generation": 非法規問題，直接生成回應
            - "query_rewrite": 法規問題，進行查詢重構
        """
        if not state.get("is_regulation_query", True):
            logger.info("[RegulationGraph] 非法規問題，跳過檢索流程")
            return "response_generation"
        else:
            logger.info("[RegulationGraph] 法規問題，進入查詢重構")
            return "query_rewrite"

    # ==================== 構建 Graph ====================

    builder = StateGraph(RegulationGraphState)

    # 添加節點
    builder.add_node("intent_analysis", intent_analysis_node)
    builder.add_node("query_rewrite", query_rewrite_node)
    builder.add_node("regulation_search", regulation_search_node)
    # builder.add_node("reference_expansion", reference_expansion_node)  # 已停用
    builder.add_node("response_generation", response_generation_node)

    # 定義流程
    builder.add_edge(START, "intent_analysis")

    # 條件分支：根據是否為法規問題決定路徑
    builder.add_conditional_edges(
        "intent_analysis",
        route_after_intent,
        {
            "query_rewrite": "query_rewrite",
            "response_generation": "response_generation"
        }
    )

    builder.add_edge("query_rewrite", "regulation_search")
    builder.add_edge("regulation_search", "response_generation")
    # builder.add_edge("reference_expansion", "response_generation")  # 已停用
    builder.add_edge("response_generation", END)

    # 編譯
    graph = builder.compile()

    logger.info("[RegulationGraph] Graph 編譯完成")

    return graph


# ============ 主程式 (用於生成流程圖) ============
# 在backend目錄下使用模組方式執行
# uv run python -m app.modules.graphs.definitions.regulation_graph
if __name__ == "__main__":
    from pathlib import Path
    import sys
    import asyncio

    # Windows 平台修正
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 添加專案路徑 (backend 目錄)
    # regulation_graph.py 在: backend/app/modules/graphs/definitions/
    # 需要回到 backend/ 目錄
    backend_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(backend_root))

    from app.core.config import settings
    from app.llm.factory import LLMProviderFactory
    from app.core.resource_manager import get_resource_manager

    print("=" * 60)
    print("生成 Regulation Graph 流程圖...")
    print("=" * 60)

    async def main():
        # 初始化 ResourceManager (需要 RetrievalService)
        rm = get_resource_manager()
        print("[INFO] 正在初始化系統資源 (需要載入 AI 模型)...")
        await rm.initialize()

        # 建立 LLM Provider
        llm_provider = rm.llm_provider
        print(f"[OK] LLM Provider 初始化完成: {type(llm_provider).__name__}")

        # 建立 RetrievalService
        from app.modules.retrieval.service import RetrievalService
        retrieval_service = RetrievalService(hybrid_retriever=rm.hybrid_retriever)
        print("[OK] RetrievalService 建立完成")

        # 建立 Graph
        app = create_regulation_graph(settings, llm_provider, retrieval_service)
        print("[OK] Regulation Graph 建立完成")

        # 生成流程圖並儲存為 PNG
        output_path = Path(__file__).parent / "regulation_graph.png"

        try:
            # 取得 Mermaid 圖表並轉換為 PNG
            png_data = app.get_graph().draw_mermaid_png()

            with open(output_path, "wb") as f:
                f.write(png_data)

            print(f"[OK] 流程圖已生成: {output_path}")
            print("=" * 60)
        except Exception as e:
            print(f"[ERROR] 生成流程圖失敗: {e}")
            print("提示: 請確保已安裝 graphviz 和相關依賴")
            print("=" * 60)
            sys.exit(1)
        finally:
            # 清理資源
            await rm.cleanup()

    # 執行
    asyncio.run(main())