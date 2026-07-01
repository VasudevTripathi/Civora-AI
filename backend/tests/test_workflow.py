import os
import json
import pytest
from typing import List, Dict, Any

from backend.app.services.policy_loader import PolicyLoader
from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.decision.models import (
    BusinessProfile,
    ApplicableRule,
    RuleEngineResult,
    EligibilityStatus,
    WorkflowStatus,
)
from backend.app.decision.engine import RuleEngine
from backend.app.decision.evaluator import ConditionEvaluator
from backend.app.decision.dependency import DependencyResolver
from backend.app.decision.eligibility import EligibilityEngine
from backend.app.decision.workflow import WorkflowEngine

# UUIDs for linking metadata
DOC_UUID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
TIMELINE_UUID = "tttttttt-tttt-tttt-tttt-tttttttttttt"
LICENSE_UUID = "llllllll-llll-llll-llll-llllllllllll"

RULE_A = {
    "id": "11111111-1111-1111-1111-111111111111",
    "version": "1.0.0",
    "title": "Rule A License",
    "description": "Requires Food Safety License.",
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
        "params": {"license_uuid": LICENSE_UUID, "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_B = {
    "id": "22222222-2222-2222-2222-222222222222",
    "version": "1.0.0",
    "title": "Rule B Audit",
    "description": "Audit for safety compliance.",
    "category": "Audit",
    "authority": "Audit Dept",
    "priority": 20,
    "dependencies": ["11111111-1111-1111-1111-111111111111"],
    "condition": {
        "fact": "state",
        "operator": "equal",
        "value": "CA"
    },
    "action": {
        "type": "apply_penalty",
        "params": {"penalty_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_C = {
    "id": "33333333-3333-3333-3333-333333333333",
    "version": "1.0.0",
    "title": "Rule C Warning",
    "description": "Non-blocking safety recommendation.",
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


RULE_D = {
    "id": "44444444-4444-4444-4444-444444444444",
    "version": "1.0.0",
    "title": "Rule D",
    "description": "Diamond Target D",
    "category": "Licensing",
    "authority": "Auth D",
    "priority": 25,
    "dependencies": ["22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"],
    "condition": {
        "fact": "state",
        "operator": "equal",
        "value": "CA"
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "44444444-dddd-dddd-dddd-dddddddddddd", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}

RULE_E = {
    "id": "55555555-5555-5555-5555-555555555555",
    "version": "1.0.0",
    "title": "Rule E",
    "description": "Post-Diamond Link E",
    "category": "Licensing",
    "authority": "Auth E",
    "priority": 30,
    "dependencies": ["44444444-4444-4444-4444-444444444444"],
    "condition": {
        "fact": "state",
        "operator": "equal",
        "value": "CA"
    },
    "action": {
        "type": "require_license",
        "params": {"license_uuid": "55555555-dddd-dddd-dddd-dddddddddddd", "value": True}
    },
    "effective_date": "2026-01-01",
    "source": "https://test.gov"
}


@pytest.fixture
def temp_knowledge_dir_wf(temp_knowledge_dir):
    """
    Writes rules, schemas, licenses, documents, and timelines into temp folders.
    """
    # Create subdirectories if they do not exist
    os.makedirs(os.path.join(temp_knowledge_dir, "schemas"), exist_ok=True)
    os.makedirs(os.path.join(temp_knowledge_dir, "rules"), exist_ok=True)
    os.makedirs(os.path.join(temp_knowledge_dir, "licenses"), exist_ok=True)
    os.makedirs(os.path.join(temp_knowledge_dir, "documents"), exist_ok=True)
    os.makedirs(os.path.join(temp_knowledge_dir, "timelines"), exist_ok=True)

    # 1. Schemas
    schema_names = [
        "policy_rule.schema.json",
        "license.schema.json",
        "document.schema.json",
        "timeline.schema.json",
    ]
    for s_name in schema_names:
        real_path = os.path.join(
            "/media/vasu/VASUDEV/Civora AI/data/knowledge/schemas", s_name
        )
        with open(real_path, "r") as f:
            schema = json.load(f)
        with open(os.path.join(temp_knowledge_dir, "schemas", s_name), "w") as f:
            json.dump(schema, f)

    # 2. Write Rules
    rules = [RULE_A, RULE_B, RULE_C, RULE_D, RULE_E]
    for r in rules:
        with open(
            os.path.join(temp_knowledge_dir, "rules", f"{r['id']}.json"), "w"
        ) as f:
            json.dump(r, f)

    # 3. Write Document Metadata
    doc_node = {
        "uuid": DOC_UUID,
        "version": "1.0.0",
        "last_updated": "2026-01-01T00:00:00Z",
        "verification_status": "certified",
        "source": "https://test.gov",
        "applicable_state": "CA",
        "applicable_district": None,
        "confidence": 1.0,
        "document_name": "Food Handler Permit Form",
        "allowed_extensions": ["pdf"],
    }
    with open(
        os.path.join(temp_knowledge_dir, "documents", f"{DOC_UUID}.json"), "w"
    ) as f:
        json.dump(doc_node, f)

    # 4. Write Timeline Metadata
    timeline_node = {
        "uuid": TIMELINE_UUID,
        "version": "1.0.0",
        "last_updated": "2026-01-01T00:00:00Z",
        "verification_status": "certified",
        "source": "https://test.gov",
        "applicable_state": "CA",
        "applicable_district": None,
        "confidence": 1.0,
        "processing_duration_days": 15,
        "sla_type": "Estimated",
    }
    with open(
        os.path.join(temp_knowledge_dir, "timelines", f"{TIMELINE_UUID}.json"), "w"
    ) as f:
        json.dump(timeline_node, f)

    # 5. Write License Metadata
    license_node = {
        "uuid": LICENSE_UUID,
        "version": "1.0.0",
        "last_updated": "2026-01-01T00:00:00Z",
        "verification_status": "certified",
        "source": "https://test.gov",
        "applicable_state": "CA",
        "confidence": 1.0,
        "license_name": "Food Safety License",
        "authority_uuid": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        "governing_rule_uuid": RULE_A["id"],
        "required_document_uuids": [DOC_UUID],
        "fee_uuids": [],
        "timeline_uuid": TIMELINE_UUID,
    }
    with open(
        os.path.join(temp_knowledge_dir, "licenses", f"{LICENSE_UUID}.json"), "w"
    ) as f:
        json.dump(license_node, f)

    return temp_knowledge_dir


def to_app_rule(r_dict: Dict[str, Any]) -> ApplicableRule:
    return ApplicableRule(
        rule_id=r_dict["id"],
        title=r_dict["title"],
        description=r_dict["description"],
        category=r_dict["category"],
        authority=r_dict["authority"],
        priority=r_dict["priority"],
        dependencies=r_dict.get("dependencies") or [],
        source=r_dict["source"],
    )


def get_profile(
    state="CA",
    industry="restaurant",
    county="Orange",
    employees=10,
) -> BusinessProfile:
    return BusinessProfile(
        business_type="Corporation",
        state=state,
        county=county,
        city=None,
        industry=industry,
        employees=employees,
        annual_revenue=10000.0,
        ownership_type="private",
        is_foreign_owner=False,
        is_home_based=False,
        additional_attributes={},
    )


# ----------------------------------------------------
# Workflow Engine Tests
# ----------------------------------------------------

def test_linear_workflow_generation(temp_knowledge_dir_wf):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir_wf)
    k_loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir_wf)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    eligibility_eng = EligibilityEngine(policy_loader=loader)
    wf_engine = WorkflowEngine(policy_loader=loader, knowledge_loader=k_loader)

    # RULE_A -> RULE_B
    profile = get_profile()
    matched = [to_app_rule(RULE_A), to_app_rule(RULE_B)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)
    eligibility_result = eligibility_eng.evaluate(
        profile, matched, condition_result, dependency_graph
    )

    wf_result = wf_engine.generate(
        profile,
        RuleEngineResult(profile=profile, matched_rules=matched),
        condition_result,
        dependency_graph,
        eligibility_result,
    )

    assert eligibility_result.status == EligibilityStatus.ELIGIBLE
    assert len(wf_result.steps) == 2

    step_a = wf_result.steps[RULE_A["id"]]
    assert step_a.status == WorkflowStatus.AVAILABLE
    assert "Food Handler Permit Form" in step_a.required_documents
    assert step_a.estimated_duration == "15 days"

    step_b = wf_result.steps[RULE_B["id"]]
    # Since step_a is not COMPLETED, step_b is BLOCKED waiting on A
    assert step_b.status == WorkflowStatus.BLOCKED
    assert RULE_A["id"] in step_b.dependencies


def test_conditional_eligibility_workflow(temp_knowledge_dir_wf):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir_wf)
    k_loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir_wf)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    eligibility_eng = EligibilityEngine(policy_loader=loader)
    wf_engine = WorkflowEngine(policy_loader=loader, knowledge_loader=k_loader)

    # RULE_C (non-blocking) fails because state is TX
    profile = get_profile(state="TX")
    matched = [to_app_rule(RULE_A), to_app_rule(RULE_C)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)
    eligibility_result = eligibility_eng.evaluate(
        profile, matched, condition_result, dependency_graph
    )

    assert eligibility_result.status == EligibilityStatus.CONDITIONALLY_ELIGIBLE

    wf_result = wf_engine.generate(
        profile,
        RuleEngineResult(profile=profile, matched_rules=matched),
        condition_result,
        dependency_graph,
        eligibility_result,
    )

    assert len(wf_result.steps) == 2
    # Rule C was conditionally failed, so its step status is BLOCKED
    assert wf_result.steps[RULE_C["id"]].status == WorkflowStatus.BLOCKED


def test_non_eligible_empty_workflow(temp_knowledge_dir_wf):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir_wf)
    k_loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir_wf)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    eligibility_eng = EligibilityEngine(policy_loader=loader)
    wf_engine = WorkflowEngine(policy_loader=loader, knowledge_loader=k_loader)

    # RULE_A (blocking) fails because industry is retail
    profile = get_profile(industry="retail")
    matched = [to_app_rule(RULE_A)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)
    eligibility_result = eligibility_eng.evaluate(
        profile, matched, condition_result, dependency_graph
    )

    assert eligibility_result.status == EligibilityStatus.NOT_ELIGIBLE

    wf_result = wf_engine.generate(
        profile,
        RuleEngineResult(profile=profile, matched_rules=matched),
        condition_result,
        dependency_graph,
        eligibility_result,
    )

    assert len(wf_result.steps) == 0
    assert wf_result.summary["status"] == "NOT_ELIGIBLE"
    assert "explanation" in wf_result.summary


