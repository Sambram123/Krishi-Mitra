# Performance & Latency Specification (PERFORMANCE)

## 1. Latency Budget Breakdown

A natural voice conversation requires minimizing the pause between when the farmer finishes speaking and when Krishi Mitra begins speaking back.

| Pipeline Stage | Phase 1 Target (Text) | Phase 2 Target (Voice) | Optimization Technique |
| :--- | :--- | :--- | :--- |
| **1. VAD End-of-Speech Detection** | N/A | $250\text{ ms}$ | Client-side WebRTC/Silero VAD with adaptive silence threshold. |
| **2. Kannada ASR Transcription** | N/A | $450\text{ ms}$ | Streaming WebSocket audio frames during speech so final transcript resolves immediately after VAD trigger. |
| **3. Dialect & Unit Pre-Normalizer** | $5\text{ ms}$ | $5\text{ ms}$ | In-memory Aho-Corasick / compiled regex lexicon lookup. |
| **4. Contextual Slot Extraction (LLM)** | $420\text{ ms}$ | $420\text{ ms}$ | Compact JSON schema output with low temperature ($T = 0.0$) and slimmed 6-turn sliding context window. |
| **5. Deterministic Rule Engine** | $8\text{ ms}$ | $8\text{ ms}$ | Pure in-memory Python evaluation over the 5 pre-loaded scheme ASTs. |
| **6. Spoken Response First Sentence** | $380\text{ ms}$ | $380\text{ ms}$ | Streaming generation; flush first sentence to TTS immediately upon hitting `.` or `?` or `।`. |
| **7. Kannada TTS First Audio Frame** | N/A | $320\text{ ms}$ | Sentence-chunked streaming TTS + Redis caching of common greetings and document explanations. |
| **Total Time-to-First-Output** | **$\approx 813\text{ ms}$** | **$\approx 1,833\text{ ms}$** | Well within natural conversational turn-taking thresholds ($< 2.0\text{ s}$). |

---

## 2. Caching & Pre-Warming Optimizations
1. **Static Greeting & Common Prompt Audio Cache**: Opening greetings and standard document descriptions (e.g., what an RTC/Pahani is) are pre-synthesized and cached in Redis/CDN for $0\text{ ms}$ TTS latency.
2. **Parallel UI Push**: As soon as Stage 5 (Deterministic Rule Engine) finishes at $\approx 880\text{ ms}$, the server pushes the `audit.update` event over WebSocket so the UI updates the Farmer Profile and Scheme Cards *while* the voice audio is starting to play.