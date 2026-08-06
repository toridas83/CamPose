"""
자세 모니터링 프로그램 — GUI 프로토타입
진입점 (Entry Point)
"""

import customtkinter as ctk

from gui.main_window import MainWindow


def main():
    # CustomTkinter 전역 테마: 다크 모드 + blue 테마 베이스
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
