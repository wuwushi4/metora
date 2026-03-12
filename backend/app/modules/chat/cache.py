# -*- coding: utf-8 -*-
"""
聊天快取服務：管理 Session 和訊息的 Redis 快取
"""
import json
from typing import List, Dict, Optional, Any
from datetime import timedelta

from redis.asyncio import Redis


class ChatCacheService:
    """聊天快取服務：管理 Session 和訊息的 Redis 快取"""

    def __init__(self, redis_client: Redis, ttl_hours: int = 2):
        """
        初始化快取服務

        Args:
            redis_client: Redis 客戶端實例
            ttl_hours: 快取過期時間（小時），預設 2 小時
        """
        self.redis = redis_client
        self.ttl = timedelta(hours=ttl_hours)

    def _session_messages_key(self, session_id: str) -> str:
        """
        生成訊息快取鍵

        Args:
            session_id: Session ID

        Returns:
            Redis 鍵名
        """
        return f"chat:session:{session_id}:messages"

    def _session_metadata_key(self, session_id: str) -> str:
        """
        生成 metadata 快取鍵

        Args:
            session_id: Session ID

        Returns:
            Redis 鍵名
        """
        return f"chat:session:{session_id}:metadata"

    async def save_message(self, session_id: str, message: Dict[str, Any]):
        """
        儲存訊息到快取

        Args:
            session_id: Session ID
            message: 訊息字典，格式：
                {
                    "role": "user" | "assistant" | "system",
                    "content": "...",
                    "created_at": "..."
                }
        """
        key = self._session_messages_key(session_id)

        # 追加到 List 尾端
        await self.redis.rpush(key, json.dumps(message, ensure_ascii=False))

        # 設定 TTL（每次寫入都刷新）
        await self.redis.expire(key, self.ttl)

    async def get_recent_messages(
        self,
        session_id: str,
        turn_limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        從快取讀取最近的訊息

        Args:
            session_id: Session ID
            turn_limit: 輪數限制（None = 全部）
                       一輪 = user + assistant 兩條訊息

        Returns:
            訊息列表
        """
        key = self._session_messages_key(session_id)

        if turn_limit:
            # 取最近 N 輪（N*2 條訊息）
            count = turn_limit * 2
            messages_json = await self.redis.lrange(key, -count, -1)
        else:
            # 取全部
            messages_json = await self.redis.lrange(key, 0, -1)

        # 解析 JSON
        messages = []
        for msg_json in messages_json:
            try:
                msg = json.loads(msg_json)
                messages.append(msg)
            except json.JSONDecodeError:
                # 跳過無法解析的訊息
                continue

        return messages

    async def save_metadata(self, session_id: str, metadata: Dict[str, Any]):
        """
        儲存 Session metadata

        Args:
            session_id: Session ID
            metadata: metadata 字典，格式：
                {
                    "title": "...",
                    "graph_type": "...",
                    "collection_ids": [...],
                    "updated_at": "..."
                }
        """
        key = self._session_metadata_key(session_id)

        # 將所有值轉為字串（Redis Hash 只支援字串）
        string_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (list, dict)):
                string_metadata[k] = json.dumps(v, ensure_ascii=False)
            else:
                string_metadata[k] = str(v)

        await self.redis.hset(key, mapping=string_metadata)
        await self.redis.expire(key, self.ttl)

    async def get_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        讀取 Session metadata

        Args:
            session_id: Session ID

        Returns:
            metadata 字典
        """
        key = self._session_metadata_key(session_id)
        raw_metadata = await self.redis.hgetall(key)

        # 解析 JSON 字串
        metadata = {}
        for k, v in raw_metadata.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v

            # 嘗試解析 JSON
            try:
                metadata[k_str] = json.loads(v_str)
            except (json.JSONDecodeError, TypeError):
                # 不是 JSON，保持原樣
                metadata[k_str] = v_str

        return metadata

    async def delete_session(self, session_id: str):
        """
        刪除 Session 的所有快取

        Args:
            session_id: Session ID
        """
        await self.redis.delete(
            self._session_messages_key(session_id),
            self._session_metadata_key(session_id)
        )

    async def refresh_ttl(self, session_id: str):
        """
        刷新 Session 的 TTL

        Args:
            session_id: Session ID
        """
        await self.redis.expire(self._session_messages_key(session_id), self.ttl)
        await self.redis.expire(self._session_metadata_key(session_id), self.ttl)

    async def get_message_count(self, session_id: str) -> int:
        """
        取得 Session 的訊息數量

        Args:
            session_id: Session ID

        Returns:
            訊息數量
        """
        key = self._session_messages_key(session_id)
        count = await self.redis.llen(key)
        return count
