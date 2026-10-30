# Web Application UX & Hackathon Workbench Layout (WEB_UX)

## 1. Responsive Dual-Mode Layout

The web interface (`frontend/src/app/page.tsx`) is engineered to serve both as a clean **Farmer Mobile View** and a comprehensive **Hackathon Demo Workbench** on desktop screens.

    +-----------------------------------------------------------------------------------+
    | [Krishi Mitra Logo]   ಕೃಷಿ ಮಿತ್ರ — ರೈತರ ಧ್ವನಿ ಸಹಾಯಕ     [Mode: Phase 1 Text | Phase 2 Voice] |
    +-----------------------------------------+-----------------------------------------+
    |     LEFT PANE: CONVERSATIONAL STAGE     |   RIGHT PANE: AUDITABLE ELIGIBILITY     |
    |                                         |               INSPECTOR                 |
    |  +-----------------------------------+  |  +-----------------------------------+  |
    |  |Dialect Quick-Test Bar (1-Click):  |  |  | Extracted Farmer Profile (Live)   |  |
    |  |[Dharwad Togari] [Mandya Drip] ... |  |  | District: DHARWAD | Land: 2.5 Ac  |  |
    |  +-----------------------------------+  |  | Crop: ತೊಗರಿ (Pigeon Pea) | OWNED   |  |
    |                                         |  +-----------------------------------+  |
    |  [Assistant Bubble - Kannada + Audio]   |                                         |
    |  "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ!..."              |  +-----------------------------------+  |
    |                                         |  | 5 Reference Schemes Status        |  |
    |  [Farmer Bubble - Raw & Normalized]     |  |                                   |  |
    |  "ನಂದು ಧಾರವಾಡ, 2 ಎಕರೆ 20 ಗುಂಟೆ..."      |  | [ELIGIBLE] PMFBY (Real)           |  |
    |   -> [2.5 Acres | Dharwad | Owned]      |  |   ✓ Crop: Pigeon Pea | ✓ Kharif   |  |
    |                                         |  |                                   |  |
    |  [Assistant Bubble - Recommendation]    |  | [ELIGIBLE] PM-KISAN (Real)        |  |
    |  "ನೀವು ಪಿಎಂ-ಕಿಸಾನ್ ಮತ್ತು ಫಸಲ್ ಬಿಮಾ..."  |  |   ✓ Owned 2.5 Ac | ✓ Non-Taxpayer |  |
    |                                         |  |                                   |  |
    |  +-----------------------------------+  |  | [NEEDS INFO] Demo Micro-Irrigation|  |
    |  |   ( (( KRISHI VOICE ORB )) )      |  |  |   ? Missing: irrigation_source    |  |
    |  |  Tap to Speak Kannada / Barge-in  |  |  |                                   |  |
    |  |  [ Or Type Kannada/Kanglish... ]  |  |  | [Click any card to view JSON rule |  |
    |  +-----------------------------------+  |  |  audit, benefits, & RTC docs]     |  |
    |                                         |  +-----------------------------------+  |
    +-----------------------------------------+-----------------------------------------+

---

## 2. Interactive Features for Live Demos

1. **Dialect & Scenario Quick-Test Bar**:
   * Includes 6 pre-loaded regional Kannada utterances (both text and pre-recorded/synthesized regional audio clips) covering:
     * *Uttara Karnataka (Dharwad)*: Red gram (*Togari*) + *Gunte* land calculation.
     * *Old Mysuru (Mandya)*: Sugarcane/Horticulture + code-mixed English *"Drip irrigation subsidy"*.
     * *Tenant Farmer (Shivamogga)*: Leased land (*Guttige*) testing PM-KISAN exclusion & PMFBY/Soil inclusion.
     * *Equipment Need (Belagavi)*: Asking for power tiller/tractor implement assistance.
     * *Follow-up Context Test*: *"ಇದಕ್ಕೆ ಏನೇನು ಡಾಕ್ಯುಮೆಂಟ್ಸ್ ಬೇಕು ಮತ್ತೆ ಎಲ್ಲಿ ಅರ್ಜಿ ಹಾಕಬೇಕು?"* (What documents are needed and where to apply?).
2. **Real-Time Slot Delta Badges**:
   * Below every farmer message bubble, small pill badges animate in showing exactly what entities were extracted in that turn (e.g., `📍 ಧಾರವಾಡ (Dharwad)`, `🌾 ತೊಗರಿ (Pigeon Pea)`, `📐 2 ಎಕರೆ 20 ಗುಂಟೆ → 2.5 Acres`).
3. **Expandable Rule Audit Tree**:
   * Clicking any of the 5 reference scheme cards opens its deterministic checklist showing green checkmarks (`✓`) for satisfied conditions, amber question marks (`?`) for missing slots, and red crosses (`✗`) for triggered exclusions.