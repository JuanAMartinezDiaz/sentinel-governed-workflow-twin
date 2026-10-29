"""Synthetic reference regressions; not deployment acceptance evidence."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest

from conftest import make_action
from sentinel_ref.evidence import EvidenceLedger
from sentinel_ref.gateway import ProtectedExecutor
from sentinel_ref.models import ExecutionPermit, RiskTier


def test_r09_valid_permit_has_one_effect_and_replay_is_blocked(gateway):
    action = make_action()
    _, permit = gateway.authorize(action)
    effects = []
    gateway.execute(action, permit, lambda payload: effects.append(dict(payload)))
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, lambda payload: effects.append(dict(payload)))
    assert effects == [{'case_id': 'SYN-1'}]


@pytest.mark.parametrize('change', [
    {'workflow_id': 'other-run'}, {'step_id': 'other-step'},
    {'agent_id': 'other-agent'}, {'action_class': 'DRAFT_RECOMMENDATION'},
    {'tool_name': 'recommendation_service'}, {'payload': {'case_id': 'SYN-OTHER'}},
    {'risk_tier': RiskTier.MODERATE}, {'confidence': 0.96}, {'reversible': False},
])
def test_r09_permit_cannot_be_transferred_to_changed_action(gateway, change):
    action = make_action()
    _, permit = gateway.authorize(action)
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(replace(action, **change), permit, effects.append)
    assert effects == []


@pytest.mark.parametrize('bad', [None, 'approved', {}, ExecutionPermit('x', '0'*64), ExecutionPermit('x', None)])
def test_r09_fabricated_or_malformed_permits_do_not_dispatch(gateway, bad):
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(make_action(), bad, effects.append)
    assert effects == []


def test_r09_payload_claim_of_certification_is_not_approval(gateway):
    action = make_action(risk_tier=RiskTier.HIGH, payload={
        'case_id': 'SYN-1', 'training_complete': True, 'certified': True,
        'reviewer': 'invented-reviewer', 'approval_receipt': 'invented-receipt',
    })
    effects = []
    _, outcome = gateway.run_governed(action, effects.append, EvidenceLedger())
    assert outcome is None and effects == []


def test_r09_concurrent_replay_dispatches_once(gateway):
    action = make_action()
    _, permit = gateway.authorize(action)
    effects = []
    barrier = Barrier(8)
    def attempt(_):
        barrier.wait(timeout=5)
        try:
            gateway.execute(action, permit, effects.append)
            return 'executed'
        except PermissionError:
            return 'blocked'
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(attempt, range(8)))
    assert outcomes.count('executed') == 1
    assert outcomes.count('blocked') == 7
    assert len(effects) == 1


def test_r09_permit_expires_at_deadline(engine):
    now = [10.0]
    gateway = ProtectedExecutor(engine, permit_ttl_seconds=5, clock=lambda: now[0])
    action = make_action()
    _, permit = gateway.authorize(action)
    now[0] = 15.0
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, effects.append)
    assert effects == []


def test_r09_authority_reduction_blocks_outstanding_permit(gateway, registry):
    action = make_action()
    _, permit = gateway.authorize(action)
    registry.register(replace(registry.get(action.agent_id), allowed_tools=frozenset()))
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, effects.append)
    assert effects == []


def test_r09_revoke_restore_does_not_resurrect_old_permit(gateway, registry):
    action = make_action()
    authority = registry.get(action.agent_id)
    _, old = gateway.authorize(action)
    registry.revoke(action.agent_id)
    registry.register(authority)  # simulated administrative restoration, not human approval
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(action, old, effects.append)
    _, fresh = gateway.authorize(action)
    gateway.execute(action, fresh, effects.append)
    assert len(effects) == 1


def test_r09_policy_change_restore_invalidates_old_permit(gateway, engine):
    action = make_action()
    original = engine.policy
    _, permit = gateway.authorize(action)
    engine.policy = replace(original, min_confidence_low=0.7)
    engine.policy = original
    effects = []
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, effects.append)
    assert effects == []


def test_r09_other_agent_change_preserves_unchanged_agent_permit(gateway, registry):
    action = make_action()
    _, permit = gateway.authorize(action)
    registry.register(replace(registry.get(action.agent_id), agent_id='agent-2'))
    effects = []
    gateway.execute(action, permit, effects.append)
    assert len(effects) == 1


def test_r09_new_executor_rejects_prior_executor_permit(gateway, engine):
    action = make_action()
    _, permit = gateway.authorize(action)
    replacement = ProtectedExecutor(engine)
    effects = []
    with pytest.raises(PermissionError):
        replacement.execute(action, permit, effects.append)
    assert effects == []


def test_r09_explicit_invalidation_blocks_pending_permit(gateway):
    action = make_action()
    _, permit = gateway.authorize(action)
    assert gateway.invalidate_all_permits() == 1
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, lambda _: pytest.fail('unexpected dispatch'))


def test_r09_failed_operation_cannot_reuse_permit(gateway):
    action = make_action()
    _, permit = gateway.authorize(action)
    effects = []
    def uncertain(payload):
        effects.append(dict(payload))
        raise TimeoutError('synthetic unknown outcome')
    with pytest.raises(TimeoutError):
        gateway.execute(action, permit, uncertain)
    with pytest.raises(PermissionError):
        gateway.execute(action, permit, uncertain)
    assert len(effects) == 1


def test_r09_pre_dispatch_audit_failure_discards_issued_permit(gateway, tmp_path, monkeypatch):
    captured = []
    original = gateway.authorize
    def capture(*args, **kwargs):
        result, permit = original(*args, **kwargs)
        captured.append(permit)
        return result, permit
    monkeypatch.setattr(gateway, 'authorize', capture)
    action = make_action()
    effects = []
    with pytest.raises(OSError):
        gateway.run_governed(action, effects.append, EvidenceLedger(tmp_path))
    assert effects == []
    with pytest.raises(PermissionError):
        gateway.execute(action, captured[0], effects.append)
    assert effects == []


def test_r09_authority_removed_during_evidence_record_blocks_dispatch(gateway, registry):
    class RevokingLedger(EvidenceLedger):
        def record(self, action, *args, **kwargs):
            event = super().record(action, *args, **kwargs)
            registry.revoke(action.agent_id)
            return event
    effects = []
    ledger = RevokingLedger()
    with pytest.raises(PermissionError):
        gateway.run_governed(make_action(), effects.append, ledger)
    assert effects == []
    assert ledger.events[-1]['execution_status'] == 'FAILED'


def test_r09_capacity_is_bounded_and_freed_after_consumption(engine):
    gateway = ProtectedExecutor(engine, max_pending_permits=1)
    action = make_action()
    _, first = gateway.authorize(action)
    with pytest.raises(RuntimeError, match='capacity'):
        gateway.authorize(action)
    gateway.execute(action, first, lambda _: None)
    _, second = gateway.authorize(action)
    assert first.signature != second.signature


def test_r09_expiry_frees_pending_capacity(engine):
    now = [0.0]
    gateway = ProtectedExecutor(engine, max_pending_permits=1, permit_ttl_seconds=1, clock=lambda: now[0])
    _, first = gateway.authorize(make_action())
    now[0] = 1.0
    _, second = gateway.authorize(make_action())
    assert first.signature != second.signature


@pytest.mark.parametrize('ttl', [0, -1, float('nan'), float('inf'), True, '60'])
def test_r09_invalid_lifetime_rejected(engine, ttl):
    with pytest.raises(ValueError):
        ProtectedExecutor(engine, permit_ttl_seconds=ttl)


@pytest.mark.parametrize('capacity', [0, -1, True, 1.5, '2'])
def test_r09_invalid_capacity_rejected(engine, capacity):
    with pytest.raises(ValueError):
        ProtectedExecutor(engine, max_pending_permits=capacity)
