# Judge Readiness: Reliability, Privacy, Offline Use, and Scale

**Prepared:** 2026-10-31  
**Project:** Krishi Mitra  
**Purpose:** Research-backed answers for judge questions and a practical next-step roadmap.  
**Scope note:** This is engineering and product guidance, not legal advice or a claim that the current demo is DPDP-compliant.

## Executive summary

Krishi Mitra already has a good reliability boundary for government-scheme screening: a curated catalogue, deterministic rule evaluation, an audit trail, source links, and user-facing disclaimers. The LLM should explain and converse; it should not decide eligibility or invent scheme conditions.

The current system is a cloud-assisted prototype, not an offline or production-scale service. Its browser keeps messages only in the live page, and the backend passes recent history with each request rather than storing conversations. Voice audio is sent to Sarvam for transcription; recognized text and conversation context are sent to Groq; generated speech is sent to Sarvam. The app logs request metadata rather than message/audio content, but this does not establish what a provider retains. These facts should be disclosed plainly.

| Judge question | Defensible short answer |
|---|---|
| How do you reduce hallucinations? | Keep eligibility in deterministic, auditable rules; ground factual advice in approved sources; attach citations to individual claims; abstain when evidence is missing or stale; measure unsupported claims. |
| Can I see earlier chats? | Not persistently today. The current page supplies up to eight recent messages as context, but refresh loses the conversation. We propose opt-in, deletable history with a short retention period. |
| What happens to voice data? | The demo sends a recording to Sarvam for speech recognition, then sends transcript/context to Groq and generated speech text to Sarvam. Our app does not currently have persistent chat/audio storage. Provider retention must be checked and disclosed before public deployment. |
| Is it fully offline? | No. Scheme rules and limited typed fallback can run locally, but natural chat and voice depend on external providers. A full-offline mode needs local ASR, language model, TTS, and local data, and must be tested on target devices. |
| Can it serve 1,000 users? | Not established by the current local `ThreadingHTTPServer` demo. A thousand registered users is a different target from a thousand simultaneous voice turns. We need a production deployment and load tests before making a capacity claim. |
| Are you using multiple agents? | No autonomous multi-agent system is present. It is a fixed pipeline: speech recognition, deterministic profile extraction/rules, LLM wording, and speech synthesis. That bounded orchestration is intentional for a high-impact eligibility decision. |

## 1. Reducing hallucinations and adding useful citations

### What exists today

- Scheme screening runs through the Python rule engine and stored scheme dataset rather than asking the LLM to decide eligibility.
- The scheme UI can show rule audit details, source URLs, and the date sources were researched. The scheme research document explicitly avoids asserting time-sensitive rates or availability without current official confirmation.
- Text and voice prompts tell the LLM not to invent scheme rates, dates, funding, availability, or official approval.
- Chat history is passed as context, but that is not a knowledge source and does not substantiate a factual claim.

These are good controls, but “zero hallucinations” is not a defensible promise. An LLM can still make unsupported claims in ordinary agronomy answers, misunderstand a Kannada transcript, or phrase a source-backed answer too strongly.

### Recommended answer-generation design

