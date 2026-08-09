from __future__ import annotations

import ctypes
import tkinter as tk
from ctypes import wintypes

import customtkinter as ctk

from core.notifications import AlertSound
from gui.constants import (
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_ORANGE,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
)


ALERT_STYLES = ["팝업 + 테두리", "우측 하단 팝업", "화면 테두리 강조"]
LEVEL_COLORS = {1: COLOR_WARNING, 2: COLOR_ORANGE, 3: COLOR_DANGER}


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def active_monitor_work_area(root) -> tuple[int, int, int, int]:
    """현재 사용 중인 창이 위치한 모니터의 작업 영역을 반환한다."""
    try:
        user32 = ctypes.windll.user32
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
        foreground = user32.GetForegroundWindow()
        monitor = user32.MonitorFromWindow(foreground, 2)  # MONITOR_DEFAULTTONEAREST
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            rect = info.rcWork
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class AlertPresenter:
    def __init__(self, root):
        self.root = root
        self._popup = None
        self._glow = None

    def show(self, title: str, message: str, level: int, style: str, sound: bool) -> None:
        if sound:
            AlertSound.play()
        if style not in ALERT_STYLES:
            style = "팝업 + 테두리"
        if style in ("우측 하단 팝업", "팝업 + 테두리"):
            self._show_popup(title, message, level)
        if style in ("화면 테두리 강조", "팝업 + 테두리"):
            self._show_edge_glow(level)

    def close(self) -> None:
        self._destroy_widget("_popup")
        self._destroy_widget("_glow")

    def _show_popup(self, title: str, message: str, level: int) -> None:
        self._destroy_widget("_popup")
        color = LEVEL_COLORS.get(level, COLOR_WARNING)
        left, top, right, bottom = active_monitor_work_area(self.root)
        width, height, margin = 410, 150, 18

        popup = ctk.CTkToplevel(self.root)
        self._popup = popup
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color=color)
        popup.geometry(f"{width}x{height}+{right - width - margin}+{bottom - height - margin}")
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        body = ctk.CTkFrame(popup, fg_color=COLOR_CARD, corner_radius=10)
        body.grid(row=0, column=0, sticky="nsew", padx=(8, 2), pady=2)
        body.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(body, text=title, font=FONT_BODY_BOLD, text_color=color, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=(16, 4), pady=(14, 4)
        )
        ctk.CTkButton(
            body, text="×", width=28, height=28, fg_color="transparent", hover_color="#39425e",
            font=("맑은 고딕", 18), command=lambda: self._destroy_widget("_popup")
        ).grid(row=0, column=1, padx=(0, 8), pady=(8, 0))
        ctk.CTkLabel(
            body, text=message, font=FONT_BODY, text_color=COLOR_TEXT, anchor="w",
            justify="left", wraplength=350
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 4))
        ctk.CTkLabel(
            body, text="잠시 후 자동으로 닫힙니다.", font=FONT_SMALL, text_color=COLOR_TEXT_DIM, anchor="w"
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 12))
        popup.deiconify()
        popup.lift()
        popup.after(8000, lambda: self._destroy_widget("_popup", popup))

    def _show_edge_glow(self, level: int) -> None:
        self._destroy_widget("_glow")
        color = LEVEL_COLORS.get(level, COLOR_WARNING)
        left, top, right, bottom = active_monitor_work_area(self.root)
        width, height = right - left, bottom - top
        transparent = "#010203"

        glow = tk.Toplevel(self.root)
        self._glow = glow
        glow.withdraw()
        glow.overrideredirect(True)
        glow.attributes("-topmost", True)
        glow.configure(bg=transparent)
        glow.geometry(f"{width}x{height}+{left}+{top}")
        try:
            glow.wm_attributes("-transparentcolor", transparent)
        except tk.TclError:
            pass
        canvas = tk.Canvas(glow, bg=transparent, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_rectangle(7, 7, width - 7, height - 7, outline=color, width=14)
        glow.update_idletasks()
        self._make_click_through(glow)
        glow.deiconify()
        glow.lift()
        self._pulse(glow, 0)

    def _pulse(self, glow, step: int) -> None:
        if self._glow is not glow or not glow.winfo_exists():
            return
        if step >= 10:
            self._destroy_widget("_glow", glow)
            return
        try:
            glow.attributes("-alpha", 0.82 if step % 2 == 0 else 0.28)
        except tk.TclError:
            pass
        glow.after(220, lambda: self._pulse(glow, step + 1))

    @staticmethod
    def _make_click_through(window) -> None:
        try:
            user32 = ctypes.windll.user32
            user32.GetParent.argtypes = [wintypes.HWND]
            user32.GetParent.restype = wintypes.HWND
            user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
            hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
            get_style = user32.GetWindowLongW
            set_style = user32.SetWindowLongW
            ex_style = get_style(hwnd, -20)
            set_style(hwnd, -20, ex_style | 0x00080000 | 0x00000020 | 0x08000000)
        except Exception:
            pass

    def _destroy_widget(self, attribute: str, expected=None) -> None:
        widget = getattr(self, attribute, None)
        if expected is not None and widget is not expected:
            return
        setattr(self, attribute, None)
        if widget is not None:
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except tk.TclError:
                pass
