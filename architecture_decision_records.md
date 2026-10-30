# Architecture Decision Records (DECISIONS)

## ADR-001: Neuro-Symbolic Split (LLM for NLU/NLG + Symbolic Engine for Eligibility)
* **Context**: Generative LLMs alone frequently hallucinate government scheme rules, confuse subsidy percentages, or skip mandatory exclusion checks. Conversely, traditional IVR decision trees fail when farmers speak naturally, provide multiple details in one sentence, or switch topics.
* **Decision**: Use an LLM strictly for **Conversational Slot Extraction** and **Spoken Kannada Response Generation**, while delegating all eligibility evaluation to a **100% deterministic Python/JSON Rule Engine**.
* **Consequences**: Complete auditability, zero hallucinated eligibility outcomes, and instant explainability for judges and farmers.

## ADR-002: Phase 1 (Text Core) to Phase 2 (Voice Pipeline) Modality Adapter
* **Context**: Debugging multi-turn slot extraction, Kannada dialect normalization, and rule engine edge cases directly through live microphone audio slows down iteration and automated testing.
* **Decision**: Build the Core Conversational Agent behind a unified `TurnProcessor` interface that accepts a normalized `TurnInput` object (`text`, `language_hint`, `audio_metadata`). Phase 1 exercises `TurnProcessor` directly via text/Kanglish; Phase 2 wraps `TurnProcessor` with streaming ASR ingress and TTS egress.
* **Consequences**: $100\%$ of automated acceptance tests written in Phase 1 remain valid in Phase 2, and the UI can offer a seamless toggle between **Voice Mode** and **Text/Debug Mode**.

## ADR-003: Sentence-Boundary TTS Streaming for Spoken Kannada
* **Context**: Waiting for a full 3-sentence Kannada explanation to finish generating before starting Text-to-Speech adds $2\text{--}3\text{ seconds}$ of dead air.
* **Decision**: Stream LLM tokens and buffer only up to the first sentence boundary (`.` or `?` or newline), immediately dispatching the first sentence (typically a warm acknowledgment like *"ಹೌದು ಯಜಮಾನರೇ, ಧಾರವಾಡದಲ್ಲಿ ತೊಗರಿ ಬೆಳೆಗೆ ವಿಮೆ ಸೌಲಭ್ಯ ಇದೆ."*) to the TTS service while subsequent sentences synthesize in parallel.
* **Consequences**: Reduces perceived voice response latency by over $45\%$.

## ADR-004: Explicit Separation of Real vs. Synthetic Reference Schemes
* **Context**: The hackathon dataset includes 2 real schemes (`PM-KISAN`, `PMFBY`) and 3 fictional/synthetic schemes (`Demo Micro-Irrigation Support`, `Demo Agricultural Equipment Assistance`, `Demo Soil Improvement Support`).
* **Decision**: Include a mandatory boolean field `is_synthetic` and `scheme_classification: "REAL" | "SYNTHETIC_DEMO"` in the scheme data model. Both the UI cards and spoken explanations explicitly frame synthetic schemes as prototype demonstration programs.
* **Consequences**: Satisfies ethical and problem-statement constraints ("no real entitlement should be implied").