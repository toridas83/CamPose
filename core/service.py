from __future__ import annotations

import os
import threading
import time
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_MPL_CONFIG = Path(__file__).resolve().parents[1] / "data" / "matplotlib"
_MPL_CONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG))

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from core.classifier import PostureResult, classify_posture
from core.cameras import list_camera_devices, resolve_camera_index
from core.config import PROJECT_DIR, baseline_store, settings_store
from core.features import aggregate_baseline, extract_features, median_features
from core.storage import append_session, iso_now
from core.timers import PostureTimerManager


@dataclass
class AnalysisSnapshot:
    frame: np.ndarray | None = None
    camera_open: bool = False
    camera_name: str = ""
    person_detected: bool = False
    lower_body_available: bool = False
    baseline_ready: bool = False
    monitoring: bool = False
    paused: bool = False
    elapsed_seconds: float = 0.0
    fps: float = 0.0
    inference_ms: float = 0.0
    results: list[PostureResult] = field(default_factory=list)
    timers: dict[str, dict] = field(default_factory=dict)
    features: dict[str, float] = field(default_factory=dict)
    error: str = ""
    warning_count: int = 0
    baseline_capturing: bool = False
    baseline_preparing: bool = False
    baseline_prepare_remaining: float = 0.0
    baseline_remaining: float = 0.0
    baseline_samples: int = 0
    baseline_message: str = ""


PROBLEM_JOINTS = {
    "거북목": {0, 7, 8, 11, 12},
    "고개 숙임": {0, 2, 5, 7, 8, 11, 12},
    "고개 기울임": {0, 2, 5, 7, 8},
    "어깨 비대칭": {11, 12, 23, 24},
    "어깨 으쓱": {7, 8, 11, 12},
    "몸통 전방 기울임": {11, 12, 23, 24},
    "몸통 측면 기울임": {11, 12, 23, 24},
    "몸통 비틀림": {11, 12, 23, 24},
    "화면에 가까움": {7, 8, 11, 12, 23, 24},
    "한쪽 다리 올림": {23, 24, 25, 26, 27, 28},
    "양쪽 다리 올림": {23, 24, 25, 26, 27, 28},
    "다리 꼬기": {23, 24, 25, 26, 27, 28},
}

LEVEL_COLORS_BGR = {
    0: (148, 148, 148),
    1: (0, 196, 255),
    2: (0, 140, 255),
    3: (60, 60, 235),
}


