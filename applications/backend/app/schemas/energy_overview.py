from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

HealthState = Literal["normal", "attention", "maintenance"]
ExpectedKind = Literal["observed", "forecast", "typical"]


class HealthOut(BaseModel):
    state: HealthState
    performance_pct: int
    real_energy_wh: float
    expected_energy_wh: float
    days: int


class MonthOutlookOut(BaseModel):
    month_start: date
    generated_wh: float
    projected_wh: float | None
    typical_wh: float | None
    typical_low_wh: float | None
    typical_high_wh: float | None


class EnergyOverviewOut(BaseModel):
    health: HealthOut | None
    generated_today_wh: float | None
    remaining_today_wh: float | None
    tomorrow_wh: float | None
    month: MonthOutlookOut


class EnergyBucketOut(BaseModel):
    start: datetime
    real_energy_wh: float | None
    expected_energy_wh: float | None
    expected_kind: ExpectedKind | None
