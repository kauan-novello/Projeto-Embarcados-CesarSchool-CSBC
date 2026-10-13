import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlantHourly(Base):
    __tablename__ = "plant_hourly"

    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pv_systems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    hour_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    energy_wh: Mapped[float] = mapped_column(Float, nullable=False)
    energy_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    radiation_wh_m2: Mapped[float] = mapped_column(Float, nullable=False)
    air_temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pressure_hpa: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_m_s: Mapped[float] = mapped_column(Float, nullable=False)
