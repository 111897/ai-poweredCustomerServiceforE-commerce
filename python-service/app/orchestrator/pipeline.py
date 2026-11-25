"""主链路编排状态机：
RECEIVE → INPUT_GUARD → (INTENT) → RETRIEVE → (TOOL) → GENERATE →
OUTPUT_GUARD → SEGMENT → DONE

事件协议（所有文本输出）：
start → [warning] → segment → delta → segment_end → ... → done
"""

import asyncio
import logging
import re
import uuid
from typing import AsyncIterator

from ..compliance import ambiguity, audit
from ..compliance.detector import BannedDetector
from ..compress.summarizer import maybe_compress
from ..core.config import settings
from ..guard import out_of_scope
from ..guard.prompt import (
    AMBIGUOUS_TEXT, FALLBACK_TEXT, LIMIT_TEXT, OUT_OF_SCOPE_TEXT,
    REJECT_TEXT, SAFETY_TEXT, SYSTEM_PROMPT,
)
from ..llm.client import LlmClient
from ..memory.store import safe_append_turn, safe_get_summary, safe_history
from ..rag.manager import RagManager
from ..rag.router import route
from ..segmenter.splitter import Segmenter
from ..streaming.protocol import segment_frames
from ..streaming.sse import frame, ping
from ..tools import order_tool, product_tool

log = logging.getLogger(__name__)

_detector: BannedDetector | None = None
_rag: RagManager | None = None
_llm = LlmClient()

_ORDER_INTENT = ("订单", "发货", "物流", "快递", "签收", "我的单", "退款")
_PRODUCT_INTENT = ("价格", "多少钱", "规格", "库存", "有货", "颜色", "款式", "商品")
_FAQ_INTENT = ("政策", "规则", "售后", "换货", "保修", "怎么退")

# 查库用的关键词清洗：去掉提问用语，只保留商品名等有效词
_ORDER_NOISE = (
    "我的", "我买的", "买的", "请问", "帮我", "查一下", "查询", "看看",
    "订单", "发货", "物流", "快递", "签收", "退款", "到哪里", "到哪", "进度",
    "了", "吗", "呢", "？", "?", "，", ",", " ", "　",
)
_PRODUCT_NOISE = (
    "我的", "请问", "帮我", "查一下", "查询", "看看", "这个", "这款",
    "多少钱", "价格", "有货", "库存", "规格", "颜色", "款式", "商品",
    "了", "吗", "呢", "？", "?", "，", ",", " ", "　",
)


def _clean_keyword(message: str, noise: tuple[str, ...]) -> str:
    text = message or ""
    for word in noise:
        text = text.replace(word, " ")
    return re.sub(r"\s+", " ", text).strip()[:20]


def init_dependencies(rag: RagManager, detector: BannedDetector) -> None:
    global _rag, _detector
    _rag = rag
    _detector = detector


def _intent(message: str, scene: str | None = None) -> str:
    if scene == "order_detail":
        return "order"
    if scene == "product_detail":
        return "product"
    text = message or ""
    if any(k in text for k in _ORDER_INTENT):
        return "order"
    if any(k in text for k in _PRODUCT_INTENT):
        return "product"
    if any(k in text for k in _FAQ_INTENT):
        return "faq"
    return "faq"


async def process_stream(user_id: int, session_id: str | None, message: str,
                         scene: str | None, trace_id: str) -> AsyncIterator[str]:
    """对外入口：带 15 秒心跳的生产者-消费者包装。"""
    sid = session_id or str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    async def produce():
        try:
            async for item in _run(user_id, sid, message, scene, trace_id):
                await queue.put(item)
        except Exception:
            log.exception("对话处理异常 trace_id=%s", trace_id)
            await queue.put(frame("error", {"code": "E5001", "message": "内部错误，请稍后再试"}))
        finally:
            await queue.put(None)

    task = asyncio.create_task(produce())
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ping()
                continue
            if item is None:
                break
            yield item
    finally:
        if not task.done():
            task.cancel()


