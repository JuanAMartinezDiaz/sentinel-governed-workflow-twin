# Fixture protocol and evidence boundary

`examples.json` contains structural examples with placeholder hashes/JWS values.
`wire-cases.json` contains explicit positive/negative JSON Schema instances.
`acceptance-baseline.json` supplies a common fictional bank state.
`acceptance-cases.json` specifies expected runtime outcomes without running them.

The oracle is derived from [R01-R10](../semantics.md), not from the implementation.
An independent reviewer still needs to approve it. Do not label the catalog
"independently tested" or count these scenarios as passed runtime controls.

## Future harness protocol

1. Load a fresh copy of the baseline for each scenario. Apply `baseline_overrides`
   as replacement JSON Pointers; every pointer must identify an existing field.
2. Apply the scenario's explicit `setup` and run its `sequence` in order. A future
   deployment-specific adapter must resolve these declarative operations to actual
   APIs, fixture records and failure hooks. That adapter is deliberately absent
   from Phase 1; the catalog is not yet an executable end-to-end suite.
3. Use isolated test identities/keys, independently seed authoritative source and
   bank state, compute real hashes, and issue genuine sandbox attestations/permits.
   Never treat `syntheticHeader.syntheticPayload.syntheticSignature` or the repeated
   example hash as valid. For the wrong-certificate test, keep the token fixed and
   change the TLS certificate. For wrong-tenant tests, use a real different tenant.
4. For race cases, synchronize workers at admission; vary scheduling and inject
   failure at reserve, dispatch, bank commit, evidence record and acknowledgment.
   Read actual bank ledger rows/receipts as the business-effect oracle, not the
   agent's claimed result or the gateway's HTTP response alone.
5. Compare terminal result, reason, permit behavior and new business effects with
   the expected values. `new_business_effects` counts effects during the WHOLE
   sequence, not just its last call. Thus A18 permits the first refund and blocks
   replay; A17/A37 start with one pre-existing effect and require zero new effects.
6. Record observed results separately with build/config/fixture digests, timestamps,
   trace/receipt references, reviewer identity and unresolved defects. Do not edit
   expected outcomes to match an implementation failure.

The baseline's scope ends at 16:00Z. Boundary and expiry tests adjust trusted test
clock deliberately; they must not disable production time validation. When setup
changes the fee amount, update authoritative eligible fee facts as specified so
the test isolates the intended limit instead of failing eligibility first.

## Follow-on cases before acceptance

The 40 scenarios cover the initial architecture decisions. Independent acceptance
must additionally exercise real vendor notification ordering and reconciliation,
end-to-end tenant isolation, mapping review/approval signatures, cross-language
canonicalization vectors, issuer/algorithm confusion, overlapping fee-item sets,
parent budget consumption, token and role expiry, source restoration, evidence
tamper/gap detection, retention/restore, pagination, rate limits and operational
load. No finite scenario catalog proves production security by itself.
