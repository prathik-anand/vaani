# Vaani — Architecture & Decisions

## At a glance

```
Browser ──HTTP──▶ FastAPI ──in-process──▶ Inference ──HTTP──▶ Ollama
                                                  └──in-process──▶ HF transformers
                                                  └──in-process──▶ Scripted stub
```

Single page web app. Single Python service. Three pluggable backends. No outbound network during normal operation.

## Component decisions

### Frontend: vanilla HTML/CSS/JS, no build step

Considered React/Vue/Svelte; decided against. A hackathon judge cloning the repo at 11pm should be able to `make run` and see the demo without `npm install`. The UI has ~200 lines of JavaScript total and a single HTML file. There is no opportunity cost from the framework absence.

### Server: FastAPI

Three reasons:
1. Async multipart upload handling for image + audio is one decorator.
2. Pydantic models give us free schema validation on `/turn` input.
3. The Kaggle judging environment likely already has FastAPI; if not, `pip install fastapi[standard]` works on every machine.

### Inference layer: three-tier with single interface

The `Inference` class has one public method, `generate()`, that returns a `TurnResult` with a fixed schema regardless of which backend served it. Backend selection happens once at server startup based on environment + availability:

```
VAANI_FORCE_STUB=1?  ──▶ Backend C (stub)
ollama list contains gemma4:*?  ──▶ Backend A (Ollama)
HF transformers + Gemma 4 weights cached?  ──▶ Backend B (HF)
otherwise  ──▶ Backend C (stub)
```

The /turn handler is blind to which backend is active. The UI is informed via /info but is purely cosmetic about it.

### Function calling: native Gemma 4, OpenAI-style definitions

Gemma 4 supports the same `{type: "function", function: {name, description, parameters}}` shape as OpenAI. Ollama parses Gemma 4 tool calls into a structured `tool_calls` array that we forward to the UI. This means the UI rendering code is identical for any future backend.

### TTS: browser-side `SpeechSynthesis`

The "offline" claim collapses if the spoken reply is synthesised by a cloud TTS at runtime. We use the browser's built-in `SpeechSynthesis`, which uses the OS's bundled voices (offline on every modern OS). ElevenLabs is used **only** for the demo-video narration — never invoked by the running app.

### STT in the web prototype: Web Speech API

The browser Web Speech API actually does call a server on Chrome (the Google ASR endpoint). This is a limitation of the *web prototype*, not of Vaani as a product. The product target is Android with Gemma 4 E4B doing native audio in entirely on-device. We document this honestly in the README.

## Data flow for one turn

```
1. User holds mic, speaks "yeh kya hai mujhe kya karna hai"
2. Browser SpeechRecognition produces text
3. (Optionally) browser captures camera frame as JPEG blob
4. Browser POSTs multipart to /turn:
     text="yeh kya hai mujhe kya karna hai"
     lang="hi"
     image=<blob>
     image_filename="prescription_hindi.jpg"
5. FastAPI hands off to Inference.generate()
6. Backend produces TurnResult{reply_text, fn_calls, language, engine, elapsed_ms}
7. /turn returns JSON
8. Browser renders the reply bubble, populates the function-call panel,
   speaks reply_text via SpeechSynthesis in the user's language
```

## Why the stub is a feature, not a hack

The CPO would have asked: "what if Gemma 4 weights aren't on the judging machine?" Without a fallback, the demo dies. With the scripted-stub fallback:
- The UI, function-call schema, video, and pitch are identical
- The engine line in the UI honestly says `stub/canonical (demo mode)`
- The same .generate() interface means swapping in a real backend is one env var

The stub is not a "fake demo." It's an honest fallback that lets us ship a story that survives infrastructure variance.

## Security / privacy posture

- No outbound network calls during /turn. Verifiable: turn off your laptop's wifi and run the demo.
- No telemetry. No analytics. No ad SDKs.
- Image uploads are processed in memory and never persisted to disk.
- The system prompt forbids diagnosis and any advice beyond what is printed.

## File map

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI surface — routes |
| `app/inference.py` | Backend selection + .generate() |
| `app/tools.py` | 5 tool definitions + dispatcher |
| `app/stub_responses.py` | Canonical scripted responses for Backend C |
| `app/system_prompt.py` | Vaani's behavioural contract |
| `static/index.html` | Phone-frame UI |
| `static/style.css` | Palette + layout |
| `static/app.js` | Camera, mic, /turn fetch, render |
| `samples/*.jpg` | 4 demo papers |
| `samples/_make_samples.py` | Reproducible generator for the papers |
| `tests/*.py` | 22 tests, all green |
