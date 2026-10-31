# Krishi Mitra

## Run the web app

From the repository root, start the same-origin Python server:

```powershell
python -m pip install -r requirements.txt
python -m backend.web_server
```

Open `http://127.0.0.1:8000`. Do not open `index.html` directly: the pages use `/api` endpoints served by this process.

## Deploy a protected demo on Render

The repository includes a `render.yaml` Blueprint for a public demo service. It binds to `0.0.0.0`, uses Render's `PORT`, enables a shared-password gate, and leaves provider credentials as dashboard-managed secrets. It does not create personal accounts or private per-user chat history; the shared password is only a demo access gate.

1. Push this branch to GitHub and create a Render Blueprint from the repository, or create a Python web service with the settings in `render.yaml`.
2. In Render's environment settings, set `DEMO_ACCESS_PASSWORD` to a randomly generated value of at least 20 characters and `DEMO_SESSION_SECRET` to a separate random value of at least 32 characters. Keep both private and share the access password only with judges. Set `GROQ_API_KEY` and `SARVAM_API_KEY` there if those features are needed. Never commit these values or put them in browser code.
3. Keep `REQUIRE_DEMO_PASSWORD=true`, `DEMO_COOKIE_SECURE=true`, and `BIND_HOST=0.0.0.0`. Render provides `PORT`; do not hardcode it.
4. Wait for the deploy and health check, then open the HTTPS URL and verify the password gate, typed chat, scheme evaluation, and voice if configured. Rotate the shared password after the demo.

The password gate uses a signed, HTTP-only, SameSite cookie that expires after 12 hours. The password is shared, so this is not authentication for individual farmers and does not provide saved-history isolation. Use a high-entropy password; do not treat the gate as a substitute for identity, authorization, rate limiting, or production security. The service remains publicly reachable at the network layer, and platform quotas/costs should be monitored.

Typed and voice chat use Groq `openai/gpt-oss-120b` for natural, multi-turn farming advice. Sarvam is used for speech-to-text and speech synthesis; scheme screening remains deterministic and rule-based. Scheme cards are shown only when the farmer asks about government support or eligibility. The last eight chat messages are sent as context so follow-up questions make sense. Kannada typed replies use Sarvam Bulbul v4 Flash speech when configured; English typed replies use the browser's speech engine. Voice chat uses Sarvam Saaras v4 for transcription and Bulbul v4 Flash for speech synthesis. Add your keys to the ignored `.env` file:

```powershell
GROQ_API_KEY=your-groq-key
SARVAM_API_KEY=your-key
```

Restart the server after changing `.env`. Keys stay on the server. Groq enables natural chat; without it, chat uses a limited local fallback. Sarvam enables voice transcription and spoken replies; typed chat still works without Sarvam. The browser records a voice turn locally (up to 25 seconds) and sends it to the same-origin API; audio is transcribed and processed server-side, with eligibility still determined by the app's rule engine. Speech recognition auto-detects Kannada or English, and the reply follows the detected language. Tap the microphone again to send. If the recording indicator detects silence and multiple input devices are available, choose the correct microphone from the selector below the recording area; the selection is remembered in this browser. Groq chat requests time out after 25 seconds, Sarvam requests after 15 seconds, and the browser stops waiting for a voice turn after 50 seconds. The assistant is instructed not to make official eligibility claims. Microphone access requires localhost or HTTPS.

Backend request and model-stage logs are written to the server terminal. They include request IDs, stage names, byte counts, durations, and provider error categories, but do not include audio, transcripts, or API keys. For more or less detail, set `LOG_LEVEL` to a Python logging level such as `DEBUG`, `INFO`, or `WARNING` before starting the server.

Run the backend and scheme tests:

```powershell
python -m unittest backend.test_rules backend.test_web_server -v
```

The stored, source-linked scheme catalogue was last researched on 2026-10-30. It includes PM-KISAN, PMFBY/Karnataka Samrakshane, PMKSY-Per Drop More Crop, SMAM, and the Soil Health Card Programme. Current district notifications, application windows, subsidy rates, allocations, enrollment, and official decisions must be confirmed with the linked government portals or relevant department. PMKSY and SMAM are shown as conditional referrals; Soil Health Card is a soil-testing/advisory service, not a cash grant.
