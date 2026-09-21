import pytest

from conftest import make_action


def test_permit_is_bound_to_exact_action_fingerprint(gateway):
    original = make_action(payload={"case_id": "SYN-1", "scope": "read-only"})
    _, permit = gateway.authorize(original)
    assert permit is not None

    modified = make_action(payload={"case_id": "SYN-1", "scope": "modified-after-approval"})

    with pytest.raises(PermissionError):
        gateway.execute(modified, permit, lambda payload: payload)
