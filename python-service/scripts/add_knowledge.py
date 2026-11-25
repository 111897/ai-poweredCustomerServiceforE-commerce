"""知识库数据追加工具：把 JSON 记录写入对应 xlsx（保留列头，按主键去重）。

用法（在项目根目录执行）：
    python python-service/scripts/add_knowledge.py faq     --file data/knowledge/new/faq.json
    python python-service/scripts/add_knowledge.py product --file data/knowledge/new/product.json
    python python-service/scripts/add_knowledge.py banned  --file data/knowledge/new/banned.json

JSON 格式：对象数组，每项一条记录，字段名与 xlsx 列头一致。
主键规则：faq 用 id，product 用 product_id，banned 用 pattern；
主键已存在则覆盖该行，否则追加。写入后服务会在 60 秒内自动重建索引。
"""

import argparse
import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "knowledge"

KINDS = {
    "faq": {
        "file": BASE / "faq" / "faq.xlsx",
        "headers": ["id", "question", "answer", "category", "updated_at"],
        "required": ["id", "question", "answer", "category"],
        "key": "id",
    },
    "product": {
        "file": BASE / "product" / "product.xlsx",
        "headers": ["product_id", "name", "category", "spec",
                    "price", "stock_status", "selling_points", "updated_at"],
        "required": ["product_id", "name", "category", "price", "stock_status"],
        "key": "product_id",
    },
    "banned": {
        "file": BASE / "banned" / "banned.xlsx",
        "headers": ["pattern", "type", "note"],
        "required": ["pattern", "type"],
        "key": "pattern",
    },
}


def _norm(value) -> str:
    return "" if value is None else str(value).strip()


def _load_rows(path: Path, headers: list[str]) -> tuple[object, list[list]]:
    """返回 (workbook, 数据行列表)，文件不存在时新建。"""
    if not path.exists():
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "data"
        sheet.append(headers)
        return workbook, []

    workbook = load_workbook(path)
    sheet = workbook.active
    values = list(sheet.iter_rows(values_only=True))
    if not values:
        sheet.append(headers)
        return workbook, []
    return workbook, [list(row) for row in values[1:]]


def append_records(kind: str, records: list[dict]) -> tuple[int, int]:
    conf = KINDS[kind]
    path: Path = conf["file"]
    headers: list[str] = conf["headers"]
    required: list[str] = conf["required"]
    key: str = conf["key"]

    path.parent.mkdir(parents=True, exist_ok=True)
    workbook, rows = _load_rows(path, headers)
    sheet = workbook.active

    if not rows and sheet.max_row < 2:
        sheet.delete_rows(1, sheet.max_row)
        sheet.append(headers)

    # 建立主键 -> 数据行下标（rows 的 0 基下标）
    key_index = headers.index(key)
    key_to_index: dict[str, int] = {}
    for i, row in enumerate(rows):
        padded = row + [None] * (len(headers) - len(row))
        value = _norm(padded[key_index])
        if value:
            key_to_index[value] = i

    added = updated = 0
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"第 {number} 条记录不是 JSON 对象")

        missing = [c for c in required if not _norm(record.get(c))]
        if missing:
            raise ValueError(f"第 {number} 条记录缺少必填字段：{', '.join(missing)}")

        new_row = [record.get(header, "") for header in headers]
        key_value = _norm(record.get(key))

        if key_value and key_value in key_to_index:
            rows[key_to_index[key_value]] = new_row
            updated += 1
        else:
            rows.append(new_row)
            if key_value:
                key_to_index[key_value] = len(rows) - 1
            added += 1

    # 重写数据区（列头不动）
    if sheet.max_row > 1:
        sheet.delete_rows(2, sheet.max_row - 1)
    for row in rows:
        sheet.append([None if value is None else value for value in row])
    workbook.save(path)

    print(f"[ok] {path.relative_to(ROOT)}：新增 {added} 条，更新 {updated} 条，"
          f"当前共 {len(rows)} 条")
    return added, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="向知识库 xlsx 追加或更新数据")
    parser.add_argument("kind", choices=sorted(KINDS), help="faq / product / banned")
    parser.add_argument("--file", required=True, help="JSON 文件路径（对象数组）")
    args = parser.parse_args()

    json_path = Path(args.file)
    if not json_path.is_absolute():
        json_path = (Path.cwd() / json_path).resolve()
    if not json_path.exists():
        print(f"[error] JSON 文件不存在：{json_path}", file=sys.stderr)
        return 1

    try:
        records = json.loads(json_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"[error] JSON 解析失败：{exc}", file=sys.stderr)
        return 1
    if not isinstance(records, list):
        print("[error] JSON 顶层必须是数组（对象数组）", file=sys.stderr)
        return 1

    try:
        append_records(args.kind, records)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
