"""SSE 压测：首 token 延迟（TTFT）/ P50 / P95 / P99 / 错误率。

用法（项目根目录，dev 鉴权）：
    python scripts/load_test.py --concurrency 5 --requests 10
JWT 鉴权：
    python scripts/load_test.py --token <bearer-token>
"""

import argparse
import asyncio
import json
import statistics
import time

import httpx


async def one_request(client: httpx.AsyncClient, url: str, headers: dict,
                      payload: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        start = time.perf_counter()
        first_delta = None
        chars = 0
        status = None
        try:
            async with client.stream("POST", url, headers=headers,
                                     json=payload, timeout=120.0) as response:
                status = response.status_code
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = json.loads(line[5:].strip())
                    content = data.get("content")
                    if content:
                        if first_delta is None:
                            first_delta = time.perf_counter() - start
                        chars += len(content)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False, "status": status, "error": str(exc),
                "ttft": None, "elapsed": time.perf_counter() - start, "chars": 0,
            }
        return {
            "ok": status == 200, "status": status, "error": "",
            "ttft": first_delta,
            "elapsed": time.perf_counter() - start,
            "chars": chars,
        }


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((p / 100.0) * (len(ordered) - 1))))
    return ordered[index]


async def main() -> int:
    parser = argparse.ArgumentParser(description="SSE 压测")
    parser.add_argument("--url", default="http://127.0.0.1:8080/api/chat/stream")
    parser.add_argument("--user", type=int, default=1001)
    parser.add_argument("--token", default="")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--message", default="我买的耳机发货了吗")
    parser.add_argument("--scene", default="order_detail")
    args = parser.parse_args()

    headers = {"Content-Type": "application/json"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"
    else:
        headers["X-Debug-User-Id"] = str(args.user)
    payload = {"message": args.message, "scene": args.scene}

    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            one_request(client, args.url, headers, payload, semaphore)
            for _ in range(max(1, args.requests))
        ])

    ok = [item for item in results if item["ok"]]
    ttft = [item["ttft"] for item in ok if item["ttft"] is not None]
    elapsed = [item["elapsed"] for item in ok]
    error_count = len(results) - len(ok)

    print("# SSE 压测结果")
    print()
    print(f"- 请求数：{len(results)}，并发：{args.concurrency}")
    print(f"- 成功：{len(ok)}，失败：{error_count}，错误率：{error_count / len(results):.1%}")
    if ttft:
        print(f"- TTFT 平均值：{statistics.mean(ttft) * 1000:.0f} ms")
        print(f"- TTFT P50/P95/P99：{percentile(ttft, 50) * 1000:.0f} / "
              f"{percentile(ttft, 95) * 1000:.0f} / {percentile(ttft, 99) * 1000:.0f} ms")
    if elapsed:
        print(f"- 总耗时 P50/P95：{percentile(elapsed, 50):.2f} / "
              f"{percentile(elapsed, 95):.2f} s")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
