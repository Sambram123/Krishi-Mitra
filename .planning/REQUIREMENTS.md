# Requirements: Krishi Mitra

**Defined:** 2026-10-30
**Core Value:** Every eligibility answer is produced by the deterministic rule engine and can be traced to a written rule — the LLM only listens and speaks, it never decides.

## v1 Requirements

Requirements for the hackathon milestone (v1.0). Each maps to exactly one roadmap phase.

### Reference Dataset

- [ ] **DATA-01**: Exactly five schemes are modeled in `data/schemes_dataset.json` — PM-KISAN and PMFBY as `real`; Demo Micro-Irrigation Support, Demo Agricultural Equipment Assistance and Demo Soil Improvement Support as `synthetic_demo` — each with eligibility rules, official exclusions, required documents, Kannada metadata and application channels, with `schemes_knowledge_base.md` §1 as the only rule source (RESOLVED-W1/W2). *Acceptance: a loader test asserts `len(schemes) == 5` and the 2-real / 3-synthetic split.*
- [ ] **DATA-02**: Every synthetic scheme carries a `[DEMO / TEST CASE]` marker emitted by the engine alongside its result, so any surface that shows the scheme shows the marker. *Acceptance: no synthetic-scheme result can be produced without the marker field set.*

### Deterministic Rule Engine

- [ ] **ENG-01**: A pure-Python evaluator in `backend/rules_engine.py` returns `ELIGIBLE` / `CONDITIONALLY_ELIGIBLE` / `INELIGIBLE` for all five schemes from a `FarmerProfile`, with an audit trail (rule evaluated, criteria matched, criteria failed, gazette reference), mandatory/optional required documents and application channels — with no LLM call and no network access in the decision path. *Acceptance: the same profile evaluated twice returns identical JSON; the suite runs offline with no API key.*

### Kannada NLU & Dialogue

- [ ] **NLU-01**: Rural Kannada speech/text is normalized to canonical values before evaluation — North Karnataka (`-aitri`) and Old Mysore (`-kanri`) forms, crop colloquia (Togari → Pigeon Pea, Kabbu → Sugarcane, Jola → Sorghum/Jowar, Ragi), and land units (Gunta → acres at 0.025, hectare → acres at 2.471, computed in Python, never by the model). *Acceptance: "20 ಗುಂಟೆ" evaluates as 0.5 acre and a Togari crop matches PMFBY's Pigeon Pea.*
- [ ] **NLU-02**: A multi-turn dialogue manager keeps session state, asks one proactive Kannada follow-up per missing required field (land size, crops, irrigation, district), and confirms inferred or conflicting values before they reach the engine — `None` never overwrites a confirmed value. *Acceptance: a message with land size only produces a spoken-Kannada crops question, and the engine runs only after the profile is complete.*
- [ ] **NLU-03**: Guardrails hold end to end — an extraction containing any eligibility/benefit/document key is blocked, stripped and logged; an asserted slot with no transcript evidence is downgraded to *inferred*; land sizes outside [0.01, 100] acres or unit/value contradictions are re-asked; conflicting scalars are quarantined; Aadhaar-like and bank-account-like 12-digit patterns are redacted from logs and traces; no reply states a payout figure. *Acceptance: negative tests for each guardrail pass, including a PMFBY crop-loss reply that names eligibility and documents but no rupee amount.*

### Stage 1 — Text-to-Text CLI

- [ ] **CLI-01**: Typing the benchmark sentence `ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?` into `cli_chat_prototype.py` returns Demo Micro-Irrigation Support and PM-KISAN as eligible, with their audit trails and document lists. *Acceptance: that exact input produces that exact eligible set, and nothing else marked ELIGIBLE.*

### Voice Output (Stage 2)

- [ ] **TTS-01**: Recommendations are synthesized as natural, warm rural Kannada audio with a free provider (Edge-TTS `kn-IN-GaganNeural` / `kn-IN-SapnaNeural` as default; Sarvam Bulbul optional), degrading to pre-rendered Kannada templates if synthesis fails.
- [ ] **TTS-02**: Stage 2 acceptance — the recommendation is spoken in under 500 ms from text-ready to first audio, in ≤2–3 sentences, with a hard formatter cap of 25 words / 2 sentences (target 15–20) and no payout figure. *Acceptance: an over-long or payout-bearing reply is rejected by the formatter and the test suite fails.*

### Voice Input (Stage 3)

- [ ] **VOI-01**: Browser voice capture with VAD and streaming Kannada ASR completes a conversational turn in under 2.0 s — 900 ms of continuous silence auto-submits, utterances are capped at 30 s, and capture is 16 kHz mono downsampled from client 44.1 kHz. *Acceptance: three consecutive spoken turns each return under 2.0 s.*

### Bimodal Web UI

