# -*- coding: utf-8 -*-
"""
法規工具函數

提供法規資料處理的通用工具，包括：
1. 條號正規化（中文數字 ↔ 阿拉伯數字）
2. 引用解析（"前條"、"第X條" → 絕對條號）
3. 階層路徑提取
"""
import re
from typing import Optional, List, Tuple, Dict


# 中文數字對照表
CHINESE_NUMBERS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000, '萬': 10000
}

ARABIC_TO_CHINESE = {
    0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
    5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
}


def chinese_to_arabic(chinese_num: str) -> Optional[int]:
    """
    將中文數字轉換為阿拉伯數字

    Args:
        chinese_num: 中文數字，如 "十", "二十", "一百"

    Returns:
        int: 阿拉伯數字，如果無法轉換則返回 None

    Examples:
        >>> chinese_to_arabic("十")
        10
        >>> chinese_to_arabic("二十三")
        23
        >>> chinese_to_arabic("一百")
        100
    """
    if not chinese_num:
        return None

    chinese_num = chinese_num.strip()
    if not chinese_num:
        return None

    # 直接數字返回
    if chinese_num.isdigit():
        return int(chinese_num)

    result = 0
    temp = 0
    unit = 1

    for char in reversed(chinese_num):
        if char not in CHINESE_NUMBERS:
            return None

        value = CHINESE_NUMBERS[char]

        if value >= 10:
            # 單位（十、百、千、萬）
            if value > unit:
                unit = value
            else:
                unit *= value

            if temp == 0:
                temp = 1
        else:
            # 數字
            temp = value

        if unit > 1:
            result += temp * unit
            temp = 0
            unit = 1

    result += temp
    return result if result > 0 else None


