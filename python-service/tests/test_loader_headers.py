from openpyxl import Workbook

from app.rag.loader import load_xlsx
from app.rag.schema_validator import canonical_header, validate_headers


def test_headers_are_normalized(tmp_path):
    path = tmp_path / "faq.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["ID", " Question ", "﻿ANSWER", "Category"])
    sheet.append([1, "问题", "答案", "售后"])
    workbook.save(path)

    headers, rows = load_xlsx(path)

    assert headers == ["id", "question", "answer", "category"]
    assert rows[0]["question"] == "问题"
    assert rows[0]["answer"] == "答案"
    assert canonical_header("﻿ID ") == "id"


def test_validate_headers_reports_missing():
    ok, missing = validate_headers(["id", "question"], ["id", "question", "answer"])
    assert not ok
    assert missing == ["answer"]