async def _run(user_id: int, session_id: str, message: str,
               scene: str | None, trace_id: str) -> AsyncIterator[str]:
    msg_id = "m-" + uuid.uuid4().hex[:12]
    yield frame("start", {"sessionId": session_id, "msgId": msg_id})

    def text_events(text: str, index: int = 1) -> list[str]:
        return segment_frames(index, text, settings.segment_mode)

    # ---- 1) 输入侧违禁词 ----
    hits = _detector.scan(message) if _detector else []
    if hits:
        audit.record(user_id, session_id, "input", "banned", hits, "blocked", trace_id)
        yield frame("warning", {"type": "banned", "message": REJECT_TEXT})
        for event in text_events(REJECT_TEXT):
            yield event
        yield frame("done", {"msgId": msg_id, "finishReason": "blocked"})
        return

    # ---- 2) 越界拦截 ----
    if out_of_scope.is_out_of_scope(message):
        audit.record(user_id, session_id, "input", "out_of_scope", [], "pulled_back", trace_id)
        yield frame("warning", {"type": "out_of_scope", "message": OUT_OF_SCOPE_TEXT})
        for event in text_events(OUT_OF_SCOPE_TEXT):
            yield event
        yield frame("done", {"msgId": msg_id, "finishReason": "blocked"})
        return

    # ---- 3) 歧义判定 ----
    history = await safe_history(user_id, session_id, limit=20)
    ambiguous, clarify = await ambiguity.judge(message, bool(history), _llm)
    if ambiguous:
        audit.record(user_id, session_id, "input", "ambiguous", [], "clarify", trace_id)
        text = clarify or AMBIGUOUS_TEXT
        yield frame("warning", {"type": "ambiguous", "message": text})
        for event in text_events(text):
            yield event
        yield frame("done", {"msgId": msg_id, "finishReason": "clarify"})
        return

    # ---- 4) 意图与 RAG 检索 ----
    intent = _intent(message, scene)
    rag_texts: list[str] = []
    if _rag is not None:
        try:
            collections = route(intent, message)
            rag_hits = _rag.search(message, collections)
            if not rag_hits and "product" in collections:
                rag_hits = _rag.search(message, ["faq"])
            rag_texts = [h["text"] for h in rag_hits]
        except Exception:
            log.warning("RAG 检索失败，降级为通用推理", exc_info=True)

    # ---- 5) 数据查询工具 ----
    data_text = ""
    try:
        if intent == "order":
            keyword = _clean_keyword(message, _ORDER_NOISE) or None
            orders = await order_tool.query_orders(user_id, keyword, trace_id)
            if orders:
                data_text = "订单查询结果：\n" + "\n".join(
                    f"- 订单号 {o.get('orderNoMasked')}：{o.get('productName')}，"
                    f"{o.get('shipStatus')}，位置：{o.get('logisticsLocation') or '暂无'}，"
                    f"收货地：{o.get('receiverArea') or '—'}"
                    for o in orders[:10])
            else:
                data_text = (
                    f"订单查询结果：用户近 {settings.order_days} 天内没有相关订单。")
        elif intent == "product":
            keyword = _clean_keyword(message, _PRODUCT_NOISE)
            products = await product_tool.search_products(keyword, trace_id)
            if products:
                data_text = "商品查询结果：\n" + "\n".join(
                    f"- {p.get('name')}（{p.get('spec') or '默认规格'}），"
                    f"价格 {p.get('price')}，{p.get('stockStatus')}"
                    for p in products[:10])
    except Exception:
        log.warning("数据查询失败，按无数据处理", exc_info=True)

    # ---- 6) 组装消息 ----
    summary = await safe_get_summary(user_id, session_id)
    context_parts: list[str] = []
    if summary:
        context_parts.append("【早期对话摘要】\n" + summary)
    if rag_texts:
        context_parts.append("【知识库参考】\n" + "\n---\n".join(rag_texts))
    if data_text:
        context_parts.append("【数据查询结果（已脱敏）】\n" + data_text)

    system_content = SYSTEM_PROMPT
    if context_parts:
        system_content += "\n\n" + "\n\n".join(context_parts)

    messages = [{"role": "system", "content": system_content}]
    for item in history[-10:]:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": message})

    # ---- 7) LLM 流式生成 + 输出合规 + 分段 ----
    segmenter = Segmenter(settings.max_answer_chars)
    full_answer = ""
    segment_index = 0
    stop_reason: str | None = None

    def handle_segment(seg: str) -> list[str]:
        nonlocal segment_index, full_answer, stop_reason
        events: list[str] = []
        seg_hits = _detector.scan(seg) if _detector else []
        if seg_hits:
            audit.record(user_id, session_id, "output", "banned", seg_hits,
                         "replaced", trace_id)
            segment_index += 1
            events.append(frame("warning", {"type": "banned", "message": SAFETY_TEXT}))
            events.extend(segment_frames(
                segment_index, SAFETY_TEXT, settings.segment_mode))
            full_answer += SAFETY_TEXT
            stop_reason = "blocked"
            return events

        segment_index += 1
        events.extend(segment_frames(segment_index, seg, settings.segment_mode))
        full_answer += seg

        if segment_index >= settings.max_segments:
            notice_index = segment_index + 1
            events.extend(segment_frames(
                notice_index, LIMIT_TEXT, settings.segment_mode))
            full_answer += LIMIT_TEXT
            stop_reason = "limit"
        return events

    try:
        async for token in _llm.stream_chat(messages, settings.temperature):
            for seg in segmenter.feed(token):
                for event in handle_segment(seg):
                    yield event
                if stop_reason:
                    break
            if stop_reason:
                break

        if not stop_reason:
            for seg in segmenter.flush():
                for event in handle_segment(seg):
                    yield event
                if stop_reason:
                    break
    except Exception:
        log.exception("LLM 生成失败 trace_id=%s", trace_id)
        if not full_answer:
            for event in segment_frames(1, FALLBACK_TEXT, settings.segment_mode):
                yield event
        yield frame("error", {"code": "E2001", "message": "AI 生成暂不可用，请稍后再试"})
        yield frame("done", {"msgId": msg_id, "finishReason": "error"})
        return

    # ---- 8) 写入短期记忆 ----
    await safe_append_turn(user_id, session_id, message,
                           full_answer or FALLBACK_TEXT)

    # ---- 9) 异步触发上下文压缩检查 ----
    asyncio.create_task(_safe_compress(user_id, session_id))

    yield frame("done", {"msgId": msg_id, "finishReason": stop_reason or "stop"})


async def _safe_compress(user_id, session_id: str) -> None:
    try:
        await maybe_compress(user_id, session_id, _llm)
    except Exception:
        log.exception("后台压缩任务失败")
