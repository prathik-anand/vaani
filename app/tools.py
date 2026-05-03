"""Vaani's tool surface.

Tools are defined in the OpenAI/Gemma function-calling shape so the same definitions
work whether the inference backend is Ollama, transformers, or the scripted stub.

In the demo, tool execution is a recorded JSON event — no real reminders are set,
no real messages are drafted. The point is to make the agentic loop *visible* on
screen, not to ship a production calendar integration tonight.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    result: Dict[str, Any]


# Each entry: (definition for the model, executor for our server)
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Schedule a recurring reminder on the user's phone for a medicine or appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "med": {"type": "string", "description": "Medicine or task name as printed on the paper."},
                    "times": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Times of day in HH:MM 24-hour format.",
                    },
                    "days": {"type": "integer", "description": "Number of days the reminder should repeat."},
                },
                "required": ["med", "times", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_reply",
            "description": "Draft a short reply (SMS, WhatsApp, school note) on the user's behalf.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "intent": {"type": "string", "description": "What the user wants to communicate, in plain words."},
                    "language": {"type": "string", "description": "Output language code, e.g. 'en', 'hi', 'ta'."},
                },
                "required": ["recipient", "intent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_red_flag",
            "description": "Mark an urgent warning sign that requires the user to go to a clinic today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["symptom", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_questions_for_clinic",
            "description": "Generate a short list of questions the user should ask at their next clinic visit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "language": {"type": "string"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_medicine_meaning",
            "description": "Explain in plain language what a medicine printed on the paper does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "language": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
]


def _set_reminder(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": True,
        "summary": f"Reminder set for {args.get('med')} at "
        f"{', '.join(args.get('times', []))} for {args.get('days')} days.",
    }


def _draft_reply(args: Dict[str, Any]) -> Dict[str, Any]:
    intent = args.get("intent", "")
    return {
        "ok": True,
        "draft": f"Namaste — {intent}. Dhanyavaad.",
        "language": args.get("language", "hi"),
    }


def _flag_red_flag(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": True,
        "severity": "high",
        "message": f"Go to clinic today: {args.get('symptom')} — {args.get('reason')}",
    }


def _prepare_questions(args: Dict[str, Any]) -> Dict[str, Any]:
    topic = args.get("topic", "your visit")
    return {
        "ok": True,
        "questions": [
            f"What exactly is {topic}?",
            "What should I avoid?",
            "When should I come back?",
        ],
    }


def _lookup_medicine(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("name", "")
    return {
        "ok": True,
        "name": name,
        "explanation": f"{name} is a common medicine. The doctor prescribed it for the issue on the paper.",
    }


_DISPATCH: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "set_reminder": _set_reminder,
    "draft_reply": _draft_reply,
    "flag_red_flag": _flag_red_flag,
    "prepare_questions_for_clinic": _prepare_questions,
    "lookup_medicine_meaning": _lookup_medicine,
}


def execute(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    fn = _DISPATCH.get(name)
    if fn is None:
        return {"ok": False, "error": f"unknown tool: {name}"}
    try:
        return fn(args)
    except Exception as e:  # noqa: BLE001  --  demo robustness
        return {"ok": False, "error": str(e)}


def names() -> List[str]:
    return list(_DISPATCH.keys())
