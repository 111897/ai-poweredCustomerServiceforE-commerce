"""知识库表格列模板（与需求文档 5.3 / 设计文档 6.4 保持一致）。"""

FAQ_HEADERS = ["id", "question", "answer", "category", "updated_at"]
FAQ_REQUIRED = ["id", "question", "answer", "category"]

PRODUCT_HEADERS = [
    "product_id", "name", "category", "spec",
    "price", "stock_status", "selling_points", "updated_at",
]
PRODUCT_REQUIRED = ["product_id", "name", "category", "price", "stock_status"]

BANNED_HEADERS = ["pattern", "type", "note"]
BANNED_REQUIRED = ["pattern", "type"]
