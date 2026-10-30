## Conflict Detection Report

Mode: new (no existing `.planning/` context to reconcile against)
Precedence applied: manifest overrides — DECISIONS.md ADR 0, SPEC.md 0, 02-AI-SPEC.md 1, architecture.md 1, prd.md 1, REQUIREMENTS.md 2, requirements.md 2, dataset_research.md 2, schemes_knowledge_base.md 2, voice_interaction_design.md 2, plan.md 3, ROADMAP.md 3, 1-PLAN.md 3, model_capabilities.yaml 3, STATE.md 4.

### BLOCKERS (0)

None. Cycle detection over the cross-ref graph found no cycles (longest chain: 02-AI-SPEC.md -> prd.md, depth 2). No UNKNOWN or low-confidence classifications. ADR-001 and ADR-002 do not contradict each other, and no ingested document overrides either locked decision.

### WARNINGS (3)

[WARNING] Scheme catalog: 5 benchmark schemes vs 6-scheme requirement
  Found: .gsd/REQUIREMENTS.md REQ-04 requires a pure Python evaluator checking explicit criteria for "Raitha Siri, Krishi Bhagya, PM-KISAN, PMFBY, Surya Raitha, and KCC"; .gsd/DECISIONS.md ADR-001 uses `RAITHA_SIRI` in its criteria example; architecture.md §2.3 appends `RAITHA_SIRI` in code and §4 returns a `raitha_siri` result; voice_interaction_design.md Script 2 promises a 60% "Surya Raitha (PM-KUSUM)" solar-pump subsidy.
  Expected: .gsd/SPEC.md "Reference Dataset Scope" (precedence 0) mandates exactly 5 schemes — PM-KISAN, PMFBY, Demo Micro-Irrigation Support, Demo Agricultural Equipment Assistance, Demo Soil Improvement Support; the same 5 are modeled in prd.md §2, .gsd/ROADMAP.md Must-Haves, schemes_knowledge_base.md §1, dataset_research.md §1, plan.md Step 1.1 and .gsd/phases/1/1-PLAN.md.
  Impact: Reading REQ-04 literally forces the rule engine to model schemes that have no catalog data at all (no eligibility rules, benefits, exclusions, or documents exist for Raitha Siri, Krishi Bhagya, Surya Raitha, KCC), and contradicts REQ-benchmark-dataset-5-schemes and the "5 reference schemes" success criterion. Reading the 5-scheme set literally leaves REQ-04 and the demo scripts referencing unevaluable schemes.
  → Decide whether the 5-scheme benchmark set is authoritative (correct REQ-04 to name those 5) or whether the four extra schemes are real scope (author their rule data, then extend REQ-benchmark-dataset-5-schemes). Update REQ-04 and the dialogue scripts to match before roadmap routing.

[WARNING] Competing eligibility-rule values for the same schemes
  Found: dataset_research.md §2 "Canonical Schema Representation" — PMFBY `notified_crops` omits Maize and `risk_types` are "Drought / Excess Rain / Pest / Localized Calamity"; PM-KISAN exclusions include `retired_pensioners_above_10000`; Demo Agricultural Equipment has `min_acres: 1.0, max_acres: 25.0` and `target_equipment` without Weeder; Demo Soil `soil_deficiencies` omit "Micronutrient Deficient" and add exclusion `commercial_polyhouse_farms`; Demo Micro-Irrigation defines no small/marginal threshold.
  Expected: schemes_knowledge_base.md §1 — PMFBY includes Maize and `risk_type IN ["Drought","Excess Rainfall","Pest Attack","Flood","Hailstorm"]`; PM-KISAN exclusions are institutional landholders, constitutional posts, Ministers/MPs/MLAs/Mayors, serving or retired government officers, income-tax payees, and registered professionals (no pensioner clause); Demo Equipment has no maximum acreage and includes "Weeder"; Demo Soil includes "Micronutrient Deficient" with no polyhouse exclusion; Demo Micro-Irrigation defines small/marginal as <= 5.0 acres at 90% and 5.0-12.5 acres at 70%.
  Impact: Both documents carry manifest precedence 2, so precedence cannot break the tie. Whichever set `backend/rules_engine.py` and `backend/test_rules.py` encode will pass or fail the same farmer profile differently (a 20-acre equipment applicant, a Maize PMFBY claimant, a micronutrient-deficient Soil Improvement applicant). A wrong choice silently flips eligibility outcomes.
  → Confirm schemes_knowledge_base.md as the canonical rule source (it is titled "Scheme Rules Catalog" and carries the official exclusions) and treat dataset_research.md §2 as illustrative; alternatively reconcile field by field before Phase 1 test data is authored.

[WARNING] PMFBY payout amount promised in a reusable demo script
  Found: voice_interaction_design.md §3 Script 1 — "ನಿಮ್ಮ 3 ಎಕರೆ ತೊಗರಿಗೆ ಕರ್ನಾಟಕ ಸಂರಕ್ಷಣೆ ಬೆಳೆ ವಿಮೆ (PMFBY) ಅಡಿಯಲ್ಲಿ ಹೆಕ್ಟೇರಿಗೆ ₹15,000 ವರೆಗೆ ಪರಿಹಾರ ಪಡೆಯಲು ಅರ್ಹರಿದ್ದೀರಿ" (qualifies for up to ₹15,000 per hectare compensation).
  Expected: .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md (SPEC, precedence 1) — "Over-promising benefit amounts: PM-KISAN installments/arrears and PMFBY payouts depend on external state; the assistant must not compute or promise a payout" and "No financial advice — do not state loan/insurance payout amounts as guarantees". schemes_knowledge_base.md PMFBY benefit is only "claim payout based on calculated yield shortfall or localized damage".
  Impact: Reusing the script verbatim in prompts, demo data, or eval goldens teaches the assistant to assert a fabricated guaranteed payout — a Critical dimension in the AI-SPEC rubric (reply over-promise rate) and a real misinformation risk for low-literacy farmers.
  → Rewrite the script or mark it non-reusable so the spoken reply names eligibility and required documents without any payout figure.

