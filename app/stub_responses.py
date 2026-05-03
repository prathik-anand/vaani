"""Scripted canonical responses used when no live Gemma 4 backend is available.

The point of the stub is honesty + reliability:
  - Honest: the README and the UI both say "scripted demo mode" when this is on.
  - Reliable: the demo path always works, even if Ollama / HF download flakes.

The architecture is unchanged whether the real model or the stub serves a turn —
the same JSON schema flows back to the client, the same function-calls render in
the right-side panel, the same audio-to-audio cycle plays.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class StubResponse:
    reply_text: str
    fn_calls: List[Dict[str, Any]]
    language: str  # ISO-639-1


# Canonical responses keyed by (paper_kind, user_intent).
# paper_kind comes from a shallow heuristic on the image filename; in production it
# comes from Gemma 4's own vision parse.
CANONICAL: Dict[str, StubResponse] = {
    "prescription_hindi__what_is_this": StubResponse(
        reply_text=(
            "यह डॉक्टर का prescription है। तीन दवाइयां लिखी हैं — Amoxicillin "
            "सुबह और रात, Paracetamol बुखार के लिए, और एक खाँसी की syrup। सात "
            "दिन तक लेनी हैं।"
        ),
        fn_calls=[
            {
                "name": "set_reminder",
                "args": {
                    "med": "Amoxicillin 500mg",
                    "times": ["09:00", "21:00"],
                    "days": 7,
                },
            }
        ],
        language="hi",
    ),
    "prescription_hindi__set_reminders": StubResponse(
        reply_text="ठीक है, तीनों दवाइयों के लिए reminder लगा दिए हैं। फ़ोन हर बार बजेगा।",
        fn_calls=[
            {
                "name": "set_reminder",
                "args": {"med": "Paracetamol 650mg", "times": ["09:00", "15:00", "21:00"], "days": 5},
            },
            {
                "name": "set_reminder",
                "args": {"med": "Cough syrup 5ml", "times": ["10:00", "22:00"], "days": 5},
            },
        ],
        language="hi",
    ),
    "school_notice_english__translate_to_hindi": StubResponse(
        reply_text=(
            "स्कूल से notice आया है। अगले शुक्रवार को parent-teacher meeting है, "
            "सुबह 10 बजे। बच्चे की progress report पर बात होगी। आपको आना होगा।"
        ),
        fn_calls=[
            {
                "name": "set_reminder",
                "args": {"med": "School PTM", "times": ["09:00"], "days": 1},
            }
        ],
        language="hi",
    ),
    "school_notice_english__what_is_this": StubResponse(
        reply_text=(
            "स्कूल से एक notice है। अगले शुक्रवार को parent-teacher meeting है, "
            "सुबह 10 बजे। बच्चे की पढ़ाई पर बात होगी। क्या मैं reminder लगा दूं?"
        ),
        fn_calls=[
            {
                "name": "set_reminder",
                "args": {"med": "School PTM", "times": ["09:00"], "days": 1},
            }
        ],
        language="hi",
    ),
    "ration_receipt_tamil__what_is_this": StubResponse(
        reply_text=(
            "இது ரேஷன் கடை ரசீது. இந்த மாதம் 5 கிலோ அரிசி, 1 கிலோ பருப்பு "
            "வாங்கியிருக்கிறீர்கள். அடுத்த மாதம் 5-ஆம் தேதிக்கு பின்னர் வாங்கலாம்."
        ),
        fn_calls=[],
        language="ta",
    ),
    "fever_paper__what_is_this": StubResponse(
        reply_text=(
            "बच्चे को 102° बुखार है, साँस तेज़ चल रही है। यह urgent है। आज ही "
            "हस्पताल ले जाइए। मैं doctor के लिए कुछ ज़रूरी सवाल भी तैयार कर देती हूँ।"
        ),
        fn_calls=[
            {
                "name": "flag_red_flag",
                "args": {
                    "symptom": "fever 102°F + fast breathing in child",
                    "reason": "possible chest infection, needs same-day care",
                },
            }
        ],
        language="hi",
    ),
    "marathi_letter__what_is_this": StubResponse(
        reply_text=(
            "हे आरोग्य विभागाचे पत्र आहे। पुढच्या रविवारी, १० मेला, सकाळी ९ ते "
            "दुपारी १ वाजेपर्यंत येरवडा PHC मध्ये मोफत आरोग्य शिबिर आहे। "
            "रक्तदाब, साखर, हिमोग्लोबिन तपासले जातील। आधार कार्ड घेऊन या। "
            "मी आठवण लावू का?"
        ),
        fn_calls=[
            {
                "name": "set_reminder",
                "args": {
                    "med": "Free health camp at Yerwada PHC",
                    "times": ["08:30"],
                    "days": 1,
                },
            }
        ],
        language="mr",
    ),
    "marathi_letter__translate_to_hindi": StubResponse(
        reply_text=(
            "स्वास्थ्य विभाग का पत्र है। अगले रविवार, १० मई को, सुबह ९ से दोपहर "
            "१ बजे तक येरवडा PHC में मुफ़्त स्वास्थ्य शिविर है। ब्लड प्रेशर, "
            "शुगर, हीमोग्लोबिन की जाँच होगी। आधार कार्ड साथ ले जाइए।"
        ),
        fn_calls=[],
        language="hi",
    ),
    # Generic fallback when image is present but unrecognised
    "_generic_paper__what_is_this": StubResponse(
        reply_text=(
            "मुझे इस कागज़ पर कुछ शब्द दिख रहे हैं लेकिन साफ़ नहीं हैं। ज़रा "
            "कैमरा थोड़ा क़रीब लाइए और दोबारा फ़ोटो लीजिए।"
        ),
        fn_calls=[],
        language="hi",
    ),
    # Pure conversational opener (no image)
    "_no_image__greeting": StubResponse(
        reply_text=(
            "नमस्ते। मैं Vaani हूँ। कोई कागज़ है तो camera से दिखाइए, मैं "
            "पढ़ कर बताऊँगी।"
        ),
        fn_calls=[],
        language="hi",
    ),
}


def _classify_paper(image_filename: Optional[str]) -> str:
    if not image_filename:
        return "_no_image"
    f = image_filename.lower()
    if "prescription" in f and "hindi" in f:
        return "prescription_hindi"
    if "school" in f:
        return "school_notice_english"
    if "ration" in f or "tamil" in f:
        return "ration_receipt_tamil"
    if "fever" in f or "child" in f:
        return "fever_paper"
    if "marathi" in f or "letter" in f:
        return "marathi_letter"
    return "_generic_paper"


def _classify_intent(text: Optional[str]) -> str:
    if not text:
        return "what_is_this"
    t = text.lower()
    if any(k in t for k in ["reminder", "lagao", "लगा", "set", "haan"]):
        return "set_reminders"
    if any(k in t for k in ["hindi mein", "hindi me", "translate", "हिंदी में"]):
        return "translate_to_hindi"
    if any(k in t for k in ["namaste", "hello", "hi vaani", "namaskar"]):
        return "greeting"
    return "what_is_this"


def lookup(image_filename: Optional[str], user_text: Optional[str]) -> StubResponse:
    paper = _classify_paper(image_filename)
    intent = _classify_intent(user_text)
    key = f"{paper}__{intent}"
    if key in CANONICAL:
        return CANONICAL[key]
    # try paper with default intent
    key = f"{paper}__what_is_this"
    if key in CANONICAL:
        return CANONICAL[key]
    if paper == "_no_image":
        return CANONICAL["_no_image__greeting"]
    return CANONICAL["_generic_paper__what_is_this"]
