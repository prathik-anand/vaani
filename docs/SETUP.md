# Vaani — Setup

Vaani uses **Gemma 4** for inference. Pick one of three backends. The app's
behaviour, function-call surface, and UX are identical across all three.

```
┌──────────────────────────────────────────────┐
│  Backend A   local Ollama        (default)   │
│  Backend B   Google AI Studio                │
│  Backend C   OpenRouter                      │
└──────────────────────────────────────────────┘
```

There's no selector env var. Whichever credential you set wins:
- `GEMINI_API_KEY` set → AI Studio
- `OPENROUTER_API_KEY` set → OpenRouter
- otherwise → local Ollama (if installed)
- nothing set + no Ollama → app refuses to start with a setup hint

Copy `.env.example` to `.env` and uncomment whichever block you want.

---

## Backend A — Local Ollama  (default; no API key)

The way Vaani is meant to ship: Gemma 4 E4B running on the device, fully
offline. Best privacy posture, lowest latency, zero recurring cost.

```bash
# 1. Install Ollama (one-time, ~60 seconds)
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh
# Windows:
winget install Ollama.Ollama

# 2. Pull Gemma 4 E4B (one-time, ~3 GB)
ollama pull gemma4:e4b

# 3. Run Vaani
make install
make run
```

Verify the engine:

```bash
curl -s http://127.0.0.1:8765/info | python -c "import sys,json;print(json.load(sys.stdin)['engine'])"
# → ollama/gemma4:e4b
```

Want a different size? `ollama pull gemma4:26b` (or `:31b`, `:e2b`) and set
`VAANI_OLLAMA_MODEL=gemma4:26b` in `.env`.

---

## Backend B — Google AI Studio  (free tier)

Simplest setup if you don't want to download weights. Free, no credit card.

```bash
# 1. Grab a key
# Open https://aistudio.google.com/apikey  → Create API key

# 2. Drop it in ./.env  (or ~/.vaani/.env)
echo "GEMINI_API_KEY=your_key_here" >> .env

# 3. Run
make run
```

The presence of `GEMINI_API_KEY` is the signal — Vaani auto-selects AI Studio
over local Ollama when the key is set. Default model is `gemma-4-27b-it`. To
override, edit the `MODEL = ...` line in `app/inference.py` (it's one line).

Verify:
```bash
curl -s http://127.0.0.1:8765/info | python -c "import sys,json;print(json.load(sys.stdin)['engine'])"
# → aistudio/gemma-4-27b-it
```

Note: AI Studio's Gemma variants don't always expose function-calling. If
the API rejects tools, the inference layer retries without them — function
calls will be empty for that turn but text generation still works. (For
guaranteed function-calling, use Backend A or C.)

---

## Backend C — OpenRouter  (paid, ~$0.05 per 1M tokens)

Use this when you want the larger 31B variant or guaranteed function-call
support, and you don't want to install Ollama.

```bash
# 1. Get a key from https://openrouter.ai/keys
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env

# 2. Run
make run
```

Default model is `google/gemma-4-27b-it`. To override, edit `app/inference.py`.

---

## Selection order (when multiple are configured)

1. `GEMINI_API_KEY`     → AI Studio wins
2. `OPENROUTER_API_KEY` → OpenRouter wins
3. local Ollama         → only if neither key is set

If none of the three is configured, the app refuses to start and prints a
short setup pointer at `/health`. Vaani does **not** ship with a silent
scripted fallback in production — every demo runs against real Gemma 4.

---

## Where to put your `.env`

Loaded in this order (first match wins, environment always overrides):

1. `$VAANI_ENV_FILE` — explicit override (`VAANI_ENV_FILE=/path/to/.env make run`)
2. `./.env` in the project root — preferred per-clone setup
3. `~/.vaani/.env` — user-wide, useful if you maintain multiple clones

`./.env` is in `.gitignore`, so your real keys never end up in commits.

---

## Make targets

```
make install     install Python deps
make run         start the FastAPI server on :8765 with the configured backend
make stub        force the test stub (no Gemma 4 needed) — for headless smoke tests only
make test        run pytest (uses stub internally)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Server refuses to boot, message includes "No Gemma 4 backend configured" | `.env` is empty and no Ollama install | Pick a backend above |
| `engine: ollama/...` but slow first turn | Ollama is loading the weights into RAM | Normal — second turn is fast |
| AI Studio returns 403 | Key not enabled for your region or model | Try `VAANI_AISTUDIO_MODEL=gemma-2-27b-it` as a fallback |
| OpenRouter 401 | Key missing or wrong | Check `secrets/.env` |
| `engine: stub/canonical` | `VAANI_FORCE_STUB=1` is set OR you used `make stub` | That's intentional for tests; use `make run` for the real demo |
