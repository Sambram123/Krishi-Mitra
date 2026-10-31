# Krishi Mitra — Complete Improvement and Production Plan

**Prepared:** 2026-10-31  
**Purpose:** Turn judge feedback and a judge-style review into a safe, testable implementation roadmap, plus a copy/paste master prompt for Gemini Argon.  
**Status:** Planning document only. No application code is changed by this document.  
**Legal/security note:** This is engineering guidance, not legal advice or a penetration test. DPDP applicability, commencement, notices, vendor terms, and retention need review by qualified India privacy counsel before launch.

## 1. Outcome we are aiming for

Krishi Mitra should be able to answer a farmer in Kannada or English using relevant, current, traceable agricultural evidence; ask for clarification instead of guessing; preserve the deterministic scheme evaluator as the sole eligibility authority; and protect every user's saved conversations and profile from other users. The deployed service should have explicit privacy consent, deletion, access control, operational monitoring, and measured capacity.

**Do not describe the target as “zero hallucinations,” “DPDP compliant,” “fully offline,” or “supports 1,000 concurrent users” until the corresponding controls have been implemented, reviewed, and measured.**

## 2. Current baseline and gaps

This section describes the repository state inspected for the earlier judge-readiness work. Re-check it against the live branch before implementation; do not assume the repo has not changed.

| Area | Current baseline | Gap / judge risk |
|---|---|---|
| Scheme advice | Curated scheme catalogue, deterministic evaluator, audit trail, source links/research date, and disclaimers are present. | LLM wording can still overstate results; current/local availability can go stale. RAG must never replace the deterministic decision. |
| General crop advice | Text model answers broad questions. | No verified crop knowledge retrieval/citation contract was found. Unsupported details can sound authoritative. |
| Crop-name understanding | Some deterministic aliases/profile extraction exist. | Unknown or ambiguous terms may be guessed as a known crop; this caused the “gomugomu” example. |
| Conversation behavior | Recent rendered messages are sent as context; server validates at most eight. | “munja” can be treated as understood; repeated answers and irrelevant follow-ups are possible. |
| Chat history | Browser memory holds the current page; no conversation database was found. | Refresh loses messages. Persistent history would require identity, ownership checks, retention, and deletion. |
| Voice path | Browser records a turn; Sarvam performs transcription and synthesis; Groq generates a response. | The provider data flow and retention must be explicitly disclosed. “Our server does not store audio” is not a claim about vendor retention. |
| Privacy/security | Operational logging avoids the transcript/audio body. | No authenticated user identity or per-user conversation storage/authorization was found. A client-supplied ID must never become authorization. |
| Offline | Local scheme data/rules and a limited typed fallback exist. | Natural generation and voice depend on cloud providers. This is not complete offline operation. |
| Deployment/scale | Local Python `ThreadingHTTPServer`, loopback binding, external model calls. | This is a demo server, not a measured production deployment. No 1,000-user capacity claim is justified. |
| Orchestration | Fixed pipeline: speech-to-text, deterministic extraction/rules, LLM wording, optional speech synthesis. | No multi-agent framework is present; do not describe the current system as an agent swarm. |

### Judge-style read-only audit

A read-only judge audit was run against the current repository. It reported four medium-priority findings; these are evidence-based observations, not a penetration test:

1. **Voice processing lacks a just-in-time notice.** The mic flow is visible in [chat.html](./chat.html); the browser posts audio and recent history from [web_app.js](./web_app.js) to `/api/voice-turn`, and the processing stages are in [backend/web_server.py](./backend/web_server.py). README disclosure alone is not a notice at the point of recording. **Likely judge question:** “Before I tap the mic, what is recorded, which providers receive it, and how can I opt out or request deletion?”
2. **The UI makes an absolute “Zero-Hallucination” claim.** The audit found the phrase in the chat UI, but ordinary model replies have no retrieval/source-check stage. Scheme cards do have source links; that narrower rule-engine control does not validate all general farming advice. **Likely judge question:** “What exactly are gomugomu and munja here, and which agricultural source supports the specific advice?” Remove the absolute claim and describe the bounded guarantee accurately.
3. **Previous chats are not persistent.** The browser builds history from currently rendered messages; the “New Consultation” action clears them; the API validates history supplied by the browser but does not save it. **Likely judge question:** “Can I reopen yesterday’s conversation after refreshing or changing devices?”
4. **No identity or per-user authorization boundary exists for public multi-user deployment.** Current routes have no authenticated identity, and the development server binds to loopback. Since the current app has no server-side conversation store, the audit did **not** demonstrate a cross-user stored-history leak. Exposing the shared provider-backed API publicly would still need authentication, abuse/rate controls, and authorization before adding persistence. **Likely judge question:** “How do you prevent another farmer from accessing my records—or an unauthenticated caller from consuming the shared provider account?”

The audit also confirmed that offline capability is limited (not full offline voice), the current orchestration is a fixed pipeline rather than an autonomous agent system, and there is no production capacity evidence. It reported that the existing offline unit suite passed **27 tests**; that result does not test live model factuality, vendor retention, privacy-law compliance, or production concurrency. The exact “gomugomu/munja” session was supplied as text, not reproduced in the running app during the audit, so those specific turn-level behaviors still need regression tests.

