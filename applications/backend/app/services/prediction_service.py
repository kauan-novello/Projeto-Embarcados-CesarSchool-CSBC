from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.hourly_prediction import OBSERVED, HourlyPrediction
from app.models.inverter_reading import InverterReading
from app.models.pv_system import PVSystem
from app.schemas.hourly_prediction import HourlyComparisonOut

PLANT_TZ = ZoneInfo("America/Recife")
HOUR = timedelta(hours=1)
EDGE_TOLERANCE = timedelta(minutes=10)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _local_date(moment: datetime):
    return moment.astimezone(PLANT_TZ).date()


def real_hourly_energy(
    db: Session, *, system: PVSystem, hours: list[datetime]
) -> dict[datetime, float | None]:
    if not hours:
        return {}
    rows = (
        db.query(InverterReading.recorded_at, InverterReading.daily_yield_wh)
        .filter(
            InverterReading.system_id == system.id,
            InverterReading.daily_yield_wh.is_not(None),
            InverterReading.recorded_at > min(hours) - HOUR,
            InverterReading.recorded_at <= max(hours) + HOUR,
        )
        .order_by(InverterReading.recorded_at)
        .all()
    )
    readings = [(_as_utc(at), float(value)) for at, value in rows if value is not None]

    def counter_at(edge: datetime, day) -> float | None:
        if edge.astimezone(PLANT_TZ).time() == datetime.min.time() and _local_date(edge) == day:
            return 0.0
        candidates = [(at, v) for at, v in readings if at <= edge and _local_date(at) == day]
        if not candidates or edge - candidates[-1][0] > EDGE_TOLERANCE:
            return None
        return candidates[-1][1]

    energy: dict[datetime, float | None] = {}
    for start in hours:
        day = _local_date(start)
        before, after = counter_at(start, day), counter_at(start + HOUR, day)
        energy[start] = (
            after - before if before is not None and after is not None and after >= before else None
        )
    return energy


def list_hourly_comparison(
    db: Session, *, system: PVSystem, start: datetime, end: datetime, kind: str = OBSERVED
) -> list[HourlyComparisonOut]:
    predictions = (
        db.query(HourlyPrediction)
        .filter(
            HourlyPrediction.system_id == system.id,
            HourlyPrediction.kind == kind,
            HourlyPrediction.hour_start >= start,
            HourlyPrediction.hour_start < end,
        )
        .order_by(HourlyPrediction.hour_start)
        .all()
    )
    real = real_hourly_energy(db, system=system, hours=[_as_utc(p.hour_start) for p in predictions])
    return [
        HourlyComparisonOut(
            hour_start=_as_utc(p.hour_start),
            kind=p.kind,
            predicted_energy_wh=p.predicted_energy_wh,
            real_energy_wh=real.get(_as_utc(p.hour_start)),
            model_version=p.model_version,
        )
        for p in predictions
    ]
