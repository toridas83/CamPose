from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from core.config import history_store


def append_session(record: dict[str, Any]) -> None:
    record.setdefault("session_id", uuid4().hex)
    history = history_store.load()
    if not isinstance(history, list):
        history = []
    history.insert(0, record)
    history_store.save(history[:200])


def load_sessions() -> list[dict[str, Any]]:
    history = history_store.load()
    return history if isinstance(history, list) else []


def delete_session(session_id: str) -> bool:
    history = load_sessions()
    filtered = [record for record in history if _record_id(record) != session_id]
    if len(filtered) == len(history):
        return False
    history_store.save(filtered)
    return True


def clear_sessions() -> int:
    history = load_sessions()
    history_store.save([])
    return len(history)


def record_id(record: dict[str, Any]) -> str:
    return _record_id(record)


def _record_id(record: dict[str, Any]) -> str:
    return str(record.get("session_id") or record.get("started_at") or "")


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
