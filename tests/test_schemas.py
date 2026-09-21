import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).parents[1]


def test_workflow_fixture_matches_schema():
    schema = json.loads((ROOT / "schemas" / "workflow.schema.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "examples" / "synthetic_bank_workflow.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=fixture, schema=schema)


def test_evidence_example_matches_schema():
    schema = json.loads((ROOT / "schemas" / "evidence.schema.json").read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / "examples" / "evidence_record.example.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=evidence, schema=schema)
