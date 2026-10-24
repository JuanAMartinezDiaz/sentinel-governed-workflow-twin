# Synthetic demo acceptance — October 24, 2026

## Scope
A browser scenario selection calls POST /api/demo, runs the Python reference governance engine, and displays the decision, checks, request-scoped evidence ID, and execution outcome. This acceptance covers the public synthetic demonstrator only.

## Reviewed revisions
- Reconciled main at 6698358fb8a7dd3b6bb4544f2f8b1c759a44eff5 into the PR through merge commit 321113073b9a09ae4beb298772d55db69aacb5c5.
- Application revision tested on Vercel: fcb9559bac4e4490e9267e29e0b701457d115197.
- Conflicts in README.md and docs/index.html were test-count labels. Kept links to current CI instead of stale totals; preserved main's evidence sample and release-readiness documentation.

## Reproduced checks
- Python 3.12.14: python -m pytest -q — 75 passed.
- Node 24.22.1: node --test tests/test_demo_client.mjs — 18 passed.
- Generated scenario consistency, JavaScript module syntax, and git whitespace checks passed.
- GitHub PR CI on application revision: [successful run 40095841633](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/actions/runs/40095841633).
- GitHub push CI: [successful run 40095837674](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/actions/runs/40095837674).

## Hosted verification
Vercel preview deployment dpl_ACoHSbPSCERZA1yafSxFqrCcVTxz reached READY:
https://sentinel-reference-demo-cclawms6p-morbiaus-projects.vercel.app

Deployment protection remains enabled. Authorized testing used a temporary share link; its access parameter is intentionally omitted here.

The initial build detected a single Python application and failed with PYTHON_ENTRYPOINT_NOT_FOUND. The repository uses separate api/demo.py and api/health.py functions. Setting Framework Preset to Other fixed the build; vercel.json now explicitly sets framework to null for reproducibility.

GET /api/health returned HTTP 200, synthetic-demo-only mode, and exactly six scenarios.

## Browser evidence
Playwright 1.62.1 with headless Chromium 153 and software WebGL exercised the actual hosted site and its actual API (no mocked success responses or substituted graphics libraries). The default Playwright browser download failed; Chromium was obtained from the @sparticuz/chromium 153.0.0 package instead.

At 1440 × 1000 and emulated 390 × 844 viewports, clicked each scenario, waited for connected status, and checked the displayed disposition. Desktop traces included request-specific evidence IDs.

| Scenario | Observed disposition |
|---|---|
| low-risk-read | ALLOW |
| high-risk-pending | REQUIRE_APPROVAL |
| high-risk-approved-demo | ALLOW |
| direct-executor-bypass | BLOCKED |
| low-confidence-draft | FALLBACK |
| unapproved-tool | DENY |

Additional assertions:
- Posting high-risk-pending with an extra human_approved field returned HTTP 400.
- Intentionally aborting the demo API request produced the unavailable indicator and ILLUSTRATIVE fallback trace.
- All six buttons were present; phone layout had no document-level horizontal overflow.
- No uncaught page errors occurred.
- Desktop and phone full-page screenshots were inspected. Phone camera framing initially clipped stages; resize now fits all six stages and adjusts fog depth.
- This was browser emulation, not a physical phone test. Software WebGL does not establish hardware-specific animation performance.

## Acceptance boundary
Suitable to merge as a synthetic public reference demo. No claim of production Sentinel acceptance, real human approval, live business-tool execution, customer ingestion, durable evidence, tenant isolation, or proprietary workflow-fixture completion. GitHub Pages remains static; the Python API requires a runtime such as the tested Vercel configuration.
