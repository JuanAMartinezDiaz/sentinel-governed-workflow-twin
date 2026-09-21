# Run the Sentinel governance demo

A reviewer can inspect the core governance behavior in about three minutes.

## Option 1 - No installation

Open the live visual demo:

**https://morbiaus.github.io/sentinel-governed-workflow-twin/**

Try these cases:

1. Low-risk read -> **ALLOW**
2. High-risk state change without approval -> **REQUIRE_APPROVAL**
3. Same state change with approval -> **ALLOW**
4. Direct protected-executor call without permit -> **BLOCKED**
5. Moderate-risk action below confidence threshold -> **FALLBACK**

## Option 2 - Run the Python reference engine

~~~bash
git clone https://github.com/Morbiaus/sentinel-governed-workflow-twin.git
cd sentinel-governed-workflow-twin
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
python -m sentinel_ref.cli
~~~

Expected: **13 passed**, then the demo returns REQUIRE_APPROVAL without human approval and ALLOW with approval.

The reference is intentionally small enough to inspect. It proves that action generation alone does not authorize execution, direct protected execution fails closed, insufficient confidence selects fallback, and every governance decision emits evidence.

The public reference is an application-layer demonstration. Production architecture should add stronger workload identity, OS/process isolation, network controls, least-privilege credentials, protected services, and tamper-evident evidence storage.
