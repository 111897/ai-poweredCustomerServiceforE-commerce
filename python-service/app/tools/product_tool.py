"""商品查询工具：调用 Java 内网只读接口（返回字段白名单）。"""

import httpx

from ..core.config import settings


async def search_products(keyword: str, trace_id: str | None = None) -> list[dict]:
    payload = {"keyword": keyword or "", "traceId": trace_id}
    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.post(
            settings.java_internal_base_url.rstrip("/") + "/internal/products/search",
            json=payload,
            headers={"X-Internal-Token": settings.internal_token},
        )
        response.raise_for_status()
        return response.json().get("products", [])
