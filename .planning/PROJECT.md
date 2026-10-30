# Krishi Mitra

## What This Is

A voice-first Kannada assistant that tells Karnataka farmers which government agricultural schemes they actually qualify for. A farmer speaks (or types) in rural Kannada; the system extracts a structured farm profile, runs a pure-Python deterministic rule engine over five benchmark schemes, and answers with a brief spoken Kannada reply plus high-contrast visual cards listing documents and the exact rules that decided the outcome.

Built for a hackathon as a 3-stage evolutionary prototype: **Stage 1** text-in → text-out CLI, **Stage 2** text-in → Kannada voice-out, **Stage 3** full voice-in / voice-out browser application. Python backend + CLI first; the browser UI arrives only in Stage 3.

## Core Value

**Every eligibility answer is produced by the deterministic rule engine and can be traced to a written rule — the LLM only listens and speaks, it never decides.** If the demo sounds warm but states an eligibility the rules did not produce, the project has failed.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **DATA-01**: The 5 benchmark schemes are modeled as data (`real` vs `synthetic_demo`, eligibility rules, exclusions, documents, Kannada metadata), sourced from `schemes_knowledge_base.md`.
- [ ] **DATA-02**: Every synthetic-scheme mention carries a `[DEMO / TEST CASE]` marker from the engine through to whatever surface shows it.
- [ ] **ENG-01**: A pure-Python deterministic evaluator returns ELIGIBLE / CONDITIONALLY_ELIGIBLE / INELIGIBLE for all 5 schemes with an audit trail, required documents and application channels — no LLM, no network.
- [ ] **NLU-01**: Rural-Kannada dialect and jargon (North Karnataka `-aitri`, Old Mysore `-kanri`, Togari/Kabbu/Jola, Gunta→acre, Kushki→Rainfed) normalize to canonical values before evaluation.
- [ ] **NLU-02**: Multi-turn slot filling asks proactive Kannada follow-ups for missing fields and confirms low-confidence or conflicting values instead of guessing.
- [ ] **NLU-03**: Guardrails hold — eligibility firewall, evidence check, land-unit sanity, conflict quarantine, PII redaction, and no payout figures in any reply.
- [ ] **CLI-01**: The benchmark Kannada sentence produces eligible Demo Micro-Irrigation Support + PM-KISAN, with audit trail and document list (Stage 1 acceptance).
- [ ] **TTS-01**: Recommendations are spoken in natural, warm rural Kannada via free TTS.
- [ ] **TTS-02**: Stage 2 acceptance — Kannada audio in <500 ms, ≤2–3 sentences, no payout figures.
- [ ] **VOI-01**: Browser voice capture with VAD and streaming transcription completes a turn in <2.0 s.
- [ ] **UI-01**: Bimodal accessible web UI — audio visualizer, live Kannada transcript, scheme cards with status colours and document checklists, barge-in.
- [ ] **UI-02**: An auditable reasoning drawer shows the rules evaluated, criteria matched/failed, and the gazette reference per scheme.
- [ ] **APP-01**: Stage 3 acceptance — speak → transcribe → evaluate → speak + cards updated in <2.0 s.
- [ ] **PLAT-01**: All three stages are delivered in order and each remains runnable from the repo.
- [ ] **PLAT-02**: The whole stack runs on free tooling — no paid tier, and Stage 2 needs no API key.

### Out of Scope

- **Raitha Siri, Krishi Bhagya, Surya Raitha (PM-KUSUM), KCC** — no rule data (eligibility rules, benefits, exclusions, documents) exists for them; RESOLVED-W1 makes the 5-scheme benchmark authoritative. Stale references in `architecture.md` §2.3/§4 and `voice_interaction_design.md` Script 2 are non-authoritative.
- **Any payout or compensation figure in a reply** (e.g. the PMFBY ₹15,000/ha line) — payout depends on external state; stating it is misinformation for low-literacy farmers (RESOLVED-W3). Replies name eligibility and documents only.
- **Write-backs to live government databases** — hackathon non-goal.
- **Languages beyond Kannada / code-mixed Kannada-English, and states beyond Karnataka** — hackathon non-goal.
- **Computer-vision pest diagnostics** — hackathon non-goal.
- **Paid model tiers, OpenAI/Anthropic paths, agent frameworks** (Google ADK, LangChain, LangGraph, LlamaIndex, Haystack, AutoGen/AG2, CrewAI) — free and open tooling only.
- **User accounts, auth, long-term profile retention** — in-process session state only, per DPDP data minimisation.

## Context

- **Repo state:** planning documents only. No application code exists yet — no `backend/`, no `data/`, no `cli_chat_prototype.py`. This milestone builds from zero.
- **Ingest provenance:** `.planning/intel/{SYNTHESIS,requirements,constraints,context,decisions}.md` plus `.planning/INGEST-CONFLICTS.md` hold the full synthesis. Requirement IDs here are normalized; the original intel IDs are preserved in `REQUIREMENTS.md` → Provenance.
- **Demo success metric:** a hackathon demo in which 100% of scheme eligibility decisions come from the deterministic rule engine (zero LLM-hallucinated eligibility), the 5 benchmark schemes evaluate correctly, and the full voice roundtrip runs under 2.0 s.
- **Audience:** low-literacy rural farmers on low-end phones. Bimodal feedback (voice + cards) is an accessibility requirement, not polish — the spoken reply is short because the cards carry the detail.
- **Canonical sources to read before planning:** `schemes_knowledge_base.md` §1 (eligibility rules), `.gsd/SPEC.md`, `.gsd/DECISIONS.md`, `.gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md` (NLU contract, guardrails, structure), `requirements.md` (schemas, dependency manifests), `architecture.md` (component layout). `dataset_research.md` §2 is illustrative only.
- **Stale doc references carried as follow-ups (source docs deliberately not edited this run):** `.gsd/REQUIREMENTS.md` REQ-04 still lists 6 schemes; `architecture.md` §2.3/§4 still use `RAITHA_SIRI`; `voice_interaction_design.md` Script 1 still promises ₹15,000/ha. Tracked in `STATE.md` → Pending Todos.
- **Existing artifacts to reconcile, not ignore:** `.gsd/phases/1/1-PLAN.md` (Phase 1 task sketch) and `.gsd/phases/02-.../02-AI-SPEC.md` (NLU contract) predate this roadmap; they inform Phase 1/2 planning but the roadmap wins on phase boundaries.

