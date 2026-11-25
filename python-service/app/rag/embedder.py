"""向量化：hash 模式（默认，离线可用）或 sentence-transformers（BGE-m3）。"""

import hashlib

import numpy as np


class HashEmbedder:
    """确定性哈希向量：无需下载模型即可运行；语义能力有限，用于演示与联调。"""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in self._tokens(text):
            digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[digest % self.dim] += 1.0
        norm = float(np.linalg.norm(vec))
        return vec / norm if norm > 0 else vec

    @staticmethod
    def _tokens(text: str) -> list[str]:
        cleaned = "".join(ch if ch.isalnum() else " " for ch in text)
        grams = [cleaned[i:i + 2] for i in range(max(len(cleaned) - 1, 1))]
        grams = [g for g in grams if g.strip()]
        return grams or [cleaned or " "]


class SentenceTransformerEmbedder:
    """BGE-m3 本地向量模型（需 pip install sentence-transformers）。"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> np.ndarray:
        vector = self._model.encode(text, normalize_embeddings=True)
        return np.asarray(vector, dtype=np.float32)


def create_embedder(provider: str):
    if provider == "sentence_transformers":
        return SentenceTransformerEmbedder()
    return HashEmbedder()
