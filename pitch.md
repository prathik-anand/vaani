# Vaani — 3-minute spoken pitch

> _If you can speak, you can use the internet._

---

## The line that has to land first (15 sec)

Seven hundred and seventy three million adults can't read. Ninety one percent of them own a phone. Zero percent of them can use Siri, ChatGPT, or any other voice agent — because every existing voice assistant assumes a connection they can't afford daily, fluency in a language they don't speak, and the ability to read a menu they can't read.

That last assumption — that the user can read — is hard-coded into the entire mobile internet. We thought it was load-bearing. Gemma 4 just made it removable.

---

## The product (45 sec)

Vaani is a single-screen Android app. There are no menus, no settings, no login. There is one big mic button.

A user holds their phone over any printed paper they receive — a prescription, a school notice, a government letter, a ration receipt — and asks "yeh kya hai" in their own language. Vaani reads the paper aloud in their tongue, and offers one helpful next action via a structured tool call: set a reminder for the medicines, draft a reply to the school, prepare questions for the next clinic visit, flag an urgent symptom and tell them to go to the hospital today.

Everything happens on-device. No internet. No subscription. Free.

The interface uses no words a user has to read. The mic is one large terracotta button. The "airplane mode — no internet — Gemma 4 on-device" banner across the top is the only label, and it's there for the trust signal, not navigation. A non-literate user picks up the phone and uses it the same way they pick up a tap.

---

## Why Gemma 4 makes this possible *now* (45 sec)

This product class was technically impossible six months ago. We needed five things from the same model:

1. Vision — to read printed text in regional scripts: Devanagari, Tamil, Bengali, Yoruba.
2. Native audio — to understand spoken queries in 140 languages, without a Whisper bolt-on that loses context.
3. Generation in the same 140 languages — so the reply sounds native.
4. Function calling — to decide whether to set a reminder versus flag urgency versus draft a reply.
5. A sub-4-gigabyte footprint — to run on a six thousand rupee Android phone, fully offline.

No closed model gives us all five. GPT-4o is API-only and costs money. Llama 3 8B is too big for the target phone and lacks native audio. Gemini Nano lacks the language coverage. Whisper-plus-LLM has no shared context.

Gemma 4 E4B is the **first open model** that gives us the entire stack in one package. This is the first month in human history this build is feasible.

---

## Demo beats (40 sec)

I'll show you the wow moment: a Devanagari prescription held to the camera, a Hindi voice query, the spoken Hindi reply naming each medicine, and the structured `set_reminder` tool call sliding in from the right with the dosing schedule.

Then I'll show the same product reading Tamil. Reading Marathi. And flagging an urgent infant fever as `flag_red_flag` with a referral to the district hospital today.

Same product. Four scripts. Four languages. Zero internet. The function-call panel on the right side is there for you, the judges — to make the agentic loop visible. The user never sees it.

---

## The architecture you'll find in the repo (15 sec)

A single FastAPI server, a vanilla HTML/CSS/JS UI, and a three-tier inference layer that auto-selects the best available backend at startup: Ollama with `gemma4:e4b` first, HuggingFace transformers second, scripted-stub third — the stub honestly labels itself in the UI. The /turn JSON schema, the function-call surface, and the UX are identical regardless of which backend is serving.

Twenty two tests pass. The README has a make demo target a stranger could follow.

---

## The ask (20 sec)

We are not building a startup. There is no business model here. Vaani is MIT-licensed and the only logo on it is the codename.

We are asking for two things from the Digital Equity track: first, the opportunity to put this in the hands of the SEWA team's pilot cohort of ASHA workers in Gujarat next month; second, your help convincing the Gemma team to publish an Android-first packaging of E4B with the on-device function-calling APIs documented for community integration.

Seven hundred and seventy three million people have phones they paid for and can't use. Tonight we built the thing that lets them use the internet they're already paying for. Vaani. Built on Gemma 4. Open source. Fork it tonight.
