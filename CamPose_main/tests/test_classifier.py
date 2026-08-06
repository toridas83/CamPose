import unittest

from core.classifier import classify_posture
from core.config import DEFAULT_SETTINGS


BASE_FEATURES = {
    "head_forward": 0.20,
    "face_shoulder_ratio": 0.40,
    "ear_shoulder_gap": 0.50,
    "eye_angle": 0.0,
    "shoulder_angle": 0.0,
    "left_ear_shoulder_gap": 0.50,
    "right_ear_shoulder_gap": 0.50,
    "trunk_forward": 0.10,
    "torso_shoulder_ratio": 1.0,
    "torso_lateral_angle": 0.0,
    "shoulder_depth_asymmetry": 0.0,
    "shoulder_width": 0.40,
    "lower_visibility": 0.9,
    "left_knee_gap": 0.80,
    "right_knee_gap": 0.80,
    "knee_height_asymmetry": 0.0,
    "left_ankle_center_cross": 0.0,
    "right_ankle_center_cross": 0.0,
}


class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {
            "features": BASE_FEATURES.copy(),
            "mad": {key: 0.0 for key in BASE_FEATURES},
            "lower_body_available": True,
        }
        self.settings = DEFAULT_SETTINGS.copy()

    def names_and_levels(self, current):
        return {item.name: item.level for item in classify_posture(current, self.baseline, self.settings)}

    def test_neutral_pose_has_no_results(self):
        self.assertEqual(classify_posture(BASE_FEATURES.copy(), self.baseline, self.settings), [])

    def test_forward_head_level_three(self):
        current = BASE_FEATURES.copy()
        current["head_forward"] += 0.16
        self.assertEqual(self.names_and_levels(current)["거북목"], 3)

    def test_shoulder_asymmetry_level_two(self):
        current = BASE_FEATURES.copy()
        current["shoulder_angle"] = 7.0
        self.assertEqual(self.names_and_levels(current)["어깨 비대칭"], 2)

    def test_lateral_trunk_level_three(self):
        current = BASE_FEATURES.copy()
        current["torso_lateral_angle"] = 21.0
        self.assertEqual(self.names_and_levels(current)["몸통 측면 기울임"], 3)

    def test_raised_leg_is_only_checked_when_visible(self):
        current = BASE_FEATURES.copy()
        current["left_knee_gap"] = 0.25
        current["knee_height_asymmetry"] = 0.45
        self.assertGreaterEqual(self.names_and_levels(current)["한쪽 다리 올림"], 2)
        current["lower_visibility"] = 0.2
        self.assertNotIn("한쪽 다리 올림", self.names_and_levels(current))


if __name__ == "__main__":
    unittest.main()

