# Constraints

> Sources, in precedence order: `.gsd/SPEC.md` (SPEC, precedence 0), `.gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md` (SPEC, precedence 1), `architecture.md` (DOC, precedence 1), `requirements.md` (manifest PRD, precedence 2), `voice_interaction_design.md` (DOC, precedence 2). Locked ADR-001/ADR-002 constraints are recorded in `decisions.md` and restated here only where a source makes them concrete. `dataset_research.md` content is illustrative/non-binding and is recorded in `context.md`, not here.

## Zero-hallucination deterministic scheme evaluation
- source: .gsd/SPEC.md (Goals 1)
- type: nfr
- content: "100% Deterministic & Auditable Scheme Evaluation: Zero-hallucination rule engine for the 5 reference schemes." Eligibility must never be produced generatively.

## Voice loop latency ceiling of 2.0 seconds
- source: .gsd/SPEC.md (Goals 3, Success Criteria); .gsd/DECISIONS.md (ADR-002)
- type: nfr
- content: "Low-latency (<2.0s) full voice-in, voice-out web application." Spoken turns are capped at "<25 words per turn" and "under 25 words / 2 sentences" (ADR-002, locked).

## Rural Kannada dialect and agricultural jargon handling
- source: .gsd/SPEC.md (Goals 2)
- type: nfr
- content: "Accurately parse North Karnataka (*-aitri*) and Mysore (*-kanri*) dialects, crop colloquia (*Togari, Kabbu, Jola*), and land units (*Gunta* to Acre)."

## Free and open-source tooling only
- source: .gsd/SPEC.md (Goals 4)
- type: nfr
- content: "Leverage free tier and open tools (Gemini 2.5 Flash free tier, Edge-TTS, Groq Whisper) ensuring zero cost and infinite repeatability."

## Scope boundaries / non-goals (hackathon)
- source: .gsd/SPEC.md (Non-Goals)
- type: nfr
- content: Out of scope: direct transactional write-backs to live government databases; multi-state language expansion beyond Kannada / code-mixed Kannada-English; computer vision pest diagnostics.

## Reference dataset scope: 5 benchmark schemes, synthetic ones marked
- source: .gsd/SPEC.md (Reference Dataset Scope)
- type: schema
- content: Exactly five modeled schemes: (1) PM-KISAN (real) — direct income assistance for landholding farmer families with strict official exclusions (taxpayers, constitutional posts) and enrollment criteria; (2) PMFBY (real) — crop insurance covering notified crops (Ragi, Togari, Jola, Paddy) across Kharif/Rabi against weather calamities; (3) Demo Micro-Irrigation Support (fictional) — drip & sprinkler subsidy logic (70-90% for small/marginal farmers with water sources); (4) Demo Agricultural Equipment Assistance (fictional) — mechanization subsidy (power tiller, rotavator, tractor); (5) Demo Soil Improvement Support (fictional) — soil fertility enhancement based on Soil Health Card deficiencies. Fictional schemes are explicitly marked with a demonstration badge.

## NLU framework: google-genai + Pydantic v2 with Ollama fallback
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§2)
- type: nfr
- content: Selected framework: Google Gen AI SDK (`google-genai`, official Gemini Python SDK) + Pydantic v2 for schema-constrained output, with a thin provider adapter for an Ollama local fallback. Versions: `google-genai>=1.0,<2.0` (pin exact at implementation time), `pydantic>=2.6,<3`, `python-dotenv>=1.0`. Local fallback: Ollama `qwen2.5:7b-instruct` (primary fallback) / `llama3.2:3b` (low-RAM fallback). Provider selected by `NLU_PROVIDER=gemini|ollama` env var at startup with runtime failover to Ollama on repeated 429/5xx/empty responses. Ruled out: Google ADK, LangChain, LlamaIndex, LangGraph, CrewAI, OpenAI Agents SDK, Anthropic Agent SDK, Haystack, AutoGen/AG2.

## LLM scope boundary: perceives and phrases, never decides
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (scope boundary; §4 Core Pattern)
- type: nfr
- content: "The LLM *perceives and phrases*. It never decides eligibility. All eligibility, benefit amounts, exclusions, and document requirements are produced by `backend/rules_engine.py` (Phase 1)." Per turn the LLM appears twice (extract, phrase) and never in the decision path; if the phrasing call fails, fall back to a template reply built from the engine output.

