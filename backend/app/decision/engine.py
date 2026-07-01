from typing import Any, Dict, List, Set, Tuple
from loguru import logger

from backend.app.core.exceptions import PolicyLoadError
from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import BusinessProfile, ApplicableRule, RuleEngineResult


def resolve_fact(profile: BusinessProfile, fact: str) -> Tuple[Any, bool]:
    """
    Resolves the fact value from the profile.
    Returns a tuple of (value, exists).
    """
    # 1. Direct attribute of BusinessProfile
    if hasattr(profile, fact):
        val = getattr(profile, fact)
        # Note: if it's a field but set to None, we treat it as not existing
        return val, (val is not None)

    # 2. Check if the fact is a nested path inside additional_attributes, e.g. "additional_attributes.key"
    if fact.startswith("additional_attributes."):
        parts = fact.split(".", 1)
        key = parts[1]
        if profile.additional_attributes and key in profile.additional_attributes:
            val = profile.additional_attributes[key]
            return val, (val is not None)
        return None, False

    # 3. Direct key in additional_attributes as fallback
    if profile.additional_attributes and fact in profile.additional_attributes:
        val = profile.additional_attributes[fact]
        return val, (val is not None)

    return None, False


def evaluate_condition(condition: Dict[str, Any], profile: BusinessProfile, missing: Set[str]) -> bool:
    """
    Evaluates a condition recursively.
    Updates the 'missing' set with facts that were accessed but missing (None/not present) in the profile.
    """
    # 1. Logical OR (any)
    if "any" in condition:
        results = []
        for cond in condition["any"]:
            results.append(evaluate_condition(cond, profile, missing))
        return any(results) if results else False

    # 2. Logical AND (all)
    if "all" in condition:
        results = []
        for cond in condition["all"]:
            results.append(evaluate_condition(cond, profile, missing))
        return all(results) if results else True

    # 3. Logical NOT (not)
    if "not" in condition:
        return not evaluate_condition(condition["not"], profile, missing)

    # 4. Simple condition
    fact = condition.get("fact")
    operator = condition.get("operator")
    value = condition.get("value")

    if not fact or not operator:
        return False

    val, exists = resolve_fact(profile, fact)

    # Handle exists operator
    normalized_op = operator.lower().replace("_", "")
    if normalized_op == "exists":
        expected_existence = bool(value)
        return exists == expected_existence

    if not exists:
        # Fact is missing from profile
        missing.add(fact)
        return False

    # Evaluate other operators
    try:
        if normalized_op in ("equal", "equals"):
            return val == value
        elif normalized_op in ("notequal", "not_equals", "notequals"):
            return val != value
        elif normalized_op in ("greaterthan", "gt"):
            return val > value
        elif normalized_op in ("greaterthanorequal", "gte"):
            return val >= value
        elif normalized_op in ("lessthan", "lt"):
            return val < value
        elif normalized_op in ("lessthanorequal", "lte"):
            return val <= value
        elif normalized_op == "in":
            # value should be a list/set/tuple
            return val in value
        elif normalized_op in ("notin", "not_in"):
            return val not in value
        elif normalized_op == "contains":
            # val should be a list/set/string
            return value in val
        else:
            return False
    except Exception as e:
        logger.warning(f"Error evaluating condition for fact '{fact}' with operator '{operator}': {e}")
        return False


def validate_rule_semantics(rule: Dict[str, Any]) -> None:
    """Validates that a rule is semantically correct."""
    if "id" not in rule or "description" not in rule or "condition" not in rule:
        raise PolicyLoadError(f"Rule is missing critical fields: {rule.get('id', 'unknown')}")
    _validate_condition_semantics(rule["condition"])


