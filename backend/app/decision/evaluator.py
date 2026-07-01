from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple
from loguru import logger

from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import (
    BusinessProfile,
    ApplicableRule,
    ConditionEvaluation,
    EvaluationResult,
    ConditionStatus,
)
from backend.app.decision.engine import resolve_fact


def evaluate_condition_detailed(
    condition: Dict[str, Any], profile: BusinessProfile
) -> Tuple[bool, Dict[str, Any], Set[str]]:
    """
    Evaluates a condition recursively.
    Returns a tuple of (passed, details_dict, missing_fields).
    """
    missing_fields = set()

    # 1. Logical OR (any)
    if "any" in condition:
        sub_details = []
        sub_results = []
        for cond in condition["any"]:
            passed, detail, sub_missing = evaluate_condition_detailed(cond, profile)
            sub_results.append(passed)
            sub_details.append(detail)
            missing_fields.update(sub_missing)
        passed = any(sub_results) if sub_results else False
        detail = {
            "operator": "any",
            "passed": passed,
            "sub_conditions": sub_details,
        }
        return passed, detail, missing_fields

    # 2. Logical AND (all)
    if "all" in condition:
        sub_details = []
        sub_results = []
        for cond in condition["all"]:
            passed, detail, sub_missing = evaluate_condition_detailed(cond, profile)
            sub_results.append(passed)
            sub_details.append(detail)
            missing_fields.update(sub_missing)
        passed = all(sub_results) if sub_results else True
        detail = {
            "operator": "all",
            "passed": passed,
            "sub_conditions": sub_details,
        }
        return passed, detail, missing_fields

    # 3. Logical NOT (not)
    if "not" in condition:
        sub_passed, sub_detail, sub_missing = evaluate_condition_detailed(condition["not"], profile)
        passed = not sub_passed
        missing_fields.update(sub_missing)
        detail = {
            "operator": "not",
            "passed": passed,
            "sub_condition": sub_detail,
        }
        return passed, detail, missing_fields

    # 4. Simple condition
    fact = condition.get("fact")
    operator = condition.get("operator")
    value = condition.get("value")

    if not fact or not operator:
        detail = {
            "passed": False,
            "error": "Missing fact or operator",
        }
        return False, detail, missing_fields

    val, exists = resolve_fact(profile, fact)
    normalized_op = operator.lower().replace("_", "")

    # Handle exists operator
    if normalized_op == "exists":
        expected_existence = bool(value)
        passed = (exists == expected_existence)
        detail = {
            "fact": fact,
            "operator": operator,
            "expected_value": value,
            "actual_value": val if exists else None,
            "passed": passed,
            "missing": False,
        }
        return passed, detail, missing_fields

    # If the fact doesn't exist, it's missing profile data
    if not exists:
        missing_fields.add(fact)
        detail = {
            "fact": fact,
            "operator": operator,
            "expected_value": value,
            "actual_value": None,
            "passed": False,
            "missing": True,
        }
        return False, detail, missing_fields

    # Evaluate other operators
    passed = False
    try:
        if normalized_op in ("equal", "equals"):
            passed = (val == value)
        elif normalized_op in ("notequal", "not_equals", "notequals"):
            passed = (val != value)
        elif normalized_op in ("greaterthan", "gt"):
            passed = (val > value)
        elif normalized_op in ("greaterthanorequal", "gte"):
            passed = (val >= value)
        elif normalized_op in ("lessthan", "lt"):
            passed = (val < value)
        elif normalized_op in ("lessthanorequal", "lte"):
            passed = (val <= value)
        elif normalized_op == "in":
            passed = (val in value)
        elif normalized_op in ("notin", "not_in"):
            passed = (val not in value)
        elif normalized_op == "contains":
            passed = (value in val)
    except Exception as e:
        logger.warning(f"Error evaluating condition for fact '{fact}' with operator '{operator}': {e}")
        passed = False

    detail = {
        "fact": fact,
        "operator": operator,
        "expected_value": value,
        "actual_value": val,
        "passed": passed,
        "missing": False,
    }
    return passed, detail, missing_fields


