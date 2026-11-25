"""RAG 离线评测：Recall@K / MRR（不调用 LLM，不写知识库）。

用法（项目根目录）：
    python python-service/scripts/eval_rag.py --out docs/eval/rag_eval.md
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python-service"))

from app.rag.embedder import HashEmbedder  # noqa: E402
from app.rag.loader import load_xlsx  # noqa: E402
from app.rag.splitter import row_to_text  # noqa: E402

KNOWLEDGE = {
    "faq": ROOT / "data/knowledge/faq/faq.xlsx",
    "product": ROOT / "data/knowledge/product/product.xlsx",
}


def load_chunks() -> list[dict]:
    chunks: list[dict] = []
    for name, path in KNOWLEDGE.items():
        _, rows = load_xlsx(path)
        for row in rows:
            text = row_to_text(name, row)
            if text.strip():
                chunks.append({"collection": name, "text": text})
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG Recall@K / MRR 评测")
    parser.add_argument("--cases", default=str(ROOT / "data/eval/rag_cases.json"))
    parser.add_argument("--out", default="")
    parser.add_argument("--k", default="1,3,5")
    args = parser.parse_args()

    ks = sorted(int(item) for item in args.k.split(",") if item.strip())
    max_k = max(ks)
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8-sig"))
    chunks = load_chunks()
    embedder = HashEmbedder()
    vectors = [embedder.embed(chunk["text"]) for chunk in chunks]

    hits_at = {k: 0 for k in ks}
    reciprocal = 0.0
    rows: list[tuple] = []

    for case in cases:
        query = case["query"]
        expect = case["expect"]
        collection = case.get("collection", "any")
        query_vector = embedder.embed(query)

        scored = []
        for chunk, vector in zip(chunks, vectors):
            if collection != "any" and chunk["collection"] != collection:
                continue
            scored.append((float(np.dot(query_vector, vector)), chunk))
        scored.sort(key=lambda item: item[0], reverse=True)

        top = scored[:max_k]
        rank = 0
        for index, (_, chunk) in enumerate(top, start=1):
            if expect in chunk["text"]:
                rank = index
                break

        if rank:
            reciprocal += 1.0 / rank
            for k in ks:
                if rank <= k:
                    hits_at[k] += 1
        rows.append((query, collection, expect, rank,
                     top[0][0] if top else 0.0))

    total = len(cases)
    lines = [
        "# RAG 离线评测",
        "",
        f"- 知识库分块数：{len(chunks)}",
        f"- 评测样本数：{total}",
        "- Embedding：HashEmbedder（演示级，可切换 BGE-m3）",
        "",
        "| 指标 | 结果 |",
        "|---|---|",
    ]
    for k in ks:
        lines.append(f"| Recall@{k} | {hits_at[k]}/{total} = {hits_at[k] / total:.1%} |")
    lines.append(f"| MRR | {reciprocal / total:.3f} |")
    lines.extend([
        "",
        "| 查询 | 子库 | 期望命中 | 首次命中排名 | Top1 分数 |",
        "|---|---|---|---|---|",
    ])
    for query, collection, expect, rank, top_score in rows:
        lines.append(
            f"| {query} | {collection} | {expect} | {rank or '-'} | {top_score:.3f} |")

    text = "\n".join(lines)
    print(text)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"\n[ok] 已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
