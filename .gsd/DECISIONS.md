# DECISIONS.md — Architecture & Technical Decision Records (ADR)

# ADR-001: Decoupling Conversational AI from Decision Engine

- **Date:** 2026-10-30
- **Status:** Accepted
- **Context:** Large Language Models (LLMs) frequently hallucinate numbers, eligibility criteria, and administrative conditions. Direct LLM-based government scheme advisories can mislead vulnerable farmers and cause financial damage.
- **Decision:** Separate the architecture into two distinct layers:
  1. **Perception & Dialogue Layer:** Uses LLMs exclusively for conversational speech interpretation, entity extraction (land size, crops, irrigation), and phrasing natural, empathetic Kannada responses.
  2. **Deterministic Rule Engine:** Uses pure Python logic evaluating concrete boolean criteria (e.g., `land_size <= 5.0 and irrigation == 'Rainfed'`) to match schemes and generate an auditable checklist.
- **Consequences:** Eliminates hallucination risk; makes all scheme recommendations auditable and transparent for hackathon judges and farmers.

---

# ADR-002: Bimodal Feedback (Voice Response + Visual Cards)

- **Date:** 2026-10-30
- **Status:** Accepted
- **Context:** Listening to 90 seconds of spoken policy text is overwhelming for voice users. However, farmers need to know document requirements, application links, and benefit figures.
- **Decision:** Keep spoken responses brief (under 25 words / 2 sentences) summarizing key eligibility, while synchronously rendering high-contrast visual cards with document checklists on screen.
- **Consequences:** Dramatically improves voice UX, keeps turn latency under 2s, and provides farmers with actionable visual checklists.
