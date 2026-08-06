"""
설정 화면
알림, 경고, 카메라 등 사용자 환경 설정을 담당합니다.
"""

import customtkinter as ctk
from tkinter import messagebox

from gui.constants import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_BUTTON,
    PAD_X,
    PAD_Y,
    CARD_CORNER,
)


class SettingsPage(ctk.CTkFrame):
    """설정 화면 클래스"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # grid 가중치 — 창 크기 변경 시 내용이 늘어나도록 설정
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

    def _build_header(self):
        """상단 제목 영역"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="설정",
            font=FONT_HEADING,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="알림, 경고, 카메라 등을 설정합니다.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_content(self):
        """설정 항목 카드"""
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLOR_ACCENT,
            scrollbar_button_hover_color=COLOR_ACCENT_HOVER,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.grid_columnconfigure(0, weight=1)

        # ── 알림 설정 카드 ──
        alert_card = self._make_card(scroll, "알림 설정")
        alert_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        alert_card.grid_columnconfigure(1, weight=1)

        self.switch_screen = self._add_switch_row(alert_card, 0, "화면 알림", True)
        self.switch_sound = self._add_switch_row(alert_card, 1, "경고음", True)
        self.switch_rest = self._add_switch_row(alert_card, 2, "휴식 알림", False)

        self.combo_warning_time = self._add_combo_row(
            alert_card, 3, "경고 발생 시간", ["5초", "10초", "20초", "30초"], "10초"
        )
        self.combo_renotify = self._add_combo_row(
            alert_card, 4, "재알림 간격", ["1분", "3분", "5분", "10분"], "3분"
        )

        # ── 감지 설정 카드 ──
        detect_card = self._make_card(scroll, "감지 설정")
        detect_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        detect_card.grid_columnconfigure(1, weight=1)

        self._add_slider_row(detect_card, 0, "감지 민감도")
        self.switch_skeleton = self._add_switch_row(detect_card, 1, "관절선 표시", True)

        # ── 카메라 설정 카드 ──
        cam_card = self._make_card(scroll, "카메라 설정")
        cam_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        cam_card.grid_columnconfigure(1, weight=1)

        self.combo_camera = self._add_combo_row(
            cam_card,
            0,
            "카메라 선택",
            ["기본 웹캠 (가상)", "외장 USB 카메라 (가상)", "노트북 내장 카메라 (가상)"],
            "기본 웹캠 (가상)",
        )

        # ── 저장 버튼 ──
        save_btn = ctk.CTkButton(
            scroll,
            text="설정 저장",
            font=FONT_BUTTON,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            height=40,
            command=self._on_save,
        )
        save_btn.grid(row=3, column=0, sticky="ew", pady=(4, 16))

    # ── UI 헬퍼 메서드 ───────────────────────────────

    def _make_card(self, parent, title: str) -> ctk.CTkFrame:
        """제목이 있는 카드 프레임 생성"""
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=FONT_BODY_BOLD,
            text_color=COLOR_ACCENT,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8))

        return card

    def _add_switch_row(self, parent, row: int, label: str, default: bool) -> ctk.CTkSwitch:
        """스위치 한 줄 추가"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=row + 1, column=0, sticky="w", padx=16, pady=8)

        switch = ctk.CTkSwitch(
            parent,
            text="",
            width=46,
            progress_color=COLOR_ACCENT,
            button_color=COLOR_TEXT,
            button_hover_color=COLOR_TEXT_DIM,
        )
        switch.grid(row=row + 1, column=1, sticky="e", padx=16, pady=8)
        if default:
            switch.select()
        return switch

    def _add_combo_row(
        self, parent, row: int, label: str, values: list, default: str
    ) -> ctk.CTkComboBox:
        """콤보박스 한 줄 추가"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=row + 1, column=0, sticky="w", padx=16, pady=8)

        combo = ctk.CTkComboBox(
            parent,
            values=values,
            font=FONT_BODY,
            dropdown_font=FONT_BODY,
            fg_color=COLOR_CARD,
            border_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
            width=200,
        )
        combo.set(default)
        combo.grid(row=row + 1, column=1, sticky="e", padx=16, pady=8)
        return combo

    def _add_slider_row(self, parent, row: int, label: str):
        """슬라이더 한 줄 추가"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=row + 1, column=0, sticky="w", padx=16, pady=8)

        slider_frame = ctk.CTkFrame(parent, fg_color="transparent")
        slider_frame.grid(row=row + 1, column=1, sticky="e", padx=16, pady=8)

        self.slider_sensitivity = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=100,
            number_of_steps=20,
            width=160,
            progress_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
        )
        self.slider_sensitivity.set(60)
        self.slider_sensitivity.pack(side="left", padx=(0, 8))

        self.lbl_sensitivity = ctk.CTkLabel(
            slider_frame,
            text="60",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            width=30,
        )
        self.lbl_sensitivity.pack(side="left")

        # 슬라이더 값 변경 시 숫자 라벨 갱신
        self.slider_sensitivity.configure(
            command=lambda v: self.lbl_sensitivity.configure(text=str(int(v)))
        )

    def _on_save(self):
        """설정 저장 버튼 — 현재는 가짜 저장 후 완료 메시지만 표시"""
        messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
