from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import speed

app = FastAPI(title="SpeedCam API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(speed.router)
