"""多集合检索：合并排序 + 相似度阈值过滤。"""


class Retriever:
    def __init__(self, embedder, stores: dict, top_k: int, min_score: float):
        self.embedder = embedder
        self.stores = stores
        self.top_k = top_k
        self.min_score = min_score

    def search(self, query: str, collections: list[str]) -> list[dict]:
        query_vector = self.embedder.embed(query)
        hits: list[dict] = []
        for name in collections:
            store = self.stores.get(name)
            if store is None:
                continue
            for doc_id, text, meta, score in store.query(query_vector, self.top_k):
                if score >= self.min_score:
                    hits.append({
                        "id": doc_id,
                        "text": text,
                        "meta": meta,
                        "score": score,
                        "collection": name,
                    })
        hits.sort(key=lambda item: item["score"], reverse=True)
        return hits[: self.top_k]