class ConditionEvaluator:
    def __init__(self, policy_loader: PolicyLoader):
        self.policy_loader = policy_loader

    def evaluate(
        self, profile: BusinessProfile, matched_rules: List[ApplicableRule]
    ) -> EvaluationResult:
        """
        Evaluates the conditions and exceptions of matched rules against the BusinessProfile.
        Returns an EvaluationResult.
        """
        evaluations: Dict[str, ConditionEvaluation] = {}
        timestamp = datetime.now(timezone.utc)

        for rule in matched_rules:
            rule_id = rule.rule_id
            rule_def = self.policy_loader.get_rule_by_id(rule_id)

            if not rule_def:
                # If rule definition is missing, treat it as FAILED
                evaluations[rule_id] = ConditionEvaluation(
                    rule_id=rule_id,
                    status=ConditionStatus.FAILED,
                    reason="Rule definition not found in PolicyLoader.",
                    missing_fields=[],
                    evaluated_conditions=[],
                    timestamp=timestamp,
                )
                continue

            missing_fields: Set[str] = set()
            evaluated_conditions: List[Dict[str, Any]] = []

            # 1. Evaluate condition
            condition_passed, cond_detail, cond_missing = evaluate_condition_detailed(
                rule_def["condition"], profile
            )
            evaluated_conditions.append(cond_detail)
            missing_fields.update(cond_missing)

            # 2. Evaluate exceptions
            exception_triggered = False
            if "exceptions" in rule_def and rule_def["exceptions"]:
                for exc in rule_def["exceptions"]:
                    exc_passed, exc_detail, exc_missing = evaluate_condition_detailed(exc, profile)
                    evaluated_conditions.append({
                        "is_exception": True,
                        "condition": exc_detail,
                    })
                    missing_fields.update(exc_missing)
                    if exc_passed:
                        exception_triggered = True

            # 3. Determine status
            # If any required profile data was missing: PENDING_INFORMATION
            if missing_fields:
                status = ConditionStatus.PENDING_INFORMATION
                reason = f"Required profile attributes are missing: {', '.join(sorted(list(missing_fields)))}"
            # If condition passed and no exception matched: SATISFIED
            elif condition_passed and not exception_triggered:
                status = ConditionStatus.SATISFIED
                reason = "All conditions were successfully satisfied."
            # Otherwise: FAILED
            else:
                status = ConditionStatus.FAILED
                if exception_triggered:
                    reason = "Rule evaluation failed because an exception clause matched."
                else:
                    reason = "Rule evaluation failed because the applicability conditions were not met."

            evaluations[rule_id] = ConditionEvaluation(
                rule_id=rule_id,
                status=status,
                reason=reason,
                missing_fields=sorted(list(missing_fields)),
                evaluated_conditions=evaluated_conditions,
                timestamp=timestamp,
            )

        # 4. Iteratively propagate dependency status (NOT_APPLICABLE)
        # If a rule depends on another rule, and that parent rule is NOT satisfied,
        # the dependent rule becomes NOT_APPLICABLE.
        changed = True
        while changed:
            changed = False
            for rule_id, evaluation in list(evaluations.items()):
                if evaluation.status == ConditionStatus.NOT_APPLICABLE:
                    continue

                rule_def = self.policy_loader.get_rule_by_id(rule_id)
                dependencies = rule_def.get("dependencies", []) if rule_def else []

                unsatisfied_deps = []
                for dep_id in dependencies:
                    dep_eval = evaluations.get(dep_id)
                    # If dependency is missing from the evaluation map or is not satisfied, it's unsatisfied
                    if not dep_eval or dep_eval.status != ConditionStatus.SATISFIED:
                        unsatisfied_deps.append(dep_id)

                if unsatisfied_deps:
                    evaluation.status = ConditionStatus.NOT_APPLICABLE
                    evaluation.reason = (
                        "Rule is not applicable because its dependency rules were "
                        f"not satisfied: {', '.join(unsatisfied_deps)}"
                    )
                    changed = True

        evaluations_list = list(evaluations.values())

        # 5. Generate summary statistics
        satisfied_count = sum(1 for e in evaluations_list if e.status == ConditionStatus.SATISFIED)
        failed_count = sum(1 for e in evaluations_list if e.status == ConditionStatus.FAILED)
        pending_count = sum(1 for e in evaluations_list if e.status == ConditionStatus.PENDING_INFORMATION)
        not_applicable_count = sum(1 for e in evaluations_list if e.status == ConditionStatus.NOT_APPLICABLE)

        summary = {
            "satisfied": satisfied_count,
            "failed": failed_count,
            "pending": pending_count,
            "not_applicable": not_applicable_count,
        }

        return EvaluationResult(
            profile=profile,
            evaluations=evaluations_list,
            summary=summary,
        )
