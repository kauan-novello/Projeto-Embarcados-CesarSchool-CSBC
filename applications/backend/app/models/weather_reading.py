from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    station_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    hour_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    radiation_wh_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_m_s: Mapped[float | None] = mapped_column(Float, nullable=True)