class PostureService:
    """카메라 한 개를 공유하는 MediaPipe 자세 분석 서비스."""

    def __init__(self):
        self._lock = threading.Lock()
        self._snapshot = AnalysisSnapshot()
        self._settings = settings_store.load()
        self._baseline = baseline_store.load()
        self._snapshot.baseline_ready = bool(self._baseline.get("features"))

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._camera_requested = False
        self._monitoring = False
        self._paused = False
        self._timer_manager = PostureTimerManager()
        self._alerts: deque[dict[str, Any]] = deque(maxlen=20)

        self._baseline_start_at = 0.0
        self._baseline_deadline = 0.0
        self._baseline_samples: list[dict[str, float]] = []
        self._session: dict[str, Any] | None = None
        self._session_last_tick = time.monotonic()
        self._active_camera_index = int(self._settings.get("camera_index", 0))
        self._active_camera_name = str(self._settings.get("camera_name", ""))

    @property
    def settings(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._settings)

    @property
    def baseline(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._baseline)

    def update_settings(self, settings: dict[str, Any]) -> bool:
        previous_camera = (
            int(self._settings.get("camera_index", 0)),
            str(self._settings.get("camera_name", "")),
        )
        next_camera = (
            int(settings.get("camera_index", 0)),
            str(settings.get("camera_name", "")),
        )
        settings_store.save(settings)
        with self._lock:
            self._settings = deepcopy(settings)
        camera_changed = previous_camera != next_camera
        if camera_changed:
            self.restart_camera()
        return camera_changed

    def restart_camera(self) -> None:
        """설정 변경 후 기존 장치를 해제하고 새 카메라를 즉시 연다."""
        should_reopen = self._camera_requested or self._monitoring
        self._camera_requested = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        self._stop_event.clear()
        if self._baseline_deadline > 0.0:
            self.cancel_baseline_capture()
        with self._lock:
            self._snapshot.frame = None
            self._snapshot.camera_open = False
            self._snapshot.camera_name = ""
            self._snapshot.error = ""
        if should_reopen:
            self.ensure_camera()

    def snapshot(self) -> AnalysisSnapshot:
        with self._lock:
            value = deepcopy(self._snapshot)
            if self._snapshot.frame is not None:
                value.frame = self._snapshot.frame.copy()
            return value

    def pop_alerts(self) -> list[dict[str, Any]]:
        with self._lock:
            values = list(self._alerts)
            self._alerts.clear()
            return values

    def ensure_camera(self) -> None:
        self._camera_requested = True
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="CamPoseWorker", daemon=True)
        self._thread.start()

    def start_monitoring(self) -> None:
        self.ensure_camera()
        self._monitoring = True
        self._paused = False
        self._timer_manager.reset()
        self._session_last_tick = time.monotonic()
        self._session = {
            "started_at": iso_now(),
            "elapsed_seconds": 0.0,
            "good_seconds": 0.0,
            "warning_count": 0,
            "postures": {},
        }

    def toggle_pause(self) -> bool:
        if not self._monitoring:
            return False
        self._paused = not self._paused
        self._session_last_tick = time.monotonic()
        return self._paused

    def stop_monitoring(self) -> None:
        if self._session:
            session = deepcopy(self._session)
            session["ended_at"] = iso_now()
            elapsed = max(session.get("elapsed_seconds", 0.0), 0.001)
            session["good_ratio"] = round(session.get("good_seconds", 0.0) / elapsed * 100, 1)
            append_session(session)
        self._session = None
        self._monitoring = False
        self._paused = False
        self._timer_manager.reset()
        with self._lock:
            self._snapshot.monitoring = False
            self._snapshot.paused = False
            self._snapshot.elapsed_seconds = 0.0
            self._snapshot.timers = {}

    def start_baseline_capture(self, seconds: float = 10.0, prepare_seconds: float = 3.0) -> None:
        self.ensure_camera()
        self._baseline_samples = []
        now = time.monotonic()
        self._baseline_start_at = now + max(0.0, prepare_seconds)
        self._baseline_deadline = self._baseline_start_at + max(0.0, seconds)
        with self._lock:
            self._snapshot.baseline_capturing = True
            self._snapshot.baseline_preparing = prepare_seconds > 0.0
            self._snapshot.baseline_prepare_remaining = max(0.0, prepare_seconds)
            self._snapshot.baseline_remaining = seconds
            self._snapshot.baseline_samples = 0
            self._snapshot.baseline_message = (
                "측정 준비 중입니다." if prepare_seconds > 0.0 else "기준 자세를 유지해 주세요."
            )

    def cancel_baseline_capture(self) -> None:
        self._baseline_start_at = 0.0
        self._baseline_deadline = 0.0
        self._baseline_samples = []
        with self._lock:
            self._snapshot.baseline_capturing = False
            self._snapshot.baseline_preparing = False
            self._snapshot.baseline_prepare_remaining = 0.0
            self._snapshot.baseline_remaining = 0.0
            self._snapshot.baseline_message = "촬영을 취소했습니다."

    def shutdown(self) -> None:
        if self._monitoring:
            self.stop_monitoring()
        self._camera_requested = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

    def _find_model(self) -> Path:
        candidates = [
            PROJECT_DIR / "pose_landmarker_lite.task",
            PROJECT_DIR.parent / "pose_landmarker_lite.task",
        ]
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError("pose_landmarker_lite.task 모델 파일을 찾을 수 없습니다.")

    def _run(self) -> None:
        capture = None
        landmarker = None
        try:
            model_path = self._find_model()
            options = vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            landmarker = vision.PoseLandmarker.create_from_options(options)
            camera_index = resolve_camera_index(
                str(self._settings.get("camera_name", "")),
                int(self._settings.get("camera_index", 0)),
            )
            self._active_camera_index = camera_index
            self._active_camera_name = next(
                (device.name for device in list_camera_devices() if device.index == camera_index),
                f"카메라 {camera_index}",
            )
            capture = cv2.VideoCapture(camera_index)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
            if not capture.isOpened():
                raise RuntimeError(f"카메라 {camera_index}번을 열 수 없습니다.")

            # 약 0.5초 구간의 중앙값으로 순간적인 랜드마크 튐과 카메라 노이즈를 완화한다.
            feature_window: deque[dict[str, float]] = deque(maxlen=15)
            frame_times: deque[float] = deque(maxlen=20)
            timestamp_ms = 0

            while not self._stop_event.is_set() and self._camera_requested:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("카메라 프레임을 읽지 못했습니다.")
                started = time.perf_counter()
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms += 1
                result = landmarker.detect_for_video(image, timestamp_ms)
                inference_ms = (time.perf_counter() - started) * 1000.0

                detected = bool(result.pose_landmarks)
                features: dict[str, float] = {}
                posture_results: list[PostureResult] = []
                landmarks = None
                if detected:
                    landmarks = result.pose_landmarks[0]
                    world = result.pose_world_landmarks[0] if result.pose_world_landmarks else None
                    raw_features = extract_features(landmarks, world)
                    feature_window.append(raw_features)
                    features = median_features(feature_window)
                    if self._baseline.get("features"):
                        posture_results = classify_posture(features, self._baseline, self._settings)
                else:
                    feature_window.clear()

                self._handle_baseline(raw_features if detected else None, frame.shape)
                alerts = []
                if self._monitoring and not self._paused and detected and self._baseline.get("features"):
                    alerts = self._timer_manager.update(posture_results, self._settings)
                    self._update_session(posture_results, len(alerts))
                else:
                    self._session_last_tick = time.monotonic()

                annotated = frame.copy()
                if landmarks and self._settings.get("show_skeleton", True):
                    self._draw_pose(annotated, landmarks, posture_results)
                # 분석은 원본 좌표로 수행하고, 사용자에게 보여주는 화면만 거울처럼 반전한다.
                annotated = cv2.flip(annotated, 1)

                now = time.perf_counter()
                frame_times.append(now)
                fps = 0.0
                if len(frame_times) > 1:
                    fps = (len(frame_times) - 1) / max(frame_times[-1] - frame_times[0], 1e-5)

                with self._lock:
                    self._alerts.extend(alerts)
                    self._snapshot.frame = annotated
                    self._snapshot.camera_open = True
                    self._snapshot.camera_name = self._active_camera_name
                    self._snapshot.person_detected = detected
                    self._snapshot.lower_body_available = features.get("lower_visibility", 0.0) >= 0.6
                    self._snapshot.baseline_ready = bool(self._baseline.get("features"))
                    self._snapshot.monitoring = self._monitoring
                    self._snapshot.paused = self._paused
                    self._snapshot.elapsed_seconds = self._session.get("elapsed_seconds", 0.0) if self._session else 0.0
                    self._snapshot.fps = fps
                    self._snapshot.inference_ms = inference_ms
                    self._snapshot.results = posture_results
                    self._snapshot.timers = self._timer_manager.snapshot()
                    self._snapshot.features = features
                    self._snapshot.error = ""
                    self._snapshot.warning_count = self._session.get("warning_count", 0) if self._session else 0
                time.sleep(0.005)
        except Exception as exc:
            with self._lock:
                self._snapshot.error = str(exc)
                self._snapshot.camera_open = False
        finally:
            if capture is not None:
                capture.release()
            if landmarker is not None:
                landmarker.close()
            with self._lock:
                self._snapshot.camera_open = False

    def _handle_baseline(self, features: dict[str, float] | None, frame_shape: tuple[int, ...]) -> None:
        if self._baseline_deadline <= 0.0:
            return
        now = time.monotonic()
        prepare_remaining = self._baseline_start_at - now
        if prepare_remaining > 0.0:
            with self._lock:
                self._snapshot.baseline_preparing = True
                self._snapshot.baseline_prepare_remaining = prepare_remaining
                self._snapshot.baseline_message = "측정 준비 중입니다. 바른 자세로 앉아 주세요."
            return

        remaining = self._baseline_deadline - now
        if features is not None and features.get("pose_visibility", 0.0) >= 0.6:
            self._baseline_samples.append(features)
        with self._lock:
            self._snapshot.baseline_preparing = False
            self._snapshot.baseline_prepare_remaining = 0.0
            self._snapshot.baseline_message = "기준 자세를 유지해 주세요."
            self._snapshot.baseline_remaining = max(0.0, remaining)
            self._snapshot.baseline_samples = len(self._baseline_samples)

        if remaining > 0.0:
            return
        self._baseline_start_at = 0.0
        self._baseline_deadline = 0.0
        if len(self._baseline_samples) < 20:
            with self._lock:
                self._snapshot.baseline_capturing = False
                self._snapshot.baseline_preparing = False
                self._snapshot.baseline_prepare_remaining = 0.0
                self._snapshot.baseline_message = "사람을 충분히 인식하지 못했습니다. 다시 촬영해 주세요."
            return
        baseline = aggregate_baseline(self._baseline_samples)
        baseline.update({
            "created_at": iso_now(),
            "camera_index": self._active_camera_index,
            "camera_name": self._active_camera_name,
            "resolution": [int(frame_shape[1]), int(frame_shape[0])],
        })
        baseline_store.save(baseline)
        self._baseline = baseline
        self._baseline_samples = []
        with self._lock:
            self._snapshot.baseline_ready = True
            self._snapshot.baseline_capturing = False
            self._snapshot.baseline_preparing = False
            self._snapshot.baseline_prepare_remaining = 0.0
            self._snapshot.baseline_remaining = 0.0
            self._snapshot.baseline_message = "기준 자세가 저장되었습니다."

    def _update_session(self, results: list[PostureResult], alert_count: int = 0) -> None:
        if not self._session:
            return
        now = time.monotonic()
        dt = min(now - self._session_last_tick, 0.25)
        self._session_last_tick = now
        self._session["elapsed_seconds"] += dt
        if not results:
            self._session["good_seconds"] += dt
        for item in results:
            posture = self._session["postures"].setdefault(item.name, {"seconds": 0.0, "max_level": 0})
            posture["seconds"] += dt
            posture["max_level"] = max(posture["max_level"], item.level)
        # 현재 활성 상태가 초기화되어도 세션 전체 경고 횟수는 감소하지 않는다.
        self._session["warning_count"] += alert_count

    def _draw_pose(self, frame: np.ndarray, landmarks: list[Any], results: list[PostureResult]) -> None:
        height, width = frame.shape[:2]
        highest = max((item.level for item in results), default=0)
        problem_joints: set[int] = set()
        for item in results:
            if item.level == highest:
                problem_joints.update(PROBLEM_JOINTS.get(item.name, set()))

        for connection in vision.PoseLandmarksConnections.POSE_LANDMARKS:
            start, end = connection.start, connection.end
            a, b = landmarks[start], landmarks[end]
            if getattr(a, "visibility", 1.0) < 0.5 or getattr(b, "visibility", 1.0) < 0.5:
                continue
            color = LEVEL_COLORS_BGR[highest] if start in problem_joints or end in problem_joints else (150, 150, 150)
            cv2.line(frame, (int(a.x * width), int(a.y * height)), (int(b.x * width), int(b.y * height)), color, 2)
        for index, item in enumerate(landmarks):
            if getattr(item, "visibility", 1.0) < 0.5:
                continue
            color = LEVEL_COLORS_BGR[highest] if index in problem_joints else (0, 184, 148)
            cv2.circle(frame, (int(item.x * width), int(item.y * height)), 3, color, -1)
