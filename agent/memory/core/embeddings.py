"""
记忆系统 - 轻量嵌入与语义索引 (Lightweight Embeddings)

无外部依赖的确定性文本嵌入：基于字符 n-gram 特征哈希，
配合余弦相似度实现语义检索。生产环境可替换为真实向量模型。

设计文档: 03_记忆系统架构.md
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, Iterable, List, Tuple


DEFAULT_DIM = 256


def _tokenize(text: str) -> List[str]:
    """切分为字符 bigram + 单词 token 的混合特征。"""
    text = (text or "").lower()
    words = re.findall(r"[\w\u4e00-\u9fff]+", text)
    features: List[str] = list(words)
    # 字符 n-gram（中文与短词友好）
    compact = re.sub(r"\s+", "", text)
    for n in (2, 3):
        features.extend(compact[i:i + n] for i in range(max(0, len(compact) - n + 1)))
    return features


def _feature_hash(feature: str, dim: int) -> int:
    """将特征哈希到 [0, dim) 的索引。"""
    digest = hashlib.md5(feature.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % dim


def embed(text: str, dim: int = DEFAULT_DIM) -> List[float]:
    """生成文本的确定性稀疏嵌入向量。"""
    vec = [0.0] * dim
    for feature in _tokenize(text):
        idx = _feature_hash(feature, dim)
        # 符号哈希以近似保留方向
        sign = 1.0 if hashlib.md5(feature.encode("utf-8")).digest()[4] < 128 else -1.0
        vec[idx] += sign
    # L2 归一化
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """余弦相似度（假设输入已归一化则直接点积）。"""
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b))


class SemanticIndex:
    """内存向量索引（朴素线性扫描）。"""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self._items: Dict[str, Tuple[str, List[float]]] = {}

    def add(self, item_id: str, embedding: List[float]) -> None:
        self._items[item_id] = (item_id, embedding)

    def remove(self, item_id: str) -> None:
        self._items.pop(item_id, None)

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """返回 (item_id, similarity) 列表，按相似度降序。"""
        scored = [
            (item_id, cosine_similarity(query_embedding, emb))
            for item_id, emb in self._items.values()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._items)


class EmbeddingModel:
    """嵌入模型封装（默认使用确定性哈希嵌入）。"""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim

    def encode(self, text: str) -> List[float]:
        return embed(text, dim=self.dim)

    def similarity(self, a: str, b: str) -> float:
        return cosine_similarity(self.encode(a), self.encode(b))


__all__ = ["embed", "cosine_similarity", "SemanticIndex", "EmbeddingModel", "DEFAULT_DIM"]
