from __future__ import annotations

import time
from tkinter import messagebox

import customtkinter as ctk
import cv2
from PIL import Image

from core.service import AnalysisSnapshot, PostureService
from gui.constants import (
    CARD_CORNER,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD,
    COLOR_CARD_HOVER,
    COLOR_DANGER,
    COLOR_ORANGE,
    COLOR_PREVIEW_BG,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SMALL,
    FONT_TIMER,
    LEVEL_COLORS,
    LEVEL_NAMES,
    PAD_X,
    PAD_Y,
)


def format_duration(seconds: float, include_hours: bool = False) -> str:
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if include_hours else f"{minutes:02d}:{secs:02d}"


def frame_to_ctk(frame, size: tuple[int, int]) -> ctk.CTkImage:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    safe_size = (max(1, int(size[0])), max(1, int(size[1])))
    return ctk.CTkImage(light_image=image, dark_image=image, size=safe_size)


class BaselinePage(ctk.CTkFrame):
    def __init__(self, master, service: PostureService, navigate):
        super().__init__(master, fg_color="transparent")
        self.service = service
        self.navigate = navigate
        self._image = None
        self._job = None
        self._return_job = None
        self._capture_started = False
        self._build_ui()

    def on_show(self) -> None:
        self.service.ensure_camera()
        self._capture_started = False
        self.capture_button.configure(state="normal")
        self.status_label.configure(text="촬영 시작을 눌러 주세요.", text_color=COLOR_TEXT)
        self.progress.set(0)
        if not self._job:
            self._poll()

    def on_hide(self) -> None:
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if self._return_job:
            self.after_cancel(self._return_job)
            self._return_job = None

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="기준 자세 설정", font=FONT_HEADING, text_color=COLOR_TEXT).grid(
            row=0, column=0, pady=(18, 5)
        )
        ctk.CTkLabel(
            self,
            text="정면을 보고 어깨에 힘을 뺀 평소의 바른 작업 자세를 10초간 유지하세요.\n가능하면 엉덩이와 무릎이 화면에 보이고 두 발은 바닥에 둡니다.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            justify="center",
        ).grid(row=1, column=0, pady=(0, 10))

        preview = ctk.CTkFrame(self, fg_color=COLOR_PREVIEW_BG, width=640, height=360, corner_radius=10)
        preview.grid(row=2, column=0, padx=30, pady=4)
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)
        self.image_label = ctk.CTkLabel(preview, text="카메라 준비 중…", text_color=COLOR_TEXT_DIM)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        self.status_label = ctk.CTkLabel(self, text="촬영 시작을 눌러 주세요.", font=FONT_BODY_BOLD, text_color=COLOR_TEXT)
        self.status_label.grid(row=3, column=0, pady=(12, 4))
        self.progress = ctk.CTkProgressBar(self, width=640, progress_color=COLOR_ACCENT)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, pady=6)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="ew", padx=30, pady=12)
        buttons.grid_columnconfigure((0, 1, 2), weight=1)
        self.capture_button = ctk.CTkButton(
            buttons, text="10초 촬영 시작", font=FONT_BUTTON, fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=self._start_capture
        )
        self.capture_button.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(
            buttons, text="다시 촬영", font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_ACCENT, command=self._start_capture
        ).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(
            buttons, text="나가기", font=FONT_BUTTON, fg_color=COLOR_CARD,
            border_width=1, border_color=COLOR_TEXT_DIM, command=self._leave
        ).grid(row=0, column=2, padx=4, sticky="ew")

    def _start_capture(self) -> None:
        snapshot = self.service.snapshot()
        if not snapshot.person_detected:
            messagebox.showwarning("사람 미감지", "먼저 카메라에 상체가 보이도록 앉아 주세요.", parent=self)
            return
        self.service.start_baseline_capture(10.0)
        self._capture_started = True
        self.capture_button.configure(state="disabled")

    def _poll(self) -> None:
        snapshot = self.service.snapshot()
        if snapshot.frame is not None:
            self._image = frame_to_ctk(snapshot.frame, (640, 360))
            self.image_label.configure(image=self._image, text="")
        elif snapshot.error:
            self.image_label.configure(text=snapshot.error)

        if snapshot.baseline_capturing:
            elapsed = 10.0 - snapshot.baseline_remaining
            self.progress.set(max(0.0, min(1.0, elapsed / 10.0)))
            self.status_label.configure(
                text=f"{snapshot.baseline_remaining:0.1f}초 남음 · 유효 프레임 {snapshot.baseline_samples}개",
                text_color=COLOR_WARNING,
            )
        elif snapshot.baseline_message:
            self.progress.set(1 if snapshot.baseline_ready and "저장" in snapshot.baseline_message else 0)
            self.status_label.configure(
                text=snapshot.baseline_message,
                text_color=COLOR_SUCCESS if "저장" in snapshot.baseline_message else COLOR_DANGER,
            )
            self.capture_button.configure(state="normal")
            if self._capture_started and snapshot.baseline_ready and "저장" in snapshot.baseline_message:
                self._capture_started = False
                self.status_label.configure(text="저장 완료 · 잠시 후 홈으로 돌아갑니다.", text_color=COLOR_SUCCESS)
                self._return_job = self.after(1200, lambda: self.navigate("monitoring"))
        self._job = self.after(100, self._poll)

    def _leave(self) -> None:
        snapshot = self.service.snapshot()
        if snapshot.baseline_capturing:
            self.service.cancel_baseline_capture()
        self.navigate("monitoring")


