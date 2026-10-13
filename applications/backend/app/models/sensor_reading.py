import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (Index("ix_sensor_readings_system_id_recorded_at", "system_id", "recorded_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pv_systems.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    power_w: Mapped[float | None] = mapped_column(Float, nullable=True)
    panel_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    irradiance: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    particulate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
