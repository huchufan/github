"""
记忆系统 - 跨层检索和融合 (Memory Retrieval & Fusion)

从多层记忆检索相关记忆并加权融合。

设计文档: 03_记忆系统架构.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.core.types import (FusedMemoryResult, FusedResult, SearchQuery,
                              SearchResult)
from agent.memory.core.layers import (ArchiveMemory, EpisodicMemory,
                                      ImmediateContextMemory, SemanticMemory,
                                      SessionMemory)

logger = logging.getLogger(__name__)


class MemoryRetrievalEngine:
    """跨层记忆检索和融合。"""

    def __init__(
        self,
        immediate: ImmediateContextMemory,
        session: SessionMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        archive: ArchiveMemory | None = None,
    ):
        self.immediate = immediate
        self.session = session
        self.episodic = episodic
        self.semantic = semantic
        self.archive = archive

    def retrieve_relevant_memory(
        self, query: str, layers: List[int] | None = None
    ) -> FusedMemoryResult:
        """从多层检索相关记忆。"""
        layers = layers if layers is not None else [1, 2, 3, 4]
        results: Dict[str, Any] = {
            "layer_1": None,
            "layer_2": [],
            "layer_3": [],
            "layer_4": [],
        }

        if 1 in layers:
            results["layer_1"] = self.immediate.get_conversation_context()
        if 2 in layers:
            results["layer_2"] = self.session.search_sessions(SearchQuery(topic=query))
        if 3 in layers:
            results["layer_3"] = self.episodic.search_events(query)
        if 4 in layers:
            results["layer_4"] = self.semantic.semantic_search(query)

        fused = self.fuse_multi_layer_results(results)
        return FusedMemoryResult(
            layer_1=results["layer_1"],
            layer_2=results["layer_2"],
            layer_3=results["layer_3"],
            layer_4=results["layer_4"],
            fused=fused,
        )

    def fuse_multi_layer_results(self, layer_results: Dict[str, Any]) -> FusedResult:
        """融合多层检索结果。"""
        weights = {"layer_1": 0.40, "layer_2": 0.30, "layer_3": 0.20, "layer_4": 0.10}

        candidates: List[Any] = []
        for layer, results in layer_results.items():
            if not results or layer == "fused":
                continue
            weight = weights.get(layer, 0.1)
            if isinstance(results, list):
                for result in results:
                    score = getattr(result, "relevance_score", 0.5)
                    candidates.append((result, score * weight))
            else:
                # 对话上下文等非列表结果，赋予基础分
                candidates.append((results, 0.5 * weight))

        candidates.sort(key=lambda x: x[1], reverse=True)
        unique = self.deduplicate_candidates(candidates)
        return FusedResult(candidates=unique, fusion_method="weighted_combination")

    @staticmethod
    def deduplicate_candidates(candidates: List[Any]) -> List[Any]:
        """按内容去重（保留首次出现的最高分）。"""
        seen: set = set()
        unique: List[Any] = []
        for item, _score in candidates:
            ident = (
                id(item)
                if not isinstance(item, SearchResult)
                else getattr(item, "knowledge_id", id(item))
            )
            if ident not in seen:
                seen.add(ident)
                unique.append(item)
        return unique


__all__ = ["MemoryRetrievalEngine"]
