# Enterprise integration Phase 1 review

Date: November 12, 2026. Status: **draft contracts and fixtures for review**.

This work specifies how existing enterprise governance decisions could constrain
an agent's execution permissions. It adds reviewable interfaces and test oracles;
it does not build an operational commercial GRC integration, enterprise approval
service, permit service or business-tool connector.

The inspected base is public main
`db1450893942393418a35fd3147cd24ac806c70a`. The public reference currently has an
in-memory authority registry, deterministic arbitration, HMAC action binding and
an application-level protected executor. Human approval is a caller assertion.
This package defines a separate enterprise contract; it does not claim to extend
those runtime protections yet.

## Reviewable additions

| Item | Scope |
|---|---|
| [Contract schema](../contracts/enterprise/v1/contract.schema.json) | 32 definitions covering source/policy versions, delegated authority, authenticated identity, action intent, approval binding, permit claims, execution and evidence |
| [OpenAPI](../contracts/enterprise/v1/openapi.json) | 11 proposed paths, scoped service roles, AND-combined token/mTLS authentication, request idempotency and explicit error/outcome shapes |
| [Semantics](../contracts/enterprise/v1/semantics.md) | R01-R10: the fictional bank rules, publication, identity, approval, canonicalization, revocation, duplicate-effect control, isolation, recovery and evidence |
| [Wire cases](../contracts/enterprise/v1/fixtures/wire-cases.json) | 28 explicit valid/invalid shape cases, including rejected caller approval flags and structurally valid but over-limit amounts |
| [Examples](../contracts/enterprise/v1/fixtures/examples.json) | 20 synthetic structural examples; placeholder JWS values/hashes are not cryptographic test vectors |
| [Acceptance catalog](../contracts/enterprise/v1/fixtures/acceptance-cases.json) | 40 declarative future runtime scenarios with expected results, all NOT_RUN |
| [Validation tests](../tests/test_enterprise_contracts.py) | Artifact validation; does not execute the acceptance scenarios against an enterprise backend |

The catalog's expected outcomes were authored from business rules independently of
the reference engine's output. No independent third-party reviewer has accepted
them. Deployment adapters, actual cryptographic test vectors and enterprise
acceptance execution remain future work.

## Important contract choices

- GRC source revisions, policy versions, grant revisions and revocation epochs
  remain distinct and are bound into authorization evidence.
- The agent submits intent only; identity, classification, canonical targets and
  authority are resolved from trusted services.
- Human approval is an authenticated attestation bound to exact action and versions,
  not a Boolean or merely an identity token.
- Single-use permits and unique business effects are separate controls. Two permits
  and overlapping fee-item sets must not produce duplicate refunds.
- Revocation is defined at dispatch admission. Already-admitted bank calls may
  commit; UNKNOWN outcomes require authoritative reconciliation.
- The executor accepts a stored request reference and permit, not an arbitrary
  callback or target URL. Credentials and bank-side controls remain separate.
- Evidence acknowledgment requires confirmed GRC writeback, not just queueing.

## Validation evidence

Local validation on November 12, 2026 used Python 3.12.14, pytest 9.2.0,
jsonschema 4.26.0, openapi-spec-validator 0.8.5 and Node.js 24.22.1.

| Check | Observed result |
|---|---|
| `python -m pytest -q tests/test_enterprise_contracts.py` | 97 artifact-validation tests passed |
| `python -m pytest -q` | 172 passed: 75 existing reference tests plus 97 new artifact-validation tests |
| `python -m scripts.sync_demo_scenarios --check` | Existing synthetic scenario contract synchronized |
| `node --check --input-type=module < docs/xray2.js` | Passed |
| `node --test tests/test_demo_client.mjs` | 18 passed |
| Baseline source SHA verification | All 61 retrieved text files match the pinned Git blobs |

The 40 catalog scenarios remain **NOT_RUN** against an enterprise implementation;
validating their shape or baseline references does not execute their control
claims. Tests do not demonstrate authenticated enterprise approval, commercial
GRC compatibility, runtime single-use permits, revocation or actual bank writes.
The exact branch commit and hosted CI result belong to the draft pull request.
The remote tree preserves all pre-existing binary assets from the pinned base.

## Review decision still required

The first implementation decision should confirm this contract, resolve the actual
GRC/identity/bank sandbox choices, approve the independent fixture oracle, and
establish operating owners. Phase 2 runtime implementation, merge and deployment
are not authorized by the Phase 1 design approval.

No existing runtime module, demonstration API handler, browser asset, or deployment
configuration is changed. The only existing dependency change is in the development
test extras to validate OpenAPI and JSON Schema formats in normal CI.
