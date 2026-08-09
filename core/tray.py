from __future__ import annotations

from collections.abc import Callable

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem


def _create_icon_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), (16, 20, 38, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((7, 7, 57, 57), fill=(0, 184, 148, 255))
    draw.arc((20, 17, 48, 48), 70, 290, fill=(255, 255, 255, 255), width=7)
    return image


class TrayController:
    def __init__(self, on_open: Callable[[], None], on_exit: Callable[[], None]):
        self.icon = Icon(
            "CamPose",
            _create_icon_image(),
            "CamPose 자세 모니터링",
            menu=Menu(
                MenuItem("대시보드 열기", lambda _icon, _item: on_open(), default=True),
                MenuItem("완전히 종료", lambda _icon, _item: on_exit()),
            ),
        )

    def start(self) -> None:
        self.icon.run_detached()

    def stop(self) -> None:
        self.icon.stop()

