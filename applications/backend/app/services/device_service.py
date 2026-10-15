import logging
import re
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.pv_system import PVSystem
from app.models.sensor_reading import SensorReading
from app.schemas.reading import ReadingIn
from app.services.inference_service import predict_hour
from app.services.reading_service import ingest_reading

logger = logging.getLogger(__name__)

DEVICE_ID_PATTERN = re.compile(r"[0-9A-F]{12}")
PAIRING_VISIBILITY = timedelta(seconds=30)


def is_valid_device_id(device_id: str) -> bool:
    return DEVICE_ID_PATTERN.fullmatch(device_id) is not None


def ingest_device_reading(db: Session, *, device_id: str, payload: ReadingIn) -> SensorReading | None:
    now = datetime.now(UTC)
    device = db.get(Device, device_id)
    if device is None:
        device = Device(id=device_id, last_seen_at=now)
        db.add(device)
    device.last_seen_at = now
    if payload.pairing_mode:
        device.pairing_seen_at = now

    if device.system_id is None:
        db.commit()
        return None
    system = db.get(PVSystem, device.system_id)
    assert system is not None
    reading = ingest_reading(db, system=system, payload=payload)
    try:
        predict_hour(
            db,
            system=system,
            hour_start=reading.recorded_at,
            radiation_wh_m2=payload.irradiance,
            air_temp_c=payload.ambient_temp_c,
        )
    except Exception:
        logger.exception("inference failed for system %s", system.id)
        db.rollback()
    return reading


def list_pairable_devices(db: Session) -> list[Device]:
    since = datetime.now(UTC) - PAIRING_VISIBILITY
    return (
        db.query(Device)
        .filter(Device.system_id.is_(None), Device.pairing_seen_at >= since)
        .order_by(Device.pairing_seen_at.desc())
        .all()
    )


def link_device(db: Session, *, system: PVSystem, device_id: str) -> PVSystem:
    if system.device_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="System already has a device")
    device = next((d for d in list_pairable_devices(db) if d.id == device_id), None)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not in pairing mode")

    device.system_id = system.id
    device.pairing_seen_at = None
    db.commit()
    db.refresh(system)
    return system


def unlink_device(db: Session, *, system: PVSystem) -> PVSystem:
    device = db.query(Device).filter(Device.system_id == system.id).first()
    if device is not None:
        device.system_id = None
        db.commit()
    db.refresh(system)
    return system
