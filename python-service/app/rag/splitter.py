"""知识库文本化与切分：按行拼成检索文本，超长再二次切分。"""


def row_to_text(kind: str, row: dict) -> str:
    if kind == "faq":
        return f"问题：{row.get('question', '')}\n答案：{row.get('answer', '')}"

    parts = [f"商品：{row.get('name', '')}", f"类目：{row.get('category', '')}"]
    for column, label in (
        ("spec", "规格"),
        ("price", "价格"),
        ("stock_status", "库存状态"),
        ("selling_points", "卖点"),
    ):
        value = row.get(column)
        if value:
            parts.append(f"{label}：{value}")
    return "；".join(parts)


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
