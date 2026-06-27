import cv2
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        detections = [
            box for box in results.boxes
            if int(box.cls[0]) in self.vehicle_classes
        ]
        if not detections:
            return None

        det = max(detections, key=lambda b: b.xyxy[0][2] - b.xyxy[0][0])
        x1, y1, x2, y2 = det.xyxy[0]
        return (int(x1), int(y1), int(x2), int(y2))
