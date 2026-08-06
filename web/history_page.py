"""
웹 — 기록 화면
"""

from nicegui import ui

from gui.constants import COLOR_ACCENT, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING
from gui.history_page import FAKE_HISTORY


def build_history_page(container):
    """기록 화면 UI 구성"""

    with container:
        ui.label("기록").classes("page-title")
        ui.label("측정 기록과 통계를 확인합니다.").classes("text-dim mb-4")

        # 요약 카드 3개
        with ui.row().classes("w-full gap-3 mb-4"):
            _stat_card("오늘의 측정 시간", "2시간 15분", "text-accent")
            _stat_card("바른 자세 비율", "78%", "text-success")
            _stat_card("경고 횟수", "5회", "text-danger")

        ui.label("최근 측정 기록").classes("font-bold text-white mb-2")

        for record in FAKE_HISTORY:
            with ui.element("div").classes("history-card w-full"):
                ui.label(record["date"]).classes("text-accent font-bold")
                ui.label(f"측정 시간: {record['time']}").classes("text-white text-sm")
                with ui.row().classes("gap-8 mt-1"):
                    ui.label(f"지속: {record['duration']}").classes("text-dim text-sm")
                    ratio_color = "text-success" if record["good_ratio"] >= 80 else "text-warning"
                    ui.label(f"바른 자세: {record['good_ratio']}%").classes(f"{ratio_color} text-sm")
                    warn_color = "text-danger" if record["warnings"] > 0 else "text-dim"
                    ui.label(f"경고: {record['warnings']}회").classes(f"{warn_color} text-sm")


def _stat_card(title: str, value: str, value_class: str):
    """통계 카드 하나"""
    with ui.column().classes("stat-card flex-1"):
        ui.label(title).classes("text-dim text-sm")
        ui.label(value).classes(f"{value_class} font-bold text-lg")
