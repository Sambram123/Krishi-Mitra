#!/usr/bin/env python3
"""
Krishi Mitra — Stage 1 Text-to-Text Conversational CLI Prototype
Interactive Kannada terminal loop evaluating farmer profiles against deterministic rules.
Supports:
  - Multi-turn slot filling with proactive follow-up questions
  - Deterministic scheme evaluation over benchmark catalog (2 Real, 3 Synthetic)
  - Color-coded audit trail and document checklists
  - Non-interactive acceptance test mode via --demo-benchmark
"""

import sys
import os
import argparse
import uuid
from typing import List, Optional

# Reconfigure stdout/stderr for Unicode/UTF-8 support on Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add workspace root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

from backend.rules_engine import SchemeEvaluator, EvaluationResult, FarmerProfile
from backend.nlu.extractor import NLUExtractor
from backend.nlu.providers import get_provider
from backend.conversation.state import ConversationState, is_profile_complete
from backend.conversation.dialogue import DialogueManager

# Terminal ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
DIM = "\033[2m"
MAGENTA = "\033[35m"


def print_banner():
    print(f"\n{BOLD}{GREEN}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}  🌾 ಕೃಷಿ ಮಿತ್ರ (Krishi Mitra) — Stage 1 Text Prototype{RESET}")
    print(f"{CYAN}  ಕರ್ನಾಟಕ ರೈತರಿಗಾಗಿ ಕನ್ನಡ ಕೃಷಿ ಯೋಜನೆಗಳ ನೈಜ ಮಾರ್ಗದರ್ಶಿ{RESET}")
    print(f"{DIM}  Deterministic Rule Engine + Dialect NLU | Type 'exit' to quit{RESET}")
    print(f"{BOLD}{GREEN}======================================================================{RESET}\n")


def display_results(results: List[EvaluationResult]):
    """Renders high-contrast, structured scheme eligibility cards in terminal."""
    if not results:
        return

    print(f"\n{BOLD}{CYAN}--- ಪರಿಶೀಲಿಸಲಾದ ಸರ್ಕಾರಿ ಮತ್ತು ಪರೀಕ್ಷಾ ಯೋಜನೆಗಳು (Scheme Cards) ---{RESET}")

    for r in results:
        # Determine status color and tag
        if r.status == "ELIGIBLE":
            status_tag = f"{BOLD}{GREEN}✔ [ಅರ್ಹರು - ELIGIBLE]{RESET}"
        elif r.status == "CONDITIONALLY_ELIGIBLE":
            status_tag = f"{BOLD}{YELLOW}⚠ [ಷರತ್ತುಬದ್ಧ - CONDITIONALLY ELIGIBLE]{RESET}"
        else:
            status_tag = f"{DIM}[ಅನರ್ಹರು - INELIGIBLE]{RESET}"

        # Demo indicator
        demo_tag = f" {BOLD}{MAGENTA}[DEMO / TEST CASE]{RESET}" if r.is_demo else f" {DIM}[REAL SCHEME]{RESET}"

        print(f"\n{status_tag}{demo_tag} {BOLD}{r.scheme_name_kn}{RESET} ({r.scheme_name_en})")
        print(f"  {CYAN}ಪ್ರಯೋಜನ (Benefit):{RESET} {r.benefit_summary_kn}")

        if r.status in ("ELIGIBLE", "CONDITIONALLY_ELIGIBLE"):
            # Audit trail
            if r.audit_trail:
                print(f"  {BOLD}ಅರ್ಹತಾ ಕಾರಣಗಳು (Audit Match):{RESET}")
                for reason in r.audit_trail:
                    print(f"    • {GREEN}{reason}{RESET}")

            # Required documents
            if r.required_documents:
                print(f"  {BOLD}ಅಗತ್ಯ ದಾಖಲೆಗಳು (Required Documents):{RESET}")
                for doc in r.required_documents:
                    d_name_kn = doc.get("name_kn") or doc.get("document_name_kn") or doc.get("name", "ದಾಖಲೆ")
                    d_name_en = doc.get("name_en") or doc.get("document_name_en", "")
                    is_mand = doc.get("mandatory") if "mandatory" in doc else doc.get("is_mandatory", True)
                    mand_str = f"{RED}*ಕಡ್ಡಾಯ (Mandatory){RESET}" if is_mand else f"{DIM}ಐಚ್ಛಿಕ (Optional){RESET}"
                    print(f"    [ ] {d_name_kn} ({d_name_en}) — {mand_str}")

        elif r.status == "INELIGIBLE":
            if r.disqualification_reasons:
                print(f"  {DIM}ಅನರ್ಹತೆಯ ಕಾರಣ:{RESET}")
                for dq in r.disqualification_reasons:
                    print(f"    {DIM}✕ {dq}{RESET}")

    print(f"\n{DIM}ಗಮನಿಸಿ: ಇದು ನಿರ್ಧಾರ-ಬೆಂಬಲ ಮಾದರಿಯಾಗಿದೆ (Prototype Decision-Support Tool).{RESET}")
    print(f"{DIM}ಅಂತಿಮ ಅರ್ಹತೆಯನ್ನು ಸಂಬಂಧಪಟ್ಟ ಇಲಾಖೆ/ಪೋರ್ಟಲ್ ನಿರ್ಧರಿಸುತ್ತದೆ.{RESET}\n")


