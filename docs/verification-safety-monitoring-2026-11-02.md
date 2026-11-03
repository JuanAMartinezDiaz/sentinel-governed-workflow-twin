# Safety-monitoring design validation - November 2, 2026

## Result and scope

The public reference can generate and validate a versioned monitoring design for
each workflow step. **Operational six-goal acceptance remains UNVERIFIED and the
release decision remains BLOCKED.** This record concerns the design tool only.

Implementation commit: `fcf3d9d9aaa1a3b75df8b6cb8c60ff30ace9c8ab`.
Tested tree: `a7c816d037d2515c3fe8c9b29bbf6b903bb42918`.
Base: `b66ba2c6fa0e39e16f57e3e1e0102d610f6653b5`.

The locally tested staged tree matched the implementation tree published to the
feature branch. [GitHub Actions run 41556388797](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/actions/runs/41556388797)
completed successfully for that implementation commit. This subsequent
documentation/evidence addition has no executable changes; its own CI result must
be checked separately.

## Observed local checks

| Check | Result |
|---|---|
| Focused design-boundary suite | 45 passed, 0 failed |
| Full Python suite | 120 passed, 0 failed; includes the 45 focused cases |
| Browser regression suite | 18 passed, 0 failed |
| Scenario synchronization | Passed; six existing API/demo scenarios unchanged |
| Browser syntax | Passed |
| Staged diff whitespace | Passed |

Local environment: Python 3.12.14, pytest 9.2.0, jsonschema 4.26.0, Node v24.22.1.
Development dependencies were reused from an existing local test installation;
no production dependencies were added.

The new tests exercise generation for five- and 17-step twins, schema validity,
changed workflow binding, missing/duplicate steps and goals, omitted mandatory
events/tests, failed controls, unsupported exemptions, fabricated approvals and
verification, malformed/oversized input and CLI exit/overwrite behavior.

## Generated draft observations

The five-step fixture produces 30 step/goal entries, all declared `specified`.
It reports 125 unresolved design fields/requirements because owner identities,
tool boundaries, event producers and rules are intentionally unassigned. These
are explicit draft gaps, not 125 failed runtime tests.

A fully populated synthetic declaration can become `COMPLETE` as a design
document. It still cannot grant release approval. Even fabricated `verified`
labels and approval references leave operational acceptance unverified.
`--require-operational-acceptance` returns code 2 in this version.

Evidence:
- [Verification record and tested file hashes](../evidence/safety-monitoring-design-2026-11-02/verification.json)
- [Generated draft assessment summary](../evidence/safety-monitoring-design-2026-11-02/draft-assessment.json)

These records are implementer-generated and unsigned. They are not an independent
assurance opinion. GitHub CI establishes automated regression results, not
operating control effectiveness or human release acceptance.

## Not executed or established

SM-01 through SM-08 runtime trials are **NOT RUN**. No authenticated human approval,
protected evidence writer, isolated business resource, real-agent containment,
cross-process revocation, durable business idempotency or proprietary-product
integration was tested here. Existing R08 and R09 acceptance gaps remain open.

The next operational increment must connect trusted identity, action-specific
approval, source-fact validation and durable independent evidence to the actual
candidate execution boundary. Use the [runtime acceptance contract](safety-monitoring.md#runtime-acceptance-contract-not-run)
and retain separate results for design validation and deployed controls.

## Reproduction

```bash
python -m pytest -q
python -m scripts.sync_demo_scenarios --check
node --test tests/test_demo_client.mjs
node --check --input-type=module < docs/xray2.js
python -m scripts.safety_monitoring check \
  --workflow examples/synthetic_dispute_monitoring_workflow.json \
  --workflow-version synthetic-dispute-v1 \
  --specification examples/synthetic_dispute_monitoring_specification.json \
  --require-operational-acceptance
```

The last command is expected to return **2**, with an incomplete design and blocked
release. Do not treat that expected result as a failed software regression or an
operational acceptance pass.
