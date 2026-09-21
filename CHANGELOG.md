# Changelog

## 0.2.1 — 2026-09-21

Decision X-Ray rendering correction.

- Removed recursive fallback screenshot from beneath the live WebGL canvas
- Made the WebGL renderer opaque to prevent text and controls bleeding through the 3D chamber
- Replaced the public preview with a clean render
- Added a regression test for the rendering boundary

## 0.2.0 — 2026-09-21

Decision X-Ray 2.0 public experience.

- Replaced the legacy static hero with a live Three.js governance chamber
- Added animated proposal, authorization gate, human authority, execution permit, protected execution, and evidence stages
- Added scenario-driven ALLOW, REQUIRE_APPROVAL, FALLBACK, and BYPASS/BLOCKED states
- Added live decision trace and scenario explanation panel
- Added responsive desktop/mobile behavior
- Added public render-integrity test for the Decision X-Ray 2.0 entry point

## 0.1.0 — 2026-09-21

Initial public reference release.

- Authority registry
- Deterministic decision arbitration
- Protected execution permits
- Structured evidence ledger
- Workflow outcome metrics
- Synthetic 17-step financial-services workflow
- Reference governance tests
- GitHub Actions CI
