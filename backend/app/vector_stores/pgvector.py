# -*- coding: utf-8 -*-
"""
PGVector 向量資料庫實作

實作 BaseVectorStore 抽象介面，提供 PostgreSQL + pgvector 後端支援
使用現有的 PostgreSQL 連線配置，將向量資料存儲在同一資料庫中
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.vector_stores.base import (
    BaseCollection,
    BaseVectorStore,
    GetResult,
    QueryResult,
)


class PGVectorCollection(BaseCollection):
    """
    PGVector Collection 實作

    每個 Collection 對應一個 PostgreSQL 資料表
    資料表結構:
    - id: VARCHAR PRIMARY KEY
    - embedding: vector(dim)
    - document: TEXT
    - metadata: JSONB
    """

    def __init__(
        self,
        engine: AsyncEngine,
        name: str,
        table_name: str,
        embedding_dim: int,
        distance_metric: str = "cosine",
    ):
        self._engine = engine
        self._name = name
        self._table_name = table_name
        self._embedding_dim = embedding_dim
        self._distance_metric = distance_metric

    @property
    def name(self) -> str:
        return self._name

    def _get_distance_operator(self) -> str:
        """根據距離度量類型返回對應的 pgvector 運算子"""
        operators = {
            "cosine": "<=>",  # Cosine distance
            "l2": "<->",  # Euclidean distance
            "ip": "<#>",  # Inner product (負值，需要取負)
        }
        return operators.get(self._distance_metric, "<=>")

    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """新增向量到集合"""
        if not ids:
            return

        async with self._engine.begin() as conn:
            # 使用 INSERT ... ON CONFLICT 處理重複 ID
            for doc_id, embedding, document, metadata in zip(
                ids, embeddings, documents, metadatas
            ):
                # 將 embedding 轉換為 pgvector 格式
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                metadata_json = json.dumps(metadata, ensure_ascii=False)

                # 使用 CAST 替代 :: 類型轉換，避免 SQLAlchemy text() 解析問題
                await conn.execute(
                    text(f"""
                        INSERT INTO {self._table_name} (id, embedding, document, metadata)
                        VALUES (:id, CAST(:embedding AS vector), :document, CAST(:metadata AS jsonb))
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            document = EXCLUDED.document,
                            metadata = EXCLUDED.metadata
                    """),
                    {
                        "id": doc_id,
                        "embedding": embedding_str,
                        "document": document,
                        "metadata": metadata_json,
                    },
                )

    async def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> QueryResult:
        """向量相似度查詢"""
        if include is None:
            include = ["documents", "metadatas", "distances"]

        all_ids: List[List[str]] = []
        all_documents: List[List[str]] = []
        all_metadatas: List[List[Dict[str, Any]]] = []
        all_distances: List[List[float]] = []

        operator = self._get_distance_operator()

        async with self._engine.connect() as conn:
            for query_embedding in query_embeddings:
                embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

                # 構建 WHERE 子句
                where_clause, params = self._build_where_clause(where)
                params["query_embedding"] = embedding_str
                params["n_results"] = n_results

                # 構建查詢（使用 CAST 替代 :: 類型轉換）
                query = f"""
                    SELECT 
                        id,
                        document,
                        metadata,
                        embedding {operator} CAST(:query_embedding AS vector) AS distance
                    FROM {self._table_name}
                    {where_clause}
                    ORDER BY embedding {operator} CAST(:query_embedding AS vector)
                    LIMIT :n_results
                """

                result = await conn.execute(text(query), params)
                rows = result.fetchall()

                batch_ids = []
                batch_documents = []
                batch_metadatas = []
                batch_distances = []

                for row in rows:
                    batch_ids.append(row[0])
                    if "documents" in include:
                        batch_documents.append(row[1])
                    if "metadatas" in include:
                        batch_metadatas.append(row[2] if row[2] else {})
                    if "distances" in include:
                        # Inner product 需要取負值轉換
                        distance = float(row[3])
                        if self._distance_metric == "ip":
                            distance = -distance
                        batch_distances.append(distance)

                all_ids.append(batch_ids)
                if "documents" in include:
                    all_documents.append(batch_documents)
                if "metadatas" in include:
                    all_metadatas.append(batch_metadatas)
                if "distances" in include:
                    all_distances.append(batch_distances)

        return QueryResult(
            ids=all_ids,
            documents=all_documents if "documents" in include else None,
            metadatas=all_metadatas if "metadatas" in include else None,
            distances=all_distances if "distances" in include else None,
        )

    async def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> GetResult:
        """直接獲取文檔（非向量查詢）"""
        if include is None:
            include = ["documents", "metadatas"]

        async with self._engine.connect() as conn:
            # 構建 WHERE 子句
            conditions = []
            params: Dict[str, Any] = {}

            if ids:
                conditions.append("id = ANY(:ids)")
                params["ids"] = ids

            if where:
                where_clause, where_params = self._build_where_clause(where, prefix="w_")
                if where_clause:
                    # 移除 "WHERE " 前綴
                    conditions.append(where_clause.replace("WHERE ", ""))
                    params.update(where_params)

            where_sql = ""
            if conditions:
                where_sql = "WHERE " + " AND ".join(conditions)

            query = f"""
                SELECT id, document, metadata
                FROM {self._table_name}
                {where_sql}
            """

            result = await conn.execute(text(query), params)
            rows = result.fetchall()

            result_ids = []
            result_documents = []
            result_metadatas = []

            for row in rows:
                result_ids.append(row[0])
                if "documents" in include:
                    result_documents.append(row[1])
                if "metadatas" in include:
                    result_metadatas.append(row[2] if row[2] else {})

        return GetResult(
            ids=result_ids,
            documents=result_documents if "documents" in include else None,
            metadatas=result_metadatas if "metadatas" in include else None,
        )

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """刪除文檔"""
        async with self._engine.begin() as conn:
            conditions = []
            params: Dict[str, Any] = {}

            if ids:
                conditions.append("id = ANY(:ids)")
                params["ids"] = ids

            if where:
                where_clause, where_params = self._build_where_clause(where)
                if where_clause:
                    conditions.append(where_clause.replace("WHERE ", ""))
                    params.update(where_params)

            if not conditions:
                # 防止誤刪全部資料
                logger.warning("delete() 未指定條件，跳過刪除操作")
                return

            where_sql = "WHERE " + " AND ".join(conditions)

            await conn.execute(
                text(f"DELETE FROM {self._table_name} {where_sql}"),
                params,
            )

    async def count(self) -> int:
        """取得文檔數量"""
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {self._table_name}")
            )
            row = result.fetchone()
            return row[0] if row else 0

    def _build_where_clause(
        self,
        where: Optional[Dict[str, Any]],
        prefix: str = "",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        將 ChromaDB 風格的 where 條件轉換為 SQL WHERE 子句

        支援的條件格式:
        - {"field": value}  -> metadata->>'field' = value
        - {"field": {"$eq": value}}  -> metadata->>'field' = value
        - {"$and": [...]}  -> (... AND ...)
        - {"$or": [...]}  -> (... OR ...)
        """
        if not where:
            return "", {}

        params: Dict[str, Any] = {}
        param_counter = [0]

        def get_param_name() -> str:
            param_counter[0] += 1
            return f"{prefix}p{param_counter[0]}"

        def process_condition(cond: Dict[str, Any]) -> str:
            conditions = []

            for key, value in cond.items():
                if key == "$and":
                    sub_conditions = [process_condition(c) for c in value]
                    conditions.append("(" + " AND ".join(sub_conditions) + ")")
                elif key == "$or":
                    sub_conditions = [process_condition(c) for c in value]
                    conditions.append("(" + " OR ".join(sub_conditions) + ")")
                elif isinstance(value, dict):
                    # 操作符格式: {"field": {"$eq": value}}
                    for op, val in value.items():
                        param_name = get_param_name()
                        if op == "$eq":
                            # 根據值的類型選擇適當的比較方式
                            if isinstance(val, (int, float)):
                                conditions.append(
                                    f"(metadata->>'{key}')::numeric = :{param_name}"
                                )
                            else:
                                conditions.append(
                                    f"metadata->>'{key}' = :{param_name}"
                                )
                            params[param_name] = val
                        elif op == "$ne":
                            conditions.append(
                                f"metadata->>'{key}' != :{param_name}"
                            )
                            params[param_name] = val
                        elif op == "$gt":
                            conditions.append(
                                f"(metadata->>'{key}')::numeric > :{param_name}"
                            )
                            params[param_name] = val
                        elif op == "$gte":
                            conditions.append(
                                f"(metadata->>'{key}')::numeric >= :{param_name}"
                            )
                            params[param_name] = val
                        elif op == "$lt":
                            conditions.append(
                                f"(metadata->>'{key}')::numeric < :{param_name}"
                            )
                            params[param_name] = val
                        elif op == "$lte":
                            conditions.append(
                                f"(metadata->>'{key}')::numeric <= :{param_name}"
                            )
                            params[param_name] = val
                        elif op == "$in":
                            conditions.append(
                                f"metadata->>'{key}' = ANY(:{param_name})"
                            )
                            params[param_name] = val
                        elif op == "$nin":
                            conditions.append(
                                f"metadata->>'{key}' != ALL(:{param_name})"
                            )
                            params[param_name] = val
                else:
                    # 簡單格式: {"field": value}
                    param_name = get_param_name()
                    if isinstance(value, (int, float)):
                        conditions.append(
                            f"(metadata->>'{key}')::numeric = :{param_name}"
                        )
                    else:
                        conditions.append(f"metadata->>'{key}' = :{param_name}")
                    params[param_name] = value

            return " AND ".join(conditions) if conditions else ""

        where_clause = process_condition(where)
        if where_clause:
            return f"WHERE {where_clause}", params
        return "", params


