"""Create and inspect a safety-monitoring companion to a synthetic workflow twin.

This is a design tool. It never authenticates reviewers, verifies operating
controls, issues execution permits, or approves deployment. Install .[dev].
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MAX_INPUT_BYTES = 5 * 1024 * 1024
GOALS = {
    "SMG-01": {
        "name": "Policy violations", "test_id": "SM-01",
        "events": ["source.fact_extracted", "source.contradiction", "policy.evaluated"],
        "requirement": "Validate material facts against versioned sources and business rules before releasing a consequential action.",
    },
    "SMG-02": {
        "name": "Unauthorized actions", "test_id": "SM-02",
        "events": ["identity.validated", "authority.changed", "tool.dispatch_requested", "authority.revoked"],
        "requirement": "Recheck authenticated identity, case scope, action, data and tool authority immediately before dispatch.",
    },
    "SMG-03": {
        "name": "Human oversight failures", "test_id": "SM-03",
        "events": ["review.requested", "review.acknowledged", "review.decided", "review.expired"],
        "requirement": "Bind review to the action and evidence; authenticate reviewer role, enforce expiry and route nonresponse to a backup owner.",
    },
    "SMG-04": {
        "name": "Behavioral drift", "test_id": "SM-04",
        "events": ["configuration.changed", "memory.changed", "baseline.compared"],
        "requirement": "Compare matched cases with a versioned baseline and keep case-specific exceptions separate from policy.",
    },
    "SMG-05": {
        "name": "Multi-agent system risks", "test_id": "SM-05",
        "events": ["delegation.created", "delegation.scope_checked", "delegation.cancelled"],
        "requirement": "Preserve case scope, narrower child authority, shared budgets and cancellation across the delegation chain.",
    },
    "SMG-06": {
        "name": "Auditability", "test_id": "SM-06",
        "events": ["audit.persisted", "tool.receipt", "business_state.reconciled", "audit.integrity_checked"],
        "requirement": "Persist pre-dispatch evidence outside agent control; reconcile observed outcomes and prevent duplicate effects after uncertain results.",
    },
}
RUNTIME_TESTS = {
    **{goal["test_id"]: goal["name"] for goal in GOALS.values()},
    "SM-07": "Monitoring outage or unavailable evaluator",
    "SM-08": "Authorized action completes once and is reconstructable",
}


def fingerprint(value: object) -> str:
    """Content binding only; a digest does not establish provenance or trust."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def read_json(path: Path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("JSON input exceeds the 5 MiB authoring limit")
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _schema_errors(instance, filename: str) -> list[str]:
    schema = read_json(ROOT / "schemas" / filename)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(f"{'/'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                  for error in validator.iter_errors(instance))


def _workflow_errors(workflow) -> list[str]:
    errors = _schema_errors(workflow, "workflow.schema.json")
    if errors:
        return errors
    ids = [step["id"] for step in workflow["steps"]]
    if len(ids) > 100:
        errors.append("workflow exceeds the 100-step authoring limit")
    if any(not step_id.strip() for step_id in ids):
        errors.append("workflow step IDs must be nonblank")
    if len(set(ids)) != len(ids):
        errors.append("workflow step IDs must be unique")
    return errors


def draft_specification(workflow: dict, workflow_version: str) -> dict:
    errors = _workflow_errors(workflow)
    if errors:
        raise ValueError("; ".join(errors))
    if not isinstance(workflow_version, str) or not workflow_version.strip():
        raise ValueError("workflow_version must be nonblank")
    steps = []
    for step in workflow["steps"]:
        controls = []
        for goal_id, goal in GOALS.items():
            controls.append({
                "goal_id": goal_id, "mandatory": True, "status": "specified",
                "required_events": list(goal["events"]), "event_producer_ref": None,
                "detection_rule_ref": None, "response": "BLOCK_OR_PAUSE",
                "test_ids": [goal["test_id"], "SM-07", "SM-08"],
                "evidence_refs": [], "verification": None,
                "not_applicable_justification": None, "disabled_capability_evidence_ref": None,
            })
        steps.append({
            "step_id": step["id"], "owner_ref": None, "agent_identity_ref": None,
            "policy_version_ref": None, "source_requirements_ref": None,
            "allowed_tools": [], "data_scope_ref": None, "reviewer_role_ref": None,
            "requirements_confirmation_ref": None, "response_owner_ref": None,
            "backup_owner_ref": None, "response_deadline_seconds": None,
            "recovery_ref": None, "retention_access_ref": None, "controls": controls,
        })
    return {
        "schema_version": "1.0", "specification_version": "draft-1",
        "workflow_id": workflow["workflow_id"], "workflow_version": workflow_version,
        "workflow_sha256": fingerprint(workflow), "scope": "synthetic_design_review",
        "steps": steps,
    }


def assess_specification(workflow: dict, specification: dict, workflow_version: str) -> dict:
    """Fail closed on structural/binding gaps; never infer operational acceptance.

    A complete result means required design fields are populated. Their truth,
    approval and referenced evidence must be verified by a separate trusted service.
    """
    issues = []

    def issue(code, path, detail):
        issues.append({"code": code, "path": path, "detail": detail})

    workflow_errors = _workflow_errors(workflow)
    spec_errors = _schema_errors(specification, "safety-monitoring.schema.json")
    for error in workflow_errors:
        issue("INVALID_WORKFLOW", "workflow", error)
    for error in spec_errors:
        issue("INVALID_SPECIFICATION", "specification", error)
    if not isinstance(workflow_version, str) or not workflow_version.strip():
        issue("INVALID_VERSION", "workflow_version", "Expected workflow version must be nonblank")
    invalid = bool(issues)
    coverage = {goal_id: {"name": goal["name"], "declared_status_counts": {}}
                for goal_id, goal in GOALS.items()}
    if not invalid:
        for key, expected in (("workflow_id", workflow["workflow_id"]),
                              ("workflow_version", workflow_version),
                              ("workflow_sha256", fingerprint(workflow))):
            if specification[key] != expected:
                issue("WORKFLOW_BINDING_MISMATCH", key, "Regenerate and reconfirm against the candidate workflow")
        expected_ids = {step["id"] for step in workflow["steps"]}
        actual_ids = [step["step_id"] for step in specification["steps"]]
        if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != expected_ids:
            issue("STEP_COVERAGE_MISMATCH", "steps", "Every workflow step must occur exactly once")
        for step in specification["steps"]:
            path = step["step_id"]
            for field in ("owner_ref", "agent_identity_ref", "policy_version_ref",
                          "source_requirements_ref", "data_scope_ref", "reviewer_role_ref",
                          "requirements_confirmation_ref", "response_owner_ref", "backup_owner_ref",
                          "response_deadline_seconds", "recovery_ref", "retention_access_ref"):
                if step[field] is None:
                    issue("UNRESOLVED_DESIGN_FIELD", f"{path}/{field}", "Owner confirmation is required")
            if not step["allowed_tools"]:
                issue("UNRESOLVED_TOOL_BOUNDARY", path, "Specify permitted tools, including an explicit manual/no-tool marker if applicable")
            goal_ids = [control["goal_id"] for control in step["controls"]]
            if len(set(goal_ids)) != len(goal_ids) or set(goal_ids) != set(GOALS):
                issue("GOAL_COVERAGE_MISMATCH", path, "Every step must address all six goals exactly once")
            for control in step["controls"]:
                goal_id = control["goal_id"]
                control_path = f"{path}/{goal_id}"
                status = control["status"]
                statuses = coverage[goal_id]["declared_status_counts"]
                statuses[status] = statuses.get(status, 0) + 1
                if status in ("missing", "failed"):
                    issue("CONTROL_UNRESOLVED", control_path, f"Control is {status}")
                if status == "not_applicable":
                    issue("EXEMPTION_UNVERIFIED", control_path, "A trusted verifier must establish that the excluded capability is disabled")
                for field in ("event_producer_ref", "detection_rule_ref"):
                    if control[field] is None:
                        issue("UNRESOLVED_MONITOR", f"{control_path}/{field}", "Specify the producer and detection rule")
                if not set(GOALS[goal_id]["events"]).issubset(control["required_events"]):
                    issue("REQUIRED_EVENTS_MISSING", control_path, "Baseline events cannot be silently removed")
                required_tests = {GOALS[goal_id]["test_id"], "SM-07", "SM-08"}
                if not required_tests.issubset(control["test_ids"]):
                    issue("REQUIRED_TESTS_MISSING", control_path, "Goal, monitoring-outage and positive-control tests are required")
    return {
        "report_version": "1.0", "scope": "synthetic_design_review",
        "workflow_sha256": fingerprint(workflow), "specification_sha256": fingerprint(specification),
        "specification_status": "INVALID" if invalid else ("INCOMPLETE" if issues else "COMPLETE"),
        "operational_acceptance": "UNVERIFIED", "release_decision": "BLOCKED",
        "release_blockers": ["TRUSTED_RUNTIME_VERIFICATION_NOT_CONNECTED"],
        "coverage": coverage, "issues": issues,
        "runtime_tests": [{"id": test_id, "name": name, "status": "NOT_RUN"}
                          for test_id, name in RUNTIME_TESTS.items()],
        "limitations": [
            "All input statuses, identities, approvals and evidence references are untrusted declarations.",
            "COMPLETE means design fields are populated; it is not approval, tested effectiveness or release authority.",
            "No runtime monitor, authenticated approval, protected evidence store or execution gate is connected by this command.",
            "A content digest detects a mismatch against the supplied workflow; it does not authenticate that workflow or evidence.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("draft", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--workflow", required=True, type=Path)
        sub.add_argument("--workflow-version", required=True)
        sub.add_argument("--output", type=Path, help="Create a new JSON file; existing files are never overwritten")
        if command == "check":
            sub.add_argument("--specification", required=True, type=Path)
            sub.add_argument("--require-operational-acceptance", action="store_true")
    args = parser.parse_args(argv)
    try:
        workflow = read_json(args.workflow)
        if args.command == "draft":
            result = draft_specification(workflow, args.workflow_version)
            code = 0
        else:
            result = assess_specification(workflow, read_json(args.specification), args.workflow_version)
            code = 0 if result["specification_status"] == "COMPLETE" else 2
            if args.require_operational_acceptance:
                code = 2  # No trusted runtime acceptance path in this version.
        serialized = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        else:
            print(serialized, end="")
        return code
    except (OSError, ValueError, RecursionError) as error:
        print(f"Safety monitoring input/output error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
