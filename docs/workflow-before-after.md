# Workflow before and after

The workflow example is deliberately synthetic. Its purpose is to show how Sentinel separates **workflow redesign** from **authority redesign**.

## Baseline

~~~mermaid
flowchart LR
  A[17-step process] --> B[Human touch at every step]
  B --> C[Sequential handoffs]
  C --> D[Partial decision evidence]
  D --> E[960 min illustrative cycle time]
~~~

## Governed redesign

~~~mermaid
flowchart LR
  A[Workflow Twin] --> B[Bounded agent work]
  B --> C[Human decision review]
  C --> D[Approval before state change]
  D --> E[Protected execution]
  E --> F[Evidence ledger]
  F --> G[Outcome measurement]
~~~

Human authority remains at S13 (decision review) and S15 (approval before state change). The agent at S16 may execute only after the protected gateway issues a permit bound to the exact proposed action.

| Measure | Baseline | Governed redesign |
|---|---:|---:|
| Cycle time | 960 min | 190 min |
| Cost units | 100 | 36 |
| Quality defect rate | 7.5% | 2.0% |
| Human touches | 17 | 6 |
| Evidence completeness | 45% | 100% |

These values are synthetic design targets, not production claims.
