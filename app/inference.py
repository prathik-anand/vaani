"""Gemma 4 inference layer — auto-selects whichever backend is available.

Selection is implicit. Whichever access path you've configured wins:

  - GEMINI_API_KEY in env       → Google AI Studio
  - OPENROUTER_API_KEY in env   → OpenRouter
  - `ollama list` has a Gemma 4 → local Ollama
  - none of the above           → refuse to start, point user at SETUP.md

If multiple are configured, AI Studio wins, then OpenRouter, then local. (When
you've put in the effort to set a key, you almost certainly want to be hitting
that path — local Ollama is the deploy target, not the dev path.)

The model running on the other end is Gemma 4 in all three cases. The
TurnResult schema, function-call surface, and UX are identical regardless.

Test mode: VAANI_FORCE_STUB=1 forces the scripted stub. Production never uses it.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app import stub_responses, tools
from app.system_prompt import SYSTEM_PROMPT

log = logging.getLogger("vaani.inference")


# ── secrets file loader ─────────────────────────────────────────────────────

def _load_secrets_file() -> None:
    """Pull keys from a .env file into os.environ, in priority order:
      1. $VAANI_ENV_FILE (explicit override)
      2. ./.env in the project root (preferred — portable, per-clone)
      3. ~/.vaani/.env (user-wide; useful if you run multiple clones)
    Anything that's already set in the real environment wins; .env never
    overrides an explicit export.
    """
    candidates: List[Path] = []
    if env_file := os.getenv("VAANI_ENV_FILE"):
        candidates.append(Path(env_file))
    candidates.append(Path(__file__).resolve().parent.parent / ".env")
    candidates.append(Path.home() / ".vaani" / ".env")
    for p in candidates:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_secrets_file()


@dataclass
class TurnResult:
    reply_text: str
    fn_calls: List[Dict[str, Any]]
    language: str
    engine: str
    elapsed_ms: int


# ── Backend: Google AI Studio ───────────────────────────────────────────────

class _AIStudio:
    """Google AI Studio (Generative Language API). Free tier."""
    MODEL = "gemma-4-27b-it"  # if AI Studio renames the SKU, edit this line.
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, key: str):
        self.key = key
        self.client = httpx.Client(timeout=120)

    def generate(self, *, user_text, image_b64, image_filename, lang) -> TurnResult:
        t0 = time.time()
        parts: List[Dict[str, Any]] = []
        if user_text:
            parts.append({"text": user_text})
        if image_b64:
            mime = "image/png" if (image_filename or "").lower().endswith(".png") else "image/jpeg"
            parts.append({"inline_data": {"mime_type": mime, "data": image_b64}})
        if not parts:
            parts.append({"text": "(no input)"})

        body: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generation_config": {"temperature": 0.4, "max_output_tokens": 800},
        }
        body_with_tools = dict(body, tools=[{
            "function_declarations": [
                {"name": t["function"]["name"],
                 "description": t["function"]["description"],
                 "parameters": t["function"]["parameters"]}
                for t in tools.TOOL_DEFINITIONS
            ]
        }])

        url = f"{self.BASE}/{self.MODEL}:generateContent?key={self.key}"
        r = self.client.post(url, json=body_with_tools)
        if r.status_code == 400 and "tool" in r.text.lower():
            log.info("AI Studio rejected tools, retrying without")
            r = self.client.post(url, json=body)
        if r.status_code != 200:
            raise RuntimeError(f"AI Studio {r.status_code}: {r.text[:300]}")

        data = r.json()
        text_parts: List[str] = []
        fn_calls: List[Dict[str, Any]] = []
        for p in (data.get("candidates") or [{}])[0].get("content", {}).get("parts", []) or []:
            if p.get("text"):
                text_parts.append(p["text"])
            if "functionCall" in p:
                fc = p["functionCall"]
                fn_calls.append({"name": fc.get("name"), "args": fc.get("args", {})})
        return TurnResult(
            reply_text="\n".join(text_parts).strip(),
            fn_calls=fn_calls, language=lang or "hi",
            engine=f"aistudio/{self.MODEL}",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


# ── Backend: OpenRouter ─────────────────────────────────────────────────────

class _OpenRouter:
    MODEL = "google/gemma-4-27b-it"
    BASE = "https://openrouter.ai/api/v1"

    def __init__(self, key: str):
        self.client = httpx.Client(
            timeout=120, base_url=self.BASE,
            headers={
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://github.com/prathik-anand/vaani",
                "X-Title": "Vaani",
            },
        )

    def generate(self, *, user_text, image_b64, image_filename, lang) -> TurnResult:
        t0 = time.time()
        content: List[Dict[str, Any]] = []
        if user_text:
            content.append({"type": "text", "text": user_text})
        if image_b64:
            mime = "image/png" if (image_filename or "").lower().endswith(".png") else "image/jpeg"
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_b64}"}})
        if not content:
            content.append({"type": "text", "text": "(no input)"})

        body = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            "tools": tools.TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "temperature": 0.4,
        }
        r = self.client.post("/chat/completions", json=body)
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter {r.status_code}: {r.text[:300]}")
        data = r.json()
        msg = (data.get("choices") or [{}])[0].get("message", {})
        text = msg.get("content", "") or ""
        fn_calls: List[Dict[str, Any]] = []
        for tc in msg.get("tool_calls") or []:
            f = tc.get("function") or {}
            try:
                args = json.loads(f.get("arguments", "{}"))
            except Exception:
                args = {}
            fn_calls.append({"name": f.get("name"), "args": args})
        return TurnResult(
            reply_text=text, fn_calls=fn_calls, language=lang or "hi",
            engine=f"openrouter/{self.MODEL}",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


# ── Backend: local Ollama ───────────────────────────────────────────────────

class _Ollama:
    PREFERRED = ("gemma4:e4b", "gemma4:e2b", "gemma4:26b", "gemma4:31b")

    def __init__(self, model: str):
        self.model = model
        self.client = httpx.Client(timeout=180, base_url="http://127.0.0.1:11434")

    @classmethod
    def detect(cls) -> Optional["_Ollama"]:
        forced = os.getenv("VAANI_OLLAMA_MODEL")
        if forced:
            return cls(forced) if shutil.which("ollama") else None
        if not shutil.which("ollama"):
            return None
        try:
            res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=4)
        except Exception:
            return None
        for tag in cls.PREFERRED:
            if tag in res.stdout:
                return cls(tag)
        return None

    def generate(self, *, user_text, image_b64, image_filename, lang) -> TurnResult:
        t0 = time.time()
        msg: Dict[str, Any] = {"role": "user", "content": user_text or ""}
        if image_b64:
            msg["images"] = [image_b64]
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, msg],
            "tools": tools.TOOL_DEFINITIONS,
            "stream": False,
            "options": {"temperature": 0.4},
        }
        r = self.client.post("/api/chat", json=body)
        r.raise_for_status()
        data = r.json()
        message = data.get("message", {})
        text = message.get("content", "") or ""
        fn_calls: List[Dict[str, Any]] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function", {})
            fn_calls.append({"name": fn.get("name"), "args": fn.get("arguments", {})})
        return TurnResult(
            reply_text=text, fn_calls=fn_calls, language=lang or "hi",
            engine=f"ollama/{self.model}",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


# ── Stub (test-only) ────────────────────────────────────────────────────────

class _Stub:
    def generate(self, *, user_text, image_b64, image_filename, lang) -> TurnResult:
        t0 = time.time()
        sr = stub_responses.lookup(image_filename, user_text)
        return TurnResult(
            reply_text=sr.reply_text, fn_calls=sr.fn_calls,
            language=sr.language or lang or "hi",
            engine="stub/canonical",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


# ── Selector ────────────────────────────────────────────────────────────────

class NoBackendError(RuntimeError):
    pass


class Inference:
    def __init__(self) -> None:
        if os.getenv("VAANI_FORCE_STUB") == "1":
            self.backend: Any = _Stub()
            return

        # Selection order: presence of a key is the signal.
        if k := (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            self.backend = _AIStudio(k)
            log.info("backend: aistudio (GEMINI_API_KEY found)")
            return
        if k := os.getenv("OPENROUTER_API_KEY"):
            self.backend = _OpenRouter(k)
            log.info("backend: openrouter (OPENROUTER_API_KEY found)")
            return
        if local := _Ollama.detect():
            self.backend = local
            log.info("backend: local (ollama %s)", local.model)
            return

        raise NoBackendError(
            "No Gemma 4 backend configured. Drop ONE of these in `./.env` "
            "(or `~/.vaani/.env`), then restart:\n"
            "  GEMINI_API_KEY=...        (https://aistudio.google.com/apikey, free)\n"
            "  OPENROUTER_API_KEY=...    (https://openrouter.ai/keys)\n"
            "  — OR install Ollama and run `ollama pull gemma4:e4b`\n"
            "See docs/SETUP.md for details."
        )

    @property
    def engine_name(self) -> str:
        b = self.backend
        if isinstance(b, _Ollama):     return f"ollama/{b.model}"
        if isinstance(b, _AIStudio):   return f"aistudio/{b.MODEL}"
        if isinstance(b, _OpenRouter): return f"openrouter/{b.MODEL}"
        if isinstance(b, _Stub):       return "stub/canonical"
        return "unknown"

    @property
    def is_stub(self) -> bool:
        return isinstance(self.backend, _Stub)

    def generate(self, *, user_text, image_b64, image_filename, lang) -> TurnResult:
        return self.backend.generate(
            user_text=user_text, image_b64=image_b64,
            image_filename=image_filename, lang=lang,
        )
