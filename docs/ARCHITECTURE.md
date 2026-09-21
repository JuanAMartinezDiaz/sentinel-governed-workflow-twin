# Architecture

Sentinel separates **ability to propose** from **authority to execute**.

## Reference layers

1. **Workflow Twin** — represents the baseline process and proposed redesign.
2. **Agent Proposal** — expresses an intended action without conferring permission.
3. **Authority Registry** — defines the action classes, tools, and maximum risk delegated to an agent.
4. **Decision Arbitration** — evaluates identity, delegated action, tool permission, risk ceiling, confidence, and approval state.
5. **Execution Permit** — cryptographically binds an authorization decision to the exact action fingerprint.
6. **Protected Executor** — rejects execution without a valid permit.
7. **Evidence Ledger** — records the decision path and disposition.
8. **Outcome Metrics** — compares baseline and redesigned workflow results.

## Invariant

A consequential operation should not be reachable merely because an AI system can generate the correct tool call.

The reference implementation therefore routes authority through a separate decision path and makes direct execution fail closed.

## Production extension

The public code demonstrates the pattern at application level. Strong deployments should move policy enforcement into an independently protected boundary and combine it with operating-system, identity, network, and credential controls.
