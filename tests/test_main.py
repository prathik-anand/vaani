"""HTTP surface — /health, /tools, /info, /turn (text-only and image-bearing paths)."""
import io
import os

os.environ["VAANI_FORCE_STUB"] = "1"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_reports_engine():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["is_stub"] is True


def test_info_lists_tools_and_offline_claim():
    r = client.get("/info")
    assert r.status_code == 200
    j = r.json()
    assert j["offline"] is True
    assert "set_reminder" in j["tools"]


def test_tools_endpoint_lists_5():
    r = client.get("/tools")
    j = r.json()
    assert len(j) == 5
    assert {t["name"] for t in j} >= {"set_reminder", "flag_red_flag", "draft_reply"}


def test_turn_text_only_greeting():
    r = client.post(
        "/turn",
        data={"text": "namaste", "lang": "hi"},
    )
    assert r.status_code == 200
    j = r.json()
    assert "Vaani" in j["reply_text"]
    assert j["language"] == "hi"


def test_turn_with_image_filename_only():
    """Stub uses filename to classify; no real image bytes needed for the canonical path."""
    r = client.post(
        "/turn",
        data={"text": "yeh kya hai", "lang": "hi", "image_filename": "prescription_hindi.jpg"},
    )
    assert r.status_code == 200
    j = r.json()
    assert "Amoxicillin" in j["reply_text"]
    assert any(fc["name"] == "set_reminder" for fc in j["fn_calls"])
    assert j["elapsed_ms"] >= 0


def test_turn_with_image_upload():
    """Upload a tiny dummy file; stub still classifies by filename."""
    fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 64
    r = client.post(
        "/turn",
        data={"text": "yeh kya hai", "lang": "hi"},
        files={"image": ("school_notice_english.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
    )
    assert r.status_code == 200
    j = r.json()
    assert "स्कूल" in j["reply_text"] or "parent" in j["reply_text"].lower()


def test_turn_red_flag_path():
    r = client.post(
        "/turn",
        data={"text": "yeh kya hai", "lang": "hi", "image_filename": "fever_paper.jpg"},
    )
    j = r.json()
    assert any(fc["name"] == "flag_red_flag" for fc in j["fn_calls"])
