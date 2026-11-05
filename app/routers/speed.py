import logging
import time

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.detector import VehicleDetector
from app.services.tracker import VehicleTracker
from app.services.speed_engine import SpeedEngine
from app.utils.image import file_to_cv2
import cv2
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speed", tags=["speed"])

detector = VehicleDetector()
tracker = VehicleTracker()
engine = SpeedEngine()

@router.post("/estimate")
async def estimate_speed(frame: UploadFile = File(...)):
    frame_data = await frame.read()
    img = file_to_cv2(frame_data)

    det = detector.detect(img)
    track = tracker.update(det)
    speed = engine.update(track)

    response = {"speed_mph": speed}
    logger.info(
        "HTTP speed estimate completed frame_bytes=%d detected=%s speed_mph=%s",
        len(frame_data),
        det is not None,
        speed,
    )
    return response


@router.websocket("/ws/estimate")
async def websocket_estimate_speed(websocket: WebSocket):
    await websocket.accept()
    client = websocket.client
    logger.info("WebSocket connected client=%s", client)
    frame_count = 0
    try:
        while True:
            # Receive raw binary image data
            data = await websocket.receive_bytes()
            
            if not data:
                continue

            frame_count += 1
            started_at = time.perf_counter()
            
            try:
                # Decode image from binary data
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    logger.warning(
                        "WebSocket frame decode failed client=%s frame=%d frame_bytes=%d",
                        client,
                        frame_count,
                        len(data),
                    )
                    await websocket.send_json({
                        "error": "Failed to decode frame"
                    })
                    continue
            except Exception as e:
                logger.exception(
                    "WebSocket frame decoding error client=%s frame=%d",
                    client,
                    frame_count,
                )
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
                "speed_mph": speed,
                "detected": det is not None
            })
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "WebSocket estimate response sent client=%s frame=%d frame_bytes=%d "
                "detected=%s speed_mph=%s processing_ms=%.1f",
                client,
                frame_count,
                len(data),
                det is not None,
                speed,
                elapsed_ms,
            )
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected client=%s frames_processed=%d", client, frame_count)
    except Exception as e:
        logger.exception(
            "WebSocket processing failed client=%s frames_processed=%d",
            client,
            frame_count,
        )
        try:
            await websocket.send_json({
                "error": f"Processing error: {str(e)}"
            })
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected while reporting error client=%s", client)
        finally:
            await websocket.close()
