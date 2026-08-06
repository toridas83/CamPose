from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from core.cameras import CameraDevice, list_camera_devices
from core.config import DEFAULT_SETTINGS
from core.service import PostureService
from gui.alerts import ALERT_STYLES
from gui.constants import (
    CARD_CORNER,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SMALL,
    PAD_X,
    PAD_Y,
)


PRESETS = {
    "조용히": {"sensitivity": "여유", "level_1_seconds": 180, "level_2_seconds": 120, "level_3_seconds": 45, "sound_alert": False},
    "기본": {"sensitivity": "기본", "level_1_seconds": 120, "level_2_seconds": 60, "level_3_seconds": 20, "sound_alert": False},
    "강한 교정": {"sensitivity": "강한 교정", "level_1_seconds": 60, "level_2_seconds": 30, "level_3_seconds": 10, "sound_alert": True},
}

PRESET_DESCRIPTIONS = {
    "조용히": "작은 변화는 허용하고 알림을 늦게 표시합니다.",
    "기본": "일반적인 민감도와 허용 시간을 사용합니다.",
    "강한 교정": "작은 변화부터 빠르게 감지하고 소리도 사용합니다.",
}


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, service: PostureService, show_test_alert, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = service
        self.show_test_alert = show_test_alert
        self.settings = service.settings
        self.posture_switches: dict[str, ctk.CTkSwitch] = {}
        self.camera_devices: list[CameraDevice] = []
        self.camera_by_label: dict[str, CameraDevice] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()
        self._refresh_cameras(show_message=False)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 0))
        ctk.CTkLabel(header, text="설정", font=FONT_HEADING, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            header, text="민감도와 단계별 허용 시간을 사용자에게 맞게 조정합니다.",
            font=FONT_BODY, text_color=COLOR_TEXT_DIM
        ).pack(anchor="w", pady=(4, 0))

    def _build_content(self) -> None:
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=COLOR_ACCENT,
            scrollbar_button_hover_color=COLOR_ACCENT_HOVER
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.grid_columnconfigure(0, weight=1)

        preset = self._make_card(scroll, "빠른 설정", "여러 옵션을 한 번에 변경합니다. 변경값은 아래 항목에 즉시 반영되며, 설정 저장을 눌러야 확정됩니다.")
        preset.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        preset.grid_columnconfigure((0, 1, 2), weight=1)
        for column, name in enumerate(PRESETS):
            box = ctk.CTkFrame(preset, fg_color="transparent")
            box.grid(row=2, column=column, sticky="nsew", padx=6, pady=(4, 8))
            ctk.CTkButton(
                box, text=name, font=FONT_BUTTON, fg_color="transparent",
                border_width=1, border_color=COLOR_ACCENT, text_color=COLOR_ACCENT,
                command=lambda value=name: self._apply_preset(value),
            ).pack(fill="x")
            ctk.CTkLabel(
                box, text=PRESET_DESCRIPTIONS[name], font=FONT_SMALL, text_color=COLOR_TEXT_DIM,
                wraplength=230, justify="left"
            ).pack(anchor="w", pady=(6, 0))
        self.preset_status = ctk.CTkLabel(preset, text="", font=FONT_SMALL, text_color=COLOR_SUCCESS)
        self.preset_status.grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 12))

        alert = self._make_card(scroll, "알림 및 시간 정책", "나쁜 자세를 언제, 어떤 방식으로 알려줄지 설정합니다.")
        alert.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        alert.grid_columnconfigure(1, weight=1)
        self.screen_switch = self._switch_row(
            alert, 0, "화면 알림", "다른 프로그램을 보고 있어도 선택한 팝업이나 테두리 효과를 표시합니다.", self.settings["screen_alert"]
        )
        self.screen_switch.configure(command=self._sync_alert_controls)
        self.sound_switch = self._switch_row(
            alert, 1, "경고음", "화면 알림과 함께 기본 시스템 소리를 재생합니다.", self.settings["sound_alert"]
        )
        selected_alert_style = self.settings.get("alert_display", "팝업 + 테두리")
        if selected_alert_style not in ALERT_STYLES:
            selected_alert_style = "팝업 + 테두리"
        self.alert_display_combo = self._combo_text_row(
            alert, 2, "화면 알림 방식", "현재 사용 중인 모니터에 표시할 시각 효과를 선택합니다.",
            ALERT_STYLES, selected_alert_style, width=240
        )
        self.level1_combo = self._combo_row(alert, 3, "1단계 허용 시간", "가벼운 자세 변화가 이 시간 이상 지속되면 알립니다.", ["30초", "60초", "120초", "180초"], self.settings["level_1_seconds"])
        self.level2_combo = self._combo_row(alert, 4, "2단계 허용 시간", "분명한 자세 변화가 이 시간 이상 지속되면 알립니다.", ["20초", "30초", "60초", "120초"], self.settings["level_2_seconds"])
        self.level3_combo = self._combo_row(alert, 5, "3단계 허용 시간", "심한 자세 변화는 더 짧은 시간 뒤 알립니다.", ["5초", "10초", "20초", "45초"], self.settings["level_3_seconds"])
        self.recovery_combo = self._combo_row(alert, 6, "회복 판정 시간", "좋은 자세를 이 시간 이상 유지해야 이전 알림 상태를 종료합니다. 그 뒤 같은 나쁜 자세가 재발하면 0초부터 다시 셉니다.", ["5초", "10초", "20초", "30초"], self.settings["recovery_seconds"])
        self.static_combo = self._combo_row(alert, 7, "같은 자세 움직임 알림", "좋은 자세라도 너무 오래 움직임이 없을 때 알리는 기능입니다. 현재 감지 로직은 준비 중입니다.", ["15분", "25분", "30분", "45분"], self.settings["static_posture_minutes"], "분")
        self.work_combo = self._combo_row(alert, 8, "연속 작업 휴식 알림", "연속 측정 시간이 지나면 화면에서 벗어나 쉬도록 알립니다. 현재 감지 로직은 준비 중입니다.", ["30분", "50분", "60분", "90분"], self.settings["work_break_minutes"], "분")
        self.alert_test_button = ctk.CTkButton(
            alert, text="화면 알림 테스트", font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_ACCENT, text_color=COLOR_ACCENT,
            command=self._test_notification
        )
        self.alert_test_button.grid(row=11, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 16))
        self._sync_alert_controls()

        detect = self._make_card(scroll, "감지 설정", "카메라와 자세 판정의 기본 동작을 설정합니다.")
        detect.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        detect.grid_columnconfigure(1, weight=1)
        self.sensitivity_combo = self._combo_text_row(
            detect, 0, "감지 민감도", "강한 교정은 작은 변화에도, 여유는 큰 변화에 반응합니다.",
            ["강한 교정", "기본", "여유"], self.settings["sensitivity"]
        )
        self.skeleton_switch = self._switch_row(
            detect, 1, "개발용 캠 스켈레톤", "개발용 캠 영상 위에 관절점과 연결선을 표시합니다.", self.settings["show_skeleton"]
        )
        self.camera_combo = self._combo_text_row(
            detect, 2, "사용할 카메라", "Windows에서 현재 확인되는 카메라 장치만 표시합니다.", ["검색 중…"], "검색 중…", width=330
        )
        ctk.CTkButton(
            detect, text="카메라 목록 새로고침", width=180, font=FONT_SMALL, fg_color="transparent",
            border_width=1, border_color=COLOR_TEXT_DIM, command=self._refresh_cameras
        ).grid(row=5, column=1, sticky="e", padx=16, pady=(0, 14))

        posture = self._make_card(scroll, "자세 종류별 감지 사용", "끄면 해당 자세는 분석 결과와 경고에서 제외됩니다.")
        posture.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        posture.grid_columnconfigure((0, 1), weight=1)
        for index, (name, enabled) in enumerate(self.settings["enabled_postures"].items()):
            switch = ctk.CTkSwitch(
                posture, text=name, font=FONT_BODY, progress_color=COLOR_ACCENT,
                button_color=COLOR_TEXT, button_hover_color=COLOR_TEXT_DIM
            )
            switch.grid(row=index // 2 + 2, column=index % 2, sticky="w", padx=16, pady=8)
            switch.select() if enabled else switch.deselect()
            self.posture_switches[name] = switch

        buttons = ctk.CTkFrame(scroll, fg_color="transparent")
        buttons.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons, text="기본값 복원", font=FONT_BUTTON, fg_color="transparent",
            border_width=1, border_color=COLOR_TEXT_DIM, command=self._restore_defaults
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            buttons, text="설정 저장", font=FONT_BUTTON, fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=self._save
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _make_card(self, parent, title: str, description: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=CARD_CORNER)
        ctk.CTkLabel(card, text=title, font=FONT_BODY_BOLD, text_color=COLOR_ACCENT).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 2)
        )
        ctk.CTkLabel(card, text=description, font=FONT_SMALL, text_color=COLOR_TEXT_DIM).grid(
            row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 8)
        )
        return card

    def _row_label(self, parent, row: int, label: str, description: str) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row + 2, column=0, sticky="w", padx=16, pady=7)
        ctk.CTkLabel(frame, text=label, font=FONT_BODY, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(frame, text=description, font=FONT_SMALL, text_color=COLOR_TEXT_DIM, wraplength=610, justify="left").pack(anchor="w", pady=(2, 0))

    def _switch_row(self, parent, row: int, label: str, description: str, default: bool) -> ctk.CTkSwitch:
        self._row_label(parent, row, label, description)
        switch = ctk.CTkSwitch(parent, text="", width=46, progress_color=COLOR_ACCENT)
        switch.grid(row=row + 2, column=1, sticky="e", padx=16, pady=8)
        switch.select() if default else switch.deselect()
        return switch

    def _combo_row(self, parent, row: int, label: str, description: str, values: list[str], default: int, suffix: str = "초") -> ctk.CTkComboBox:
        return self._combo_text_row(parent, row, label, description, values, f"{default}{suffix}")

    def _combo_text_row(
        self, parent, row: int, label: str, description: str, values: list[str], default: str, width: int = 190
    ) -> ctk.CTkComboBox:
        self._row_label(parent, row, label, description)
        combo = ctk.CTkComboBox(
            parent, values=values, font=FONT_BODY, dropdown_font=FONT_BODY, width=width,
            fg_color=COLOR_CARD, border_color=COLOR_ACCENT, button_color=COLOR_ACCENT
        )
        combo.set(default)
        combo.grid(row=row + 2, column=1, sticky="e", padx=16, pady=8)
        return combo

    def _apply_preset(self, name: str) -> None:
        preset = PRESETS[name]
        self.sensitivity_combo.set(preset["sensitivity"])
        self.level1_combo.set(f"{preset['level_1_seconds']}초")
        self.level2_combo.set(f"{preset['level_2_seconds']}초")
        self.level3_combo.set(f"{preset['level_3_seconds']}초")
        self.sound_switch.select() if preset["sound_alert"] else self.sound_switch.deselect()
        self.preset_status.configure(text=f"'{name}' 값이 아래 옵션에 반영되었습니다. 설정 저장을 눌러 확정하세요.")

    def _restore_defaults(self) -> None:
        self.sensitivity_combo.set("기본")
        self.level1_combo.set("120초")
        self.level2_combo.set("60초")
        self.level3_combo.set("20초")
        self.recovery_combo.set("10초")
        self.static_combo.set("25분")
        self.work_combo.set("50분")
        self.screen_switch.select()
        self.sound_switch.deselect()
        self.alert_display_combo.set("팝업 + 테두리")
        self._sync_alert_controls()
        self.skeleton_switch.select()
        for switch in self.posture_switches.values():
            switch.select()
        self.preset_status.configure(text="기본값이 화면에 반영되었습니다. 설정 저장을 눌러 확정하세요.")

    def _refresh_cameras(self, show_message: bool = True) -> None:
        self.camera_devices = list_camera_devices()
        self.camera_by_label = {device.label: device for device in self.camera_devices}
        if self.camera_devices:
            values = [device.label for device in self.camera_devices]
            self.camera_combo.configure(values=values, state="normal")
            preferred_name = str(self.service.settings.get("camera_name", ""))
            preferred_index = int(self.service.settings.get("camera_index", 0))
            physical_default = next(
                (device.label for device in self.camera_devices if "virtual" not in device.name.lower()),
                values[0],
            )
            selected = next(
                (device.label for device in self.camera_devices if device.name == preferred_name),
                next(
                    (device.label for device in self.camera_devices if device.index == preferred_index and "virtual" not in device.name.lower()),
                    physical_default,
                ),
            )
            self.camera_combo.set(selected)
            if show_message:
                messagebox.showinfo("카메라 검색", f"사용 가능한 카메라 {len(values)}개를 찾았습니다.")
        else:
            self.camera_combo.configure(values=["카메라를 찾지 못했습니다"], state="disabled")
            self.camera_combo.set("카메라를 찾지 못했습니다")
            if show_message:
                messagebox.showwarning("카메라 검색", "Windows에서 사용할 수 있는 카메라를 찾지 못했습니다.")

    def _test_notification(self) -> None:
        if not self.screen_switch.get():
            messagebox.showinfo("화면 알림 꺼짐", "화면 알림을 켠 뒤 테스트해 주세요.")
            return
        self.show_test_alert(self.alert_display_combo.get(), bool(self.sound_switch.get()))
        self.preset_status.configure(text="선택한 방식으로 테스트 알림을 표시했습니다.")

    def _sync_alert_controls(self) -> None:
        enabled = bool(self.screen_switch.get())
        self.alert_display_combo.configure(state="normal" if enabled else "disabled")
        self.alert_test_button.configure(state="normal" if enabled else "disabled")

    @staticmethod
    def _number(value: str) -> int:
        digits = "".join(character for character in value if character.isdigit())
        return int(digits or 0)

    def _save(self) -> None:
        settings = self.service.settings
        selected_device = self.camera_by_label.get(self.camera_combo.get())
        settings.update({
            "screen_alert": bool(self.screen_switch.get()),
            "sound_alert": bool(self.sound_switch.get()),
            "alert_display": self.alert_display_combo.get(),
            "show_skeleton": bool(self.skeleton_switch.get()),
            "sensitivity": self.sensitivity_combo.get(),
            "level_1_seconds": self._number(self.level1_combo.get()),
            "level_2_seconds": self._number(self.level2_combo.get()),
            "level_3_seconds": self._number(self.level3_combo.get()),
            "recovery_seconds": self._number(self.recovery_combo.get()),
            "static_posture_minutes": self._number(self.static_combo.get()),
            "work_break_minutes": self._number(self.work_combo.get()),
            "enabled_postures": {name: bool(switch.get()) for name, switch in self.posture_switches.items()},
        })
        if selected_device:
            settings["camera_index"] = selected_device.index
            settings["camera_name"] = selected_device.name
        camera_changed = self.service.update_settings(settings)
        self.preset_status.configure(text="설정이 저장되었습니다.")
        message = "설정을 저장했습니다."
        if camera_changed:
            message += "\n선택한 카메라를 즉시 다시 연결합니다."
        messagebox.showinfo("설정 저장", message)
