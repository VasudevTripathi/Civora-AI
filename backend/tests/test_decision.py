import os
import json
import pytest
from typing import Dict, Any

from backend.app.core.exceptions import PolicyLoadError
from backend.app.services.policy_loader import PolicyLoader
from backend.app.decision.models import BusinessProfile
from backend.app.decision.engine import RuleEngine

# Sample Rule definitions for testing
RULE_SINGLE_CA = {
    "id": "11111111-1111-1111-1111-111111111111",
    "version": "1.0.0",
    "title": "California State Tax Registration",
    "description": "Requires California businesses to register for state taxes.",
    "category": "Taxation",
    "authority": "California Franchise Tax Board",
    "priority": 10,
    "condition": {
        "fact": "state",
        "operator": "equal",
        "value": "CA"
    },
    "action": {
        "type": "require_license",
        "params": {
            "license_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://ftb.ca.gov"
}

RULE_INDUSTRY_REST = {
    "id": "22222222-2222-2222-2222-222222222222",
    "version": "1.0.0",
    "title": "Food Service Permit",
    "description": "Requires restaurants to obtain a health permit.",
    "category": "Health & Safety",
    "authority": "Department of Health",
    "priority": 20,
    "condition": {
        "fact": "industry",
        "operator": "equal",
        "value": "restaurant"
    },
    "action": {
        "type": "require_license",
        "params": {
            "license_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://health.gov"
}

RULE_EMPLOYEES_50 = {
    "id": "33333333-3333-3333-3333-333333333333",
    "version": "1.0.0",
    "title": "Large Employer Disclosure",
    "description": "Applies to businesses with more than 50 employees.",
    "category": "Labor Regulation",
    "authority": "Department of Labor",
    "priority": 5,
    "condition": {
        "fact": "employees",
        "operator": "greaterThan",
        "value": 50
    },
    "action": {
        "type": "trigger_notification",
        "params": {
            "notification_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://dol.gov"
}

RULE_LOGICAL_AND = {
    "id": "44444444-4444-4444-4444-444444444444",
    "version": "1.0.0",
    "title": "New York Retail License",
    "description": "Requires retail businesses in NY to obtain a certificate.",
    "category": "Licensing",
    "authority": "NY State Division of Licensing",
    "priority": 30,
    "condition": {
        "all": [
            {"fact": "state", "operator": "equal", "value": "NY"},
            {"fact": "industry", "operator": "equal", "value": "retail"}
        ]
    },
    "action": {
        "type": "require_license",
        "params": {
            "license_uuid": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://ny.gov"
}

RULE_LOGICAL_OR = {
    "id": "55555555-5555-5555-5555-555555555555",
    "version": "1.0.0",
    "title": "Southern States Commerce Permit",
    "description": "Applies to businesses in Texas or Florida.",
    "category": "Commerce",
    "authority": "Southern States Council",
    "priority": 15,
    "condition": {
        "any": [
            {"fact": "state", "operator": "equal", "value": "TX"},
            {"fact": "state", "operator": "equal", "value": "FL"}
        ]
    },
    "action": {
        "type": "trigger_notification",
        "params": {
            "notification_uuid": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://southcommerce.gov"
}

RULE_LOGICAL_NOT = {
    "id": "66666666-6666-6666-6666-666666666666",
    "version": "1.0.0",
    "title": "Commercial Premises Safety",
    "description": "Applies to non-home-based businesses.",
    "category": "Safety",
    "authority": "OSHA",
    "priority": 8,
    "condition": {
        "not": {
            "fact": "is_home_based",
            "operator": "equal",
            "value": True
        }
    },
    "action": {
        "type": "trigger_notification",
        "params": {
            "notification_uuid": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://osha.gov"
}

RULE_DEPENDENCY_CA_REST = {
    "id": "77777777-7777-7777-7777-777777777777",
    "version": "1.0.0",
    "title": "CA Food Service Additional Permit",
    "description": "Depends on California State Tax Registration.",
    "category": "Licensing",
    "authority": "CA Health",
    "priority": 25,
    "dependencies": ["11111111-1111-1111-1111-111111111111"],
    "condition": {
        "all": [
            {"fact": "state", "operator": "equal", "value": "CA"},
            {"fact": "industry", "operator": "equal", "value": "restaurant"}
        ]
    },
    "action": {
        "type": "require_license",
        "params": {
            "license_uuid": "gggggggg-gggg-gggg-gggg-gggggggggggg",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://ca.gov"
}

RULE_EXCEPTIONS_TECH = {
    "id": "88888888-8888-8888-8888-888888888888",
    "version": "1.0.0",
    "title": "Small Tech Startup Incentive",
    "description": "Applies to tech industry except if employees > 50.",
    "category": "Incentive",
    "authority": "Startup Board",
    "priority": 40,
    "condition": {
        "fact": "industry",
        "operator": "equal",
        "value": "tech"
    },
    "exceptions": [
        {
            "fact": "employees",
            "operator": "greaterThan",
            "value": 50
        }
    ],
    "action": {
        "type": "exempt_license",
        "params": {
            "license_uuid": "hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://startup.gov"
}

RULE_COUNTY_CHECK = {
    "id": "99999999-9999-9999-9999-999999999999",
    "version": "1.0.0",
    "title": "Orange County Food Handler Permit",
    "description": "Applies to restaurants in Orange County.",
    "category": "Licensing",
    "authority": "Orange County Health",
    "priority": 30,
    "condition": {
        "all": [
            {"fact": "industry", "operator": "equal", "value": "restaurant"},
            {"fact": "county", "operator": "equal", "value": "Orange"}
        ]
    },
    "action": {
        "type": "require_license",
        "params": {
            "license_uuid": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii",
            "value": True
        }
    },
    "effective_date": "2026-01-01",
    "source": "https://oc.gov"
}


@pytest.fixture
def temp_rules_dir(temp_knowledge_dir):
    """
    Overwrites the mock schema from temp_knowledge_dir with the actual extended one
    so we can validate real-world conditions.
    """
    real_schema_path = "/media/vasu/VASUDEV/Civora AI/data/knowledge/schemas/policy_rule.schema.json"
    with open(real_schema_path, "r") as f:
        schema = json.load(f)

    # Write schema
    with open(os.path.join(temp_knowledge_dir, "schemas", "policy_rule.schema.json"), "w") as f:
        json.dump(schema, f)

    return temp_knowledge_dir


def write_rule(directory: str, filename: str, rule: Dict[str, Any]):
    with open(os.path.join(directory, "rules", filename), "w") as f:
        json.dump(rule, f)


def get_mock_profile(
    business_type="Corporation",
    state="CA",
    county=None,
    city=None,
    industry="restaurant",
    employees=15,
    annual_revenue=150000.00,
    ownership_type="private",
    is_foreign_owner=False,
    is_home_based=False,
    additional_attributes=None
) -> BusinessProfile:
    return BusinessProfile(
        business_type=business_type,
        state=state,
        county=county,
        city=city,
        industry=industry,
        employees=employees,
        annual_revenue=annual_revenue,
        ownership_type=ownership_type,
        is_foreign_owner=is_foreign_owner,
        is_home_based=is_home_based,
        additional_attributes=additional_attributes or {}
    )


# ----------------------------------------------------
# Test cases
# ----------------------------------------------------

def test_single_rule_matching(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_single.json", RULE_SINGLE_CA)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # 1. Match CA business profile
    profile_ca = get_mock_profile(state="CA")
    result_ca = engine.match(profile_ca)
    assert len(result_ca.matched_rules) == 1
    assert result_ca.matched_rules[0].rule_id == RULE_SINGLE_CA["id"]
    assert result_ca.matched_rules[0].title == RULE_SINGLE_CA["title"]

    # 2. No match NY business profile
    profile_ny = get_mock_profile(state="NY")
    result_ny = engine.match(profile_ny)
    assert len(result_ny.matched_rules) == 0


def test_multiple_rules_matching_and_priority_sorting(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_single.json", RULE_SINGLE_CA)
    write_rule(temp_rules_dir, "rule_industry.json", RULE_INDUSTRY_REST)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # Profile is CA and restaurant (should match both)
    profile = get_mock_profile(state="CA", industry="restaurant")
    result = engine.match(profile)

    assert len(result.matched_rules) == 2
    # Verify priority sorting: RULE_INDUSTRY_REST priority is 20, RULE_SINGLE_CA is 10
    # Higher priority must come first
    assert result.matched_rules[0].rule_id == RULE_INDUSTRY_REST["id"]
    assert result.matched_rules[1].rule_id == RULE_SINGLE_CA["id"]


def test_numerical_threshold_matching(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_employees.json", RULE_EMPLOYEES_50)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # Profile with 10 employees (should not match)
    profile_small = get_mock_profile(employees=10)
    result_small = engine.match(profile_small)
    assert len(result_small.matched_rules) == 0

    # Profile with 60 employees (should match)
    profile_large = get_mock_profile(employees=60)
    result_large = engine.match(profile_large)
    assert len(result_large.matched_rules) == 1
    assert result_large.matched_rules[0].rule_id == RULE_EMPLOYEES_50["id"]


def test_logical_operators_and_or_not(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_and.json", RULE_LOGICAL_AND)
    write_rule(temp_rules_dir, "rule_or.json", RULE_LOGICAL_OR)
    write_rule(temp_rules_dir, "rule_not.json", RULE_LOGICAL_NOT)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # 1. Test AND logic
    # Matches NY + retail
    p_ny_retail = get_mock_profile(state="NY", industry="retail")
    res1 = engine.match(p_ny_retail)
    assert any(r.rule_id == RULE_LOGICAL_AND["id"] for r in res1.matched_rules)

    # Doesn't match NY + restaurant
    p_ny_rest = get_mock_profile(state="NY", industry="restaurant")
    res2 = engine.match(p_ny_rest)
    assert not any(r.rule_id == RULE_LOGICAL_AND["id"] for r in res2.matched_rules)

    # 2. Test OR logic
    # Matches TX
    p_tx = get_mock_profile(state="TX")
    res_tx = engine.match(p_tx)
    assert any(r.rule_id == RULE_LOGICAL_OR["id"] for r in res_tx.matched_rules)

    # Matches FL
    p_fl = get_mock_profile(state="FL")
    res_fl = engine.match(p_fl)
    assert any(r.rule_id == RULE_LOGICAL_OR["id"] for r in res_fl.matched_rules)

    # Doesn't match GA
    p_ga = get_mock_profile(state="GA")
    res_ga = engine.match(p_ga)
    assert not any(r.rule_id == RULE_LOGICAL_OR["id"] for r in res_ga.matched_rules)

    # 3. Test NOT logic
    # Matches if is_home_based is False
    p_commercial = get_mock_profile(is_home_based=False)
    res_comm = engine.match(p_commercial)
    assert any(r.rule_id == RULE_LOGICAL_NOT["id"] for r in res_comm.matched_rules)

    # Doesn't match if is_home_based is True
    p_home = get_mock_profile(is_home_based=True)
    res_home = engine.match(p_home)
    assert not any(r.rule_id == RULE_LOGICAL_NOT["id"] for r in res_home.matched_rules)


def test_rule_exceptions(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_exceptions.json", RULE_EXCEPTIONS_TECH)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # 1. Tech startup with 10 employees (should match)
    p_startup = get_mock_profile(industry="tech", employees=10)
    res_startup = engine.match(p_startup)
    assert len(res_startup.matched_rules) == 1
    assert res_startup.matched_rules[0].rule_id == RULE_EXCEPTIONS_TECH["id"]

    # 2. Tech startup with 60 employees (should be exempt via exception check)
    p_big_tech = get_mock_profile(industry="tech", employees=60)
    res_big = engine.match(p_big_tech)
    assert len(res_big.matched_rules) == 0


def test_missing_profile_data_tracking(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_county.json", RULE_COUNTY_CHECK)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # Profile lacks county (county is None)
    profile_missing_county = get_mock_profile(industry="restaurant", county=None)
    result = engine.match(profile_missing_county)

    assert len(result.matched_rules) == 0
    # The missing field should be captured under missing_information
    assert "county" in result.missing_information


def test_dependency_resolution_and_warnings(temp_rules_dir):
    write_rule(temp_rules_dir, "rule_single.json", RULE_SINGLE_CA)
    write_rule(temp_rules_dir, "rule_dependency.json", RULE_DEPENDENCY_CA_REST)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    engine = RuleEngine(policy_loader=loader)
    engine.load_rules()

    # Case A: Profile satisfies both RULE_SINGLE_CA and RULE_DEPENDENCY_CA_REST conditions.
    # Since both match, dependencies are fully satisfied.
    profile_ok = get_mock_profile(state="CA", industry="restaurant")
    result_ok = engine.match(profile_ok)
    assert len(result_ok.matched_rules) == 2
    assert len(result_ok.warnings) == 0

    # Case B: Rule dependency is missing.
    # Suppose we load ONLY RULE_DEPENDENCY_CA_REST without RULE_SINGLE_CA.
    loader_missing_dep = PolicyLoader(knowledge_dir=temp_rules_dir)
    # We clear and rewrite rules directory to contain ONLY the dependent rule
    os.remove(os.path.join(temp_rules_dir, "rules", "rule_single.json"))
    
    engine_missing_dep = RuleEngine(policy_loader=loader_missing_dep)
    engine_missing_dep.load_rules()

    result_missing = engine_missing_dep.match(profile_ok)
    # The dependent rule must be filtered out, and a warning should be added
    assert len(result_missing.matched_rules) == 0
    assert len(result_missing.warnings) == 1
    assert "dependency" in result_missing.warnings[0].lower()


def test_invalid_rules_handling(temp_rules_dir):
    # Rule with unsupported operator "is_greater_than"
    rule_invalid_operator = {
        "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
        "version": "1.0.0",
        "description": "Invalid rule",
        "condition": {
            "fact": "employees",
            "operator": "is_greater_than",
            "value": 10
        },
        "action": {
            "type": "trigger_notification",
            "params": {"notification_uuid": "cccccccc-cccc-cccc-cccc-cccccccccccc", "value": True}
        },
        "priority": 5,
        "effective_date": "2026-01-01",
        "source": "https://dol.gov"
    }
    write_rule(temp_rules_dir, "invalid_rule.json", rule_invalid_operator)

    loader = PolicyLoader(knowledge_dir=temp_rules_dir)
    
    # 1. PolicyLoader.load_rule raises PolicyLoadError on schema validation failure
    with pytest.raises(PolicyLoadError):
        loader.load_rule("invalid_rule.json")

    # 2. Direct semantic validation of the invalid rule dictionary should raise PolicyLoadError
    from backend.app.decision.engine import validate_rule_semantics
    with pytest.raises(PolicyLoadError) as exc_info:
        validate_rule_semantics(rule_invalid_operator)
    assert "unsupported condition operator" in str(exc_info.value).lower()

