"""Passing these tests means a LIMITATION was reproduced, not a control passed.

These assertions deliberately document boundaries that still block acceptance.
Replace a limitation assertion with a protection regression when it is fixed.
"""
import json
import sqlite3

from conftest import make_action
from sentinel_ref.evidence import EvidenceLedger
from sentinel_ref.models import RiskTier


def test_reference_limitation_caller_assertion_is_not_authenticated_approval(gateway):
    effects = []
    ledger = EvidenceLedger()
    gateway.run_governed(make_action(risk_tier=RiskTier.HIGH), effects.append, ledger, human_approved=True)
    assert len(effects) == 1  # No authenticated reviewer participated.
    assert ledger.events[0]['decision_context']['approval_evidence_type'] == 'caller_assertion'


def test_reference_limitation_fabricated_export_can_claim_unobserved_success(tmp_path):
    ledger = EvidenceLedger()
    effects = []
    ledger.events.append({'event_type': 'execution', 'decision_id': 'fabricated', 'execution_status': 'SUCCEEDED'})
    destination = tmp_path / 'fabricated.json'
    ledger.export_package(destination)
    assert json.loads(destination.read_text())['events'][0]['execution_status'] == 'SUCCEEDED'
    assert effects == []  # Exported claim did not originate from observed execution.


def test_reference_limitation_direct_sandbox_sqlite_write_is_outside_gateway(tmp_path):
    # Local temporary SQLite only. No production resource, credential or network access.
    ledger = EvidenceLedger()
    with sqlite3.connect(tmp_path / 'synthetic.sqlite') as database:
        database.execute('CREATE TABLE training (agent TEXT, certified INTEGER)')
        database.execute('INSERT INTO training VALUES (?, ?)', ('SYN-AGENT', 1))
        assert database.execute('SELECT count(*) FROM training').fetchone()[0] == 1
    assert ledger.events == []  # Same-process database access has no enforced gateway.


def test_reference_limitation_fresh_permits_do_not_deduplicate_business_effect(gateway):
    effects = []
    action = make_action()
    _, first = gateway.authorize(action)
    _, second = gateway.authorize(action)
    assert first.signature != second.signature
    gateway.execute(action, first, effects.append)
    gateway.execute(action, second, effects.append)
    assert len(effects) == 2  # One-use permits are not a durable case-level idempotency key.
