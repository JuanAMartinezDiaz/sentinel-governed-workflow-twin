import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from conftest import make_action
from sentinel_ref.evidence import EvidenceLedger
from sentinel_ref.models import RiskTier


def test_blocked_action_never_calls_operation(gateway):
    ledger = EvidenceLedger()
    called = []
    action = make_action(risk_tier=RiskTier.HIGH)
    gateway.run_governed(action, lambda payload: called.append(payload), ledger)
    assert called == []
    assert ledger.events[-1]['execution_status'] == 'BLOCKED'
    assert ledger.events[0]['decision_id'] == ledger.events[1]['decision_id']


def test_execution_failure_is_preserved_without_sensitive_error(gateway):
    ledger = EvidenceLedger()
    def fail(payload):
        raise RuntimeError('sensitive content')
    with pytest.raises(RuntimeError):
        gateway.run_governed(make_action(), fail, ledger)
    assert ledger.events[-1]['execution_status'] == 'FAILED'
    assert 'sensitive content' not in json.dumps(ledger.events)


def test_policy_change_and_repeated_action_remain_distinguishable(gateway, tmp_path):
    ledger = EvidenceLedger()
    action = make_action()
    gateway.run_governed(action, lambda payload: 'secret output', ledger)
    gateway._engine.policy = replace(gateway._engine.policy, min_confidence_low=0.7)
    gateway.run_governed(action, lambda payload: None, ledger)
    first, second = ledger.events[0], ledger.events[2]
    assert first['decision_id'] != second['decision_id']
    assert first['decision_context']['policy_fingerprint'] != second['decision_context']['policy_fingerprint']
    assert first['decision_context']['policy_snapshot']['min_confidence_low'] == 0.6
    assert second['decision_context']['authority_snapshot']['agent_id'] == action.agent_id
    schema = json.loads((Path(__file__).parents[1] / 'schemas/evidence.schema.json').read_text())
    jsonschema.validate(first, schema)
    path = tmp_path / 'package.json'
    ledger.export_package(path)
    package = json.loads(path.read_text())
    assert package['events'] == ledger.events
    assert 'secret output' not in path.read_text()
    assert ledger.events[1]['execution_status'] == 'SUCCEEDED'


def test_evidence_write_failure_prevents_execution(gateway, tmp_path):
    ledger = EvidenceLedger(tmp_path)  # a directory cannot be opened as a JSONL file
    called = []
    with pytest.raises(OSError):
        gateway.run_governed(make_action(), lambda payload: called.append(payload), ledger)
    assert called == []
