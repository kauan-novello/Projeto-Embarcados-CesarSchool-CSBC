from sqlalchemy.orm import Session

from app.models.inverter_reading import InverterReading
from app.models.pv_system import PVSystem
from app.schemas.inverter_reading import InverterReadingOut


def get_latest_inverter_reading(db: Session, *, system: PVSystem) -> InverterReadingOut | None:
    reading = (
        db.query(InverterReading)
        .filter(InverterReading.system_id == system.id)
        .order_by(InverterReading.recorded_at.desc())
        .first()
    )
    return InverterReadingOut.model_validate(reading) if reading else None
