import logging
from dataclasses import dataclass

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]


class VehicleDetector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        detections = list(results.boxes)
        if not detections:
            return None

        det = max(detections, key=lambda b: b.xyxy[0][2] - b.xyxy[0][0])
        class_id = int(det.cls[0])
        class_name = self.model.names[class_id]
        logger.info(
            "Detected object class_id=%d class_name=%s",
            class_id,
            class_name,
        )
        x1, y1, x2, y2 = det.xyxy[0]
        return Detection(
            class_id=class_id,
            class_name=class_name,
            confidence=float(det.conf[0]),
            bbox=(int(x1), int(y1), int(x2), int(y2)),
        )
