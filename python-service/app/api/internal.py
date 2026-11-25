"""内网接口：POST /internal/chat（SSE 流式），仅供 Java 网关调用。"""

import logging

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from ..core.config import settings
from ..orchestrator.pipeline import process_stream

log = logging.getLogger(__name__)
router = APIRouter()


class ChatIn(BaseModel):
    userId: int | None = Field(default=None, gt=0)
    sessionId: str | None = Field(
        default="", max_length=64, pattern=r"^[A-Za-z0-9_-]*$")
    message: str = Field(min_length=1, max_length=2000)
    scene: str | None = Field(default="", max_length=32)
    traceId: str | None = Field(default="", max_length=64)

    @field_validator("scene")
    @classmethod
    def _check_scene(cls, value: str | None) -> str:
        if value is None or value == "":
            return ""
        if value not in ("order_detail", "product_detail", "home"):
            raise ValueError("scene 非法")
        return value


@router.post("/internal/chat")
async def chat(
    body: ChatIn,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=401, detail="internal auth failed")
    if not body.message or len(body.message) > 2000:
        raise HTTPException(status_code=400, detail="invalid message")
    if body.userId is None:
        raise HTTPException(status_code=400, detail="userId missing")

    generator = process_stream(
        user_id=body.userId,
        session_id=body.sessionId or None,
        message=body.message,
        scene=body.scene or "",
        trace_id=body.traceId or "",
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