class DeveloperCameraPage(ctk.CTkFrame):
    METRICS = [
        ("얼굴/어깨 비율", "face_shoulder_ratio"),
        ("어깨 각도", "shoulder_angle"),
        ("눈 각도", "eye_angle"),
        ("귀-어깨 간격", "ear_shoulder_gap"),
        ("머리 전방값", "head_forward"),
        ("몸통 전방값", "trunk_forward"),
        ("몸통 측면각", "torso_lateral_angle"),
        ("어깨 깊이차", "shoulder_depth_asymmetry"),
        ("무릎 높이차", "knee_height_asymmetry"),
    ]

    def __init__(self, master, service: PostureService, navigate):
        super().__init__(master, fg_color="transparent")
        self.service = service
        self.navigate = navigate
        self._image = None
        self._job = None
        self._build_ui()

    def on_show(self) -> None:
        self.service.ensure_camera()
        if not self._job:
            # grid 배치 직후에는 페이지 크기가 1x1로 보고될 수 있으므로
            # 한 번의 UI 사이클이 지난 뒤 첫 프레임을 그린다.
            self._job = self.after(50, self._poll)

    def on_hide(self) -> None:
        if self._job:
            self.after_cancel(self._job)
            self._job = None

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD_X, pady=(PAD_Y, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="개발용 캠 · 실시간 측정값", font=FONT_HEADING, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(
            header, text="나가기", width=100, font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_TEXT_DIM, command=lambda: self.navigate("monitoring")
        ).grid(row=0, column=1, sticky="e")
        camera_frame = ctk.CTkFrame(self, fg_color=COLOR_PREVIEW_BG, corner_radius=0)
        camera_frame.grid(row=1, column=0, sticky="nsew")
        camera_frame.grid_columnconfigure(0, weight=1)
        camera_frame.grid_rowconfigure(0, weight=1)
        self.image_label = ctk.CTkLabel(camera_frame, text="카메라 준비 중…", text_color=COLOR_TEXT_DIM)
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        panel = ctk.CTkScrollableFrame(self, fg_color=COLOR_CARD, corner_radius=0)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="실시간 분석", font=FONT_HEADING, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w", padx=16, pady=(18, 8)
        )
        self.summary_label = ctk.CTkLabel(
            panel, text="준비 중", font=FONT_BODY, text_color=COLOR_TEXT_DIM, justify="left", anchor="w"
        )
        self.summary_label.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        self.posture_label = ctk.CTkLabel(
            panel, text="좋은 자세", font=FONT_BODY_BOLD, text_color=COLOR_SUCCESS, justify="left", anchor="w"
        )
        self.posture_label.grid(row=2, column=0, sticky="ew", padx=16, pady=8)

        ctk.CTkLabel(panel, text="현재값 / 기준값 / 변화량", font=FONT_BODY_BOLD, text_color=COLOR_ACCENT).grid(
            row=3, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        self.metric_labels: dict[str, ctk.CTkLabel] = {}
        for row, (title, key) in enumerate(self.METRICS, start=4):
            label = ctk.CTkLabel(panel, text=title, font=FONT_SMALL, text_color=COLOR_TEXT_DIM, justify="left", anchor="w")
            label.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
            self.metric_labels[key] = label

    def _poll(self) -> None:
        self._job = None
        snapshot = self.service.snapshot()
        available_width = self.winfo_width() - 470
        available_height = self.winfo_height() - 90
        width = max(320, available_width)
        height = max(180, min(int(width * 9 / 16), available_height))
        if snapshot.frame is not None:
            self._image = frame_to_ctk(snapshot.frame, (width, height))
            self.image_label.configure(image=self._image, text="")
        elif snapshot.error:
            self.image_label.configure(text=snapshot.error)

        self.summary_label.configure(text=(
            f"사람 감지: {'예' if snapshot.person_detected else '아니오'}\n"
            f"기준 자세: {'설정됨' if snapshot.baseline_ready else '미설정'}\n"
            f"하체 측정: {'가능' if snapshot.lower_body_available else '화면 밖/불충분'}\n"
            f"측정 상태: {'일시정지' if snapshot.paused else '측정 중' if snapshot.monitoring else '대기'}\n"
            f"FPS: {snapshot.fps:.1f} · 추론: {snapshot.inference_ms:.1f} ms"
        ))
        if snapshot.results:
            lines = []
            for item in snapshot.results:
                duration = snapshot.timers.get(item.name, {}).get("duration", 0)
                lines.append(f"{item.name} · {item.level}단계 · {format_duration(duration)}\n  {item.reason}")
            top = snapshot.results[0]
            self.posture_label.configure(text="\n".join(lines), text_color=LEVEL_COLORS[top.level])
        else:
            text = "기준 자세가 필요합니다." if not snapshot.baseline_ready else "좋은 자세 · 0단계"
            self.posture_label.configure(text=text, text_color=COLOR_SUCCESS)

        baseline = self.service.baseline.get("features", {})
        for title, key in self.METRICS:
            current = snapshot.features.get(key)
            base = baseline.get(key)
            if current is None or base is None:
                value = "측정 불가"
            else:
                value = f"{current:+.3f} / {base:+.3f} / {current - base:+.3f}"
            self.metric_labels[key].configure(text=f"{title}\n{value}")
        self._job = self.after(100, self._poll)

class MonitoringPage(ctk.CTkFrame):
    def __init__(self, master, service: PostureService, navigate, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = service
        self.navigate = navigate
        self._job = None
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_overview()
        self._build_status_panel()
        self._poll()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))
        ctk.CTkLabel(header, text="실시간 자세 모니터링", font=FONT_HEADING, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            header, text="영상은 저장하지 않으며, 개발용 캠을 열 때만 화면을 표시합니다.",
            font=FONT_BODY, text_color=COLOR_TEXT_DIM
        ).pack(anchor="w", pady=(4, 0))

    def _build_overview(self) -> None:
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=1, column=0, sticky="nsew", padx=(PAD_X, 8), pady=PAD_Y)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(card, text="모니터링 상태", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_DIM).grid(
            row=0, column=0, pady=(28, 6)
        )
        self.main_posture = ctk.CTkLabel(card, text="대기 중", font=FONT_TIMER, text_color=COLOR_TEXT_DIM)
        self.main_posture.grid(row=1, column=0, pady=4)
        self.main_reason = ctk.CTkLabel(
            card, text="기준 자세를 설정한 후 측정을 시작하세요.", font=FONT_BODY,
            text_color=COLOR_TEXT_DIM, justify="center", wraplength=580
        )
        self.main_reason.grid(row=2, column=0, pady=(4, 16))

        status_box = ctk.CTkFrame(card, fg_color=COLOR_PREVIEW_BG, corner_radius=10)
        status_box.grid(row=3, column=0, sticky="nsew", padx=24, pady=12)
        status_box.grid_columnconfigure(0, weight=1)
        self.active_list = ctk.CTkLabel(
            status_box, text="활성 자세 없음", font=FONT_BODY, text_color=COLOR_TEXT_DIM,
            justify="left", anchor="nw"
        )
        self.active_list.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        ctk.CTkButton(
            card, text="개발용 캠 열기", font=FONT_BUTTON, height=42,
            fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
            text_color=COLOR_ACCENT, hover_color=COLOR_CARD_HOVER,
            command=self._open_developer_camera,
        ).grid(row=4, column=0, sticky="ew", padx=24, pady=(12, 24))

    def _build_status_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=1, column=1, sticky="nsew", padx=(8, PAD_X), pady=PAD_Y)
        panel.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        info.grid(row=0, column=0, sticky="ew")
        info.grid_columnconfigure(1, weight=1)
        self.elapsed_label = self._info_row(info, 0, "측정 시간", "00:00:00", COLOR_ACCENT)
        self.bad_label = self._info_row(info, 1, "대표 나쁜 자세", "00:00", COLOR_DANGER)
        self.warning_label = self._info_row(info, 2, "경고 횟수", "0회", COLOR_WARNING)
        self.camera_label = self._info_row(info, 3, "카메라 / 기준", "대기 / 미설정", COLOR_TEXT)
        self.lower_label = self._info_row(info, 4, "하체 측정", "화면 밖", COLOR_TEXT_DIM)

        self.alert_banner = ctk.CTkLabel(
            panel, text="", font=FONT_BODY_BOLD, text_color=COLOR_WARNING,
            fg_color=COLOR_CARD, corner_radius=8, height=44
        )
        self.alert_banner.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons, text="기준 자세 설정", font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_ACCENT, text_color=COLOR_ACCENT,
            command=self._open_baseline_dialog,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.start_button = ctk.CTkButton(
            buttons, text="측정 시작", font=FONT_BUTTON, fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=self._start
        )
        self.start_button.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.pause_button = ctk.CTkButton(
            buttons, text="일시정지", font=FONT_BUTTON, fg_color=COLOR_WARNING,
            hover_color="#d89112", state="disabled", command=self._pause
        )
        self.pause_button.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        self.stop_button = ctk.CTkButton(
            buttons, text="측정 종료 및 기록 저장", font=FONT_BUTTON, fg_color=COLOR_DANGER,
            hover_color="#c74442", state="disabled", command=self._stop
        )
        self.stop_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _info_row(self, parent, row: int, title: str, value: str, color: str) -> ctk.CTkLabel:
        ctk.CTkLabel(parent, text=title, font=FONT_SMALL, text_color=COLOR_TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=16, pady=10
        )
        label = ctk.CTkLabel(parent, text=value, font=FONT_BODY_BOLD, text_color=color)
        label.grid(row=row, column=1, sticky="e", padx=16, pady=10)
        return label

    def _start(self) -> None:
        if not self.service.baseline.get("features"):
            messagebox.showwarning("기준 자세 필요", "먼저 기준 자세를 설정해 주세요.")
            self._open_baseline_dialog()
            return
        self.service.start_monitoring()
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="일시정지")
        self.stop_button.configure(state="normal")

    def _pause(self) -> None:
        paused = self.service.toggle_pause()
        self.pause_button.configure(text="재개" if paused else "일시정지")

    def _stop(self) -> None:
        self.service.stop_monitoring()
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="일시정지")
        self.stop_button.configure(state="disabled")
        self.alert_banner.configure(text="측정 기록을 저장했습니다.")

    def _open_baseline_dialog(self) -> None:
        self.navigate("baseline")

    def _open_developer_camera(self) -> None:
        self.navigate("developer_camera")

    def _poll(self) -> None:
        snapshot = self.service.snapshot()
        self._render(snapshot)
        self._job = self.after(200, self._poll)

    def show_alert(self, alert: dict) -> None:
        if not self.service.settings.get("screen_alert", True):
            return
        self.alert_banner.configure(
            text=f"{alert['name']} {alert['level']}단계가 {format_duration(alert['duration'])} 지속되었습니다.",
            text_color=LEVEL_COLORS[alert["level"]],
        )

    def _render(self, snapshot: AnalysisSnapshot) -> None:
        self.elapsed_label.configure(text=format_duration(snapshot.elapsed_seconds, True))
        self.warning_label.configure(text=f"{snapshot.warning_count}회")
        self.camera_label.configure(
            text=(f"{snapshot.camera_name or '연결'} / {'설정됨' if snapshot.baseline_ready else '미설정'}"
                  if snapshot.camera_open else f"대기 / {'설정됨' if snapshot.baseline_ready else '미설정'}"),
            text_color=COLOR_SUCCESS if snapshot.camera_open else COLOR_TEXT_DIM,
        )
        self.lower_label.configure(
            text="측정 가능" if snapshot.lower_body_available else "화면 밖/불충분",
            text_color=COLOR_SUCCESS if snapshot.lower_body_available else COLOR_TEXT_DIM,
        )
        if snapshot.error:
            self.main_posture.configure(text="카메라 오류", text_color=COLOR_DANGER)
            self.main_reason.configure(text=snapshot.error)
            return
        if snapshot.paused:
            self.main_posture.configure(text="일시정지", text_color=COLOR_WARNING)
            self.main_reason.configure(text="자세 시간은 누적되지 않습니다.")
            return
        if not snapshot.monitoring:
            self.main_posture.configure(text="대기 중", text_color=COLOR_TEXT_DIM)
            self.main_reason.configure(text="측정 시작 전에는 자세 시간을 누적하지 않습니다.")
        elif not snapshot.person_detected:
            self.main_posture.configure(text="사람 미감지", text_color=COLOR_TEXT_DIM)
            self.main_reason.configure(text="카메라 정면에 상체가 보이도록 앉아 주세요.")
        elif snapshot.results:
            top = snapshot.results[0]
            self.main_posture.configure(text=f"{top.name} · {top.level}단계", text_color=LEVEL_COLORS[top.level])
            self.main_reason.configure(text=top.reason)
        else:
            self.main_posture.configure(text=LEVEL_NAMES[0], text_color=COLOR_SUCCESS)
            self.main_reason.configure(text="기준 자세의 허용 범위 안에 있습니다.")

        lines = []
        for item in snapshot.results:
            duration = snapshot.timers.get(item.name, {}).get("duration", 0.0)
            lines.append(f"● {item.name:<12} {item.level}단계   {format_duration(duration)}")
        self.active_list.configure(text="\n".join(lines) if lines else "활성 자세 없음")
        if snapshot.results:
            top_duration = snapshot.timers.get(snapshot.results[0].name, {}).get("duration", 0.0)
            self.bad_label.configure(text=format_duration(top_duration))
        else:
            self.bad_label.configure(text="00:00")
