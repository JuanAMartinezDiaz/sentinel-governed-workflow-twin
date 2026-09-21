import json
from pathlib import Path


def test_synthetic_workflow_has_exactly_17_steps():
    path = Path(__file__).parents[1] / "examples" / "synthetic_bank_workflow.json"
    workflow = json.loads(path.read_text(encoding="utf-8"))
    assert len(workflow["steps"]) == 17
    assert "Fictional" in workflow["disclaimer"]
