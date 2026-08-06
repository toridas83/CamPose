"""CamPose 데스크톱 애플리케이션 진입점."""

import signal
from threading import Event

import customtkinter as ctk

from gui.main_window import MainWindow


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    app = MainWindow()
    stop_requested = Event()

    def request_stop(_signum=None, _frame=None) -> None:
        stop_requested.set()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_stop)

    def poll_terminal_stop() -> None:
        if stop_requested.is_set():
            app.request_safe_exit()
            return
        app.after(100, poll_terminal_stop)

    app.after(100, poll_terminal_stop)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        request_stop()
        app.request_safe_exit()
    finally:
        app.request_safe_exit()


if __name__ == "__main__":
    main()
