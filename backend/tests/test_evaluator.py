import os
import json
import pytest
from typing import Dict, Any

from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import BusinessProfile, ApplicableRule, ConditionStatus
from backend.app.decision.evaluator import ConditionEvaluator

# Mock Rules for Evaluator Tests
RULE_SATISFIED = {
    "id": "10000000-1000-1000-1000-100000000000",
    "version": "1.0.0",
    "title": "CA Restaurant Permit",
    "description": "Applies to California restaurants.",
    "category": "Licensing",
    "authority": "CA Health Dept",
    "priority": 10,
    "condition": {
        "all": [
            {"fact": "state", "operator": "equal", "value": "CA"},
            {"fact": "industry", "operator": "equal", "value": "restaurant"}
        ]
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://ca.gov"
}

RULE_FAILED = {
    "id": "20000000-2000-2000-2000-200000000000",
    "version": "1.0.0",
    "title": "Large Company OSHA Audit",
    "description": "Applies to businesses with more than 100 employees.",
    "category": "Audit",
    "authority": "OSHA",
    "priority": 5,
    "condition": {
        "fact": "employees",
        "operator": "greaterThan",
        "value": 100
    },
    "action": {
        "type": "trigger_notification",
        "params": {"notification_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://osha.gov"
}

RULE_PENDING = {
    "id": "30000000-3000-3000-3000-300000000000",
    "version": "1.0.0",
    "title": "Local County Health Certificate",
    "description": "Applies to restaurants in a specific county.",
    "category": "Licensing",
    "authority": "County Authority",
    "priority": 15,
    "condition": {
        "all": [
            {"fact": "industry", "operator": "equal", "value": "restaurant"},
            {"fact": "county", "operator": "equal", "value": "Orange"}
        ]
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://county.gov"
}

RULE_COMPLEX_NESTED = {
    "id": "40000000-4000-4000-4000-400000000000",
    "version": "1.0.0",
    "title": "Special Regional Commerce Incentive",
    "description": "Applies to NY retail OR TX agriculture.",
    "category": "Incentive",
    "authority": "Regional Board",
    "priority": 8,
    "condition": {
        "any": [
            {
                "all": [
                    {"fact": "state", "operator": "equal", "value": "NY"},
                    {"fact": "industry", "operator": "equal", "value": "retail"}
                ]
            },
            {
                "all": [
                    {"fact": "state", "operator": "equal", "value": "TX"},
                    {"fact": "industry", "operator": "equal", "value": "agriculture"}
                ]
            }
        ]
    },
    "action": {
        "type": "exempt_license",
        "params": {"license_uuid": "dddddddd-dddd-dddd-dddd-dddddddddddd", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://regional.gov"
}

RULE_DEPENDENT_SATISFIED = {
    "id": "50000000-5000-5000-5000-500000000000",
    "version": "1.0.0",
    "title": "Dependent Food Permit",
    "description": "Requires CA Restaurant Permit to be satisfied.",
    "category": "Licensing",
    "authority": "CA Health",
    "priority": 12,
    "dependencies": ["10000000-1000-1000-1000-100000000000"],
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
    "source": "https://ca.gov"
}

RULE_DEPENDENT_NOT_APPLICABLE = {
    "id": "60000000-6000-6000-6000-600000000000",
    "version": "1.0.0",
    "title": "OSHA High Risk Followup",
    "description": "Depends on OSHA audit being satisfied.",
    "category": "Audit",
    "authority": "OSHA",
    "priority": 4,
    "dependencies": ["20000000-2000-2000-2000-200000000000"],
    "condition": {
        "fact": "employees",
        "operator": "greaterThan",
        "value": 100
    },
    "action": {
        "type": "trigger_notification",
        "params": {"notification_uuid": "ffffffff-ffff-ffff-ffff-ffffffffffff", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://osha.gov"
}

RULE_BOUNDARY_CHECK = {
    "id": "70000000-7000-7000-7000-700000000000",
    "version": "1.0.0",
    "title": "Boundary Employee Rules",
    "description": "Applies to businesses with 50 or more employees.",
    "category": "Audit",
    "authority": "State Audit",
    "priority": 25,
    "condition": {
        "fact": "employees",
        "operator": "greaterThanOrEqual",
        "value": 50
    },
    "action": {
        "type": "trigger_notification",
        "params": {"notification_uuid": "gggggggg-gggg-gggg-gggg-gggggggggggg", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://state.gov"
}


@pytest.fixture
def temp_rules_dir_eval(temp_knowledge_dir):
    """
    Sets up the schemas and loads rules for evaluator tests.
    """
    real_schema_path = "/media/vasu/VASUDEV/Civora AI/data/knowledge/schemas/policy_rule.schema.json"
    with open(real_schema_path, "r") as f:
        schema = json.load(f)

    with open(os.path.join(temp_knowledge_dir, "schemas", "policy_rule.schema.json"), "w") as f:
        json.dump(schema, f)

    # Write all rules
    rules = [
        RULE_SATISFIED,
        RULE_FAILED,
        RULE_PENDING,
        RULE_COMPLEX_NESTED,
        RULE_DEPENDENT_SATISFIED,
        RULE_DEPENDENT_NOT_APPLICABLE,
        RULE_BOUNDARY_CHECK
    ]
    for r in rules:
        with open(os.path.join(temp_knowledge_dir, "rules", f"{r['id']}.json"), "w") as f:
            json.dump(r, f)

    return temp_knowledge_dir


def to_applicable_rule(r_dict: Dict[str, Any]) -> ApplicableRule:
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


def get_mock_profile(
    state="CA",
    industry="restaurant",
    county=None,
    employees=10,
    annual_revenue=50000.0,
    additional_attributes=None
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
        additional_attributes=additional_attributes or {}
    )


# ----------------------------------------------------
# Evaluator tests
# ----------------------------------------------------

def test_satisfied_and_failed_conditions(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)

    # Profile: CA restaurant with 10 employees (satisfies RULE_SATISFIED, fails RULE_FAILED)
    profile = get_mock_profile(state="CA", industry="restaurant", employees=10)
    matched = [to_applicable_rule(RULE_SATISFIED), to_applicable_rule(RULE_FAILED)]

    result = evaluator.evaluate(profile, matched)

    # Check summary stats
    assert result.summary["satisfied"] == 1
    assert result.summary["failed"] == 1

    # Check detail evaluations
    eval_satisfied = next(e for e in result.evaluations if e.rule_id == RULE_SATISFIED["id"])
    assert eval_satisfied.status == ConditionStatus.SATISFIED
    assert eval_satisfied.reason == "All conditions were successfully satisfied."
    assert len(eval_satisfied.missing_fields) == 0

    eval_failed = next(e for e in result.evaluations if e.rule_id == RULE_FAILED["id"])
    assert eval_failed.status == ConditionStatus.FAILED
    assert "applicability conditions were not met" in eval_failed.reason.lower()


def test_pending_information_status(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)

    # Profile lacks county (county=None), which is required by RULE_PENDING
    profile = get_mock_profile(state="CA", industry="restaurant", county=None)
    matched = [to_applicable_rule(RULE_PENDING)]

    result = evaluator.evaluate(profile, matched)

    assert result.summary["pending"] == 1
    eval_pending = result.evaluations[0]
    assert eval_pending.status == ConditionStatus.PENDING_INFORMATION
    assert "county" in eval_pending.missing_fields
    assert "Required profile attributes are missing" in eval_pending.reason


def test_complex_and_or_nesting(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)

    matched = [to_applicable_rule(RULE_COMPLEX_NESTED)]

    # 1. Matches first sub-condition (NY + retail)
    profile1 = get_mock_profile(state="NY", industry="retail")
    res1 = evaluator.evaluate(profile1, matched)
    assert res1.summary["satisfied"] == 1

    # 2. Matches second sub-condition (TX + agriculture)
    profile2 = get_mock_profile(state="TX", industry="agriculture")
    res2 = evaluator.evaluate(profile2, matched)
    assert res2.summary["satisfied"] == 1

    # 3. Fails both sub-conditions (CA + retail)
    profile3 = get_mock_profile(state="CA", industry="retail")
    res3 = evaluator.evaluate(profile3, matched)
    assert res3.summary["failed"] == 1


def test_dependency_propagation_not_applicable(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)

    # RULE_DEPENDENT_SATISFIED depends on RULE_SATISFIED (which is satisfied)
    # RULE_DEPENDENT_NOT_APPLICABLE depends on RULE_FAILED (which fails)
    profile = get_mock_profile(state="CA", industry="restaurant", employees=10)
    matched = [
        to_applicable_rule(RULE_SATISFIED),
        to_applicable_rule(RULE_FAILED),
        to_applicable_rule(RULE_DEPENDENT_SATISFIED),
        to_applicable_rule(RULE_DEPENDENT_NOT_APPLICABLE)
    ]

    result = evaluator.evaluate(profile, matched)

    assert result.summary["satisfied"] == 2  # RULE_SATISFIED and RULE_DEPENDENT_SATISFIED
    assert result.summary["failed"] == 1     # RULE_FAILED
    assert result.summary["not_applicable"] == 1  # RULE_DEPENDENT_NOT_APPLICABLE

    eval_dep_ok = next(e for e in result.evaluations if e.rule_id == RULE_DEPENDENT_SATISFIED["id"])
    assert eval_dep_ok.status == ConditionStatus.SATISFIED

    eval_dep_na = next(e for e in result.evaluations if e.rule_id == RULE_DEPENDENT_NOT_APPLICABLE["id"])
    assert eval_dep_na.status == ConditionStatus.NOT_APPLICABLE
    assert "dependency rules were not satisfied" in eval_dep_na.reason


def test_boundary_values(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)
    matched = [to_applicable_rule(RULE_BOUNDARY_CHECK)]

    # 1. Just below threshold (49 employees) -> FAILED
    profile_below = get_mock_profile(employees=49)
    result_below = evaluator.evaluate(profile_below, matched)
    assert result_below.evaluations[0].status == ConditionStatus.FAILED

    # 2. Exactly at threshold (50 employees) -> SATISFIED (gte check)
    profile_exact = get_mock_profile(employees=50)
    result_exact = evaluator.evaluate(profile_exact, matched)
    assert result_exact.evaluations[0].status == ConditionStatus.SATISFIED

    # 3. Just above threshold (51 employees) -> SATISFIED
    profile_above = get_mock_profile(employees=51)
    result_above = evaluator.evaluate(profile_above, matched)
    assert result_above.evaluations[0].status == ConditionStatus.SATISFIED


def test_missing_rule_definition_handling(temp_rules_dir_eval):
    loader = PolicyLoader(knowledge_dir=temp_rules_dir_eval)
    evaluator = ConditionEvaluator(policy_loader=loader)

    # Create a mock rule that exists in matched rules list but not in policy rules directory
    non_existent_rule = ApplicableRule(
        rule_id="99999999-9999-9999-9999-999999999999",
        title="Ghost Rule",
        description="Not found rule",
        category="Licensing",
        authority="Ghost Authority",
        priority=100,
        dependencies=[],
        source="https://ghost.gov"
    )

    profile = get_mock_profile()
    result = evaluator.evaluate(profile, [non_existent_rule])

    # Should gracefully capture as FAILED and report that rule definition was not found
    assert result.summary["failed"] == 1
    eval_ghost = result.evaluations[0]
    assert eval_ghost.status == ConditionStatus.FAILED
    assert "not found" in eval_ghost.reason.lower()
