"""会话短期记忆（FR-02 / FR-09）。

后端：
- memory：进程内（演示用，重启即丢），带 30 分钟滑动过期 + 机会式清理
- redis ：List 存消息 + Hash 存元信息 + String 存摘要，Lua 原子写入 + 滑动 TTL

可靠性：
- init_store() 启动时 ping Redis，失败立即回退进程内
- safe_* 包装在 Redis 中途故障时切换进程内，避免整轮对话 500
"""

import json
import logging
import time
from abc import ABC, abstractmethod

from ..core.config import settings

log = logging.getLogger(__name__)

MAX_MESSAGES = 400          # 单会话消息条数上限（约 200 轮）
SWEEP_EVERY = 100           # 每 N 次访问做一次过期清理
MAX_SESSIONS = 5000         # 进程内最大会话数


def _keys(user_id: int, session_id: str) -> tuple[str, str, str]:
    base = f"{user_id}:{session_id}"
    return f"chat:{base}", f"chat:meta:{base}", f"chat:sum:{base}"


class BaseMemoryStore(ABC):
    @abstractmethod
    async def append_turn(self, user_id, session_id, user_msg, assistant_msg): ...

    @abstractmethod
    async def history(self, user_id, session_id, limit: int = 20) -> list[dict]: ...

    @abstractmethod
    async def get_summary(self, user_id, session_id) -> str: ...

    @abstractmethod
    async def save_summary(self, user_id, session_id, summary: str): ...

    @abstractmethod
    async def get_meta(self, user_id, session_id) -> dict: ...

    @abstractmethod
    async def set_meta(self, user_id, session_id, meta: dict): ...

    @abstractmethod
    async def trim(self, user_id, session_id, keep_rounds: int): ...


class InProcessMemoryStore(BaseMemoryStore):
    def __init__(self):
        self._data: dict[str, dict] = {}
        self._ops = 0

    def _sweep(self) -> None:
        now = time.time()
        expired = [
            key for key, entry in self._data.items()
            if now - entry["last_active"] > settings.session_ttl_seconds
        ]
        for key in expired:
            self._data.pop(key, None)
        overflow = len(self._data) - MAX_SESSIONS
        if overflow > 0:
            ordered = sorted(
                self._data.items(), key=lambda item: item[1]["last_active"])
            for key, _ in ordered[:overflow]:
                self._data.pop(key, None)

    def _entry(self, user_id, session_id) -> dict:
        self._ops += 1
        if self._ops % SWEEP_EVERY == 0:
            self._sweep()

        key = f"{user_id}:{session_id}"
        now = time.time()
        entry = self._data.get(key)
        if entry and now - entry["last_active"] > settings.session_ttl_seconds:
            del self._data[key]
            entry = None
        if entry is None:
            entry = {
                "messages": [],
                "summary": "",
                "meta": {"round_count": 0, "last_compress_round": 0},
                "last_active": now,
            }
            self._data[key] = entry
        entry["last_active"] = now
        return entry

    async def append_turn(self, user_id, session_id, user_msg, assistant_msg):
        entry = self._entry(user_id, session_id)
        now = time.time()
        entry["messages"].append({"role": "user", "content": user_msg, "ts": now})
        entry["messages"].append({"role": "assistant", "content": assistant_msg, "ts": now})
        entry["messages"] = entry["messages"][-MAX_MESSAGES:]
        entry["meta"]["round_count"] += 1

    async def history(self, user_id, session_id, limit: int = 20) -> list[dict]:
        return self._entry(user_id, session_id)["messages"][-limit:]

    async def get_summary(self, user_id, session_id) -> str:
        return self._entry(user_id, session_id)["summary"]

    async def save_summary(self, user_id, session_id, summary: str):
        self._entry(user_id, session_id)["summary"] = summary

    async def get_meta(self, user_id, session_id) -> dict:
        return dict(self._entry(user_id, session_id)["meta"])

    async def set_meta(self, user_id, session_id, meta: dict):
        self._entry(user_id, session_id)["meta"] = dict(meta)

    async def trim(self, user_id, session_id, keep_rounds: int):
        entry = self._entry(user_id, session_id)
        entry["messages"] = entry["messages"][-(keep_rounds * 2):]


