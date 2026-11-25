import math
from datetime import datetime
from uuid import UUID

from kokogram_shared.clock import Clock
from redis.asyncio import Redis


class RedisPresenceStore:
    def __init__(self, redis: Redis, clock: Clock) -> None:
        self._redis = redis
        self._clock = clock

    def _conn_key(self, connection_id: str) -> str:
        return f"presence:conn:{connection_id}"

    def _conn_user_key(self, connection_id: str) -> str:
        return f"presence:conn_user:{connection_id}"

    def _user_conns_key(self, user_id: UUID | str) -> str:
        return f"presence:user:{user_id}:conns"

    @property
    def _expirations_key(self) -> str:
        return "presence:expirations"

    def _conn_subs_key(self, connection_id: str) -> str:
        return f"presence:conn:{connection_id}:subs"

    def _user_subs_key(self, user_id: UUID | str) -> str:
        return f"presence:user:{user_id}:subs"

    async def register_connection(
        self, connection_id: str, user_id: UUID, expires_at: datetime
    ) -> bool:
        user_key = self._user_conns_key(user_id)
        ttl = max(1, math.ceil((expires_at - self._clock.now()).total_seconds()))

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.set(self._conn_key(connection_id), str(user_id), ex=ttl)
            pipe.set(self._conn_user_key(connection_id), str(user_id))
            pipe.sadd(user_key, connection_id)
            pipe.scard(user_key)
            pipe.zadd(self._expirations_key, {connection_id: expires_at.timestamp()})
            results = await pipe.execute()

        sadd_added = results[2]
        total_conns = results[3]
        is_first = sadd_added == 1 and total_conns == 1
        return is_first

    async def remove_connection(self, connection_id: str) -> tuple[UUID | None, bool]:
        conn_key = self._conn_key(connection_id)
        conn_user_key = self._conn_user_key(connection_id)

        user_id_raw = await self._redis.get(conn_key)
        if user_id_raw is None:
            user_id_raw = await self._redis.get(conn_user_key)

        conn_subs_key = self._conn_subs_key(connection_id)
        subscribed_targets = await self._redis.smembers(conn_subs_key)
        if subscribed_targets:
            async with self._redis.pipeline(transaction=True) as pipe:
                for target_raw in subscribed_targets:
                    target_str = (
                        target_raw.decode("utf-8")
                        if isinstance(target_raw, bytes)
                        else str(target_raw)
                    )
                    pipe.srem(self._user_subs_key(target_str), connection_id)
                pipe.delete(conn_subs_key)
                await pipe.execute()

        if user_id_raw is None:
            await self._redis.zrem(self._expirations_key, connection_id)
            return None, False

        user_id_str = (
            user_id_raw.decode("utf-8") if isinstance(user_id_raw, bytes) else str(user_id_raw)
        )
        user_id = UUID(user_id_str)
        user_key = self._user_conns_key(user_id)

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.delete(conn_key)
            pipe.delete(conn_user_key)
            pipe.srem(user_key, connection_id)
            pipe.zrem(self._expirations_key, connection_id)
            pipe.scard(user_key)
            results = await pipe.execute()

        srem_removed = results[2]
        remaining_conns = results[4]
        is_last = srem_removed == 1 and remaining_conns == 0
        return user_id, is_last

    async def connection_exists(self, connection_id: str) -> bool:
        now_ts = self._clock.now().timestamp()
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.exists(self._conn_key(connection_id))
            pipe.zscore(self._expirations_key, connection_id)
            exists_raw, score = await pipe.execute()
        return bool(exists_raw) and score is not None and score > now_ts

    async def ping_connection(self, connection_id: str, expires_at: datetime) -> bool:
        if not await self.connection_exists(connection_id):
            return False

        ttl = max(1, math.ceil((expires_at - self._clock.now()).total_seconds()))
        extended = await self._redis.expire(self._conn_key(connection_id), ttl)
        if not extended:
            return False

        await self._redis.zadd(
            self._expirations_key,
            {connection_id: expires_at.timestamp()},
            xx=True,
        )
        return True

    async def get_expired_connections(self, now: datetime) -> list[str]:
        now_ts = now.timestamp()
        expired = await self._redis.zrange(self._expirations_key, "-inf", now_ts, byscore=True)
        result: list[str] = []
        for item in expired:
            conn_id = item.decode("utf-8") if isinstance(item, bytes) else str(item)
            result.append(conn_id)
        return result

    async def add_subscriptions(self, connection_id: str, target_user_ids: list[UUID]) -> None:
        if not target_user_ids:
            return
        conn_subs_key = self._conn_subs_key(connection_id)
        target_strs = list(dict.fromkeys(str(u) for u in target_user_ids))

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.sadd(conn_subs_key, *target_strs)
            for target_str in target_strs:
                pipe.sadd(self._user_subs_key(target_str), connection_id)
            await pipe.execute()

    async def remove_subscriptions(self, connection_id: str, target_user_ids: list[UUID]) -> None:
        if not target_user_ids:
            return
        conn_subs_key = self._conn_subs_key(connection_id)
        target_strs = list(dict.fromkeys(str(u) for u in target_user_ids))

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.srem(conn_subs_key, *target_strs)
            for target_str in target_strs:
                pipe.srem(self._user_subs_key(target_str), connection_id)
            await pipe.execute()

    async def get_user_statuses(self, user_ids: list[UUID]) -> dict[UUID, bool]:
        if not user_ids:
            return {}

        now_ts = self._clock.now().timestamp()
        unique_user_ids = list(dict.fromkeys(user_ids))

        async with self._redis.pipeline(transaction=False) as pipe:
            for u_id in unique_user_ids:
                pipe.smembers(self._user_conns_key(u_id))
            user_conns_results = await pipe.execute()

        user_to_conns: dict[UUID, list[str]] = {}
        all_conn_ids: set[str] = set()

        for u_id, raw_conns in zip(unique_user_ids, user_conns_results, strict=True):
            conn_list: list[str] = []
            for c_raw in raw_conns:
                c_id = c_raw.decode("utf-8") if isinstance(c_raw, bytes) else str(c_raw)
                conn_list.append(c_id)
                all_conn_ids.add(c_id)
            user_to_conns[u_id] = conn_list

        if not all_conn_ids:
            return {u_id: False for u_id in user_ids}

        all_conn_list = list(all_conn_ids)
        async with self._redis.pipeline(transaction=False) as pipe:
            for c_id in all_conn_list:
                pipe.zscore(self._expirations_key, c_id)
            scores = await pipe.execute()

        conn_scores: dict[str, float | None] = dict(zip(all_conn_list, scores, strict=True))

        result: dict[UUID, bool] = {}
        for u_id in user_ids:
            conns = user_to_conns.get(u_id, [])
            has_alive = any(
                (conn_scores.get(c_id) is not None and conn_scores[c_id] > now_ts) for c_id in conns
            )
            result[u_id] = has_alive

        return result

    async def get_subscribers_for_user(self, user_id: UUID) -> set[str]:
        members = await self._redis.smembers(self._user_subs_key(user_id))
        result: set[str] = set()
        for item in members:
            conn_id = item.decode("utf-8") if isinstance(item, bytes) else str(item)
            result.add(conn_id)
        return result
