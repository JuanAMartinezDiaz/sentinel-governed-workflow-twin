# Security

This repository is a public reference implementation and contains no production credentials, customer data, employer data, or private Sentinel source code.

## Security model

The sample protected executor demonstrates an application-layer authorization boundary using action fingerprints and HMAC-signed permits. It is intended to make the capability-versus-authority distinction testable.

It is **not** a claim that an in-process Python boundary is sufficient for hostile-code isolation.

A production implementation should apply controls appropriate to the threat model, including combinations of:

- separate-process or separate-service policy enforcement
- workload identity and short-lived credentials
- least-privilege tool scopes
- network policy
- operating-system sandboxing
- secrets isolation
- tamper-evident evidence storage
- independent monitoring and alerting
- explicit human approval for consequential actions

Please do not submit real customer, employer, or sensitive operational data in issues or pull requests.
