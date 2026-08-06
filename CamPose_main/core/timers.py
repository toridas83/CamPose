from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.classifier import PostureResult


@dataclass
class PostureTimer:
    level: int = 0
    duration: float = 0.0
    missing_for: float = 0.0
    notified_levels: set[int] = field(default_factory=set)


class PostureTimerManager:
    def __init__(self):
        self.states: dict[str, PostureTimer] = {}
        self._last_update = time.monotonic()

    def reset(self) -> None:
        self.states.clear()
        self._last_update = time.monotonic()

    def update(self, results: list[PostureResult], settings: dict) -> list[dict]:
        now = time.monotonic()
        dt = min(now - self._last_update, 0.25)
        self._last_update = now
        active = {item.name: item for item in results}
        alerts: list[dict] = []
        recovery = float(settings.get("recovery_seconds", 10))

        for name, result in active.items():
            state = self.states.setdefault(name, PostureTimer())
            state.level = result.level
            state.duration += dt
            state.missing_for = 0.0
            limit = float(settings.get(f"level_{result.level}_seconds", 60))
            if state.duration >= limit and result.level not in state.notified_levels:
                state.notified_levels.add(result.level)
                alerts.append({"name": name, "level": result.level, "duration": state.duration})

        for name, state in list(self.states.items()):
            if name in active:
                continue
            # 좋은 자세가 회복 판정 시간을 모두 채우기 전까지는 같은 자세 상태로
            # 유지한다. 회복 시간이 지나 상태가 삭제된 뒤 재발하면 0초부터 다시 센다.
            state.missing_for += dt
            if state.missing_for >= recovery:
                del self.states[name]

        return alerts

    def snapshot(self) -> dict[str, dict]:
        return {
            name: {"level": state.level, "duration": state.duration}
            for name, state in self.states.items()
            if state.missing_for == 0.0
        }
