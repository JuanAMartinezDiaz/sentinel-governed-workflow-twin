# Authority semantics for a future implementation

Status: proposed design. These requirements are not implemented by Phase 1.
`R01`-`R10` form the independently specified oracle used by the acceptance catalog.
The financial thresholds below are fictional bank policy, not legal requirements.

## R01 - Monetary scope and trusted business facts

Only `POST_FEE_REFUND` through `core.refund.v1`, in the approved workflow, account
partition and tenant/environment, is in scope. Refunds must correct independently
verified erroneous fee items and credit their original account in USD. An inactive
account, ineligible fee, altered destination or amount above the eligible fee total
is denied. The action-to-tool mapping is a pair, not two unrelated allowlists.

Each amount is an integer number of cents, strictly positive, no more than
`2^53-1`. `$0.01` through `$100.00` can execute within active delegation without
individual approval. Above `$100.00` through `$500.00` requires an independent
operations manager. Above `$500.00` is denied on this agent path even if a manager
approves. The existing human procedure remains available separately.

For approval thresholds, use requested amount plus already applied and reserved
refunds on the same case. A first `$75` refund followed by a second `$75` request
therefore requires approval for the second request. Also enforce per-case,
per-account UTC-day and per-grant UTC-day budgets. Reservations and admission must
be atomic. Verify the fee source and cap individually per fee item; a unique
constraint per tenant/account/fee item/remedy prevents overlapping fee sets from
being refunded twice. A set-level operation key alone is insufficient.

Agent confidence, prose and self-declared risk never increase authority. Trusted
action metadata and source facts determine the control path.

## R02 - Authentication, parsing and trust

Every API operation requires BOTH an enterprise OAuth access token with its stated
scope and mutual TLS; the two schemes are in the same OpenAPI security requirement
object. Verify issuer, audience, expiry, tenant/environment and the access token's
binding to the presented workload certificate. OAuth scope is necessary, not
sufficient authorization. Validate the current grant and object ownership too.

Resolve workload identity and tenant from verified credentials, never the agent
body. Validate that any service-submitted tenant, source or grant matches that
authenticated context. Cross-tenant object lookup returns no record details.
The `WorkloadIdentity` certificate thumbprint uses a `sha256:` hex representation;
the JWS `cnf.x5t#S256` uses base64url of the same SHA-256 certificate DER digest.
Conversion must be exact; do not compare those two strings directly.

Parse strictly before schema validation: reject duplicate JSON keys, invalid UTF-8,
unpaired surrogates, NaN/Infinity and numbers outside the exact supported range.
Apply body-size, depth, array-count and rate limits. Do not silently round values.
`format` checks are assertions in the chosen validator configuration. All timestamps
are UTC with `Z`; comparisons use trusted service time. Request headers containing
tokens and permit/approval JWS bodies are excluded from logs and evidence exports.

## R03 - Source, policy and delegation publication

GRC/AI governance owns the decision. Sentinel owns its reviewed executable
representation. The connector may submit candidates; it cannot activate them.
Retrieve authoritative source state after an authenticated change notification;
deduplicate notifications and reconcile missed/out-of-order changes by source
revision. Conflicting revisions for the same system/tenant/record identity cannot
coexist in an active bundle. Never interpret narrative instructions as executable
authority.

Required publication sequence: `CANDIDATE -> VALIDATED -> APPROVED -> ACTIVE`.
Require named business/control ownership and an independent mapping reviewer.
Publisher and reviewer must be distinct eligible principals. Their signed review
attestation binds the exact definition digest and source revisions. Validation
failure or conflicting source decisions prevents activation. Store revisions
immutably; compare-and-set protects activation from concurrent updates.

Policy activation may end in `SUPERSEDED` or `REVOKED`; neither is reactivated
in place. Rollback is a newly reviewed version with a higher revision, not reuse
of an old version number or clearing a revocation flag. Relevant changes invalidate
outstanding approvals and permits. Source revisions are opaque equality tokens,
not integers to compare lexically. Reuse of a revision with changed content is a
conflict and an integrity incident.

Delegations require a named owner and independent authorizer. States are
`CANDIDATE -> ACTIVE -> SUSPENDED | EXPIRED | REVOKED | SUPERSEDED`.
Resumption requires a new reviewed revision. A child is a subset of every ancestor
in action/tool/resource scope, validity interval, environment and monetary limits.
It cannot create extra budget. Parent budgets are charged atomically along with
child budgets, so multiple children cannot multiply the parent's allowance.
Parent revocation invalidates descendants. A root grant requires an explicit
approved root-authority source; the agent cannot create or expand its own grant.

