"""
Krishi Mitra — FastAPI Backend Server
Integrates conversational AI dialogue management with the web frontend.
Provides:
  - POST /api/chat: Multi-turn farmer dialogue processing with NLU and deterministic evaluation
  - GET /api/health: Service status and model configuration
  - Static file serving for index.html, chat.html, stitch_design.html, and assets/
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

from backend.rules_engine import SchemeEvaluator, EvaluationResult, FarmerProfile
from backend.nlu.extractor import NLUExtractor
from backend.nlu.providers import get_provider
from backend.conversation.state import ConversationState, is_profile_complete
from backend.conversation.dialogue import DialogueManager

app = FastAPI(title="Krishi Mitra API", version="1.0.0")

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (DPDP 2023 data minimisation: in-process per-session state)
sessions: Dict[str, ConversationState] = {}

# Lazy-loaded singleton managers
_evaluator: Optional[SchemeEvaluator] = None
_dialogue_manager: Optional[DialogueManager] = None


def get_dialogue_manager() -> DialogueManager:
    global _evaluator, _dialogue_manager
    if _dialogue_manager is None:
        if _evaluator is None:
            _evaluator = SchemeEvaluator()
        try:
            extractor = NLUExtractor()
        except Exception as e:
            # Fallback to offline ollama provider if API key missing
            extractor = NLUExtractor(provider_name="ollama")
        _dialogue_manager = DialogueManager(extractor=extractor, evaluator=_evaluator)
    return _dialogue_manager


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., description="Farmer utterance in Kannada or English")
    language: Optional[str] = Field("kn", description="Language preference: 'kn' or 'en'")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    reply_kn: str
    missing_slots: List[str]
    is_profile_complete: bool
    farmer_profile: Dict[str, Any]
    evaluation_results: List[Dict[str, Any]]
    warnings: List[str]


@app.get("/api/health")
def health_check():
    provider_name = os.getenv("NLU_PROVIDER", "gemini")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    has_gemini_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "provider": provider_name,
        "model": model_name,
        "has_gemini_key": has_gemini_key,
        "active_sessions": len(sessions),
    }


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())[:8]
    if session_id not in sessions:
        sessions[session_id] = ConversationState(session_id=session_id)

    state = sessions[session_id]
    dm = get_dialogue_manager()

    turn_output = dm.process_turn(state, req.message.strip())
    sessions[session_id] = turn_output["state"]

    eval_results_data = []
    for r in turn_output["evaluation_results"]:
        eval_results_data.append({
            "scheme_id": r.scheme_id,
            "scheme_name_kn": r.scheme_name_kn,
            "scheme_name_en": r.scheme_name_en,
            "status": r.status,
            "is_demo": r.is_demo,
            "benefit_summary_kn": r.benefit_summary_kn,
            "benefit_summary_en": r.benefit_summary_en,
            "audit_trail": r.audit_trail,
            "disqualification_reasons": r.disqualification_reasons,
            "required_documents": r.required_documents,
            "disclaimer_kn": r.disclaimer_kn,
        })

    is_complete = is_profile_complete(turn_output["state"])
    reply_text = turn_output["reply_kn"]

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        reply_kn=turn_output["reply_kn"],
        missing_slots=turn_output["missing_slots"],
        is_profile_complete=is_complete,
        farmer_profile=turn_output["state"].confirmed_profile,
        evaluation_results=eval_results_data,
        warnings=turn_output["warnings"],
    )


# Serve root static pages
@app.get("/")
def serve_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Krishi Mitra API running"}


@app.get("/chat")
def serve_chat():
    chat_path = os.path.join(BASE_DIR, "chat.html")
    if os.path.exists(chat_path):
        return FileResponse(chat_path)
    return {"message": "chat.html not found"}


@app.get("/stitch")
def serve_stitch():
    stitch_path = os.path.join(BASE_DIR, "stitch_design.html")
    if os.path.exists(stitch_path):
        return FileResponse(stitch_path)
    return {"message": "stitch_design.html not found"}


# Mount assets folder for videos, images, and audio
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