1. **Separate decision from explanation.** Treat the deterministic evaluator as the sole authority for scheme results. Keep outputs such as `ELIGIBLE`, `CONDITIONALLY_ELIGIBLE`, `INFORMATIONAL`, and `INELIGIBLE` tied to the exact rule result; do not let an LLM change a status.
2. **Build a small, curated knowledge base.** For agricultural advice, prefer traceable sources such as ICAR, Karnataka Agriculture/Horticulture Department, the relevant University of Agricultural Sciences, Krishi Vigyan Kendras (KVKs), IMD, and official scheme portals. Store source title, issuing organization, URL, publication/effective date, last-checked date, covered district/season, and the exact passage or structured fact used. Avoid treating arbitrary web search results as authoritative.
3. **Retrieve before drafting.** Search the approved corpus for passages relevant to the farmer’s question; pass only those passages plus the farmer’s relevant context to the response model. For scheme queries, retrieve the scheme record and rule result. Microsoft’s [RAG overview](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview) describes retrieval, grounding, and citation/provenance patterns; citations must still be checked for whether they actually support the generated statement.
4. **Return claim-level evidence.** Have the response layer produce a structured answer: short reply, claims, and for each claim one or more source IDs/URLs and the supporting excerpt. Render citations beside the claim or card, not only in a bibliography at the bottom. Show source owner and “checked on” date. Never display a citation that was not among the retrieved evidence.
5. **Abstain safely.** If sources are missing, contradictory, stale, or do not cover the user’s district/season, say so and direct the farmer to the relevant department/KVK. Do not fill the gap with a plausible-sounding rate, dosage, deadline, or approval claim.
6. **Keep the voice answer concise; make evidence visible.** Speak a short, plain-language summary. Show citations, date, limitations, and details on the screen. Offer a way to open the official source.
7. **Evaluate systematically.** Create a reviewed test set of Kannada/English/code-mixed questions, dialect and ASR errors, follow-ups, outdated facts, ambiguous eligibility, and adversarial prompts. Track:
   - unsupported factual-claim rate and citation correctness (does the cited passage support the claim?);
   - answer faithfulness to retrieved context and rule-engine output;
   - correct abstention when evidence is absent/stale;
   - scheme decision agreement with the deterministic engine;
   - Kannada transcript/entity accuracy across dialects;
   - latency and failure rate by stage.