### Credential safety action

A provider credential appeared in the IDE-selected text earlier in this conversation. Treat that credential as exposed: rotate/revoke it with its provider, check that `.env` is ignored and not tracked, and inspect history for accidental commits. Do not put credential values in this document, prompts, screenshots, logs, or source code. If any secret has been committed, rotate it even if the commit is later removed.

## 3. Product and AI behavior requirements

### 3.1 Clarify before crop-specific claims

- Maintain an explicit crop/fruit alias catalogue with local spellings, transliterations, known variants, and confidence/ambiguity metadata.
- If an input could match multiple crops, is unfamiliar, or has low-confidence transcription, ask a short clarification question before giving crop-specific facts.
- Never infer “Gomugomu” means amla without confirmation. Offer likely interpretations only as possibilities, e.g. “Do you mean Indian gooseberry/amla, a local crop name, or something else?”
- If the user confirms a crop, retain that confirmation in the current conversation and show the normalized crop name for easy correction.
- Do not add broad fuzzy mapping that silently converts an unknown word to the nearest crop.

### 3.2 Understand conversation and ask useful follow-ups

- Classify a turn as an answer to a pending clarification, a new question, a likely typo/unclear utterance, or a topic change.
- Maintain a small explicit dialogue state: pending clarification, known farmer facts, current topic, and unanswered user request.
- For an unclear response such as “munja,” say it was not understood and ask the user to repeat or clarify. Do not repeat the previous answer as if the turn had been understood.
- Ask no more than one follow-up at a time, and only if it materially improves the current answer. District may be useful for localized recommendations; acreage is not needed to explain basic fruit properties.
- Do not ask for details already provided. Do not request sensitive identifiers (Aadhaar, bank credentials) for general advice.
- If district is supplied but the retrieved evidence is not district-specific, explicitly say the advice is general; do not claim “in Dharwad” merely because the user named Dharwad.
- Keep the requested answer primary. Avoid ending every answer with a question when no useful question remains.

### 3.3 Retrieval-augmented, cited answers

Build a small, curated knowledge base before adopting a vector database:

1. **Start with authoritative, permissioned material.** Prefer official Karnataka Agriculture/Horticulture Department, ICAR, the relevant University of Agricultural Sciences, KVK, IMD, and official scheme sources. Record the publisher and exact URL. Respect licensing and site terms; do not bulk-scrape restricted sources.
2. **Use structured records with provenance.** Each fact/passage has a stable ID, title, source organization, source URL, language, crop/topic, district/state scope, season, publication/effective date if known, last-verified date, passage, and reviewer/status. Keep original Kannada/English when available and note whether translation is human-reviewed.
3. **Use simple retrieval first.** For the initial bounded corpus, implement deterministic keyword/BM25 or database full-text search with crop/topic/language/region filters. Add hybrid/vector retrieval only if a labeled evaluation set shows keyword misses relevant Kannada/code-mixed questions. Do not add an embedding service or vector database solely because “RAG” is fashionable.
4. **Retrieve evidence before generation.** Send only the current question, necessary context, and top relevant approved passages to the answer composer. Keep retrieval results distinct from conversation history and from scheme decisions.
5. **Require claim/source linkage.** Return a typed response containing reply text plus citations referencing only retrieved source IDs. Render citation title, publisher, link, scope, and “last checked” date beside the answer/card. Do not let the model create URLs or source titles.
6. **Validate grounding.** Check that every source ID exists in the retrieved set and is applicable to the answer's crop, location, and season. If evidence is weak, stale, conflicting, or out of scope, abstain or ask a clarification; never backfill with model memory.
7. **Separate evidence classes.** Label source-backed general advice, deterministic rule-backed scheme screening, and unverified/general information distinctly. Scheme screening remains preliminary and is never represented as government approval.
8. **Version content.** Keep ingestion/review dates and change history; stale content must be flagged and excluded or shown with an explicit stale warning according to a documented policy.
9. **Prevent corpus poisoning and prompt injection.** Treat retrieved source text as untrusted data, not instructions. Curate/import content through a controlled process; limit supported file types; validate source URLs and provenance; do not allow documents to grant the model tools or privileges.

### 3.4 Accuracy and safety evaluation

Create a small reviewed regression set before changing prompts or retrieval. It should include:

- The exact “gomugomu” sequence; ambiguous name; confirmed amla; unknown crop; typo; transliteration; Kannada and code-mixed forms.
- “neptune” as invalid district; a real Karnataka district; district-specific question with no district evidence.
- “munja” or other non-answer while the assistant has a pending question.
- Irrigation/soil/dosage/variety questions with enough, insufficient, stale, and conflicting evidence.
- Follow-up turns, topic changes, repeated user facts, and relevant vs irrelevant follow-up tests.
- Scheme eligibility positive, negative, missing-field, conditional, outdated, and out-of-scope cases. Confirm generated wording cannot change engine output.
- Prompt injection in user text and retrieved passages; malicious-looking links; unsupported answer requests.
- English, Kannada, transliteration, dialect variants, noisy/misrecognized voice transcripts.

