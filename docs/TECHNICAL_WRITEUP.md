# Vaani — Technical Write-up

**Hackathon:** Gemma 4 Good Hackathon (Kaggle × Google DeepMind)
**Track:** Digital Equity & Inclusivity
**Submitter:** Prathik (Pune, India)
**Repo:** github.com/prathik-anand/vaani
**Demo video:** see Kaggle submission gallery

---

## 1. The problem we chose to solve

**773 million adults globally cannot read.** (UNESCO, 2023.) Two-thirds of them are women. They live everywhere — rural India, urban slums in Lagos, indigenous villages in Peru, refugee camps in Bangladesh.

**91% of them own a smartphone.** (GSMA Mobile Gender Gap Report, 2024.) Many own data plans they cannot afford to use daily.

**0% of them can use Siri, Alexa, ChatGPT, or any existing voice agent meaningfully.** Every commercial voice assistant assumes:

1. A reliable internet connection — they don't have it.
2. The user can read on-screen menus to set preferences — they cannot.
3. Fluency in the assistant's preferred language — most cannot speak it.

The cost of illiteracy compounds every week. A woman receives a prescription for her child and asks her teenage neighbour to read it. The neighbour is busy. The child takes the wrong dose. A school sends home a notice about an exam — the parent doesn't see it; the child fails. A microfinance loan reminder is missed; the family loses 10% of monthly income to a late fee.

We asked: **what if literally pointing your phone at any paper, and saying *"yeh kya hai?"* in your own language, gave you back a clear spoken explanation — and offered to act on it for you — even with no signal?**

---

## 2. Why Gemma 4 makes this possible *now*

This product was technically impossible six months ago. The combination of features we required existed in no single model:

| What we needed | Gemma 4 capability we used |
|---|---|
| OCR + parse of printed paper in regional scripts | Native vision input on E4B (Devanagari, Tamil, Roman, etc.) |
| Understand spoken queries in 140 languages | E4B native audio input — no Whisper bolt-on |
| Produce conversational reply in the same language | Native generation across 140 languages |
| Decide whether to set a reminder vs. flag urgency vs. draft a reply | Native function calling with structured JSON tool calls |
| Run the whole stack offline on a sub-$80 Android phone | E4B's 4-bit quantised footprint (~3 GB) and on-device runtime |
| Low latency so a non-literate user doesn't lose the thread of a conversation | E4B optimised for Qualcomm/MediaTek mobile silicon |

**No closed model gives us all six.** GPT-4o has the multimodal-ness but is API-only and costs money. Llama 3 8B is too big for the target phone and lacks native audio. Gemini Nano is on-device but lacks the language coverage. Whisper-on-phone-plus-LLM has no shared context between the audio-understanding and reasoning steps.

Gemma 4 E4B is the **first month** in human history that this build is feasible.

---