class RedisMemoryStore(BaseMemoryStore):
    APPEND_LUA = """
    local list_key = KEYS[1]
    local meta_key = KEYS[2]
    local msg = ARGV[1]
    local ttl = tonumber(ARGV[2])
    local max_len = tonumber(ARGV[3])
    redis.call('RPUSH', list_key, msg)
    redis.call('LTRIM', list_key, -max_len, -1)
    redis.call('HSET', meta_key, 'last_active', ARGV[4])
    redis.call('HINCRBY', meta_key, 'round_count', 1)
    redis.call('EXPIRE', list_key, ttl)
    redis.call('EXPIRE', meta_key, ttl)
    return 1
    """

    def __init__(self):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=settings.redis_connect_timeout,
            socket_timeout=settings.redis_socket_timeout,
            health_check_interval=30,
        )
        self._append_script = self._redis.register_script(self.APPEND_LUA)

    async def ping(self) -> bool:
        return bool(await self._redis.ping())

    async def close(self) -> None:
        await self._redis.aclose()

    async def append_turn(self, user_id, session_id, user_msg, assistant_msg):
        list_key, meta_key, sum_key = _keys(user_id, session_id)
        now = str(time.time())
        for role, content in (("user", user_msg), ("assistant", assistant_msg)):
            message = json.dumps(
                {"role": role, "content": content, "ts": time.time()},
                ensure_ascii=False,
            )
            await self._append_script(
                keys=[list_key, meta_key],
                args=[message, settings.session_ttl_seconds, MAX_MESSAGES, now],
            )
        await self._redis.expire(sum_key, settings.session_ttl_seconds)

    async def history(self, user_id, session_id, limit: int = 20) -> list[dict]:
        list_key, _, _ = _keys(user_id, session_id)
        raw = await self._redis.lrange(list_key, -limit, -1)
        return [json.loads(item) for item in raw]

    async def get_summary(self, user_id, session_id) -> str:
        _, _, sum_key = _keys(user_id, session_id)
        return await self._redis.get(sum_key) or ""

    async def save_summary(self, user_id, session_id, summary: str):
        _, meta_key, sum_key = _keys(user_id, session_id)
        await self._redis.set(sum_key, summary, ex=settings.session_ttl_seconds)
        await self._redis.expire(meta_key, settings.session_ttl_seconds)

    async def get_meta(self, user_id, session_id) -> dict:
        _, meta_key, _ = _keys(user_id, session_id)
        data = await self._redis.hgetall(meta_key)
        return {
            "round_count": int(data.get("round_count", 0)),
            "last_compress_round": int(data.get("last_compress_round", 0)),
        }

    async def set_meta(self, user_id, session_id, meta: dict):
        _, meta_key, _ = _keys(user_id, session_id)
        await self._redis.hset(meta_key, mapping={
            "round_count": int(meta.get("round_count", 0)),
            "last_compress_round": int(meta.get("last_compress_round", 0)),
        })
        await self._redis.expire(meta_key, settings.session_ttl_seconds)

    async def trim(self, user_id, session_id, keep_rounds: int):
        list_key, _, _ = _keys(user_id, session_id)
        await self._redis.ltrim(list_key, -(keep_rounds * 2), -1)


_store: BaseMemoryStore | None = None


def _fallback_to_memory(reason: str) -> None:
    global _store
    if not isinstance(_store, InProcessMemoryStore):
        _store = InProcessMemoryStore()
        log.warning("会话记忆已切换到进程内（原因：%s）", reason)


async def init_store() -> BaseMemoryStore:
    """启动时初始化记忆后端：Redis 不可用则立即回退进程内。"""
    global _store
    if _store is not None:
        return _store

    if settings.memory_backend == "redis":
        candidate = None
        try:
            candidate = RedisMemoryStore()
            await candidate.ping()
            _store = candidate
            log.info("会话记忆后端：redis")
            return _store
        except Exception as exc:
            log.warning("Redis 不可用，回退进程内记忆: %s", exc)
            if candidate is not None:
                try:
                    await candidate.close()
                except Exception:
                    log.debug("关闭 Redis 连接失败", exc_info=True)
    else:
        _store = InProcessMemoryStore()
        log.info("会话记忆后端：memory")
        return _store

    _store = InProcessMemoryStore()
    log.info("会话记忆后端：memory（Redis 不可用）")
    return _store


async def close_store() -> None:
    global _store
    if isinstance(_store, RedisMemoryStore):
        try:
            await _store.close()
        except Exception:
            log.warning("关闭 Redis 连接失败", exc_info=True)
    _store = None


def get_store() -> BaseMemoryStore:
    global _store
    if _store is None:
        _store = InProcessMemoryStore()
        log.info("会话记忆后端：memory（未初始化）")
    return _store


async def safe_history(user_id, session_id, limit: int = 20) -> list[dict]:
    try:
        return await get_store().history(user_id, session_id, limit)
    except Exception as exc:
        log.warning("读取会话历史失败，降级为空历史: %s", exc)
        _fallback_to_memory("history")
        return []


async def safe_append_turn(user_id, session_id, user_msg, assistant_msg) -> None:
    try:
        await get_store().append_turn(user_id, session_id, user_msg, assistant_msg)
    except Exception as exc:
        log.warning("写入会话记忆失败，切换进程内: %s", exc)
        _fallback_to_memory("append_turn")
        try:
            await get_store().append_turn(user_id, session_id, user_msg, assistant_msg)
        except Exception:
            log.exception("进程内会话记忆写入失败")


async def safe_get_summary(user_id, session_id) -> str:
    try:
        return await get_store().get_summary(user_id, session_id)
    except Exception as exc:
        log.warning("读取会话摘要失败: %s", exc)
        _fallback_to_memory("get_summary")
        return ""


async def safe_save_summary(user_id, session_id, summary: str) -> None:
    try:
        await get_store().save_summary(user_id, session_id, summary)
    except Exception as exc:
        log.warning("保存会话摘要失败: %s", exc)
        _fallback_to_memory("save_summary")


async def safe_get_meta(user_id, session_id) -> dict:
    try:
        return await get_store().get_meta(user_id, session_id)
    except Exception as exc:
        log.warning("读取会话元信息失败: %s", exc)
        _fallback_to_memory("get_meta")
        return {"round_count": 0, "last_compress_round": 0}


async def safe_set_meta(user_id, session_id, meta: dict) -> None:
    try:
        await get_store().set_meta(user_id, session_id, meta)
    except Exception as exc:
        log.warning("保存会话元信息失败: %s", exc)
        _fallback_to_memory("set_meta")


async def safe_trim(user_id, session_id, keep_rounds: int) -> None:
    try:
        await get_store().trim(user_id, session_id, keep_rounds)
    except Exception as exc:
        log.warning("裁剪会话历史失败: %s", exc)
        _fallback_to_memory("trim")
