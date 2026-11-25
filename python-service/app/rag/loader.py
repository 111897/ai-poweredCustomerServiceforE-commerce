"""xlsx 知识库解析（openpyxl）：首行为列头，一行一条记录。"""

import logging
from pathlib import Path

from openpyxl import load_workbook

from .schema_validator import canonical_header

log = logging.getLogger(__name__)


def load_xlsx(path: Path) -> tuple[list[str], list[dict]]:
    """
    :return: (规范化后的列头列表, 行记录列表[dict])
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        values = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()

    if not values:
        return [], []

    # 列头统一小写，避免 ID / Question 等写法导致取值 key 不一致
    raw_headers = [canonical_header(c) for c in values[0]]
    headers: list[str] = []
    seen: set[str] = set()
    for header in raw_headers:
        if header in seen:
            log.warning("知识库列头重复：%s，保留首个", header)
            continue
        seen.add(header)
        headers.append(header)

    rows: list[dict] = []
    for raw in values[1:]:
        if raw is None:
            continue
        if all(c is None or str(c).strip() == "" for c in raw):
            continue
        rows.append({
            headers[i]: (str(raw[i]).strip() if raw[i] is not None else "")
            for i in range(len(headers)) if i < len(raw)
        })
    return headers, rows
