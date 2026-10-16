# Run the Sentinel governance demo

A reviewer can inspect the core governance behavior in about three minutes.

## Option 1 - No installation

Open the live visual demo:

**https://juanamartinezdiaz.github.io/sentinel-governed-workflow-twin/**

<!-- BEGIN SYNTHETIC SCENARIOS -->
The API supports **6 fixed synthetic scenarios**, all **6 available in Decision X-Ray**. No scenarios are API-only.

| API scenario | Visual selection | Decision | Simulated execution |
|---|---|---|---|
| `low-risk-read` | LOW RISK READ | `ALLOW` | `SUCCEEDED` |
| `high-risk-pending` | HIGH RISK / NO APPROVAL | `REQUIRE_APPROVAL` | `BLOCKED` |
| `high-risk-approved-demo` | HIGH RISK / SIMULATED APPROVAL | `ALLOW` | `SUCCEEDED` |
| `direct-executor-bypass` | BYPASS ATTEMPT | `BLOCKED` | `BLOCKED` |
| `low-confidence-draft` | LOW CONFIDENCE | `FALLBACK` | `BLOCKED` |
| `unapproved-tool` | UNAPPROVED TOOL | `DENY` | `BLOCKED` |
<!-- END SYNTHETIC SCENARIOS -->

GitHub Pages displays generated illustrative traces. It has no Python runtime. A connected API is identified explicitly by the status indicator. All approval is simulated.

## Option 2 - Run the Python reference engine

~~~bash
git clone https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin.git
cd sentinel-governed-workflow-twin
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
python -m sentinel_ref.cli
~~~

Expected: the complete test suite passes, then the demo returns REQUIRE_APPROVAL without human approval and ALLOW with approval.

The reference is intentionally small enough to inspect. It proves that action generation alone does not authorize execution, direct protected execution fails closed, insufficient confidence selects fallback, and every governance decision emits evidence.

The public reference is an application-layer demonstration. Production architecture should add stronger workload identity, OS/process isolation, network controls, least-privilege credentials, protected services, and tamper-evident evidence storage.