## Extraction wire schema (ExtractOut / LandSize)
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§3 Entry Point Pattern; §4b)
- type: schema
- content: `LandSize { value: float, unit: Literal["acre","gunta","hectare"] }` — `normalized_acres` is computed in Python, NOT by the model. `ExtractOut { dialect_region?: "North_Karnataka"|"Old_Mysore"|"Coastal"|"General", district?: str, land_size?: LandSize, ownership_type: "Owner"|"Tenant"|"Joint Family"|"Unknown" (default "Unknown"), crops_local: list[str] (default [], max 10), irrigation_source?: "Rainfed"|"Borewell"|"Canal"|"Open Well"|"None", assistance_intent?: "scheme_discovery"|"crop_loss_compensation"|"solar_pump"|"loan_waiver"|"fertilizer_seed_subsidy"|"general_inquiry" }`. Rules: `extra="forbid"`, enums instead of free strings, no derived fields, `None` means "not stated"; a second validation failure yields an empty extraction (never a guess) plus a clarification reply.

## Model configuration per turn
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§4)
- type: nfr
- content: Extraction: `gemini-2.5-flash`, `temperature=0.1`, `top_p=0.95`, `max_output_tokens=1024`, `response_mime_type="application/json"`, `response_schema=ExtractOut`. Reply phrasing: same model, `temperature=0.5`, `max_output_tokens=256`, free text constrained by system rules (≤ 25 words, no eligibility claims). Local fallback: Ollama `qwen2.5:7b-instruct`, `temperature=0.0`, JSON mode via prompt + post-validation. Free tier is 15 RPM / 1M TPM; serialize per session, exponential backoff with jitter. Extraction p95 target ≤ 900 ms (Gemini); local fallback p95 ≤ 3 s.

## ConversationState model and merge policy
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§4 State Management)
- type: schema
- content: `ConversationState` is a Pydantic model held in an in-process `dict[session_id, ConversationState]` (Phase 2 CLI), holding `confirmed_profile`, `inferred_slots` (low-confidence, require confirmation), `turn_history` (last 6 turns), `schema_version`. Merge policy: scalars are last-write-wins only when the new value is evidence-backed and non-conflicting; a conflicting scalar is quarantined and triggers a clarification question; `crops` is a set union; `None` never overwrites a confirmed value. State is JSON-serializable for Phase 4 persistence. Context sent to the extractor: current utterance + confirmed profile + unresolved slot list only; never the scheme catalog.

## Online guardrails
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§6)
- type: nfr
- content: (1) Eligibility firewall — NLU JSON containing any eligibility/benefit/document key is blocked, stripped, re-run, and logged. (2) Evidence check — asserted slot with no fuzzy transcript match is downgraded to `inferred` and confirmed before the rule engine. (3) Unit sanity — acres outside [0.01, 100] or unit/value contradiction is flagged and re-asked, never passed to the engine. (4) Conflict guard — conflicting scalar is quarantined with a disambiguating question. (5) Demo transparency — `[DEMO / TEST CASE]` disclaimer injected when a synthetic scheme appears without a marker. (6) PII redaction — 12-digit Aadhaar-like or bank-account-like patterns redacted before logging/tracing, never persisted. (7) Safety/empty-response — `finish_reason != STOP` or empty text → retry once, then local fallback, then template reply.

## Evaluation strategy and tooling
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§5)
- type: nfr
- content: Primary tooling: Promptfoo (CLI, CI/CD, custom assertions over JSON) + pytest for deterministic unit checks + Pydantic validators. Tracing default: Arize Phoenix (local/self-hosted via OpenInference); override to Langfuse only by explicit team decision. CI: `pytest backend/tests -q` then `npx promptfoo@latest eval -c promptfooconfig.yaml --no-cache -o eval-results.json`; fail the job when any Critical dimension regresses. Critical dimensions include slot extraction accuracy, land-unit normalization, crop canonicalization, missing-slot detection, hallucinated slots, demo transparency, E2E routing fidelity. Reference dataset: 40 gold examples (10 North Karnataka, 10 Old Mysore/Mandya/Hassan, 10 code-mixed, 5 unit traps, 5 multi-turn missing-slot), row shape `{id, transcript_history[], gold_profile, gold_missing_slots, gold_eligibility_set, dialect_slice, notes}`.

