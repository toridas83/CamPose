from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraDevice:
    index: int
    name: str

    @property
    def label(self) -> str:
        return f"{self.name}  (장치 {self.index})"


def list_camera_devices() -> list[CameraDevice]:
    """Windows DirectShow 입력 장치를 실제 장치명과 함께 반환한다."""
    try:
        from pygrabber.dshow_graph import FilterGraph

        names = FilterGraph().get_input_devices()
        return [CameraDevice(index, str(name)) for index, name in enumerate(names)]
    except Exception:
        # pygrabber/DirectShow를 사용할 수 없는 환경에서도 기존 설정은 쓸 수 있다.
        return []


def resolve_camera_index(preferred_name: str, fallback_index: int) -> int:
    devices = list_camera_devices()
    if preferred_name:
        for device in devices:
            if device.name == preferred_name:
                return device.index
    fallback = next((device for device in devices if device.index == fallback_index), None)
    if fallback and "virtual" not in fallback.name.lower():
        return fallback.index
    physical = next((device for device in devices if "virtual" not in device.name.lower()), None)
    if physical:
        return physical.index
    return fallback_index
