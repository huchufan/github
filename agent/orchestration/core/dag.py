"""
智能编排框架 - DAG 数据结构 (Directed Acyclic Graph)

有向无环图构建、拓扑排序、分层执行顺序与环检测。

设计文档: 02_智能编排框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """DAG 节点。"""
    id: str
    name: str = ""
    task_type: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """DAG 边。"""
    source: str
    target: str
    condition: Optional[str] = None


class DAG:
    """有向无环图。"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[str]] = {}
        self._indegree: Dict[str, int] = {}

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        self.nodes[node.id] = node
        self._adjacency.setdefault(node.id, [])
        self._indegree.setdefault(node.id, 0)

    def add_edge(self, source: str, target: str, condition: Optional[str] = None) -> None:
        if source not in self.nodes or target not in self.nodes:
            raise ValueError("Source or target node not found")
        self.edges.append(Edge(source, target, condition))
        self._adjacency[source].append(target)
        self._indegree[target] = self._indegree.get(target, 0) + 1

    def has_cycle(self) -> bool:
        """检测是否有环。"""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True

    def topological_sort(self) -> List[str]:
        """Kahn 拓扑排序，返回节点 id 顺序；有环时抛 ValueError。"""
        indegree = dict(self._indegree)
        from collections import deque

        queue = deque([n for n in self.nodes if indegree.get(n, 0) == 0])
        order: List[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor in self._adjacency.get(current, []):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            raise ValueError("Graph contains a cycle")

        return order

    def get_execution_order(self) -> List[List[str]]:
        """
        获取分层执行顺序（支持并行）。

        返回每层可并行执行的节点 id 列表，按依赖层次排列。
        """
        levels: List[List[str]] = []
        indegree = dict(self._indegree)
        from collections import deque

        ready = deque([n for n in self.nodes if indegree.get(n, 0) == 0])
        remaining = len(self.nodes)

        while ready:
            level: List[str] = []
            next_ready: List[str] = []
            while ready:
                current = ready.popleft()
                level.append(current)
                remaining -= 1
                for neighbor in self._adjacency.get(current, []):
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        next_ready.append(neighbor)
            levels.append(level)
            ready = deque(next_ready)

        if remaining != 0:
            raise ValueError("Graph contains a cycle")

        return levels

    def find_critical_path(self) -> List[str]:
        """基于拓扑层数的关键路径（简单实现：最长依赖链）。"""
        if not self.nodes:
            return []
        # 自顶向下最长路径长度
        topo = self.topological_sort()
        longest: Dict[str, int] = {n: 1 for n in self.nodes}
        prev: Dict[str, Optional[str]] = {n: None for n in self.nodes}

        for node in topo:
            for neighbor in self._adjacency.get(node, []):
                if longest[node] + 1 > longest[neighbor]:
                    longest[neighbor] = longest[node] + 1
                    prev[neighbor] = node

        # 找到最长路径终点
        end = max(self.nodes, key=lambda n: longest[n])
        path: List[str] = []
        cur: Optional[str] = end
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    def calculate_parallelism_degree(self, execution_order: List[List[str]]) -> float:
        """计算平均并行度。"""
        if not execution_order:
            return 0.0
        return sum(len(level) for level in execution_order) / len(execution_order)


__all__ = ["Node", "Edge", "DAG"]
