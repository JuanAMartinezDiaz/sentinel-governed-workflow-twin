# Sentinel AI workflow governance case study

Juan A. Martinez Diaz, MBA · Independent project work · Updated November 9, 2026

I developed Sentinel as a way to examine how an organization could give AI a useful role in a workflow while retaining authority over consequential actions. This public reference uses a fictional financial-services process to make governance decisions inspectable through workflow documentation, executable controls, tests, and records of what happened.

## The problem and my contribution

The example begins with a 17-step exception-handling process involving information retrieval, risk review, a proposed disposition, and an account change. An agent's ability to propose that change does not establish that it has permission to execute it. The governance problem is to define which work can be delegated, when human approval is required, and how a reviewer can reconstruct the decision and its outcome.

I conceived Sentinel, defined its governance model and validation approach, and directed prototype development. My work brings experience in technology operations and independent banking risk oversight to the design of agent permissions, approval gates, exception handling, and evidence requirements. The public implementation gives an employer or customer a way to examine those decisions alongside the code and tests.

## Decisions made in the reference design

The [workflow comparison](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/docs/workflow-before-after.md) keeps human decision review and approval before consequential state changes. The reference engine checks the agent's declared identity, delegated action, permitted tool, risk ceiling, confidence input, and approval state before issuing a permit bound to the proposed action. The protected executor rejects a direct call without a valid permit, while the evidence record distinguishes authorization from successful, blocked, or failed execution.

These choices are connected to selected NIST AI RMF 1.0 outcomes in a [control and test crosswalk](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/docs/framework-alignment.md). The mapping explains the contribution and remaining gap for each outcome; it does not claim that a technical control satisfies an organization's governance obligations.

## Evidence a reviewer can inspect

| Question | Evidence in the public reference |
| --- | --- |
| Is the work and the human decision path defined? | [Synthetic workflow](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/examples/synthetic_bank_workflow.json) and [workflow comparison](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/docs/workflow-before-after.md). |
| Does an unapproved high-risk action stop? | [Approval tests](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/tests/test_arbitration.py), including cases before and after simulated approval. |
| Can an action bypass authorization or change after approval? | [Gateway tests](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/tests/test_gateway.py) and [permit-binding test](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/tests/test_permit_binding.py). |
| Does the record explain what actually happened? | [Execution-evidence tests](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/tests/test_governed_evidence.py), covering blocked operations, failures, policy changes, and evidence-write failures. |
| What was verified, and against which revision? | [Dated verification](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/docs/verification-2026-11-09.md) and [GitHub test runs](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/actions/workflows/ci.yml). |

The [interactive reference](https://sentinel-reference-demo.vercel.app/) provides six fixed synthetic scenarios. A reviewer can compare an allowed read, an action awaiting approval, a bypass attempt, a fallback, and other declared outcomes, then inspect the tests supporting the behavior. The browser identifies whether it is connected to the reference engine or displaying an illustrative fallback.

## What this work establishes

The portfolio demonstrates my approach to workflow analysis, governance design, control specification, and evaluation of reference behavior. It also shows how I document unresolved limitations rather than treating an implemented control as proof of operating effectiveness. The code, test results, and design rationale provide material for a technical or governance interview and for a scoped discussion with a potential customer.

The examples are synthetic; approval is simulated, no live customer operation is performed, and the public API does not provide durable evidence storage or tenant isolation. Risk and confidence values are declared inputs. Illustrative time and cost figures are design assumptions, not measured customer savings, and the reference does not establish production readiness of the proprietary Sentinel product. Production adoption would require authenticated approval, deployment-specific security and isolation, retained evidence, operational monitoring, and an accountable release decision under the [release-readiness framework](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/main/docs/release-readiness-framework.md).

[Explore the full project portfolio](https://github.com/JuanAMartinezDiaz/JuanAMartinezDiaz/blob/main/PROJECTS.md) · [Inspect the source](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin) · [View my professional background](https://www.linkedin.com/in/juan-martinez-diaz-50943411/)
