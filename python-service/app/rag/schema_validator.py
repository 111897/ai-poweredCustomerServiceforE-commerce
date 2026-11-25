"""知识库列头模板校验（AC-12）：列头不符或缺少必填列 → 该子库拒载。"""


def canonical_header(value) -> str:
    """统一列头：去 BOM、去首尾空白、转小写。"""
    text = "" if value is None else str(value)
    return text.replace("﻿", "").strip().lower()


def validate_headers(headers: list[str], required: list[str]) -> tuple[bool, list[str]]:
    """
    :return: (是否通过, 缺失的必填列)
    """
    normalized = [canonical_header(h) for h in headers]
    missing = [r for r in required if r.lower() not in normalized]
    return len(missing) == 0, missing
