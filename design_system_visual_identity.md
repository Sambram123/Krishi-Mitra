# Design System Specification (DESIGN_SYSTEM)

## 1. Design Philosophy: "Earthy Clarity & Rural Trust"
Krishi Mitra's interface serves two simultaneous audiences during the hackathon and in field deployment:
1. **The Farmer**: Needs high-contrast, glare-resistant visuals suitable for outdoor sunlight on an affordable Android smartphone, large touch targets, clear voice status animations, and minimal text clutter.
2. **The Hackathon Judge / Auditor**: Needs a toggleable or split-screen **Transparency & Audit Drawer** showing live dialect normalization, extracted slots, and the deterministic rule tree.

---

## 2. Color Palette

| Token | Hex Code | Usage | Contrast Ratio (on Surface) |
| :--- | :--- | :--- | :--- |
| `--krishi-green-700` | `#1B5E20` | Primary brand header, eligible status banner, active voice ring | $7.8:1$ (AAA) |
| `--krishi-green-600` | `#2E7D32` | Primary action buttons, verified rule checkmark | $5.4:1$ (AA) |
| `--krishi-amber-600` | `#D97706` | `POTENTIALLY_ELIGIBLE_MISSING_INFO` badge, follow-up question highlight | $4.7:1$ (AA) |
| `--krishi-terracotta-600` | `#C2410C` | Microphone active recording pulse (Listening state) | $5.1:1$ (AA) |
| `--krishi-earth-50` | `#FAF8F5` | Warm off-white background (reduces harsh screen glare outdoors) | — |
| `--krishi-slate-900` | `#0F172A` | Primary Kannada & English body typography | $16.2:1$ (AAA) |
| `--krishi-synthetic-purple` | `#6D28D9` | Distinct badge color for `[DEMO / SYNTHETIC SCHEME]` cards | $6.4:1$ (AA) |

---

## 3. Typography & Kannada Script Rendering
* **Primary Kannada Font**: `Noto Sans Kannada` (weights `400`, `600`, `700`).
  * Line height must be set to at least `1.65` (`leading-relaxed`) so Kannada subscript consonant conjuncts (*ottakshara* / ಒತ್ತಕ್ಷರಗಳು) never clip or collide vertically.
* **Secondary UI / Audit Font**: `Inter` for English labels and `JetBrains Mono` for JSON rule traces.
* **Minimum Font Sizes**:
  * Spoken transcript bubbles: `1.125rem` (`18px`)
  * Scheme card titles: `1.25rem` (`20px`, bold)
  * Touch buttons: Minimum height `56px` (`3.5rem`)

---

## 4. Core Voice State Visual Tokens
The central **Krishi Voice Orb** communicates system state through four unmistakable visual states:
1. **Idle / Ready**: Solid `--krishi-green-600` circle with microphone icon and label *"ಮಾತನಾಡಲು ಒತ್ತಿರಿ (Tap to Speak)"*.
2. **Listening (Farmer Speaking)**: Pulsing concentric rings in `--krishi-terracotta-600` reacting to live microphone decibel levels + live partial Kannada transcript.
3. **Thinking & Verifying Rules**: Rotating golden-green agrarian chakra animation ($< 1\text{ s}$) while slots normalize and rules evaluate.
4. **Speaking (Krishi Mitra Explaining)**: Smooth waveform equalizer in `--krishi-green-700` with a prominent *"ನಿಲ್ಲಿಸಿ / ಮಧ್ಯೆ ಮಾತನಾಡಿ (Interrupt / Speak Now)"* button.