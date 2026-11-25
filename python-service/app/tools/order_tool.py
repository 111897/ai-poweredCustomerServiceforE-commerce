"""订单查询工具：调用 Java 内网只读接口（返回数据已脱敏）。"""

import httpx

from ..core.config import settings


async def query_orders(user_id: int, keyword: str | None = None,
                       trace_id: str | None = None) -> list[dict]:
    payload = {
        "userId": user_id,
        "days": settings.order_days,
        "keyword": keyword,
        "traceId": trace_id,
    }
    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.post(
            settings.java_internal_base_url.rstrip("/") + "/internal/orders/query",
            json=payload,
            headers={"X-Internal-Token": settings.internal_token},
        )
        response.raise_for_status()
        return response.json().get("orders", [])
