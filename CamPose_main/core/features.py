from __future__ import annotations

import math
from statistics import median
from typing import Any, Iterable


NOSE = 0
LEFT_EYE = 2
RIGHT_EYE = 5
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


def _point(landmarks: list[Any], index: int) -> tuple[float, float, float, float]:
    item = landmarks[index]
    return float(item.x), float(item.y), float(item.z), float(getattr(item, "visibility", 1.0))


def _mid(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple((x + y) / 2.0 for x, y in zip(a, b))


def _distance_2d(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _distance_3d(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _line_angle(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _vertical_angle(top: tuple[float, ...], bottom: tuple[float, ...]) -> float:
    dx = top[0] - bottom[0]
    dy = bottom[1] - top[1]
    return math.degrees(math.atan2(dx, max(abs(dy), 1e-6)))


def _joint_angle(a: tuple[float, ...], b: tuple[float, ...], c: tuple[float, ...]) -> float:
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    denom = math.hypot(*ba) * math.hypot(*bc)
    if denom < 1e-8:
        return 0.0
    cosine = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / denom))
    return math.degrees(math.acos(cosine))


def extract_features(image_landmarks: list[Any], world_landmarks: list[Any] | None) -> dict[str, float]:
    points = [_point(image_landmarks, i) for i in range(33)]
    world = [_point(world_landmarks, i) for i in range(33)] if world_landmarks else points

    ls, rs = points[LEFT_SHOULDER], points[RIGHT_SHOULDER]
    lh, rh = points[LEFT_HIP], points[RIGHT_HIP]
    le, re = points[LEFT_EAR], points[RIGHT_EAR]
    ley, rey = points[LEFT_EYE], points[RIGHT_EYE]
    shoulder_mid = _mid(ls, rs)
    hip_mid = _mid(lh, rh)
    ear_mid = _mid(le, re)
    shoulder_width = max(_distance_2d(ls, rs), 1e-5)
    hip_width = max(_distance_2d(lh, rh), 1e-5)
    torso_length = max(_distance_2d(shoulder_mid, hip_mid), 1e-5)
    face_width = max(_distance_2d(le, re), _distance_2d(ley, rey), 1e-5)

    wls, wrs = world[LEFT_SHOULDER], world[RIGHT_SHOULDER]
    wlh, wrh = world[LEFT_HIP], world[RIGHT_HIP]
    wle, wre = world[LEFT_EAR], world[RIGHT_EAR]
    wshoulder_mid = _mid(wls, wrs)
    whip_mid = _mid(wlh, wrh)
    wear_mid = _mid(wle, wre)
    world_torso = max(_distance_3d(wshoulder_mid, whip_mid), 1e-5)
    world_shoulder = max(_distance_3d(wls, wrs), 1e-5)

    lk, rk = points[LEFT_KNEE], points[RIGHT_KNEE]
    la, ra = points[LEFT_ANKLE], points[RIGHT_ANKLE]
    lower_visibility = min(lh[3], rh[3], max(lk[3], rk[3]))

    return {
        "face_width": face_width,
        "shoulder_width": shoulder_width,
        "hip_width": hip_width,
        "torso_length": torso_length,
        "face_shoulder_ratio": face_width / shoulder_width,
        "shoulder_hip_ratio": shoulder_width / hip_width,
        "torso_shoulder_ratio": torso_length / shoulder_width,
        "ear_shoulder_gap": (shoulder_mid[1] - ear_mid[1]) / shoulder_width,
        "left_ear_shoulder_gap": (ls[1] - le[1]) / shoulder_width,
        "right_ear_shoulder_gap": (rs[1] - re[1]) / shoulder_width,
        "eye_angle": _line_angle(ley, rey),
        "ear_angle": _line_angle(le, re),
        "shoulder_angle": _line_angle(ls, rs),
        "hip_angle": _line_angle(lh, rh),
        "torso_lateral_angle": _vertical_angle(shoulder_mid, hip_mid),
        "torso_offset": (shoulder_mid[0] - hip_mid[0]) / shoulder_width,
        "head_offset": (ear_mid[0] - shoulder_mid[0]) / shoulder_width,
        "head_forward": (wshoulder_mid[2] - wear_mid[2]) / world_torso,
        "trunk_forward": (whip_mid[2] - wshoulder_mid[2]) / world_torso,
        "shoulder_depth_asymmetry": abs(wls[2] - wrs[2]) / world_shoulder,
        "left_knee_gap": (lk[1] - lh[1]) / torso_length,
        "right_knee_gap": (rk[1] - rh[1]) / torso_length,
        "knee_height_asymmetry": abs(lk[1] - rk[1]) / torso_length,
        "left_ankle_center_cross": max(0.0, (la[0] - hip_mid[0]) / shoulder_width),
        "right_ankle_center_cross": max(0.0, (hip_mid[0] - ra[0]) / shoulder_width),
        "left_hip_angle": _joint_angle(ls, lh, lk),
        "right_hip_angle": _joint_angle(rs, rh, rk),
        "left_knee_angle": _joint_angle(lh, lk, la),
        "right_knee_angle": _joint_angle(rh, rk, ra),
        "pose_visibility": median(point[3] for point in (ls, rs, lh, rh, le, re)),
        "lower_visibility": lower_visibility,
        "left_knee_visibility": lk[3],
        "right_knee_visibility": rk[3],
        "left_ankle_visibility": la[3],
        "right_ankle_visibility": ra[3],
    }


def aggregate_baseline(samples: Iterable[dict[str, float]]) -> dict[str, Any]:
    rows = list(samples)
    if not rows:
        raise ValueError("기준 자세 표본이 없습니다.")
    keys = rows[0].keys()
    medians = {key: median(row[key] for row in rows) for key in keys}
    deviations = {
        key: median(abs(row[key] - medians[key]) for row in rows)
        for key in keys
    }
    return {
        "features": medians,
        "mad": deviations,
        "sample_count": len(rows),
        "lower_body_available": medians.get("lower_visibility", 0.0) >= 0.6,
    }


def median_features(samples: Iterable[dict[str, float]]) -> dict[str, float]:
    rows = list(samples)
    if not rows:
        return {}
    return {key: median(row[key] for row in rows) for key in rows[0]}

