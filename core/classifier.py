from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.features import line_angle_delta


@dataclass(frozen=True)
class PostureResult:
    name: str
    level: int
    score: float
    reason: str


SENSITIVITY_FACTORS = {"강한 교정": 0.75, "기본": 1.0, "여유": 1.25}

# 전면 웹캠의 원근 왜곡과 MediaPipe 추정 오차를 고려한 서비스용 경험 기준이다.
# 임상 진단 기준이 아니며 값은 각각 1단계, 2단계, 3단계 진입 임계값이다.
POSTURE_THRESHOLDS: dict[str, tuple[float, float, float]] = {
    "거북목": (0.10, 0.20, 0.35),
    "고개 숙임": (0.12, 0.25, 0.40),
    "고개 기울임": (10.0, 20.0, 30.0),
    "어깨 비대칭": (10.0, 20.0, 30.0),
    "어깨 으쓱": (0.15, 0.30, 0.50),
    "몸통 전방 기울임": (0.12, 0.25, 0.40),
    "몸통 측면 기울임": (10.0, 20.0, 30.0),
    "몸통 비틀림": (0.15, 0.30, 0.50),
    "화면에 가까움": (0.15, 0.30, 0.50),
    "한쪽 다리 올림": (0.25, 0.45, 0.65),
    "양쪽 다리 올림": (0.25, 0.45, 0.65),
    "다리 꼬기": (0.08, 0.18, 0.30),
}


def _level(value: float, thresholds: tuple[float, float, float]) -> int:
    if value >= thresholds[2]:
        return 3
    if value >= thresholds[1]:
        return 2
    if value >= thresholds[0]:
        return 1
    return 0


def _combined_evidence(first: float, second: float) -> float:
    """서로 다른 두 추정 신호를 결합해 한 신호의 순간 튐이 단계를 지배하지 않게 한다."""
    return (max(0.0, first) + max(0.0, second)) / 2.0


def classify_posture(
    current: dict[str, float],
    baseline: dict[str, Any],
    settings: dict[str, Any],
) -> list[PostureResult]:
    base = baseline.get("features", {})
    mad = baseline.get("mad", {})
    if not base:
        return []
    factor = SENSITIVITY_FACTORS.get(settings.get("sensitivity", "기본"), 1.0)
    enabled = settings.get("enabled_postures", {})
    results: list[PostureResult] = []

    def add(name: str, value: float, limits: tuple[float, float, float], reason: str, noise_key: str | None = None):
        if not enabled.get(name, True):
            return
        adjusted = tuple(limit * factor for limit in limits)
        if noise_key:
            noise_floor = mad.get(noise_key, 0.0) * 3.0
            adjusted = tuple(max(limit, noise_floor) for limit in adjusted)
        level = _level(max(0.0, value), adjusted)
        if level:
            results.append(PostureResult(name, level, value, reason))

    head_forward = current["head_forward"] - base["head_forward"]
    face_growth = current["face_shoulder_ratio"] / max(base["face_shoulder_ratio"], 1e-5) - 1.0
    add("거북목", _combined_evidence(head_forward, face_growth), POSTURE_THRESHOLDS["거북목"], "머리가 어깨보다 카메라 쪽으로 이동", "head_forward")

    gap_drop = base["ear_shoulder_gap"] - current["ear_shoulder_gap"]
    add("고개 숙임", gap_drop, POSTURE_THRESHOLDS["고개 숙임"], "귀-어깨의 세로 간격 감소", "ear_shoulder_gap")

    head_tilt = abs(line_angle_delta(current["eye_angle"], base["eye_angle"]))
    add("고개 기울임", head_tilt, POSTURE_THRESHOLDS["고개 기울임"], "눈 선의 좌우 기울기 변화", "eye_angle")

    shoulder_tilt = abs(line_angle_delta(current["shoulder_angle"], base["shoulder_angle"]))
    add("어깨 비대칭", shoulder_tilt, POSTURE_THRESHOLDS["어깨 비대칭"], "양쪽 어깨 높이 차이", "shoulder_angle")

    shrug = max(
        base["left_ear_shoulder_gap"] - current["left_ear_shoulder_gap"],
        base["right_ear_shoulder_gap"] - current["right_ear_shoulder_gap"],
    )
    add("어깨 으쓱", shrug, POSTURE_THRESHOLDS["어깨 으쓱"], "한쪽 귀-어깨 간격 감소", "ear_shoulder_gap")

    trunk_forward = current["trunk_forward"] - base["trunk_forward"]
    torso_shorten = 1.0 - current["torso_shoulder_ratio"] / max(base["torso_shoulder_ratio"], 1e-5)
    add("몸통 전방 기울임", _combined_evidence(trunk_forward, torso_shorten), POSTURE_THRESHOLDS["몸통 전방 기울임"], "어깨가 골반보다 카메라 쪽으로 이동", "trunk_forward")

    lateral = abs(current["torso_lateral_angle"] - base["torso_lateral_angle"])
    add("몸통 측면 기울임", lateral, POSTURE_THRESHOLDS["몸통 측면 기울임"], "어깨 중심이 골반 중심에서 좌우로 이동", "torso_lateral_angle")

    twist = current["shoulder_depth_asymmetry"] - base["shoulder_depth_asymmetry"]
    add("몸통 비틀림", twist, POSTURE_THRESHOLDS["몸통 비틀림"], "양쪽 어깨의 깊이 차이 증가", "shoulder_depth_asymmetry")

    approach = current["shoulder_width"] / max(base["shoulder_width"], 1e-5) - 1.0
    add("화면에 가까움", approach, POSTURE_THRESHOLDS["화면에 가까움"], "화면 속 어깨 너비 증가", "shoulder_width")

    lower_visible = current.get("lower_visibility", 0.0) >= 0.6
    if lower_visible:
        if baseline.get("lower_body_available", False):
            left_reference = max(base.get("left_knee_gap", 0.75), 0.1)
            right_reference = max(base.get("right_knee_gap", 0.75), 0.1)
        else:
            # 기준 촬영에서 다리가 보이지 않았을 때는 무릎이 몸통 길이의 0.75배 아래에
            # 있는 상태를 임시 중립값으로 사용한다. 이 값은 프로젝트 경험값이다.
            left_reference = right_reference = 0.75
        left_raise = 1.0 - current["left_knee_gap"] / left_reference
        right_raise = 1.0 - current["right_knee_gap"] / right_reference
        raises = sorted((left_raise, right_raise), reverse=True)
        add("한쪽 다리 올림", max(raises[0], current["knee_height_asymmetry"]), POSTURE_THRESHOLDS["한쪽 다리 올림"], "한쪽 무릎이 기준보다 골반 쪽으로 올라옴", "knee_height_asymmetry")
        both_leg_thresholds = tuple(limit * factor for limit in POSTURE_THRESHOLDS["양쪽 다리 올림"])
        if raises[1] >= both_leg_thresholds[0] and enabled.get("양쪽 다리 올림", True):
            level = _level(raises[1], both_leg_thresholds)
            results.append(PostureResult("양쪽 다리 올림", max(2, level), raises[1], "양쪽 무릎이 모두 골반 쪽으로 올라옴"))
        ankle_cross = max(current["left_ankle_center_cross"], current["right_ankle_center_cross"])
        add("다리 꼬기", ankle_cross, POSTURE_THRESHOLDS["다리 꼬기"], "발목이 몸의 중심선을 넘어감", "left_ankle_center_cross")

    return sorted(results, key=lambda item: (-item.level, -item.score, item.name))
