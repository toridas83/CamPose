import unittest
from unittest.mock import patch

from core.cameras import CameraDevice, resolve_camera_index


class CameraTests(unittest.TestCase):
    @patch("core.cameras.list_camera_devices")
    def test_prefers_named_device(self, mocked):
        mocked.return_value = [CameraDevice(0, "Virtual Camera"), CameraDevice(1, "USB Webcam")]
        self.assertEqual(resolve_camera_index("USB Webcam", 0), 1)

    @patch("core.cameras.list_camera_devices")
    def test_avoids_virtual_camera_for_legacy_default(self, mocked):
        mocked.return_value = [CameraDevice(0, "Virtual Camera"), CameraDevice(1, "Built-in Camera")]
        self.assertEqual(resolve_camera_index("", 0), 1)


if __name__ == "__main__":
    unittest.main()