def arabic_to_chinese(num: int) -> str:
    """
    將阿拉伯數字轉換為中文數字

    Args:
        num: 阿拉伯數字

    Returns:
        str: 中文數字

    Examples:
        >>> arabic_to_chinese(10)
        '十'
        >>> arabic_to_chinese(23)
        '二十三'
        >>> arabic_to_chinese(100)
        '一百'
    """
    if num == 0:
        return '零'

    if num < 0:
        return '負' + arabic_to_chinese(-num)

    result = ''

    # 處理萬位
    if num >= 10000:
        wan = num // 10000
        if wan >= 10:
            result += arabic_to_chinese(wan // 10) + '十'
            if wan % 10 > 0:
                result += ARABIC_TO_CHINESE[wan % 10]
        else:
            result += ARABIC_TO_CHINESE[wan]
        result += '萬'
        num %= 10000
        if num > 0 and num < 1000:
            result += '零'

    # 處理千位
    if num >= 1000:
        qian = num // 1000
        result += ARABIC_TO_CHINESE[qian] + '千'
        num %= 1000
        if num > 0 and num < 100:
            result += '零'

    # 處理百位
    if num >= 100:
        bai = num // 100
        result += ARABIC_TO_CHINESE[bai] + '百'
        num %= 100
        if num > 0 and num < 10:
            result += '零'

    # 處理十位
    if num >= 10:
        shi = num // 10
        if result or shi > 1:  # 如果前面有數字或十位大於1
            result += ARABIC_TO_CHINESE[shi]
        result += '十'
        num %= 10

    # 處理個位
    if num > 0:
        result += ARABIC_TO_CHINESE[num]

    return result


def normalize_article_number(article_str: str) -> Optional[str]:
    """
    正規化條號，統一轉換為阿拉伯數字

    Args:
        article_str: 條號字串，如 "第10條", "第十條", "10", "十"

    Returns:
        str: 正規化的條號（純數字），如 "10", "2-1"

    Examples:
        >>> normalize_article_number("第10條")
        '10'
        >>> normalize_article_number("第十條")
        '10'
        >>> normalize_article_number("第2條之1")
        '2-1'
    """
    if not article_str:
        return None

    article_str = article_str.strip()

    # 移除"第"和"條"
    article_str = article_str.replace('第', '').replace('條', '').strip()

    # 處理"之"的情況（如：第2條之1 → 2-1）
    if '之' in article_str:
        parts = article_str.split('之')
        if len(parts) == 2:
            main_num = parts[0].strip()
            sub_num = parts[1].strip()

            # 轉換主條號
            if main_num.isdigit():
                main_arabic = main_num
            else:
                main_arabic = str(chinese_to_arabic(main_num))

            # 轉換分支號
            if sub_num.isdigit():
                sub_arabic = sub_num
            else:
                sub_arabic = str(chinese_to_arabic(sub_num))

            return f"{main_arabic}-{sub_arabic}"

    # 處理"-"的情況（如：2-1）
    if '-' in article_str:
        return article_str  # 已經是數字格式

    # 純數字
    if article_str.isdigit():
        return article_str

    # 中文數字
    arabic = chinese_to_arabic(article_str)
    return str(arabic) if arabic is not None else None


def format_article_display(article_num: str, use_chinese: bool = True) -> str:
    """
    格式化條號顯示

    Args:
        article_num: 條號（數字），如 "10", "2-1"
        use_chinese: 是否使用中文數字

    Returns:
        str: 格式化的條號，如 "第10條", "第十條"

    Examples:
        >>> format_article_display("10", use_chinese=False)
        '第10條'
        >>> format_article_display("10", use_chinese=True)
        '第十條'
        >>> format_article_display("2-1", use_chinese=True)
        '第2條之1'
    """
    if not article_num:
        return ""

    # 處理分支條文
    if '-' in article_num:
        parts = article_num.split('-')
        main_num = parts[0]
        sub_num = parts[1]

        if use_chinese:
            main_chinese = arabic_to_chinese(int(main_num))
            sub_chinese = arabic_to_chinese(int(sub_num))
            return f"第{main_chinese}條之{sub_chinese}"
        else:
            return f"第{main_num}條之{sub_num}"

    # 一般條文
    if use_chinese:
        chinese_num = arabic_to_chinese(int(article_num))
        return f"第{chinese_num}條"
    else:
        return f"第{article_num}條"


def parse_reference_text(text: str) -> List[str]:
    """
    從文本中提取引用文字

    Args:
        text: 條文內容

    Returns:
        List[str]: 引用文字列表，如 ["前條", "第2條", "第5條第1項"]

    Examples:
        >>> parse_reference_text("依前條規定...")
        ['前條']
        >>> parse_reference_text("依第2條及第3條規定...")
        ['第2條', '第3條']
    """
    if not text:
        return []

    references = []

    # 匹配 "前條", "前項", "前款"
    prev_patterns = [
        r'前條(?:第[一二三四五六七八九十\d]+項)?',
        r'前項(?:第[一二三四五六七八九十\d]+款)?',
        r'前款'
    ]

    for pattern in prev_patterns:
        matches = re.findall(pattern, text)
        references.extend(matches)

    # 匹配 "第X條", "第X條第Y項", "第X條第Y項第Z款"
    article_pattern = r'第[一二三四五六七八九十百千萬\d之\-]+條(?:第[一二三四五六七八九十\d]+項)?(?:第[一二三四五六七八九十\d]+款)?'
    matches = re.findall(article_pattern, text)
    references.extend(matches)

    # 去重並保持順序
    seen = set()
    unique_refs = []
    for ref in references:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)

    return unique_refs


def resolve_reference(
    ref_text: str,
    current_article_num: str,
    all_article_nums: List[str]
) -> Optional[str]:
    """
    解析引用文字為絕對條號

    Args:
        ref_text: 引用文字，如 "前條", "第10條"
        current_article_num: 當前條號
        all_article_nums: 所有條號列表（按順序）

    Returns:
        str: 絕對條號，如果無法解析則返回 None

    Examples:
        >>> resolve_reference("前條", "10", ["8", "9", "10", "11"])
        '9'
        >>> resolve_reference("第8條", "10", ["8", "9", "10", "11"])
        '8'
    """
    if not ref_text or not current_article_num:
        return None

    # 處理"前條"
    if ref_text.startswith('前條'):
        try:
            current_idx = all_article_nums.index(current_article_num)
            if current_idx > 0:
                return all_article_nums[current_idx - 1]
        except (ValueError, IndexError):
            return None

    # 處理"第X條"
    if ref_text.startswith('第') and '條' in ref_text:
        # 提取條號部分
        article_part = ref_text.split('條')[0].replace('第', '')
        normalized = normalize_article_number(article_part)
        if normalized in all_article_nums:
            return normalized

    return None