def _validate_condition_semantics(condition: Dict[str, Any]) -> None:
    if "all" in condition:
        if not isinstance(condition["all"], list):
            raise PolicyLoadError("'all' condition must be a list")
        for sub in condition["all"]:
            _validate_condition_semantics(sub)
    elif "any" in condition:
        if not isinstance(condition["any"], list):
            raise PolicyLoadError("'any' condition must be a list")
        for sub in condition["any"]:
            _validate_condition_semantics(sub)
    elif "not" in condition:
        if not isinstance(condition["not"], dict):
            raise PolicyLoadError("'not' condition must be an object")
        _validate_condition_semantics(condition["not"])
    else:
        # Simple condition
        fact = condition.get("fact")
        operator = condition.get("operator")
        # Note: value can be None, so we check if key exists
        if not fact or not operator or "value" not in condition:
            raise PolicyLoadError(f"Condition is missing 'fact', 'operator', or 'value': {condition}")

        valid_ops = {
            "equal", "equals",
            "notequal", "not_equals", "notequals",
            "greaterthan", "greater_than", "gt",
            "greaterthanorequal", "greater_than_or_equal", "gte",
            "lessthan", "less_than", "lt",
            "lessthanorequal", "less_than_or_equal", "lte",
            "in", "notin", "not_in",
            "contains", "exists"
        }
        if operator.lower().replace("_", "") not in valid_ops:
            raise PolicyLoadError(f"Unsupported condition operator: '{operator}'")


class RuleEngine:
    def __init__(self, policy_loader: PolicyLoader):
        self.policy_loader = policy_loader
        self.rules: List[Dict[str, Any]] = []

    def load_rules(self) -> None:
        """Loads and validates policy rules from the policy loader."""
        raw_rules = self.policy_loader.load_all_rules()
        valid_rules = []
        for r in raw_rules:
            validate_rule_semantics(r)
            valid_rules.append(r)
        self.rules = valid_rules
        logger.info(f"RuleEngine loaded and validated {len(self.rules)} rules.")

    def match(self, profile: BusinessProfile) -> RuleEngineResult:
        """
        Matches the business profile against loaded rules.
        Returns a RuleEngineResult containing matched rules, warnings, and missing information.
        """
        matched_rules_dicts = []
        global_missing: Set[str] = set()

        for rule in self.rules:
            rule_missing: Set[str] = set()

            # 1. Evaluate condition
            condition_matched = evaluate_condition(rule["condition"], profile, rule_missing)

            # 2. Evaluate exceptions
            exception_matched = False
            if "exceptions" in rule and rule["exceptions"]:
                for exc in rule["exceptions"]:
                    if evaluate_condition(exc, profile, rule_missing):
                        exception_matched = True
                        break

            # Rule matches if the condition is met and no exceptions are met
            if condition_matched and not exception_matched:
                matched_rules_dicts.append(rule)

            # Keep track of missing facts encountered
            global_missing.update(rule_missing)

        # Resolve dependencies
        resolved_rules = {r["id"]: r for r in matched_rules_dicts}
        removed_any = True
        warnings = []

        while removed_any:
            removed_any = False
            to_remove = []
            for rule_id, rule in list(resolved_rules.items()):
                dependencies = rule.get("dependencies", [])
                for dep_id in dependencies:
                    if dep_id not in resolved_rules:
                        to_remove.append((rule_id, dep_id))
                        break

            for rule_id, dep_id in to_remove:
                if rule_id in resolved_rules:
                    del resolved_rules[rule_id]
                    warnings.append(
                        f"Rule '{rule_id}' was excluded because its dependency '{dep_id}' was not satisfied."
                    )
                    removed_any = True

        # Map to ApplicableRule Pydantic models
        final_matched_rules = []
        for r in resolved_rules.values():
            final_matched_rules.append(
                ApplicableRule(
                    rule_id=r["id"],
                    title=r.get("title") or r["description"],
                    description=r["description"],
                    category=r.get("category") or "General",
                    authority=r.get("authority") or "Unknown",
                    priority=r["priority"],
                    dependencies=r.get("dependencies") or [],
                    source=r["source"],
                )
            )

        # Sort final matched rules by priority (highest first)
        final_matched_rules.sort(key=lambda x: x.priority, reverse=True)

        return RuleEngineResult(
            profile=profile,
            matched_rules=final_matched_rules,
            warnings=warnings,
            missing_information=sorted(list(global_missing)),
        )