Check authoritative GRC revision/status at both permit issuance and dispatch
admission. In this initial profile, unavailable or mismatched source state blocks
the action. A future cache/freshness lease requires an explicit revised policy.
A GRC update becomes enforceable when observed; this distributed race is not
removed by synchronous reads. An urgent kill switch must reach Sentinel directly.

## R04 - Human approval

Only the trusted approval backend calls `submitApprovalDecision`, using its own
workload credentials. A human logs in through the enterprise identity provider
and performs the review; an ID token or OAuth access token alone is not an approval.
Verify an allowlisted approval issuer and signature, and compare every signed
submission field with the request envelope. The attestation must carry the human
subject/issuer, role, authentication assurance/time, decision/time/expiry and the
full `ApprovalBinding`. Caller-supplied role names are not trusted.

The displayed review must include exact amount, account reference, fee items,
reason/evidence and policy/authority versions. The approver must have the current
`fee-refund-manager` role, the configured step-up assurance, and differ from the
request maker. The agent is never an eligible approver. Recheck role and approval
status at admission; a missing authoritative status service fails closed.

Approve only the bound action digest and source/policy/grant/resource versions.
Approval expiry is at most 600 seconds after decision time; `now >= expires_at`
is expired. A rejection, withdrawal, relevant version change or role removal
invalidates approval and dependent permits. An approval must not override a hard
deny. Replayed decision IDs return their original result only for identical content;
changed content conflicts. Withdrawal is a new auditable decision with its own
idempotency key and does not erase the original approval.

## R05 - Canonical action and permit

The service stores an immutable `CanonicalIntent`. Hydrate all identity, scope,
source and resource fields from trusted services. Sort unique `fee_item_ids`
lexically, `source_refs` by system/tenant/record ID, and resource versions by resource
ID before finalizing. Bind the reviewed normalized representation; never mutate
that intent after approval. Hash its full RFC 8785 JCS UTF-8 representation with
SHA-256, encoded as `sha256:` plus lowercase hex. `PolicyRecord.digest` similarly
hashes only `PolicyDefinition`, which has no self-referential digest field.
The existing Python `ProposedAction.fingerprint()` is not this new digest profile.

The proposed permit is a compact JWS with protected `typ=sentinel-permit+jwt`,
`alg=ES256` and an allowlisted `kid`. The deployment must validate this profile
before acceptance. Do not accept `none`, untrusted embedded keys, arbitrary `jku`
URLs or symmetric/asymmetric algorithm substitution. Signing keys reside outside
the agent/executor; executors have verification keys only. Key revocation must
invalidate permits, including cached keys. Key rotation must preserve replay state.

Verify all `PermitClaims`: issuer, exact executor audience, workload subject,
tenant/environment, caller certificate binding, digest, unique jti, active policy,
grant revision/epoch and ancestors, source/resource versions and required approval.
Approval may be null only when policy permits that exact action without it.
Enforce `iat <= nbf <= now < exp`, `0 < exp - iat <= 60` seconds, and relevant
policy/grant validity. This pilot applies no expiry grace. Excess clock uncertainty
is an operational error that blocks issuance/admission. JWS and JSON Schema alone
do not enforce these comparisons or cryptographic checks.

GET status endpoints only retrieve stored results; they do not mint replacement
permits. An expired permit requires a new authorization request and fresh checks.
Whether a still-valid approval can be reused depends on an exact binding match;
by default create a new action review rather than silently rebinding it.

## R06 - Revocation and ordering

Revocation and execution admission share a serializable state transaction. An
authenticated revoke request compare-and-sets the expected epoch, durably advances
it and records evidence. The acknowledgment means later admissions cannot pass on
that target or a descendant. A disconnect is not acknowledgment.

At admission, check active versions/epochs, consume the unused jti, reserve all
applicable budgets, reserve the operation and fee-item uniqueness keys, and record
the dispatch intent/outbox atomically. A stale cache is insufficient. Pending
dispatches should be canceled when possible, but an already admitted or sent bank
request can still commit. Do not report a refund as reversed merely because the
grant was revoked. Stronger commit-time revocation requires bank-side transactional
fencing. Stop new actions and reconcile already-in-flight work.

## R07 - Idempotency and duplicate business effects

Transport idempotency is keyed by authenticated tenant, caller, method/path and
`Idempotency-Key`, bound to canonical request content. Identical repeats return the
original outcome; different content returns 409. A fresh transport key does not
reset consumed permits, business uniqueness or limits.

