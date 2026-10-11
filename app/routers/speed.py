from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.detector import VehicleDetector
from app.services.tracker import VehicleTracker
from app.services.speed_engine import SpeedEngine
from app.utils.image import file_to_cv2
import cv2
import base64
import json

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
            # Receive frame data as base64 string or binary
            data = await websocket.receive_text()
            
            # Parse JSON to get frame data
            message = json.loads(data)
            frame_data = message.get("frame")
            
            if not frame_data:
                await websocket.send_json({
                    "error": "No frame data provided"
                })
                continue
            
            # Decode base64 frame
            try:
                frame_bytes = base64.b64decode(frame_data)
                import numpy as np
                nparr = np.frombuffer(frame_bytes, np.uint8)
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
            
            # Encode image to base64
            _, buffer = cv2.imencode(".jpg", img)
            jpg_as_text = base64.b64encode(buffer).decode("utf-8")
            
            # Send response
            await websocket.send_json({
                "speed_mph": speed,
                "frame": jpg_as_text,
                "detection": det
            })
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        await websocket.send_json({
            "error": f"Processing error: {str(e)}"
        })
        await websocket.close()
