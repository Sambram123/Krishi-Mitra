# Non-Functional Requirements (NON_FUNCTIONAL_REQUIREMENTS)

## 1. Latency & Real-Time Responsiveness
* **NFR-PERF-01 (Rule Engine Execution Time)**: Deterministic evaluation of all 5 schemes against the `FarmerProfile` must execute in $< 15\text{ ms}$ ($P_{99}$).
* **NFR-PERF-02 (Phase 1 Text Turn Latency)**: End-to-end response time for text interaction (Slot extraction + Rule evaluation + Kannada response generation) must Achieve Time-to-First-Token (TTFT) $< 900\text{ ms}$ and full completion $< 2.2\text{ s}$.
* **NFR-PERF-03 (Phase 2 Voice-to-Voice Latency)**: Time from end-of-speech (VAD trigger) to first audio byte played back to the farmer must target $< 1.8\text{ s}$ ($P_{50}$) and $< 2.8\text{ s}$ ($P_{95}$) via sentence-level TTS streaming.

## 2. Determinism, Auditability & Safety
* **NFR-SAFE-01 (Zero Hallucinated Rules)**: The system must have a $0\%$ hallucination rate on eligibility criteria, subsidy amounts, and required documents. All factual numbers and document lists are injected directly from the versioned JSON scheme catalog.
* **NFR-SAFE-02 (Synthetic Scheme Guardrail)**: Every synthetic scheme (`DEMO_MICRO_IRRIGATION`, `DEMO_AGRI_EQUIPMENT`, `DEMO_SOIL_IMPROVEMENT`) must carry an immutable `is_synthetic: true` flag that forces both the UI and spoken response layer to indicate it is a demonstration scheme.
* **NFR-SAFE-03 (Privacy & Ephemeral PII)**: No sensitive government ID numbers (such as Aadhaar numbers or bank account numbers) shall ever be requested or stored by the assistant. If a farmer speaks a 12-digit number, it must be masked (`XXXX-XXXX-XXXX`) in logs.

## 3. Usability & Spoken Ergonomics
* **NFR-UX-01 (Cognitive Load Limit)**: Spoken turns must not exceed $45\text{ words}$ (approx. $15\text{--}20\text{ seconds}$ of speech) unless the farmer specifically requests a detailed step-by-step document readout.
* **NFR-UX-02 (Low-Literacy Visual Support)**: The companion visual interface must use recognizable iconography (crops, water droplets, tractor, shield, soil leaf) and color-coded status badges (`Green = Eligible`, `Amber = Needs Info`, `Grey/Red = Not Eligible`).