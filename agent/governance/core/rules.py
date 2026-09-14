"""
治理框架 - 行为规则库 (Behavior Rules)

系统遵循的沟通准则与自动化偏好规则。规则以 YAML 配置持久化，
通过 BehaviorRuleStore 加载与查询，供编排/自动化层在决策时引用。

设计文档: 01_治理框架设计.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BehaviorRule:
    """一条行为规则。"""

    id: str = ""
    name: str = ""
    category: str = ""
    priority: str = "MEDIUM"
    description: str = ""
    applies_to: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorRule":
        """从字典构造（忽略未知字段）。"""
        known = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in known})


class BehaviorRuleStore:
    """行为规则库：加载、存储与查询。"""

    def __init__(self, rules: Optional[List[BehaviorRule]] = None):
        self.rules: List[BehaviorRule] = list(rules or [])

    def add_rule(self, rule: BehaviorRule) -> None:
        """添加规则（按 id 去重）。"""
        if rule.id and self.get_rule(rule.id) is not None:
            return
        self.rules.append(rule)

    def get_rule(self, rule_id: str) -> Optional[BehaviorRule]:
        """按 id 查询规则。"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def get_rules(self, category: Optional[str] = None) -> List[BehaviorRule]:
        """查询规则；可按类别过滤。"""
        if category is None:
            return list(self.rules)
        return [r for r in self.rules if r.category == category]

    def applicable_to(self, scope: str) -> List[BehaviorRule]:
        """返回适用于给定场景 (scope) 的规则。"""
        return [r for r in self.rules if scope in r.applies_to]

    @classmethod
    def from_yaml(
        cls, path: str | Path, key: str = "behavior_rules"
    ) -> "BehaviorRuleStore":
        """从 YAML 配置加载行为规则。"""
        import yaml

        p = Path(path)
        if not p.exists():
            logger.warning("配置不存在: %s", p)
            return cls()
        with p.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        rules = [BehaviorRule.from_dict(item) for item in data.get(key, [])]
        return cls(rules)

    def __len__(self) -> int:
        return len(self.rules)


__all__ = ["BehaviorRule", "BehaviorRuleStore"]
