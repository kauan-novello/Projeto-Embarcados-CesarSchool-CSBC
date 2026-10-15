from datetime import datetime

from pydantic import BaseModel


class PlantHourlyOut(BaseModel):
    hour_start: datetime
    energy_wh: float
    radiation_wh_m2: float
    air_temp_c: float
    humidity_pct: float
    humidity_estimated: bool
    pressure_hpa: float
    wind_speed_m_s: float

    model_config = {"from_attributes": True}
