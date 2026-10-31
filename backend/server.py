"""
Krishi Mitra — FastAPI Backend Server
Integrates conversational AI dialogue management with the web frontend.
Provides:
  - Authentication & Authorization: Phone + OTP, JWT, Rotating Refresh Tokens, RBAC
  - DPDP Consent Management: Explicit, informed, revocable voice consent & right to erasure
  - POST /api/chat: Multi-turn farmer dialogue processing with NLU and deterministic evaluation (Protected)
  - POST /api/voice-turn: Audio processing with Sarvam and Groq (Protected by require_voice_consent)
  - GET /api/health: Service status and model configuration (Public)
  - Static file serving for index.html, chat.html, stitch_design.html, web_app.js, and assets/
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
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

from backend.web_server import APIError, handle_chat as run_groq_chat, handle_voice_turn
from backend.db.database import init_db
from backend.db.models import User
from backend.auth import (
    auth_router,
    admin_router,
    get_current_user,
    assert_production_config,
)
from backend.consent import (
    consent_router,
    user_privacy_router,
    require_voice_consent,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify production requirements
    assert_production_config()
    # Ensure database tables exist
    init_db()
    yield


app = FastAPI(title="Krishi Mitra API", version="1.0.0", lifespan=lifespan)

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(consent_router)
app.include_router(user_privacy_router)

# In-memory session store (DPDP 2023 data minimisation: in-process per-session state bound to user_id)
sessions: Dict[str, Dict[str, Any]] = {}


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., description="Farmer utterance in Kannada or English")
    language: Optional[str] = Field("kn", description="Language preference: 'kn' or 'en'")
    profile: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, str]] = Field(default_factory=list)


class VoiceTurnRequest(BaseModel):
    session_id: Optional[str] = None
    audio: str = Field(..., max_length=5_600_000)
    mime_type: str
    recording_duration_ms: Optional[int] = None
    language: Optional[str] = Field("kn", description="Language preference: 'kn' or 'en'")
    profile: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    reply_kn: str = ""
    transcript: Optional[str] = None
    detected_language: Optional[str] = None
    audio: Optional[str] = None
    mime_type: Optional[str] = None
    model_mode: Optional[str] = None
    missing_slots: List[str] = Field(default_factory=list)
    is_profile_complete: bool
    farmer_profile: Dict[str, Any] = Field(default_factory=dict)
    evaluation_results: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


@app.get("/api/health")
def health_check():
    has_groq_key = bool(os.getenv("GROQ_API_KEY"))
    has_sarvam_key = bool(os.getenv("SARVAM_API_KEY"))
    return {
        "status": "healthy",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "has_groq_key": has_groq_key,
        "has_sarvam_key": has_sarvam_key,
        "active_sessions": len(sessions),
    }


def _session_context(session_id: str, profile: Dict[str, Any], history: List[Dict[str, str]], user_id: str):
    """
    Retrieves or initializes session state bound to user_id.
    Prevents IDOR by blocking cross-user session reads or writes.
    """
    if session_id in sessions:
        session = sessions[session_id]
        owner_id = session.get("user_id")
        if owner_id and owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: session belongs to another user",
            )
    else:
        session = sessions.setdefault(session_id, {"profile": {}, "history": [], "user_id": user_id})

    session["user_id"] = user_id
    session["profile"].update(profile)
    if history:
        session["history"] = history[-8:]
    return session


def _profile_is_complete(profile: Dict[str, Any]) -> bool:
    return all(profile.get(field) for field in ("district", "land_acres", "crops", "irrigation_type"))


def _format_response(session_id: str, result: Dict[str, Any]) -> ChatResponse:
    profile = result["profile"]
    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        reply_kn=result["reply"] if result.get("language") == "kn" else "",
        transcript=result.get("transcript"),
        detected_language=result.get("detected_language"),
        audio=result.get("audio"),
        mime_type=result.get("mime_type"),
        model_mode=result.get("model_mode"),
        missing_slots=result.get("missing_slots", []),
        is_profile_complete=_profile_is_complete(profile),
        farmer_profile=profile,
        evaluation_results=(
            result["evaluations"] if result.get("show_evaluations") else []
        ),
        warnings=[],
    )


def _record_turn(session: Dict[str, Any], message: str, reply: str) -> None:
    session["history"].extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ])
    session["history"] = session["history"][-8:]


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    session_id = req.session_id or str(uuid.uuid4())[:8]
    session = _session_context(session_id, req.profile, req.history, user_id)
    payload = {
        "message": req.message,
        "language": req.language,
        "profile": dict(session["profile"]),
        "history": [dict(turn) for turn in session["history"]],
    }
    try:
        result = run_groq_chat(payload, request_id=uuid.uuid4().hex[:12])
    except APIError as error:
        raise HTTPException(status_code=error.status, detail=str(error)) from error

    session["profile"] = result["profile"]
    # DPDP 2023: Retain transcript turns only if user explicitly opted in to history saving
    if getattr(current_user, "save_history", False):
        _record_turn(session, req.message.strip(), result["reply"])
    return _format_response(session_id, result)


@app.post("/api/voice-turn", response_model=ChatResponse)
def voice_turn(req: VoiceTurnRequest, current_user: User = Depends(require_voice_consent)):
    user_id = str(current_user.id)
    session_id = req.session_id or str(uuid.uuid4())[:8]
    session = _session_context(session_id, req.profile, req.history, user_id)
    payload = req.model_dump(exclude={"session_id"})
    payload["profile"] = dict(session["profile"])
    payload["history"] = [dict(turn) for turn in session["history"]]
    try:
        result = handle_voice_turn(payload, request_id=uuid.uuid4().hex[:12])
    except APIError as error:
        raise HTTPException(status_code=error.status, detail=str(error)) from error

    session["profile"] = result["profile"]
    # DPDP 2023: Retain transcript turns only if user explicitly opted in to history saving
    if getattr(current_user, "save_history", False):
        _record_turn(session, result["transcript"], result["reply"])
    return _format_response(session_id, result)


# Serve root static pages
@app.get("/")
@app.get("/index.html")
def serve_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Krishi Mitra API running"}


@app.get("/chat")
@app.get("/chat.html")
def serve_chat():
    chat_path = os.path.join(BASE_DIR, "chat.html")
    if os.path.exists(chat_path):
        return FileResponse(chat_path)
    return {"message": "chat.html not found"}


@app.get("/stitch")
@app.get("/stitch.html")
@app.get("/stitch_design.html")
def serve_stitch():
    stitch_path = os.path.join(BASE_DIR, "stitch_design.html")
    if os.path.exists(stitch_path):
        return FileResponse(stitch_path)
    return {"message": "stitch_design.html not found"}


@app.get("/web_app.js")
def serve_web_app():
    js_path = os.path.join(BASE_DIR, "web_app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="web_app.js not found")


# Mount assets folder for videos, images, and audio
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
