"""FastAPI entry — Vaani's HTTP surface.

Endpoints:
  GET  /                    — single-page UI (phone-frame)
  GET  /health              — engine + version
  GET  /tools               — registered tool definitions (judges' transparency)
  GET  /samples             — list bundled demo papers
  POST /turn                — one inference turn (multipart: text | audio | image)

The server never makes outbound calls during normal operation. Inference is local;
TTS is browser-side. The only env var that matters at app runtime is VAANI_FORCE_STUB.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import tools
from app.inference import Inference, NoBackendError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("vaani")

ROOT = Path(__file__).parent.parent
STATIC_DIR = ROOT / "static"
SAMPLES_DIR = ROOT / "samples"

app = FastAPI(title="Vaani", version="0.1.0", docs_url="/docs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/samples", StaticFiles(directory=SAMPLES_DIR), name="samples")


@app.middleware("http")
async def _no_cache_static(request, call_next):
    """Don't let browsers cache /static — the app evolves rapidly during a
    demo and stale CSS/JS makes verification miserable."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response

# Single Inference instance — backend is chosen once at startup.
# NoBackendError is caught so /health can guide the user to docs/SETUP.md
# rather than crashing the whole process.
INFERENCE: Optional[Inference]
_BACKEND_ERROR: Optional[str] = None
try:
    INFERENCE = Inference()
    log.info("vaani: engine=%s, stub=%s", INFERENCE.engine_name, INFERENCE.is_stub)
except NoBackendError as e:
    INFERENCE = None
    _BACKEND_ERROR = str(e)
    log.error("Vaani has no backend configured:\n%s", e)


class HealthResponse(BaseModel):
    status: str
    engine: str
    is_stub: bool
    version: str


class ToolDef(BaseModel):
    name: str
    description: str


class FnCall(BaseModel):
    name: str
    args: dict


class TurnResponse(BaseModel):
    transcript: str
    reply_text: str
    language: str
    fn_calls: List[FnCall]
    engine: str
    elapsed_ms: int


@app.get("/", response_class=FileResponse)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if INFERENCE is None:
        return HealthResponse(
            status="no_backend", engine="—", is_stub=False, version="0.1.0",
        )
    return HealthResponse(
        status="ok",
        engine=INFERENCE.engine_name,
        is_stub=INFERENCE.is_stub,
        version="0.1.0",
    )


@app.get("/tools", response_model=List[ToolDef])
def list_tools() -> List[ToolDef]:
    out = []
    for d in tools.TOOL_DEFINITIONS:
        f = d["function"]
        out.append(ToolDef(name=f["name"], description=f["description"]))
    return out


@app.get("/samples")
def list_samples() -> JSONResponse:
    if not SAMPLES_DIR.exists():
        return JSONResponse({"samples": []})
    out = []
    for p in sorted(SAMPLES_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            out.append({"name": p.name, "url": f"/samples/{p.name}"})
    return JSONResponse({"samples": out})


@app.post("/turn", response_model=TurnResponse)
async def turn(
    text: Optional[str] = Form(default=None),
    lang: str = Form(default="hi"),
    image_filename: Optional[str] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    audio: Optional[UploadFile] = File(default=None),  # noqa: ARG001  (browser-side STT used in demo)
) -> TurnResponse:
    """One conversational turn.

    The audio file is accepted for forward-compatibility with backends B (HF)
    and a future Backend D that runs Gemma 4 E4B with native audio. For tonight
    the in-app speech-to-text is browser-side (Web Speech API), so the server
    receives the resulting *text* in `text`.
    """
    if INFERENCE is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": "no_backend",
                "detail": _BACKEND_ERROR or "no Gemma 4 backend configured — see docs/SETUP.md",
            },
        )

    image_b64: Optional[str] = None
    fname: Optional[str] = image_filename
    if image is not None:
        raw = await image.read()
        image_b64 = base64.b64encode(raw).decode("ascii")
        fname = fname or image.filename

    result = INFERENCE.generate(
        user_text=text, image_b64=image_b64, image_filename=fname, lang=lang
    )
    return TurnResponse(
        transcript=text or "",
        reply_text=result.reply_text,
        language=result.language,
        fn_calls=[FnCall(name=fc["name"], args=fc.get("args", {})) for fc in result.fn_calls],
        engine=result.engine,
        elapsed_ms=result.elapsed_ms,
    )


@app.get("/info")
def info() -> dict:
    """Verbose info — used by the README's `make demo` smoke check."""
    if INFERENCE is None:
        return {
            "name": "Vaani",
            "tagline": "If you can speak, you can use the internet.",
            "engine": None,
            "is_stub": False,
            "backend_error": _BACKEND_ERROR,
            "tools": tools.names(),
            "endpoints": ["/", "/health", "/tools", "/samples", "/turn", "/info"],
            "offline": False,
            "upstream_calls": "n/a — no backend configured",
        }
    engine = INFERENCE.engine_name
    is_local = engine.startswith("ollama/") or INFERENCE.is_stub
    return {
        "name": "Vaani",
        "tagline": "If you can speak, you can use the internet.",
        "engine": engine,
        "is_stub": INFERENCE.is_stub,
        "tools": tools.names(),
        "endpoints": ["/", "/health", "/tools", "/samples", "/turn", "/info"],
        "offline": is_local,
        "upstream_calls": (
            "none during normal operation"
            if is_local
            else f"calls upstream API for {engine.split('/')[0]}"
        ),
    }
