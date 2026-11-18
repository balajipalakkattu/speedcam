import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.detector import VehicleDetector, logger


class VehicleDetectorTests(unittest.TestCase):
    def test_detects_class_outside_previous_target_list(self):
        detection = SimpleNamespace(
            cls=[16],
            xyxy=[[10, 20, 50, 80]],
            conf=[0.93],
        )
        detector = VehicleDetector.__new__(VehicleDetector)
        detector.model = Mock(
            names={16: "dog"},
            return_value=[SimpleNamespace(boxes=[detection])],
        )

        with self.assertLogs(logger, level="INFO") as captured:
            result = detector.detect(object())

        self.assertEqual(result.bbox, (10, 20, 50, 80))
        self.assertEqual(result.class_name, "dog")
        self.assertEqual(result.confidence, 0.93)
        self.assertIn("class_id=16 class_name=dog", captured.output[0])

    def test_detects_person(self):
        person = SimpleNamespace(
            cls=[0],
            xyxy=[[10, 20, 50, 80]],
            conf=[0.87],
        )
        detector = VehicleDetector.__new__(VehicleDetector)
        detector.model = Mock(
            names={0: "person"},
            return_value=[SimpleNamespace(boxes=[person])],
        )

        result = detector.detect(object())

        self.assertEqual(result.class_name, "person")
        self.assertEqual(result.bbox, (10, 20, 50, 80))


if __name__ == "__main__":
    unittest.main()
