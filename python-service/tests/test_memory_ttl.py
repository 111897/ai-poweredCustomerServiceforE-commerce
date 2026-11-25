import pytest

from app.core.config import settings
from app.memory.store import InProcessMemoryStore


@pytest.mark.asyncio
async def test_session_expires(monkeypatch):
    monkeypatch.setattr(settings, "session_ttl_seconds", 1800)
    store = InProcessMemoryStore()
    await store.append_turn(1, "s1", "问题", "回答")

    assert len(await store.history(1, "s1")) == 2

    # 把 TTL 设为 -1，模拟会话过期
    monkeypatch.setattr(settings, "session_ttl_seconds", -1)
    assert await store.history(1, "s1") == []


@pytest.mark.asyncio
async def test_meta_and_summary(monkeypatch):
    monkeypatch.setattr(settings, "session_ttl_seconds", 1800)
    store = InProcessMemoryStore()
    await store.save_summary(1, "s2", "摘要")
    await store.set_meta(1, "s2", {"round_count": 3, "last_compress_round": 1})

    assert await store.get_summary(1, "s2") == "摘要"
    assert await store.get_meta(1, "s2") == {
        "round_count": 3, "last_compress_round": 1}
