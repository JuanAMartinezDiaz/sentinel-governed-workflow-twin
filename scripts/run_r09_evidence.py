"""Reproduce bounded R09 observations; never reports deployment acceptance.

Run: python -m scripts.run_r09_evidence --output /tmp/r09-observations.json
No model calls, network calls, production resources, or real human approvals.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
from tempfile import TemporaryDirectory

from sentinel_ref.arbitration import ArbitrationEngine
from sentinel_ref.authority import AuthorityRegistry
from sentinel_ref.evidence import EvidenceLedger
from sentinel_ref.gateway import EvidencePersistenceError, ProtectedExecutor
from sentinel_ref.models import AgentAuthority, ExecutionPermit, ProposedAction, RiskTier


def fixture(**gateway_options):
    registry = AuthorityRegistry()
    authority = AgentAuthority('SYN-AGENT', frozenset({'UPDATE_SYNTHETIC_CASE'}), frozenset({'sandbox'}), RiskTier.HIGH)
    registry.register(authority)
    engine = ArbitrationEngine(registry)
    gateway = ProtectedExecutor(engine, **gateway_options)
    action = ProposedAction('SYN-WORKFLOW', 'SYN-STEP', 'SYN-AGENT', 'UPDATE_SYNTHETIC_CASE', 'sandbox', RiskTier.LOW, 0.99, payload={'case_id': 'SYN-R09'})
    return registry, authority, engine, gateway, action


def denied(call):
    try:
        call()
    except PermissionError:
        return True
    return False


def observations():
    rows = []
    def record(identifier, result_class, description, expected, actual, note=''):
        if expected != actual:
            raise AssertionError(f'{identifier}: expected {expected!r}, observed {actual!r}')
        rows.append({'id': identifier, 'result': result_class, 'description': description,
                     'expected': expected, 'observed': actual, 'note': note})
    _, _, _, gateway, action = fixture()
    state = []; ledger = EvidenceLedger()
    gateway.run_governed(action, state.append, ledger)
    record('C01', 'CONTROL_CHECK_PASSED', 'Authorized synthetic action and correlated execution evidence',
           {'effects': 1, 'execution': 'SUCCEEDED', 'correlated': True},
           {'effects': len(state), 'execution': ledger.events[-1]['execution_status'],
            'correlated': ledger.events[0]['decision_id'] == ledger.events[-1]['decision_id']})

    _, _, _, gateway, action = fixture(); state = []
    forged = ExecutionPermit(action.fingerprint(), '0' * 64)
    blocked = denied(lambda: gateway.execute(action, forged, state.append))
    record('C02', 'CONTROL_CHECK_PASSED', 'Fabricated permit cannot grant execution',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)})

    _, _, _, gateway, action = fixture(); state = []
    action = replace(action, risk_tier=RiskTier.HIGH, payload={'case_id': 'SYN-R09', 'certified': True, 'approval_receipt': 'invented'})
    result, _ = gateway.run_governed(action, state.append, EvidenceLedger())
    record('C03', 'CONTROL_CHECK_PASSED', 'Fabricated certification in payload is not approval',
           {'disposition': 'REQUIRE_APPROVAL', 'effects': 0}, {'disposition': result.disposition.value, 'effects': len(state)})

    _, _, _, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action); gateway.execute(action, permit, state.append)
    blocked = denied(lambda: gateway.execute(action, permit, state.append))
    record('C04', 'CONTROL_CHECK_PASSED', 'Consumed permit replay is blocked',
           {'replay_blocked': True, 'effects': 1}, {'replay_blocked': blocked, 'effects': len(state)})

    _, _, _, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action)
    blocked = denied(lambda: gateway.execute(replace(action, workflow_id='SYN-OTHER-RUN'), permit, state.append))
    record('C05', 'CONTROL_CHECK_PASSED', 'Cross-workflow permit transfer is blocked',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)})

    now = [0.0]
    _, _, _, gateway, action = fixture(permit_ttl_seconds=1, clock=lambda: now[0]); state = []
    _, permit = gateway.authorize(action); now[0] = 1.0
    blocked = denied(lambda: gateway.execute(action, permit, state.append))
    record('C06', 'CONTROL_CHECK_PASSED', 'Expired unused permit is blocked',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)})

    registry, authority, _, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action); registry.register(replace(authority, allowed_tools=frozenset()))
    blocked = denied(lambda: gateway.execute(action, permit, state.append))
    record('C07', 'CONTROL_CHECK_PASSED', 'Outstanding permit cannot survive authority reduction',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)})

    registry, authority, _, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action); registry.revoke(action.agent_id); registry.register(authority)
    blocked = denied(lambda: gateway.execute(action, permit, state.append))
    _, fresh = gateway.authorize(action); gateway.execute(action, fresh, state.append)
    record('C08', 'CONTROL_CHECK_PASSED', 'Regrant requires a fresh permit; old permit stays invalid',
           {'old_blocked': True, 'fresh_effects': 1}, {'old_blocked': blocked, 'fresh_effects': len(state)},
           'Administrative restoration is simulated; no real reviewer or requalification was tested.')

    _, _, engine, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action); original = engine.policy
    engine.policy = replace(original, min_confidence_low=0.7); engine.policy = original
    blocked = denied(lambda: gateway.execute(action, permit, state.append))
    record('C09', 'CONTROL_CHECK_PASSED', 'Policy change and restoration cannot resurrect old permit',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)})

    _, _, engine, gateway, action = fixture(); state = []
    _, permit = gateway.authorize(action); replacement = ProtectedExecutor(engine)
    blocked = denied(lambda: replacement.execute(action, permit, state.append))
    record('C10', 'CONTROL_CHECK_PASSED', 'A replacement executor rejects prior instance permits',
           {'blocked': True, 'effects': 0}, {'blocked': blocked, 'effects': len(state)},
           'In-memory instance test only; not production key rotation, key revocation, or historical receipt verification.')

    with TemporaryDirectory(prefix='sentinel-r09-') as folder:
        root = Path(folder)
        _, _, _, gateway, action = fixture(); state = []
        failed = False
        try:
            gateway.run_governed(action, state.append, EvidenceLedger(root))
        except OSError:
            failed = True
        record('C11', 'CONTROL_CHECK_PASSED', 'Pre-dispatch evidence-write failure prevents governed action',
               {'audit_failed': True, 'effects': 0}, {'audit_failed': failed, 'effects': len(state)})

        class SuccessEvidenceFailure(EvidenceLedger):
            def record_execution(self, action, status, decision_id, **kwargs):
                if status == 'SUCCEEDED':
                    raise OSError('synthetic audit outage')
                return super().record_execution(action, status, decision_id, **kwargs)
        _, _, _, gateway, action = fixture(); state = []; outcome = None
        try:
            gateway.run_governed(action, state.append, SuccessEvidenceFailure())
        except EvidencePersistenceError as error:
            outcome = error.execution_status
        record('C12', 'CONTROL_CHECK_PASSED', 'Post-effect audit failure is distinguished from no execution',
               {'reported_outcome': 'SUCCEEDED', 'effects': 1}, {'reported_outcome': outcome, 'effects': len(state)},
               'This is an exception contract, not durable reconciliation or automatic safe retry.')

        _, _, _, gateway, action = fixture(); state = []; ledger = EvidenceLedger()
        gateway.run_governed(replace(action, risk_tier=RiskTier.HIGH), state.append, ledger, human_approved=True)
        record('L01', 'LIMITATION_REPRODUCED', 'Unauthenticated caller approval can authorize a high-risk action',
               {'effects': 1, 'approval_type': 'caller_assertion'},
               {'effects': len(state), 'approval_type': ledger.events[0]['decision_context']['approval_evidence_type']})

        ledger = EvidenceLedger()
        ledger.events.append({'event_type': 'execution', 'decision_id': 'fabricated', 'execution_status': 'SUCCEEDED'})
        output = root / 'forged-export.json'; ledger.export_package(output)
        record('L02', 'LIMITATION_REPRODUCED', 'Writable evidence export can claim a success that never occurred',
               {'claimed_success': True, 'observed_effects': 0},
               {'claimed_success': json.loads(output.read_text())['events'][0]['execution_status'] == 'SUCCEEDED', 'observed_effects': 0})

        ledger = EvidenceLedger()
        with sqlite3.connect(root / 'synthetic.sqlite') as database:
            database.execute('CREATE TABLE certifications (agent TEXT, certified INTEGER)')
            database.execute('INSERT INTO certifications VALUES (?, ?)', ('SYN-AGENT', 1))
            count = database.execute('SELECT count(*) FROM certifications').fetchone()[0]
        record('L03', 'LIMITATION_REPRODUCED', 'Direct temporary SQLite write is not mediated by Python gateway',
               {'rows_written': 1, 'gateway_events': 0}, {'rows_written': count, 'gateway_events': len(ledger.events)},
               'Isolated local synthetic database only; no production bypass or access was attempted.')

        _, _, _, gateway, action = fixture(); state = []
        _, first = gateway.authorize(action); _, second = gateway.authorize(action)
        gateway.execute(action, first, state.append); gateway.execute(action, second, state.append)
        record('L04', 'LIMITATION_REPRODUCED', 'Fresh authorizations can repeat the same business effect',
               {'distinct_permits': True, 'effects': 2}, {'distinct_permits': first.signature != second.signature, 'effects': len(state)},
               'One-use permits do not implement durable business-level idempotency.')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = observations()
    root = Path(__file__).resolve().parents[1]
    source_paths = ['sentinel_ref/arbitration.py', 'sentinel_ref/authority.py', 'sentinel_ref/gateway.py',
                    'tests/test_r09_permits.py', 'tests/test_r09_limitations.py', 'scripts/run_r09_evidence.py']
    hashes = {name: sha256((root / name).read_bytes()).hexdigest() for name in source_paths}
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip())
    report = {'schema_version': '1.0', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'synthetic public reference only; no live model, real human approval, or production resource',
              'checkout_revision': revision, 'working_tree_dirty': dirty, 'source_sha256': hashes,
              'runtime': {'python': platform.python_version(), 'implementation': platform.python_implementation()},
              'summary': {'control_checks_passed': sum(r['result'] == 'CONTROL_CHECK_PASSED' for r in rows),
                          'limitations_reproduced': sum(r['result'] == 'LIMITATION_REPRODUCED' for r in rows),
                          'r09_acceptance': 'BLOCKED', 'proprietary_deployment': 'NOT_RUN',
                          'independent_reviewer': 'UNASSIGNED'},
              'observations': rows,
              'not_tested': ['authenticated human approval and requalification', 'OS/network/database credential isolation',
                             'production key lifecycle and signed evidence verification', 'durable evidence integrity and restart reconciliation',
                             'cross-worker business idempotency', 'live-agent behavior under pressure',
                             'atomic authorization changes across processes and in-flight cancellation']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report['summary'], indent=2))
    print(f'Evidence written: {args.output}')
    # Successful reproduction is not release acceptance; consult summary.r09_acceptance.


if __name__ == '__main__':
    main()
