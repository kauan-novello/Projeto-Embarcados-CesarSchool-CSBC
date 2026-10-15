from datetime import datetime

from pydantic import BaseModel


class HourlyComparisonOut(BaseModel):
    hour_start: datetime
    kind: str
    predicted_energy_wh: float
    real_energy_wh: float | None
    model_version: str
