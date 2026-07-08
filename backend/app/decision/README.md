# Decision Layer Module

## Purpose
The `decision` module contains the decoupled logic engines responsible for matching, evaluating, resolving, and planning the compliance roadmap of a business profile against policy rules.

## Responsibilities
* **Rule Matching**: Identifies active policies applicable to a business's type, state, and size (`engine.py`).
* **Condition Evaluation**: Recursively parses logical rules (`all`, `any`, `not`) and handles missing details (`evaluator.py`).
* **Dependency Resolution**: Organizes matched rules in a Directed Acyclic Graph (DAG) using topological sorting and detects cycles (`dependency.py`).
* **Eligibility Assessment**: Inspects condition satisfaction, generating severe/non-severe compliance warnings and recommended remedies (`eligibility.py`).
* **Workflow Roadmap**: Maps critical paths, estimates duration metrics, and marks steps as `AVAILABLE` or `BLOCKED` (`workflow.py`).

## Public Interfaces
* `RuleEngine(policy_loader)`
  * `match(profile: BusinessProfile) -> RuleEngineResult`
* `ConditionEvaluator(policy_loader)`
  * `evaluate(profile: BusinessProfile, matched_rules: List[ApplicableRule]) -> EvaluationResult`
* `DependencyResolver()`
  * `build_graph(matched_rules: List[ApplicableRule], evaluations: List[ConditionEvaluation]) -> DependencyGraph`
* `EligibilityEngine(policy_loader)`
  * `evaluate(...) -> EligibilityResult`
* `WorkflowEngine(policy_loader, knowledge_loader)`
  * `generate(...) -> WorkflowResult`

## Dependencies
* **Internal**: `backend/app/core` (exceptions, settings), `backend/app/services` (loaders), and `backend/app/domain` (models).
* **External**: `pydantic`.

## Forbidden Dependencies
* **Compliance Facade**: Must not import the compliance engine or compliance plans.
* **API Layer**: Must not import API endpoints or routers.

## Fit in the Overall Architecture
This layer consumes canonical objects and evaluates them against business profile facts. The output is a highly structured, sequenced workflow dependency roadmap. It sits above the Domain/Knowledge layers and directly below the Compliance Facade.
