import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OverheatAlert(Base):
    __tablename__ = "overheat_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pv_systems.id", ondelete="CASCADE"), nullable=False
    )
    panel_temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_c: Mapped[float] = mapped_column(Float, nullable=False)
    email_to: Mapped[str | None] = mapped_column(String, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
