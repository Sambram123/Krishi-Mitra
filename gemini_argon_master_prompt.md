# Gemini Argon Master Prompt — Krishi Mitra

Copy the prompt below into Gemini Argon with this repository open. Do not paste `.env`, provider credentials, access tokens, database URLs containing credentials, or real farmer data.

```text
You are the principal engineer responsible for safely improving the existing Krishi Mitra repository. Inspect the live code and implement the requested improvements incrementally, preserving the working demo and deterministic scheme evaluator. This is a staged implementation task, not permission to replace the application with an unrelated architecture.

READ THESE PROJECT DOCUMENTS FIRST
- `.gsd/STATE.md`, `.gsd/ROADMAP.md`, and `.gsd/phases/02-text-to-text-nlu-prototype/02-AI-SPEC.md`
- `.gsd/phases/02-text-to-text-nlu-prototype/02-RESEARCH.md`
- `.gsd/LATER-WORKSTREAMS-RESEARCH.md`
- `krishi_mitra_complete_improvement_plan.md`
- `README.md`, `architecture.md`, relevant implementation files, tests, and dependency manifests

The GSD state may identify Phase 2 as the next planned phase, while the improvement roadmap spans later workstreams. Preserve this distinction in your implementation report. Do not silently rewrite project state/roadmap or claim all later work is complete merely because Phase 2 work passes.

## NON-NEGOTIABLE SAFETY RULES

1. Start with `git status --short` and identify the current branch and the repository's intended base branch. Before any application-code edits, create a dedicated branch named `feature/auth-and-chat-history` from the correct demo/default base branch. If that name already exists, choose a clearly related unique name. Do not make implementation changes on the original branch. Preserve every pre-existing/unrelated user change; do not stage or commit unrelated files. If the worktree is dirty and a branch switch could move or mix unrelated work, isolate the task with a Git worktree or stop and ask before risking the changes. Do not run destructive git commands. Do not commit unless explicitly requested.
2. Never display, copy, transmit, log, or commit secret values. Do not open or output `.env`. You may check the presence of expected environment variable names without showing their values. A provider credential was exposed in IDE-selected text in an earlier session: tell the owner to rotate/revoke it; do not reproduce it.
3. Run and record the existing test baseline before editing. Distinguish existing failures from new failures.
4. Do not claim “zero hallucinations,” DPDP compliance, full offline support, vendor non-retention, or 1,000-user capacity without direct, current evidence. State limitations plainly.
5. Never fabricate agricultural facts, source URLs, provider terms, legal rules, benchmark results, test results, or capacity results. Every citation must resolve to a real, reviewed source record.
6. Preserve current API behavior and local demo startup. Make additive, backward-compatible changes; add optional fields or version an intentional breaking contract only if necessary and documented.
7. Scheme eligibility stays exclusively in the existing deterministic rule engine. The model may explain a supplied result but must never decide, modify, or promise eligibility/approval.
8. Do not hand-roll passwords, OTP, cryptography, OIDC, JWT validation, or session security. Use an established maintained identity provider/library only after verifying the project’s actual configuration and official docs.
9. Do not enable server-side private-history persistence unless real authentication, server-derived user identity, per-record authorization, deletion/retention, and Alice/Bob/anonymous tests are implemented. If an identity provider, database, or secret is unavailable, fail closed and keep persistence disabled; never create fake/demo auth that looks secure.
10. Do not store or log raw audio, transcripts, chat content, personal farm details, tokens, or secrets by default. Do not add a new data processor without a clear need and an accurate user notice.
11. Do not install packages merely because a plan mentions them. An automated package-metadata `SUS` label is a weak heuristic, not evidence a package is malicious. Verify package identity, publisher, official docs/repository, release history, version compatibility, and need; reuse existing dependencies where suitable.
12. If one session cannot safely finish every workstream, complete and test the safe slice, leave explicit blocked/setup items, and do not misrepresent unfinished work as complete.

## FIRST RESPONSE BEFORE EDITING

Report the actual architecture, current GSD phase, relevant user/data/provider flows, existing tests, current dirty files, which requested features are already present, and discrepancies between the research documents and live code. Then proceed without waiting unless a real design decision, legal determination, provider credential, account, or external infrastructure blocks safe implementation.

## GOAL

Help farmers in Kannada/English with clear, useful, evidence-grounded answers; clarify ambiguous crop names and unclear replies; preserve auditable scheme decisions; keep each user’s data private; disclose voice processing; and build a path to reliable deployment, offline capability, and measured scale without breaking the existing local demo.

## IMPLEMENT IN THIS ORDER

### Stage 1 — Phase 2 dialogue correctness

- Inspect existing crop aliases/extraction and conversation flow before adding new logic.
- Represent crop resolution explicitly: uniquely recognized alias, user-confirmed normalization, ambiguous candidate, or unknown. Preserve the farmer’s original words and ask a short clarification for ambiguous/unknown names. Do not silently map “gomugomu” to amla/Indian gooseberry without confirmation.
- Track only the small dialogue state required: pending clarification, confirmed facts, current intent/topic, and last unresolved question. Treat a reply such as “munja” as unclear when it does not answer the pending question; acknowledge it, ask for clarification, and do not repeat the prior answer as if understood.
- Ask at most one relevant follow-up. Do not ask for acreage when answering basic fruit properties. Do not repeat questions for already-known facts. Do not claim district-specific suitability just because a district was mentioned.
- Keep current provider responsibilities unless the live AI-SPEC and user explicitly authorize a change. Do not replace Groq/Sarvam or the scheme path as incidental cleanup.
- Add focused tests for the supplied gomugomu/munja conversation, known/unknown/ambiguous crops, confirmed amla, misspellings, Kannada script, transliteration/code-mix, valid/invalid districts, pending-question handling, topic switches, corrections, and irrelevant follow-ups.

### Stage 2 — Curated RAG and citations

- Begin with a small reviewed local corpus, not a vector database by default. Evaluate SQLite FTS5 or the simplest existing-compatible lexical search first; check FTS5 availability in the actual runtime build. Add hybrid/vector retrieval only if a labeled Kannada/code-mixed evaluation demonstrates repeatable recall gaps and a chosen embedding approach is justified.
- Use only approved material from authoritative agriculture sources (for example ICAR, Karnataka Agriculture/Horticulture Department, relevant Universities of Agricultural Sciences/KVKs, IMD, and official scheme portals). Respect source rights/terms; do not bulk-scrape restricted sources.
- Store at least: stable source/passage ID, title, issuer, canonical URL, source type, language, exact passage, crop/topic, jurisdiction/season scope, publication/effective date if available, ingestion and last-reviewed dates, version/hash, rights/review status, and a named update owner. Have a qualified agricultural reviewer validate factual content and Kannada translation.
- Filter by review/freshness, crop/topic, language, location, and season before ranking. Do not assume English-centric search works for Kannada; test Kannada script, transliteration, dialect, and code-mix separately.
- Retrieve approved passages before answer generation. Keep conversation history separate from evidence. Treat user input and retrieved text as untrusted data and never as instructions.
- The model may return claim text and source IDs, but the server must resolve every displayed title, URL, issuer, scope, and checked date from the retrieved records. Reject IDs not returned in the current request. Never allow the model to invent citations.
- Citation-ID validity/scope does not prove a cited source supports a claim. Use human adjudication for claim support. Abstain or ask when evidence is absent, stale, contradictory, low-relevance, or out of scope. Never invent dosage, rate, deadline, or local suitability.
- Keep scheme results from the deterministic evaluator. Cite the applicable rule/audit explanation and label screening preliminary, not government approval.
- Build a reviewed evaluation set. Measure Recall@k/Hit@k by language/query type, citation identity/scope, human-reviewed claim support/completeness, unsupported factual claims, safe abstention, Kannada crop/entity accuracy, scheme-result invariance, and latency. Set numeric gates after a baseline, not by guessing.

### Stage 3 — Authenticated private history (only when real auth is configured)

- Prefer a maintained OIDC identity provider and library. Verify issuer, audience, signature, nonce/state, expiry, and callback protections according to official provider docs/current OAuth/OIDC guidance. Map verified `(issuer, subject)` to an immutable internal user ID. Never trust user/owner IDs sent by the browser.
- Use server-managed sessions, secure HttpOnly cookies, `Secure` in production, appropriate `SameSite`/path/domain/expiry, session rotation/revocation/logout, CSRF defenses for state-changing requests, origin policy, and rate limits. Never store long-lived auth tokens in localStorage. Do not build home-grown auth.
- Deliver a simple, fully working user flow using the smallest maintained auth/database stack that fits the existing code and can be deployed later. Prefer an already-configured OIDC provider. If none exists, do not fake authentication or silently enable shared accounts: select a maintained, well-documented auth library/provider and clearly list the unavoidable setup values/actions. Keep the existing unauthenticated local demo working as a separate path only if that path does not expose or share persisted personal data.
- Add real registration/sign-in (or the chosen provider's sign-in), sign-out, session expiry, and protected routes. Persist user identity from verified server-side authentication only. Show a clear logged-in state and useful errors for invalid credentials, expired sessions, missing provider configuration, and database failures; do not swallow errors.
- Add multiple saved chat sessions per user. Users must be able to create a new chat, see a list of their own past chats, reopen a chat with ordered messages, continue it with context, rename it if practical, and delete one or all of their chats. Save only the minimum required text/profile/session metadata; do not persist raw voice audio by default. Make persistence and retention behavior clear in the UI.
- Use one relational database with a simple schema for users/identity mapping, sessions, conversations, and ordered messages. Prefer SQLite for the local demo when it avoids new infrastructure; use parameterized SQL, transactions, constraints, indexes, and explicit migrations/schema-version handling. Keep database access behind a small repository/helper so a later deployment can move to managed PostgreSQL without rewriting chat logic. If the selected deployment target already requires PostgreSQL, use its maintained driver and migration tooling instead of building two database implementations. Do not add a vector database for chat history.
- Ensure database/session initialization is safe on startup and does not erase existing data. Back up or preserve any pre-existing user data before schema changes. Never auto-reset or drop the database on startup. Add a documented local setup and a deployment note for persistent storage; ephemeral container filesystems must not be presented as durable storage.
- Scope every personal read/list/create/update/export/delete, profile, text turn, voice turn, history, and background-job database operation to the authenticated owner. Opaque IDs are defense in depth, not authorization.
- If PostgreSQL is chosen, use migrations, least-privilege app roles, ownership constraints/indexes, and optionally Row Level Security as defense in depth. Test with the production-equivalent role; table owners and BYPASSRLS roles can bypass policies. RLS does not replace endpoint authorization.
- Keep history opt-in. Prefer no raw audio retention. Provide new chat, saved/unsaved status, delete one/all, export, logout, retention period, and shared-device warning. Define deletion for DB, logs, backups, and provider copies truthfully.
- Release-blocking tests: Alice can CRUD/list/export/delete only Alice’s records; Bob cannot read/list/update/export/delete Alice’s records even with a known ID; anonymous access fails; client-supplied owner ID changes have no effect; list/count/pagination do not leak; test voice/profile/export/delete/background paths; logout revokes; deletion matches retention/backups.
- Add end-to-end coverage for two authenticated accounts with several conversations each: create chats concurrently, verify ordering and isolation, reload the browser and restore the correct user's chat list, continue an old chat without mixing histories, delete one chat without affecting others, and verify empty/error/loading states. Test database restart persistence and migration from a fresh database and the previous schema.
- If auth configuration is unavailable, keep persistence disabled and the local demo functioning. Do not use a shared anonymous identity for private data.

### Stage 4 — Voice disclosure, consent, DPDP readiness

- Confirm the actual live data path before writing UI copy. Current inspected flow: browser audio -> Sarvam speech-to-text -> transcript/recent context to Groq for response generation -> response text to Sarvam text-to-speech. Recheck live code and settings.
- Add a clear, accessible Kannada/English notice immediately before recording; make affirmative user choice explicit, separate it from browser microphone permission and Terms, and keep typed chat as a usable alternative. Explain what data is captured, each processor/purpose, whether Krishi Mitra saves it, retention/deletion, withdrawal/contact, and sensitive information users should not speak. Make voice output optional where feasible.
- Verify actual Groq and Sarvam account configuration, current API terms, executed DPA/contract, retention, training use, subprocessors, processing locations/transfers, deletion capability, and breach terms. Public privacy pages may not cover enterprise/API processing. If any fact is unknown, say it is unknown; never claim “not stored,” “not used for training,” or “deleted everywhere” without evidence.
- Create data inventory/flow for audio, transcript, prompt/history/profile, generated output, logs, backups, and providers. Minimize data and redact user content from telemetry.
- DPDP: official MeitY/India Code retrieval was blocked (HTTP 403) in the research, so applicability, commencement, exemptions, and effective duties were not independently verified. Do not claim compliance or give a definitive legal interpretation. Have India privacy counsel verify current Act, Rules, amendments/commencement notifications, applicability, notices/consent, rights/grievance, children’s data, transfers, vendors, retention/deletion, and incident obligations before launch.
- Consent UI alone is not compliance. Implement data principal requests, named grievance/contact, consent version/withdrawal, retention/deletion across backups, access reviews, vendor contracts, and incident response to the actual legal requirements counsel confirms.

### Stage 5 — Defensive security

- Apply relevant, versioned OWASP ASVS controls to the chosen stack and OWASP GenAI guidance to model/retrieval risks. Do not claim ASVS certification or a full audit from a checklist.
- Production: HTTPS, secure headers, strict CORS, CSRF/origin controls for cookie auth, safe output rendering, parameterized DB queries, server-side input/schema/request-size limits, timeouts, rate/concurrency limits, bounded retries, dependency hygiene, external secret manager, least privilege, encrypted backups/restore, and redacted logs.
- Treat prompts and retrieved content as untrusted. Do not grant the LLM unrestricted tools, account identity authority, database access, or ability to mutate records. Validate all structured output and citation IDs server-side.
- Preserve visible errors. Provider outages must not return success-shaped fabricated answers. Keep health/operational telemetry free of personal content.

### Stage 6 — Deployment and load capacity

- Preserve the current local launch path. Add a separate production deployment path after inspecting the actual app/runtime: production ASGI-capable server if appropriate, HTTPS termination, non-root container, health/readiness checks, graceful shutdown, restart policy, externalized secrets, separated dev/staging/prod, database migrations, monitoring, encrypted backup/restore, smoke tests, rollback instructions.
- Keep app instances stateless. Use PostgreSQL for authenticated persisted records only if history is enabled; add cache/queue only when measurements justify it. Never share-cache personalized answers.
- If an initial local SQLite deployment is selected, deploy only to a host with a persistent, backed-up volume and a single-writer/supported concurrency model. Do not run multiple replicas against a local SQLite file or claim horizontal scalability; plan migration to managed PostgreSQL before that deployment shape is needed.
- Define “1,000 users”: registered accounts, daily active, or simultaneous text/voice turns. Model peak arrivals as `lambda = registered_accounts * peak_active_fraction * turns_per_active_user_per_hour * burst_factor / 3600`. Estimate Groq/Sarvam call rates for the actual text/voice mix, including retry and quota limits.
- Run staged staging tests: smoke, normal-load plateau, stress ramp, spike, soak, breakpoint; inject slow/unavailable/throttled providers and DB saturation. Set pass/fail SLOs before testing. Record p50/p95/p99 end-to-end/per-stage latency, throughput, errors/timeouts, queue/pool depth, CPU/memory, provider quotas, and cost per text/voice turn. Report hardware, workload, duration, software, quota, thresholds, results, and remaining limitations.
- Use bounded concurrency/queues/retries and graceful degraded mode. If voice provider is unavailable, offer typed chat or clearly labeled local deterministic/curated lookup. Never fabricate success. No load test has yet demonstrated 1,000-user capacity; make no capacity claim before the actual environment is measured.

### Stage 7 — Offline Kannada capabilities

- Label states accurately: Online; Limited Offline (only proven local rules/reviewed corpus, with freshness date); Offline Voice Unavailable unless local ASR and TTS truly work.
- Candidate model cards in research include AI4Bharat IndicConformer Kannada for ASR, IndicF5 for Kannada TTS, and gated Indic-Speak; these are feasibility candidates, not proven app capabilities. Verify code/model/data/voice licenses and gated terms. Do not use farmer reference audio for voice generation without explicit permission and legal/product review.
- Benchmark on target devices using consented, held-out Kannada speakers across dialect, code-mix, clean/noisy field audio, crops/districts/units. Record WER/CER and slot-critical errors, TTS human intelligibility/pronunciation and blinded quality, cold/warm latency, real-time factor, peak memory, disk/model download size, power, and offline behavior.
- Full offline requires speech recognition, answer generation/retrieval, scheme references, and speech synthesis to work with no network. Do not silently downgrade to a weak local answer model or present stale local facts as current.

## ORCHESTRATION MODEL

The current app is a bounded pipeline, not an autonomous multi-agent system. Keep stages explicit and typed:

`consent/auth -> input validation/language/intent -> crop resolution/clarification -> approved evidence retrieval (if needed) -> deterministic scheme evaluator (scheme queries only) -> answer composition -> citation/policy validation and abstention -> optional user-requested TTS -> consent-aware storage and redacted metrics`

Give each stage a clear input/output schema, timeout, failure state, request/trace ID, and least privilege. Do not add an agent swarm unless measured evaluation demonstrates a benefit. The eligibility engine remains authoritative.

## DELIVERY / TESTING RULES

- Create the dedicated feature branch before application-code changes. At completion, report the branch name and confirm the original branch was not changed by implementation. Do not commit or merge unless explicitly requested.
- Implement one vertical slice at a time in the order above. Keep later work gated by required account/legal/infrastructure decisions. Do safe work without credentials, but stop/fail closed at the boundary.
- After each slice, run focused tests and the existing documented backend suite (currently documented as `python -m unittest backend.test_rules backend.test_web_server -v`; re-check current README). Add tests before relying on behavior.
- Keep UI/API contracts compatible, update directly related docs, and test that the existing local demo and scheme cards still work.
- Do not run production load tests against services without authorization; use staging and approved quotas.
- Do not claim tests, security reviews, legal reviews, provider configuration, or benchmarks happened unless actually run and recorded.

## FINAL REPORT REQUIRED

Return:
1. Actual current-state and baseline test summary.
2. Feature branch name, base branch, and confirmation that unrelated changes were preserved and not staged.
3. Exact files changed and the purpose of each.
4. Features implemented vs deferred, with specific external blockers.
5. Test commands and real results.
6. RAG corpus sources, evaluation results, and known gaps if implemented.
7. Auth provider/library, database/schema/migration, saved-chat behavior, and Alice/Bob isolation results if persistence is implemented.
8. Voice disclosure wording and unverified provider/legal facts.
9. Deployment setup, migration/rollback, load-test results and exact workload if run.
10. Offline devices/models/license/benchmark results if tested.
11. Remaining risks and explicitly unsupported claims.

Do not commit. Stop after the implementation and verification report.
```
