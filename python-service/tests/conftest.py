"""测试环境隔离：不连接 Redis / 真实 LLM / MySQL。"""

import os

os.environ["MEMORY_BACKEND"] = "memory"
os.environ["LLM_MOCK"] = "true"
os.environ["INTERNAL_TOKEN"] = "test-internal-token"
os.environ["AUDIT_LOG_PATH"] = "./logs/test-audit.log"
