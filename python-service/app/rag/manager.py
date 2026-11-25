"""RAG 管理器：多子库加载、列头模板校验、热更新与检索入口。"""

import asyncio
import logging
from pathlib import Path

from ..core.config import settings
from .embedder import create_embedder
from .loader import load_xlsx
from .retriever import Retriever
from .schema_validator import validate_headers
from .splitter import row_to_text, split_text
from .templates import FAQ_REQUIRED, PRODUCT_REQUIRED
from .vector_store import create_store

log = logging.getLogger(__name__)

# 子库名 -> (配置属性名, 必填列)
_COLLECTIONS = {
    "faq": ("knowledge_faq_path", FAQ_REQUIRED),
    "product": ("knowledge_product_path", PRODUCT_REQUIRED),
}


class RagManager:
    def __init__(self):
        self.embedder = create_embedder(settings.embedding_provider)
        self.stores = {
            name: create_store(settings.vector_store, f"kc_{name}")
            for name in _COLLECTIONS
        }
        self.retriever = Retriever(
            self.embedder, self.stores, settings.rag_top_k, settings.rag_min_score)
        self._mtimes: dict[str, float] = {}
        self.ok_collections: set[str] = set()

    async def load_all(self) -> None:
        await asyncio.to_thread(self._load_all_sync)

    def _load_all_sync(self) -> None:
        for name, (attr, required) in _COLLECTIONS.items():
            self._load_one(name, getattr(settings, attr), required)

    def _load_one(self, name: str, dir_path: str, required: list[str]) -> None:
        path = Path(dir_path) / f"{name}.xlsx"
        if not path.exists():
            log.warning("知识库文件不存在: %s", path)
            self.ok_collections.discard(name)
            return
        try:
            headers, rows = load_xlsx(path)
            ok, missing = validate_headers(headers, required)
            if not ok:
                log.error("知识库 %s 列头不合规范，缺少必填列 %s，已拒载", name, missing)
                self.stores[name].add([], [], [], [])
                self.ok_collections.discard(name)
                return

            ids: list[str] = []
            texts: list[str] = []
            metas: list[dict] = []
            vectors = []
            for row_index, row in enumerate(rows):
                text = row_to_text(name, row)
                if not text.strip():
                    continue
                for chunk_index, chunk in enumerate(split_text(
                        text, settings.chunk_size, settings.chunk_overlap)):
                    ids.append(f"{name}-{row_index}-{chunk_index}")
                    texts.append(chunk)
                    metas.append({
                        "source_file": str(path),
                        "category": row.get("category", ""),
                        "updated_at": row.get("updated_at", ""),
                    })
                    vectors.append(self.embedder.embed(chunk))

            self.stores[name].add(ids, texts, metas, vectors)
            self.ok_collections.add(name)
            self._mtimes[name] = path.stat().st_mtime
            log.info("知识库 %s 已加载：%d 行 → %d 个分块", name, len(rows), len(ids))
        except Exception:
            log.exception("知识库 %s 加载失败", name)
            self.ok_collections.discard(name)

    async def hot_reload_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.hot_reload_seconds)
            await asyncio.to_thread(self._check_and_reload)

    def _check_and_reload(self) -> None:
        for name, (attr, required) in _COLLECTIONS.items():
            path = Path(getattr(settings, attr)) / f"{name}.xlsx"
            if not path.exists():
                continue
            mtime = path.stat().st_mtime
            if self._mtimes.get(name) != mtime:
                log.info("检测到 %s 变更，重建索引", name)
                self._load_one(name, getattr(settings, attr), required)

    def search(self, query: str, collections: list[str]) -> list[dict]:
        return self.retriever.search(query, collections)
