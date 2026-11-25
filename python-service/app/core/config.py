"""全局配置：从环境变量 / .env 读取，所有路径均为相对项目根的相对路径。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- Java 数据服务 ----
    java_base_url: str = "http://127.0.0.1:8080"
    # 内部数据接口独立端口（公网端口不暴露 /internal/**）
    java_internal_base_url: str = "http://127.0.0.1:8081"
    internal_token: str = ""
    order_days: int = 10

    # ---- 会话记忆 ----
    memory_backend: str = "memory"          # memory | redis
    redis_url: str = "redis://127.0.0.1:6379/0"
    redis_connect_timeout: float = 1.0
    redis_socket_timeout: float = 1.0
    session_ttl_seconds: int = 1800

    # ---- 知识库（相对项目根）----
    knowledge_faq_path: str = "./data/knowledge/faq"
    knowledge_product_path: str = "./data/knowledge/product"
    knowledge_banned_path: str = "./data/knowledge/banned"
    hot_reload_seconds: int = 60

    # ---- 向量库与 Embedding ----
    vector_store: str = "memory"            # memory | chroma
    embedding_provider: str = "hash"        # hash | sentence_transformers
    rag_top_k: int = 5
    rag_min_score: float = 0.75
    chunk_size: int = 500
    chunk_overlap: int = 100

    # ---- 大模型 ----
    llm_mock: bool = True
    llm_base_url: str = "https://api.example.com/v1"
    llm_api_key: str = ""
    llm_model: str = "your-model-name"
    temperature: float = 0.3

    # ---- 回答长度与分段 ----
    max_answer_chars: int = 200
    max_segments: int = 5
    segment_mode: str = "auto"              # auto | continue

    # ---- 上下文压缩 ----
    compress_threshold: int = 30
    compress_keep_rounds: int = 6
    compress_summary_max: int = 500

    # ---- 审计日志 ----
    audit_log_path: str = "./logs/audit.log"
    audit_log_max_bytes: int = 10 * 1024 * 1024
    audit_log_backup_count: int = 5


settings = Settings()
