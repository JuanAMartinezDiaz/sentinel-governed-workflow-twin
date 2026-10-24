"""Fixed synthetic API inputs and visual metadata; no customer records."""

from typing import Any

from sentinel_ref.models import RiskTier


SCENARIOS: dict[str, dict[str, Any]] = {
    'low-risk-read': {
        'action_class': 'READ_CASE',
        'tool_name': 'case_api',
        'risk_tier': RiskTier.LOW,
        'confidence': 0.95,
        'human_approved': False,
        "visual": {
            'key': 'read',
            'title': 'LOW RISK READ',
            'tone': 'cyan',
            'stop': 'pass',
            'label': 'LOW RISK READ',
            'sub': 'Read-only action. Human approval is not required.',
            'summary': (
                'The agent is registered, READ_CASE is delegated, case_api is approved, the '
                'action is within the risk ceiling, and confidence clears the LOW threshold.'
            ),
        },
    },
    'high-risk-pending': {
        'action_class': 'COMMIT_ACCOUNT_CHANGE',
        'tool_name': 'account_change_api',
        'risk_tier': RiskTier.HIGH,
        'confidence': 0.97,
        'human_approved': False,
        "visual": {
            'key': 'high',
            'title': 'HIGH RISK ACTION',
            'tone': 'amber',
            'stop': 'gate',
            'label': 'HIGH RISK / NO APPROVAL',
            'sub': 'Stops at the authority boundary.',
            'summary': (
                'The agent may propose the state change, but capability does not supply '
                'authority. No execution permit exists until the required human approval is '
                'present.'
            ),
        },
    },
    'high-risk-approved-demo': {
        'action_class': 'COMMIT_ACCOUNT_CHANGE',
        'tool_name': 'account_change_api',
        'risk_tier': RiskTier.HIGH,
        'confidence': 0.97,
        'human_approved': True,
        "visual": {
            'key': 'approved',
            'title': 'SIMULATED APPROVAL',
            'tone': 'green',
            'stop': 'pass',
            'label': 'HIGH RISK / SIMULATED APPROVAL',
            'sub': 'Fixed simulation; no person approved an action.',
            'summary': (
                'This fixed synthetic scenario simulates approval, binds authorization to the '
                'action fingerprint, and allows a simulated protected operation. No person '
                'approved an action.'
            ),
        },
    },
    'direct-executor-bypass': {
        'action_class': 'COMMIT_ACCOUNT_CHANGE',
        'tool_name': 'account_change_api',
        'risk_tier': RiskTier.HIGH,
        'confidence': 0.97,
        'human_approved': False,
        'attempt_direct_bypass': True,
        "visual": {
            'key': 'bypass',
            'title': 'BYPASS ATTEMPT',
            'tone': 'red',
            'stop': 'bypass',
            'label': 'BYPASS ATTEMPT',
            'sub': 'Protected executor rejects a missing permit.',
            'summary': (
                'The governed request first requires approval. A separate direct executor '
                'call without a valid permit is then rejected. The returned ledger records '
                'the governed request; the additional bypass rejection appears in the trace.'
            ),
        },
    },
    'low-confidence-draft': {
        'action_class': 'DRAFT_RECOMMENDATION',
        'tool_name': 'recommendation_service',
        'risk_tier': RiskTier.MODERATE,
        'confidence': 0.65,
        'human_approved': False,
        "visual": {
            'key': 'confidence',
            'title': 'CONFIDENCE BELOW FLOOR',
            'tone': 'amber',
            'stop': 'fallback',
            'label': 'LOW CONFIDENCE',
            'sub': 'Bounded fallback, no execution.',
            'summary': (
                'The proposed action is otherwise delegated, but confidence is below the '
                'MODERATE threshold. The reference engine selects the declared safe fallback '
                'without executing an action.'
            ),
        },
    },
    'unapproved-tool': {
        'action_class': 'READ_CASE',
        'tool_name': 'unapproved_external_tool',
        'risk_tier': RiskTier.LOW,
        'confidence': 0.95,
        'human_approved': False,
        "visual": {
            'key': 'tool',
            'title': 'UNAPPROVED TOOL',
            'tone': 'red',
            'stop': 'gate',
            'label': 'UNAPPROVED TOOL',
            'sub': 'Tool permission denied, no execution.',
            'summary': (
                'READ_CASE is delegated and the action is low risk, but the requested tool is '
                "outside the agent's approved tools. The tool-permission check denies the "
                'action and no execution permit is issued.'
            ),
        },
    },
}