class PGVectorStore(BaseVectorStore):
    """
    PGVector 向量資料庫實作

    使用 PostgreSQL + pgvector 擴展進行向量存儲
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        table_prefix: Optional[str] = None,
        embedding_dim: Optional[int] = None,
        distance_metric: Optional[str] = None,
    ):
        """
        初始化 PGVector 向量資料庫

        Args:
            database_url: 資料庫連線字串，預設使用 settings.DATABASE_URL
            table_prefix: 資料表前綴，預設使用 settings.PGVECTOR_TABLE_PREFIX
            embedding_dim: 向量維度，預設使用 settings.PGVECTOR_EMBEDDING_DIM
            distance_metric: 距離度量，預設使用 settings.VECTOR_DISTANCE_METRIC
        """
        self._database_url = database_url or settings.DATABASE_URL
        self._table_prefix = table_prefix or getattr(
            settings, "PGVECTOR_TABLE_PREFIX", "vector_"
        )
        self._embedding_dim = embedding_dim or getattr(
            settings, "PGVECTOR_EMBEDDING_DIM", 1024
        )
        self._distance_metric = distance_metric or settings.VECTOR_DISTANCE_METRIC
        self._engine: Optional[AsyncEngine] = None
        self._collections_metadata: Dict[str, Dict[str, Any]] = {}

    def _get_table_name(self, collection_name: str) -> str:
        """取得 Collection 對應的資料表名稱"""
        # 清理名稱，只保留合法字元
        safe_name = "".join(
            c if c.isalnum() or c == "_" else "_" for c in collection_name
        )
        return f"{self._table_prefix}{safe_name}"

    async def initialize(self) -> None:
        """初始化 PGVector 連線"""
        if self._engine is not None:
            logger.warning("PGVector 已初始化，返回現有實例")
            return

        logger.info("正在初始化 PGVector...")
        logger.info(f"  - 資料表前綴: {self._table_prefix}")
        logger.info(f"  - 向量維度: {self._embedding_dim}")
        logger.info(f"  - 距離度量: {self._distance_metric}")

        try:
            # 建立連線引擎
            self._engine = create_async_engine(
                self._database_url,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
            )

            # 確保 pgvector 擴展已安裝
            async with self._engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # 載入現有 collections 的 metadata
            await self._load_collections_metadata()

            logger.info("✅ PGVector 已初始化")

        except Exception as e:
            logger.error(f"❌ PGVector 初始化失敗: {e}")
            raise

    async def close(self) -> None:
        """關閉 PGVector 連線"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.info("PGVector 連線已關閉")

    async def heartbeat(self) -> bool:
        """檢查連線狀態"""
        if self._engine is None:
            return False

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def _load_collections_metadata(self) -> None:
        """載入現有 collections 的 metadata"""
        if self._engine is None:
            return

        try:
            async with self._engine.connect() as conn:
                # 查詢所有以 table_prefix 開頭的資料表
                result = await conn.execute(
                    text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name LIKE :prefix
                    """),
                    {"prefix": f"{self._table_prefix}%"},
                )
                tables = result.fetchall()

                for (table_name,) in tables:
                    # 從資料表名稱還原 collection 名稱
                    collection_name = table_name[len(self._table_prefix) :]
                    self._collections_metadata[collection_name] = {
                        "table_name": table_name
                    }

        except Exception as e:
            logger.warning(f"載入 collections metadata 失敗: {e}")

    async def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BaseCollection:
        """取得或建立集合"""
        if self._engine is None:
            raise RuntimeError("PGVector 尚未初始化")

        table_name = self._get_table_name(name)

        # 檢查資料表是否存在，不存在則建立
        async with self._engine.begin() as conn:
            # 檢查資料表是否存在
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """),
                {"table_name": table_name},
            )
            exists = result.scalar()

            if not exists:
                # 建立資料表
                await conn.execute(
                    text(f"""
                        CREATE TABLE {table_name} (
                            id VARCHAR(512) PRIMARY KEY,
                            embedding vector({self._embedding_dim}),
                            document TEXT,
                            metadata JSONB
                        )
                    """)
                )

                # 建立向量索引（使用 HNSW 索引加速查詢）
                index_name = f"{table_name}_embedding_idx"
                if self._distance_metric == "cosine":
                    await conn.execute(
                        text(f"""
                            CREATE INDEX {index_name} ON {table_name} 
                            USING hnsw (embedding vector_cosine_ops)
                        """)
                    )
                elif self._distance_metric == "l2":
                    await conn.execute(
                        text(f"""
                            CREATE INDEX {index_name} ON {table_name} 
                            USING hnsw (embedding vector_l2_ops)
                        """)
                    )
                elif self._distance_metric == "ip":
                    await conn.execute(
                        text(f"""
                            CREATE INDEX {index_name} ON {table_name} 
                            USING hnsw (embedding vector_ip_ops)
                        """)
                    )

                # 建立 metadata JSONB 索引
                await conn.execute(
                    text(f"""
                        CREATE INDEX {table_name}_metadata_idx ON {table_name} 
                        USING gin (metadata)
                    """)
                )

                logger.info(f"已建立 PGVector 資料表: {table_name}")

        # 記錄 metadata
        self._collections_metadata[name] = {
            "table_name": table_name,
            **(metadata or {}),
        }

        return PGVectorCollection(
            engine=self._engine,
            name=name,
            table_name=table_name,
            embedding_dim=self._embedding_dim,
            distance_metric=self._distance_metric,
        )

    async def get_collection(self, name: str) -> BaseCollection:
        """取得現有集合"""
        if self._engine is None:
            raise RuntimeError("PGVector 尚未初始化")

        table_name = self._get_table_name(name)

        # 檢查資料表是否存在
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """),
                {"table_name": table_name},
            )
            exists = result.scalar()

            if not exists:
                raise ValueError(f"集合 '{name}' 不存在")

        return PGVectorCollection(
            engine=self._engine,
            name=name,
            table_name=table_name,
            embedding_dim=self._embedding_dim,
            distance_metric=self._distance_metric,
        )

    async def delete_collection(self, name: str) -> None:
        """刪除集合"""
        if self._engine is None:
            raise RuntimeError("PGVector 尚未初始化")

        table_name = self._get_table_name(name)

        async with self._engine.begin() as conn:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

        # 移除 metadata
        self._collections_metadata.pop(name, None)

        logger.info(f"已刪除 PGVector 資料表: {table_name}")

    async def list_collections(self) -> List[str]:
        """列出所有集合名稱"""
        if self._engine is None:
            raise RuntimeError("PGVector 尚未初始化")

        async with self._engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE :prefix
                """),
                {"prefix": f"{self._table_prefix}%"},
            )
            tables = result.fetchall()

        # 從資料表名稱還原 collection 名稱
        return [row[0][len(self._table_prefix) :] for row in tables]

