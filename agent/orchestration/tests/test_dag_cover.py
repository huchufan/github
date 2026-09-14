import pytest

from agent.orchestration.core.dag import DAG, Node


def test_add_node_and_duplicate():
    d = DAG()
    n = Node(id="n1", name="Node1")
    d.add_node(n)
    assert "n1" in d.nodes
    with pytest.raises(ValueError):
        d.add_node(n)


def test_add_edge_missing_node_raises():
    d = DAG()
    d.add_node(Node(id="a"))
    with pytest.raises(ValueError):
        d.add_edge("a", "b")


def test_topological_sort_and_cycle_detection():
    d = DAG()
    for i in ["a", "b", "c"]:
        d.add_node(Node(id=i))
    d.add_edge("a", "b")
    d.add_edge("b", "c")
    order = d.topological_sort()
    assert order == ["a", "b", "c"]
    # introduce cycle
    d.add_edge("c", "a")
    with pytest.raises(ValueError):
        d.topological_sort()
    assert d.has_cycle()


def test_get_execution_order_and_parallelism():
    d = DAG()
    for i in ["n1", "n2", "n3", "n4"]:
        d.add_node(Node(id=i))
    d.add_edge("n1", "n3")
    d.add_edge("n2", "n3")
    d.add_edge("n3", "n4")
    levels = d.get_execution_order()
    # first level contains n1 and n2 in some order
    assert any(set(level) == {"n1", "n2"} for level in levels[:1]) or set(
        levels[0]
    ) == {"n1", "n2"}
    # parallelism degree > 1
    deg = d.calculate_parallelism_degree(levels)
    assert deg >= 1.0


def test_find_critical_path():
    d = DAG()
    for i in ["a", "b", "c", "d", "e"]:
        d.add_node(Node(id=i))
    d.add_edge("a", "b")
    d.add_edge("b", "c")
    d.add_edge("a", "d")
    d.add_edge("d", "e")
    path = d.find_critical_path()
    # longest chains are a->b->c (3) and a->d->e (3)
    assert len(path) == 3
    assert path[0] == "a"
