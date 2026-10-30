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

from backend.web_server import APIError, handle_chat as run_groq_chat, handle_voice_turn

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


def _session_context(session_id: str, profile: Dict[str, Any], history: List[Dict[str, str]]):
    session = sessions.setdefault(session_id, {"profile": {}, "history": []})
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
def handle_chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())[:8]
    session = _session_context(session_id, req.profile, req.history)
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
    _record_turn(session, req.message.strip(), result["reply"])
    return _format_response(session_id, result)


@app.post("/api/voice-turn", response_model=ChatResponse)
def voice_turn(req: VoiceTurnRequest):
    session_id = req.session_id or str(uuid.uuid4())[:8]
    session = _session_context(session_id, req.profile, req.history)
    payload = req.model_dump(exclude={"session_id"})
    payload["profile"] = dict(session["profile"])
    payload["history"] = [dict(turn) for turn in session["history"]]
    try:
        result = handle_voice_turn(payload, request_id=uuid.uuid4().hex[:12])
    except APIError as error:
        raise HTTPException(status_code=error.status, detail=str(error)) from error

    session["profile"] = result["profile"]
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


# Mount assets folder for videos, images, and audio
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
