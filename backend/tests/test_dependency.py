import pytest
from typing import List
from backend.app.decision.models import ApplicableRule
from backend.app.decision.dependency import DependencyResolver


def create_rule(rule_id: str, dependencies: List[str] = None) -> ApplicableRule:
    return ApplicableRule(
        rule_id=rule_id,
        title=f"Rule {rule_id}",
        description=f"Description of rule {rule_id}",
        category="General",
        authority="Test Auth",
        priority=5,
        dependencies=dependencies or [],
        source="https://test.gov"
    )


def test_linear_chains():
    # Chain: A -> B -> C -> D
    # B depends on A, C depends on B, D depends on C
    rules = [
        create_rule("A", []),
        create_rule("B", ["A"]),
        create_rule("C", ["B"]),
        create_rule("D", ["C"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert not graph.cycles_detected
    assert graph.execution_order == ["A", "B", "C", "D"]
    assert graph.roots == ["A"]
    assert graph.leaf_nodes == ["D"]

    # Verify depths
    assert graph.nodes["A"].depth == 0
    assert graph.nodes["B"].depth == 1
    assert graph.nodes["C"].depth == 2
    assert graph.nodes["D"].depth == 3


def test_branching_graphs():
    # Branching: A -> B, A -> C (one parent to multiple children)
    # AND X -> Z, Y -> Z (multiple parents to one child)
    rules = [
        create_rule("A", []),
        create_rule("B", ["A"]),
        create_rule("C", ["A"]),
        create_rule("X", []),
        create_rule("Y", []),
        create_rule("Z", ["X", "Y"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert not graph.cycles_detected
    # roots: A, X, Y
    assert sorted(graph.roots) == ["A", "X", "Y"]
    # leaf nodes: B, C, Z
    assert sorted(graph.leaf_nodes) == ["B", "C", "Z"]

    # Order verification (A before B and C; X, Y before Z)
    order = graph.execution_order
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("X") < order.index("Z")
    assert order.index("Y") < order.index("Z")

    assert graph.nodes["Z"].depth == 1
    assert graph.nodes["B"].depth == 1


def test_multiple_roots_and_disconnected_trees():
    # Tree 1: A -> B
    # Tree 2: X -> Y
    rules = [
        create_rule("A", []),
        create_rule("B", ["A"]),
        create_rule("X", []),
        create_rule("Y", ["X"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert not graph.cycles_detected
    assert sorted(graph.roots) == ["A", "X"]
    assert sorted(graph.leaf_nodes) == ["B", "Y"]

    order = graph.execution_order
    assert order.index("A") < order.index("B")
    assert order.index("X") < order.index("Y")


def test_shared_dependencies_diamond():
    # Diamond: A -> B -> D, A -> C -> D
    rules = [
        create_rule("A", []),
        create_rule("B", ["A"]),
        create_rule("C", ["A"]),
        create_rule("D", ["B", "C"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert not graph.cycles_detected
    assert graph.roots == ["A"]
    assert graph.leaf_nodes == ["D"]

    order = graph.execution_order
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")

    assert graph.nodes["D"].depth == 2


def test_cycle_detection_direct():
    # Cycle: A -> B -> A
    rules = [
        create_rule("A", ["B"]),
        create_rule("B", ["A"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert graph.cycles_detected
    # Topological sort/depth calculation should be bypassed or return empty/partial values
    assert len(graph.execution_order) == 0

    errors = resolver.validate_graph()
    assert any("Cycle detected" in err for err in errors)


def test_cycle_detection_indirect():
    # Cycle: A -> B -> C -> A
    rules = [
        create_rule("A", ["C"]),
        create_rule("B", ["A"]),
        create_rule("C", ["B"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)

    assert graph.cycles_detected
    errors = resolver.validate_graph()
    assert any("Cycle detected" in err for err in errors)


def test_invalid_dependencies_handling():
    # 1. Self-dependency: A -> A
    rules = [
        create_rule("A", ["A"])
    ]
    resolver = DependencyResolver()
    graph = resolver.build_graph(rules)
    errors = resolver.validate_graph()
    assert any("Self-dependency detected" in err for err in errors)

    # 2. Missing dependency: B -> C (C not in matched rules)
    rules2 = [
        create_rule("A", []),
        create_rule("B", ["C"])
    ]
    resolver2 = DependencyResolver()
    graph2 = resolver2.build_graph(rules2)
    errors2 = resolver2.validate_graph()
    assert any("Missing dependency" in err and "C" in err for err in errors2)
    # B should still be in execution order since C is missing, so in-degree inside graph is 0
    assert "B" in graph2.execution_order
