# -*- coding: utf-8 -*-
"""
向量化輔助模組
處理 Embedding 生成和向量資料庫存儲的核心邏輯
"""
import json
from typing import List, Dict, Any

from loguru import logger

from app.models.embeddings import EmbeddingModel
from app.core.config import settings
from app.vector_stores.base import BaseVectorStore


async def vectorize_chunks(
    collection_id: int,
    collection_name: str,
    dataset_id: int,
    dataset_filename: str,
    chunks: List[Dict[str, Any]],
    embedding_model: EmbeddingModel,
    vector_store: BaseVectorStore
) -> None:
    """
    將 chunks 向量化並存入向量資料庫

    Args:
        collection_id: Collection ID
        collection_name: Collection 名稱（用於顯示）
        dataset_id: Dataset ID
        dataset_filename: Dataset 原始檔名
        chunks: 分塊結果（來自 chunker）
        embedding_model: Embedding 模型實例
        vector_store: 向量資料庫實例

    Raises:
        RuntimeError: 當向量化或向量資料庫操作失敗時
    """
    if len(chunks) == 0:
        logger.warning(f"Dataset {dataset_id} 沒有可向量化的分塊")
        return

    logger.info(f"開始向量化 Dataset {dataset_id}，共 {len(chunks)} 個分塊")

    # 1. 準備向量資料庫 Collection
    vector_collection_name = f"collection_{collection_id}"
    vector_collection = await vector_store.get_or_create_collection(
        name=vector_collection_name,
        metadata={
            "collection_id": collection_id,
            "collection_name": collection_name,
            "hnsw:space": settings.VECTOR_DISTANCE_METRIC,  # 明確指定距離度量 (cosine/l2/ip)
        }
    )

    # 2. 增強 metadata 並生成 Chunk ID
    enhanced_chunks = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        qa_id = metadata.get("qa_id")
        representation = metadata.get("representation")

        # 生成唯一 Chunk ID
        # 格式: c{collection_id}_d{dataset_id}_{qa_id}_{representation}
        if qa_id is not None:
            chunk_id = f"c{collection_id}_d{dataset_id}_{qa_id}_{representation}"
        else:
            # 若沒有 qa_id，使用 chunk_index
            chunk_index = metadata.get("chunk_index", 0)
            chunk_id = f"c{collection_id}_d{dataset_id}_idx{chunk_index}_{representation}"

        # 增強 metadata（展平巢狀字典以符合向量資料庫限制）
        enhanced_metadata = {
            "collection_id": collection_id,
            "collection_name": collection_name,
            "dataset_id": dataset_id,
            "dataset_filename": dataset_filename,
        }

        # 展平原有 metadata，過濾掉不支援的類型（dict, list）
        for key, value in metadata.items():
            if key in ["qa_metadata", "file_metadata"]:
                # 巢狀 metadata 展平為字串（JSON 序列化）
                if value:
                    enhanced_metadata[key] = json.dumps(value, ensure_ascii=False)
            elif key == "keywords":
                # list 轉換為逗號分隔的字串
                if isinstance(value, list):
                    enhanced_metadata[key] = ", ".join(str(item) for item in value)
                else:
                    enhanced_metadata[key] = str(value) if value is not None else None
            elif isinstance(value, (str, int, float, bool)) or value is None:
                # 支援的類型直接加入
                enhanced_metadata[key] = value
            elif isinstance(value, (dict, list)):
                # 其他巢狀結構轉為 JSON 字串
                enhanced_metadata[key] = json.dumps(value, ensure_ascii=False)
            else:
                # 其他類型轉為字串
                enhanced_metadata[key] = str(value)

        # 保留所有原始欄位（包含 type 和 vectorization_text）
        enhanced_chunk = {
            "id": chunk_id,
            "content": chunk["content"],
            "metadata": enhanced_metadata
        }

        # 保留 type 欄位（用於條件判斷）
        if "type" in chunk:
            enhanced_chunk["type"] = chunk["type"]

        # 保留 vectorization_text 欄位（用於向量編碼）
        if "vectorization_text" in chunk:
            enhanced_chunk["vectorization_text"] = chunk["vectorization_text"]

        enhanced_chunks.append(enhanced_chunk)

    # 3. 批次生成 Embeddings
    logger.info(f"開始生成向量，batch_size={settings.EMBEDDING_BATCH_SIZE}")

    all_ids = []
    all_embeddings = []
    all_documents = []
    all_metadatas = []

    batch_size = settings.EMBEDDING_BATCH_SIZE

    # DEBUG: 檢查第一個 chunk 的結構
    if len(enhanced_chunks) > 0:
        first_chunk = enhanced_chunks[0]
        logger.debug(f"[vectorization] 第一個 chunk 的欄位: {list(first_chunk.keys())}")
        logger.debug(f"[vectorization] type 欄位: {first_chunk.get('type', 'NOT_FOUND')}")
        logger.debug(f"[vectorization] 是否有 vectorization_text: {'vectorization_text' in first_chunk}")

    for i in range(0, len(enhanced_chunks), batch_size):
        batch = enhanced_chunks[i:i + batch_size]

        # 根據 chunk_type 選擇向量編碼來源
        batch_texts = []
        for chunk in batch:
            chunk_type = chunk.get("type", "")
            has_vectorization_text = "vectorization_text" in chunk

            # 情境分塊：優先使用 vectorization_text（純情境文字）
            if chunk_type == "regulation_scenario" and has_vectorization_text:
                text_to_encode = chunk["vectorization_text"]
                batch_texts.append(text_to_encode)
                logger.debug(
                    f"[vectorization] ✅ 情境分塊使用 vectorization_text: "
                    f"{text_to_encode[:50]}..."
                )
            else:
                # 其他分塊類型：使用 content 欄位
                text_to_encode = chunk["content"]
                batch_texts.append(text_to_encode)
                if chunk_type == "regulation_scenario":
                    logger.warning(
                        f"[vectorization] ⚠️ 情境分塊缺少 vectorization_text，"
                        f"使用 content（type={chunk_type}, has_field={has_vectorization_text}）"
                    )

        # 生成向量（新架構：EmbeddingModel.encode() 是異步方法）
        try:
            batch_embeddings = await embedding_model.encode(batch_texts)
        except Exception as e:
            logger.error(f"Embedding 生成失敗: {e}")
            raise RuntimeError(f"Embedding 生成失敗: {e}")

        # 收集資料
        for chunk, embedding in zip(batch, batch_embeddings):
            all_ids.append(chunk["id"])
            all_embeddings.append(embedding)
            all_documents.append(chunk["content"])
            all_metadatas.append(chunk["metadata"])

        logger.info(f"已生成 {len(all_embeddings)}/{len(enhanced_chunks)} 個向量")

    # 4. 批次插入向量資料庫（限制每批 1000 個）
    logger.info(f"開始插入向量到 collection '{vector_collection_name}'")

    vector_batch_size = 1000  # 批次插入限制
    for i in range(0, len(all_ids), vector_batch_size):
        batch_ids = all_ids[i:i + vector_batch_size]
        batch_embeddings = all_embeddings[i:i + vector_batch_size]
        batch_documents = all_documents[i:i + vector_batch_size]
        batch_metadatas = all_metadatas[i:i + vector_batch_size]

        try:
            await vector_collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas
            )
        except Exception as e:
            logger.error(f"向量資料庫插入失敗: {e}")
            raise RuntimeError(f"向量資料庫插入失敗: {e}")

        logger.info(f"已插入 {min(i + vector_batch_size, len(all_ids))}/{len(all_ids)} 個向量")

    logger.info(f"✅ Dataset {dataset_id} 向量化完成，共 {len(chunks)} 個分塊")


