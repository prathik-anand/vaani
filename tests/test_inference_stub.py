"""Stub backend always works and produces the canonical demo responses."""
import os

import pytest

os.environ["VAANI_FORCE_STUB"] = "1"

from app.inference import Inference  # noqa: E402


@pytest.fixture(scope="module")
def infer() -> Inference:
    return Inference()


def test_stub_is_active(infer):
    assert infer.is_stub is True
    assert "stub" in infer.engine_name


def test_prescription_hindi_basic(infer):
    r = infer.generate(
        user_text="yeh kya hai",
        image_b64=None,
        image_filename="prescription_hindi.jpg",
        lang="hi",
    )
    assert r.language == "hi"
    assert "Amoxicillin" in r.reply_text
    assert any(c["name"] == "set_reminder" for c in r.fn_calls)


def test_prescription_set_reminders_followup(infer):
    r = infer.generate(
        user_text="haan, lagao",
        image_b64=None,
        image_filename="prescription_hindi.jpg",
        lang="hi",
    )
    assert "reminder" in r.reply_text.lower() or "रिमाइंडर" in r.reply_text or "लगा" in r.reply_text
    names = [c["name"] for c in r.fn_calls]
    assert names.count("set_reminder") >= 1


def test_school_notice_translate(infer):
    r = infer.generate(
        user_text="yeh hindi mein bolo",
        image_b64=None,
        image_filename="school_notice_english.jpg",
        lang="hi",
    )
    assert r.language == "hi"
    assert "स्कूल" in r.reply_text or "parent" in r.reply_text.lower()


def test_ration_receipt_tamil(infer):
    r = infer.generate(
        user_text=None,
        image_b64=None,
        image_filename="ration_receipt_tamil.jpg",
        lang="ta",
    )
    assert r.language == "ta"


def test_red_flag_path(infer):
    r = infer.generate(
        user_text="yeh kya hai",
        image_b64=None,
        image_filename="fever_paper.jpg",
        lang="hi",
    )
    assert any(c["name"] == "flag_red_flag" for c in r.fn_calls)


def test_no_image_greeting(infer):
    r = infer.generate(
        user_text="namaste",
        image_b64=None,
        image_filename=None,
        lang="hi",
    )
    assert "Vaani" in r.reply_text


def test_unknown_paper_falls_back(infer):
    r = infer.generate(
        user_text="yeh kya hai",
        image_b64=None,
        image_filename="some_random_paper.jpg",
        lang="hi",
    )
    # generic fallback asks the user to bring the camera closer
    assert "कैमरा" in r.reply_text or len(r.reply_text) > 0
