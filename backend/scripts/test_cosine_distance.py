# -*- coding: utf-8 -*-
"""
Cosine Distance 測試工具

用途: 模擬 ChromaDB 的 Cosine Distance 計算，測試兩個文字之間的相似度
使用方法: python backend/scripts/test_cosine_distance.py "文字1" "文字2"
"""
import sys
from pathlib import Path
import asyncio

# 添加 backend 目錄到 Python 路徑
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import numpy as np
from app.models.embeddings import EmbeddingModel
from app.core.config import settings


def calculate_cosine_metrics(vec1: np.ndarray, vec2: np.ndarray) -> dict:
    """
    計算 Cosine 相關指標

    Args:
        vec1: 第一個向量
        vec2: 第二個向量

    Returns:
        包含各種指標的字典
    """
    # 確保向量是 numpy array
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # 1. Cosine Similarity (點積，因為向量已正規化)
    cosine_similarity = float(np.dot(vec1, vec2))

    # 2. Cosine Distance (ChromaDB 定義: 1.0 - similarity)
    cosine_distance = 1.0 - cosine_similarity

    # 3. 檢索 Score (系統中的分數轉換)
    retrieval_score = 1.0 - cosine_distance  # 等於 cosine_similarity

    return {
        "cosine_similarity": cosine_similarity,
        "cosine_distance": cosine_distance,
        "retrieval_score": retrieval_score,
    }


def check_threshold(score: float, threshold: float) -> tuple[bool, str]:
    """
    檢查分數是否通過閾值

    Args:
        score: 檢索分數
        threshold: 閾值

    Returns:
        (是否通過, 建議訊息)
    """
    passed = score >= threshold

    if passed:
        if score > 0.8:
            suggestion = "✅ 極高相關性，完全匹配或高度相似"
        elif score > 0.6:
            suggestion = "✅ 高相關性，內容高度相關"
        else:
            suggestion = "✅ 中等相關性，剛好通過閾值"
    else:
        diff = threshold - score
        if diff > 0.3:
            suggestion = f"❌ 相關性很低，與閾值差距 {diff:.3f}，可能需要優化查詢"
        elif diff > 0.1:
            suggestion = f"⚠️ 相關性偏低，與閾值差距 {diff:.3f}，建議降低閾值或改善查詢"
        else:
            suggestion = f"⚠️ 接近閾值，與閾值差距僅 {diff:.3f}，可考慮微調閾值"

    return passed, suggestion


def format_output(
    text1: str,
    text2: str,
    vec1: np.ndarray,
    vec2: np.ndarray,
    metrics: dict,
    threshold: float,
) -> str:
    """
    格式化輸出結果

    Args:
        text1: 第一個文字
        text2: 第二個文字
        vec1: 第一個向量
        vec2: 第二個向量
        metrics: 計算指標
        threshold: 系統閾值

    Returns:
        格式化的輸出字串
    """
    passed, suggestion = check_threshold(metrics["retrieval_score"], threshold)

    output = []
    output.append("=" * 70)
    output.append("Cosine Distance 測試工具".center(70))
    output.append("=" * 70)
    output.append("")

    output.append(f"【文字 1】")
    output.append(f"  {text1}")
    output.append("")
    output.append(f"【文字 2】")
    output.append(f"  {text2}")
    output.append("")

    output.append("─" * 70)
    output.append("【向量信息】")
    output.append(f"  - 嵌入模型: {settings.EMBEDDING_MODEL}")
    output.append(f"  - 向量維度: {len(vec1)}")
    output.append(f"  - 是否正規化: True")
    output.append(f"  - 設備: {settings.EMBEDDING_DEVICE}")
    output.append("")

    output.append("─" * 70)
    output.append("【計算結果】")
    output.append(
        f"  1. Cosine Similarity:        {metrics['cosine_similarity']:7.4f}  (範圍 [-1, 1])"
    )
    output.append(
        f"  2. Cosine Distance (ChromaDB): {metrics['cosine_distance']:7.4f}  (範圍 [0, 2])"
    )
    output.append(
        f"  3. 檢索 Score (1.0 - dist):   {metrics['retrieval_score']:7.4f}  (範圍 [-1, 1])"
    )
    output.append("")

    output.append("─" * 70)
    output.append("【閾值判斷】")
    output.append(f"  - 當前系統閾值: {threshold}")
    output.append(
        f"  - 是否通過閾值: {'✅ 是' if passed else '❌ 否'} ({metrics['retrieval_score']:.4f} {'≥' if passed else '<'} {threshold})"
    )
    output.append(f"  - 建議: {suggestion}")
    output.append("")

    output.append("=" * 70)

    return "\n".join(output)


def main():
    """主函數"""
    # 檢查命令行參數
    if len(sys.argv) != 3:
        print("❌ 錯誤: 請提供兩個文字參數")
        print("")
        print("使用方法:")
        print('  python backend/scripts/test_cosine_distance.py "文字1" "文字2"')
        print("")
        print("範例:")
        print(
            '  python backend/scripts/test_cosine_distance.py "What is the company policy?" "Our company was founded in 2020 and focuses on AI solutions."'
        )
        sys.exit(1)

    text1 = sys.argv[1]
    text2 = sys.argv[2]

    print("\n⏳ 正在載入 BGE 嵌入模型...")
    print(f"   模型: {settings.EMBEDDING_MODEL}")
    print(f"   設備: {settings.EMBEDDING_DEVICE}")

    # 初始化嵌入模型
    try:
        embedding_model = EmbeddingModel()
        embedding_model.load()
    except Exception as e:
        print(f"\n❌ 模型載入失敗: {e}")
        print("\n請確保:")
        print(f"  1. 模型已下載到: {settings.HUGGINGFACE_CACHE_DIR}")
        print(
            f"  2. 如果使用 CUDA，請確保 CUDA 可用或修改 .env 中的 EMBEDDING_DEVICE=cpu"
        )
        sys.exit(1)

    print("✅ 模型載入成功\n")

    print("⏳ 正在編碼文字為向量...")

    # 編碼文字
    try:
        # embeddings = embedding_model.encode([text1, text2])
        embeddings = asyncio.run(embedding_model.encode([text1, text2]))
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
    except Exception as e:
        print(f"\n❌ 文字編碼失敗: {e}")
        sys.exit(1)

    print("✅ 編碼完成\n")

    # 計算指標
    metrics = calculate_cosine_metrics(vec1, vec2)

    # 格式化輸出
    output = format_output(
        text1, text2, vec1, vec2, metrics, settings.VECTOR_SEARCH_SCORE_THRESHOLD
    )

    print(output)


if __name__ == "__main__":
    main()