## 3. System design

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (the "phone")                                      │
│   • Phone-frame UI (HTML/CSS, no build step)                │
│   • ✈ Offline badge (real claim, not decorative)            │
│   • Camera + hold-to-talk mic + 4 sample papers             │
│   • Right panel: live function-call log (judges' view)      │
└────────────────────────┬────────────────────────────────────┘
                         │ POST /turn (multipart: text+image)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI server (localhost:8765, no outbound calls)         │
│   • /turn       orchestrates a conversational turn          │
│   • /tools      lists 5 registered functions                │
│   • /info       reports engine + offline status             │
└────────────────────────┬────────────────────────────────────┘
                         │ in-process call
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Inference layer (3 backends, single .generate())           │
│   A. Ollama  → gemma4:e4b on localhost:11434 (preferred)    │
│   B. HF transformers → google/gemma-4-e4b 4-bit quantised   │
│   C. Scripted stub → canonical responses (honest fallback)  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Why three backends

The judging machine on Kaggle probably will not have Gemma 4 weights pre-downloaded. We could not bet the whole submission on whether `ollama pull gemma4:e4b` succeeds the first time. So:

- **Backend A (Ollama)** — what runs in production. Cleanest path; Ollama has first-class Gemma 4 support including images and tools.
- **Backend B (transformers)** — fallback for environments without Ollama. Slower to load but uses the same weights.
- **Backend C (scripted stub)** — final fallback. The /turn surface and the function-call shape are identical, so the UX, the video, and the judges' visceral experience are unaffected. **The UI honestly labels the engine as `stub/canonical (demo mode)` when this backend is active.** We do not pretend.

### 3.3 Function calling

Gemma 4's native function-calling lets the model emit structured tool calls alongside its text reply. We register five tools:

| Tool | When the model calls it |
|---|---|
| `set_reminder` | Prescription with timed doses; appointment notice |
| `draft_reply` | School notice asking for confirmation; SMS to be sent back |
| `flag_red_flag` | Symptoms on a paper that warrant immediate clinic visit |
| `prepare_questions_for_clinic` | Diagnosis paper the user will discuss with a doctor |
| `lookup_medicine_meaning` | User asks what a specific medicine does |

The function-call panel on the right side of the UI exists to make the agentic loop *visible* to judges — every tool call streams in as it fires, with arguments shown verbatim.

### 3.4 The system prompt

Held in [`app/system_prompt.py`](../app/system_prompt.py). Encodes Vaani's safety boundary:

- Reply in the user's spoken language; default to Hindi if unsure.
- Never diagnose. Never give medical advice beyond what is printed.
- Red-flag symptoms → call `flag_red_flag` and direct user to the clinic today.
- At most one function call per turn; two short sentences before it.

---

## 4. UX design choices that matter

This is a product for users who **cannot read**. Every UI choice is downstream of that.

- **One screen.** No menus. No settings. No login.
- **One big mic button** (88px, terracotta). Hold-to-talk maps to a familiar gesture.
- **Sample-paper buttons are letters, not words** (Rx, School, Ration, Fever) — a literate operator picks them during the demo, but in real use the user just shows a paper to the camera.
- **The bot's first message is spoken aloud** when the page loads, not just shown as text.
- **The function-call panel sits *outside* the phone frame** — it is for judges, not users. The user's UI has zero JSON.

---

## 5. What we did *not* do tonight (and why)

| Cut | Why |
|---|---|
| Real Android APK | Would have taken 2+ days. The web app demonstrates the same UX and same model interaction. |
| Fine-tuning Gemma 4 on a literacy-help corpus | Vanilla Gemma 4 already handles the demo well. Fine-tuning would have eaten the night with marginal gain. |
| Production-grade ASR for all 140 languages in the in-app mic | Web Speech API covers the 4 demo languages; for production, E4B's native audio replaces it entirely. |
| Cloud sync, accounts, paid tier | This is FOSS for impact. There is no business model here. |

---

## 6. Limitations and honesty

- The in-app speech-to-text in this web prototype uses the browser's Web Speech API, which on most browsers calls a server. **In production on Android with Gemma 4 E4B, the ASR is on-device** — that's the whole point of the E4B audio capability. The web demo is a UX prototype; the architecture is for the phone.
- The scripted-stub backend is the inference path that runs on machines without Gemma 4 installed. It's labelled in the UI. The Ollama backend is what runs the real model.
- We do not claim to solve illiteracy. We claim to make every printed paper *immediately understandable* — which is not the same thing, but is a meaningful step.

---

## 7. What's next (post-hackathon)

- Package as an Android APK with the Gemma 4 E4B weights bundled.
- Pilot with 30 ASHA workers in 2 districts (we have a contact at SEWA).
- Add more languages incrementally (Bengali, Telugu, Marathi, Yoruba, Quechua).
- Open the function surface to community contributions (e.g., a `read_pension_card` tool with state-specific rules).

---

## 8. Acknowledgements

- Google DeepMind & the Gemma team for an open model that makes this category of product possible.
- Kaggle for the hackathon platform.
- 773 million people who deserve better tools than the ones the rest of us take for granted.
