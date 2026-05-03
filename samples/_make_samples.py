"""Generate the bundled demo papers using PIL.

Iteration 2 — the CPO flagged that earlier samples were English-rendered, which
killed the "Vaani reads scripts you can't" pitch. Now everything that should be
in a regional script *is* in a regional script (Devanagari / Tamil / Marathi).

Run once:  python samples/_make_samples.py

Outputs:
  prescription_devanagari.jpg   — Hindi prescription, full Devanagari
  school_notice_english.jpg     — English notice (translation demo target)
  ration_receipt_tamil.jpg      — Tamil ration receipt, full Tamil
  marathi_letter.jpg            — Marathi government letter (Devanagari)
  fever_paper.jpg               — English doctor's note with red-flag findings
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent

W, H = 900, 1200
PAPER = (251, 248, 242)
INK   = (35, 38, 45)
RED   = (180, 40, 30)
GREY  = (110, 110, 110)
LINE  = (210, 210, 210)


def _font(size: int, *, bold: bool = False, indic: bool = False) -> ImageFont.ImageFont:
    if indic:
        # Nirmala UI ships with Windows 10/11 and covers Devanagari, Tamil, Bengali, etc.
        for c in [
            "C:/Windows/Fonts/Nirmala.ttc",
            "C:/Windows/Fonts/NirmalaB.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        ]:
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf"   if not bold else "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), PAPER)
    return img, ImageDraw.Draw(img)


def _hline(d: ImageDraw.ImageDraw, y: int, x0: int = 60, x1: int = W - 60) -> None:
    d.line([(x0, y), (x1, y)], fill=LINE, width=1)


def make_prescription_devanagari() -> None:
    img, d = _new()
    f_h1   = _font(48, bold=True)
    f_h2   = _font(30, bold=True, indic=True)
    f_p_en = _font(26)
    f_p_hi = _font(28, indic=True)
    f_s    = _font(22, indic=True)
    f_s_en = _font(20)

    d.text((60, 60), "डॉ. आर. शर्मा,  MBBS, MD", font=f_h2, fill=INK)
    d.text((60, 110), "पुणे सिविल अस्पताल  ·  Reg. 23415", font=f_s, fill=GREY)
    _hline(d, 165)
    d.text((60, 195), "रोगी: आशा काले", font=f_p_hi, fill=INK)
    d.text((60, 240), "उम्र: ६ वर्ष        दिनांक: ०३.०५.२०२६", font=f_p_hi, fill=INK)
    _hline(d, 305)

    d.text((60, 330), "Rx", font=f_h1, fill=INK)

    d.text((60, 410), "१.  Tab. Amoxicillin  ५०० mg", font=f_p_hi, fill=INK)
    d.text((90, 450), "सुबह १ गोली + रात १ गोली × ७ दिन", font=f_s, fill=GREY)

    d.text((60, 510), "२.  Tab. Paracetamol  ६५० mg", font=f_p_hi, fill=INK)
    d.text((90, 550), "बुख़ार होने पर १ गोली, दिन में अधिकतम ३ × ५ दिन", font=f_s, fill=GREY)

    d.text((60, 610), "३.  Cough syrup (Ascoril)", font=f_p_hi, fill=INK)
    d.text((90, 650), "५ ml दिन में दो बार × ५ दिन", font=f_s, fill=GREY)

    _hline(d, 720)
    d.text((60, 750), "सलाह: ख़ूब पानी पिलाइए। ७ दिन बाद दिखाएँ।", font=f_p_hi, fill=INK)
    d.text((60, 1100), "हस्ताक्षर: ____________________     मुहर", font=f_s, fill=GREY)

    img.save(OUT / "prescription_hindi.jpg", quality=88)


def make_school_notice() -> None:
    img, d = _new()
    f_h1 = _font(38, bold=True)
    f_h2 = _font(28, bold=True)
    f_p  = _font(24)
    f_s  = _font(20)
    d.text((60, 60), "ZILLA PARISHAD PRIMARY SCHOOL", font=f_h1, fill=INK)
    d.text((60, 110), "Yerwada, Pune  ·  Class 4-B", font=f_s, fill=GREY)
    _hline(d, 160)
    d.text((60, 200), "NOTICE", font=f_h2, fill=INK)
    d.text((60, 250), "Date: 03 May 2026", font=f_s, fill=GREY)
    d.text((60, 320), "Dear Parent,", font=f_p, fill=INK)
    d.multiline_text(
        (60, 380),
        "A parent-teacher meeting is scheduled for\n"
        "Friday, 10 May 2026 at 10:00 AM in the\n"
        "school assembly hall. We will discuss\n"
        "your child's progress in the third term\n"
        "and the upcoming examinations.\n\n"
        "Your attendance is required. Please bring\n"
        "your child's previous report card.",
        font=f_p, fill=INK, spacing=8,
    )
    d.text((60, 1000), "—  Headmistress, R. Patil", font=f_s, fill=INK)
    img.save(OUT / "school_notice_english.jpg", quality=88)


def make_ration_receipt_tamil() -> None:
    img, d = _new()
    f_h1 = _font(36, bold=True, indic=True)
    f_h2 = _font(28, bold=True, indic=True)
    f_p  = _font(26, indic=True)
    f_s  = _font(20, indic=True)

    d.text((60, 60), "தமிழ்நாடு குடிமை பொருள் வழங்கல் கழகம்", font=f_h1, fill=INK)
    d.text((60, 115), "பொது விநியோக முறை  ·  ரசீது", font=f_s, fill=GREY)
    _hline(d, 170)
    d.text((60, 200), "அட்டை எண்: TN-04-2387", font=f_p, fill=INK)
    d.text((60, 240), "உரிமையாளர்: ம. லட்சுமி", font=f_p, fill=INK)
    d.text((60, 280), "கடை: 047, தி. நகர்", font=f_p, fill=INK)
    d.text((60, 320), "தேதி: 03/05/2026", font=f_p, fill=INK)
    _hline(d, 380)

    d.text((60, 410), "பொருள்", font=f_h2, fill=INK)
    d.text((460, 410), "அளவு", font=f_h2, fill=INK)
    d.text((680, 410), "விலை", font=f_h2, fill=INK)
    _hline(d, 460)
    rows = [
        ("அரிசி (வேக)",   "5 கி",  "இலவசம்"),
        ("துவரம் பருப்பு", "1 கி",  "₹30"),
        ("சர்க்கரை",       "1 கி",  "₹13.50"),
        ("சமையல் எண்ணெய்", "1 லி",  "₹25"),
    ]
    y = 500
    for n, q, c in rows:
        d.text((60, y), n, font=f_p, fill=INK)
        d.text((460, y), q, font=f_p, fill=INK)
        d.text((680, y), c, font=f_p, fill=INK)
        y += 55
    _hline(d, y + 20)
    d.text((60, y + 50), "மொத்தம்: ₹68.50", font=f_h2, fill=INK)
    d.text((60, y + 120), "அடுத்த மாதம் 5-ஆம் தேதிக்கு பின் வாங்கலாம்.", font=f_s, fill=GREY)

    img.save(OUT / "ration_receipt_tamil.jpg", quality=88)


def make_marathi_letter() -> None:
    """Government health-camp letter in Marathi (Devanagari) — fourth Indic script."""
    img, d = _new()
    f_h1 = _font(34, bold=True, indic=True)
    f_h2 = _font(28, bold=True, indic=True)
    f_p  = _font(26, indic=True)
    f_s  = _font(20, indic=True)

    d.text((60, 60), "महाराष्ट्र शासन — आरोग्य विभाग", font=f_h1, fill=INK)
    d.text((60, 110), "प्राथमिक आरोग्य केंद्र, येरवडा, पुणे", font=f_s, fill=GREY)
    _hline(d, 165)

    d.text((60, 200), "विषय: मोफत आरोग्य शिबिर", font=f_h2, fill=INK)
    d.text((60, 245), "दिनांक: ०३ मे २०२६", font=f_s, fill=GREY)

    d.text((60, 320), "श्रीमती / श्रीमान,", font=f_p, fill=INK)
    d.multiline_text(
        (60, 380),
        "येत्या रविवारी, १० मे २०२६ रोजी, सकाळी\n"
        "९ ते दुपारी १ या वेळेत, येरवडा PHC येथे\n"
        "मोफत आरोग्य तपासणी शिबिर आयोजित आहे।\n\n"
        "रक्तदाब, साखर, हिमोग्लोबिन, BMI ची\n"
        "मोफत तपासणी होईल। आधार कार्ड सोबत\n"
        "आणावे।",
        font=f_p, fill=INK, spacing=10,
    )
    d.text((60, 1050), "—  वैद्यकीय अधिकारी, डॉ. एम. अय्यर", font=f_s, fill=INK)
    img.save(OUT / "marathi_letter.jpg", quality=88)


def make_fever_paper() -> None:
    img, d = _new()
    f_h1 = _font(40, bold=True)
    f_h2 = _font(28, bold=True)
    f_p  = _font(24)
    f_s  = _font(20)
    d.text((60, 60), "OBSERVATION NOTE", font=f_h1, fill=INK)
    d.text((60, 110), "PHC Yerwada  ·  03 May 2026, 16:40", font=f_s, fill=GREY)
    _hline(d, 165)
    d.text((60, 195), "Patient: Karan Kale (8 mo)", font=f_p, fill=INK)
    d.text((60, 235), "Mother: Asha Kale", font=f_p, fill=INK)
    _hline(d, 290)
    d.text((60, 320), "Findings:", font=f_h2, fill=INK)
    d.multiline_text(
        (60, 370),
        "•  Temperature: 102.4°F\n"
        "•  Respiratory rate: 64 / min  (high)\n"
        "•  Chest indrawing: present\n"
        "•  Refusing feeds for 6 hours",
        font=f_p, fill=INK, spacing=10,
    )
    _hline(d, 620)
    d.text((60, 650), "REFER URGENTLY", font=f_h2, fill=RED)
    d.multiline_text(
        (60, 710),
        "Take baby to district hospital today.\n"
        "Show this paper at the emergency desk.",
        font=f_p, fill=INK, spacing=8,
    )
    d.text((60, 1100), "—  Dr. M. Iyer (signature)", font=f_s, fill=INK)
    img.save(OUT / "fever_paper.jpg", quality=88)


if __name__ == "__main__":
    make_prescription_devanagari()
    make_school_notice()
    make_ration_receipt_tamil()
    make_marathi_letter()
    make_fever_paper()
    for f in sorted(OUT.glob("*.jpg")):
        print(f.name, f.stat().st_size, "bytes")