### INFO (9)

[INFO] Auto-resolved: google-genai version floor
  Note: requirements.md §3 lists `google-genai>=0.1.0`; .gsd/phases/02-.../02-AI-SPEC.md §2 pins `google-genai>=1.0,<2.0` (SPEC precedence 1 over PRD precedence 2). Synthesized intel keeps the SPEC pin; 02-AI-SPEC pitfall #5 also warns not to install the legacy `google-generativeai` package alongside it.

[INFO] Auto-resolved: rule engine module path
  Note: architecture.md §2.3 names `schemes_evaluator.py`; .gsd/ROADMAP.md Phase 1, .gsd/phases/1/1-PLAN.md (verify imports `from backend.rules_engine import SchemeEvaluator`), plan.md Step 1.2, 02-AI-SPEC recommended structure, and .gsd/STATE.md all name `backend/rules_engine.py`. Resolved to `backend/rules_engine.py` (SPEC-typed source plus 5 of 6 sources); `schemes_evaluator.py` recorded as a prose alias in architecture.md only.

[INFO] Auto-resolved: dataset artifact path
  Note: .gsd/STATE.md names `schemes_db.json`; .gsd/ROADMAP.md, plan.md, .gsd/phases/1/1-PLAN.md, dataset_research.md and 02-AI-SPEC.md all name `data/schemes_dataset.json`. STATE.md carries the lowest precedence in the ingest set (4); resolved to `data/schemes_dataset.json` and STATE.md's reference treated as stale.

[INFO] Auto-resolved: Phase 2 module layout and CLI filename
  Note: .gsd/ROADMAP.md Phase 2 deliverables are `backend/nlu_extractor.py`, `backend/conversation_state.py`, `cli_chat_prototype.py`; plan.md Steps 1.3-1.4 use `backend/nlu_extractor.py` and `cli_chat.py`. 02-AI-SPEC (precedence 1) specifies a `backend/nlu/` package (schemas, prompts, extractor, normalize, providers/) plus `backend/conversation/{state,dialogue}.py` and `cli_chat_prototype.py`. Resolved toward the AI-SPEC layout as the higher-precedence technical contract; `cli_chat.py` is superseded by `cli_chat_prototype.py`, while the ROADMAP deliverable names remain valid as labels.

[INFO] Auto-resolved: brevity and latency targets are nested, not contradictory
  Note: ADR-002 (locked) caps spoken replies at "under 25 words / 2 sentences"; SPEC Goals 3 / REQ-01 / REQ-05 repeat <25 words and <2.0s. voice_interaction_design.md tightens to 15-20 words per turn and a <1800ms budget; prd.md §4.2 requires Stage 2 audio in <500ms within 2-3 sentences. Every stricter value is a compatible subset of the locked ceiling, so no decision is overridden — planning should target the stricter numbers (<1.8s, 15-20 words) while honoring ADR-002.

[INFO] Routing note: requirements.md yielded constraints, not requirements
  Note: requirements.md is manifest-typed PRD (precedence 2), but its content is a technical contract — audio/acoustic specifications, `FarmerAgriculturalProfile` and `SchemeEvaluationResult` TypeScript interfaces, dependency manifests, and a failure-mode table — with no user stories or acceptance criteria. Its content was routed to constraints.md (schema / api-contract / nfr) rather than inventing requirement entries. Manifest type remains authoritative for provenance.

[INFO] STATE.md status is stale relative to phase artifacts
  Note: .gsd/STATE.md says "Status: Ready for Planning" and "Next Steps: Run `/plan 1`", but .gsd/phases/1/1-PLAN.md (phase 1, plan 1, wave 1) and .gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md already exist. STATE titles Phase 1 "Knowledge Catalog & Deterministic Rule Engine" while ROADMAP titles it "Reference Dataset & Deterministic Rule Engine". STATE is the lowest-precedence DOC (4); downstream routing should trust ROADMAP plus the phase artifacts over STATE's status line.

[INFO] Provider selection only partly locked
  Note: architecture.md §2.2 offers Gemini 2.5 Flash or GPT-4o-mini; prd.md lists Gemini Flash or local Ollama. ASR ordering differs (architecture: Sarvam primary with Groq fallback; prd.md and plan.md list Groq first; ROADMAP: "Sarvam AI / Groq Whisper"). TTS ordering differs (architecture: Sarvam Bulbul top with ElevenLabs for wow factor; prd.md and ROADMAP: Edge-TTS first, Sarvam optional). 02-AI-SPEC (SPEC, precedence 1) resolves the LLM choice to `google-genai` Gemini with an Ollama fallback and no OpenAI path — recorded in constraints.md. ASR/TTS remain option lists; either is acceptable provided the <1.8-2.0s budget holds.

[INFO] Untrusted-input scan advisory on dataset_research.md
  Note: the read of dataset_research.md raised a LOW advisory for invisible-unicode (a single pattern, consistent with Kannada script and math markup in the document). No instruction-like injected content was found and the document was used as data only. No other ingested source raised a scan flag.
