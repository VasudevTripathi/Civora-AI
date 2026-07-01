from typing import Any, Dict, List, Optional
from loguru import logger

from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import (
    BusinessProfile,
    ApplicableRule,
    ConditionEvaluation,
    EvaluationResult,
    DependencyGraph,
    EligibilityStatus,
    EligibilityIssue,
    EligibilityResult,
    ConditionStatus,
)


def generate_recommended_action(rule_def: Dict[str, Any], evaluation: ConditionEvaluation) -> str:
    """
    Generates a recommended action based on the rule definition and evaluation context.
    """
    # 1. Check explicit property in rule JSON root
    if "recommended_action" in rule_def:
        return rule_def["recommended_action"]

    # 2. Check within action params
    action_params = rule_def.get("action", {}).get("params", {})
    if "recommended_action" in action_params:
        return action_params["recommended_action"]

    title = rule_def.get("title", "Requirement")
    action_type = rule_def.get("action", {}).get("type")

    # 3. Handle employee threshold conditions
    is_employee_related = False
    for cond in evaluation.evaluated_conditions:
        if cond.get("fact") == "employees":
            is_employee_related = True
        elif "sub_conditions" in cond:
            for sub in cond["sub_conditions"]:
                if sub.get("fact") == "employees":
                    is_employee_related = True

    if is_employee_related:
        return "Reduce workforce classification issue"

    # 4. Handle license requirements
    if "license" in title.lower() or "certificate" in title.lower() or action_type == "require_license":
        return f"Apply for {title}"

    return f"Satisfy {title} requirement"


def generate_issue_message(rule_def: Dict[str, Any], evaluation: ConditionEvaluation) -> str:
    """
    Generates a descriptive issue message based on the rule and condition evaluation status.
    """
    title = rule_def.get("title", "Requirement")
    if evaluation.status == ConditionStatus.PENDING_INFORMATION:
        fields_str = ", ".join(evaluation.missing_fields)
        return f"{title} missing: required profile attributes {fields_str} not provided."
    elif evaluation.status == ConditionStatus.FAILED:
        return f"{title} failure: condition evaluation not met."
    elif evaluation.status == ConditionStatus.NOT_APPLICABLE:
        return f"{title} dependency blocker: pre-requisite rules not met."
    return f"{title} unsatisfied."


class EligibilityEngine:
    def __init__(self, policy_loader: PolicyLoader):
        self.policy_loader = policy_loader

    def evaluate(
        self,
        profile: BusinessProfile,
        matched_rules: List[ApplicableRule],
        condition_result: EvaluationResult,
        dependency_graph: DependencyGraph,
    ) -> EligibilityResult:
        """
        Determines the business profile eligibility against evaluated rules.
        """
        issues: List[EligibilityIssue] = []
        blocking_rules: List[str] = []
        missing_information: List[str] = []
        next_steps: List[str] = []

        # Map evaluations by rule ID for fast lookup
        eval_map = {ev.rule_id: ev for ev in condition_result.evaluations}

        for rule in matched_rules:
            rule_id = rule.rule_id
            rule_def = self.policy_loader.get_rule_by_id(rule_id)

            if not rule_def:
                # If rule definition is missing, it is a blocking failure
                issues.append(
                    EligibilityIssue(
                        rule_id=rule_id,
                        severity="ERROR",
                        message=f"Rule '{rule_id}' definition not found.",
                        blocking=True,
                        recommended_action="Contact system administrator.",
                    )
                )
                blocking_rules.append(rule_id)
                continue

            # Check if the rule is blocking/mandatory
            # Rules are blocking by default, unless explicitly set to false or has notification action
            is_blocking = True
            if "blocking" in rule_def:
                is_blocking = bool(rule_def["blocking"])
            elif rule_def.get("action", {}).get("type") == "trigger_notification":
                is_blocking = False

            evaluation = eval_map.get(rule_id)

            # If no evaluation exists or status is not SATISFIED, construct an issue
            if not evaluation or evaluation.status != ConditionStatus.SATISFIED:
                eval_status = evaluation.status if evaluation else ConditionStatus.FAILED

                severity = "ERROR" if is_blocking else "WARNING"
                message = generate_issue_message(rule_def, evaluation)
                rec_action = generate_recommended_action(rule_def, evaluation)

                issues.append(
                    EligibilityIssue(
                        rule_id=rule_id,
                        severity=severity,
                        message=message,
                        blocking=is_blocking,
                        recommended_action=rec_action,
                    )
                )

                if is_blocking:
                    blocking_rules.append(rule_id)

                if evaluation:
                    for mf in evaluation.missing_fields:
                        if mf not in missing_information:
                            missing_information.append(mf)

                if rec_action not in next_steps:
                    next_steps.append(rec_action)

        # Determine overall Eligibility Status
        has_blocking_issues = len(blocking_rules) > 0
        has_non_blocking_issues = len(issues) > len(blocking_rules)

        if has_blocking_issues:
            status = EligibilityStatus.NOT_ELIGIBLE
        elif has_non_blocking_issues:
            status = EligibilityStatus.CONDITIONALLY_ELIGIBLE
        else:
            status = EligibilityStatus.ELIGIBLE

        # Generate summary statistics
        summary = {
            "status": status.value,
            "total_issues": len(issues),
            "blocking_issues": len(blocking_rules),
            "non_blocking_issues": len(issues) - len(blocking_rules),
            "missing_fields_count": len(missing_information),
        }

        # Maintain deterministic order
        missing_information.sort()

        return EligibilityResult(
            status=status,
            issues=issues,
            blocking_rules=blocking_rules,
            missing_information=missing_information,
            next_steps=next_steps,
            summary=summary,
        )
