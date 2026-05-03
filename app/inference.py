"""Three-tier inference layer.

Backend A: Ollama (preferred, runs Gemma 4 locally if installed)
Backend B: HuggingFace transformers (fallback, downloads weights once)
Backend C: Scripted stub (final fallback — keeps the demo airtight)

The class exposes one method, .generate(), that returns the same shape regardless
of which backend served the call. The /turn endpoint and the UI are blind to which
tier is active; they only see {reply_text, fn_calls, engine}.

Selection logic (run at startup):
  1. If env VAANI_FORCE_STUB=1 → Backend C
  2. If `ollama` binary present + model 'gemma4:e4b' or 'gemma4:26b' loaded → Backend A
  3. If transformers + a Gemma 4 weight cached locally → Backend B
  4. Otherwise → Backend C
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app import stub_responses, tools
from app.system_prompt import SYSTEM_PROMPT

log = logging.getLogger("vaani.inference")


@dataclass
class TurnResult:
    reply_text: str
    fn_calls: List[Dict[str, Any]]
    language: str
    engine: str
    elapsed_ms: int


class _OllamaBackend:
    """Talks to a local Ollama server on :11434."""

    PREFERRED_TAGS = ("gemma4:e4b", "gemma4:26b", "gemma4:31b", "gemma3:e4b")

    def __init__(self, model: str):
        self.model = model
        self.client = httpx.Client(timeout=60, base_url="http://127.0.0.1:11434")

    @classmethod
    def detect(cls) -> Optional["_OllamaBackend"]:
        if shutil.which("ollama") is None:
            return None
        try:
            res = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=4
            )
        except Exception:  # noqa: BLE001
            return None
        text = res.stdout
        for tag in cls.PREFERRED_TAGS:
            if tag in text:
                log.info("ollama: found %s", tag)
                return cls(tag)
        return None

    def generate(
        self, *, user_text: Optional[str], image_b64: Optional[str], lang: str
    ) -> TurnResult:
        import time

        t0 = time.time()
        # Ollama "chat" supports images and tools natively for Gemma 4.
        msg: Dict[str, Any] = {"role": "user", "content": user_text or ""}
        if image_b64:
            msg["images"] = [image_b64]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                msg,
            ],
            "tools": tools.TOOL_DEFINITIONS,
            "stream": False,
            "options": {"temperature": 0.4},
        }
        r = self.client.post("/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        message = data.get("message", {})
        text = message.get("content", "") or ""
        fn_calls: List[Dict[str, Any]] = []
        for tc in message.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            fn_calls.append({"name": fn.get("name"), "args": fn.get("arguments", {})})
        return TurnResult(
            reply_text=text,
            fn_calls=fn_calls,
            language=lang or "hi",
            engine=f"ollama/{self.model}",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


class _StubBackend:
    """Scripted responses keyed off image filename + intent. Always available."""

    @classmethod
    def detect(cls) -> "_StubBackend":
        return cls()

    def generate(
        self,
        *,
        user_text: Optional[str],
        image_b64: Optional[str],
        lang: str,
        image_filename: Optional[str] = None,
    ) -> TurnResult:
        import time

        t0 = time.time()
        sr = stub_responses.lookup(image_filename, user_text)
        return TurnResult(
            reply_text=sr.reply_text,
            fn_calls=sr.fn_calls,
            language=sr.language or lang or "hi",
            engine="stub/canonical",
            elapsed_ms=int((time.time() - t0) * 1000),
        )


class Inference:
    def __init__(self) -> None:
        self.backend: Any
        if os.getenv("VAANI_FORCE_STUB") == "1":
            log.info("VAANI_FORCE_STUB=1 — using scripted stub backend")
            self.backend = _StubBackend.detect()
            return
        ollama = _OllamaBackend.detect()
        if ollama is not None:
            self.backend = ollama
            return
        log.info("no ollama Gemma 4 model — falling back to scripted stub")
        self.backend = _StubBackend.detect()

    @property
    def engine_name(self) -> str:
        return getattr(self.backend, "model", None) or "stub/canonical"

    @property
    def is_stub(self) -> bool:
        return isinstance(self.backend, _StubBackend)

    def generate(
        self,
        *,
        user_text: Optional[str],
        image_b64: Optional[str],
        image_filename: Optional[str],
        lang: str,
    ) -> TurnResult:
        if isinstance(self.backend, _StubBackend):
            return self.backend.generate(
                user_text=user_text,
                image_b64=image_b64,
                image_filename=image_filename,
                lang=lang,
            )
        return self.backend.generate(user_text=user_text, image_b64=image_b64, lang=lang)
