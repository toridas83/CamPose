"""
자세 모니터링 — 웹 GUI 프로토타입
브라우저에서 실행됩니다. (NiceGUI)
"""

from nicegui import ui

from web.styles import WEB_CSS
from web.monitoring_page import MonitoringState, build_monitoring_page
from web.history_page import build_history_page
from web.settings_page import build_settings_page


# 페이지 컨테이너와 메뉴 버튼 참조
_pages: dict = {}
_menu_buttons: dict = {}
_monitoring_state = MonitoringState()


@ui.page("/")
def main_page():
    """메인 페이지 — 사이드바 + 콘텐츠 영역"""

    ui.dark_mode(True)
    ui.add_head_html(WEB_CSS)

    def show_page(key: str):
        """선택한 화면만 표시"""
        for k, page in _pages.items():
            visible = k == key
            page.set_visibility(visible)
            page.style(f"display: {'flex' if visible else 'none'}")
        for k, btn in _menu_buttons.items():
            if k == key:
                btn.classes(remove="menu-btn", add="menu-btn-active")
            else:
                btn.classes(remove="menu-btn-active", add="menu-btn")

    with ui.row().classes("w-full min-h-screen no-wrap"):
        # ── 사이드바 ──
        with ui.column().classes("sidebar h-screen p-4 gap-1"):
            ui.label("🧘 자세\n모니터링").classes("text-accent text-xl font-bold mb-6 whitespace-pre-line")

            menus = [
                ("monitoring", "📷  실시간 측정"),
                ("history", "📊  기록"),
                ("settings", "⚙️  설정"),
            ]
            for key, label in menus:
                btn = ui.button(label, on_click=lambda k=key: show_page(k)).classes("menu-btn w-full")
                _menu_buttons[key] = btn

            ui.space()
            ui.label("v0.1 웹 프로토타입").classes("text-dim text-xs")

        # ── 콘텐츠 영역 ──
        with ui.column().classes("flex-grow p-4 overflow-auto"):
            _pages["monitoring"] = ui.column().classes("w-full")
            _pages["history"] = ui.column().classes("w-full")
            _pages["settings"] = ui.column().classes("w-full")

            build_monitoring_page(_pages["monitoring"], _monitoring_state)
            build_history_page(_pages["history"])
            build_settings_page(_pages["settings"])

            # 처음에는 실시간 측정만 표시
            show_page("monitoring")


def main():
    """웹 서버 시작"""
    ui.run(
        title="자세 모니터링",
        host="127.0.0.1",
        port=8765,
        reload=False,
        show=True,  # 브라우저 자동 열기
    )


if __name__ == "__main__":
    main()
