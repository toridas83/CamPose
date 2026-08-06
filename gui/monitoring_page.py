"""
실시간 측정 화면 + 기준 자세 설정 팝업
카메라/YOLO 없이 가짜 데이터와 타이머로 동작을 시뮬레이션합니다.
"""

import customtkinter as ctk
from tkinter import messagebox

from gui.constants import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD,
    COLOR_DANGER,
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
    PAD_X,
    PAD_Y,
    CARD_CORNER,
    POSTURE_COLORS,
)

# 테스트용 자세 상태 목록
POSTURE_STATES = ["좋은 자세", "자세 주의", "나쁜 자세", "사람 미감지"]


class BaselinePostureDialog(ctk.CTkToplevel):
    """기준 자세 설정 팝업 창"""

    def __init__(self, master):
        super().__init__(master)

        self.title("기준 자세 설정")
        self.geometry("520x580")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_CARD)

        # 촬영 완료 여부
        self._captured = False
        self._countdown_job = None
        self._countdown_value = 0

        self._build_ui()
        self._center_on_parent(master)

        # 팝업을 모달처럼 동작시키기
        self.transient(master)
        self.grab_set()
        self.focus()

    def _center_on_parent(self, parent):
        """부모 창 중앙에 팝업 배치"""
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self):
        """팝업 UI 구성"""
        self.grid_columnconfigure(0, weight=1)

        # 제목
        ctk.CTkLabel(
            self,
            text="기준 자세 설정",
            font=FONT_HEADING,
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, pady=(20, 8))

        # 카메라 미리보기 (가짜)
        preview = ctk.CTkFrame(self, fg_color=COLOR_PREVIEW_BG, corner_radius=CARD_CORNER, height=220)
        preview.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            preview,
            text="카메라 미리보기",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
        ).grid(row=0, column=0)

        # 안내 문구
        ctk.CTkLabel(
            self,
            text="등을 곧게 펴고 모니터 정면을 바라본 자세로\n3초 카운트다운 후 기준 자세를 촬영하세요.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            justify="center",
        ).grid(row=2, column=0, pady=8)

        # 카운트다운 표시
        self.lbl_countdown = ctk.CTkLabel(
            self,
            text="",
            font=FONT_TIMER,
            text_color=COLOR_ACCENT,
        )
        self.lbl_countdown.grid(row=3, column=0, pady=4)

        # 촬영 상태 표시
        self.lbl_status = ctk.CTkLabel(
            self,
            text="기준 자세를 촬영해 주세요.",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT,
        )
        self.lbl_status.grid(row=4, column=0, pady=4)

        # 버튼 영역
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, pady=20, padx=24, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="기준 자세 촬영",
            font=FONT_BUTTON,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._start_capture,
        ).grid(row=0, column=0, padx=4, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="다시 촬영",
            font=FONT_BUTTON,
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_ACCENT,
            text_color=COLOR_ACCENT,
            hover_color=COLOR_CARD,
            command=self._reset_capture,
        ).grid(row=0, column=1, padx=4, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="기준 자세 저장",
            font=FONT_BUTTON,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._save_baseline,
        ).grid(row=0, column=2, padx=4, sticky="ew")

    def _start_capture(self):
        """3초 카운트다운 후 촬영 완료 상태로 전환"""
        if self._countdown_job:
            return  # 이미 카운트다운 중

        self._captured = False
        self.lbl_status.configure(text="촬영 준비 중...", text_color=COLOR_WARNING)
        self._countdown_value = 3
        self._tick_countdown()

    def _tick_countdown(self):
        """카운트다운 1초씩 감소"""
        if self._countdown_value > 0:
            self.lbl_countdown.configure(text=str(self._countdown_value))
            self._countdown_value -= 1
            self._countdown_job = self.after(1000, self._tick_countdown)
        else:
            self.lbl_countdown.configure(text="📸")
            self._countdown_job = None
            self._captured = True
            self.lbl_status.configure(
                text="✓ 기준 자세 촬영 완료!",
                text_color=COLOR_SUCCESS,
            )

    def _reset_capture(self):
        """촬영 상태 초기화"""
        if self._countdown_job:
            self.after_cancel(self._countdown_job)
            self._countdown_job = None

        self._captured = False
        self._countdown_value = 0
        self.lbl_countdown.configure(text="")
        self.lbl_status.configure(
            text="기준 자세를 다시 촬영해 주세요.",
            text_color=COLOR_TEXT,
        )

    def _save_baseline(self):
        """기준 자세 저장 (가짜)"""
        if not self._captured:
            messagebox.showwarning("저장 불가", "먼저 기준 자세를 촬영해 주세요.")
            return
        messagebox.showinfo("저장 완료", "기준 자세가 저장되었습니다.")
        self.destroy()