def test_critical_path_and_completion_percentage(temp_knowledge_dir_wf):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir_wf)
    k_loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir_wf)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    eligibility_eng = EligibilityEngine(policy_loader=loader)
    wf_engine = WorkflowEngine(policy_loader=loader, knowledge_loader=k_loader)

    # Chain: A -> B
    profile = get_profile()
    matched = [to_app_rule(RULE_A), to_app_rule(RULE_B)]

    condition_result = evaluator.evaluate(profile, matched)
    dependency_graph = resolver.build_graph(matched, condition_result.evaluations)
    eligibility_result = eligibility_eng.evaluate(
        profile, matched, condition_result, dependency_graph
    )

    wf_result = wf_engine.generate(
        profile,
        RuleEngineResult(profile=profile, matched_rules=matched),
        condition_result,
        dependency_graph,
        eligibility_result,
    )

    # Structural critical path of longest dependency chain
    assert wf_result.critical_path == [RULE_A["id"], RULE_B["id"]]

    # Default completion is 0.0
    assert wf_result.completion_percentage == 0.0

    # Simulate persistence marking step A as COMPLETED
    wf_result.steps[RULE_A["id"]].status = WorkflowStatus.COMPLETED
    # Recalculate
    new_pct = wf_engine.calculate_completion_percentage(wf_result.steps)
    assert new_pct == 50.0


