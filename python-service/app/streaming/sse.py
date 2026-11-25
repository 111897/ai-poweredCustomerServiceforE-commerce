"""SSE 帧编码。事件：start / segment / delta / segment_end / warning / done / error。"""

import json
from typing import Any


def frame(event: str, data: dict[str, Any] | None = None) -> str:
    payload = json.dumps(data or {}, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def ping() -> str:
    """心跳注释帧（客户端可忽略）。"""
    return ": ping\n\n"
