"""
기록 화면
오늘의 측정 요약과 최근 측정 기록을 표시합니다. (가짜 데이터)
"""

import customtkinter as ctk

from gui.constants import (
    COLOR_ACCENT,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SMALL,
    PAD_X,
    PAD_Y,
    CARD_CORNER,
)


# 가짜 측정 기록 5건
FAKE_HISTORY = [
    {"date": "2026-08-04", "time": "09:00 ~ 10:30", "duration": "1시간 30분", "good_ratio": 82, "warnings": 3},
    {"date": "2026-08-03", "time": "14:00 ~ 16:15", "duration": "2시간 15분", "good_ratio": 75, "warnings": 7},
    {"date": "2026-08-03", "time": "09:30 ~ 11:00", "duration": "1시간 30분", "good_ratio": 88, "warnings": 1},
    {"date": "2026-08-02", "time": "13:00 ~ 15:45", "duration": "2시간 45분", "good_ratio": 70, "warnings": 9},
    {"date": "2026-08-01", "time": "10:00 ~ 12:00", "duration": "2시간 00분", "good_ratio": 91, "warnings": 0},
]


class HistoryPage(ctk.CTkFrame):
    """기록 화면 클래스"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_summary()
        self._build_history_list()

    def _build_header(self):
        """상단 제목"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))

        ctk.CTkLabel(
            header,
            text="기록",
            font=FONT_HEADING,
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="측정 기록과 통계를 확인합니다.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_DIM,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    def _build_summary(self):
        """오늘 요약 카드 3개 (측정 시간, 바른 자세 비율, 경고 횟수)"""
        summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        summary_frame.grid(row=1, column=0, sticky="ew", padx=PAD_X, pady=PAD_Y)
        summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._make_stat_card(summary_frame, 0, "오늘의 측정 시간", "2시간 15분", COLOR_ACCENT)
        self._make_stat_card(summary_frame, 1, "바른 자세 비율", "78%", COLOR_SUCCESS)
        self._make_stat_card(summary_frame, 2, "경고 횟수", "5회", COLOR_DANGER)

    def _make_stat_card(self, parent, col: int, title: str, value: str, value_color: str):
        """통계 카드 하나 생성"""
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0), pady=0)

        ctk.CTkLabel(
            card,
            text=title,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_DIM,
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            card,
            text=value,
            font=FONT_BODY_BOLD,
            text_color=value_color,
        ).pack(pady=(0, 16))

    def _build_history_list(self):
        """최근 측정 기록 목록"""
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=PAD_X, pady=(0, PAD_Y))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            list_frame,
            text="최근 측정 기록",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            scrollbar_button_color=COLOR_ACCENT,
        )
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        for i, record in enumerate(FAKE_HISTORY):
            self._make_history_card(scroll, i, record)

    def _make_history_card(self, parent, row: int, record: dict):
        """기록 카드 한 건"""
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)

        # 날짜
        ctk.CTkLabel(
            card,
            text=record["date"],
            font=FONT_BODY_BOLD,
            text_color=COLOR_ACCENT,
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 4))

        # 측정 시간대
        ctk.CTkLabel(
            card,
            text=f"측정 시간: {record['time']}",
            font=FONT_BODY,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=2)

        # 측정 지속 / 바른 자세 비율 / 경고
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=16, pady=(4, 12))
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)

        items = [
            ("지속", record["duration"], COLOR_TEXT),
            ("바른 자세", f"{record['good_ratio']}%", COLOR_SUCCESS if record["good_ratio"] >= 80 else COLOR_WARNING),
            ("경고", f"{record['warnings']}회", COLOR_DANGER if record["warnings"] > 0 else COLOR_TEXT_DIM),
        ]
        for col, (label, val, color) in enumerate(items):
            frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame.grid(row=0, column=col, sticky="w")
            ctk.CTkLabel(frame, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_DIM).pack(anchor="w")
            ctk.CTkLabel(frame, text=val, font=FONT_BODY_BOLD, text_color=color).pack(anchor="w")
