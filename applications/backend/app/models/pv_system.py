import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db.base import Base
from app.models.device import Device
from app.models.sensor_reading import SensorReading

if TYPE_CHECKING:
    from app.models.user import User


class InverterType(str, enum.Enum):
    ON_GRID = "on_grid"
    OFF_GRID = "off_grid"


class SystemStatus(str, enum.Enum):
    AWAITING_PAIRING = "awaiting_pairing"
    ONLINE_UNTRAINED = "online_untrained"
    TRAINING = "training"
    MODEL_ACTIVE = "model_active"


class PVSystem(Base):
    __tablename__ = "pv_systems"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    installed_power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    inverter_type: Mapped[InverterType] = mapped_column(Enum(InverterType), nullable=False)
    status: Mapped[SystemStatus] = mapped_column(
        Enum(SystemStatus), nullable=False, default=SystemStatus.AWAITING_PAIRING
    )
    training_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    weather_station_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    device_id: Mapped[str | None] = column_property(
        select(Device.id).where(Device.system_id == id).correlate_except(Device).scalar_subquery()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_reading_at: Mapped[datetime | None] = column_property(
        select(func.max(SensorReading.recorded_at))
        .where(SensorReading.system_id == id)
        .correlate_except(SensorReading)
        .scalar_subquery()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="systems")
