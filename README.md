# Vaani

> _If you can speak, you can use the internet._

A voice-first, vision-enabled, **fully offline** pocket interpreter for the **773 million adults** worldwide who own a smartphone but cannot read. Speak in your own language; point the camera at any paper you receive (prescription, school notice, government letter, ration receipt); Vaani reads it, explains it back to you in your tongue, and offers to act on it — set a reminder, draft a reply, prepare questions for the clinic, flag urgency.

Built on **Gemma 4 E4B** running on-device. No cloud. No subscription. No signal needed.

Submitted to the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) (Kaggle × Google DeepMind) — **Digital Equity & Inclusivity** track.

---

## Why this matters

- **773 million adults** are illiterate (UNESCO, 2023). 91% of them own a phone (GSMA).
- Existing voice agents (Siri, Alexa, ChatGPT-Voice) all assume three things this population doesn't have: an internet connection they can afford daily, fluency in the assistant's preferred language, and familiarity with menus and apps.
- Gemma 4 is the **first open model** that combines vision + native audio + 140-language reach + function calling in a 4B-parameter package small enough to run on a ₹6,000 ($75) Android phone, **offline**.

That combination is what makes Vaani possible this month — not last year, not on Gemma 3, not on closed models that need an API key.

---

## What it does

A single screen. One button.

1. The user holds their phone over any printed paper.
2. They speak in their own language: *"yeh kya hai?"* / *"what does this say?"*
3. Vaani reads the paper aloud in their language and offers one helpful next action via a function call (`set_reminder`, `draft_reply`, `flag_red_flag`, `prepare_questions_for_clinic`, `lookup_medicine_meaning`).
4. Everything happens on-device. The "✈ Offline" badge is real, not decorative.

---

## Architecture

```
Browser (phone-frame UI) ──POST /turn──▶ FastAPI ──▶ Inference layer
                                                       ├─ Backend A: Ollama (gemma4:e4b)
                                                       ├─ Backend B: HF transformers
                                                       └─ Backend C: scripted stub (honest fallback)
```

The inference layer auto-selects the best available backend at startup. The /turn endpoint and the UI are blind to which backend served the call — they just see `{reply_text, fn_calls, engine}`.

The scripted-stub backend exists so that the **demo never fails** even if Ollama/HF aren't installed on the judging machine. When it's active, the UI honestly labels the engine line as `stub/canonical (demo mode)`. The architecture, function-call surface, UX, and pitch are unchanged.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for diagrams and design decisions, and [docs/TECHNICAL_WRITEUP.md](docs/TECHNICAL_WRITEUP.md) for the Kaggle submission write-up.

---

## Run it

```bash
make install
make run
# open http://127.0.0.1:8765
```

That's it. No API key required. No network calls during normal operation (verify with `make run` and your laptop's wifi off).

For the deterministic scripted demo (used in the video):
```bash
make stub
```

For the test suite:
```bash
make test
```

---

## Demo path (60 seconds)

1. Open `http://127.0.0.1:8765` in Chrome.
2. The phone-frame loads with a visible **✈ Offline** badge.
3. Tap the **Rx** sample (or hold the camera over any printed paper).
4. Hold the **mic** button and say *"yeh kya hai mujhe kya karna hai"* (or click — it'll send a default question).
5. Vaani replies in spoken Hindi explaining the prescription and offers `set_reminder`.
6. Tap the mic again, say *"haan, lagao"* — three reminders are scheduled. The function-call panel on the right shows every call as it fires.
7. Tap **School** sample. Mic. *"yeh hindi mein bolo."* Notice translates and reads aloud.

---

## What Vaani does NOT do

- It does not diagnose. It reads what is on the paper.
- It does not prescribe. It explains the medicines the doctor already chose.
- It does not store conversations remotely. There is no remote.
- It does not sell anything. The codebase is FOSS.

---

## Tech

| Layer | Choice |
|---|---|
| Inference | Gemma 4 E4B via Ollama, with HF transformers and scripted-stub fallbacks |
| Server | FastAPI + uvicorn |
| Frontend | Vanilla HTML / CSS / JS (no build step) |
| In-app speech-to-text | Web Speech API (browser-native) |
| In-app text-to-speech | Browser `SpeechSynthesis` (offline) |
| Function calling | Native Gemma 4 tool definitions (OpenAI-style) |
| Demo-video narration | ElevenLabs (build-time only — never invoked at runtime) |

---

## Repository layout

```
project/
├── app/                     # FastAPI server + inference + tools
│   ├── main.py              # /turn /health /tools /info
│   ├── inference.py         # Ollama → HF → stub
│   ├── tools.py             # 5 tool definitions + dispatcher
│   ├── stub_responses.py    # canonical scripted responses
│   └── system_prompt.py     # Vaani's behavioural contract
├── static/                  # UI (no build step)
├── samples/                 # 4 demo papers
├── tests/                   # 15 tests, all green
└── docs/
    ├── ARCHITECTURE.md
    └── TECHNICAL_WRITEUP.md   # the Kaggle write-up
```

---

## License

MIT. Use it. Fork it. Translate it. Put it on a billion phones.
