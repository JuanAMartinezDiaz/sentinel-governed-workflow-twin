# Enterprise integration contracts - Phase 1

**Design and fixture package only. No enterprise API routes, approval service,
commercial GRC connector, permit issuer or bank adapter are implemented here.**

Contract version: `1.0.0` (proposed). Reviewed public baseline:
`db1450893942393418a35fd3147cd24ac806c70a`.
All bank records, amounts, subjects, domains and scenarios are fictional.

## Review order

1. [Requirements and semantics](semantics.md): normative behavior for a future implementation.
2. [OpenAPI](openapi.json): proposed service boundaries, roles, inputs and responses.
3. [JSON Schema](contract.schema.json): 32 named definitions under `$defs`.
4. [Structural examples](fixtures/examples.json) and [wire cases](fixtures/wire-cases.json).
5. [Acceptance scenarios](fixtures/acceptance-cases.json) and [fixture protocol](fixtures/README.md).
6. [Phase 1 review record](../../../docs/enterprise-integration-phase1.md).

Select a named `$defs` schema; the schema document is a definition bundle, not a
generic validator of all message types. The OpenAPI component definitions are
equivalent, using local references; a regression check detects drift between them.
OpenAPI 3.1.1 is an explicitly pinned compatibility choice, not a claim to be the
latest published OpenAPI release.

## What can be tested now

`python -m pytest -q tests/test_enterprise_contracts.py` validates schema and
OpenAPI structure, examples, negative wire cases, contract parity, authentication
requirements and the acceptance catalog's integrity. Install `.[dev]` first.

It does **not** run the catalog against Sentinel. Every runtime scenario is marked
`NOT_RUN`, with the catalog runtime marked `NOT_IMPLEMENTED`. Expected decisions
were specified from the fictional business rules, without calling the existing
engine. That separation is not an independent assurance opinion: a reviewer
independent of the implementer must approve the oracle and later assess results.

The existing `sentinel_ref`, `api` and visual demonstration remain separate.
Schema-valid requests are not necessarily authorized. For example, `$750` is a
well-formed amount but exceeds this workflow's delegation and must be denied by
the future semantic evaluator.

## Protocol versioning

The body requires `contract_version: "1.0.0"`. Unsupported versions or unknown
fields are rejected, including nested fields. Because this contract is closed,
adding an accepted field or enum value requires a coordinated version change;
do not silently treat it as backward compatible. Never coerce malformed money,
drop unknown fields, or select a permissive fallback schema.

`v1` identifies this proposed API family. Before a release, its exact schemas,
policy mapping and digest profile must be pinned together. Policy content version,
source revision, delegation revision and revocation epoch are distinct from API
schema version; all are checked in their own roles.

Reserved `.invalid` hosts are illustrative placeholders. The example JWS strings,
certificate thumbprints and hashes establish shape only and are not usable keys,
signatures, credentials or cryptographic test vectors.
