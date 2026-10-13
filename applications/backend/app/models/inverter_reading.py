import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InverterReading(Base):
    __tablename__ = "inverter_readings"
    __table_args__ = (
        UniqueConstraint(
            "system_id", "recorded_at", "source", name="uq_inverter_readings_system_recorded_source"
        ),
        CheckConstraint("source IN ('cloud', 'modbus')", name="ck_inverter_readings_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pv_systems.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    power_w: Mapped[float | None] = mapped_column(Float, nullable=True)
    dc_power_w: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_yield_wh: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_yield_wh: Mapped[float | None] = mapped_column(Float, nullable=True)
    internal_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_frequency_hz: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mppt1_voltage_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt1_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt2_voltage_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt2_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt3_voltage_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt3_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt4_voltage_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    mppt4_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
