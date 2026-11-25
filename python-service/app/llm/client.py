"""大模型客户端：OpenAI 兼容接口 + Mock 模式（本地模拟，便于无 Key 联调）。"""

import asyncio
import json
import logging
from typing import AsyncIterator

import httpx

from ..core.config import settings

log = logging.getLogger(__name__)


class LlmClient:
    def __init__(self):
        self.is_mock = settings.llm_mock

    # ------------------------------------------------------------------
    # 流式对话生成
    # ------------------------------------------------------------------
    async def stream_chat(self, messages: list[dict],
                          temperature: float | None = None) -> AsyncIterator[str]:
        if self.is_mock:
            async for chunk in self._mock_stream(messages):
                yield chunk
            return
        async for chunk in self._real_stream(messages, temperature):
            yield chunk

    async def _real_stream(self, messages, temperature):
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        obj = json.loads(data)
                        delta = obj["choices"][0].get("delta", {}).get("content") or ""
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta

    async def _mock_stream(self, messages):
        user_text = messages[-1]["content"] if messages else ""
        reply = self._mock_reply(user_text)
        for i in range(0, len(reply), 12):
            await asyncio.sleep(0.02)
            yield reply[i:i + 12]

    @staticmethod
    def _mock_reply(user_text: str) -> str:
        """模拟回答（>200 字以便验证分段；内容为通用话术）。"""
        text = user_text or ""
        if any(k in text for k in ("订单", "发货", "物流", "快递", "签收")):
            return (
                "您好，已经为您查询到相关订单信息。您的订单目前显示为已发货，物流正在运输途中，"
                "收货地址显示到区县一级，详细的街道与门牌信息已按隐私规则隐藏。"
                "您可以在订单详情页查看完整的物流轨迹与最新节点。"
                "如果物流长时间没有更新，建议您稍后再查看，或联系人工客服协助核实。"
                "本平台支持七天无理由退换货，商品如有质量问题可申请免费换货或退款，"
                "在订单页发起售后申请后，客服会在 24 小时内处理。"
                "如有其他与购物相关的问题，欢迎继续向我咨询。"
            )
        if any(k in text for k in ("价格", "多少钱", "规格", "库存", "有货")):
            return (
                "您好，关于商品的规格、价格与库存信息，以商品详情页展示为准。"
                "部分热门规格库存有限，建议您尽早下单以免缺货。"
                "商品支持七天无理由退换，若出现质量问题可以申请免费换货。"
                "物流方面，下单后一般在 48 小时内发出，偏远地区可能顺延。"
                "如果您能告诉我更具体的商品名称或型号，我可以帮您进一步查询价格和库存。"
                "如需售后处理，也可以在订单页直接发起申请。"
            )
        return (
            "您好，我是平台的购物客服助手，可以协助您查询订单、了解商品信息和售后政策。"
            "关于您咨询的问题，建议先查看商品详情页或订单页的相关信息。"
            "如果问题仍未解决，请告诉我具体的商品名称或订单相关细节，我会继续为您查询。"
            "平台支持七天无理由退换货，物流一般在 48 小时内发出。"
            "与购物无关的问题我无法处理，但欢迎您继续咨询商品、订单或售后相关的内容。"
        )

    # ------------------------------------------------------------------
    # 非流式（摘要 / 分类）
    # ------------------------------------------------------------------
    async def complete(self, messages: list[dict], max_tokens: int = 512) -> str:
        if self.is_mock:
            user_text = messages[-1]["content"] if messages else ""
            return user_text[: settings.compress_summary_max]
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            obj = response.json()
            return obj["choices"][0]["message"]["content"] or ""

    async def classify_ambiguity(self, message: str) -> bool:
        answer = await self.complete([
            {"role": "system",
             "content": (
                 "判断用户问题是否存在两种以上明显不同、且会导致答复内容明显不同的解读。"
                 "购物咨询（订单、物流、商品、售后）通常不算歧义。"
                 "只在确实无法确定用户意图时回答 yes，否则回答 no。只输出 yes 或 no。"
             )},
            {"role": "user", "content": message},
        ], max_tokens=8)
        return "yes" in answer.strip().lower()