Measure and retain a baseline for:

- Crop identity precision and clarification rate (unknown/ambiguous names must not silently map).
- Retrieval recall on the reviewed set; citation validity and claim-support rate.
- Unsupported factual claim rate; abstention correctness when evidence is absent/stale.
- Scheme result agreement with the deterministic rule engine (must be exact).
- Follow-up relevance, duplicate/repeated answer rate, and response language.
- p50/p95/p99 latency, timeout/error rates, and cost per text/voice turn.

Have a Kannada-speaking agricultural subject-matter reviewer validate reference answers and citations. Do not treat an LLM grader alone as proof that citations support claims.

## 4. Privacy, accounts, and “only a user can view their data”

### 4.1 Identity and authorization requirements

Authentication answers “who signed in?” Authorization answers “may this identity access this record?” Both are required.

- Use an established, maintained identity implementation/provider; do not hand-roll passwords, OTP, session signing, or JWT validation.
- If no identity provider is already configured, choose and document one deliberately. Keep provider secrets in deployment secret storage. Do not enable server-side personal chat/profile persistence until real identity configuration is complete.
- The backend must derive `user_id` only from a verified server-side session/token. Never trust a client-provided `user_id`, `owner_id`, conversation ID, or profile ID as proof of ownership.
- Every read/write/list/export/delete endpoint must scope the query to the authenticated owner. Use an unguessable record ID as defense in depth, not as authorization.
- Return no record data for unauthenticated requests. Return a consistent not-found/forbidden response for another user’s records without revealing that a record exists.
- Ensure the same owner check applies to voice, text, history, profile, export, delete, background jobs, and any admin/support path.
- Add database constraints and indexes for ownership. Consider Postgres row-level security as defense in depth; configure the application role and policies correctly, including table-owner/RLS bypass pitfalls. RLS does not replace endpoint authorization.
- Use a server-side session with rotation on login/privilege change and logout/revocation. For browser cookies use `HttpOnly`, `Secure` in production, an appropriate `SameSite` policy, narrow path/domain, expiry, CSRF protection for state-changing requests, and origin checks. Do not put long-lived bearer tokens in localStorage.
- Enforce account recovery securely, rate-limit authentication, avoid user enumeration, and record minimal security events without sensitive content.

### 4.2 Ownership tests (release blockers)

Automated integration tests must create Alice and Bob and prove:

1. Alice can create/list/read/update/export/delete Alice’s conversations and profile.
2. Bob cannot read/list/update/export/delete Alice’s records even if he knows or guesses their identifiers.
3. An unauthenticated request cannot read or mutate either user’s data.
4. Changing `owner_id`/`user_id` in a request body or query has no effect.
5. List endpoints never return another user’s records; pagination/counts do not leak cross-user data.
6. Logout/revocation makes the old session unusable.
7. Delete removes the user-visible data and is reflected in backups/retention policy or the user-facing notice accurately explains the deletion timeline.

Do not launch persistent multi-user chat until these tests pass.

### 4.3 Chat/audio storage and user controls

- State the default clearly. Recommended default: save text chat only when the user explicitly enables history; do not retain raw audio after transcription unless a specifically justified, consented feature requires it.
- Provide “New chat,” “Delete chat,” “Delete all,” “Export my data,” and sign-out controls. Show saved/unsaved status and retention period.
- Use server-side persistence only for authenticated accounts. Browser-local history may be offered as a separate mode, with a shared-device warning and clear wipe controls.
- Store minimum necessary personal data. Avoid Aadhaar, bank credentials, exact location, land records, or names unless truly needed for the chosen feature.
- Define retention and automated deletion for active data, logs, backups, and provider copies. Document what deletion can/cannot remove after a third party processes a request.
- Keep raw audio out of application logs, analytics, crash reports, and persistent storage by default. Redact transcripts and personal facts from traces.
- Protect backups and database snapshots; deletion policy must include their expiry/restoration process.

### 4.4 Voice notice and consent UX

Before recording begins, show a clear, accessible notice in Kannada and English. Separate it from the browser microphone permission prompt and from general Terms of Service. Make typed chat available as an alternative.

The notice should state, after provider review:

- Microphone audio is recorded for this turn and whether any copy is stored by Krishi Mitra.
- Which provider receives audio for transcription (currently Sarvam); which receives transcript/context for answer generation (currently Groq); which receives reply text for speech generation (currently Sarvam).
- Purpose, data categories, retention/deletion, relevant provider processing/retention, support contact, and how to withdraw/stop voice use.
- Chat history is not saved by default today; if that changes, describe the optional setting and retention separately.
- Do not speak Aadhaar, bank credentials, or other unnecessary sensitive information.

Example starting copy (must be checked against actual vendor contracts/configuration and translated/reviewed):

> **Before using voice:** Krishi Mitra records this message and sends it to Sarvam to transcribe. The transcript and recent chat context are sent to Groq to create a response. If spoken output is enabled, response text is sent to Sarvam to generate speech. Krishi Mitra does not save the recording or chat history on its server by default. Service-provider processing may be subject to their current terms. You can use typed chat instead. Do not share account numbers, Aadhaar numbers, or passwords.  
> **[Continue with voice] [Use text instead] [Privacy details]**