Use human review by an agricultural subject-matter expert for the reference answers and high-impact advice. NIST’s [AI RMF and Generative AI Profile](https://www.nist.gov/itl/ai-risk-management-framework) offer a useful risk-management structure; OWASP’s [GenAI project](https://genai.owasp.org/llm-top-10/) is useful for prompt-injection and LLM application security risks. Neither makes a product “hallucination-proof.”

### Citation contract

Every factual claim that can materially affect a farmer should be one of:

- **Source-backed:** cite an approved, relevant source and show when it was checked.
- **Rule-backed:** cite the scheme rule/audit explanation and label screening as preliminary, not government approval.
- **Unverified/uncertain:** explicitly say the app cannot verify it and direct the farmer to an official channel.

Do not cite model-generated text, another chat, or a search-result snippet as evidence. For fast-changing benefits, rates, application windows, weather, or district notifications, show a last-checked date and require live official confirmation or abstain.

## 2. Previous chats and conversation memory

### Current behavior in this repository

- `web_app.js` builds recent context from messages currently rendered in the page and sends up to eight messages with a request.
- The server validates a maximum of eight history messages. It does not write conversations to a database.
- Reloading the page loses the visible conversation. `localStorage` is currently used for language and preferred microphone only, not chat history.
- The existing scheme catalogue and audit results are separate from personal conversation history.

So the accurate product answer is: **“The demo remembers recent turns while this page is open, but does not yet provide a saved-chat history.”**

### Recommended privacy-preserving rollout

1. **Start with opt-in history on the device.** Store text conversation records in IndexedDB (not server-side by default), with a visible “Save chats on this device” option, “New chat,” “Delete this chat,” and “Delete all chats” controls. Explain that local browser storage is not encrypted against other people who can access that device/browser profile.
2. **Do not save voice recordings by default.** If transcripts are kept as chat text, clearly say so and let users delete them. Keep recording/audio only in memory for the request where possible; do not add server-side audio retention without a separate, justified purpose and explicit consent.
3. **Offer account sync only as a separate opt-in.** Cross-device history requires authentication, access controls, encrypted transport/storage, retention limits, deletion workflows, and a documented processor/vendor arrangement. Make the feature optional; keep a no-account or guest path if feasible.
4. **Set a retention schedule.** Decide a short default retention period based on product need, then delete expired records and backups according to a documented schedule. Do not keep sensitive farm details “just in case.”
5. **Minimize what is sent for each turn.** Send only the history needed for a follow-up, and only the relevant profile fields. Do not put personal details into analytics or application logs.

Chat history is convenient but increases privacy impact if a device or account is shared. Make clear who can see it, where it is stored, how long it remains, and how the user can erase it.

## 3. Voice-data disclosure, consent, and DPDP readiness

### What the current data path means for users

The current voice path records a turn in the browser (up to approximately 25 seconds per the project README), sends the audio to Sarvam for transcription, sends transcript and recent conversation context to Groq for a reply, and sends generated reply text to Sarvam for speech synthesis. The API logs operational metadata such as request IDs, stage names, byte/character counts, durations, and provider error categories; the code avoids logging the audio, transcript text, or API keys. The repository has no persistent chat/audio database.

This describes **our app’s current code**, not a guarantee about Sarvam’s or Groq’s retention, subprocessors, processing locations, or training use. Those provider terms and data-processing arrangements must be reviewed before handling real farmers’ personal data. Do not say “your voice is never stored” until the provider behavior and contract support that claim.

### DPDP-oriented controls to design for

The [Digital Personal Data Protection Act, 2023](https://www.indiacode.nic.in/) and notified [DPDP Rules, 2025](https://www.meity.gov.in/data-protection-framework) should be reviewed together with their commencement notifications and any later amendments. The Act’s consent model calls for consent to be free, specific, informed, unconditional, and unambiguous, given through clear affirmative action; it also provides data-principal rights and duties for data fiduciaries. The rules and commencement schedule matter, so obtain current India-specific legal advice before launch.

For a voice-first service, design as though identifiable audio, transcripts, and linked farm/profile details are personal data:

- **Give a just-in-time notice before recording.** In plain Kannada and English, say what is captured (microphone audio and transcript), why (answering the farming question), who processes it (Krishi Mitra and named service providers), whether it is saved, retention/deletion behavior, and how to withdraw consent or use typed chat instead.
- **Separate consent from the browser permission prompt.** The operating-system/browser microphone permission is not a substitute for an app privacy notice and affirmative consent. A “Terms & Conditions” checkbox alone is also not a sufficiently clear explanation of voice processing.
- **Make choice real.** Provide “Continue with voice” and a usable typed alternative. Do not make a farmer accept optional saved history or analytics just to ask a question. Withdrawal should be easy to find and should stop future processing; explain what cannot be recalled after a provider has processed a request.
- **Name processors and purposes.** Disclose Sarvam speech recognition/synthesis and Groq response generation, including what each receives. Review current data-processing terms, retention, training use, subprocessors, security, breach notice, transfer/location terms, and deletion support; configure the least-retentive options available.
- **Minimize, secure, and govern.** Use TLS in production, restrict staff access, keep secrets out of client code, avoid sensitive log payloads, define retention and deletion for primary storage/backups, protect saved accounts, and prepare incident and grievance procedures.
- **Support rights and contact.** Provide a clear contact/grievance route and a way to request access, correction, erasure, and account/chat deletion as applicable. Define how identity is verified without collecting unnecessary documents.
- **Consider children and shared devices.** Avoid collecting children’s data in the intended farmer flow; seek legal review for age/guardian obligations and avoid behavioral tracking/targeted advertising. Warn users not to speak Aadhaar, bank credentials, or other unnecessary sensitive information.
- **Document the data flow.** Maintain a simple inventory of data, purpose, legal basis/consent, system/vendor, location, retention, access, and deletion owner. Review it whenever a provider or feature changes.

### Suggested consent notice (prototype wording; legal review required)

> **Voice privacy:** If you choose voice, Krishi Mitra records this message and sends it to Sarvam to convert speech to text. The transcript and recent chat context go to Groq to create a reply; reply text goes to Sarvam to make speech. Krishi Mitra does not currently save chat audio or conversation history on its server. The service providers may process data under their own terms. You can use typed chat instead. Do not say account numbers, Aadhaar numbers, or passwords.  
> **[Continue with voice] [Use text instead] [Privacy details]**

Before deploying, replace generic language with a verified vendor-specific notice: provider retention, training policy, data location/transfer, deletion ability, and the app’s actual retention controls. Add a separate, optional consent for saving chats if history is introduced.

## 4. Complete offline mode

### Current limitation

The demo is not fully offline. Groq provides natural text generation, Sarvam provides speech recognition and synthesis, and the voice-turn route depends on Sarvam. A limited local text response exists when Groq is unavailable, and the scheme rules/catalogue are local, but this is not equivalent to full offline farming advice or offline voice. The development server also listens on loopback (`127.0.0.1`) and is not an internet-hosted multi-user deployment.

### Practical offline modes

1. **Offline-safe basic mode (best first milestone):** Keep deterministic scheme screening, local catalogue, and a small set of reviewed FAQs/guidance available without network. Disable unsupported live features and clearly label when source freshness is unknown. Use typed input if local voice is not ready.
2. **Full local voice mode (later):** Package a local Kannada-capable ASR model, local language model or retrieval-based answer system, and Kannada TTS voice. [`whisper.cpp`](https://github.com/ggml-org/whisper.cpp) demonstrates CPU/local and on-device Whisper inference, but it does not prove that the selected model is accurate enough for local Kannada agricultural dialects or that suitable Kannada TTS is available. Benchmark on representative phones/laptops and noisy rural recordings before claiming support.
3. **Synchronize carefully when online.** If offline conversations are saved locally and later synced, show the user what will upload, protect the local store, resolve duplicates/conflicts, and provide deletion that reaches synced server copies.

Offer three honest states: **Online (cloud voice available)**, **Limited offline (local rules/verified reference answers)**, and **Offline voice unavailable** until the full local stack passes validation. A weak local model should not silently answer high-impact questions with lower confidence.

## 5. Scalability to 1,000 users

First clarify the judge’s number: **1,000 registered users**, **1,000 daily users**, and **1,000 simultaneous voice turns** require very different capacity. Do not claim support for 1,000 concurrent sessions based only on the current demo.

### Current constraint

The backend uses Python’s `ThreadingHTTPServer`, binds to `127.0.0.1`, and holds chat context in requests/browser state. There is no production deployment topology, shared session database, authentication layer, distributed queue, or measured concurrency target in the current repository. Each voice turn makes multiple external service calls, so provider quotas, latency, failures, and concurrency limits can dominate server capacity.

### Suggested production shape

```text
Browser/mobile
    -> HTTPS reverse proxy / load balancer
    -> stateless API workers
         -> PostgreSQL (accounts, consent, optional saved text chats)
         -> Redis (short-lived session/cache/rate-limit state)
         -> job/worker pool for slow ASR/TTS tasks where needed
         -> Groq / Sarvam adapters with timeouts, quotas, retry limits
    -> metrics, traces, redacted logs, alerts
```

- Move from the local demo server to a production ASGI/API setup, with multiple workers/replicas behind a load balancer. Scale from measured resource use; worker count alone does not establish capacity.
- Keep API instances stateless. Put optional durable chats in a database, and short-lived coordination/rate-limit state in a shared store. Do not store raw audio unless there is a specific consented purpose.
- Bound provider concurrency and request sizes; use per-user/IP quotas, timeouts, circuit breakers, bounded retries, and graceful degradation. Never retry a voice request in a way that unexpectedly replays or duplicates a sensitive recording.
- Cache non-personal, stable scheme/reference data. Do not cache personalized answers across users. Put a visible “last verified” date on time-sensitive references.
- Instrument per-stage latency/error rates and provider throttling, while redacting message content and audio. Set explicit service targets only after measuring.
- Run staged load tests at the target mix of text and voice, including burst traffic, provider throttling, database failures, and slow ASR/TTS. Measure p50/p95/p99 latency, error rate, queue depth, resource headroom, and provider quota use. Then size infrastructure and cost per user from evidence.
- Add a fallback experience: if voice providers are overloaded, offer typed chat or local rule/catalogue lookup rather than an indefinite spinner or a fabricated successful response.

FastAPI’s [deployment guidance](https://fastapi.tiangolo.com/deployment/server-workers/) describes worker-process replication as one way to use multiple cores and serve more requests. That is a deployment primitive, not a capacity guarantee; the application and all external dependencies still require load testing.

## 6. Agent orchestration: what is actually implemented

There is **no multi-agent orchestration framework or autonomous agent swarm** in the current implementation. The actual flow is a bounded pipeline:

```text
Text: user message -> deterministic profile extraction -> rule evaluation
     -> Groq response wording -> optional Sarvam speech output

Voice: browser recording -> Sarvam speech-to-text -> deterministic profile extraction
      -> rule evaluation -> Groq response wording -> Sarvam text-to-speech
```

Conversation history is passed by the browser as recent context. The LLM is a language-generation step, not an agent that can independently approve eligibility or call arbitrary tools. This is a useful safety property: a high-impact decision has one inspectable path through explicit rules.

If orchestration expands, prefer an explicit workflow/state machine over several free-running agents:

1. **Input/consent gate** checks request, language, and permission.
2. **Intent router** selects crop advice, scheme screening, or general information.
3. **Evidence retriever** returns approved, current sources for the selected intent.
4. **Deterministic evaluator** handles eligibility only.
5. **Answer composer** summarizes supplied evidence and attaches citations.
6. **Policy/quality gate** checks source presence, dates, claims, and safe abstention.
7. **Voice output stage** runs only when requested and consented.

Give each stage a typed input/output schema, explicit timeout and failure state, least-privilege access, and trace ID. Do not let an LLM invent tools, alter rule results, or act on accounts. If a stage fails, surface the failure or use a clearly labeled limited fallback. This keeps orchestration observable and testable without overselling “agents.”

## 7. Recommended delivery order

1. **Before the next demo:** Add a privacy explanation to the voice flow and verbally explain current cloud processing; state that chats are not saved and full offline mode is not available.
2. **Reliability:** Extend the curated source catalogue for crop advice; return claim-linked citations; create the evaluation set and measure unsupported claims/abstention.
3. **Conversation history:** Ship opt-in, device-local text history with clear delete controls; decide retention before account sync.
4. **Privacy readiness:** Review provider terms/DPAs and applicable DPDP commencement/rules with counsel; implement a notice, consent record, rights/grievance contact, data inventory, and deletion process.
5. **Offline feasibility:** Prototype Kannada local ASR/TTS and local inference on the actual target device; keep offline claims limited to what passes measured tests.
6. **Scale:** Define whether the target is registered, daily-active, or concurrent users; deploy a production topology and load-test the realistic voice/text mix before claiming 1,000-user capacity.

## Sources and further reading

Sources were consulted on **2026-10-31**. Government sites may block automated retrieval; use the official text and current notifications for legal interpretation.

1. Government of India, Ministry of Electronics and Information Technology, [Data Protection Framework](https://www.meity.gov.in/data-protection-framework) — official entry point for the DPDP framework, Act, and Rules.
2. Government of India, [India Code](https://www.indiacode.nic.in/) — search for *The Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023)* and use the authoritative text.
3. Microsoft Learn, [Retrieval-Augmented Generation (RAG) with Azure AI Search](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview) — retrieval, grounding, citations/provenance, latency, and security considerations.
4. NIST, [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) and [Generative AI Profile (NIST AI 600-1)](https://doi.org/10.6028/NIST.AI.600-1) — voluntary risk-management and generative-AI risk guidance.
5. OWASP, [Generative AI Security Project / LLM Top 10](https://genai.owasp.org/llm-top-10/) — LLM application risk and mitigation guidance.
6. `whisper.cpp`, [project documentation](https://github.com/ggml-org/whisper.cpp) — local CPU/GPU inference and on-device examples; Kannada dialect accuracy and local TTS still require independent evaluation.
7. FastAPI, [Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/) — worker processes and deployment replication concepts; not a substitute for load testing.
8. Project implementation references: [README.md](./README.md), [architecture.md](./architecture.md), [dataset_research.md](./dataset_research.md), [backend/web_server.py](./backend/web_server.py), and [web_app.js](./web_app.js).

### Legal caveat

This document is not legal advice. DPDP obligations, applicable commencement dates, Rules, exemptions, vendor arrangements, and cross-border transfer conditions can change and depend on the exact deployment. Have Indian privacy counsel review the production data flow and user-facing notice before collecting real users’ voice or chat data.
