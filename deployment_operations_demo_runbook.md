# Deployment, Operations & Live Demo Runbook (DEPLOYMENT_AND_OPERATIONS)

## 1. Containerized Deployment (`docker-compose.yml`)

Krishi Mitra is packaged for reproducible single-command deployment during the hackathon evaluation:

    version: '3.9'
    services:
      postgres:
        image: postgres:16-alpine
        environment:
          POSTGRES_USER: krishi
          POSTGRES_PASSWORD: krishi_pass
          POSTGRES_DB: krishi_mitra
        ports:
          - "5432:5432"

      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"

      backend:
        build: ./backend
        env_file: .env
        ports:
          - "8000:8000"
        depends_on:
          - postgres
          - redis

      frontend:
        build: ./frontend
        environment:
          NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
          NEXT_PUBLIC_WS_URL: ws://localhost:8000/api/v1
        ports:
          - "3000:3000"
        depends_on:
          - backend

---

## 2. Live Hackathon Demo Runbook & Fail-Safe Mechanisms

Live audio demos in crowded hackathon venues face two common risks: venue background noise and unstable Wi-Fi. Krishi Mitra includes built-in operational safeguards:

1. **Push-to-Talk + VAD Toggle**:
   * In a quiet room, use **Hands-Free VAD Mode** for natural turn-taking.
   * On a noisy hackathon stage, switch the UI toggle to **Push-to-Talk (Hold Mic)** so background chatter is never transcribed into the farmer's session.
2. **Pre-Recorded Regional Farmer Audio Injection**:
   * In addition to live microphone speech, the UI includes **Play Authentic Regional Farmer Voice Sample** buttons (Dharwad accent, Mandya accent, Coastal accent) that feed real `.wav` audio through the exact same ASR $\rightarrow$ NLU $\rightarrow$ Rule Engine $\rightarrow$ TTS pipeline, guaranteeing reproducible regional accent demonstrations even if the presenter is not a native speaker of all regional dialects.
3. **Zero-Network Rule Engine Independence**:
   * The entire 5-scheme Eligibility Rule Engine and Kannada Dialect Normalizer run $100\%$ locally inside the Python backend process with zero external API dependencies.