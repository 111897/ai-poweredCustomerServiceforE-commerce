"""Python AI 服务入口：启动时加载知识库/违禁词，并开启热更新任务。"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .api.internal import router as internal_router
from .compliance.detector import BannedDetector
from .core.config import settings
from .core.logging import setup_logging
from .memory.store import close_store, init_store
from .orchestrator.pipeline import init_dependencies
from .rag.manager import RagManager

setup_logging()
log = logging.getLogger(__name__)


async def _detector_hot_reload(detector: BannedDetector) -> None:
    path = Path(settings.knowledge_banned_path) / "banned.xlsx"
    last_mtime = 0.0
    while True:
        try:
            mtime = path.stat().st_mtime if path.exists() else 0.0
            if mtime and mtime != last_mtime:
                detector.load(settings.knowledge_banned_path)
                last_mtime = mtime
        except Exception:
            log.warning("违禁词热更新检查失败", exc_info=True)
        await asyncio.sleep(settings.hot_reload_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_store()
    rag = RagManager()
    await rag.load_all()
    detector = BannedDetector(settings.knowledge_banned_path)
    init_dependencies(rag, detector)

    reload_task = asyncio.create_task(rag.hot_reload_loop())
    detector_task = asyncio.create_task(_detector_hot_reload(detector))

    log.info(
        "AI 服务已启动（LLM_MOCK=%s, VECTOR_STORE=%s, EMBEDDING=%s, MEMORY=%s）",
        settings.llm_mock, settings.vector_store,
        settings.embedding_provider, settings.memory_backend,
    )
    try:
        yield
    finally:
        reload_task.cancel()
        detector_task.cancel()
        await close_store()


app = FastAPI(title="AICS Python AI Service", lifespan=lifespan)
app.include_router(internal_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
