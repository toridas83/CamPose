from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"
BASELINE_PATH = DATA_DIR / "baseline.json"
HISTORY_PATH = DATA_DIR / "history.json"


DEFAULT_SETTINGS: dict[str, Any] = {
    "camera_index": 0,
    "camera_name": "",
    "show_skeleton": True,
    "screen_alert": True,
    "sound_alert": False,
    "alert_display": "팝업 + 테두리",
    "sensitivity": "기본",
    "level_1_seconds": 120,
    "level_2_seconds": 60,
    "level_3_seconds": 20,
    "recovery_seconds": 10,
    "renotify_seconds": 180,
    "static_posture_minutes": 25,
    "work_break_minutes": 50,
    "break_minutes": 5,
    "enabled_postures": {
        "거북목": True,
        "고개 숙임": True,
        "고개 기울임": True,
        "어깨 비대칭": True,
        "어깨 으쓱": True,
        "몸통 전방 기울임": True,
        "몸통 측면 기울임": True,
        "몸통 비틀림": True,
        "화면에 가까움": True,
        "한쪽 다리 올림": True,
        "양쪽 다리 올림": True,
        "다리 꼬기": True,
    },
}


class JsonStore:
    def __init__(self, path: Path, default: Any):
        self.path = path
        self.default = default
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Any:
        with self._lock:
            if not self.path.exists():
                return deepcopy(self.default)
            try:
                with self.path.open("r", encoding="utf-8") as file:
                    loaded = json.load(file)
            except (OSError, json.JSONDecodeError):
                return deepcopy(self.default)
        if isinstance(self.default, dict) and isinstance(loaded, dict):
            return _deep_merge(deepcopy(self.default), loaded)
        return loaded

    def save(self, value: Any) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(value, file, ensure_ascii=False, indent=2)
            temp_path.replace(self.path)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


settings_store = JsonStore(SETTINGS_PATH, DEFAULT_SETTINGS)
baseline_store = JsonStore(BASELINE_PATH, {})
history_store = JsonStore(HISTORY_PATH, [])
