import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_overheat_alert_email
from app.models.overheat_alert import OverheatAlert
from app.models.pv_system import PVSystem, SystemStatus
from app.models.sensor_reading import SensorReading
from app.schemas.reading import ReadingIn

logger = logging.getLogger(__name__)


def ingest_reading(db: Session, *, system: PVSystem, payload: ReadingIn) -> SensorReading:
    reading = SensorReading(
        system_id=system.id,
        recorded_at=payload.timestamp or datetime.now(UTC),
        power_w=payload.power_w,
        panel_temp_c=payload.panel_temp_c,
        ambient_temp_c=payload.ambient_temp_c,
        ambient_humidity_pct=payload.ambient_humidity_pct,
        irradiance=payload.irradiance,
        pressure_hpa=payload.pressure_hpa,
        particulate_pct=payload.particulate_pct,
    )
    db.add(reading)

    if system.status == SystemStatus.AWAITING_PAIRING:
        system.status = SystemStatus.ONLINE_UNTRAINED

    if payload.panel_temp_c is not None and payload.panel_temp_c > settings.panel_overheat_threshold_c:
        _raise_overheat_alert(db, system=system, panel_temp_c=payload.panel_temp_c)

    db.commit()
    db.refresh(reading)
    return reading


def _raise_overheat_alert(db: Session, *, system: PVSystem, panel_temp_c: float) -> None:
    email_to = settings.alert_email_to or None
    alert = OverheatAlert(
        system_id=system.id,
        panel_temp_c=panel_temp_c,
        threshold_c=settings.panel_overheat_threshold_c,
        email_to=email_to,
    )
    db.add(alert)

    if email_to:
        try:
            send_overheat_alert_email(
                to=email_to,
                system_name=system.name,
                panel_temp_c=panel_temp_c,
                threshold_c=settings.panel_overheat_threshold_c,
            )
        except OSError:
            logger.exception("Failed to send overheat alert email for system %s", system.id)


def list_readings(db: Session, *, system: PVSystem, start: datetime, end: datetime) -> list[SensorReading]:
    return (
        db.query(SensorReading)
        .filter(
            SensorReading.system_id == system.id,
            SensorReading.recorded_at >= start,
            SensorReading.recorded_at <= end,
        )
        .order_by(SensorReading.recorded_at)
        .all()
    )


def get_latest_reading(db: Session, *, system: PVSystem) -> SensorReading | None:
    return (
        db.query(SensorReading)
        .filter(SensorReading.system_id == system.id)
        .order_by(SensorReading.recorded_at.desc())
        .first()
    )


def list_alerts(db: Session, *, system: PVSystem) -> list[OverheatAlert]:
    return (
        db.query(OverheatAlert)
        .filter(OverheatAlert.system_id == system.id)
        .order_by(OverheatAlert.triggered_at.desc())
        .all()
    )
