# Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)

> **A Voice-First, Auditable Kannada AI Assistant for Discovering & Verifying Agricultural Government Schemes**

## 1. Overview

**Krishi Mitra** bridges the last-mile information gap between farmers in Karnataka and Central/State government agricultural welfare schemes. Instead of forcing farmers to navigate fragmented web portals or fill out rigid forms in formal literary Kannada or English, Krishi Mitra engages farmers in natural, colloquial spoken Kannada—handling regional accents, code-mixed English phrases, local crop names, and traditional land units—while using a **100% deterministic, auditable rule engine** to evaluate scheme eligibility.

### Core Innovation
The core innovation of Krishi Mitra is **Conversational Voice-First Slot Elicitation paired with Symbolic Rule Verification**:
1. **Spoken-Style Dialogue Management**: Responses are crafted specifically for the ear (short, conversational, rhythmic Kannada sentences with natural discourse markers) rather than reading out long markdown bullet lists.
2. **Dialect & Agricultural Entity Normalization**: Converts regional terms (e.g., *Mungaru* $\rightarrow$ `KHARIF`, *20 Gunte* $\rightarrow$ `$0.5\text{ Acres}$`, *Togari* $\rightarrow$ `PIGEON_PEA`) before rule evaluation.
3. **Zero-Hallucination Eligibility Layer**: The LLM never decides eligibility on its own. It extracts structured agricultural slots and passes them to a deterministic JSON Rule Engine that outputs a verifiable audit trail (`ELIGIBLE`, `INELIGIBLE`, or `MISSING_INFO`).

---

## 2. Phased Engineering Strategy

We are building Krishi Mitra using a **Core-First, Modality-Layered** approach:

* **Phase 1: Core Conversational Agent + Auditable Rule Engine (Text & Transliterated Kannada Interaction)**
  * Build and validate the multi-turn conversation state machine, entity normalization layer, slot-filling dialogue manager, and deterministic eligibility engine.
  * Expose a text chat + simulated voice transcript workbench supporting Kannada script (`ಕನ್ನಡ`), Kanglish (Romanized Kannada), and code-mixed English.
* **Phase 2: Voice-First Streaming Pipeline Migration**
  * Wrap the Phase 1 Core Agent with a low-latency Speech-to-Speech pipeline: Voice Activity Detection (VAD), Kannada Automatic Speech Recognition (ASR), barge-in handling, and prosody-tuned Spoken Kannada Text-to-Speech (TTS).

---

## 3. Reference Scheme Dataset

Krishi Mitra evaluates five baseline schemes in the prototype (clearly distinguishing real statutory schemes from synthetic test schemes):

| Scheme ID | Scheme Name | Type | Core Purpose in Prototype |
| :--- | :--- | :--- | :--- |
| `PM_KISAN` | **PM-KISAN** | Real | Income assistance (`₹6,000/year`) for eligible landholding farmer families; verifies land ownership and institutional/tax exclusions. |
| `PMFBY` | **PMFBY (Pradhan Mantri Fasal Bima Yojana)** | Real | Crop insurance subject to crop, notified district/taluk, season (*Kharif*/*Rabi*/*Summer*), and loanee/non-loanee cut-off rules. |
| `DEMO_MICRO_IRRIGATION` | **Demo Micro-Irrigation Support** | Fictional / Synthetic | Synthetic test case for drip/sprinkler irrigation subsidy rules based on water-intensive/horticultural crops and landholding caps. |
| `DEMO_AGRI_EQUIPMENT` | **Demo Agricultural Equipment Assistance** | Fictional / Synthetic | Synthetic test case for farm mechanization/equipment subsidy decision rules (e.g., power tiller, sprayer, tractor implements). |
| `DEMO_SOIL_IMPROVEMENT` | **Demo Soil Improvement Support** | Fictional / Synthetic | Synthetic test case for soil health card, micronutrients, and green manure recommendation paths. |

---

## 4. Documentation Index

All project documentation is located in the repository and organized as follows:

1. **Product & Scope**
   * `PRD.md` — Product Requirements Document, user personas, and user journeys.
   * `SCOPE.md` — In-scope vs. out-of-scope boundaries for Phase 1 and Phase 2.
   * `REQUIREMENTS.md` — High-level business, linguistic, and regulatory transparency requirements.
   * `FUNCTIONAL_REQUIREMENTS.md` — Detailed functional specifications (`FR-01` to `FR-25`).
   * `NON_FUNCTIONAL_REQUIREMENTS.md` — Latency, reliability, determinism, and accessibility SLAs.
2. **Architecture & Engineering**
   * `ARCHITECTURE.md` — System architecture, Phase 1 to Phase 2 adapter pattern, and data flow.
   * `DECISIONS.md` — Architecture Decision Records (ADRs) justifying tech stack and design choices.
   * `FILE_STRUCTURE.md` — Monorepo directory layout for backend, frontend, rules, and voice pipeline.
   * `DATA_MODEL.md` — Domain models, slot schemas, unit normalization rules, and audit trace structures.
   * `DATABASE.md` — PostgreSQL + Redis persistence schema and session state storage.
   * `API_SPEC.md` — REST and WebSocket endpoints for text turns, audio streaming, and rule inspection.
   * `DOCUMENT_MANAGEMENT.md` — Management of scheme rule definitions and farmer KYC document checklists (RTC/Pahani, FRUITS ID, Aadhaar).
3. **Design & Experience**
   * `DESIGN_SYSTEM.md` — Visual identity, agrarian color palette, typography (Noto Sans Kannada), and accessibility tokens.
   * `UI_UX.md` — Voice-first human-computer interaction principles, prosody guidelines, and visual affordances.
   * `WEB_UX.md` — Responsive web application layout, developer audit drawer, and Phase 1/2 mode switcher.
4. **Execution, Testing & Operations**
   * `PLAN.md` — Step-by-step hackathon execution roadmap and milestone schedule.
   * `SETUP.md` — Local environment setup, environment variables, and seed scripts.
   * `PERFORMANCE.md` — Latency budgets, streaming chunk targets, and caching benchmarks.
   * `QUALITY_GATE.md` — Definition of Done, zero-hallucination checks, and CI gates.
   * `ACCEPTANCE_TESTS.md` — End-to-end test scenarios covering dialects, missing slots, exclusions, and context retention.
   * `DEPLOYMENT_AND_OPERATIONS.md` — Dockerized deployment, monitoring, and live hackathon demo runbook.