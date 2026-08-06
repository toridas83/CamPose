"""
웹 — 설정 화면
"""

from nicegui import ui


def build_settings_page(container):
    """설정 화면 UI 구성"""

    with container:
        ui.label("설정").classes("page-title")
        ui.label("알림, 경고, 카메라 등을 설정합니다.").classes("text-dim mb-4")

        # 알림 설정
        with ui.column().classes("card w-full mb-3"):
            ui.label("알림 설정").classes("text-accent font-bold mb-2")
            _switch_row("화면 알림", True)
            _switch_row("경고음", True)
            _switch_row("휴식 알림", False)
            _combo_row("경고 발생 시간", ["5초", "10초", "20초", "30초"], "10초")
            _combo_row("재알림 간격", ["1분", "3분", "5분", "10분"], "3분")

        # 감지 설정
        with ui.column().classes("card w-full mb-3"):
            ui.label("감지 설정").classes("text-accent font-bold mb-2")
            with ui.row().classes("setting-row w-full"):
                ui.label("감지 민감도").classes("text-white")
                ui.slider(min=0, max=100, value=60).classes("w-40").props("color=green")
            _switch_row("관절선 표시", True)

        # 카메라 설정
        with ui.column().classes("card w-full mb-3"):
            ui.label("카메라 설정").classes("text-accent font-bold mb-2")
            _combo_row(
                "카메라 선택",
                ["기본 웹캠 (가상)", "외장 USB 카메라 (가상)", "노트북 내장 카메라 (가상)"],
                "기본 웹캠 (가상)",
            )

        ui.button("설정 저장", on_click=lambda: ui.notify("설정이 저장되었습니다.", type="positive")).props(
            "color=green"
        ).classes("w-full")


def _switch_row(label: str, default: bool):
    """스위치 한 줄"""
    with ui.row().classes("setting-row w-full"):
        ui.label(label).classes("text-white")
        ui.switch(value=default).props("color=green")


def _combo_row(label: str, options: list, default: str):
    """콤보박스 한 줄"""
    with ui.row().classes("setting-row w-full"):
        ui.label(label).classes("text-white")
        ui.select(options, value=default).classes("w-48").props("dense outlined dark")
