# Requirements

> Extracted from the three manifest-typed PRDs: `prd.md` (precedence 1), `.gsd/REQUIREMENTS.md` (precedence 2), `requirements.md` (precedence 2).
> **Note:** `requirements.md` contains no user stories or acceptance criteria — it is a technical contract (dependency manifests, TypeScript schemas, failure-mode table). Its content is preserved in `constraints.md`; see INGEST-CONFLICTS.md INFO.

## REQ-progressive-3-stage-delivery
- source: prd.md (§1.1)
- description: Development is structured into three progressive prototypes. Stage 1 Text-to-Text Prototype: Kannada text input, dialect & jargon slot extraction (Gemini Flash free tier / local LLM), deterministic evaluation over 5 reference schemes, auditable text recommendations and follow-up questions. Stage 2 Voice Output Prototype: text in → dialogue logic → spoken Kannada voice out, natural rural cadence tuning (Edge-TTS / Sarvam Bulbul), brevity constraint (<25 words per spoken turn). Stage 3 Full Voice AI Application: spoken Kannada in (Sarvam Saaras / Groq Whisper v3), bimodal high-contrast web UI (audio visualizer + live cards), full sub-2-second conversational turn-taking loop.
- acceptance: Three stages delivered in the stated order, each runnable as its described artifact (text CLI → text-in/voice-out → full voice-in/voice-out with UI).
- scope: delivery model; Stages 1–3

## REQ-benchmark-dataset-5-schemes
- source: prd.md (§2)
- description: The system is tested against a hybrid benchmark dataset of 2 Real schemes and 3 Synthetic/Fictional schemes: PM-KISAN (real; ₹6,000/yr income support, strict official exclusions — institutional landholders, income-tax payees, constitutional posts — and mandatory documents RTC/Pahani + Aadhaar-NPCI seeded bank account); PMFBY (real; crop insurance for notified crops Ragi, Togari, Jola, Paddy, Cotton across Kharif/Rabi against weather calamities); Demo Micro-Irrigation Support (fictional; drip & sprinkler subsidy 70% general / 90% small-marginal, tests water source availability and historical subsidy cooldown); Demo Agricultural Equipment Assistance (fictional; mechanization subsidy for power tillers, rotavators, small tractors, capped at ₹1,00,000 / 50%); Demo Soil Improvement Support (fictional; soil health incentive ₹5,000/ha based on Soil Health Card deficiency indicators).
- acceptance: All five schemes are modeled and evaluable, with the 2-real / 3-synthetic split preserved.
- scope: reference dataset; scheme catalog

## REQ-demo-scheme-transparency-badge
- source: prd.md (§2, Transparency Guardrail)
- description: The application displays a distinct `[DEMO / TEST CASE]` badge alongside synthetic schemes to prevent real-world misinformation.
- acceptance: A `[DEMO / TEST CASE]` badge appears in output for every synthetic scheme mention.
- scope: transparency guardrail; synthetic-scheme presentation

## REQ-free-tooling-blueprint
- source: prd.md (§3)
- description: Milestone 1 — Python 3.10+, Google Gemini 2.5 Flash via free API tier (15 RPM / 1M TPM) or local Ollama (Llama 3.2 / Qwen 2.5), pure Python deterministic rule engine, interactive Terminal CLI + JSON test harness. Milestone 2 — Edge-TTS (`kn-IN-GaganNeural`, `kn-IN-SapnaNeural`; zero API keys, zero cost) or Sarvam AI Bulbul (hackathon free-tier credits). Milestone 3 — Groq Cloud Whisper-large-v3 (sub-300ms, free tier, Kannada agricultural prompt conditioning) or Sarvam AI Saaras (code-mixed Kannada); frontend React + Vite + TailwindCSS with Web Audio API.
- acceptance: The described toolchain is used at each milestone without requiring paid tiers.
- scope: technology stack; free/open-source tooling

