# Using Hugging Face to Support Sentinel Model Evaluation

Juan A. Martinez Diaz, MBA | Independent model research | Prepared November 12, 2026

I built Sentinel to make agent authority, approval requirements, and execution evidence explicit and testable. Alongside that work, I use Hugging Face to source models for local experimentation. A September 21, 2026 comparison illustrates how I connect model results to a development decision: the candidate with more exact matches also produced more safety-significant misses under the lab rubric, so the assessment recommended further evaluation rather than promotion to autonomous governance use.

## Purpose and scope

The experiment examined whether two candidate models could produce the expected governance decisions for synthetic workflow cases. The requested JSON contained disposition, autonomy, human approval, and gap code. The work ran locally and used synthetic data. It was separate from Sentinel's public reference, which demonstrates deterministic controls with fixed scenarios and has no language-model integration. [1]

My contribution connects technology risk experience with model acquisition, evaluation design, review of failure patterns, and documented advancement criteria. The results below are stored experiment records from September 21. Their contents were inspected and the counts recomputed on November 12; that review did not rerun inference.

## Hugging Face and model provenance

The lab records identify Qwen as `nvidia/Qwen3.6-35B-A3B-NVFP4` and name vLLM as its runtime. Its Hugging Face cache contains snapshot `491c2f1ea524c639598bf8fa787a93fed5a6fbce`. The later preparation record identifies Nemotron as `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4` and records downloaded revision `16993199e436da4ba75ddc410855f87e0d996ee6`.

These records support model acquisition and local evaluation. They do not cryptographically bind every recorded response to a model snapshot. Hugging Face documents downloads by revision and model cards covering intended uses, limitations, training information, and reported results. Those capabilities support provenance and due diligence; the records examined here do not establish a completed license or model-card review. [2, 3]

## Method and recorded findings

Both result files contain the same 100 ordered case identifiers and expected answers. The stored harness defines a shared prompt and scorer. An exact match requires every expected value and no extra keys.

The rubric flags two safety-significant conditions: explicitly declining required human approval, or accepting a case that requires human review. This is a narrow test definition; it does not capture every possible unsafe behavior. Missing fields fail exact matching but are not automatically counted as safety-significant misses.

| Recorded result | Qwen | Nemotron Nano Omni |
| --- | ---: | ---: |
| Synthetic cases | 100 | 100 |
| Exact matches | 43 | 77 |
| Safety-significant misses under the lab rubric | 5 | 7 |
| Exact matches in the 20 holdout-labeled cases | 9 | 15 |
| Safety-significant misses in that subset | 0 | 2 |

The corpus labels 60 cases as training, 20 as validation, and 20 as holdout. The 100-case totals therefore are not held-out accuracy estimates. Independent sealing, absence of contamination, identical runtime conditions, and statistical generalizability have not been established. Neither result file contains an API-error row. These are local synthetic findings, not a general ranking of either model family.

## Decision and relevance to Sentinel

The dated decision memo retained Qwen as the research baseline and Nemotron as a challenger. It concluded that neither unmodified model was ready to act as an autonomous Sentinel governance reasoner. It called for investigation of failures, separate training and evaluation data, and zero safety-significant holdout misses before considering promotion. Qwen's zero misses in one small holdout-labeled subset did not establish overall readiness.

The work informed the next development step by exposing specific failure patterns and documenting the evidence required for further consideration. It did not establish production integration, customer savings, or complete safety assurance. Sentinel's deterministic authority controls have their own implementation and test evidence. [1]

NIST AI RMF MEASURE 2.1 addresses documentation of test sets, metrics, and evaluation tools; MEASURE 2.3 addresses evidence under conditions resembling deployment. This case illustrates a limited application of those ideas and identifies the work still required before a deployment decision. [4]

## Evidence record

The findings come from the stored `workflow-governance-100-v3` experiment: `results/qwen36-workflow-governance-100-v3.json`, `results/nemotron3nanoomni-workflow-governance-100-v3.json`, `cases/workflow-governance-100-v3.json`, `scripts/run_workflow_100_v3.py`, and `FINAL_BASELINE_COMPARISON_20260921.md`. Model provenance is recorded in `manifests/frozen-candidates.json` and `NEXT_STEPS_VERIFIED_20260921.md`.

The original lab files are retained separately. This case study presents a checked summary, not a public reproduction package. SHA-256 fingerprints recorded during the November 12 inspection are included below. They identify the files as inspected; they do not prove historical immutability.

## Sources

1. [Sentinel reference README at the reviewed revision](https://github.com/JuanAMartinezDiaz/sentinel-governed-workflow-twin/blob/db1450893942393418a35fd3147cd24ac806c70a/README.md).
2. [Hugging Face download and revision documentation](https://huggingface.co/docs/huggingface_hub/en/guides/download).
3. [Hugging Face model-card documentation](https://huggingface.co/docs/hub/en/model-cards).
4. [NIST AI RMF 1.0 Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/).

## Source file fingerprints

Qwen results: `aa2120ec2e5ac2e3f10f6cb2513125d66c2632dd6584335f1d39546019d2a3a4`

Nemotron results: `9a1b83a3f2b0757d788f8fef0bf2c364d7caededbfe8308e50c3f31fceca6972`

Corpus: `0afeb8e03b87d8c2736a5a116aff614e5723f8cf096e4e2dea4adc4c9cb8bc5b`

Scoring harness: `7a3cfb023114cf3d0fef09df436b7352d4aea35fcce423596437ad7af408ecf8`

Decision memo: `b047cec9cf48f69bea3bdfb826d18827115e4a6233417826453858db303df9c6`
