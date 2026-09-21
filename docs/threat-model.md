# Threat model

This public threat model describes the security properties demonstrated by the reference implementation. It is intentionally narrower than a production Sentinel threat model.

| Threat | Example | Reference control | Result |
|---|---|---|---|
| Unregistered agent | Unknown agent proposes an action | Authority Registry | DENY |
| Delegation overreach | Registered agent proposes an undelegated action class | Action-class authorization | DENY |
| Tool escalation | Agent attempts an unapproved tool | Tool permission check | DENY |
| Risk escalation | Proposed action exceeds the agent risk ceiling | Risk ceiling | DENY |
| Low-confidence execution | Material action falls below declared confidence | Confidence gate + bounded fallback | FALLBACK |
| Missing human authority | High-risk action has no approval | Human approval gate | REQUIRE_APPROVAL |
| Direct executor bypass | Code calls protected executor without permit | Permit validation | BLOCK |
| Permit tampering | Signature is changed | HMAC validation | BLOCK |
| Permit replay on modified action | Approved payload is changed after authorization | Action fingerprint binding | BLOCK |
| Evidence loss | Decision occurs without a reconstructable trace | Evidence ledger | Evidence emitted at decision boundary |

## Trust boundaries

The public reference contains three logical trust boundaries:

1. **Proposal boundary** — an agent can form an intended action but gains no execution right merely by doing so.
2. **Authorization boundary** — deterministic checks decide whether execution authority exists and may issue a permit.
3. **Execution boundary** — the protected operation requires a permit bound to the exact action fingerprint.

## Deliberate limitations

The reference implementation holds its signing secret in process memory. That is sufficient to demonstrate permit binding and fail-closed application behavior, but it is not intended to resist malicious code already executing inside the same process.

A production implementation should consider:

- independently protected policy/enforcement services
- workload or non-human identity
- short-lived least-privilege credentials
- operating-system or container isolation
- egress/network policy
- policy and model version binding
- nonce/expiry/replay controls where permits cross trust boundaries
- tamper-evident evidence storage
- independent monitoring and alerting
- explicit break-glass and recovery procedures

## Security invariant

**Generating a syntactically valid tool call is not equivalent to possessing authority to execute it.**

The reference tests are designed to make that distinction observable and reproducible.
