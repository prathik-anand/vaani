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
import re
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


_INDIC_RANGES = (
    (0x0900, 0x097F),  # Devanagari (Hindi/Marathi/Sanskrit)
    (0x0980, 0x09FF),  # Bengali
    (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Oriya
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
)


def _is_indic(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _INDIC_RANGES)


_TOOL_NAMES = (
    "set_reminder", "flag_red_flag", "draft_reply",
    "prepare_questions_for_clinic", "lookup_medicine_meaning",
)


def _line_is_meta(line: str) -> bool:
    """True if the line is clearly model meta-commentary, not user-facing reply.

    Conservative — we'd rather leak a tiny bit of meta than strip the reply.
    Romanized Indic content (Tanglish, Hinglish) is intentionally kept.
    """
    s = line.strip()
    if not s:
        return False
    # Numbered scratchpad item, e.g.  "1. " or "6.  **..."
    if re.match(r"^\d+\.\s", s):
        return True
    # Markdown-style internal heading or bullet
    if re.match(r"^(\*\*|##\s|###\s|>\s|\*\s)", s):
        return True
    # Indented field-like line: "   * symptom:" or "   - reason:"
    if re.match(r"^[\*\-]\s+\w+:", s) or re.match(r"^\w+\s*:\s*[\"`]", s):
        return True
    # Mentions a tool name in backticks or after "function call"
    sl = s.lower()
    for tn in _TOOL_NAMES:
        if f"`{tn}`" in s or f"`{tn}(" in s:
            return True
    if "function call" in sl and ("`" in s or ":" in s):
        return True
    # Sentence starts with an English planning prefix
    starts = (
        "i will ", "i'll ", "let me ", "let's ", "plan:", "response:",
        "response draft:", "the user is asking", "the user wants",
        "i should ", "okay,", "alright,", "thinking:", "analysis:",
        "reasoning:", "i need to ", "i'm going to ", "now i ",
    )
    if any(sl.startswith(p) for p in starts):
        return True
    return False


def _try_parse_json_object(s: str) -> Optional[Dict[str, Any]]:
    """Tolerant parse: clean parse first, then regex-extract the first balanced
    {...} object from anywhere in `s`. Returns None if nothing valid is found."""
    if not s:
        return None
    s = s.strip()
    # Clean parse
    try:
        v = json.loads(s)
        if isinstance(v, dict):
            return v
    except (json.JSONDecodeError, ValueError):
        pass
    # Find the first '{' and walk for its balanced match
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if esc:
            esc = False; continue
        if c == "\\":
            esc = True; continue
        if c == '"':
            in_str = not in_str; continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start : i + 1]
                try:
                    v = json.loads(candidate)
                    if isinstance(v, dict):
                        return v
                except (json.JSONDecodeError, ValueError):
                    return None
    return None


