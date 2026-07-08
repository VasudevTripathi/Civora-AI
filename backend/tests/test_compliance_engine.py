import os
import json
import tempfile
import pytest
from pydantic import ValidationError

from backend.app.compliance.engine import ComplianceEngine
from backend.app.compliance.models import CompliancePlan
from backend.app.decision.models import BusinessProfile, EligibilityStatus, WorkflowStatus


@pytest.fixture
def prod_knowledge_dir() -> str:
    """
    Returns the absolute path to the production knowledge directory.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "knowledge")


def test_successful_delaware_llc_generation_e2e(prod_knowledge_dir):
    """
    Tests successful compliance plan generation end-to-end against the
    Delaware LLC Knowledge Pack.
    """
    engine = ComplianceEngine(knowledge_dir=prod_knowledge_dir)

    profile = BusinessProfile(
        business_type="LLC",
        state="DE",
        industry="General Business",
        employees=5,
        annual_revenue=200000.0,
        ownership_type="LLC",
        is_foreign_owner=False,
        is_home_based=False,
        additional_attributes={}
    )

    plan = engine.generate_plan(profile)

    assert isinstance(plan, CompliancePlan)
    assert plan.profile.state == "DE"
    assert plan.profile.business_type == "LLC"
    
    # Assert matched rules are loaded and matched
    assert len(plan.matched_rules) >= 2
    rule_ids = {r.rule_id for r in plan.matched_rules}
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0020" in rule_ids  # Formation Rule
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0021" in rule_ids  # Business License Rule

    # Assert eligibility result
    assert plan.eligibility_result.status == EligibilityStatus.ELIGIBLE
    assert len(plan.eligibility_result.blocking_rules) == 0

    # Assert workflow generation
    assert len(plan.workflow_result.steps) >= 2
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0020" in plan.workflow_result.steps
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0021" in plan.workflow_result.steps

    # Check status and sequencing:
    # Formation Rule (no dependencies) -> AVAILABLE
    # Business License Rule (depends on Formation) -> BLOCKED
    formation_step = plan.workflow_result.steps["8e8d89e5-9c88-469b-8e1d-384a28bb0020"]
    license_step = plan.workflow_result.steps["8e8d89e5-9c88-469b-8e1d-384a28bb0021"]
    
    assert formation_step.status == WorkflowStatus.AVAILABLE
    assert license_step.status == WorkflowStatus.BLOCKED
    assert formation_step.rule_id in license_step.dependencies


def test_missing_profile_fields():
    """
    Tests that missing required profile fields trigger a Pydantic ValidationError.
    """
    with pytest.raises(ValidationError):
        # Missing state, industry, employees, annual_revenue, ownership_type, etc.
        BusinessProfile(
            business_type="LLC"
        )


def test_no_matching_rules(prod_knowledge_dir):
    """
    Tests that a profile matching no active rules (e.g. state CA, business Corporation)
    generates a clean plan with empty matched rules and empty workflow steps.
    """
    engine = ComplianceEngine(knowledge_dir=prod_knowledge_dir)

    profile = BusinessProfile(
        business_type="Corporation",
        state="CA",
        industry="Technology",
        employees=15,
        annual_revenue=1500000.0,
        ownership_type="Corporation",
        is_foreign_owner=False,
        is_home_based=False,
        additional_attributes={}
    )

    plan = engine.generate_plan(profile)

    assert isinstance(plan, CompliancePlan)
    assert len(plan.matched_rules) == 0
    assert len(plan.workflow_result.steps) == 0


def test_eligibility_failures_and_blocking(prod_knowledge_dir):
    """
    Tests the engine handling of eligibility failures and blocking issues.
    We set up a temporary environment with a blocking rule (e.g. employee count limit).
    """
    # 1. Read real policy_rule schema
    real_schema_path = os.path.join(prod_knowledge_dir, "schemas", "policy_rule.schema.json")
    with open(real_schema_path, "r", encoding="utf-8") as f:
        policy_schema = json.load(f)

    real_rule_schema_path = os.path.join(prod_knowledge_dir, "schemas", "rule.schema.json")
    with open(real_rule_schema_path, "r", encoding="utf-8") as f:
        rule_schema = json.load(f)

    # 2. Setup temp directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "schemas"))
        os.makedirs(os.path.join(tmpdir, "rules"))
        os.makedirs(os.path.join(tmpdir, "businesses"))
        os.makedirs(os.path.join(tmpdir, "licenses"))
        os.makedirs(os.path.join(tmpdir, "timelines"))
        os.makedirs(os.path.join(tmpdir, "fees"))
        os.makedirs(os.path.join(tmpdir, "documents"))

        # Write schemas
        with open(os.path.join(tmpdir, "schemas", "policy_rule.schema.json"), "w", encoding="utf-8") as f:
            json.dump(policy_schema, f)
        with open(os.path.join(tmpdir, "schemas", "rule.schema.json"), "w", encoding="utf-8") as f:
            json.dump(rule_schema, f)

        # Write blocking rule (employees must exist, but has missing_attribute exception)
        blocking_rule = {
            "id": "99999999-9999-9999-9999-999999999999",
            "uuid": "99999999-9999-9999-9999-999999999999",
            "type": "rule",
            "jurisdiction": "DE",
            "authority": "OSHA",
            "title": "Employee Limit Rule",
            "description": "Requires missing_attribute to not be some_value.",
            "effective_date": "2026-01-01",
            "version": "1.0.0",
            "source": "https://osha.gov",
            "last_updated": "2026-07-08T15:00:00Z",
            "verification_status": "expert_verified",
            "applicable_state": "DE",
            "confidence": 1.0,
            "legal_act_uuid": "8e8d89e5-9c88-469b-8e1d-384a28bb0099",
            "section_reference": "OSHA-101",
            "rule_description": "Fails if employees exceed 50.",
            "condition": {
                "fact": "employees",
                "operator": "exists",
                "value": True
            },
            "exceptions": [
                {
                    "fact": "missing_attribute",
                    "operator": "equal",
                    "value": "some_value"
                }
            ],
            "action": {
                "type": "apply_penalty",
                "params": {
                    "penalty_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc"
                }
            },
            "priority": 10
        }
        with open(os.path.join(tmpdir, "rules", "blocking_rule.json"), "w", encoding="utf-8") as f:
            json.dump(blocking_rule, f)

        # Initialize engine pointing to temp dir
        engine = ComplianceEngine(knowledge_dir=tmpdir)

        # Case A: Eligible (we mock by using a profile, wait, since the exception is missing_attribute,
        # if we supply missing_attribute in additional_attributes, it evaluates cleanly without missing fields!)
        profile_eligible = BusinessProfile(
            business_type="LLC",
            state="DE",
            industry="General Business",
            employees=10,
            annual_revenue=100000.0,
            ownership_type="LLC",
            is_foreign_owner=False,
            is_home_based=False,
            additional_attributes={"missing_attribute": "other_value"}
        )
        plan_eligible = engine.generate_plan(profile_eligible)
        assert plan_eligible.eligibility_result.status == EligibilityStatus.ELIGIBLE

        # Case B: Ineligible / Pending Information (missing_attribute is not in profile)
        profile_ineligible = BusinessProfile(
            business_type="LLC",
            state="DE",
            industry="General Business",
            employees=10,
            annual_revenue=100000.0,
            ownership_type="LLC",
            is_foreign_owner=False,
            is_home_based=False,
            additional_attributes={}  # missing_attribute is missing
        )
        plan_ineligible = engine.generate_plan(profile_ineligible)
        assert plan_ineligible.eligibility_result.status == EligibilityStatus.NOT_ELIGIBLE
        assert "99999999-9999-9999-9999-999999999999" in plan_ineligible.eligibility_result.blocking_rules
        assert "missing_attribute" in plan_ineligible.eligibility_result.missing_information
