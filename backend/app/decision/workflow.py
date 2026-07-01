from typing import Any, Dict, List, Optional
from loguru import logger

from backend.app.services.policy_loader import PolicyLoader
from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.decision.models import (
    BusinessProfile,
    RuleEngineResult,
    EvaluationResult,
    ConditionEvaluation,
    DependencyGraph,
    EligibilityResult,
    EligibilityStatus,
    ConditionStatus,
    WorkflowStatus,
    WorkflowStep,
    WorkflowResult,
)


class WorkflowEngine:
    def __init__(
        self,
        policy_loader: PolicyLoader,
        knowledge_loader: Optional[KnowledgeLoader] = None,
    ):
        self.policy_loader = policy_loader
        self.knowledge_loader = knowledge_loader or KnowledgeLoader(
            knowledge_dir=policy_loader.knowledge_dir
        )

    def generate(
        self,
        profile: BusinessProfile,
        rule_result: RuleEngineResult,
        evaluation_result: EvaluationResult,
        dependency_graph: DependencyGraph,
        eligibility_result: EligibilityResult,
    ) -> WorkflowResult:
        """
        Converts the eligibility and dependency status of matching rules into a roadmap workflow.
        """
        # 1. Handle NOT_ELIGIBLE case
        if eligibility_result.status == EligibilityStatus.NOT_ELIGIBLE:
            blocking_reasons = "; ".join(
                issue.message for issue in eligibility_result.issues if issue.blocking
            )
            explanation = (
                f"Business is not eligible. Reasons: {blocking_reasons}"
                if blocking_reasons
                else "Business is not eligible due to mandatory policy requirements."
            )
            return WorkflowResult(
                steps={},
                execution_order=[],
                critical_path=[],
                blocked_steps=[],
                completion_percentage=0.0,
                summary={
                    "status": "NOT_ELIGIBLE",
                    "explanation": explanation,
                    "total_steps": 0,
                },
            )

        # 2. Build steps
        steps = self.build_steps(
            matched_rules=rule_result.matched_rules,
            evaluations=evaluation_result.evaluations,
            dependency_graph=dependency_graph,
        )

        # 3. Determine status of steps in execution order (topological order)
        execution_order = self.calculate_execution_order(dependency_graph)
        self.determine_status(steps, evaluation_result.evaluations, execution_order)

        # 4. Identify blocked steps
        blocked_steps = self.identify_blocked_steps(steps)

        # 5. Calculate completion stats
        completion_pct = self.calculate_completion_percentage(steps)

        # 6. Calculate critical path
        critical_path = self.calculate_critical_path(dependency_graph.nodes, execution_order)

        # 7. Compile Summary
        satisfied_count = sum(1 for s in steps.values() if s.status == WorkflowStatus.COMPLETED)
        available_count = sum(1 for s in steps.values() if s.status == WorkflowStatus.AVAILABLE)
        blocked_count = sum(1 for s in steps.values() if s.status == WorkflowStatus.BLOCKED)

        summary = {
            "status": eligibility_result.status.value,
            "total_steps": len(steps),
            "available_steps": available_count,
            "blocked_steps": blocked_count,
            "completed_steps": satisfied_count,
            "completion_percentage": completion_pct,
            "critical_path_length": len(critical_path),
        }

        return WorkflowResult(
            steps=steps,
            execution_order=execution_order,
            critical_path=critical_path,
            blocked_steps=blocked_steps,
            completion_percentage=completion_pct,
            summary=summary,
        )

    def build_steps(
        self, matched_rules, evaluations, dependency_graph
    ) -> Dict[str, WorkflowStep]:
        """
        Builds initial WorkflowStep objects by resolving metadata from JSON configurations.
        """
        steps = {}
        for rule in matched_rules:
            rule_id = rule.rule_id
            rule_def = self.policy_loader.get_rule_by_id(rule_id)

            required_documents: List[str] = []
            estimated_duration: Optional[str] = None

            # Resolve from rule definition if present
            if rule_def:
                if "required_documents" in rule_def:
                    required_documents.extend(rule_def["required_documents"])
                if "estimated_duration" in rule_def:
                    estimated_duration = rule_def["estimated_duration"]

            # Load from linked license asset
            action_params = rule_def.get("action", {}).get("params", {}) if rule_def else {}
            license_uuid = action_params.get("license_uuid")

            if license_uuid:
                license_node = self.knowledge_loader.get_by_uuid("licenses", license_uuid)
                if license_node:
                    # Load documents
                    for doc_uuid in license_node.get("required_document_uuids", []):
                        doc_node = self.knowledge_loader.get_by_uuid("documents", doc_uuid)
                        if doc_node and doc_node.get("document_name"):
                            required_documents.append(doc_node["document_name"])
                    # Load timeline
                    timeline_uuid = license_node.get("timeline_uuid")
                    if timeline_uuid:
                        timeline_node = self.knowledge_loader.get_by_uuid("timelines", timeline_uuid)
                        if timeline_node:
                            days = timeline_node.get("processing_duration_days")
                            estimated_duration = f"{days} days"

            # Deduplicate documents list
            required_documents = sorted(list(set(required_documents)))

            # Use graph dependencies if present
            graph_node = dependency_graph.nodes.get(rule_id)
            dependencies = graph_node.parents if graph_node else rule.dependencies

            steps[rule_id] = WorkflowStep(
                step_id=rule_id,
                rule_id=rule_id,
                title=rule.title,
                description=rule.description,
                status=WorkflowStatus.NOT_STARTED,
                authority=rule.authority,
                priority=rule.priority,
                dependencies=dependencies,
                required_documents=required_documents,
                estimated_duration=estimated_duration,
            )

        return steps

    def determine_status(
        self,
        steps: Dict[str, WorkflowStep],
        evaluations: List[ConditionEvaluation],
        execution_order: List[str],
    ):
        """
        Calculates status for each step. Iterating in topological order ensures
        that parent status is determined before child status.
        """
        eval_map = {ev.rule_id: ev for ev in evaluations}

        for step_id in execution_order:
            step = steps[step_id]
            evaluation = eval_map.get(step_id)

            # Check if any parent dependencies in the graph are not completed
            pending_parents = []
            for p in step.dependencies:
                parent_step = steps.get(p)
                if parent_step and parent_step.status != WorkflowStatus.COMPLETED:
                    pending_parents.append(p)

            if pending_parents:
                step.status = WorkflowStatus.BLOCKED
                step.blocking_reason = (
                    f"Waiting for parent dependency: {', '.join(pending_parents)}"
                )
            elif evaluation and evaluation.status != ConditionStatus.SATISFIED:
                step.status = WorkflowStatus.BLOCKED
                step.blocking_reason = f"Eligibility issue: {evaluation.reason}"
            else:
                # If there are no blocking parents and eligibility conditions are met, it is AVAILABLE
                # Note: IN_PROGRESS and COMPLETED status overrides can be injected from a database persistence layer.
                step.status = WorkflowStatus.AVAILABLE
                step.blocking_reason = None

    def calculate_execution_order(self, dependency_graph: DependencyGraph) -> List[str]:
        return dependency_graph.execution_order

    def identify_blocked_steps(self, steps: Dict[str, WorkflowStep]) -> List[str]:
        return [step_id for step_id, step in steps.items() if step.status == WorkflowStatus.BLOCKED]

    def calculate_completion_percentage(self, steps: Dict[str, WorkflowStep]) -> float:
        total = len(steps)
        if total == 0:
            return 0.0
        completed = sum(1 for step in steps.values() if step.status == WorkflowStatus.COMPLETED)
        return float(completed / total * 100.0)

    def calculate_critical_path(
        self, nodes: Dict[str, Any], execution_order: List[str]
    ) -> List[str]:
        """
        Calculates the critical path in the DAG using dynamic programming.
        The critical path represents the longest chain of dependencies.
        """
        if not execution_order:
            return []

        paths: Dict[str, List[str]] = {}

        for nid in execution_order:
            node = nodes[nid]
            graph_parents = [p for p in node.parents if p in nodes]

            if not graph_parents:
                paths[nid] = [nid]
            else:
                # Find the parent that lies on the longest path so far
                best_parent = max(graph_parents, key=lambda p: len(paths[p]))
                paths[nid] = paths[best_parent] + [nid]

        if not paths:
            return []

        # Return the longest path computed
        longest_path_key = max(paths.keys(), key=lambda k: len(paths[k]))
        return paths[longest_path_key]
