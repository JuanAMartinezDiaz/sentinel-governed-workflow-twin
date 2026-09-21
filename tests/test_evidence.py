from sentinel_ref.evidence import EvidenceLedger
from conftest import make_action


def test_evidence_record_contains_fingerprint_trace_and_permit(gateway, tmp_path):
    action = make_action()
    result, permit = gateway.authorize(action)
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    event = ledger.record(action, result, permit)

    assert len(event["action_fingerprint"]) == 64
    assert event["trace"]
    assert event["permit_issued"] is True
    assert (tmp_path / "evidence.jsonl").exists()