Derive the business operation key server-side as `refund:` plus lowercase SHA-256
hex of JCS `{tenant_id, account_ref, remedy_type, fee_item_ids}`, where remedy_type
is `BANK_PROCESSING_ERROR` and fee_item_ids are sorted and unique. The illustrative
human-readable key in structural examples is not a canonicalization test vector.
New request IDs, new permits and
worker restarts must not change it. Additionally enforce the per-fee-item unique
constraint from R01 to prevent overlapping sets or split requests. Preserve
idempotency/uniqueness records at least through the workflow's reconciliation and
business retention horizon, never just the permit's 60-second life.

Use the same stable business key at the bank API and a conditional write against
trusted resource versions. Distinguish an exact prior completed operation from
conflicting parameters. No live autonomous acceptance if the bank cannot enforce
equivalent conditional/idempotent behavior. There is no assumed distributed
transaction across Sentinel's database and an unrelated bank API.

## R08 - Protected execution boundary

Only a separate executor service owns bank write credentials and network access.
The agent cannot reach the bank API, edit policy/grants, read signing keys or
select a callback/URL. The server resolves the fixed action/tool mapping. Native
bank authorization remains in force; a Sentinel permit does not replace it.
Separate service identities are required for agent, GRC ingestion, policy
publication, delegation publication, approval backend, executor and evidence export.

## R09 - Failure and recovery

Missing required identity, source, approval, authority, journal or key state blocks
consequential execution. Bounded fallback means route to a human work queue; it
does not mean perform the original write under weaker checks.

Execution states: `RESERVED -> DISPATCHED -> SUCCEEDED | FAILED_CONFIRMED | UNKNOWN`.
`UNKNOWN -> RECONCILED` requires authoritative evidence of APPLIED with receipt or
NOT_APPLIED. An ambiguous timeout is UNKNOWN, not FAILED_CONFIRMED. Do not blindly
retry. Query by the stable business key; repeat a bank call only under proven
bank-side idempotency semantics. After recovery, preserve consumed jti values,
revocation epochs, budgets and business uniqueness. Restoring an older snapshot
alone cannot be accepted without reconciling newer ledger and bank state.

No automated break-glass mode. Emergency human action belongs to a separate named,
time-limited bank procedure with its own approval and evidence.

## R10 - Evidence and GRC return path

Record all decisions, approvals, revocations, admissions and outcomes; link source
record revision, policy/grant versions, human approval, permit, bank receipt and
correlation identifiers. Never export a reusable JWS or raw credentials. Minimize
account identifiers and sensitive business facts; apply retention/access controls.

Evidence is durably journaled before dispatch. Export through a durable outbox
with unique event IDs. The adapter acknowledges only after the GRC evidence
attachment is confirmed; queue acceptance alone is not GRC acknowledgment. Retry
with deduplication and report unresolved deliveries. An example pilot rule pauses
new writes after 300 seconds of unacknowledged evidence backlog.

`event_digest` hashes the JCS event with that field omitted; `previous_event_digest`
links within a tenant's ordered evidence stream. Hash chaining is not immutable
storage. Production needs separately administered retention, signatures/anchors,
sequence/gap detection, backup and restore testing. Corrections are new events,
not edits to historical approvals or decisions.

## API errors and role assignment

| Operation | Authorized service role |
|---|---|
| Policy candidate | GRC ingestion connector |
| Policy activation | Policy publisher with independently verified reviewer |
| Delegation candidate/activation | Separate authority administration roles |
| Action request/status | Registered agent; object ownership still checked |
| Approval submission | Trusted approval backend after human review |
| Execution/status | Bound agent to protected executor; executor dispatches bank call |
| Revocation | Authorized control/operations role, never agent self-service |
| Evidence delivery | Evidence exporter to separate GRC adapter |

400: malformed contract; 401: authentication invalid; 403: authority denied;
409: version/idempotency/replay conflict; 412: resource precondition changed;
503: required dependency unavailable. Pre-auth failures use `Error`; evaluated
domain decisions use `DecisionResponse`. An unknown identity may receive a DENY
with null policy/grant/digest to avoid disclosing records. Decision ALLOW and
REQUIRE_APPROVAL require resolved binding fields. A failed caller-authorization
check may use Error even at an endpoint whose normal domain response is a decision.

Do not interpret HTTP 2xx as bank success: inspect decision/execution state.
Approval submission can return HTTP 200 with DENY. Evidence delivery's HTTP 200
means GRC acknowledgment, not execution permission. A get-status result containing
an old permit is still subject to expiry and live authority validation.

## Standards references

- [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html)
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12)
- [RFC 8785, JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [RFC 7515, JSON Web Signature](https://www.rfc-editor.org/rfc/rfc7515.html)
- [RFC 8705, mutual TLS and certificate-bound tokens](https://www.rfc-editor.org/rfc/rfc8705.html)

These standards define selected representation/security mechanisms. They do not
validate Sentinel, the fictional policy, or regulatory compliance.
