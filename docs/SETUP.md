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

`.env.example` ships with `VAANI_BACKEND=local`. Copy it to `.env` and
uncomment a different section if you want to switch.

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

# 2. Drop it in either D:/hackthon/secrets/.env  or  project/.env
echo "GEMINI_API_KEY=your_key_here" >> D:/hackthon/secrets/.env

# 3. Tell Vaani to use AI Studio
echo "VAANI_BACKEND=aistudio" >> project/.env

# 4. Run
make run
```

Default model is `gemma-4-27b-it`. Override with `VAANI_AISTUDIO_MODEL=gemma-4-9b-it`
or whichever Gemma variant the AI Studio rate limits favour today.

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
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> D:/hackthon/secrets/.env

# 2. Set the backend
echo "VAANI_BACKEND=openrouter" >> project/.env

# 3. Run
make run
```

Default model is `google/gemma-4-27b-it`. Override with `VAANI_OPENROUTER_MODEL`
to pick e.g. `google/gemma-4-31b-it` or any other OpenRouter Gemma listing.

---

## Auto-select fallback

If `VAANI_BACKEND` is unset, the inference layer probes in this order:
1. Local Ollama (if `ollama list` shows a Gemma 4 tag)
2. AI Studio (if `GEMINI_API_KEY` is in the env)
3. OpenRouter (if `OPENROUTER_API_KEY` is in the env)

If none of the three are configured, the app refuses to start and prints a
short setup pointer at `/health`. Vaani does **not** ship with a silent
scripted fallback in production — every demo runs against real Gemma 4.

---

## Where to put your `.env`

Two places are loaded in order:
1. `D:/hackthon/secrets/.env` — preferred for keys (machine-wide, shared with
   the demo-video pipeline)
2. `project/.env` — for backend selection + per-project overrides

Either works. Keys in `secrets/.env` are picked up by the app *and* by the
ElevenLabs narration synth in the video pipeline.

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
