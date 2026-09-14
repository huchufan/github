"""治理框架 - 行为规则库测试"""

from agent.governance.core.rules import BehaviorRule, BehaviorRuleStore


class TestBehaviorRule:
    def test_from_dict(self):
        rule = BehaviorRule.from_dict({"id": "r1", "name": "测试", "category": "test"})
        assert rule.id == "r1"
        assert rule.category == "test"

    def test_from_dict_ignores_unknown(self):
        rule = BehaviorRule.from_dict(
            {"id": "r1", "name": "测试", "unknown_field": 123}
        )
        assert rule.id == "r1"
        assert not hasattr(rule, "unknown_field")


class TestBehaviorRuleStore:
    def test_add_and_query(self):
        store = BehaviorRuleStore()
        store.add_rule(
            BehaviorRule(
                id="r1",
                name="中文交流",
                category="communication",
                applies_to=["conversation"],
            )
        )
        assert len(store) == 1
        assert store.get_rule("r1").name == "中文交流"
        assert store.get_rules("communication")[0].id == "r1"
        assert len(store.applicable_to("conversation")) == 1
        assert store.applicable_to("unrelated") == []

    def test_deduplicate_by_id(self):
        store = BehaviorRuleStore()
        store.add_rule(BehaviorRule(id="r1", name="v1"))
        store.add_rule(BehaviorRule(id="r1", name="v2"))
        assert len(store) == 1
        assert store.get_rule("r1").name == "v1"

    def test_load_from_yaml(self):
        store = BehaviorRuleStore.from_yaml("config/governance/governance.yaml")
        assert len(store) == 2
        ids = {r.id for r in store.rules}
        assert "rule-zh-communication" in ids
        assert "rule-automation-preference" in ids
        # 中文交流规则适用于对话场景
        zh = store.get_rule("rule-zh-communication")
        assert "conversation" in zh.applies_to