class MonitoringPage(ctk.CTkFrame):
    """실시간 측정 화면 클래스"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # 측정 타이머 관련 변수
        self._timer_running = False
        self._timer_paused = False
        self._elapsed_seconds = 0
        self._bad_posture_seconds = 0
        self._timer_job = None
        self._warning_count = 2  # 오늘 경고 횟수 (가짜 초기값)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_preview()
        self._build_status_panel()

    def _build_header(self):
        """상단 제목"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))

        ctk.CTkLabel(
            header,
            text="실시간 측정",
            font=FONT_HEADING,
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="웹캠으로 자세를 실시간 분석합니다.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    def _build_preview(self):
        """왼쪽 16:9 웹캠 미리보기 영역"""
        preview_outer = ctk.CTkFrame(self, fg_color="transparent")
        preview_outer.grid(row=1, column=0, sticky="nsew", padx=(PAD_X, 8), pady=PAD_Y)
        preview_outer.grid_columnconfigure(0, weight=1)
        preview_outer.grid_rowconfigure(0, weight=1)

        # 16:9 비율 유지를 위해 aspect ratio frame 사용
        self.preview_frame = ctk.CTkFrame(
            preview_outer,
            fg_color=COLOR_PREVIEW_BG,
            corner_radius=CARD_CORNER,
        )
        self.preview_frame.grid(row=0, column=0, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            self.preview_frame,
            text="카메라 미리보기",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
        ).grid(row=0, column=0)

    def _build_status_panel(self):
        """오른쪽 상태 카드 + 버튼 패널"""
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=1, column=1, sticky="nsew", padx=(8, PAD_X), pady=PAD_Y)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        # ── 자세 상태 카드 ──
        status_card = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        status_card.grid(row=0, column=0, sticky="nsew")
        status_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status_card,
            text="현재 자세 상태",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_DIM,
        ).grid(row=0, column=0, pady=(16, 4))

        self.lbl_posture = ctk.CTkLabel(
            status_card,
            text="좋은 자세",
            font=FONT_TIMER,
            text_color=COLOR_SUCCESS,
        )
        self.lbl_posture.grid(row=1, column=0, pady=(0, 16))

        # 구분선
        ctk.CTkFrame(status_card, height=1, fg_color=COLOR_TEXT_DIM).grid(
            row=2, column=0, sticky="ew", padx=16
        )

        # 측정 정보
        info_frame = ctk.CTkFrame(status_card, fg_color="transparent")
        info_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        info_frame.grid_columnconfigure(1, weight=1)

        labels = ["측정 시간", "나쁜 자세 지속", "오늘 경고 횟수"]
        self.lbl_elapsed = ctk.CTkLabel(info_frame, text="00:00:00", font=FONT_BODY_BOLD, text_color=COLOR_ACCENT)
        self.lbl_bad_duration = ctk.CTkLabel(info_frame, text="00:00", font=FONT_BODY_BOLD, text_color=COLOR_DANGER)
        self.lbl_warnings = ctk.CTkLabel(info_frame, text="2회", font=FONT_BODY_BOLD, text_color=COLOR_WARNING)

        for i, (label, value_lbl) in enumerate(zip(labels, [self.lbl_elapsed, self.lbl_bad_duration, self.lbl_warnings])):
            ctk.CTkLabel(info_frame, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_DIM, anchor="w").grid(
                row=i, column=0, sticky="w", pady=4
            )
            value_lbl.grid(row=i, column=1, sticky="e", pady=4)

        # ── 테스트용 자세 상태 변경 ──
        test_frame = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        test_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        test_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            test_frame,
            text="테스트: 자세 상태",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_DIM,
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self.combo_posture = ctk.CTkComboBox(
            test_frame,
            values=POSTURE_STATES,
            font=FONT_BODY,
            command=self._on_posture_changed,
            fg_color=COLOR_CARD,
            border_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
        )
        self.combo_posture.set("좋은 자세")
        self.combo_posture.grid(row=0, column=1, padx=12, pady=10, sticky="e")

        # ── 버튼 영역 ──
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="기준 자세 설정",
            font=FONT_BUTTON,
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_ACCENT,
            text_color=COLOR_ACCENT,
            hover_color=COLOR_CARD,
            command=self._open_baseline_dialog,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="측정 시작",
            font=FONT_BUTTON,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._start_timer,
        )
        self.btn_start.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.btn_pause = ctk.CTkButton(
            btn_frame,
            text="일시정지",
            font=FONT_BUTTON,
            fg_color=COLOR_WARNING,
            hover_color="#d68910",
            command=self._pause_timer,
            state="disabled",
        )
        self.btn_pause.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        self.btn_stop = ctk.CTkButton(
            btn_frame,
            text="측정 종료",
            font=FONT_BUTTON,
            fg_color=COLOR_DANGER,
            hover_color="#c0392b",
            command=self._stop_timer,
            state="disabled",
        )
        self.btn_stop.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    # ── 타이머 로직 ──────────────────────────────────

    def _format_time(self, total_seconds: int) -> str:
        """초 → HH:MM:SS 문자열"""
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _format_mmss(self, total_seconds: int) -> str:
        """초 → MM:SS 문자열"""
        m = total_seconds // 60
        s = total_seconds % 60
        return f"{m:02d}:{s:02d}"

    def _start_timer(self):
        """측정 시작 — 타이머 동작"""
        if self._timer_running and not self._timer_paused:
            return

        self._timer_running = True
        self._timer_paused = False
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="일시정지")
        self.btn_stop.configure(state="normal")
        self._tick()

    def _pause_timer(self):
        """일시정지 / 재개 토글"""
        if not self._timer_running:
            return

        if self._timer_paused:
            self._timer_paused = False
            self.btn_pause.configure(text="일시정지")
            self._tick()
        else:
            self._timer_paused = True
            self.btn_pause.configure(text="재개")
            if self._timer_job:
                self.after_cancel(self._timer_job)
                self._timer_job = None

    def _stop_timer(self):
        """측정 종료 — 타이머 초기화"""
        self._timer_running = False
        self._timer_paused = False
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

        self._elapsed_seconds = 0
        self._bad_posture_seconds = 0
        self.lbl_elapsed.configure(text="00:00:00")
        self.lbl_bad_duration.configure(text="00:00")

        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="일시정지")
        self.btn_stop.configure(state="disabled")

    def _tick(self):
        """1초마다 호출되는 타이머"""
        if not self._timer_running or self._timer_paused:
            return

        self._elapsed_seconds += 1

        # 현재 자세가 '나쁜 자세'이면 지속 시간 증가
        current = self.combo_posture.get()
        if current == "나쁜 자세":
            self._bad_posture_seconds += 1

        self.lbl_elapsed.configure(text=self._format_time(self._elapsed_seconds))
        self.lbl_bad_duration.configure(text=self._format_mmss(self._bad_posture_seconds))

        self._timer_job = self.after(1000, self._tick)

    # ── 이벤트 핸들러 ──────────────────────────────────

    def _on_posture_changed(self, value: str):
        """테스트 콤보박스로 자세 상태 변경"""
        color = POSTURE_COLORS.get(value, COLOR_TEXT)
        self.lbl_posture.configure(text=value, text_color=color)

        # 나쁜 자세가 아닌 상태로 바뀌면 지속 시간 리셋
        if value != "나쁜 자세":
            self._bad_posture_seconds = 0
            self.lbl_bad_duration.configure(text="00:00")

    def _open_baseline_dialog(self):
        """기준 자세 설정 팝업 열기"""
        BaselinePostureDialog(self.winfo_toplevel())
