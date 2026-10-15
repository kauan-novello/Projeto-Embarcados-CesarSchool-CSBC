from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReadingIn(BaseModel):
    timestamp: datetime | None = None
    power_w: float | None = None
    panel_temp_c: float | None = None
    ambient_temp_c: float | None = None
    ambient_humidity_pct: float | None = None
    irradiance: float
    pressure_hpa: float | None = None
    particulate_pct: float | None = None
    pairing_mode: bool = False


class ReadingOut(BaseModel):
    id: UUID
    recorded_at: datetime
    power_w: float | None = None
    panel_temp_c: float | None = None
    ambient_temp_c: float | None = None
    ambient_humidity_pct: float | None = None
    irradiance: float
    pressure_hpa: float | None = None
    particulate_pct: float | None = None

    model_config = {"from_attributes": True}


class OverheatAlertOut(BaseModel):
    id: UUID
    panel_temp_c: float | None = None
    threshold_c: float
    email_to: str | None
    triggered_at: datetime

    model_config = {"from_attributes": True}
