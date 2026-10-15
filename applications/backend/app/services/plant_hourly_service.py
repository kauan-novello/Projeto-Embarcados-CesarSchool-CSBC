from sqlalchemy.orm import Session

from app.models.plant_hourly import PlantHourly
from app.models.pv_system import PVSystem


def list_plant_hourly(db: Session, *, system: PVSystem) -> list[PlantHourly]:
    return (
        db.query(PlantHourly)
        .filter(PlantHourly.system_id == system.id)
        .order_by(PlantHourly.hour_start)
        .all()
    )
