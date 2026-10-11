from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.detector import VehicleDetector
from app.services.tracker import VehicleTracker
from app.services.speed_engine import SpeedEngine
from app.utils.image import file_to_cv2
import cv2
import base64
import json
import numpy as np

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


@router.websocket("/ws/estimate")
async def websocket_estimate_speed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive raw binary image data
            data = await websocket.receive_bytes()
            
            if not data:
                continue
            
            try:
                # Decode image from binary data
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    await websocket.send_json({
                        "error": "Failed to decode frame"
                    })
                    continue
            except Exception as e:
                await websocket.send_json({
                    "error": f"Frame decoding error: {str(e)}"
                })
                continue
            
            # Process frame
            det = detector.detect(img)
            track = tracker.update(det)
            speed = engine.update(track)
            
            # Draw bounding box if available
            if det:
                x1, y1, x2, y2 = det
                cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
            
            # Encode image to base64 for response
            _, buffer = cv2.imencode(".jpg", img)
            jpg_as_text = base64.b64encode(buffer).decode("utf-8")
            
            # Send response as JSON
            await websocket.send_json({
                "speed_mph": speed,
                "frame": jpg_as_text,
                "detection": det if det else None
            })
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        try:
            await websocket.send_json({
                "error": f"Processing error: {str(e)}"
            })
        except:
            pass
        await websocket.close()
