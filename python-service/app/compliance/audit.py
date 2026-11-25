"""合规审计：命中记录写入独立 audit 日志（命中内容本身掩码）。"""

import logging

_audit_logger = logging.getLogger("aics.audit")


def record(user_id, session_id: str, direction: str, rule_type: str,
           hits: list[str], action: str, trace_id: str | None = None) -> None:
    masked = ["*" * min(len(h), 8) for h in (hits or [])]
    _audit_logger.warning(
        "audit user=%s session=%s direction=%s rule=%s action=%s hits=%s trace=%s",
        user_id, session_id, direction, rule_type, action, masked, trace_id,
    )
