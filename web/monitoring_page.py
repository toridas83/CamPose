"""
웹 — 실시간 측정 화면 + 기준 자세 설정 다이얼로그
"""

from nicegui import ui

from gui.constants import POSTURE_COLORS
from gui.monitoring_page import POSTURE_STATES


class MonitoringState:
    """측정 타이머 상태 (웹 세션용)"""

    def __init__(self):
        self.elapsed = 0
        self.bad_posture = 0
        self.running = False
        self.paused = False
        self.current_posture = "좋은 자세"


def build_monitoring_page(container, state: MonitoringState):
    """실시간 측정 화면 UI 구성"""

    # UI 요소 참조 (타이머 콜백에서 갱신)
    refs = {}

    def format_hms(sec: int) -> str:
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def format_mmss(sec: int) -> str:
        m, s = divmod(sec, 60)
        return f"{m:02d}:{s:02d}"

    def update_posture_label(value: str):
        """자세 상태 라벨 색상 갱신"""
        color = POSTURE_COLORS.get(value, "#eaeaea")
        refs["posture_label"].text = value
        refs["posture_label"].style(f"color: {color}")

    def on_posture_change(e):
        state.current_posture = e.value
        update_posture_label(e.value)
        if e.value != "나쁜 자세":
            state.bad_posture = 0
            refs["bad_label"].text = "00:00"

    def tick():
        """1초마다 타이머 갱신"""
        if not state.running or state.paused:
            return
        state.elapsed += 1
        if state.current_posture == "나쁜 자세":
            state.bad_posture += 1
        refs["elapsed_label"].text = format_hms(state.elapsed)
        refs["bad_label"].text = format_mmss(state.bad_posture)

    def start_timer():
        if state.running and not state.paused:
            return
        state.running = True
        state.paused = False
        refs["btn_start"].disable()
        refs["btn_pause"].enable()
        refs["btn_stop"].enable()
        refs["btn_pause"].text = "일시정지"
        timer.activate()

    def pause_timer():
        if not state.running:
            return
        if state.paused:
            state.paused = False
            refs["btn_pause"].text = "일시정지"
            timer.activate()
        else:
            state.paused = True
            refs["btn_pause"].text = "재개"
            timer.deactivate()

    def stop_timer():
        state.running = False
        state.paused = False
        state.elapsed = 0
        state.bad_posture = 0
        timer.deactivate()
        refs["elapsed_label"].text = "00:00:00"
        refs["bad_label"].text = "00:00"
        refs["btn_start"].enable()
        refs["btn_pause"].disable()
        refs["btn_pause"].text = "일시정지"
        refs["btn_stop"].disable()

    # 기준 자세 다이얼로그
    dialog_refs = {"captured": False, "countdown_job": None}

    def open_baseline_dialog():
        dialog_refs["captured"] = False
        dialog_refs["countdown_label"].text = ""
        dialog_refs["status_label"].text = "기준 자세를 촬영해 주세요."
        dialog_refs["status_label"].classes(remove="text-success text-warning")
        baseline_dialog.open()

    def start_capture():
        if dialog_refs.get("countdown_active"):
            return
        dialog_refs["countdown_active"] = True
        dialog_refs["captured"] = False
        dialog_refs["status_label"].text = "촬영 준비 중..."
        dialog_refs["status_label"].classes(add="text-warning")
        _run_countdown(3)

    def _run_countdown(n: int):
        if n > 0:
            dialog_refs["countdown_label"].text = str(n)
            ui.timer(1.0, lambda: _run_countdown(n - 1), once=True)
        else:
            dialog_refs["countdown_label"].text = "📸"
            dialog_refs["countdown_active"] = False
            dialog_refs["captured"] = True
            dialog_refs["status_label"].text = "✓ 기준 자세 촬영 완료!"
            dialog_refs["status_label"].classes(remove="text-warning", add="text-success")

    def reset_capture():
        dialog_refs["countdown_active"] = False
        dialog_refs["captured"] = False
        dialog_refs["countdown_label"].text = ""
        dialog_refs["status_label"].text = "기준 자세를 다시 촬영해 주세요."
        dialog_refs["status_label"].classes(remove="text-success text-warning")

    def save_baseline():
        if not dialog_refs["captured"]:
            ui.notify("먼저 기준 자세를 촬영해 주세요.", type="warning")
            return
        ui.notify("기준 자세가 저장되었습니다.", type="positive")
        baseline_dialog.close()

    with container:
        ui.label("실시간 측정").classes("page-title")
        ui.label("웹캠으로 자세를 실시간 분석합니다.").classes("text-dim mb-4")

        with ui.row().classes("w-full gap-4 items-start"):
            # 왼쪽: 카메라 미리보기
            with ui.column().classes("flex-[3] w-full"):
                with ui.element("div").classes("preview-box w-full"):
                    ui.label("카메라 미리보기")

            # 오른쪽: 상태 패널
            with ui.column().classes("flex-[2] w-full gap-3"):
                with ui.column().classes("card w-full"):
                    ui.label("현재 자세 상태").classes("text-dim text-sm")
                    refs["posture_label"] = ui.label("좋은 자세").classes("posture-label text-success")

                    ui.separator().classes("my-2")

                    with ui.row().classes("w-full justify-between"):
                        ui.label("측정 시간").classes("text-dim text-sm")
                        refs["elapsed_label"] = ui.label("00:00:00").classes("timer-label text-accent")
                    with ui.row().classes("w-full justify-between"):
                        ui.label("나쁜 자세 지속").classes("text-dim text-sm")
                        refs["bad_label"] = ui.label("00:00").classes("font-bold text-danger")
                    with ui.row().classes("w-full justify-between"):
                        ui.label("오늘 경고 횟수").classes("text-dim text-sm")
                        ui.label("2회").classes("font-bold text-warning")

                # 테스트 콤보박스
                with ui.row().classes("card w-full items-center justify-between"):
                    ui.label("테스트: 자세 상태").classes("text-dim text-sm")
                    ui.select(POSTURE_STATES, value="좋은 자세", on_change=on_posture_change).classes(
                        "w-40"
                    ).props("dense outlined dark")

                # 버튼
                ui.button("기준 자세 설정", on_click=open_baseline_dialog).props("outline color=green").classes(
                    "w-full"
                )
                with ui.row().classes("w-full gap-2"):
                    refs["btn_start"] = ui.button("측정 시작", on_click=start_timer).props("color=green").classes(
                        "flex-1"
                    )
                    refs["btn_pause"] = ui.button("일시정지", on_click=pause_timer).props("color=orange").classes(
                        "flex-1"
                    )
                    refs["btn_pause"].disable()
                refs["btn_stop"] = ui.button("측정 종료", on_click=stop_timer).props("color=red").classes("w-full")
                refs["btn_stop"].disable()

    # 1초 타이머 (비활성 상태로 시작)
    timer = ui.timer(1.0, tick, active=False)

    # 기준 자세 팝업
    with ui.dialog() as baseline_dialog, ui.card().classes("p-6").style("min-width: 420px; background: #0f3460"):
        ui.label("기준 자세 설정").classes("text-xl font-bold text-white mb-2")
        with ui.element("div").classes("preview-box w-full mb-3"):
            ui.label("카메라 미리보기")
        ui.label("등을 곧게 펴고 모니터 정면을 바라본 자세로\n3초 카운트다운 후 기준 자세를 촬영하세요.").classes(
            "text-dim text-sm mb-2"
        )
        dialog_refs["countdown_label"] = ui.label("").classes("timer-label text-accent text-center w-full")
        dialog_refs["status_label"] = ui.label("기준 자세를 촬영해 주세요.").classes("font-bold text-white mb-3")
        with ui.row().classes("w-full gap-2"):
            ui.button("기준 자세 촬영", on_click=start_capture).props("color=green").classes("flex-1")
            ui.button("다시 촬영", on_click=reset_capture).props("outline color=green").classes("flex-1")
            ui.button("기준 자세 저장", on_click=save_baseline).props("color=green").classes("flex-1")

    update_posture_label("좋은 자세")
