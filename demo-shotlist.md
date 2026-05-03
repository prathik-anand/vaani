# Vaani — Final Demo Storyboard (90-second cut as shipped)

This is the storyboard the demo video at `video/vaani-demo.mp4` was rendered from. Final runtime: 50.6 seconds.

| # | Time | Beat | What's on screen | Voice-over |
|---|---|---|---|---|
| 1 | 0:00 | Hook | Number `773,000,000` counts up; "adults cannot read." underneath | "Seven hundred and seventy three million adults can't read." |
| 2 | 0:03 | Stakes | "91% of them own a smartphone." | "Ninety one percent of them own a phone." |
| 3 | 0:06 | Problem | Three sample papers fan out in the dark | "Every week they receive paper they can't decode. A prescription. A school notice. A government letter." |
| 4 | 0:13 | Pain | "The neighbour is busy." | (same) |
| 5 | 0:16 | Pivot | "Until tonight." (terracotta) | (same) |
| 6 | 0:18 | Solution reveal | Vaani phone-frame; airplane banner glows red across top; empty bot bubble greets user | "This is Vaani. It runs on a six thousand rupee Android. Offline. In their own language. Free." |
| 7 | 0:24 | **WOW** | Devanagari prescription fills viewport · mic pulses red · bot bubble fills with Hindi reply · `set_reminder` JSON card slides in from right with accent flash · 200ms chime sting | (Hindi voice) "यह डॉक्टर का प्रिस्क्रिप्शन है। तीन दवाइयाँ लिखी हैं… क्या मैं रिमाइंडर लगा दूँ?" |
| 8 | 0:31 | Defensibility | Phone carousel: Tamil receipt with `set_reminder` → Marathi letter with `set_reminder` → urgent fever paper with `flag_red_flag` | "The same product reads Tamil. Reads Marathi. Flags an urgent fever as urgent." |
| 9 | 0:41 | Why now | Dark card: "Gemma 4 E4B" + 4 bullets (vision · voice · 140 langs · 4 GB on-device) | "Gemma 4 E4B. Vision, voice, a hundred and forty languages. Four gigabytes. On a phone." |
| 10 | 0:46 | Thesis | "If you can speak, you can use the internet." | (same) |
| 11 | 0:50 | End card / ask | Vaani · Built on Gemma 4 · Open source · github.com/prathik-anand/vaani | "Vaani. Built on Gemma 4. Open source. Fork it tonight." |

## Hard cuts vs soft fades

- Snap cut between shots 4 and 5 (pivot to "Until tonight.")
- Crossfade across keyframes inside shots 7 and 8 (paper → bubble → fn-call card)
- Soft fade-in/out everywhere else (0.25s)

## Audio

- ElevenLabs Rachel for English narration
- ElevenLabs Aria (multilingual_v2) for the in-product Hindi reply
- Single 200ms two-tone chime sting at 0:30 (function-call slide-in)
- No background music — the wow plays in deliberate silence

## Brand discipline

The codename "Vaani" appears exactly twice in the video:
1. Spoken at the head of shot 6 ("This is Vaani.")
2. Written on the end card

Every other shot suppresses the codename per the Content Director brief.
