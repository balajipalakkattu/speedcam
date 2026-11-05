import logging

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class VehicleDetector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.target_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        detections = [
            box for box in results.boxes
            if int(box.cls[0]) in self.target_classes
        ]
        if not detections:
            return None

        det = max(detections, key=lambda b: b.xyxy[0][2] - b.xyxy[0][0])
        class_id = int(det.cls[0])
        logger.info(
            "Detected object class_id=%d class_name=%s",
            class_id,
            self.model.names[class_id],
        )
        x1, y1, x2, y2 = det.xyxy[0]
        return (int(x1), int(y1), int(x2), int(y2))
