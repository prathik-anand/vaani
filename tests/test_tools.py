"""Tools dispatch returns structured results for each registered name."""
from app import tools


def test_tool_definitions_shape():
    for d in tools.TOOL_DEFINITIONS:
        assert d["type"] == "function"
        f = d["function"]
        assert "name" in f and "description" in f and "parameters" in f


def test_set_reminder_executes():
    r = tools.execute("set_reminder", {"med": "Amoxicillin", "times": ["09:00", "21:00"], "days": 7})
    assert r["ok"] is True
    assert "Amoxicillin" in r["summary"]


def test_draft_reply_uses_intent():
    r = tools.execute("draft_reply", {"recipient": "school", "intent": "I will come tomorrow"})
    assert r["ok"] is True
    assert "I will come tomorrow" in r["draft"]


def test_red_flag_marks_high_severity():
    r = tools.execute(
        "flag_red_flag",
        {"symptom": "fever 102°F + fast breathing", "reason": "possible infection"},
    )
    assert r["severity"] == "high"


def test_prepare_questions_returns_list():
    r = tools.execute("prepare_questions_for_clinic", {"topic": "diabetes"})
    assert isinstance(r["questions"], list) and len(r["questions"]) >= 3


def test_lookup_medicine():
    r = tools.execute("lookup_medicine_meaning", {"name": "Paracetamol"})
    assert r["ok"] is True and "Paracetamol" in r["explanation"]


def test_unknown_tool_is_safe():
    r = tools.execute("not_a_tool", {})
    assert r["ok"] is False
    assert "unknown" in r["error"]