async def delete_dataset_vectors(
    dataset_id: int,
    collection_id: int
) -> None:
    """
    刪除特定 Dataset 的向量資料

    Args:
        dataset_id: Dataset ID
        collection_id: Collection ID

    說明:
        - 使用 metadata filter 刪除指定 Dataset 的所有向量
        - 不會刪除整個向量資料庫 Collection
    """
    from app.core.resource_manager import get_resource_manager

    try:
        resources = get_resource_manager()
        vector_store = resources.vector_store

        if vector_store is None:
            logger.warning("向量資料庫尚未初始化，跳過刪除")
            return

        vector_collection_name = f"collection_{collection_id}"

        # 檢查 Collection 是否存在
        collections = await vector_store.list_collections()
        if vector_collection_name not in collections:
            logger.info(f"向量資料庫 collection '{vector_collection_name}' 不存在，跳過刪除")
            return

        vector_collection = await vector_store.get_collection(name=vector_collection_name)

        # 使用 metadata filter 刪除
        await vector_collection.delete(
            where={"dataset_id": dataset_id}
        )

        logger.info(f"✅ 已刪除 Dataset {dataset_id} 的向量資料")

    except Exception as e:
        logger.error(f"刪除 Dataset {dataset_id} 向量資料失敗: {e}")
        # 不拋出異常，避免阻止資料庫記錄刪除
        pass


async def delete_collection_vectors(collection_id: int) -> None:
    """
    刪除整個 Collection 的向量資料

    Args:
        collection_id: Collection ID

    說明:
        - 直接刪除整個向量資料庫 Collection
        - 比逐個刪除 Dataset 更高效
    """
    from app.core.resource_manager import get_resource_manager

    try:
        resources = get_resource_manager()
        vector_store = resources.vector_store

        if vector_store is None:
            logger.warning("向量資料庫尚未初始化，跳過刪除")
            return

        vector_collection_name = f"collection_{collection_id}"

        # 檢查 Collection 是否存在
        collections = await vector_store.list_collections()
        if vector_collection_name not in collections:
            logger.info(f"向量資料庫 collection '{vector_collection_name}' 不存在，跳過刪除")
            return

        # 刪除整個 Collection
        await vector_store.delete_collection(name=vector_collection_name)

        logger.info(f"✅ 已刪除向量資料庫 collection '{vector_collection_name}'")

    except Exception as e:
        logger.error(f"刪除 Collection {collection_id} 向量資料失敗: {e}")
        # 不拋出異常，避免阻止資料庫記錄刪除
        pass
