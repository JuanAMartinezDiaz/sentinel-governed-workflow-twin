"""Validate Phase 1 artifacts, never claim enterprise runtime acceptance.

The acceptance scenarios are an independently specified oracle for a future
integration. These tests validate that catalog, not an implementation of it.
No test imports sentinel_ref or generates expected decisions from its engine.
"""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from openapi_spec_validator import OpenAPIV31SpecValidator


ROOT = Path(__file__).resolve().parents[1] / "contracts" / "enterprise" / "v1"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


SCHEMA = load("contract.schema.json")
EXAMPLES = load("fixtures/examples.json")["examples"]
WIRE_CASES = load("fixtures/wire-cases.json")
CATALOG = load("fixtures/acceptance-cases.json")


def validator(name):
    return Draft202012Validator(
        {"$defs": SCHEMA["$defs"], "$ref": "#/$defs/" + name},
        format_checker=FormatChecker(),
    )


def test_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(SCHEMA)


def test_openapi_is_valid_and_uses_placeholder_servers():
    api = load("openapi.json")
    OpenAPIV31SpecValidator(api).validate()
    assert api["servers"][0]["url"] == "https://sentinel.example.invalid"
    assert api["paths"]["/v1/evidence-events"]["servers"][0]["url"] == (
        "https://grc-adapter.example.invalid"
    )


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_synthetic_structural_examples(name):
    validator(name).validate(EXAMPLES[name])


@pytest.mark.parametrize("case", WIRE_CASES, ids=lambda x: x["id"])
def test_wire_contract_acceptance_and_rejection(case):
    errors = list(validator(case["schema"]).iter_errors(case["instance"]))
    assert (not errors) == case["expected_valid"], [error.message for error in errors]


def test_openapi_schema_definitions_do_not_drift():
    def rewrite(value):
        if isinstance(value, dict):
            return {
                k: v.replace("#/$defs/", "#/components/schemas/") if k == "$ref" else rewrite(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        return value

    assert load("openapi.json")["components"]["schemas"] == rewrite(SCHEMA["$defs"])


def test_every_object_contract_is_closed_and_has_defined_required_fields():
    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) <= value["properties"].keys()
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(SCHEMA)


def test_all_api_operations_require_both_workload_authentication_mechanisms():
    api = load("openapi.json")
    seen = set()
    for item in api["paths"].values():
        for method, operation in item.items():
            if method not in {"get", "post"}:
                continue
            assert operation["operationId"] not in seen
            seen.add(operation["operationId"])
            # Same object means AND. Separate objects would mean OR in OpenAPI.
            assert len(operation["security"]) == 1
            requirement = operation["security"][0]
            assert set(requirement) == {"oauth2", "mutualTLS"}
            assert len(requirement["oauth2"]) == 1
            if method == "post":
                assert any(
                    p["name"] == "Idempotency-Key" and p["required"]
                    for p in operation["parameters"]
                )


def test_acceptance_catalog_schema_and_status_are_explicit():
    schema = load("fixtures/acceptance-catalog.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(CATALOG)
    cases = CATALOG["cases"]
    assert len({case["id"] for case in cases}) == len(cases)
    assert CATALOG["runtime_execution"] == "NOT_IMPLEMENTED"
    assert {case["runtime_status"] for case in cases} == {"NOT_RUN"}
    assert {r for case in cases for r in case["requirement_ids"]} == {
        f"R{i:02d}" for i in range(1, 11)
    }


def test_acceptance_catalog_includes_control_and_failure_boundaries():
    required = {
        "identity", "approval", "threshold", "authority", "binding", "revocation",
        "replay", "duplicate-effect", "aggregate", "source", "resource", "bypass",
        "failure", "evidence", "idempotency", "input", "recovery", "key-management",
    }
    assert required <= {case["family"] for case in CATALOG["cases"]}


@pytest.mark.parametrize("case", CATALOG["cases"], ids=lambda x: x["id"])
def test_acceptance_fixture_overrides_reference_real_baseline_fields(case):
    # This is fixture validation ONLY. It does not execute sequence actions.
    state = deepcopy(load("fixtures/acceptance-baseline.json"))
    for pointer, value in case["baseline_overrides"].items():
        assert pointer.startswith("/")
        parts = pointer[1:].split("/")
        node = state
        for part in parts[:-1]:
            node = node[part]
        assert parts[-1] in node
        node[parts[-1]] = value
    for name, key in [("PolicyRecord", "policy"), ("DelegationRecord", "delegation"),
                      ("WorkloadIdentity", "identity"), ("ActionRequest", "request")]:
        validator(name).validate(state[key])
    if state["approval"] is not None:
        validator("ApprovalRecord").validate(state["approval"])


def test_unresolved_execution_cannot_be_labeled_successful():
    unknown = deepcopy(EXAMPLES["ExecutionResponse"])
    unknown.update(status="UNKNOWN", outcome="UNRESOLVED", receipt=None)
    validator("ExecutionResponse").validate(unknown)
    unknown["outcome"] = "APPLIED"
    with pytest.raises(ValidationError):
        validator("ExecutionResponse").validate(unknown)


def test_unresolved_identity_denial_need_not_disclose_policy_or_grant():
    denied = deepcopy(EXAMPLES["DecisionResponse"])
    denied.update(disposition="DENY", reason_code="UNKNOWN_WORKLOAD", action_digest=None,
                  policy=None, delegation=None, approval_id=None, permit=None)
    validator("DecisionResponse").validate(denied)
