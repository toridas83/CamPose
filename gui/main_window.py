from __future__ import annotations

from queue import Empty, SimpleQueue
from tkinter import messagebox

import customtkinter as ctk

from gui.constants import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG,
    COLOR_SIDEBAR,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    FONT_SIDEBAR,
    FONT_TITLE,
    SIDEBAR_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)


class MainWindow(ctk.CTk):
    def __init__(self, enable_tray: bool = True):
        super().__init__()
        # OpenCV 5가 Tcl/Tk보다 먼저 로드되면 일부 Windows Conda 환경에서
        # Tcl DLL 탐색이 충돌한다. Tk 생성 후 자세 엔진을 지연 import한다.
        from core.service import PostureService
        from gui.alerts import AlertPresenter

        self.title("CamPose · 자세 모니터링")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.service = PostureService()
        self.alert_presenter = AlertPresenter(self)
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._sidebar_buttons: dict[str, ctk.CTkButton] = {}
        self._current_page = ""
        self._tray_actions: SimpleQueue[str] = SimpleQueue()
        self._tray = None
        self._hidden_notice_sent = False
        self._exiting = False

        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_pages()
        self._show_page("monitoring")
        self.after(150, self._poll_service_alerts)
        if enable_tray:
            from core.tray import TrayController

            self._tray = TrayController(
                on_open=lambda: self._tray_actions.put("open"),
                on_exit=lambda: self._tray_actions.put("exit"),
            )
            self._tray.start()
            self.after(200, self._poll_tray_actions)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR, corner_radius=0, width=SIDEBAR_WIDTH)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            sidebar, text="CamPose\n자세 모니터링", font=FONT_TITLE,
            text_color=COLOR_ACCENT, justify="left"
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(26, 34))

        for row, (key, label) in enumerate(
            [("monitoring", "실시간 측정"), ("history", "기록"), ("settings", "설정")], start=1
        ):
            button = ctk.CTkButton(
                sidebar, text=label, font=FONT_SIDEBAR, anchor="w", height=44,
                corner_radius=8, fg_color="transparent", text_color=COLOR_TEXT,
                hover_color=COLOR_ACCENT_HOVER, command=lambda page=key: self._show_page(page)
            )
            button.grid(row=row, column=0, sticky="ew", padx=12, pady=4)
            self._sidebar_buttons[key] = button

        exit_area = ctk.CTkFrame(sidebar, fg_color="transparent")
        exit_area.grid(row=5, column=0, sticky="sew", padx=12, pady=(0, 6))
        ctk.CTkButton(
            exit_area, text="백그라운드로 숨기기", height=34, font=("맑은 고딕", 11),
            fg_color="transparent", border_width=1, border_color=COLOR_TEXT_DIM,
            command=self._hide_to_tray,
        ).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            exit_area, text="앱 완전히 종료", height=34, font=("맑은 고딕", 11),
            fg_color="transparent", border_width=1, border_color="#ef5350",
            text_color="#ef5350", command=self._confirm_exit,
        ).pack(fill="x")
        ctk.CTkLabel(
            sidebar, text="v0.4 개발용 MVP", font=("맑은 고딕", 10), text_color=COLOR_TEXT_DIM
        ).grid(row=6, column=0, sticky="sw", padx=20, pady=(4, 12))

    def _build_pages(self) -> None:
        from gui.history_page import HistoryDetailPage, HistoryPage
        from gui.monitoring_page import BaselinePage, DeveloperCameraPage, MonitoringPage
        from gui.settings_page import SettingsPage

        content = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self._pages = {
            "monitoring": MonitoringPage(content, self.service, self._show_page),
            "baseline": BaselinePage(content, self.service, self._show_page),
            "developer_camera": DeveloperCameraPage(content, self.service, self._show_page),
            "history": HistoryPage(content, self._open_history_detail),
            "history_detail": HistoryDetailPage(content, self._show_page),
            "settings": SettingsPage(content, self.service, self._show_test_alert),
        }
        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _open_history_detail(self, record: dict) -> None:
        detail = self._pages["history_detail"]
        detail.set_record(record)
        self._show_page("history_detail")

    def _show_page(self, page_key: str) -> None:
        if page_key == self._current_page:
            return
        if self._current_page:
            current = self._pages[self._current_page]
            if hasattr(current, "on_hide"):
                current.on_hide()
        for page in self._pages.values():
            page.grid_remove()
        page = self._pages[page_key]
        page.grid(row=0, column=0, sticky="nsew")
        if hasattr(page, "refresh"):
            page.refresh()
        if hasattr(page, "on_show"):
            page.on_show()
        self._current_page = page_key

        menu_key = {
            "baseline": "monitoring",
            "developer_camera": "monitoring",
            "history_detail": "history",
        }.get(page_key, page_key)
        for key, button in self._sidebar_buttons.items():
            button.configure(fg_color=COLOR_ACCENT if key == menu_key else "transparent")

    def _on_close(self) -> None:
        if self._tray:
            choice = messagebox.askyesnocancel(
                "CamPose 닫기",
                "백그라운드에서 자세 측정을 계속할까요?\n\n"
                "예: 시스템 트레이로 숨기기\n"
                "아니오: 카메라를 해제하고 완전히 종료\n"
                "취소: 대시보드로 돌아가기",
            )
            if choice is True:
                self._hide_to_tray()
            elif choice is False:
                self._exit_app()
            return
        self._exit_app()

    def _hide_to_tray(self) -> None:
        if not self._tray:
            messagebox.showinfo("백그라운드 실행", "시스템 트레이 기능이 비활성화되어 있습니다.")
            return
        self.withdraw()
        if not self._hidden_notice_sent:
            self.alert_presenter.show(
                "CamPose가 백그라운드에서 실행 중입니다.",
                "작업 표시줄의 CamPose 아이콘을 두 번 클릭하면 대시보드가 다시 열립니다.",
                1,
                "우측 하단 팝업",
                False,
            )
            self._hidden_notice_sent = True

    def _confirm_exit(self) -> None:
        if messagebox.askyesno("앱 완전히 종료", "자세 측정을 중단하고 CamPose를 완전히 종료할까요?"):
            self._exit_app()

    def _poll_tray_actions(self) -> None:
        try:
            while True:
                action = self._tray_actions.get_nowait()
                if action == "open":
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                elif action == "exit":
                    self._exit_app()
                    return
        except Empty:
            pass
        self.after(200, self._poll_tray_actions)

    def _poll_service_alerts(self) -> None:
        if self._exiting:
            return
        alerts = self.service.pop_alerts()
        if alerts:
            settings = self.service.settings
            monitoring = self._pages.get("monitoring")
            for alert in alerts:
                if monitoring:
                    monitoring.show_alert(alert)
                if settings.get("screen_alert", True):
                    self.alert_presenter.show(
                        f"{alert['name']} · {alert['level']}단계",
                        f"나쁜 자세가 {int(alert['duration'])}초 지속되었습니다. 자세를 바꿔 주세요.",
                        int(alert["level"]),
                        str(settings.get("alert_display", "팝업 + 테두리")),
                        bool(settings.get("sound_alert", False)),
                    )
                elif settings.get("sound_alert", False):
                    from core.notifications import AlertSound

                    AlertSound.play()
        self.after(150, self._poll_service_alerts)

    def _show_test_alert(self, style: str, sound: bool) -> None:
        self.alert_presenter.show(
            "CamPose 알림 테스트 · 3단계",
            "다른 프로그램을 보고 있을 때에도 이 알림이 표시되는지 확인해 주세요.",
            3,
            style,
            sound,
        )

    def _exit_app(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        self.alert_presenter.close()
        if self._tray:
            self._tray.stop()
            self._tray = None
        self.service.shutdown()
        self.destroy()

    def request_safe_exit(self) -> None:
        """Ctrl+C와 자동화 테스트에서 확인창 없이 안전하게 종료한다."""
        self._exit_app()
