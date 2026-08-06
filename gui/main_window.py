"""
메인 윈도우
사이드바 네비게이션과 화면 전환을 담당합니다.
"""

from typing import Optional

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
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
)
from gui.monitoring_page import MonitoringPage
from gui.history_page import HistoryPage
from gui.settings_page import SettingsPage


class MainWindow(ctk.CTk):
    """프로그램 메인 창"""

    def __init__(self):
        super().__init__()

        # ── 창 기본 설정 ──
        self.title("자세 모니터링")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=COLOR_BG)

        # grid 레이아웃 — 사이드바(0) + 콘텐츠(1)
        self.grid_columnconfigure(0, weight=0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar_buttons: dict[str, ctk.CTkButton] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._current_page: Optional[str] = None

        self._build_sidebar()
        self._build_content_area()
        self._show_page("monitoring")

    def _build_sidebar(self):
        """왼쪽 사이드바 메뉴"""
        sidebar = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR, corner_radius=0, width=SIDEBAR_WIDTH)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(4, weight=1)  # 하단 여백 확보

        # 앱 로고 / 제목
        ctk.CTkLabel(
            sidebar,
            text="🧘 자세\n모니터링",
            font=FONT_TITLE,
            text_color=COLOR_ACCENT,
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(24, 32))

        # 메뉴 항목 정의 (키, 표시 이름)
        menus = [
            ("monitoring", "📷  실시간 측정"),
            ("history", "📊  기록"),
            ("settings", "⚙️  설정"),
        ]

        for i, (key, label) in enumerate(menus):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=FONT_SIDEBAR,
                anchor="w",
                height=44,
                corner_radius=8,
                fg_color="transparent",
                text_color=COLOR_TEXT,
                hover_color=COLOR_ACCENT_HOVER,
                command=lambda k=key: self._show_page(k),
            )
            btn.grid(row=i + 1, column=0, sticky="ew", padx=12, pady=4)
            self._sidebar_buttons[key] = btn

        # 하단 버전 정보
        ctk.CTkLabel(
            sidebar,
            text="v0.1 프로토타입",
            font=("맑은 고딕", 10),
            text_color=COLOR_TEXT_DIM,
        ).grid(row=5, column=0, sticky="sw", padx=20, pady=16)

    def _build_content_area(self):
        """오른쪽 콘텐츠 영역 — 각 화면 페이지를 담는 컨테이너"""
        self.content = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # 각 페이지 생성 (처음에는 숨김)
        self._pages["monitoring"] = MonitoringPage(self.content)
        self._pages["history"] = HistoryPage(self.content)
        self._pages["settings"] = SettingsPage(self.content)

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _show_page(self, page_key: str):
        """선택한 페이지만 보이도록 전환"""
        if page_key == self._current_page:
            return

        # 모든 페이지 숨기기
        for key, page in self._pages.items():
            page.grid_remove()

        # 선택 페이지 표시
        self._pages[page_key].grid(row=0, column=0, sticky="nsew")
        self._current_page = page_key

        # 사이드바 버튼 활성/비활성 스타일 갱신
        for key, btn in self._sidebar_buttons.items():
            if key == page_key:
                btn.configure(fg_color=COLOR_ACCENT, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT)
