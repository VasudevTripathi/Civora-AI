import os
import json
import pytest
from typing import List, Dict, Any

from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import (
    BusinessProfile,
    ApplicableRule,
    EligibilityStatus,
)
from backend.app.decision.evaluator import ConditionEvaluator
from backend.app.decision.dependency import DependencyResolver
from backend.app.decision.eligibility import EligibilityEngine

# Mock Rules for Eligibility Tests
RULE_LICENSE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "version": "1.0.0",
    "title": "Food Safety Certificate",
    "description": "Applies to food businesses.",
    "category": "Licensing",
    "authority": "Health Dept",
    "priority": 10,
    "condition": {
        "fact": "industry",
        "operator": "equal",
        "value": "restaurant"
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_NOTIFICATION = {
    "id": "22222222-2222-2222-2222-222222222222",
    "version": "1.0.0",
    "title": "Safety Warning",
    "description": "Non-blocking notification for restaurants.",
    "category": "Info",
    "authority": "Health Dept",
    "priority": 5,
    "condition": {
        "fact": "state",
        "operator": "equal",
        "value": "CA"
    },
    "action": {
        "type": "trigger_notification",
        "params": {"notification_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_EMPLOYEES = {
    "id": "33333333-3333-3333-3333-333333333333",
    "version": "1.0.0",
    "title": "OSHA Audit exemption",
    "description": "Exceeding 50 employees triggers a blocking failure.",
    "category": "Audit",
    "authority": "OSHA",
    "priority": 8,
    "condition": {
        "fact": "employees",
        "operator": "lessThan",
        "value": 50
    },
    "action": {
        "type": "apply_penalty",
        "params": {"penalty_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_PENDING_INFO = {
    "id": "44444444-4444-4444-4444-444444444444",
    "version": "1.0.0",
    "title": "Local County Health Certificate",
    "description": "Mandatory rule requiring county value.",
    "category": "Licensing",
    "authority": "County Authority",
    "priority": 12,
    "condition": {
        "fact": "county",
        "operator": "equal",
        "value": "Orange"
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "dddddddd-dddd-dddd-dddd-dddddddddddd", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_DEPENDENT = {
    "id": "55555555-5555-5555-5555-555555555555",
    "version": "1.0.0",
    "title": "High Risk Operation permit",
    "description": "Requires Food Safety Certificate to be satisfied.",
    "category": "Licensing",
    "authority": "Health Dept",
    "priority": 15,
    "dependencies": ["11111111-1111-1111-1111-111111111111"],
    "condition": {
        "fact": "industry",
        "operator": "equal",
        "value": "restaurant"
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}


@pytest.fixture
def temp_rules_dir_elig(temp_knowledge_dir):
    """
    Sets up schemas and loads rules for eligibility tests.
    """
    real_schema_path = "/media/vasu/VASUDEV/Civora AI/data/knowledge/schemas/policy_rule.schema.json"
    with open(real_schema_path, "r") as f:
        schema = json.load(f)

    with open(os.path.join(temp_knowledge_dir, "schemas", "policy_rule.schema.json"), "w") as f:
        json.dump(schema, f)

    rules = [
        RULE_LICENSE,
        RULE_NOTIFICATION,
        RULE_EMPLOYEES,
        RULE_PENDING_INFO,
        RULE_DEPENDENT
    ]
    for r in rules:
        with open(os.path.join(temp_knowledge_dir, "rules", f"{r['id']}.json"), "w") as f:
            json.dump(r, f)

    return temp_knowledge_dir


def to_app_rule(r_dict: Dict[str, Any]) -> ApplicableRule:
    return ApplicableRule(
        rule_id=r_dict["id"],
        title=r_dict.get("title") or r_dict["description"],
        description=r_dict["description"],
        category=r_dict.get("category") or "General",
        authority=r_dict.get("authority") or "Unknown",
        priority=r_dict["priority"],
        dependencies=r_dict.get("dependencies") or [],
        source=r_dict["source"]
    )


def get_profile(
    state="CA",
    industry="restaurant",
    county="Orange",
    employees=10,
    annual_revenue=50000.0
) -> BusinessProfile:
    return BusinessProfile(
        business_type="Corporation",
        state=state,
        county=county,
        city=None,
        industry=industry,
        employees=employees,
        annual_revenue=annual_revenue,
        ownership_type="private",
        is_foreign_owner=False,
        is_home_based=False,
        additional_attributes={}
    )


# ----------------------------------------------------
# Eligibility Engine Tests
# ----------------------------------------------------

def test_eligible_status(temp_rules_dir_elig):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_elig)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    engine = EligibilityEngine(policy_loader=loader)

    # Profile satisfies RULE_LICENSE, RULE_NOTIFICATION, and RULE_EMPLOYEES
    profile = get_profile(state="CA", industry="restaurant", employees=10)
    matched = [to_app_rule(RULE_LICENSE), to_app_rule(RULE_NOTIFICATION), to_app_rule(RULE_EMPLOYEES)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)

    result = engine.evaluate(profile, matched, condition_result, dependency_graph)

    assert result.status == EligibilityStatus.ELIGIBLE
    assert len(result.issues) == 0
    assert len(result.blocking_rules) == 0


def test_conditional_eligibility(temp_rules_dir_elig):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_elig)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    engine = EligibilityEngine(policy_loader=loader)

    # RULE_LICENSE (blocking) passes
    # RULE_NOTIFICATION (non-blocking, triggers on CA state) fails because state is "TX"
    profile = get_profile(state="TX", industry="restaurant")
    matched = [to_app_rule(RULE_LICENSE), to_app_rule(RULE_NOTIFICATION)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)

    result = engine.evaluate(profile, matched, condition_result, dependency_graph)

    assert result.status == EligibilityStatus.CONDITIONALLY_ELIGIBLE
    assert len(result.issues) == 1
    assert result.issues[0].blocking is False
    assert result.issues[0].severity == "WARNING"
    assert len(result.blocking_rules) == 0


def test_blocking_failure(temp_rules_dir_elig):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_elig)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    engine = EligibilityEngine(policy_loader=loader)

    # RULE_EMPLOYEES requires < 50 employees. Profile has 60 employees -> Fails
    profile = get_profile(employees=60)
    matched = [to_app_rule(RULE_LICENSE), to_app_rule(RULE_EMPLOYEES)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)

    result = engine.evaluate(profile, matched, condition_result, dependency_graph)

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert len(result.blocking_rules) == 1
    assert result.blocking_rules[0] == RULE_EMPLOYEES["id"]
    assert result.issues[0].blocking is True
    assert result.issues[0].severity == "ERROR"
    assert "workforce" in result.issues[0].recommended_action.lower()


def test_missing_information_blocking(temp_rules_dir_elig):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_elig)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    engine = EligibilityEngine(policy_loader=loader)

    # RULE_PENDING_INFO requires county, but profile county is None
    profile = get_profile(county=None)
    matched = [to_app_rule(RULE_PENDING_INFO)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)

    result = engine.evaluate(profile, matched, condition_result, dependency_graph)

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert "county" in result.missing_information
    assert len(result.blocking_rules) == 1


def test_dependency_blockers(temp_rules_dir_elig):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_elig)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    engine = EligibilityEngine(policy_loader=loader)

    # RULE_DEPENDENT depends on RULE_LICENSE.
    # If industry is "retail", RULE_LICENSE fails, so RULE_DEPENDENT becomes NOT_APPLICABLE.
    # Since RULE_DEPENDENT is blocking and not satisfied, it results in NOT_ELIGIBLE.
    profile = get_profile(industry="retail")
    matched = [to_app_rule(RULE_LICENSE), to_app_rule(RULE_DEPENDENT)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)

    result = engine.evaluate(profile, matched, condition_result, dependency_graph)

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert len(result.blocking_rules) == 2  # Both failed/not applicable
