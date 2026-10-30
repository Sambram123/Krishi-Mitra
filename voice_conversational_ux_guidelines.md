# Voice & Conversational UX Specification (UI_UX)

## 1. Why Krishi Mitra Is Not "Just a Chatbot with a Microphone"

Adding ASR and TTS to a standard text chatbot produces a poor farmer experience because text chatbots output long bulleted lists, markdown asterisks (`**`), parenthetical acronyms, and robotic multi-part questionnaires. Krishi Mitra enforces five **Voice-First UX Laws**:

### Law 1: Ear-First Sentence Structure (Prosody & Pacing)
* **Bad (Text Chatbot Read Aloud)**: *"1. PM-KISAN: Benefit Rs. 6000/yr. Eligibility: Landholding farmer. Documents: RTC, Aadhaar. 2. PMFBY: Crop insurance..."*
* **Good (Krishi Mitra Spoken Kannada)**: *"ಯಜಮಾನರೇ, ನಿಮ್ಮ ಮಾಹಿತಿ ಪ್ರಕಾರ ನಿಮಗೆ ಮುಖ್ಯವಾಗಿ ಎರಡು ಯೋಜನೆಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತವೆ. ಮೊದಲನೆಯದು ಪಿಎಂ-ಕಿಸಾನ್. ಇದರಲ್ಲಿ ವರ್ಷಕ್ಕೆ ಆರು ಸಾವಿರ ರೂಪಾಯಿ ನೇರವಾಗಿ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಬರುತ್ತದೆ. ಎರಡನೆಯದು ನಿಮ್ಮ ತೊಗರಿ ಬೆಳೆಗೆ ಫಸಲ್ ಬಿಮಾ ವಿಮೆ. ಇವುಗಳಲ್ಲಿ ಯಾವುದರ ದಾಖಲೆಗಳ ಬಗ್ಗೆ ಮೊದಲು ತಿಳಿಸಲಿ?"*

### Law 2: Conversational Grounding (Implicit Confirmation)
Whenever a farmer provides details in regional terms, Krishi Mitra naturally echoes the normalized understanding inside its reply so the farmer knows they were heard accurately:
* *Farmer*: *"ನಂದು ಒಂದೂವರೆ ಎಕರೆ ಇಪ್ಪತ್ತು ಗುಂಟೆ ಜಮೀನು ಐತಿ."*
* *Krishi Mitra*: *"ಸರಿ, ಅಂದರೆ ಒಟ್ಟು ಎರಡು ಎಕರೆ ಜಮೀನು ಇದೆ ಅಲ್ವಾ..."* (Implicitly confirming $1.5\text{ Ekare} + 20\text{ Gunte} = 2.0\text{ Acres}$).

### Law 3: One-Turn, One-Focus Questioning
Never ask more than 1–2 tightly coupled pieces of missing information in a single turn. If 4 slots are missing, ask for crop and land size first; ask about season or irrigation source in the next turn.

### Law 4: Verbalized Numbers & Acronyms
Before text is sent to the TTS engine, the `tts_service.py` normalizer rewrites symbols so the TTS never misreads them:
* `₹6,000` $\rightarrow$ `ಆರು ಸಾವಿರ ರೂಪಾಯಿ`
* `2.5 ಎಕರೆ` $\rightarrow$ `ಎರಡೂವರೆ ಎಕರೆ`
* `RTC` $\rightarrow$ `ಪಹಣಿ ಪತ್ರ ಅಂದರೆ ಆರ್‌ಟಿಸಿ`

### Law 5: Respectful Empathy on Ineligibility
When a farmer is ineligible for a scheme (e.g., a tenant farmer asking for PM-KISAN), clearly explain the exact rule without dead-ending the conversation, and immediately pivot to schemes they *can* access (such as PMFBY crop insurance or Demo Soil Improvement Support).