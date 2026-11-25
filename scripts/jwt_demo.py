"""JWT 全链路演示：获取 dev-token → 带 Bearer 调用 SSE 对话。

前提：start-java-jwt.bat 已启动（AICS_AUTH_MODE=jwt + AICS_DEV_TOKEN_ENABLED=true）。
"""

import json
import sys

import httpx

BASE = "http://127.0.0.1:8080"


def main() -> int:
    with httpx.Client(timeout=30.0) as client:
        try:
            resp = client.post(BASE + "/api/auth/dev-token", json={"userId": 1001})
            resp.raise_for_status()
        except Exception as exc:
            print(f"[error] 获取 dev-token 失败：{exc}", file=sys.stderr)
            return 1

        token = resp.json().get("token", "")
        print(f"dev-token 获取成功，长度 {len(token)}，前 20 位：{token[:20]}...")

        try:
            with client.stream(
                "POST",
                BASE + "/api/chat/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "我买的耳机发货了吗", "scene": "order_detail"},
                timeout=120.0,
            ) as stream:
                print(f"HTTP {stream.status_code}")
                event = ""
                for line in stream.iter_lines():
                    if line.startswith("event:"):
                        event = line[6:].strip()
                        print(line)
                    elif line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        if event == "delta":
                            print("回答:", data.get("content", ""))
                        else:
                            print(line)
        except Exception as exc:
            print(f"[error] 调用对话接口失败：{exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