def _filter_args_for_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Drop args keys that aren't in the chosen tool's parameter schema."""
    for t in tools.TOOL_DEFINITIONS:
        if t["function"]["name"] == name:
            allowed = set(t["function"]["parameters"].get("properties", {}).keys())
            return {k: v for k, v in args.items() if k in allowed}
    return args


def _clean_reply(text: str) -> str:
    """Drop chain-of-thought / meta-commentary; keep the user-facing reply.

    Strategy: split into lines, drop meta lines, keep the rest. If the result
    is empty (all lines looked meta), fall back to the original — better to
    show garbage than nothing.
    """
    if not text:
        return ""
    lines = text.splitlines()
    kept = [ln for ln in lines if not _line_is_meta(ln)]
    cleaned = "\n".join(kept).strip()
    # If we accidentally stripped everything, fall back
    if not cleaned:
        cleaned = text.strip()
    # Strip wrapping quotes if model echoed the reply quoted
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()
    # Collapse internal blank-line runs
    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()
    return cleaned


# ── Backend: Google AI Studio ───────────────────────────────────────────────

class _AIStudio:
    """Google AI Studio (Generative Language API). Free tier.

    Verified live model IDs (queried 2026-05-03 via /v1beta/models):
      - gemma-4-26b-a4b-it    (MoE, 4B active per token — fastest)
      - gemma-4-31b-it        (dense, top quality)
      - gemma-3n-e4b-it       (Gemma 3 nano fallback if Gemma 4 unavailable)
    """
    MODEL = "gemma-4-26b-a4b-it"  # if AI Studio renames the SKU, edit this line.
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, key: str):
        self.key = key
        self.client = httpx.Client(timeout=120)

    # Flat schema: tool_call.args is a single object whose properties are the
    # union of every tool's parameters. Gemma 4 fills only the relevant subset.
    _ALL_ARG_PROPS: Dict[str, Any] = {}
    for _t in tools.TOOL_DEFINITIONS:
        for _k, _v in _t["function"]["parameters"].get("properties", {}).items():
            # If the same key appears in multiple tools, take the first (they all
            # have compatible types in this surface).
            _ALL_ARG_PROPS.setdefault(_k, _v)

    _RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "The 1-2 sentence spoken reply, in the user's language. No planning, no English meta-commentary.",
            },
            "tool_call": {
                "type": "object",
                "description": "Optional. If set, name must be one of the listed tools and args must be filled per that tool's parameters.",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": [t["function"]["name"] for t in tools.TOOL_DEFINITIONS],
                    },
                    "args": {
                        "type": "object",
                        "properties": _ALL_ARG_PROPS,
                    },
                },
            },
        },
        "required": ["reply"],
    }

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

        # Inline tool docs WITH full parameter schema into the system prompt.
        # Gemma-via-AIStudio reliably honours responseSchema but not tools[],
        # so we encode the tool surface in plain text the model can reason over.
        tool_blocks = []
        for t in tools.TOOL_DEFINITIONS:
            f = t["function"]
            params = f["parameters"]
            props = params.get("properties", {})
            required = params.get("required", [])
            arg_lines = []
            for pname, pspec in props.items():
                marker = " (required)" if pname in required else ""
                ptype = pspec.get("type", "string")
                pdesc = pspec.get("description", "")
                arg_lines.append(f"    - {pname} ({ptype}){marker}: {pdesc}")
            tool_blocks.append(
                f"  • {f['name']}\n"
                f"    {f['description']}\n"
                + "\n".join(arg_lines)
            )
        tools_doc = "\n".join(tool_blocks)
        sys_prompt = SYSTEM_PROMPT + (
            "\n\nWHEN TO CALL A TOOL — set tool_call.{name, args} to one of these "
            "when it would help. Always populate every required arg. Examples of "
            "well-formed args:\n"
            "  set_reminder → {\"med\": \"Amoxicillin 500mg\", \"times\": [\"08:00\",\"20:00\"], \"days\": 7}\n"
            "  flag_red_flag → {\"symptom\": \"fever 102F + fast breathing in infant\", \"reason\": \"needs same-day care\"}\n"
            "  prepare_questions_for_clinic → {\"topic\": \"diabetes follow-up\", \"language\": \"hi\"}\n"
            "  draft_reply → {\"recipient\": \"school\", \"intent\": \"I will attend the meeting\", \"language\": \"hi\"}\n"
            "  lookup_medicine_meaning → {\"name\": \"Amoxicillin\", \"language\": \"hi\"}\n"
            "Omit tool_call entirely if no action helps.\n\n"
            "FULL TOOL SURFACE:\n" + tools_doc
        )

        body: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "system_instruction": {"parts": [{"text": sys_prompt}]},
            "generation_config": {
                "temperature": 0.2,
                "max_output_tokens": 800,
                "response_mime_type": "application/json",
                "response_schema": self._RESPONSE_SCHEMA,
            },
        }

        url = f"{self.BASE}/{self.MODEL}:generateContent?key={self.key}"
        r = self.client.post(url, json=body)
        if r.status_code != 200:
            raise RuntimeError(f"AI Studio {r.status_code}: {r.text[:300]}")

        data = r.json()
        text_parts: List[str] = []
        for p in (data.get("candidates") or [{}])[0].get("content", {}).get("parts", []) or []:
            if p.get("text"):
                text_parts.append(p["text"])
        raw = "\n".join(text_parts).strip()

        parsed = _try_parse_json_object(raw)
        reply_text = ""
        fn_calls: List[Dict[str, Any]] = []
        if parsed is not None:
            reply_text = (parsed.get("reply") or "").strip()
            tc = parsed.get("tool_call")
            if isinstance(tc, dict) and tc.get("name"):
                fn_calls.append({
                    "name": tc["name"],
                    "args": _filter_args_for_tool(tc["name"], tc.get("args") or {}),
                })
        # If reply parsed empty or degenerate (model wrote just punctuation),
        # extract a real sentence from the raw text via the heuristic cleaner.
        if len(reply_text) < 10 or all(not c.isalnum() for c in reply_text):
            log.info("AI Studio: schema reply looked degenerate, falling back to cleaner")
            cleaned = _clean_reply(raw)
            if len(cleaned) > len(reply_text):
                reply_text = cleaned

        return TurnResult(
            reply_text=reply_text,
            fn_calls=fn_calls,
            language=lang or "hi",
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
            reply_text=_clean_reply(text), fn_calls=fn_calls, language=lang or "hi",
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
            reply_text=_clean_reply(text), fn_calls=fn_calls, language=lang or "hi",
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
