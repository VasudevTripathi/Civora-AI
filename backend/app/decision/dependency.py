from typing import Dict, List, Optional, Set, Tuple
from loguru import logger

from backend.app.decision.models import (
    ApplicableRule,
    ConditionEvaluation,
    DependencyNode,
    DependencyGraph,
)


class DependencyResolver:
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}

    def build_graph(
        self,
        matched_rules: List[ApplicableRule],
        evaluations: Optional[List[ConditionEvaluation]] = None,
    ) -> DependencyGraph:
        """
        Builds the dependency graph from matched rules and evaluation statuses.
        """
        self.nodes = {}

        # 1. Map evaluations by rule_id for easy status lookup
        status_map = {}
        if evaluations:
            for ev in evaluations:
                status_map[ev.rule_id] = (
                    ev.status.value if hasattr(ev.status, "value") else str(ev.status)
                )

        # 2. Create DependencyNode for every matched rule
        for rule in matched_rules:
            self.nodes[rule.rule_id] = DependencyNode(
                rule_id=rule.rule_id,
                title=rule.title,
                parents=[],
                children=[],
                depth=0,
                status=status_map.get(rule.rule_id),
            )

        # 3. Setup parent-child links
        for rule in matched_rules:
            u_node = self.nodes[rule.rule_id]
            for dep_id in rule.dependencies:
                # B depends on A => A is parent of B
                if dep_id not in u_node.parents:
                    u_node.parents.append(dep_id)

                # A has child B
                if dep_id in self.nodes:
                    dep_node = self.nodes[dep_id]
                    if rule.rule_id not in dep_node.children:
                        dep_node.children.append(rule.rule_id)

        # Sort lists to be deterministic
        for node in self.nodes.values():
            node.parents.sort()
            node.children.sort()

        # 4. Detect cycles
        has_cycles, _ = self.detect_cycles()

        # 5. Topological Sort & Depth Calculation
        execution_order = []
        if not has_cycles:
            execution_order = self.topological_sort()
            self.calculate_depths(execution_order)

        roots = self.find_root_nodes()
        leaf_nodes = self.find_leaf_nodes()

        return DependencyGraph(
            nodes=self.nodes,
            roots=roots,
            leaf_nodes=leaf_nodes,
            execution_order=execution_order,
            cycles_detected=has_cycles,
        )

    def detect_cycles(self) -> Tuple[bool, List[List[str]]]:
        """
        Detects cycles in the graph using DFS graph coloring.
        Returns a tuple of (has_cycles, list of cycle paths).
        """
        visited = {}  # 0: white, 1: gray, 2: black
        cycles = []

        for nid in self.nodes:
            visited[nid] = 0

        def dfs(u: str, path: List[str]):
            visited[u] = 1  # visiting (gray)
            path.append(u)

            for v in self.nodes[u].children:
                if v not in self.nodes:
                    continue
                if visited[v] == 1:
                    # Cycle detected! Extract the loop path
                    try:
                        idx = path.index(v)
                        cycles.append(path[idx:] + [v])
                    except ValueError:
                        pass
                elif visited[v] == 0:
                    dfs(v, path)

            path.pop()
            visited[u] = 2  # visited (black)

        for nid in self.nodes:
            if visited[nid] == 0:
                dfs(nid, [])

        return len(cycles) > 0, cycles

    def topological_sort(self) -> List[str]:
        """
        Sorts the node IDs topologically using Kahn's algorithm.
        Returns a list of IDs in execution order.
        """
        # Compute in-degrees (number of parents present in the graph)
        in_degree = {}
        for nid, node in self.nodes.items():
            in_degree[nid] = sum(1 for p in node.parents if p in self.nodes)

        # Queue for nodes with no parents in the graph
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        queue.sort()  # stable sort for deterministic ordering

        execution_order = []
        while queue:
            u = queue.pop(0)
            execution_order.append(u)

            for v in self.nodes[u].children:
                if v in in_degree:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)
            queue.sort()  # keep sorted for deterministic ordering

        return execution_order

    def calculate_depths(self, execution_order: List[str]):
        """
        Calculates the maximum depth from any root for every node in the graph.
        """
        depths = {nid: 0 for nid in self.nodes}

        for nid in execution_order:
            node = self.nodes[nid]
            parent_depths = [depths[p] for p in node.parents if p in depths]
            if parent_depths:
                depths[nid] = max(parent_depths) + 1
            else:
                depths[nid] = 0
            node.depth = depths[nid]

    def find_root_nodes(self) -> List[str]:
        """
        Finds nodes that have no parents present in the graph.
        """
        roots = []
        for nid, node in self.nodes.items():
            has_parent_in_graph = any(p in self.nodes for p in node.parents)
            if not has_parent_in_graph:
                roots.append(nid)
        roots.sort()
        return roots

    def find_leaf_nodes(self) -> List[str]:
        """
        Finds nodes that have no children present in the graph.
        """
        leaves = []
        for nid, node in self.nodes.items():
            has_child_in_graph = any(c in self.nodes for c in node.children)
            if not has_child_in_graph:
                leaves.append(nid)
        leaves.sort()
        return leaves

    def validate_graph(self) -> List[str]:
        """
        Validates the graph's integrity.
        Returns a list of errors/warnings found.
        """
        errors = []

        # 1. Check self loops
        for nid, node in self.nodes.items():
            if nid in node.parents:
                errors.append(f"Self-dependency detected: Rule '{nid}' depends on itself.")

        # 2. Check cycles
        has_cycles, cycles = self.detect_cycles()
        if has_cycles:
            for cycle in cycles:
                cycle_str = " -> ".join(cycle)
                errors.append(f"Cycle detected: {cycle_str}")

        # 3. Check for missing/invalid dependency references
        for nid, node in self.nodes.items():
            for p in node.parents:
                if p not in self.nodes:
                    errors.append(
                        f"Missing dependency: Rule '{nid}' depends on '{p}', but '{p}' is not in matched rules."
                    )

        return errors
