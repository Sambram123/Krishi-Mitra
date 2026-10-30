# Decisions (ADR)

> Source set: `.gsd/DECISIONS.md` (manifest type ADR, precedence 0, locked). Both records carry **Status: Accepted**, dated 2026-10-30. LOCKED — no other source in this ingest may auto-override them.

## ADR-001: Decoupling Conversational AI from Decision Engine
- source: .gsd/DECISIONS.md
- status: locked (Accepted, 2026-10-30)
- decision: Separate the architecture into two distinct layers. (1) **Perception & Dialogue Layer:** LLMs used exclusively for conversational speech interpretation, entity extraction (land size, crops, irrigation), and phrasing natural, empathetic Kannada responses. (2) **Deterministic Rule Engine:** pure Python logic evaluating concrete boolean criteria (e.g., `land_size <= 5.0 and irrigation == 'Rainfed'`) to match schemes and generate an auditable checklist.
- scope: conversational AI layer; decision engine; LLM hallucination control; deterministic rule engine; scheme matching; Kannada voice responses

## ADR-002: Bimodal Feedback (Voice Response + Visual Cards)
- source: .gsd/DECISIONS.md
- status: locked (Accepted, 2026-10-30)
- decision: Keep spoken responses brief (under 25 words / 2 sentences) summarizing key eligibility, while synchronously rendering high-contrast visual cards with document checklists on screen.
- scope: bimodal feedback; Kannada voice responses; visual cards; turn latency (< 2s)
