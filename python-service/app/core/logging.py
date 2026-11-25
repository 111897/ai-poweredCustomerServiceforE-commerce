"""结构化日志（JSON 行）+ 独立审计文件（轮转）。

敏感字段由调用方传入前已掩码，此处不落明文。
"""

import json
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import settings

_EXTRA_FIELDS = ("trace_id", "session_id", "user_id", "direction", "rule_type")
log = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _setup_audit_file() -> None:
    audit = logging.getLogger("aics.audit")
    if any(isinstance(h, RotatingFileHandler) for h in audit.handlers):
        return
    try:
        path = Path(settings.audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            path,
            maxBytes=settings.audit_log_max_bytes,
            backupCount=settings.audit_log_backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(JsonFormatter())
        audit.addHandler(handler)
        audit.setLevel(logging.INFO)
        audit.propagate = True  # 同时输出到控制台
    except Exception:
        log.warning("审计文件初始化失败，仅输出到控制台", exc_info=True)


def setup_logging() -> None:
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    _setup_audit_file()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
