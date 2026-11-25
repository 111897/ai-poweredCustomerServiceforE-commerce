"""SSE 事件协议：所有文本输出统一封装为 segment → delta → segment_end。"""

from .sse import frame


def segment_frames(index: int, text: str, mode: str) -> list[str]:
    """生成一个完整文本段的三帧事件。"""
    return [
        frame("segment", {"index": index, "total": "?", "mode": mode}),
        frame("delta", {"content": text}),
        frame("segment_end", {"index": index, "length": len(text)}),
    ]
