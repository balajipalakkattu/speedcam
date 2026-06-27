from fastapi import APIRouter, UploadFile, File
from app.services.detector import VehicleDetector
from app.services.tracker import VehicleTracker
from app.services.speed_engine import SpeedEngine
from app.utils.image import file_to_cv2
import cv2
import base64

router = APIRouter(prefix="/speed", tags=["speed"])

detector = VehicleDetector()
tracker = VehicleTracker()
engine = SpeedEngine()

@router.post("/estimate")
async def estimate_speed(frame: UploadFile = File(...)):
    img = file_to_cv2(await frame.read())

    det = detector.detect(img)
    track = tracker.update(det)
    speed = engine.update(track)

    # Draw bounding box if available
    if det:
        x1, y1, x2, y2 = det
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

    # Encode image to base64
    _, buffer = cv2.imencode(".jpg", img)
    jpg_as_text = base64.b64encode(buffer).decode("utf-8")

    return {
        "speed_mph": speed,
        "frame": jpg_as_text
    }
