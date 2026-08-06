import unittest
from unittest.mock import patch

from core.classifier import PostureResult
from core.timers import PostureTimerManager


class TimerTests(unittest.TestCase):
    def test_same_posture_realerts_only_after_recovery_time(self):
        bad = [PostureResult("거북목", 3, 1.0, "test")]
        settings = {
            "level_3_seconds": 0.5,
            "recovery_seconds": 0.5,
        }
        timeline = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        with patch("core.timers.time.monotonic", side_effect=timeline):
            timers = PostureTimerManager()
            self.assertEqual(timers.update(bad, settings), [])
            self.assertEqual(len(timers.update(bad, settings)), 1)

            # 회복 시간이 부족하면 기존 알림 상태를 유지하므로 다시 알리지 않는다.
            self.assertEqual(timers.update([], settings), [])
            self.assertEqual(timers.update(bad, settings), [])

            # 좋은 자세가 회복 시간을 모두 채우면 기존 상태가 종료된다.
            self.assertEqual(timers.update([], settings), [])
            self.assertEqual(timers.update([], settings), [])

            # 같은 자세가 재발하면 0초부터 다시 세고 임계시간 뒤 재알림한다.
            self.assertEqual(timers.update(bad, settings), [])
            second_alert = timers.update(bad, settings)
            self.assertEqual(len(second_alert), 1)
            self.assertEqual(second_alert[0]["name"], "거북목")


if __name__ == "__main__":
    unittest.main()

