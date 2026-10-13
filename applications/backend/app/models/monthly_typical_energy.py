import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthlyTypicalEnergy(Base):
    __tablename__ = "monthly_typical_energy"

    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pv_systems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    energy_wh: Mapped[float] = mapped_column(Float, nullable=False)
    low_wh: Mapped[float] = mapped_column(Float, nullable=False)
    high_wh: Mapped[float] = mapped_column(Float, nullable=False)
    n_years: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
