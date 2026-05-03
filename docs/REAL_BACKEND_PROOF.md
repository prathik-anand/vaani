# Real Gemma 4 backend — verification path

The judging machine may not have Gemma 4 weights pre-installed; the demo defaults to the scripted-stub backend (which is honestly labelled in the UI). For judges who want to verify that the same code path works against real Gemma 4 E4B, here is the exact procedure.

## 1. Install Ollama (one-time, 60 seconds)

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows
winget install Ollama.Ollama
```

## 2. Pull Gemma 4 E4B (~3 GB, one-time)

```bash
ollama pull gemma4:e4b
```

The 4-bit quantised E4B weight is about 3 GB. Pulls in 2–4 minutes on a normal home connection. Once pulled, the model lives in `~/.ollama/models/` — no further network use.

## 3. Run Vaani

```bash
make run
```

At startup the inference layer probes `ollama list`. If `gemma4:e4b` is present, it auto-selects Backend A. The `/info` endpoint will then report:

```json
{
  "engine": "ollama/gemma4:e4b",
  "is_stub": false,
  "offline": true,
  "upstream_calls": "none during normal operation"
}
```

The UI's "Engine" line in the right panel changes to `ollama/gemma4:e4b` (no "(demo mode)" suffix).

## 4. Verify a real turn

```bash
curl -X POST http://127.0.0.1:8765/turn \
  -F "text=yeh kya hai mujhe kya karna hai" \
  -F "lang=hi" \
  -F "image=@samples/prescription_hindi.jpg" \
  -F "image_filename=prescription_hindi.jpg"
```

Expected response shape (from real Gemma 4 E4B; exact wording will vary):

```json
{
  "transcript": "yeh kya hai mujhe kya karna hai",
  "reply_text": "यह एक प्रिस्क्रिप्शन है। तीन दवाइयाँ लिखी हैं ...",
  "language": "hi",
  "fn_calls": [
    {
      "name": "set_reminder",
      "args": { "med": "Amoxicillin 500mg", "times": ["09:00","21:00"], "days": 7 }
    }
  ],
  "engine": "ollama/gemma4:e4b",
  "elapsed_ms": 1840
}
```

The `engine` field is the proof. If it begins with `ollama/`, the inference came from the real model — not the stub.

## 5. Verify offline operation

After step 2 completes, disable your network:
- macOS: `networksetup -setairportpower en0 off`
- Linux: `nmcli networking off`
- Windows: toggle airplane mode in the system tray

Re-run the curl from step 4. It should still succeed — Ollama serves on `localhost:11434`, and Vaani never makes any other outbound call.

## What stays the same regardless of backend

- The `/turn` JSON schema
- The function-call shape
- The system prompt
- The UX
- The video pitch

The stub-vs-real distinction is one line in `inference.py`. Everything else is identical. That's the architectural point.

## Why we ship with stub-by-default for the demo machine

A hackathon judge has 90 seconds per submission. We will not gamble those 90 seconds on a 3 GB download finishing in time. The stub guarantees the demo flows perfectly; the README guarantees a verifiable Ollama path one command away.