def extract_hierarchy_path(
    chapter_num: str,
    chapter_name: str,
    article_num: str,
    use_chinese: bool = False
) -> str:
    """
    提取階層路徑

    Args:
        chapter_num: 章號
        chapter_name: 章名稱
        article_num: 條號
        use_chinese: 是否使用中文數字

    Returns:
        str: 階層路徑，如 "第一章 總則/第3條"

    Examples:
        >>> extract_hierarchy_path("1", "總則", "3", use_chinese=True)
        '第一章 總則/第三條'
        >>> extract_hierarchy_path("1", "總則", "3", use_chinese=False)
        '第1章 總則/第3條'
    """
    if use_chinese:
        chapter_display = f"第{arabic_to_chinese(int(chapter_num))}章"
        article_display = format_article_display(article_num, use_chinese=True)
    else:
        chapter_display = f"第{chapter_num}章"
        article_display = format_article_display(article_num, use_chinese=False)

    return f"{chapter_display} {chapter_name}/{article_display}"


def build_reference_graph(
    articles: List[Dict[str, any]],
    all_article_nums: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    """
    建立引用關係圖

    優先使用 JSON 中的 references 欄位（如果存在），否則動態解析 content。

    Args:
        articles: 條文列表，每個條文可能包含：
                 - article_num: 條文編號
                 - content: 條文內容
                 - references: 引用關係（可選，包含 forward_refs 和 backward_refs）
        all_article_nums: 所有條號列表（按順序）

    Returns:
        Dict: 引用關係圖，格式：
            {
                "3": {
                    "forward_refs": ["2"],  # 第3條引用的條文
                    "backward_refs": ["8"]  # 引用第3條的條文
                }
            }
    """
    from loguru import logger

    graph = {}

    # 初始化圖
    for article_num in all_article_nums:
        graph[article_num] = {
            "forward_refs": [],
            "backward_refs": []
        }

    # 統計：有多少條文使用了 JSON references vs 動態解析
    json_refs_count = 0
    dynamic_parse_count = 0

    # 建立引用關係
    for article in articles:
        current_num = article.get("article_num")
        if not current_num:
            continue

        # 優先使用 JSON 中的 references 欄位
        references = article.get("references")
        if references and isinstance(references, dict):
            forward_refs = references.get("forward_refs", [])
            backward_refs = references.get("backward_refs", [])

            # 確保引用列表是列表類型
            if isinstance(forward_refs, list):
                # 過濾無效的引用編號（必須在 all_article_nums 中）
                valid_forward_refs = [
                    ref for ref in forward_refs
                    if ref in all_article_nums
                ]
                graph[current_num]["forward_refs"] = valid_forward_refs

                if forward_refs and len(forward_refs) != len(valid_forward_refs):
                    invalid_refs = set(forward_refs) - set(valid_forward_refs)
                    logger.debug(
                        f"[build_reference_graph] 第 {current_num} 條的 forward_refs "
                        f"包含無效引用：{invalid_refs}"
                    )

            if isinstance(backward_refs, list):
                # 過濾無效的引用編號
                valid_backward_refs = [
                    ref for ref in backward_refs
                    if ref in all_article_nums
                ]
                graph[current_num]["backward_refs"] = valid_backward_refs

                if backward_refs and len(backward_refs) != len(valid_backward_refs):
                    invalid_refs = set(backward_refs) - set(valid_backward_refs)
                    logger.debug(
                        f"[build_reference_graph] 第 {current_num} 條的 backward_refs "
                        f"包含無效引用：{invalid_refs}"
                    )

            json_refs_count += 1
            logger.debug(
                f"[build_reference_graph] 第 {current_num} 條使用 JSON references: "
                f"forward={graph[current_num]['forward_refs']}, "
                f"backward={graph[current_num]['backward_refs']}"
            )
        else:
            # 如果沒有 references 欄位，則動態解析 content
            content = article.get("content", "")
            ref_texts = parse_reference_text(content)

            for ref_text in ref_texts:
                resolved_num = resolve_reference(ref_text, current_num, all_article_nums)
                if resolved_num and resolved_num != current_num:
                    # 前向引用：current_num 引用 resolved_num
                    if resolved_num not in graph[current_num]["forward_refs"]:
                        graph[current_num]["forward_refs"].append(resolved_num)

                    # 後向引用：resolved_num 被 current_num 引用
                    if current_num not in graph[resolved_num]["backward_refs"]:
                        graph[resolved_num]["backward_refs"].append(current_num)

            dynamic_parse_count += 1
            if ref_texts:
                logger.debug(
                    f"[build_reference_graph] 第 {current_num} 條動態解析 content，"
                    f"找到引用：{graph[current_num]['forward_refs']}"
                )

    # 統計報告
    logger.info(
        f"[build_reference_graph] 引用關係建立完成：共 {len(all_article_nums)} 條，"
        f"使用 JSON references: {json_refs_count} 條，動態解析: {dynamic_parse_count} 條"
    )

    return graph


def validate_article_structure(article: Dict[str, any]) -> Tuple[bool, Optional[str]]:
    """
    驗證條文結構是否完整

    Args:
        article: 條文字典

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)
    """
    required_fields = ["article_num", "article_display", "content"]

    for field in required_fields:
        if field not in article:
            return False, f"缺少必填欄位：{field}"

    if not article["article_num"]:
        return False, "條號不能為空"

    if not article["content"] or not article["content"].strip():
        return False, "條文內容不能為空"

    return True, None


def sort_article_nums(article_nums: List[str]) -> List[str]:
    """
    按條文編號升序排序

    排序規則：
    1. 主條號升序（數字比較，不是字串比較）
    2. 同主條號時，無分支在前，有分支在後
    3. 同主條號的分支，按分支號升序

    Args:
        article_nums: 條文編號列表，如 ["10", "3", "25-1", "3-1", "25"]

    Returns:
        List[str]: 排序後的條文編號列表，如 ["3", "3-1", "10", "25", "25-1"]

    Examples:
        >>> sort_article_nums(["10", "3", "25-1", "3-1", "25"])
        ["3", "3-1", "10", "25", "25-1"]

        >>> sort_article_nums(["5", "3-2", "3-1", "3", "10-1"])
        ["3", "3-1", "3-2", "5", "10-1"]

        >>> sort_article_nums(["1", "2", "3"])
        ["1", "2", "3"]
    """
    def parse_article_num(article_num: str) -> Tuple[int, int]:
        """
        解析條文編號為 (主條號, 分支號) 用於排序

        Args:
            article_num: 條文編號，如 "3", "25-1"

        Returns:
            Tuple[int, int]: (主條號, 分支號)
            - 主條號：條文的主編號（如 "3" 或 "25-1" 的主編號都是整數）
            - 分支號：如果有分支則為分支編號，否則為 0（無分支排在前面）
        """
        if "-" in article_num:
            # 分支條文，如 "25-1"
            parts = article_num.split("-")
            try:
                main_num = int(parts[0])
                sub_num = int(parts[1])
                return (main_num, sub_num)
            except (ValueError, IndexError):
                # 無法解析，返回一個大數字讓它排在後面
                return (999999, 999999)
        else:
            # 一般條文，如 "3"
            try:
                main_num = int(article_num)
                return (main_num, 0)  # 分支號為 0，排在同主條號的分支之前
            except ValueError:
                # 無法解析，返回一個大數字讓它排在後面
                return (999999, 0)

    # 使用解析函數作為排序鍵
    return sorted(article_nums, key=parse_article_num)
