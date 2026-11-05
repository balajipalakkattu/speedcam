from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.detector import VehicleDetector
from app.services.tracker import VehicleTracker
from app.services.speed_engine import SpeedEngine
from app.utils.image import file_to_cv2
import cv2
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

    return {"speed_mph": speed}


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
            
            # Only send the speed result; the client does not need a processed image.
            await websocket.send_json({
                "speed_mph": speed
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
