# Public reference verification November 9 2026

This report records local verification of Sentinel's public synthetic reference. Runtime and test source were checked out at revision `b66ba2c6fa0e39e16f57e3e1e0102d610f6653b5`; the accompanying portfolio update changes documentation only. The tests were executed with automated assistance on Windows using Python 3.12.14 and Node.js 24.22.1. This is a reproducible project check, not an independent assurance opinion or production acceptance.

| Check | Observed result |
| --- | --- |
| `python -X utf8 -m pytest -q --basetemp <writable-test-directory>` | **75 passed** in 1.27 seconds |
| `node --test tests/test_demo_client.mjs` | **18 passed**, zero failures |

The Python suite covers policy arbitration, simulated approval, protected execution, permit integrity and action binding, evidence recording, API outcomes, workflow metrics, and consistency between scenario fixtures and the browser demonstration. The browser-client suite checks connected responses and explicitly identified illustrative fallback behavior. Inspect the [tests](../tests) and [CI configuration](../.github/workflows/ci.yml) for the precise assertions and normal dependency setup.

On the first Windows run, 70 Python tests passed, two failed because the local default text encoding could not read UTF-8 fixtures, and three could not create temporary directories. Re-running with UTF-8 mode and a writable test directory resolved those environment problems without changing runtime or test source. The final result above applies to that configuration.

Passing these tests establishes the asserted behavior for the included fixtures. Approval remains simulated; declared risk and confidence inputs are not independently calibrated; the public API does not establish durable evidence retention or tenant isolation. No customer deployment, measured business savings, production security assessment, or acceptance of the proprietary Sentinel product was tested. See the [case study](case-study.md), [framework crosswalk](framework-alignment.md), and [release-readiness framework](release-readiness-framework.md) for the relationship between this evidence and the remaining work.

Results are dated and revision-specific. Later code changes require new verification.
