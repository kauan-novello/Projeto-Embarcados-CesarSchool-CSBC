from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, devices, systems
from app.services.mqtt_ingest import start_mqtt_ingest, stop_mqtt_ingest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    mqtt_client = start_mqtt_ingest()
    try:
        yield
    finally:
        stop_mqtt_ingest(mqtt_client)


app = FastAPI(title="SolarSense API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(systems.router)
app.include_router(devices.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
