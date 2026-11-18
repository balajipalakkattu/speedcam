import unittest
from unittest.mock import patch

from starlette.websockets import WebSocketDisconnect

from app.routers import speed as speed_router


class FakeFrame:
    async def read(self):
        return b"frame"


class FakeWebSocket:
    def __init__(self):
        self.messages = []
        self.frame_received = False
        self.client = "test-client"

    async def accept(self):
        pass

    async def receive_bytes(self):
        if self.frame_received:
            raise WebSocketDisconnect(code=1000)
        self.frame_received = True
        return b"frame"

    async def send_json(self, message):
        self.messages.append(message)

    async def close(self):
        pass


class SpeedEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_endpoint_returns_detection_details(self):
        detection = speed_router.Detection(
            class_id=0,
            class_name="person",
            confidence=0.87,
            bbox=(10, 20, 50, 80),
        )
        with patch.object(speed_router, "file_to_cv2", return_value=object()), \
                patch.object(speed_router.detector, "detect", return_value=detection), \
                patch.object(
                    speed_router.tracker,
                    "update",
                    return_value=(30, 50),
                ) as update_tracker, \
                patch.object(speed_router.engine, "update", return_value=2.5):
            result = await speed_router.estimate_speed(FakeFrame())

        update_tracker.assert_called_once_with(detection.bbox)
        self.assertEqual(
            result,
            {
                "speed_mph": 2.5,
                "detected": True,
                "detection": {
                    "class_id": 0,
                    "class_name": "person",
                    "confidence": 0.87,
                    "bbox": (10, 20, 50, 80),
                },
            },
        )

    async def test_http_endpoint_returns_speed_without_frame(self):
        with self.assertLogs(speed_router.logger, level="INFO") as captured:
            with (
                patch.object(speed_router, "file_to_cv2", return_value=object()),
                patch.object(speed_router.detector, "detect", return_value=None),
                patch.object(speed_router.tracker, "update", return_value=None),
                patch.object(speed_router.engine, "update", return_value=42.5),
            ):
                result = await speed_router.estimate_speed(FakeFrame())

        self.assertEqual(
            result,
            {"speed_mph": 42.5, "detected": False, "detection": None},
        )
        self.assertIn("HTTP speed estimate completed", captured.output[0])
        self.assertIn("speed_mph=42.5", captured.output[0])

    async def test_websocket_returns_speed_and_detection_status_without_frame(self):
        websocket = FakeWebSocket()
        with self.assertLogs(speed_router.logger, level="INFO") as captured:
            with (
                patch.object(speed_router.cv2, "imdecode", return_value=object()),
                patch.object(speed_router.detector, "detect", return_value=None),
                patch.object(speed_router.tracker, "update", return_value=None),
                patch.object(speed_router.engine, "update", return_value=42.5),
            ):
                await speed_router.websocket_estimate_speed(websocket)

        self.assertEqual(len(websocket.messages), 1)
        self.assertEqual(websocket.messages[0]["speed_mph"], 42.5)
        self.assertFalse(websocket.messages[0]["detected"])
        self.assertIsNone(websocket.messages[0]["detection"])
        self.assertIsInstance(websocket.messages[0]["processing_ms"], float)
        self.assertTrue(any("WebSocket connected" in line for line in captured.output))
        self.assertTrue(any(
            "WebSocket estimate response sent" in line and "speed_mph=42.5" in line
            for line in captured.output
        ))

    async def test_websocket_returns_detection_details(self):
        websocket = FakeWebSocket()
        detection = speed_router.Detection(
            class_id=0,
            class_name="person",
            confidence=0.87,
            bbox=(10, 20, 50, 80),
        )
        with self.assertLogs(speed_router.logger, level="INFO"):
            with (
                patch.object(speed_router.cv2, "imdecode", return_value=object()),
                patch.object(speed_router.detector, "detect", return_value=detection),
                patch.object(
                    speed_router.tracker,
                    "update",
                    return_value=(30, 50),
                ) as update_tracker,
                patch.object(speed_router.engine, "update", return_value=2.5),
            ):
                await speed_router.websocket_estimate_speed(websocket)

        update_tracker.assert_called_once_with(detection.bbox)
        self.assertEqual(len(websocket.messages), 1)
        response = websocket.messages[0]
        self.assertEqual(response["speed_mph"], 2.5)
        self.assertTrue(response["detected"])
        self.assertEqual(
            response["detection"],
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.87,
                "bbox": (10, 20, 50, 80),
            },
        )
        self.assertIsInstance(response["processing_ms"], float)


if __name__ == "__main__":
    unittest.main()