## Regulatory / compliance constraints (DPDP 2023, Aadhaar Act)
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§1b Regulatory / Compliance Context)
- type: nfr
- content: DPDP Act 2023 — farmer data (land records, Aadhaar references, bank status, location) requires lawful purpose, notice/consent, purpose limitation, data minimization; collect only what a scheme rule needs; do not persist Aadhaar or bank account numbers. Aadhaar Act — do not store or display full Aadhaar numbers; refer to Aadhaar as a document to bring; redact 12-digit patterns from logs/traces. Advisory disclaimer — prototype/decision-support tool, not a government authority; final eligibility is determined by the department/portal. Synthetic-scheme disclosure in text and (later) audio. No financial advice — do not state loan/insurance payout amounts as guarantees.

## Recommended Phase 2 project structure
- source: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (§3 Recommended Project Structure)
- type: nfr
- content: `backend/nlu/{schemas.py, prompts.py, extractor.py, normalize.py, providers/{gemini.py, ollama.py}}`, `backend/conversation/{state.py, dialogue.py}`, `backend/rules_engine.py` (Phase 1, unchanged), `backend/tests/{test_nlu_extraction.py, test_conversation_state.py}`, `data/schemes_dataset.json` (Phase 1), `data/eval/nlu_golden.jsonl`, `cli_chat_prototype.py`.

## Audio ingestion and acoustic specifications
- source: requirements.md (§1.1)
- type: nfr
- content: Audio format Opus / WebM / Linear PCM 16-bit. Sampling rate minimum 16 kHz (recommended 44.1 kHz client capture downsampled to 16 kHz mono). VAD via Web Audio API / Silero VAD on the browser client; silence threshold 900 ms of continuous silence triggers auto-submission; max utterance limit 30 seconds per turn.

## FarmerAgriculturalProfile extraction contract
- source: requirements.md (§1.2)
- type: schema
- content: TypeScript interface with fields `session_id`, `language: "kn-IN"`, `dialect_region? ("North_Karnataka"|"Old_Mysore"|"Coastal"|"General")`, `district?`, `taluk?`, `land_size {value, unit: "acre"|"gunta"|"hectare", normalized_acres}` (1 gunta = 0.025 acre, 1 hectare = 2.471 acres), `ownership_type ("Owner"|"Tenant"|"Joint Family"|"Unknown")`, `crops[] {local_name_kn, standard_name_en, season? ("Kharif"|"Rabi"|"Summer")}`, `irrigation_source ("Rainfed"|"Borewell"|"Canal"|"Open Well"|"None")`, `farmer_category? ("Marginal (<2.5 acres)"|"Small (2.5-5 acres)"|"Large (>5 acres)")`, `assistance_intent` (6-value enum), `missing_required_slots[]("land_size"|"crops"|"irrigation_source"|"district")`.

## SchemeEvaluationResult engine contract
- source: requirements.md (§2)
- type: api-contract
- content: The rule engine operates deterministically on the profile above without calling any external LLM, returning `SchemeEvaluationResult { scheme_id, scheme_name_kn, scheme_name_en, department, status: "ELIGIBLE"|"CONDITIONALLY_ELIGIBLE"|"INELIGIBLE", estimated_benefit {type: "Direct_Cash_Transfer"|"Subsidy_Percentage"|"Insurance_Payout"|"Low_Interest_Loan", amount_in_inr?, description_kn}, audit_trail {rule_evaluated, criteria_matched[], criteria_failed[], official_gazette_ref}, required_documents[] {document_name_kn, document_name_en, is_mandatory, how_to_obtain_kn}, application_channels[] ("Grama One"|"Raitha Samparka Kendra (RSK)"|"Seva Sindhu Online"|"Samrakshan Portal") }`.

## Backend dependency manifest
- source: requirements.md (§3)
- type: nfr
- content: `fastapi>=0.110.0`, `uvicorn[standard]>=0.28.0`, `pydantic>=2.6.0`, `python-multipart>=0.0.9`, `google-genai>=0.1.0`, `requests>=2.31.0`, `soundfile>=0.12.1`, `pydub>=0.25.1`, `python-dotenv>=1.0.1`, `aiofiles>=23.2.1`. (The `google-genai` floor here is superseded by the SPEC pin — see INGEST-CONFLICTS.md INFO.)

## Frontend dependency manifest
- source: requirements.md (§3)
- type: nfr
- content: dependencies `react ^18.3.1`, `react-dom ^18.3.1`, `lucide-react ^0.364.0`, `clsx ^2.1.0`, `tailwind-merge ^2.2.2`; devDependencies `@vitejs/plugin-react ^4.2.1`, `tailwindcss ^3.4.1`, `vite ^5.2.0`.

