from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SoundResult:
    success: bool
    message: str


class AlertSound:
    """Windows 기본 시스템 경고음 재생."""

    @staticmethod
    def play() -> SoundResult:
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return SoundResult(True, "경고음을 재생했습니다.")
        except Exception as exc:
            return SoundResult(False, f"경고음 재생 실패: {exc}")