## Constraints

- **Architecture (ADR-001, locked):** LLM *perceives and phrases*, never decides. All eligibility, benefit wording, exclusions and document requirements come from `backend/rules_engine.py`. No LLM in the decision path; if phrasing fails, fall back to a template reply built from engine output.
- **Brevity (ADR-002, locked):** spoken reply under 25 words / 2 sentences; design target 15–20 words.
- **Latency:** full voice roundtrip <2.0 s; design budget <1.8 s (VAD 150 ms, ASR 600 ms, extract+eval 450 ms, TTS first chunk 450 ms, playback 150 ms).
- **Tooling (free only):** `google-genai>=1.0,<2.0` + Pydantic v2 (`>=2.6,<3`), Ollama `qwen2.5:7b-instruct` fallback selected by `NLU_PROVIDER=gemini|ollama`; Edge-TTS `kn-IN-GaganNeural` / `kn-IN-SapnaNeural` (no key, no cost); Groq Whisper large-v3 or Sarvam Saaras for ASR; FastAPI + React 18 + Vite + TailwindCSS. Gemini free tier is 15 RPM / 1M TPM — serialize per session.
- **Module paths (fixed):** `data/schemes_dataset.json`; `backend/rules_engine.py` (`SchemeEvaluator`, `FarmerProfile`, `EvaluationResult`); `backend/nlu/{schemas,prompts,extractor,normalize}.py` + `backend/nlu/providers/{gemini,ollama}.py`; `backend/conversation/{state,dialogue}.py`; `backend/tts_service.py`; `backend/asr_service.py`; `backend/server.py`; `cli_chat_prototype.py`; `frontend/`.
- **Schemes (RESOLVED-W1):** exactly five — PM-KISAN, PMFBY, Demo Micro-Irrigation Support, Demo Agricultural Equipment Assistance, Demo Soil Improvement Support.
- **Rules source (RESOLVED-W2):** `schemes_knowledge_base.md` §1 is canonical; `dataset_research.md` §2 is illustrative. Concretely: PMFBY covers Maize and risk types Drought / Excess Rainfall / Pest Attack / Flood / Hailstorm; PM-KISAN has **no** pensioner exclusion; Demo Equipment has **no** max acreage and includes Weeder; Demo Soil includes "Micronutrient Deficient" and has no polyhouse exclusion; Demo Micro-Irrigation is ≤5.0 acres @90% and 5.0–12.5 acres @70%.
- **Privacy/compliance:** DPDP 2023 + Aadhaar Act — never persist or display full Aadhaar/bank numbers, redact 12-digit patterns from logs and traces, collect only what a rule needs. Advisory framing: decision-support prototype, not a government authority.
- **Environment:** Python 3.10+, single developer + AI agent, Windows dev machine. No test infrastructure exists yet.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LLM perceives and phrases; Python engine decides (ADR-001) | Hallucinated eligibility is the core product risk; auditability is the differentiator | ✓ Locked |
| Bimodal feedback: ≤25-word spoken reply + synchronous visual cards (ADR-002) | Voice alone cannot carry document checklists to low-literacy users; latency budget forbids long speech | ✓ Locked |
| The 5-scheme SPEC benchmark set is authoritative (RESOLVED-W1) | No rule data exists for Raitha Siri, Krishi Bhagya, Surya Raitha or KCC; a 6th scheme would be unbuildable | ✓ Locked |
| `schemes_knowledge_base.md` §1 is the canonical rule source (RESOLVED-W2) | Titled rule catalog, carries official exclusions; `dataset_research.md` §2 is illustrative research output | ✓ Locked |
| Never state a payout or compensation amount (RESOLVED-W3) | PMFBY/PM-KISAN amounts depend on external state; over-promising is a Critical eval dimension | ✓ Locked |
| `google-genai>=1.0,<2.0` + Pydantic v2, Ollama `qwen2.5:7b-instruct` fallback | SPEC pin outweighs the older `>=0.1.0` floor; schema-constrained output; offline demo safety | — Pending |
| Rule engine path is `backend/rules_engine.py` (not `schemes_evaluator.py`) | 6 of 7 sources plus the SPEC-typed plan agree; `schemes_evaluator.py` is prose in `architecture.md` only | — Pending |
| Dataset artifact is `data/schemes_dataset.json` | ROADMAP, plan.md, 1-PLAN and the AI-SPEC agree; `.gsd/STATE.md`'s `schemes_db.json` is stale | — Pending |
| NLU laid out as a `backend/nlu/` package per 02-AI-SPEC; CLI is `cli_chat_prototype.py` | Higher-precedence technical contract; supersedes `nlu_extractor.py` / `cli_chat.py` | — Pending |
| Session state in-process (`dict[session_id, ConversationState]`), JSON-serializable | DPDP minimisation, no DB needed for a demo; keeps the door open for Phase 4 persistence | — Pending |
| Stage 2 uses Edge-TTS before Sarvam Bulbul | Zero API key and zero cost guarantees a rehearsable demo; Sarvam optional upgrade | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-30 after initialization from doc ingest*