Do not publish the sample unchanged. Confirm current processor terms, locations, retention, training use, subprocessors, deletion, contractual safeguards, and breach processes first.

### 4.5 DPDP implementation checklist

Review the Digital Personal Data Protection Act, 2023, DPDP Rules, 2025, commencement notifications, amendments, and applicable exemptions with India privacy counsel. Do not infer the effective date of each obligation from the Act’s publication date alone.

Engineering/product readiness should include:

- A data inventory/data-flow diagram covering audio, transcripts, account identifiers, farm profiles, chat history, logs, backups, and each processor.
- Purpose limitation and minimization; a plain-language notice and specific, affirmative consent where required; separate optional consent for history/analytics.
- Consent receipt/version/time and withdrawal handling, with no silent re-consent.
- Data principal request workflow for access, correction, erasure, grievance, and other applicable rights.
- Retention/deletion schedule, security safeguards, breach response, vendor/processor agreements, and access review.
- Appropriate handling of children’s data and guardian consent where legally required; do not target children or use behavioral tracking without legal review.
- A named grievance/contact route and operational owner for requests.
- Kannada and English notices tested with actual users for comprehension and accessibility.

Consent UI is not by itself legal compliance. Product data flows, contracts, retention, security, and operational procedures must match what the notice promises.

## 5. Cybersecurity and AI safety controls

Use OWASP ASVS as a web-app verification checklist and OWASP GenAI guidance for AI-specific threats. Minimum engineering controls:

- HTTPS in production; secure cookies; validated origins; CSRF protections for cookie-authenticated mutations; strict CORS allowlist.
- Server-side input validation, request-size/time limits, safe output rendering, parameterized database access, and safe URL handling.
- Authentication/authorization checks on every object request; least-privilege database/application accounts; separate dev/test/prod credentials.
- Rate limits and abuse controls for login, chat, voice, uploads, and expensive provider calls; concurrency limits and bounded retries.
- Secrets in environment/secret manager only; rotate exposed credentials; never ship provider secrets to browser code; redact logs and errors.
- Dependency pinning/updates, vulnerability scanning, secure headers, backup encryption, tested restore, and documented incident response.
- Do not log prompts, personal data, raw audio, model responses containing sensitive facts, or authorization tokens. Keep request IDs and aggregate performance metrics.
- Treat user text and retrieved documents as untrusted input. Retrieval is not a trusted instruction channel. Do not give the LLM tools that can access private data or mutate accounts.
- Enforce a strict output schema. Validate all citations server-side against the retrieved set. Escape content rendered in HTML; never render model-provided HTML.
- Preserve clear model/provider error states. No broad catch that converts a provider failure into a fabricated success response.

## 6. Offline capability

Keep the current online experience intact and describe offline support as a separate tier:

1. **Online:** Current cloud providers available.
2. **Limited offline:** Local deterministic scheme screening and cached, reviewed reference content. Show content age and disable or qualify time-sensitive claims.
3. **Full offline voice (future):** Local Kannada ASR, local answer model or retrieval-only guidance, and Kannada TTS. Test model memory, device requirements, dialect/noise accuracy, latency, license, and update size on target devices.

Do not silently substitute a weak offline model. If the user is offline and a capability is unavailable, state that explicitly and offer the limited local features. Syncing locally saved personal conversations later must be opt-in and must use the authenticated account’s ownership rules.

## 7. Deployment and scale

### 7.1 Safe deployment target

Use an incremental deployment, not a destructive rewrite:

- Keep the existing local demo launch path working for development.
- Introduce a production ASGI/API entrypoint and container configuration as an additive path. Preserve route behavior and response shapes or version any intentional changes.
- Terminate TLS at a managed HTTPS proxy/load balancer; run app workers as a non-root user; use health/readiness checks, startup/restart policy, and graceful shutdown.
- Use PostgreSQL for authenticated persisted records, migrations, encrypted backups, and least-privilege database roles. Use a shared cache/queue only where measured need exists.
- Use a managed secrets store for production keys. Do not commit `.env`, secrets, generated user data, or model weights without license review.
- Separate dev/staging/prod, use staging migrations and smoke tests, and maintain rollback instructions.
- Add monitoring for latency/errors/provider timeouts/queue depth/DB pool/CPU/memory and costs, with content-redacted metrics.

### 7.2 Define what “1,000 users” means

Record separate targets for 1,000 registered accounts, daily active users, and peak concurrent text/voice turns. Model realistic traffic. Each voice request may use transcription, LLM, and TTS providers, so provider quota/concurrency may be the limiting factor, not Python request handling.

Before claiming capacity:

- Load-test the deployed staging stack with realistic text/voice proportions and burst patterns.
- Test external provider throttling, slow responses, provider outage, DB saturation, queue backlog, and retry behavior.
- Measure p50/p95/p99 end-to-end and per-stage latency, errors, resource use, provider quotas, queue wait, and cost.
- Set explicit service objectives based on the results and capacity-plan with headroom.
- Keep a degraded mode: typed chat or deterministic local lookup when voice providers are overloaded; never fabricate success.

