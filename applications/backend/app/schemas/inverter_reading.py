from datetime import datetime

from pydantic import BaseModel


class InverterReadingOut(BaseModel):
    recorded_at: datetime
    source: str
    power_w: float | None = None
    dc_power_w: float | None = None
    daily_yield_wh: float | None = None
    total_yield_wh: float | None = None

    model_config = {"from_attributes": True}
