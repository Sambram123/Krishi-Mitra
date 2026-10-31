# Later Workstreams — Focused Research

**Researched:** 2026-10-31  
**Scope:** Follow-on research for curated-corpus RAG/citations, private authenticated history, voice processing disclosure/vendor terms and DPDP research limits, production/capacity, and Kannada offline ASR/TTS.  
**Status:** Research only. No application code, dependencies, state, roadmap, or existing research files were changed. No `.env` was inspected; no package was installed and no tests or load/model benchmarks were run.

## Phase boundary

`.gsd/STATE.md:8-17` says, verbatim, “**Phase**: 1 (Completed)” and “**Status**: Ready for Phase 2 (Text-to-Text Conversational Prototype).” This artifact is an addendum for later workstreams, not an expansion of immediate Phase 2. Phase 2 should remain the dialogue-correctness slice; do not make persistence, RAG, provider/privacy claims, production deployment, load tests, or offline speech part of its acceptance criteria. [VERIFIED: `.gsd/STATE.md:8-17`]

## Live implementation facts relevant to later work

The current web client sends the voice recording and recent chat context to the backend:

```javascript
const result = await postJson('/api/voice-turn', {
  audio: await blobToBase64(blob),
  mime_type: mimeType,
  recording_duration_ms: recordingDurationMs,
  language: currentLanguage,
  profile,
  history: recentChatHistory(),
});
```

[VERIFIED: `web_app.js:463-469`; verbatim source excerpt above]

The backend sends audio to Sarvam transcription, adds recent history to the Groq request, and sends the generated reply to Sarvam speech synthesis. The source values are:

```python
model="saaras:v4"
chat_messages.extend(history)
model="bulbul:v4-flash"
```

[VERIFIED: `backend/web_server.py:763-765,849,874-876`; verbatim values above]

The handler’s explicit POST branches are `"/api/chat"`, `"/api/evaluate"`, and `"/api/voice-turn"` [VERIFIED: `backend/web_server.py:963-971`; verbatim: `if route == "/api/chat":`, `elif route == "/api/evaluate":`, `elif route == "/api/voice-turn":`]. The inspected handler does not implement login, persistent-history, or owner-scoped record routes; this is a finding about the inspected route code, not a claim about every possible deployment component. The current local server is started with `server = ThreadingHTTPServer(("127.0.0.1", port), KrishiMitraHandler)` [VERIFIED: `backend/web_server.py:1010`; verbatim source line].

## 1. Curated corpus RAG and citation correctness