- [ ] **UI-01**: A high-contrast web UI shows an audio visualizer, live Kannada transcript in Kannada script, scheme cards with status colours (Eligible = green, Under Review = yellow, Ineligible = muted), document checklists, and a `[Real]` vs `[DEMO / TEST CASE]` distinction; starting to speak interrupts playback immediately (barge-in). *Acceptance: cards update in the same turn as the spoken reply, and speaking over audio stops it.*
- [ ] **UI-02**: An auditable reasoning drawer expands per scheme to show the exact rules evaluated, the criteria matched and failed, and the gazette reference. *Acceptance: every card's "why you qualify" points match the engine's audit trail verbatim.*

### Application & Delivery

- [ ] **APP-01**: Stage 3 acceptance — a farmer speaks into the browser mic, and live transcription, eligibility computation, spoken audio and updated scheme cards all complete in under 2.0 s.
- [ ] **PLAT-01**: The three stages exist in their stated order and each remains runnable from the repo: Stage 1 text CLI → Stage 2 text-in/voice-out → Stage 3 voice-in/voice-out web app. *Acceptance: all three launch from one checkout during rehearsal.*
- [ ] **PLAT-02**: The whole stack runs on free tooling — Gemini 2.5 Flash free tier or local Ollama, Edge-TTS, Groq Whisper or Sarvam free credits, open-source frontend — with no paid tier anywhere and no API key required for Stage 1 tests or Stage 2 audio. *Acceptance: Stage 1 test suite and Stage 2 playback both succeed with no keys configured.*

## v2 Requirements

None defined. Deferred scope is tracked in Out of Scope below; adding it back requires a roadmap update.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Raitha Siri, Krishi Bhagya, Surya Raitha (PM-KUSUM), KCC | No rule data (eligibility rules, benefits, exclusions, documents) exists; the 5-scheme benchmark is authoritative (RESOLVED-W1) |
| Payout or compensation figures in any reply (e.g. PMFBY ₹15,000/ha) | Amounts depend on external state; promising one is misinformation and a Critical eval failure (RESOLVED-W3) |
| Write-backs to live government databases | Hackathon non-goal; read-only decision support |
| Languages other than Kannada / code-mixed Kannada-English; states other than Karnataka | Hackathon non-goal |
| Computer-vision pest diagnostics | Hackathon non-goal |
| Paid model tiers; OpenAI/Anthropic paths; ADK, LangChain, LangGraph, LlamaIndex, Haystack, AutoGen/AG2, CrewAI | Free and open tooling only; SPEC rules these frameworks out |
| User accounts, auth, long-term profile retention | In-process session state only, per DPDP data minimisation |

## Provenance

Requirement IDs above are normalized for roadmap use. Original intel IDs (`.planning/intel/requirements.md`):

| Normalized | Intel ID / source |
|-----------|-------------------|
| DATA-01 | `REQ-benchmark-dataset-5-schemes` (prd.md §2) |
| DATA-02 | `REQ-demo-scheme-transparency-badge` (prd.md §2) |
| ENG-01 | `REQ-04-deterministic-rule-engine` (.gsd/REQUIREMENTS.md) — **corrected**: the 6-scheme list is replaced by the 5 benchmark schemes per RESOLVED-W1 |
| NLU-01 | `REQ-02-dialect-jargon-normalizer` (.gsd/REQUIREMENTS.md) |
| NLU-02 | `REQ-03-multi-turn-slot-filling` (.gsd/REQUIREMENTS.md) |
| NLU-03 | New — derived from 02-AI-SPEC §6 guardrails + RESOLVED-W3 (no prior REQ-ID existed) |
| CLI-01 | `REQ-stage1-success` (prd.md §4.1) |
| TTS-01 | `REQ-05-kannada-tts` (.gsd/REQUIREMENTS.md) |
| TTS-02 | `REQ-stage2-success` (prd.md §4.2) |
| VOI-01 | `REQ-01-voice-streaming-pipeline` (.gsd/REQUIREMENTS.md) + requirements.md §1.1 acoustics |
| UI-01 | `REQ-06-bimodal-web-ui` (.gsd/REQUIREMENTS.md) |
| UI-02 | `REQ-07-auditable-reasoning-drawer` (.gsd/REQUIREMENTS.md) |
| APP-01 | `REQ-stage3-success` (prd.md §4.3) |
| PLAT-01 | `REQ-progressive-3-stage-delivery` (prd.md §1.1) |
| PLAT-02 | `REQ-free-tooling-blueprint` (prd.md §3) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| ENG-01 | Phase 1 | Pending |
| NLU-01 | Phase 2 | Pending |
| NLU-02 | Phase 2 | Pending |
| NLU-03 | Phase 2 | Pending |
| CLI-01 | Phase 2 | Pending |
| PLAT-02 | Phase 2 | Pending |
| TTS-01 | Phase 3 | Pending |
| TTS-02 | Phase 3 | Pending |
| VOI-01 | Phase 4 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-02 | Phase 4 | Pending |
| APP-01 | Phase 4 | Pending |
| PLAT-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-30*
*Last updated: 2026-10-30 after initialization from doc ingest*
