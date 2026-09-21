# Framework alignment notes

These notes are implementation-oriented and are **not compliance claims**.

## NIST AI Risk Management Framework

The reference architecture supports concerns associated with GOVERN, MAP, MEASURE, and MANAGE by making authority, risk classification, approval, evidence, and measurable outcomes explicit.

The repository currently references **AI RMF 1.0** and the **NIST AI 600-1 Generative AI Profile**. NIST has stated that AI RMF 1.0 is under revision in 2026, so mappings should be versioned rather than treated as permanent.

Official reference: https://www.nist.gov/itl/ai-risk-management-framework

## MITRE ATLAS

ATLAS is a living knowledge base for adversarial behavior involving AI-enabled systems, including agentic AI.

Sentinel's reference controls are relevant to threat themes such as agent tool invocation, unauthorized capability use, poisoned context/tools, credential misuse, and harmful actions because the design narrows delegated tools and actions and requires a separate execution permit.

Official reference: https://atlas.mitre.org/

## OWASP Top 10 for Agentic Applications 2026

The OWASP agentic guidance emphasizes risks including goal hijacking, tool misuse, identity/privilege abuse, agentic supply-chain vulnerabilities, and unexpected code execution.

The reference repository addresses a subset of those concerns through explicit agent authority, approved tools, risk ceilings, protected execution, fail-closed behavior, and evidence traces.

Official reference: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

## Interpretation

Framework alignment should answer a narrow question: **which risk or governance concern is this implementation mechanism intended to address?**

It should not be used to imply certification, regulatory conformity, or complete control coverage.
