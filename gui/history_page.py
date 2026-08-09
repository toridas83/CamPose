from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.storage import clear_sessions, delete_session, load_sessions, record_id
from gui.constants import (
    CARD_CORNER,
    COLOR_ACCENT,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_ORANGE,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SMALL,
    LEVEL_COLORS,
    PAD_X,
    PAD_Y,
)
from gui.monitoring_page import format_duration


class HistoryPage(ctk.CTkFrame):
    def __init__(self, master, open_detail, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.open_detail = open_detail
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self.summary = ctk.CTkFrame(self, fg_color="transparent")
        self.summary.grid(row=1, column=0, sticky="ew", padx=PAD_X, pady=PAD_Y)
        self.summary.grid_columnconfigure((0, 1, 2), weight=1)
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=COLOR_ACCENT)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=PAD_X, pady=(0, PAD_Y))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.refresh()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="측정 기록", font=FONT_HEADING, text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text="영상이 아닌 자세 종류·등급·지속시간 수치만 저장합니다.",
            font=FONT_BODY, text_color=COLOR_TEXT_DIM
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ctk.CTkButton(
            header, text="전체 기록 삭제", width=130, font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_DANGER, text_color=COLOR_DANGER,
            command=self._delete_all,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

    def refresh(self) -> None:
        for child in self.summary.winfo_children():
            child.destroy()
        for child in self.list_frame.winfo_children():
            child.destroy()
        sessions = load_sessions()
        today = datetime.now().date().isoformat()
        today_sessions = [item for item in sessions if str(item.get("started_at", "")).startswith(today)]
        total = sum(item.get("elapsed_seconds", 0.0) for item in today_sessions)
        weighted_good = sum(item.get("elapsed_seconds", 0.0) * item.get("good_ratio", 0.0) for item in today_sessions)
        good_ratio = weighted_good / total if total else 0.0
        warnings = sum(item.get("warning_count", 0) for item in today_sessions)
        self._stat_card(0, "오늘 측정 시간", format_duration(total, True), COLOR_ACCENT)
        self._stat_card(1, "오늘 좋은 자세", f"{good_ratio:.0f}%" if total else "-", COLOR_SUCCESS)
        self._stat_card(2, "오늘 경고", f"{warnings}회", COLOR_WARNING)

        if not sessions:
            ctk.CTkLabel(
                self.list_frame, text="저장된 측정 기록이 없습니다.\n측정을 종료하면 이곳에 기록됩니다.",
                font=FONT_BODY, text_color=COLOR_TEXT_DIM, justify="center"
            ).grid(row=0, column=0, pady=80)
            return
        for row, record in enumerate(sessions):
            self._session_card(row, record)

    def _stat_card(self, column: int, title: str, value: str, color: str) -> None:
        card = ctk.CTkFrame(self.summary, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
        ctk.CTkLabel(card, text=title, font=FONT_SMALL, text_color=COLOR_TEXT_DIM).pack(pady=(15, 4))
        ctk.CTkLabel(card, text=value, font=FONT_BODY_BOLD, text_color=color).pack(pady=(0, 15))

    def _session_card(self, row: int, record: dict) -> None:
        card = ctk.CTkFrame(self.list_frame, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        start = display_datetime(record.get("started_at", ""))
        end = display_datetime(record.get("ended_at", ""), time_only=True)
        ctk.CTkLabel(card, text=f"{start} ~ {end}", font=FONT_BODY_BOLD, text_color=COLOR_ACCENT).grid(
            row=0, column=0, sticky="w", padx=16, pady=(13, 5)
        )
        ctk.CTkLabel(
            card,
            text=(f"측정 {format_duration(record.get('elapsed_seconds', 0), True)}   ·   "
                  f"좋은 자세 {record.get('good_ratio', 0):.1f}%   ·   경고 {record.get('warning_count', 0)}회"),
            font=FONT_BODY, text_color=COLOR_TEXT
        ).grid(row=1, column=0, sticky="w", padx=16, pady=3)
        postures = record.get("postures", {})
        details = "   ".join(
            f"{name} {value.get('max_level', 0)}단계 {format_duration(value.get('seconds', 0))}"
            for name, value in sorted(postures.items(), key=lambda item: -item[1].get("seconds", 0))[:5]
        ) if postures else "감지된 나쁜 자세 없음"
        ctk.CTkLabel(
            card, text=details, font=FONT_SMALL, text_color=COLOR_TEXT_DIM, wraplength=760, justify="left"
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(3, 13))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=3, sticky="e", padx=14)
        ctk.CTkButton(
            actions, text="상세 보기", width=95, fg_color=COLOR_ACCENT,
            command=lambda value=record: self.open_detail(value)
        ).pack(pady=(0, 6))
        ctk.CTkButton(
            actions, text="삭제", width=95, fg_color="transparent", border_width=1,
            border_color=COLOR_DANGER, text_color=COLOR_DANGER,
            command=lambda value=record: self._delete_one(value)
        ).pack()

    def _delete_one(self, record: dict) -> None:
        if not messagebox.askyesno("기록 삭제", "선택한 측정 기록을 삭제할까요?"):
            return
        delete_session(record_id(record))
        self.refresh()

    def _delete_all(self) -> None:
        sessions = load_sessions()
        if not sessions:
            messagebox.showinfo("기록 삭제", "삭제할 기록이 없습니다.")
            return
        if not messagebox.askyesno("전체 기록 삭제", f"저장된 기록 {len(sessions)}개를 모두 삭제할까요?\n이 작업은 되돌릴 수 없습니다."):
            return
        clear_sessions()
        self.refresh()


class HistoryDetailPage(ctk.CTkFrame):
    def __init__(self, master, navigate, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.navigate = navigate
        self.record: dict = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))
        self.header.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            self.header, text="← 뒤로", width=90, font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_TEXT_DIM, command=lambda: self.navigate("history")
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
        self.title_label = ctk.CTkLabel(self.header, text="세션 상세", font=FONT_HEADING, text_color=COLOR_TEXT)
        self.title_label.grid(row=0, column=1, sticky="w")
        self.subtitle_label = ctk.CTkLabel(self.header, text="", font=FONT_BODY, text_color=COLOR_TEXT_DIM)
        self.subtitle_label.grid(row=1, column=1, sticky="w", pady=(4, 0))
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=COLOR_ACCENT)
        self.content.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        self.content.grid_columnconfigure(0, weight=1)

    def set_record(self, record: dict) -> None:
        self.record = record

    def refresh(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()
        if not self.record:
            return
        start = display_datetime(self.record.get("started_at", ""))
        end = display_datetime(self.record.get("ended_at", ""), time_only=True)
        self.subtitle_label.configure(text=f"{start} ~ {end}")

        summary = ctk.CTkFrame(self.content, fg_color="transparent")
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        summary.grid_columnconfigure((0, 1, 2), weight=1)
        self._summary_card(summary, 0, "측정 시간", format_duration(self.record.get("elapsed_seconds", 0), True), COLOR_ACCENT)
        self._summary_card(summary, 1, "좋은 자세", f"{self.record.get('good_ratio', 0):.1f}%", COLOR_SUCCESS)
        self._summary_card(summary, 2, "경고 횟수", f"{self.record.get('warning_count', 0)}회", COLOR_WARNING)

        chart = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        chart.grid(row=1, column=0, sticky="ew")
        chart.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(chart, text="자세별 감지 시간", font=FONT_BODY_BOLD, text_color=COLOR_ACCENT).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(16, 10)
        )
        postures = self.record.get("postures", {})
        max_seconds = max((item.get("seconds", 0.0) for item in postures.values()), default=1.0)
        if not postures:
            ctk.CTkLabel(chart, text="감지된 나쁜 자세가 없습니다.", font=FONT_BODY, text_color=COLOR_TEXT_DIM).grid(
                row=1, column=0, columnspan=3, pady=28
            )
        for row, (name, value) in enumerate(
            sorted(postures.items(), key=lambda item: -item[1].get("seconds", 0.0)), start=1
        ):
            level = int(value.get("max_level", 0))
            seconds = float(value.get("seconds", 0.0))
            ctk.CTkLabel(chart, text=name, font=FONT_BODY, text_color=COLOR_TEXT, width=150, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(18, 8), pady=9
            )
            bar = ctk.CTkProgressBar(chart, height=16, progress_color=LEVEL_COLORS.get(level, COLOR_ACCENT))
            bar.set(seconds / max_seconds if max_seconds else 0)
            bar.grid(row=row, column=1, sticky="ew", padx=8, pady=9)
            ctk.CTkLabel(
                chart, text=f"{format_duration(seconds)} · {level}단계", font=FONT_SMALL,
                text_color=LEVEL_COLORS.get(level, COLOR_TEXT_DIM), width=110, anchor="e"
            ).grid(row=row, column=2, sticky="e", padx=(8, 18), pady=9)
        ctk.CTkLabel(
            chart,
            text="막대 길이는 이 세션에서 가장 오래 감지된 자세를 100%로 한 상대 비교입니다.",
            font=FONT_SMALL, text_color=COLOR_TEXT_DIM
        ).grid(row=len(postures) + 1, column=0, columnspan=3, sticky="w", padx=18, pady=(8, 16))

    @staticmethod
    def _summary_card(parent, column: int, title: str, value: str, color: str) -> None:
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
        ctk.CTkLabel(card, text=title, font=FONT_SMALL, text_color=COLOR_TEXT_DIM).pack(pady=(15, 4))
        ctk.CTkLabel(card, text=value, font=FONT_BODY_BOLD, text_color=color).pack(pady=(0, 15))


def display_datetime(value: str, time_only: bool = False) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%H:%M:%S" if time_only else "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return value or "-"