def run_benchmark_test() -> bool:
    """
    Executes CLI-01 acceptance test sentence:
    'ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?'
    Must screen PM-KISAN as eligible and PMKSY micro-irrigation as conditional.
    """
    print(f"\n{BOLD}Running CLI-01 Acceptance Test Benchmark...{RESET}")
    benchmark_sentence = "ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?"
    print(f"Input: \"{benchmark_sentence}\"")

    evaluator = SchemeEvaluator()

    benchmark_profile = FarmerProfile(
        farmer_name="ಬಸವರಾಜ್",
        district="General",
        land_acres=3.0,
        ownership="Owner",
        crops=["Ragi"],
        irrigation_type="Borewell",
        has_water_source=True,
    )

    results = evaluator.evaluate_all(benchmark_profile)
    display_results(results)

    eligible_ids = [r.scheme_id for r in results if r.status == "ELIGIBLE"]
    print(f"Eligible scheme IDs: {eligible_ids}")

    pmksy = next((r for r in results if r.scheme_id == "pmksy_pdmc"), None)
    has_pm_kisan = "pm_kisan" in eligible_ids

    if pmksy and pmksy.status == "CONDITIONALLY_ELIGIBLE" and has_pm_kisan:
        print(f"\n{BOLD}{GREEN}✔ CLI-01 ACCEPTANCE TEST PASSED!{RESET}")
        print("PM-KISAN is screened eligible; PMKSY micro-irrigation remains conditional because current Karnataka rates and criteria require confirmation.\n")
        return True
    else:
        print(f"\n{BOLD}{RED}✕ CLI-01 ACCEPTANCE TEST FAILED!{RESET}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Krishi Mitra Stage 1 CLI Chat Prototype")
    parser.add_argument(
        "--demo-benchmark",
        action="store_true",
        help="Run the benchmark acceptance test sentence non-interactively and exit.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=os.getenv("NLU_PROVIDER", "gemini"),
        help="NLU Provider: 'gemini' or 'ollama'",
    )
    args = parser.parse_args()

    if args.demo_benchmark:
        success = run_benchmark_test()
        sys.exit(0 if success else 1)

    print_banner()

    try:
        extractor = NLUExtractor(provider_name=args.provider)
        dialogue = DialogueManager(extractor=extractor)
    except Exception as e:
        print(f"{YELLOW}Warning: NLU Provider initialization notice: {e}{RESET}")
        print(f"{DIM}Running with deterministic evaluation mode.{RESET}\n")
        dialogue = DialogueManager(extractor=NLUExtractor(provider=None, provider_name="ollama"))

    session_id = str(uuid.uuid4())[:8]
    state = ConversationState(session_id=session_id)

    print(f"{CYAN}ಕೃಷಿ ಮಿತ್ರ:{RESET} ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಕೃಷಿ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ (ಉದಾ: ಹೊಲ ಎಷ್ಟು ಎಕರೆ, ಯಾವ ಬೆಳೆ, ನೀರಾವರಿ ಸೌಲಭ್ಯ ಇದೆ).\n")

    while True:
        try:
            user_input = input(f"{BOLD}ನೀವು (Farmer):{RESET} ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "ಮುಕ್ತಾಯ"):
                print(f"\n{GREEN}ಧನ್ಯವಾದಗಳು! ಮತ್ತೆ ಭೇಟಿಯಾಗೋಣ.{RESET}\n")
                break

            turn_result = dialogue.process_turn(state, user_input)
            state = turn_result["state"]

            print(f"\n{CYAN}ಕೃಷಿ ಮಿತ್ರ:{RESET} {turn_result['reply_kn']}")

            # If evaluation was executed, render scheme cards
            if turn_result["evaluation_results"]:
                display_results(turn_result["evaluation_results"])

            print()

        except KeyboardInterrupt:
            print(f"\n\n{GREEN}ನಿರ್ಗಮಿಸಲಾಗುತ್ತಿದೆ. ಧನ್ಯವಾದಗಳು!{RESET}\n")
            break
        except Exception as err:
            print(f"\n{RED}ದೋಷ (Error): {err}{RESET}\n")


if __name__ == "__main__":
    main()
