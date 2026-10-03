# Evidence model

Governance becomes materially more useful when every consequential decision produces structured evidence.

The reference evidence record contains:

- workflow and step identifiers
- agent identity
- action class and tool
- risk tier
- immutable action fingerprint
- final disposition
- reason
- whether an execution permit was issued
- ordered control trace
- timestamp

This permits an independent reviewer to reconstruct **what was proposed, what controls evaluated it, what decision was reached, and whether execution authority existed**.

A production evidence plane should additionally address integrity, retention, access control, correlation identifiers, model/tool versions, policy version, human approver identity, and tamper-evident storage.

## Decision context and observed execution

`ProtectedExecutor.run_governed` records the effective policy snapshot and its
SHA-256 fingerprint, delegated agent authority, required confidence, and the
caller-provided approval flag before attempting protected execution. A unique
`decision_id` joins that decision to its observed `BLOCKED`, `SUCCEEDED`, or
`FAILED` execution event. Permit issuance alone does not establish execution.
Repeated proposals retain separate decision IDs even when their action
fingerprints match. Tool outputs and exception messages are excluded from the
package to avoid unnecessary sensitive-data retention.

The evaluated trace connects concrete controls to the effective policy:

| Control | Evaluated source | Risk addressed |
| --- | --- | --- |
| Agent registration | Authority registry lookup | Unknown agent |
| Delegated action | Authority snapshot: allowed actions | Unauthorized action class |
| Tool permission | Authority snapshot: allowed tools | Unapproved tool use |
| Risk ceiling | Authority snapshot: maximum risk tier | Excessive delegated risk |
| Confidence | Policy threshold for declared risk tier | Insufficient confidence |
| Human approval | Policy approval threshold and caller flag | Unapproved consequential action |

Run `python -m sentinel_ref.cli --evidence-package /tmp/sentinel-evidence.json`
to export the synthetic demonstration. The package contains both waiting for
approval and successful execution evidence. Tests also cover blocked actions,
operation failures, policy changes, and evidence-write failure before execution.

These records support inspection, not a certification or compliance claim.
Approval remains a caller assertion; it is not authenticated approver evidence.
The policy hash identifies effective configuration, not an approved policy
library version. Risk and confidence remain declared inputs. The ledger is not
tamper-proof, and an execution failure may include partial tool side effects.
Production integration needs trusted classification, authenticated approval,
retention controls, independently protected storage, and clean-start validation
against the real agent and protected tool.
