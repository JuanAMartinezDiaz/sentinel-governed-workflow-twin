"""Design-boundary regression tests; these are not SM-01..SM-08 runtime trials."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.safety_monitoring import (
    GOALS, assess_specification, draft_specification, fingerprint, main, read_json,
)

ROOT = Path(__file__).resolve().parents[1]
VERSION = "synthetic-dispute-v1"


@pytest.fixture
def workflow():
    return read_json(ROOT / "examples/synthetic_dispute_monitoring_workflow.json")


@pytest.fixture
def specification(workflow):
    return draft_specification(workflow, VERSION)


@pytest.fixture
def populated(specification):
    """Populate synthetic declarations only, never real identity/approval evidence."""
    for step in specification["steps"]:
        for field, value in step.items():
            if value is None:
                step[field] = 300 if field == "response_deadline_seconds" else f"synthetic:{field}"
        step["allowed_tools"] = ["synthetic:case-tool"]
        for control in step["controls"]:
            control["event_producer_ref"] = "synthetic:producer"
            control["detection_rule_ref"] = "synthetic:rule"
    return specification


def check(workflow, specification):
    return assess_specification(workflow, specification, VERSION)


def codes(report):
    return {issue["code"] for issue in report["issues"]}


def test_companion_is_reproducible_and_does_not_mutate_workflow(workflow, specification):
    before = deepcopy(workflow)
    saved = read_json(ROOT / "examples/synthetic_dispute_monitoring_specification.json")
    assert specification == saved == draft_specification(workflow, VERSION)
    assert workflow == before
    assert specification["workflow_sha256"] == fingerprint(workflow)
    assert len(specification["steps"]) == 5
    assert all({c["goal_id"] for c in s["controls"]} == set(GOALS) for s in specification["steps"])
    assert all(s["owner_ref"] is None for s in specification["steps"])


def test_schema_is_valid_and_both_fixtures_conform(workflow, specification):
    for filename, fixture in (("workflow.schema.json", workflow),
                              ("safety-monitoring.schema.json", specification)):
        schema = read_json(ROOT / "schemas" / filename)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(fixture)


def test_existing_seventeen_step_twin_is_supported():
    workflow = read_json(ROOT / "examples/synthetic_bank_workflow.json")
    before = deepcopy(workflow)
    specification = draft_specification(workflow, "existing-v1")
    report = assess_specification(workflow, specification, "existing-v1")
    assert workflow == before
    assert len(specification["steps"]) == 17
    assert sum(sum(g["declared_status_counts"].values()) for g in report["coverage"].values()) == 102
    assert report["release_decision"] == "BLOCKED"


def test_new_draft_has_explicit_gaps_and_no_claimed_runtime_results(workflow, specification):
    report = check(workflow, specification)
    assert report["specification_status"] == "INCOMPLETE"
    assert "UNRESOLVED_DESIGN_FIELD" in codes(report)
    assert "UNRESOLVED_TOOL_BOUNDARY" in codes(report)
    assert "UNRESOLVED_MONITOR" in codes(report)
    assert {t["id"] for t in report["runtime_tests"]} == {f"SM-{i:02}" for i in range(1, 9)}
    assert all(t["status"] == "NOT_RUN" for t in report["runtime_tests"])


def test_complete_design_cannot_grant_operational_authority(workflow, populated):
    report = check(workflow, populated)
    assert report["specification_status"] == "COMPLETE"
    assert not report["issues"]
    assert report["operational_acceptance"] == "UNVERIFIED"
    assert report["release_decision"] == "BLOCKED"
    assert report["release_blockers"] == ["TRUSTED_RUNTIME_VERIFICATION_NOT_CONNECTED"]


def test_fabricated_verification_and_approval_do_not_unlock_release(workflow, populated):
    for step in populated["steps"]:
        step["requirements_confirmation_ref"] = "fabricated:approval"
        for control in step["controls"]:
            control["status"] = "verified"
            control["evidence_refs"] = ["fabricated:all-tests-passed"]
            control["verification"] = {
                "artifact_ref": "fabricated:report", "candidate_revision": "made-up",
                "configuration_sha256": "a" * 64, "checked_at": "2026-11-02T23:00:00Z",
                "reviewer_ref": "fabricated:reviewer",
            }
    report = check(workflow, populated)
    assert report["specification_status"] == "COMPLETE"
    assert report["release_decision"] == "BLOCKED"
    assert all(t["status"] == "NOT_RUN" for t in report["runtime_tests"])


@pytest.mark.parametrize("field,value", [
    ("workflow_id", "another-workflow"), ("workflow_version", "older-version"),
    ("workflow_sha256", "0" * 64),
])
def test_companion_cannot_be_reused_with_another_candidate(workflow, populated, field, value):
    populated[field] = value
    assert "WORKFLOW_BINDING_MISMATCH" in codes(check(workflow, populated))


@pytest.mark.parametrize("field,value", [
    ("human_approval", False), ("risk_tier", "LOW"), ("action_class", "READ_CASE"),
    ("proposed_mode", "ASSIST"),
])
def test_workflow_change_invalidates_prior_design_binding(workflow, populated, field, value):
    workflow["steps"][-1][field] = value
    report = check(workflow, populated)
    assert report["specification_status"] == "INCOMPLETE"
    assert "WORKFLOW_BINDING_MISMATCH" in codes(report)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown"])
def test_step_coverage_cannot_be_reduced(workflow, populated, mutation):
    if mutation == "missing":
        populated["steps"].pop()
    elif mutation == "duplicate":
        populated["steps"][-1] = deepcopy(populated["steps"][0])
    else:
        populated["steps"][-1]["step_id"] = "invented-step"
    assert "STEP_COVERAGE_MISMATCH" in codes(check(workflow, populated))


def test_duplicate_goal_cannot_replace_a_missing_goal(workflow, populated):
    populated["steps"][0]["controls"][-1] = deepcopy(populated["steps"][0]["controls"][0])
    assert "GOAL_COVERAGE_MISMATCH" in codes(check(workflow, populated))


@pytest.mark.parametrize("mutation", ["drop_goal", "optional", "unknown_goal", "allow_on_failure", "extra_release_flag", "unknown_version"])
def test_unsafe_contract_changes_are_invalid(workflow, populated, mutation):
    control = populated["steps"][0]["controls"][0]
    if mutation == "drop_goal":
        populated["steps"][0]["controls"].pop()
    elif mutation == "optional":
        control["mandatory"] = False
    elif mutation == "unknown_goal":
        control["goal_id"] = "OTHER"
    elif mutation == "allow_on_failure":
        control["response"] = "ALLOW"
    elif mutation == "extra_release_flag":
        populated["release_approved"] = True
    else:
        populated["schema_version"] = "2.0"
    report = check(workflow, populated)
    assert report["specification_status"] == "INVALID"
    assert report["release_decision"] == "BLOCKED"


@pytest.mark.parametrize("field,code", [
    ("required_events", "REQUIRED_EVENTS_MISSING"), ("test_ids", "REQUIRED_TESTS_MISSING"),
])
def test_required_events_and_tests_cannot_be_omitted(workflow, populated, field, code):
    populated["steps"][0]["controls"][0][field] = []
    assert code in codes(check(workflow, populated))


@pytest.mark.parametrize("status", ["missing", "failed"])
def test_one_failed_mandatory_control_cannot_be_averaged_away(workflow, populated, status):
    populated["steps"][-1]["controls"][-1]["status"] = status
    report = check(workflow, populated)
    assert "CONTROL_UNRESOLVED" in codes(report)
    assert report["specification_status"] == "INCOMPLETE"


def test_claimed_exemption_requires_independent_verification(workflow, populated):
    control = populated["steps"][0]["controls"][4]
    control.update(status="not_applicable", not_applicable_justification="No child agents intended",
                   disabled_capability_evidence_ref="synthetic:disabled-config")
    report = check(workflow, populated)
    assert "EXEMPTION_UNVERIFIED" in codes(report)
    assert report["release_decision"] == "BLOCKED"


@pytest.mark.parametrize("status", ["verified", "not_applicable"])
def test_status_labels_require_supporting_fields(workflow, populated, status):
    populated["steps"][0]["controls"][0]["status"] = status
    assert check(workflow, populated)["specification_status"] == "INVALID"


@pytest.mark.parametrize("value", ["", "   ", 7, False])
def test_owners_must_be_nonblank_references(workflow, populated, value):
    populated["steps"][0]["owner_ref"] = value
    assert check(workflow, populated)["specification_status"] == "INVALID"


@pytest.mark.parametrize("mutation", ["duplicate", "blank", "too_many"])
def test_ambiguous_or_oversized_workflows_are_rejected(workflow, mutation):
    if mutation == "duplicate":
        workflow["steps"].append(deepcopy(workflow["steps"][0]))
    elif mutation == "blank":
        workflow["steps"][0]["id"] = " "
    else:
        workflow["steps"] = [{**workflow["steps"][0], "id": str(i)} for i in range(101)]
    with pytest.raises(ValueError):
        draft_specification(workflow, VERSION)


@pytest.mark.parametrize("contents", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":-Infinity}'])
def test_ambiguous_json_is_rejected(tmp_path, contents):
    path = tmp_path / "input.json"
    path.write_text(contents)
    with pytest.raises(ValueError):
        read_json(path)


def test_json_size_limit(tmp_path):
    path = tmp_path / "input.json"
    path.write_text('"' + 'x' * (5 * 1024 * 1024) + '"')
    with pytest.raises(ValueError, match="5 MiB"):
        read_json(path)


def test_invalid_documents_produce_blocked_report():
    report = assess_specification([], {}, VERSION)
    assert report["specification_status"] == "INVALID"
    assert report["release_decision"] == "BLOCKED"


def test_cli_preserves_existing_output_and_reports_incomplete_design(tmp_path, capsys):
    source = str(ROOT / "examples/synthetic_dispute_monitoring_workflow.json")
    output = tmp_path / "specification.json"
    arguments = ["--workflow", source, "--workflow-version", VERSION]
    assert main(["draft", *arguments, "--output", str(output)]) == 0
    original = output.read_bytes()
    assert main(["draft", *arguments, "--output", str(output)]) == 2
    assert output.read_bytes() == original
    assert main(["check", *arguments, "--specification", str(output)]) == 2
    assert json.loads(capsys.readouterr().out)["release_decision"] == "BLOCKED"


def test_complete_design_cli_cannot_pass_operational_gate(tmp_path, populated, capsys):
    path = tmp_path / "populated.json"
    path.write_text(json.dumps(populated))
    arguments = ["check", "--workflow", str(ROOT / "examples/synthetic_dispute_monitoring_workflow.json"),
                 "--workflow-version", VERSION, "--specification", str(path)]
    assert main(arguments) == 0
    assert main([*arguments, "--require-operational-acceptance"]) == 2
    assert '"release_decision": "BLOCKED"' in capsys.readouterr().out
