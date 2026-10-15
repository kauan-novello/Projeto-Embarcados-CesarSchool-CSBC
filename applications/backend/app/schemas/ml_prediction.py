from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MLPredictionOut(BaseModel):
    id: UUID
    predicted_efficiency_pct: float
    predicted_generation_kwh_next_day: float
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}
