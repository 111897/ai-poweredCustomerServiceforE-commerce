"""上下文压缩（FR-09）：每累计 30 题触发一次摘要，保留最近 6 轮原文；失败降级保留 10 轮。"""

import logging

from ..core.config import settings
from ..memory.store import (
    safe_get_meta, safe_history, safe_save_summary, safe_set_meta, safe_trim,
)

log = logging.getLogger(__name__)

SUMMARY_INSTRUCTION = (
    "将以下对话压缩为不超过 {max_chars} 字的摘要，保留用户诉求、涉及商品/订单的关键事实、"
    "尚未解决的问题；不得添加新信息。"
)


async def maybe_compress(user_id, session_id: str, llm) -> bool:
    meta = await safe_get_meta(user_id, session_id)
    round_count = int(meta.get("round_count", 0))
    last_round = int(meta.get("last_compress_round", 0))

    if round_count - last_round < settings.compress_threshold:
        return False

    try:
        history = await safe_history(user_id, session_id, limit=400)
        dialogue = "\n".join(
            f"{m['role']}: {m['content']}" for m in history)
        summary = await llm.complete([
            {"role": "system",
             "content": SUMMARY_INSTRUCTION.format(max_chars=settings.compress_summary_max)},
            {"role": "user", "content": dialogue[:6000]},
        ])
        summary = (summary or "").strip()[: settings.compress_summary_max]
        if not summary:
            raise ValueError("摘要为空")

        await safe_save_summary(user_id, session_id, summary)
        await safe_trim(user_id, session_id, settings.compress_keep_rounds)
        meta["last_compress_round"] = round_count
        await safe_set_meta(user_id, session_id, meta)
        log.info("会话压缩完成 user=%s session=%s round=%s", user_id, session_id, round_count)
        return True
    except Exception as exc:
        log.warning("摘要生成失败，降级为保留最近 10 轮: %s", exc)
        try:
            await safe_trim(user_id, session_id, 10)
            meta["last_compress_round"] = round_count
            await safe_set_meta(user_id, session_id, meta)
        except Exception:
            log.exception("压缩降级处理失败")
        return False
