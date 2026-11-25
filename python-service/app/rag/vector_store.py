"""向量存储：内存余弦检索（默认）或 Chroma（可选）。"""

import logging

import numpy as np

log = logging.getLogger(__name__)


class MemoryVectorStore:
    """进程内向量库：add 采用整库重建语义。"""

    def __init__(self):
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._metas: list[dict] = []
        self._vectors: np.ndarray | None = None

    def add(self, ids: list[str], texts: list[str],
            metas: list[dict], vectors: list[np.ndarray]) -> None:
        self._ids = list(ids)
        self._texts = list(texts)
        self._metas = list(metas)
        self._vectors = np.asarray(vectors, dtype=np.float32) if len(vectors) else None

    def query(self, vector: np.ndarray, top_k: int) -> list[tuple[str, str, dict, float]]:
        if self._vectors is None or len(self._vectors) == 0:
            return []
        scores = self._vectors @ np.asarray(vector, dtype=np.float32)
        order = np.argsort(-scores)[:top_k]
        return [(self._ids[i], self._texts[i], self._metas[i], float(scores[i]))
                for i in order]


class ChromaVectorStore:
    """Chroma 持久化向量库（需 pip install chromadb）。"""

    def __init__(self, collection_name: str):
        import chromadb
        self._client = chromadb.PersistentClient(path="./data/chroma")
        self._name = collection_name
        self._collection = self._open_cosine_collection()

    def _open_cosine_collection(self):
        """打开 cosine 集合；若已存在旧的 L2 集合则删除重建。"""
        try:
            collection = self._client.get_collection(self._name)
            space = (collection.metadata or {}).get("hnsw:space")
            if space == "cosine":
                return collection
            self._client.delete_collection(self._name)
        except Exception:
            pass
        return self._client.create_collection(
            self._name, metadata={"hnsw:space": "cosine"})

    def add(self, ids: list[str], texts: list[str],
            metas: list[dict], vectors: list[np.ndarray]) -> None:
        try:
            self._client.delete_collection(self._name)
        except Exception:
            pass
        self._collection = self._client.create_collection(
            self._name, metadata={"hnsw:space": "cosine"})
        if ids:
            self._collection.add(
                ids=list(ids),
                documents=list(texts),
                metadatas=list(metas),
                embeddings=[v.tolist() for v in vectors],
            )

    def query(self, vector: np.ndarray, top_k: int) -> list[tuple[str, str, dict, float]]:
        result = self._collection.query(
            query_embeddings=[vector.tolist()], n_results=top_k)
        hits: list[tuple[str, str, dict, float]] = []
        ids = result.get("ids") or [[]]
        for i in range(len(ids[0])):
            hits.append((
                result["ids"][0][i],
                (result.get("documents") or [[""]])[0][i],
                (result.get("metadatas") or [[{}]])[0][i] or {},
                1.0 - float(result["distances"][0][i]),
            ))
        return hits


def create_store(name: str, collection: str):
    if name == "chroma":
        try:
            return ChromaVectorStore(collection)
        except Exception as exc:  # chromadb 未安装/启动失败
            log.warning("Chroma 不可用，回退内存向量库: %s", exc)
    return MemoryVectorStore()