Worker count is not a capacity proof. Run load tests against the actual deployment and actual external dependencies.

## 8. Bounded orchestration (not an agent swarm)

Keep orchestration explicit, typed, and auditable:

```text
Consent/auth gate
  -> input validation + language/intent detection
  -> crop-name resolution (clarify if ambiguous)
  -> retrieve approved evidence (when factual advice needs it)
  -> deterministic scheme evaluator (scheme queries only)
  -> answer composer with schema-bound claim/citation output
  -> citation/policy validation and safe abstention
  -> optional TTS only after user chose voice output
  -> redacted metrics and consent-aware persistence
```

The current app is a fixed pipeline, not autonomous multi-agent orchestration. Do not add autonomous agents for scheme eligibility. If future specialist components are introduced, each needs typed schemas, least-privilege access, timeout/failure handling, trace IDs, and end-to-end tests. A simpler sequential workflow is preferable unless evaluation demonstrates a measurable benefit.

## 9. Backward-compatible implementation sequence

Implementation should be staged and deployable in small slices. Stop and report if a stage requires an unavailable provider account, legal decision, secret, or destructive migration.

### Stage 0 — Baseline and safety

- Inspect dirty worktree first and preserve unrelated/uncommitted user changes.
- Read `.gsd/STATE.md`, project docs, current routes, data format, requirements, and tests.
- Run existing tests and record baseline.
- Verify `.env` is ignored and not tracked without printing any secret value; rotate the credential identified in the credential safety note.
- Add no breaking changes or new provider dependencies at this stage.

**Gate:** Existing tests pass before feature work; secrets are rotated and excluded.

### Stage 1 — Dialogue correctness (crop path only)

- Implement explicit crop aliases/ambiguity handling and structured clarification state.
- Handle unclear responses as not understood; preserve pending question.
- Remove unrelated acreage prompts from generic fruit/crop fact answers.
- Avoid local-specific claims unless evidence carries the location scope.
- Keep scheme route and existing profile extraction behavior unchanged where tested.

**Gate:** New conversation regressions pass; existing tests and sample smoke flows pass.

### Stage 2 — Curated knowledge base and citations

- Add a small versioned source catalogue and retrieval with no vector DB initially.
- Build typed citation metadata and optional response fields to preserve current clients.
- Add grounded answer instructions, citation validation, stale/out-of-scope abstention, and safe fallback.
- Seed only reviewed facts with real source links; do not manufacture crop-specific data.

**Gate:** Every displayed citation resolves to a retrieved record and supports the claim; unsupported test questions abstain; scheme statuses remain unchanged.

### Stage 3 — Authenticated, private history

- Pick/configure a maintained identity provider; do not ship fake identity or insecure demo auth.
- Add migrations and owner-scoped conversation/profile APIs. Derive owner from verified auth server-side.
- Add consent-aware history UI, export/delete, logout, retention, and data inventory.
- Add cross-user access-control integration tests before enabling persistence.

**Gate:** Alice/Bob/anonymous authorization tests pass on all personal-data endpoints. Without provider configuration, server persistence remains disabled and only clearly labeled local demo behavior is available.

### Stage 4 — Voice notice, consent, and provider review

- Verify actual provider contractual/privacy behavior and supported data processing settings.
- Implement just-in-time Kannada/English voice notice, typed alternative, consent version/withdrawal, and retention/deletion behavior.
- Do not claim zero vendor retention unless contract/configuration proves it.

**Gate:** Notice accurately matches measured data flow; consent is not conflated with browser mic permission.

### Stage 5 — Production deployment

- Add production ASGI/container/proxy/DB configuration while retaining the existing local demo launcher.
- Add migrations, health checks, secure settings, environment validation, logs/metrics redaction, backups, and smoke tests.
- Add staging deployment and rollback guide; do not include live credentials.

**Gate:** Existing demo works; production smoke test passes; no secrets are present in client assets/logs.

### Stage 6 — Offline and capacity evidence

- Add explicit limited-offline behavior; benchmark local speech/model options before full offline claims.
- Define workload and run staging load tests for text and voice.
- Publish a capacity statement that names tested concurrency, hardware, provider quotas, p95 latency, and limitations.

**Gate:** No “1,000 concurrent” claim without test evidence; offline mode displays capability and freshness accurately.

## 10. Acceptance criteria

The plan is complete only when:

- Unknown/ambiguous crop names trigger clarification; no unsupported crop mapping occurs.
- Unclear input is recognized as unclear, and the dialogue does not repeat a prior answer or ask an unrelated question.
- Crop advice is grounded in relevant, current sources or safely abstains. Citations are valid and claim-linked.
- Scheme decisions still come solely from the deterministic evaluator, with exact agreement between API result, card, and spoken wording.
- Chat history is not persisted without user choice; if persisted, every record is owner-scoped and Alice/Bob tests prove isolation.
- Voice processing notice accurately names the configured providers, purposes, and storage/retention behavior; typed mode remains available.
- User can view/export/delete their own data and cannot access another user's data.
- Existing local demo and regression tests continue to work after additive production changes.
- Deployment is HTTPS-enabled, secrets are externalized, logs are redacted, and operational failures are explicit.
- Capacity and offline claims match measured test results.