## REQ-stage1-success
- source: prd.md (§4.1)
- description: Text input such as "ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?" correctly outputs eligibility for `Demo Micro-Irrigation Support` and `PM-KISAN` with audit trail and document list.
- acceptance: For that input, both schemes are returned eligible with audit trail and required-document list.
- scope: Stage 1 acceptance

## REQ-stage2-success
- source: prd.md (§4.2)
- description: The recommendation is converted into natural, warm, spoken Kannada audio in under 500ms, strictly limited to 2-3 clear sentences.
- acceptance: Audio produced in < 500ms and ≤ 2-3 sentences.
- scope: Stage 2 acceptance

## REQ-stage3-success
- source: prd.md (§4.3)
- description: A user speaks into the browser microphone; the system transcribes live, computes eligibility, plays spoken audio, and updates interactive scheme cards in < 2.0 seconds.
- acceptance: End-to-end voice-in → cards-updated loop measured under 2.0 seconds.
- scope: Stage 3 acceptance

## REQ-01-voice-streaming-pipeline
- source: .gsd/REQUIREMENTS.md (REQ-01, status Pending, traces to SPEC Goal 1)
- description: Low-Latency Kannada Voice Streaming Pipeline — audio capture with Web VAD, low-bitrate streaming, and <2.0s roundtrip response.
- acceptance: Roundtrip response under 2.0 seconds.
- scope: voice streaming pipeline

## REQ-02-dialect-jargon-normalizer
- source: .gsd/REQUIREMENTS.md (REQ-02, status Pending, traces to SPEC Goal 2)
- description: Kannada Dialect & Agricultural Jargon Normalizer — entity extraction module resolving North Karnataka / Mysore dialects, local crop terms, and land units.
- acceptance: Not stated in source (traceability matrix lists no acceptance criteria; Source column references SPEC Goal 2).
- scope: dialect normalization; entity extraction

## REQ-03-multi-turn-slot-filling
- source: .gsd/REQUIREMENTS.md (REQ-03, status Pending, traces to SPEC Goals 1, 2)
- description: Multi-Turn Slot-Filling Dialogue Manager — context-retaining conversational engine that proactively inquires for missing profile fields.
- acceptance: Not stated in source (Source column references SPEC Goals 1, 2).
- scope: dialogue management

## REQ-04-deterministic-rule-engine
- source: .gsd/REQUIREMENTS.md (REQ-04, status Pending, traces to SPEC Goal 3)
- description: Deterministic Scheme Eligibility Rule Engine — pure Python evaluator checking explicit criteria for Raitha Siri, Krishi Bhagya, PM-KISAN, PMFBY, Surya Raitha, and KCC.
- acceptance: Not stated in source (Source column references SPEC Goal 3).
- scope: eligibility rule engine; scheme set (see INGEST-CONFLICTS.md WARNING — 6 schemes here vs 5-scheme benchmark dataset elsewhere)

## REQ-05-kannada-tts
- source: .gsd/REQUIREMENTS.md (REQ-05, status Pending, traces to SPEC Goal 1)
- description: Natural Kannada Spoken Synthesis (TTS) — expressive, concise audio response generation (<25 words per turn) delivered in warm rural tone.
- acceptance: <25 words per turn; warm rural tone.
- scope: TTS; spoken response generation

## REQ-06-bimodal-web-ui
- source: .gsd/REQUIREMENTS.md (REQ-06, status Pending, traces to SPEC Goal 4)
- description: Bimodal Accessible Web UI — high-contrast visual dashboard featuring audio visualizer, live transcript, scheme cards, and document checklists.
- acceptance: Not stated in source (Source column references SPEC Goal 4).
- scope: web UI; accessibility

## REQ-07-auditable-reasoning-drawer
- source: .gsd/REQUIREMENTS.md (REQ-07, status Pending, traces to SPEC Goal 3)
- description: Auditable Reasoning & Verification Drawer — interactive breakdown displaying the exact government gazette rules validated for each scheme.
- acceptance: Not stated in source (Source column references SPEC Goal 3).
- scope: auditability; reasoning display