**Recommendation:** Start with a reviewed, versioned corpus and lexical retrieval, not a vector database. SQLite FTS5 is a full-text-search module with ranking support; SQLite documentation also makes FTS5 availability dependent on how SQLite was built, so check the actual runtime build before selecting it. [CITED: [SQLite FTS5](https://www.sqlite.org/fts5.html), overview/ranking and “Compiling FTS5” sections]

### Source record and retrieval contract

Maintain one source record per citable passage (plus a document-level record), with:

- Stable `source_id` and `passage_id`; title; publisher/issuing body; canonical URL; jurisdiction and source type.
- Original language and passage text; translation text plus human-review status when applicable; crop/topic tags; geographic scope; season; publication/effective dates where available.
- Rights/permission basis, ingestion date, last-verified date, source version/hash, review status (`draft`, `reviewed`, `stale`, or `superseded`) **[ASSUMED: proposed statuses, not existing repository enum values]**, reviewer role, and update owner.

These are recommended schema fields, not existing repository types. Use only material the project is permitted to reproduce; have an agricultural reviewer confirm the passage, translation, jurisdiction, and freshness. A named project maintainer should own the source register and update queue; a qualified agriculture reviewer should approve advice content. Do not auto-promote scraped or model-generated text into the reviewed corpus. [Recommendation grounded in the cited SQLite retrieval boundary and the project’s existing later-stage plan: `krishi_mitra_complete_improvement_plan.md:66-79`.]

Apply status, crop/topic, location, season, and language filters before ranking. Begin with FTS5 lexical retrieval over reviewed original-language and human-reviewed translated terms, plus a small, curated alias/synonym map for Kannada and transliteration. Measure Kannada-script, transliteration, and code-mixed recall separately; do not assume a tokenizer or English-centric search handles Kannada adequately. Add hybrid/vector retrieval only if the labeled evaluation shows repeatable misses and a chosen embedding path has acceptable language coverage, cost, rights, and operational dependencies.

The answer model may return text and `citation_ids`, but the server must resolve every displayed title, URL, publisher, scope, and checked date from the retrieved records—not from model-generated strings. Reject any citation ID that was not in that request’s retrieval set; reject stale, unreviewed, conflicting, or out-of-scope evidence and abstain or ask a clarifying question. This validates citation identity and scope, **not** whether a citation actually supports each sentence. Require qualified human review for claim-level support. Keep the deterministic scheme evaluator as the sole scheme eligibility authority.

### Evaluation and update gate

Build a reviewed query set spanning crop/topic, Kannada script, transliteration/code-mix, location/season scope, stale/conflicting evidence, prompt-injection text in source passages, and questions with no evidence. Track separately:

- Retrieval `Recall@k`/`Hit@k` (and rank quality such as MRR or nDCG) by language and query type.
- Citation-ID validity and citation scope correctness; human-adjudicated claim-support and citation-completeness rates.
- Correct abstention for insufficient, stale, conflicting, or out-of-scope evidence; unsupported factual claim rate.
- Regression invariance of deterministic scheme results.

Set numeric release thresholds only after establishing a human-reviewed baseline; a syntactically valid citation is not evidence of a grounded answer. Re-review source changes on a documented cadence and when an issuing body changes guidance; automatically mark expired/replaced evidence stale until reviewed. [Evaluation design is a recommendation; FTS5 capabilities are cited above.]

## 2. Authenticated private chat history and Alice/Bob isolation

**Recommendation:** Keep server-side history disabled until a real OIDC identity configuration, server-derived principal, persistence, retention/deletion rules, and the tests below are in place. Authentication establishes identity; authorization separately checks whether that identity may act on a particular record. OWASP recommends least privilege, deny-by-default, and tests for mapped permissions. [CITED: [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)]

Use a maintained OIDC implementation/provider and a server-managed session. On successful OIDC validation, derive the application principal from the verified issuer and subject (`iss`, `sub`) and map that pair to an immutable internal user ID; never accept `user_id`, `owner_id`, profile ID, or conversation ID as identity proof. OIDC is the identity layer on OAuth; use the current OAuth 2.0 Security BCP for protocol choices. [CITED: [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html); [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700)]

For every conversation/profile read, list, create, update, export, delete, text turn, and voice turn, apply ownership in the server-side database operation. Example shape: `SELECT ... FROM conversations WHERE id = :id AND owner_id = :authenticated_user_id`. Set owner fields from the authenticated principal on create. Use opaque IDs only as defense in depth. With cookie sessions, use secure cookie attributes, rotation/expiry/revocation, CSRF defenses for state-changing requests, and origin validation; OWASP notes cookies are automatically sent by browsers and requires backend CSRF validation for state-changing requests. [CITED: [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html); [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)]

If PostgreSQL is selected, consider row-level security as defense in depth, but test with the actual application DB role: PostgreSQL documents that table owners and roles with bypass privileges can bypass row policies by default. Keep endpoint-level authorization regardless. [CITED: [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)]

### Required integration tests (release blockers)

Create Alice, Bob, and an anonymous client with isolated records and test the actual API/database path:

1. Alice can create, list, read, update, export, and delete Alice’s conversations and profile.
2. Bob cannot read/list/update/export/delete Alice’s records—even with a known record ID—and receives a response that does not reveal whether the foreign record exists.
3. Anonymous requests cannot read or mutate personal records; all routes that consume personal profile/history are covered.
4. Changing `owner_id`/`user_id` in a body, query, path, or pagination parameter does not change the principal or returned ownership.
5. Lists, counts, cursors, and page boundaries never include or reveal Bob’s or Alice’s records to the other.
6. Apply the same tests to voice requests, transcript/history access, profile, export, delete, and any background-job path that can access personal data.
7. Logout/revocation makes the old session unusable; deletion behavior is verified against the declared retention/backup policy.

Do not enable persisted multi-user history until the complete suite passes with the production-equivalent authentication and database roles. These tests extend the improvement plan’s Alice/Bob release gate. [VERIFIED: `krishi_mitra_complete_improvement_plan.md:122-142,284-292`; primary-source support for access-control testing cited above]

## 3. Voice disclosure, vendor data flow, and India DPDP research status

### Data flow established by inspected code

The inspected voice flow is: browser microphone recording → own `/api/voice-turn` endpoint → Sarvam speech-to-text → transcript plus client-supplied recent history/profile into the Groq chat request → reply text to Sarvam text-to-speech → response audio to browser. The route and provider operations are evidenced by the quoted `web_app.js` and `backend/web_server.py` excerpts above. The browser requests microphone access at `web_app.js:568`; microphone permission alone is not a product disclosure or an explanation of provider processing. [VERIFIED: `web_app.js:534-568`; `backend/web_server.py:763-765,849-876`]

Put a short Kannada/English notice immediately before recording starts. Describe the actual flow: audio is sent to Sarvam for transcription; transcript and supplied recent chat context are sent to Groq for response generation; response text is sent to Sarvam for speech synthesis. Offer typed chat as an alternative and make voice output optional. Do not promise deletion, non-retention, no training, data residency, or legal compliance unless the actual contract, account settings, and implemented deletion behavior support that exact promise.

### What the primary vendor sources do and do not establish

- **Groq:** Its current API data-controls page says ordinary inference requests are not retained by default, but describes limited reliability/abuse logging up to 30 days, an optional Zero Data Retention setting, and US GCP storage for retained customer data. It lists chat completions and audio endpoints. This is a statement about the published service documentation, **not proof of this project account’s settings, accepted contract, exact endpoint configuration, or applicable exception**. The account-level setting and executed Services Agreement/DPA must be verified before wording any notice. [CITED: [Groq “Your Data”](https://console.groq.com/docs/your-data), “Customer Data”, retention table, and “Data Location”; [Services Agreement](https://console.groq.com/docs/legal/services-agreement), last modified 2026-06-22; [DPA](https://console.groq.com/docs/legal/customer-data-processing-addendum), effective 2025-10-15]
- **Sarvam:** Its public Privacy Policy explicitly excludes content processed on behalf of enterprise customers and says customer agreements govern that data. Its public Terms of Service identify developer APIs, including speech-to-text and text-to-speech, and say the EULA, DPA, and product-specific terms form part of the agreement. The underlying account-specific/API DPA and product terms were not verified here; therefore Sarvam audio/transcript retention, training use, subprocessors, location, and deletion are **unknown**. [CITED: [Sarvam Privacy Policy](https://www.sarvam.ai/privacy-policy), updated 2026-07-29; [Sarvam Terms of Service](https://www.sarvam.ai/terms-of-service), effective 2026-07-29]
- **Training behavior:** No account-specific observation was available in this research; whether either provider uses this project’s inputs for training is unknown. Do not claim either behavior without the executed agreement and account configuration. `[ASSUMED: unresolved; confirm with each provider]`

Maintain a data-flow inventory for audio, transcript, prompt/history/profile, generated response/audio, logs, backups, and every processor. Verify contractual terms and controls before release; log only operational metadata needed for service health and keep actual user content out of logs unless a separately reviewed need exists. This is a control recommendation, not a legal conclusion.

### DPDP legal-status boundary

Fetches of the official MeitY Data Protection Framework page, India Code record, and a MeitY DPDP Rules PDF returned HTTP 403 in this session. No current primary-law text or commencement notification was verified. **This research makes no claim about DPDP applicability, compliance, commencement, exemptions, or the effective date of any duty.** Before launch, India privacy counsel must verify the current Act, Rules, amendments/notifications and commencement instruments, and review the actual roles, notices, vendor contracts, data flows, retention/deletion, rights/grievance, children’s data, transfers, and incident process. [SOURCE RETRIEVAL BLOCKED: official URLs below returned 403; no legal inference is drawn.]

### Security verification scope

Use the versioned OWASP ASVS 5.0.0 chapters relevant to these workstreams; the official versioned CSV names these categories verbatim: “Encoding and Sanitization”, “Validation and Business Logic”, “API and Web Service”, “Authentication”, “Session Management”, “Authorization”, “OAuth and OIDC”, “Secure Communication”, “Configuration”, “Data Protection”, and “Security Logging and Error Handling”. [CITED: [OWASP ASVS 5.0.0 official CSV](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv); category names confirmed from its chapter columns]

Apply these to the eventual selected stack: safe rendering and citation URLs (Encoding/Sanitization); request validation and bounded payloads (Validation/Business Logic); endpoint behavior and API authorization (API/Web Service); identity provider callback (Authentication, OAuth/OIDC); session lifecycle and CSRF controls (Session Management); per-object ownership (Authorization); HTTPS and secure settings (Secure Communication, Configuration); retention, deletion, and backups (Data Protection); and redacted operational events (Logging/Error Handling). Select and test the applicable individual requirements after the production architecture is chosen; no ASVS audit or compliance claim is made here.

## 4. Production deployment and a measurable “1,000 users” target

**Recommendation:** Preserve the local demo entrypoint and add a separate production-serving path after selecting the hosting/runtime. The inspected server binds to loopback and uses Python’s threaded HTTP server (quoted above); do not expose that local launch command as proof of production readiness. Use managed HTTPS termination, a production ASGI-capable runtime selected for the app, health/readiness and graceful shutdown, bounded request/provider timeouts, rate/concurrency limits, secrets management, staging, rollbackable migrations, and redacted metrics. FastAPI’s deployment guidance describes HTTPS, startup/restarts, replication, memory, and worker-process deployment concepts; its worker documentation is not a capacity guarantee for this app. [VERIFIED: `backend/web_server.py:9,1010`; CITED: [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/), [worker processes](https://fastapi.tiangolo.com/deployment/server-workers/)]

“1,000 users” must be defined as registered accounts, daily active users, or peak simultaneous turns. Registered accounts alone do not specify traffic. Parameterize a load model before setting targets:

- Let `R = 1,000` registered accounts, `a` = peak-hour active fraction, `r` = turns per active user per hour, `b` = burst multiplier, and `v` = voice share.
- Estimated peak turn arrival rate: `λ = R × a × r × b / 3,600` turns/second. Voice arrival rate is `v × λ`.
- Approximate provider call rates, excluding retries: Groq chat `≈ λ`; Sarvam ASR `≈ vλ`; Sarvam TTS `≈ vλ` when voice replies are enabled.
- Approximate in-flight work at each stage as `arrival rate × mean stage service time`; calculate separately for ASR, LLM, TTS, database, and end-to-end. Use observed stage times and provider quotas, not guessed constants.

Run a staged test sequence against staging: script/health smoke → normal-load plateau → stress ramp → spike → soak → breakpoint. k6 documentation recommends different test types for different risks and pass/fail thresholds for SLOs. [CITED: [k6 load-test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/); [k6 thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)]

Measure end-to-end and per-stage p50/p95/p99 latency, throughput, HTTP/provider error and timeout rates, rate-limit responses, queue wait/depth, DB pool saturation, CPU/memory, provider quotas, and cost per text/voice turn. Set pass/fail SLOs and provider spend limits before testing; do not fabricate target values before product and budget decisions. Test both realistic production providers (within approved quotas) and controlled injected latency/failure to test resilience.

Degrade deliberately: bounded concurrency and queue; bounded retries with jitter; fail fast on provider throttling/outage; offer typed chat when voice services are unavailable; use only reviewed local content/deterministic rules for fallback and label its limits; never fabricate a successful answer. Keep a database failure closed for private-history operations. Publish the exact workload, hardware, software, provider limits, thresholds, run duration, and results before making any capacity statement. **No 1,000-user capacity claim is supported now.** k6 was not found on PATH in this session; it was not installed and no load test was run. [VERIFIED: session PATH probe; no capacity measurement performed]

## 5. Kannada offline ASR/TTS feasibility (not capability proof)

**ASR feasibility evidence:** AI4Bharat’s IndicConformer Kannada model card specifies Kannada, 16 kHz mono WAV input, a 120M-parameter Conformer-Large model, and NeMo inference. Hugging Face model metadata lists MIT and about 1.57 GB stored model files. This is evidence of a candidate model and documented interface—not target-device speed, dialect/noise quality, memory at runtime, or a tested application capability. [CITED: [IndicConformer Kannada model card](https://huggingface.co/ai4bharat/indicconformer_stt_kn_hybrid_ctc_rnnt_large); [Hugging Face model metadata](https://huggingface.co/api/models/ai4bharat/indicconformer_stt_kn_hybrid_ctc_rnnt_large)]

**TTS feasibility evidence:** AI4Bharat’s IndicF5 card lists Kannada and requires generated text, reference audio, and the reference transcript; Hugging Face metadata labels the model MIT. Its card also says voice cloning requires explicit permission for voices used. Do not use a farmer’s recording as a reference voice without explicit permission and a reviewed product/legal basis. [CITED: [IndicF5 model card](https://huggingface.co/ai4bharat/IndicF5); [IndicF5 metadata](https://huggingface.co/api/models/ai4bharat/IndicF5)]

The newer Bodhan-AI Indic-Speak card lists Kannada, is gated behind acceptance of its license, and reports a 3.3B-parameter model / about 7.3 GB of model storage in Hugging Face metadata. Its page advertises performance metrics, but those are model-publisher claims and were not independently reproduced on Krishi Mitra devices; its metadata marks the license `other`. Treat it as a license/access-gated benchmark candidate, not an approved dependency or quality conclusion. [CITED: [Indic-Speak model card](https://huggingface.co/bodhan-ai/indic-speak); [model metadata](https://huggingface.co/api/models/bodhan-ai/indic-speak); [license text](https://github.com/Bodhan-AI/bodhan-model-info/blob/main/licenses/indic-open-model-license/v1/Indic_Open_Model_License.md)]

Before any offline claim, run a target-device benchmark with consented, held-out Kannada speakers across dialect, clean/noisy field audio, code-mix, and relevant crop/district/unit vocabulary. Report ASR WER/CER **and slot-critical error rates**; separately measure TTS human intelligibility/pronunciation and blinded listener quality; record cold-start and steady-state latency, real-time factor, peak RAM/VRAM, disk/download size, power, and offline behavior. Verify all model, code, dataset, and voice-reference terms for the intended distribution/use. A full-offline claim additionally requires that answer generation/retrieval and scheme references work without network—not only ASR and TTS. No Kannada quality or offline capability is demonstrated by this research.

## Dependencies and rollout gates

| Workstream | Required decisions/dependencies | Release gate |
|---|---|---|
| Curated corpus | Permitted authoritative source set; named content owner and agricultural reviewer; FTS5 runtime check; reviewed bilingual query set. | Citation IDs all resolve to retrieved reviewed records; claim-support/abstention evaluation meets thresholds set from baseline; scheme-engine results unchanged. |
| Private history | Selected OIDC provider and production configuration; secure session/revocation; persistent store/migrations; retention/export/delete policy; counsel review. | Alice/Bob/anonymous suite passes on every personal-data path using production-equivalent identity and DB roles. |
| Voice disclosure | Verified Sarvam API DPA/product terms and Groq account settings/contract; confirmed actual flow; reviewed Kannada/English disclosure. | Notice matches actual processing; privacy/counsel review complete; no unsupported retention/training promises. |
| Production/capacity | Hosting/runtime, provider quotas/budget, staging, secrets, monitoring, workload inputs, agreed SLOs. | Deployment smoke/rollback pass; staged load sequence meets declared thresholds; no capacity statement beyond measured workload. |
| Offline speech | Target device(s), consented labeled test audio, human Kannada reviewers, model/license review, local inference path. | Reproducible target-device ASR/TTS and no-network tests meet declared metrics; limitations documented. |

## Sources and retrieval notes

### Repository evidence (opened this session)

- `.gsd/STATE.md:1-17` — active milestone/phase and next step.
- `krishi_mitra_complete_improvement_plan.md:66-79,104-142,144-178,205-232,265-315` — later-stage constraints and release gates.
- `backend/web_server.py:9,763-765,849-876,963-971,1010`; `web_app.js:463-469,534-568` — current server/provider/request paths.
- `.gsd/phases/02-text-to-text-nlu-prototype/02-RESEARCH.md` — existing prior research; this artifact deepens later workstreams rather than replacing it.

### Official / primary external sources (retrieved 2026-10-31)

- OWASP [Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), and [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) — ownership checks, session risks, CSRF controls.
- OWASP [ASVS 5.0.0 official CSV](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv) — applicable chapter names verified against the versioned source; no control-level audit performed.
- OpenID Foundation [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) and IETF [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700) — identity layer and OAuth security BCP.
- PostgreSQL [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) — row-level policy scope and bypass caveats.
- SQLite [FTS5](https://www.sqlite.org/fts5.html) — lexical search, ranking, build availability.
- Groq [Your Data](https://console.groq.com/docs/your-data), [Services Agreement](https://console.groq.com/docs/legal/services-agreement), [DPA](https://console.groq.com/docs/legal/customer-data-processing-addendum); Sarvam [Privacy Policy](https://www.sarvam.ai/privacy-policy), [Terms of Service](https://www.sarvam.ai/terms-of-service) — only public provider statements; actual account-level terms/settings remain to be checked.
- FastAPI [Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/) and [Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/); Grafana k6 [Test Types](https://grafana.com/docs/k6/latest/testing-guides/test-types/) and [Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) — deployment concepts and staged performance test design.
- AI4Bharat [IndicConformer Kannada](https://huggingface.co/ai4bharat/indicconformer_stt_kn_hybrid_ctc_rnnt_large), [IndicF5](https://huggingface.co/ai4bharat/IndicF5); Bodhan-AI [Indic-Speak](https://huggingface.co/bodhan-ai/indic-speak) — model-card claims and metadata only, not independent benchmarks.

### Retrieval blocks / unknowns

- Official MeitY Data Protection Framework (`https://www.meity.gov.in/data-protection-framework`), India Code (`https://www.indiacode.nic.in/handle/123456789/22094`), and the attempted MeitY DPDP Rules PDF (`https://www.meity.gov.in/static/uploads/2025/DPDP-Rules-2025.pdf`) returned HTTP 403. Current primary legal text/status therefore remains unverified; make no legal-status or compliance assertion.
- Sarvam enterprise/API data-processing terms were not retrieved or account-verified. Groq API/account controls and executed contract were not checked in the project account. Provider training use and account-specific retention behavior remain unknown.
- Target deployment host, identity provider, privacy counsel, content reviewer, target speech devices, and provider quotas are not established in the inspected materials. No tests, model benchmarks, or load tests were run.
