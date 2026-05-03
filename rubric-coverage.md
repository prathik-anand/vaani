# Vaani — Judging-rubric coverage map

The Gemma 4 Good Hackathon publishes three judging pillars. This is how Vaani addresses each.

## Pillar 1 — Impact & Vision

| What judges look for | Where Vaani addresses it |
|---|---|
| Real problem, big audience | 773 million illiterate adults globally; 91% mobile-phone penetration. Numbers cited from UNESCO 2023 and GSMA 2024. See [docs/TECHNICAL_WRITEUP.md §1](docs/TECHNICAL_WRITEUP.md). |
| Clear theory of impact | Each printed paper a non-literate adult receives is decoded into spoken language and converted into one concrete next action — set a reminder, draft a reply, flag urgency. The unit of impact is one paper made actionable. |
| Inclusivity | Track choice (Digital Equity) is the thesis, not a tag. UX designed around a user who cannot read: one-button, no menus, hold-to-talk, no required reading. See [docs/ARCHITECTURE.md §UX](docs/ARCHITECTURE.md). |
| Realism / deployability | Targets a ₹6,000 Android phone with ~4 GB Gemma 4 E4B running offline. Pilot pathway via SEWA ASHA-worker cohort outlined in pitch. |

## Pillar 2 — Technical Depth & Execution

| What judges look for | Where Vaani addresses it |
|---|---|
| Use of Gemma 4's *unique* capabilities | Multimodal (image + audio + text) + native function calling + 140-language reach + on-device 4 GB footprint — every one used in the demo path. See feature-to-need table in [docs/TECHNICAL_WRITEUP.md §2](docs/TECHNICAL_WRITEUP.md). |
| Working code, not slide-ware | FastAPI + vanilla JS, single `make run` brings up the demo. 22 tests pass. Live demo at /turn returns structured JSON with function calls. |
| Sound architecture | Three-tier inference layer (Ollama → HF → stub) with single `.generate()` interface, single `/turn` schema regardless of backend. Stub is an honest fallback — labelled in the UI. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). |
| Offline / privacy posture | Verifiable: turn off wifi, demo still works. No outbound calls during /turn. No telemetry. Image data processed in memory, never persisted. See README §Tech and `app/inference.py`. |
| Honest path to real-Gemma backend | [docs/REAL_BACKEND_PROOF.md](docs/REAL_BACKEND_PROOF.md) gives a 4-step verifiable curl path: install Ollama, pull `gemma4:e4b`, `make run`, hit /info — engine line flips from `stub/canonical` to `ollama/gemma4:e4b`. |

## Pillar 3 — Video Pitch & Storytelling

| What judges look for | Where Vaani addresses it |
|---|---|
| Hook in the first 3 seconds | Cold-open on `773,000,000` counting up — number, not logo. |
| Narrative arc | Problem → Pain → Pivot → Solution reveal → Wow → Defensibility → Why now → Thesis → Ask. See [demo-shotlist.md](demo-shotlist.md). |
| One memorable moment | 0:24–0:30 — Devanagari prescription + airplane-mode banner + spoken Hindi + structured `set_reminder` JSON card sliding in with a chime sting. Four-part chord no other entry will assemble. |
| Demo fidelity | Real Indic-script papers (Hindi, Tamil, Marathi); real-shaped function-call payloads; real /turn JSON visible. No fake spinners. |
| Tight runtime | 50.6 seconds. Under the 60s ceiling, well under the typical 90s ceiling. |
| Production quality | ElevenLabs narration (Rachel) + multilingual model for Hindi. ffmpeg composite at 1920×1080. Cover image included. |

## Sponsor stack

There is one sponsor: Google DeepMind's Gemma 4. We use it for everything. The codebase makes no calls to any other model. The only third-party service used in the build is ElevenLabs — and only for the *demo video narration*, never invoked by the running app. This is the right move for this hackathon's specific brief; multi-sponsor stacking is not relevant here.

## Boundaries we hold

- Vaani never diagnoses. It reads what is on the paper.
- Vaani never prescribes. It explains the medicines the doctor already chose.
- Vaani never auto-sends anything. Drafts go through user confirmation.
- Vaani never stores data remotely. There is no remote.
