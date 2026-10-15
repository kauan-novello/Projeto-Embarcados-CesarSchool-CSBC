from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.pv_system import InverterType, SystemStatus


class PVSystemCreate(BaseModel):
    name: str
    location: str
    installed_power_kw: float
    inverter_type: InverterType
    photo_url: str | None = None


class PVSystemUpdate(BaseModel):
    name: str
    location: str
    installed_power_kw: float
    inverter_type: InverterType
    photo_url: str | None = None


class PVSystemOut(BaseModel):
    id: UUID
    name: str
    location: str
    installed_power_kw: float
    inverter_type: InverterType
    status: SystemStatus
    training_started_at: datetime
    photo_url: str | None
    device_id: str | None
    weather_station_id: str | None
    last_reading_at: datetime | None

    model_config = {"from_attributes": True}