## 11. Research sources

Reviewed on 2026-10-31. Official pages may block automated retrieval; consult current primary text and counsel for legal applicability.

### India privacy and legal framework

- Ministry of Electronics and Information Technology, [Data Protection Framework](https://www.meity.gov.in/data-protection-framework) — official entry point for the Act and Rules.
- Government of India, [India Code](https://www.indiacode.nic.in/) — authoritative legislation portal; search *Digital Personal Data Protection Act, 2023* and related Rules/notifications.
- This research did not independently verify every current commencement notification or provider contractual term. Resolve that before production; do not use this document as a compliance certification.

### Identity, authorization, security

- OWASP, [Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/) — testable web application security requirements.
- OWASP, [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — deny by default, check authorization on every request, and avoid relying on obscurity.
- OWASP, [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) — secure session lifecycle and cookie handling.
- OWASP, [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — password hashing guidance if a password-based system is deliberately selected; prefer a maintained identity provider rather than custom auth.
- OWASP, [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) — protections for cookie-authenticated state-changing requests.
- PostgreSQL, [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) — database-level row policies and important owner/BYPASSRLS caveats.
- OWASP GenAI Security Project, [LLM Top 10](https://genai.owasp.org/llm-top-10/) — LLM/agent security risks and mitigations.

### AI quality, retrieval, offline, deployment

- Microsoft Learn, [RAG with Azure AI Search](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview) — retrieval, grounding, citation/provenance, latency, and security considerations.
- NIST, [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) and [Generative AI Profile](https://doi.org/10.6028/NIST.AI.600-1) — voluntary AI risk-management guidance.
- NIST, [Privacy Framework](https://www.nist.gov/privacy-framework) — voluntary privacy-risk management framework.
- [`whisper.cpp`](https://github.com/ggml-org/whisper.cpp) — local CPU/GPU/on-device Whisper inference examples; this does not establish Kannada dialect accuracy or provide Kannada TTS.
- FastAPI, [Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/) and [Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/) — HTTPS, lifecycle, replication and worker considerations; neither is a capacity guarantee.
- Google, [Gemini API documentation](https://ai.google.dev/gemini-api/docs) — product documentation only; Gemini Argon feature availability is determined by the user’s actual coding environment.

## 12. Master prompt for Gemini Argon

Copy the prompt below into Gemini Argon after opening the Krishi Mitra repository. Keep the code repository available to the model, but **do not paste `.env`, API keys, access tokens, database URLs with credentials, or production data**. Rotate the credential previously exposed in the IDE selection before deployment.

```text
You are the principal engineer implementing judge-readiness and production hardening for the existing Krishi Mitra repository. Work directly in the current repository. The goal is to deliver working, tested improvements without breaking the existing demo or deterministic scheme engine.

IMPORTANT OPERATING RULES
1. Begin by reading the repository's actual project state and current code. Read .gsd/STATE.md if present (the repository may use .gsd rather than .planning), README, architecture/product docs, current routes, data files, dependency manifests, and tests. Do not assume this plan exactly matches the current branch.
2. Run `git status --short` first. Do not discard, overwrite, reformat, or revert unrelated user changes. Integrate around dirty files. Do not run destructive git commands. Do not commit unless explicitly requested.
3. Never print, reveal, copy, transmit, or commit secret values. Do not open or output `.env` contents. You may check whether expected variable names are configured without displaying values. If a key might have been exposed, tell the user to rotate it; do not repeat it.
4. Establish and record a baseline by running the existing tests and local smoke flow before editing. If baseline tests fail, distinguish pre-existing failures from changes and do not conceal them.
5. Make incremental, backward-compatible changes. Keep the current local demo entry point and existing route response contracts working. Add optional fields rather than removing/renaming existing fields. Preserve deterministic scheme decisions exactly. No unrelated cleanup.
6. Do not claim zero hallucinations, legal compliance, full offline support, or 1,000-user capacity without direct evidence. Report measured results and remaining setup honestly.
7. Do not fabricate agricultural facts, source URLs, provider retention claims, legal requirements, or test results. A citation must refer to a real, reviewed source record.
8. Use maintained libraries and official documentation. Do not hand-roll cryptography, password storage, OTP, JWT verification, or session security.
9. If a mandatory external setup (identity provider, DB, SMTP, cloud secrets, legal determination) is unavailable, implement a fail-closed integration/configuration path and document the exact user action. Do not fake successful authentication, consent, persistence, or provider behavior.
10. Do not store or log raw audio, transcripts, private chat text, auth tokens, or secrets by default. Avoid sending personal data to new providers without documented need and disclosure.

REQUIRED FIRST REPORT
Before changing files, report:
- actual project architecture, current scope/state, relevant APIs, current data flow, and key tests;
- baseline test results and dirty worktree files;
- which pieces of this plan are already implemented;
- any conflict between the plan and the current repository.
Then proceed autonomously on safe, additive work. Ask the user only if a decision or external credential truly blocks a secure implementation. Do not remove working functionality to avoid asking.

PRODUCT REQUIREMENTS
A. Ambiguous crop names and conversation quality
- The user phrase “gomugomu” must not silently be treated as Indian gooseberry/amla. If no verified alias uniquely matches, ask the farmer to clarify before giving crop-specific facts. Provide likely interpretations only as options, not as a conclusion.
- An unclear reply such as “munja” while a question is pending must be treated as unclear. Acknowledge it and ask for repetition/clarification; do not repeat the prior answer or ask about acreage unrelated to the original question.
- Preserve dialogue topic/pending clarification and avoid asking for already-known facts. Ask at most one relevant follow-up; do not assert local (e.g. district-specific) suitability without location-scoped evidence.
- Add focused regression tests for ambiguous, unknown, confirmed, misspelled, transliterated, Kannada, English, code-mixed, invalid district, unclear answer, topic change, and relevant/irrelevant follow-up cases.

B. Safe, useful grounded answers
- Create a small, versioned, manually curated knowledge base using real authoritative agricultural sources. Each record must include stable ID, title, publisher, URL, language, crop/topic, district/season scope if applicable, publication/effective date if available, last reviewed date, passage/fact, and review status.
- Do not fabricate or bulk-import unsupported facts. If no reviewed sources exist for an answer, ask for clarification or abstain and explain that local verification is needed.
- Start with simple keyword/full-text/BM25 retrieval and filters over the small local corpus. Do not add a vector database, embeddings provider, or complex framework unless a measured test shows it is needed.
- Retrieve evidence before generation. Keep user conversation history separate from factual evidence. Treat retrieved documents and user text as untrusted data, never as instructions.
- Add optional, schema-validated citation metadata referencing only retrieved source IDs. The server must validate citations; the model must never invent a URL/title. Show source title, issuer, link, scope, and last-reviewed date in the UI.
- Fail safely on stale, contradictory, low-relevance, or out-of-scope evidence. No unsupported dosage/rate/deadline/eligibility claims.
- Keep scheme eligibility exclusively in the existing deterministic rule engine. Test exact agreement for every scheme status. The LLM may summarize rule output but may not change it or call it official approval.
- Preserve the existing UI/API shape and add citations as optional fields until all clients support them.

C. Auth, ownership, private history, and user data
- First look for existing identity/auth. Reuse an existing maintained provider if present. If none exists, do not invent a provider or implement custom password/OTP/JWT security. Add a standard OIDC integration/configuration using a maintained library, document required issuer/client/secret configuration, and fail closed until configured. Do not enable server-persisted personal chats/profiles under a shared anonymous identity.
- The server must derive the account/user ID only from verified server-side authentication. Ignore/reject client-supplied owner IDs. Every conversation, profile, list, export, update, and delete operation must enforce ownership at the data access boundary.
- Use a secure server-side session or correctly verified OIDC flow, secure HttpOnly cookies in production, appropriate SameSite/Secure settings, session expiry/rotation/revocation, CSRF protection on mutations, origin checks, auth rate limits, and logout. Never store long-lived auth tokens in localStorage. Do not expose provider/API secrets to browser JS.
- If PostgreSQL is used, add migrations, ownership constraints/indexes, least-privilege roles, and optionally Row Level Security as defense in depth. Understand/test table owner and BYPASSRLS behavior; RLS does not replace API checks.
- Add “new chat,” opt-in history, export, delete one/all, sign-out, retention, and visible saved/unsaved state. Do not retain raw audio by default. Avoid collecting Aadhaar/bank credentials or other unneeded sensitive data.
- Add integration tests for Alice/Bob/anonymous: each account can only read/write/list/export/delete its own records, guessed/known foreign IDs do not expose data, client owner-ID changes have no effect, logout revokes the old session, and no unauthenticated access is allowed. These are release blockers.
- If identity provider configuration is unavailable, keep personal server persistence disabled and the existing demo working. Do not simulate a secure user.

D. Voice privacy and consent
- Add an accessible just-in-time Kannada and English notice before recording, separate from browser mic permission and Terms. Keep typed chat as a real alternative. Do not record before affirmative user action/consent.
- Describe only verified processing: current intended flow is audio to Sarvam for transcription, transcript/recent context to Groq for response generation, and response text to Sarvam for speech synthesis. Verify current contracts/settings, retention, training use, subprocessors, location/transfer and deletion before making claims. If not verified, disclose uncertainty and leave the feature/configuration clearly documented.
- Explain purpose, data categories, whether our app stores audio/history, retention/deletion, processors, withdrawal/help contact, and avoid speaking Aadhaar/account details. Save a consent-version/event only as legally and operationally appropriate.
- Do not represent a Terms checkbox or browser mic permission as sufficient privacy consent. Do not bundle optional history/analytics consent with voice.
- Create a data-flow inventory, retention/deletion rules covering DB/logs/backups/provider copies, rights/grievance workflow, incident plan, and a clear counsel-review TODO. Do not claim DPDP compliance without legal review of the Act, Rules, commencement notifications, amendments, and actual deployment.

E. Security baseline
- Follow OWASP ASVS and OWASP GenAI defensive guidance: HTTPS deployment, secure headers/cookies, strict CORS, CSRF controls, server-side authorization on every request, parameterized DB operations, input/request size limits, timeout/rate limits, dependency hygiene, secret management, redacted logs, least privilege, backups/restore, error handling, and safe HTML rendering.
- Treat prompt injection as untrusted input. Do not give the LLM unrestricted tools, database access, user identity authority, or permission to mutate data. Validate output schema and every citation server-side.
- Avoid broad exception catches/success-shaped fallbacks. Provider failure must be explicit, with a truthful limited fallback.
- Add security tests for cross-user access and auth/consent handling. Do not produce exploit steps or run offensive tests against systems outside this local repo.

F. Offline behavior
- Clearly label Online, Limited Offline, and Offline Voice Unavailable states.
- Ensure limited offline mode uses only local deterministic rules and reviewed local content, with freshness indicators and safe behavior for unsupported questions.
- Do not claim full offline unless Kannada ASR, answer/retrieval, and TTS all work locally on target hardware. If exploring whisper.cpp or another local stack, benchmark Kannada dialect/noisy audio accuracy, memory, latency, license, model distribution, and Kannada TTS separately.
- Do not silently downgrade to a less reliable model. Explain unavailable capability and let the farmer use the supported typed/local feature.

G. Deployment and scale
- Preserve current local demo. Add a separate production entrypoint/container path rather than destructively replacing the existing server.
- Use production ASGI/API server, HTTPS reverse proxy/managed TLS, non-root container, health/readiness checks, graceful shutdown, restart policy, externalized secrets, separated dev/staging/prod settings, DB migrations, encrypted backups, restore instructions, and rollback/smoke tests.
- Use PostgreSQL for authenticated saved records if persistence is implemented. Add cache/queue only when measurements justify it. Keep service instances stateless; never cache personalized answers across users.
- Document which deployment variables are required by name only, without values. Provide safe example env template.
- Define whether “1,000 users” means registered users, daily active users, or concurrent text/voice requests. Do not claim 1,000 concurrent users without staged load test against the actual deployment and provider quotas.
- Load test realistic text/voice mix, bursts, slow/outage providers, DB/queue saturation, and retries; report p50/p95/p99, errors, CPU/memory, queue, provider quotas, and cost. Add quotas/timeouts/backpressure and honest degraded mode.

H. Orchestration
- Document the real current flow as a bounded pipeline, not a multi-agent swarm.
- Implement/retain explicit stages: consent/auth -> validate/language/intent -> crop resolution/clarification -> retrieve approved sources -> deterministic scheme rules if relevant -> response compose -> citation/policy gate -> optional TTS -> consent-aware storage and redacted metrics.
- Use typed inputs/outputs, trace/request IDs, clear timeout/failure behavior, least privilege, and tests. Do not add autonomous agents unless there is demonstrated measurable benefit. Scheme decisions may never be delegated to an LLM.

IMPLEMENTATION SEQUENCE
1. Baseline inventory and tests. Preserve dirty files.
2. Dialogue correctness for crop ambiguity and unclear answers.
3. Curated source records, retrieval, citations, abstention, and evaluation set.
4. Authenticated ownership-scoped history, privacy UI, deletion/export/retention. Keep persistence disabled until auth is real.
5. Voice notice/consent and provider contract/data-flow verification.
6. Additive production deployment path and operational controls.
7. Limited offline mode; prototype full offline only after measured target-device validation.
8. Staging load tests and capacity report.

After each stage, run the smallest relevant tests plus the complete existing backend test suite. Do not proceed past a failed regression without identifying/fixing the cause. Keep code changes surgical and update directly related docs.

REQUIRED FINAL VERIFICATION
- Run `python -m unittest backend.test_rules backend.test_web_server -v` (or the current repository's documented equivalent).
- Run new focused tests for dialogue ambiguity, evidence/citation validation, scheme invariance, authentication and cross-user ownership.
- Test the current local app’s typed and voice paths where provider configuration allows; report unavailable secrets/providers rather than faking success.
- Verify no current API secrets are in tracked files, static assets, logs, tests, or the generated documentation. Do not print secret values.
- Verify citation links and IDs are real and map to reviewed records.
- Verify no change broke the existing demo launcher, existing scheme UI/API, or fallback behavior.
- If production infrastructure/provider credentials are unavailable, clearly list what remains and do not claim production readiness.
- Provide a concise change summary, exact files changed, tests run and results, deployment/setup steps, legal/vendor items requiring human review, measured performance (if load-tested), and risks not resolved. Do not commit.

Start with the REQUIRED FIRST REPORT. Then execute in the sequence above, preserving the existing system. If the request is too large to complete safely in one context, complete the highest-priority verified slices, leave the rest as explicit blocked/setup tasks, and never mark unfinished security/privacy work as complete.
```

## 13. Implementation expectation

The “one shot” prompt is designed to make Gemini inspect, implement, and verify in one working session, but secure identity-provider setup, legal review, provider contract review, production credentials, and load-test infrastructure may require human actions. The correct result when those are unavailable is a tested, fail-closed implementation with explicit setup steps—not a mock login, fabricated compliance statement, or unverified deployment claim.