def test_complex_topologies_and_critical_path(temp_knowledge_dir_wf):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir_wf)
    k_loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir_wf)
    evaluator = ConditionEvaluator(policy_loader=loader)
    resolver = DependencyResolver()
    eligibility_eng = EligibilityEngine(policy_loader=loader)
    wf_engine = WorkflowEngine(policy_loader=loader, knowledge_loader=k_loader)

    # Let's create a custom list of rules to make a Diamond + Extra branch:
    # A
    # B (deps: A)
    # C (deps: A)
    # D (deps: B, C)
    # E (deps: D)
    # This forms a diamond and then a linear link.
    rules = [
        to_app_rule(RULE_A), # ID: 11111111...
        to_app_rule(RULE_B), # ID: 22222222... (deps: A)
        ApplicableRule(
            rule_id="33333333-3333-3333-3333-333333333333",
            title="Rule C",
            description="Branch C",
            category="Licensing",
            authority="Auth C",
            priority=15,
            dependencies=["11111111-1111-1111-1111-111111111111"],
            source="https://test.gov"
        ),
        ApplicableRule(
            rule_id="44444444-4444-4444-4444-444444444444",
            title="Rule D",
            description="Diamond Target D",
            category="Licensing",
            authority="Auth D",
            priority=25,
            dependencies=["22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"],
            source="https://test.gov"
        ),
        ApplicableRule(
            rule_id="55555555-5555-5555-5555-555555555555",
            title="Rule E",
            description="Post-Diamond Link E",
            category="Licensing",
            authority="Auth E",
            priority=30,
            dependencies=["44444444-4444-4444-4444-444444444444"],
            source="https://test.gov"
        )
    ]

    profile = get_profile()
    condition_result = evaluator.evaluate(profile, rules)
    dependency_graph = resolver.build_graph(rules, condition_result.evaluations)
    eligibility_result = eligibility_eng.evaluate(
        profile, rules, condition_result, dependency_graph
    )

    wf_result = wf_engine.generate(
        profile,
        RuleEngineResult(profile=profile, matched_rules=rules),
        condition_result,
        dependency_graph,
        eligibility_result,
    )

    # The critical path should go A -> (B or C) -> D -> E
    assert len(wf_result.critical_path) == 4
    assert wf_result.critical_path[0] == "11111111-1111-1111-1111-111111111111"
    assert wf_result.critical_path[2] == "44444444-4444-4444-4444-444444444444"
    assert wf_result.critical_path[3] == "55555555-5555-5555-5555-555555555555"
