from app.rag.embedder import HashEmbedder
from app.rag.retriever import Retriever
from app.rag.vector_store import MemoryVectorStore


def test_retriever_returns_best_match():
    embedder = HashEmbedder()
    store = MemoryVectorStore()
    texts = [
        "问题：退换货政策是什么\n答案：七天无理由退换货",
        "商品：降噪蓝牙耳机；价格：299.00",
    ]
    store.add(
        ["faq-1", "product-1"],
        texts,
        [{"kind": "faq"}, {"kind": "product"}],
        [embedder.embed(text) for text in texts],
    )

    retriever = Retriever(embedder, {"faq": store}, top_k=2, min_score=0.0)
    hits = retriever.search("退换货政策是什么", ["faq"])

    assert hits
    assert hits[0]["id"] == "faq-1"
    assert hits[0]["score"] > 0.5
