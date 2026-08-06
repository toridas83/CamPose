import unittest
from unittest.mock import patch

from core.classifier import PostureResult
from core.service import PostureService


class ServiceSettingsTests(unittest.TestCase):
    def test_camera_change_requests_immediate_restart(self):
        service = PostureService()
        changed = service.settings
        changed["camera_index"] = int(changed.get("camera_index", 0)) + 1
        changed["camera_name"] = "Test Camera"
        with patch("core.service.settings_store.save"), patch.object(service, "restart_camera") as restart:
            self.assertTrue(service.update_settings(changed))
            restart.assert_called_once_with()

    def test_non_camera_setting_does_not_restart_camera(self):
        service = PostureService()
        changed = service.settings
        changed["show_skeleton"] = not changed.get("show_skeleton", True)
        with patch("core.service.settings_store.save"), patch.object(service, "restart_camera") as restart:
            self.assertFalse(service.update_settings(changed))
            restart.assert_not_called()

    def test_session_warning_count_is_cumulative(self):
        service = PostureService()
        service._session = {
            "elapsed_seconds": 0.0,
            "good_seconds": 0.0,
            "warning_count": 0,
            "postures": {},
        }
        result = [PostureResult("거북목", 3, 1.0, "test")]
        with patch("core.service.time.monotonic", side_effect=[1.0, 1.25]):
            service._session_last_tick = 1.0
            service._update_session(result, alert_count=1)
            service._update_session([], alert_count=0)
        self.assertEqual(service._session["warning_count"], 1)


if __name__ == "__main__":
    unittest.main()