## Error handling and edge-case protocols
- source: requirements.md (§4)
- type: nfr
- content: (1) Heavy wind / tractor noise → ASR gibberish or zero tokens: detect confidence < 0.4 and respond with a polite Kannada audio nudge. (2) Mixed English/Kannada jargon ("Nanage borewell ge loan subsidy bekittu"): few-shot system prompt maps "borewell", "subsidy", "loan" to Kannada agricultural context. (3) Incomplete land information: rule engine tags `missing_required_slots: ["land_size"]`; dialogue manager generates a spoken-Kannada follow-up. (4) Tenant farmer with no RTC in own name: engine detects `ownership_type == "Tenant"`, filters owner-only schemes, redirects to tenant-applicable schemes (e.g., PMFBY via tenancy certificate). (5) API rate limits / outage: automatic fallback to secondary provider or pre-rendered Kannada audio templates.

## API contract: POST /api/v1/voice/interact
- source: architecture.md (§4)
- type: api-contract
- content: Input form-data (`audio_file`: WebM/WAV, `session_id`: UUID, `client_state`: optional JSON). Output JSON: `session_id`, `transcription` (Kannada), `farmer_profile {district, land_acres, crops[], irrigation, farmer_category}`, `schemes_evaluated[] {scheme_id, name_kn, name_en, status, benefit, audit_reason, documents_required[]}`, `follow_up_question_needed` (Kannada), `audio_response_url`.

## ASR and TTS provider selection
- source: architecture.md (§2.1, §2.4)
- type: nfr
- content: ASR — Sarvam AI (Saaras / Indic Whisper) primary recommended (best accuracy for Indian accents, regional dialects, code-mixed Kannada + English; ~700 ms cloud latency), Bhashini strong alternative/hybrid, Groq Whisper Large v3 fast fallback/demo safety net (<300 ms), Web Speech API client fallback. TTS — Sarvam AI (Bulbul) top recommendation (~400 ms, expressive Indian-accented Kannada cadence), ElevenLabs Multilingual v2 best final-presentation voice (~600 ms), Google Cloud TTS `kn-IN` Neural2 solid alternative (~300 ms).

## Deterministic rule engine implementation pattern
- source: architecture.md (§2.3)
- type: nfr
- content: Pure Python deterministic evaluator implementing the Rule Object / Specification Pattern; evaluates explicit boolean conditions (e.g., `if profile.land_size_acres <= 5.0 and profile.irrigation_type == "Rainfed": eligible_schemes.append(RAITHA_SIRI)`) and emits audit-trail strings. No LLM call in the decision path.

## Voice turn latency budget under 1800 ms
- source: voice_interaction_design.md (§4.4)
- type: nfr
- content: Client VAD detection 150 ms; audio transmission & Sarvam ASR 600 ms; Fast LLM entity extraction & rule evaluation 450 ms; Sarvam/ElevenLabs TTS first audio chunk 450 ms; browser audio playback initiation 150 ms; total ~1.8 seconds.

## Spoken response brevity
- source: voice_interaction_design.md (§1, §4.3)
- type: nfr
- content: Spoken responses capped at 2 to 3 concise, rhythmic sentences (15-20 words max per audio turn); the LLM system prompt hard limit is "maximum 25 words" and eligibility must be confirmed "using only the verified rules passed to you". Full details are shown visually on cards instead of being spoken.

## Barge-in / interruptible playback
- source: voice_interaction_design.md (§1)
- type: nfr
- content: Audio playback must pause immediately via Web VAD as soon as the farmer speaks; users must not have to wait for robotic audio to finish before speaking again.

## Conversational state machine
- source: voice_interaction_design.md (§2)
- type: protocol
- content: States/transitions: `Idle_Greeting` → `Listening_For_Profile` → `Parsing_Slots` (Extract_Location, Extract_Land_Size, Extract_Crops, Extract_Irrigation, Extract_Needs) → `Evaluate_Completeness` → (`Clarification_Turn` → `Listening_For_Profile`) or `Run_Rule_Engine` → `Generate_Auditable_Result` → `Deliver_Voice_Response` → `Interactive_Card_Review` → (`Listening_For_Followup` → `Clarification_Turn`) or terminate.
