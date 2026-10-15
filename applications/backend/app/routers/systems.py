from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.ml_prediction import MLPrediction
from app.models.overheat_alert import OverheatAlert
from app.models.plant_hourly import PlantHourly
from app.models.pv_system import PVSystem
from app.models.sensor_reading import SensorReading
from app.models.user import User
from app.schemas.device import DeviceLinkIn
from app.schemas.energy_overview import EnergyBucketOut, EnergyOverviewOut
from app.schemas.hourly_prediction import HourlyComparisonOut
from app.schemas.inverter_reading import InverterReadingOut
from app.schemas.ml_prediction import MLPredictionOut
from app.schemas.model_report import ModelReportOut
from app.schemas.plant_hourly import PlantHourlyOut
from app.schemas.pv_system import PVSystemCreate, PVSystemOut, PVSystemUpdate
from app.schemas.reading import OverheatAlertOut, ReadingOut
from app.services import energy_overview_service, model_report_service
from app.services.device_service import link_device, unlink_device
from app.services.inverter_service import get_latest_inverter_reading
from app.services.ml_prediction_service import get_latest_prediction
from app.services.plant_hourly_service import list_plant_hourly
from app.services.prediction_service import list_hourly_comparison
from app.services.reading_service import get_latest_reading, list_alerts, list_readings
from app.services.system_service import (
    create_system,
    delete_system,
    get_owned_system_or_404,
    list_systems,
    start_training,
    update_system,
)

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("", response_model=list[PVSystemOut])
def get_systems(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[PVSystem]:
    return list_systems(db, owner=current_user)


@router.post("", response_model=PVSystemOut, status_code=status.HTTP_201_CREATED)
def post_system(
    payload: PVSystemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    return create_system(db, owner=current_user, data=payload)


@router.get("/{system_id}", response_model=PVSystemOut)
def get_system(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    return get_owned_system_or_404(db, system_id=system_id, owner=current_user)


@router.patch("/{system_id}", response_model=PVSystemOut)
def patch_system(
    system_id: UUID,
    payload: PVSystemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return update_system(db, system=system, data=payload)


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_system(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    delete_system(db, system=system)


@router.put("/{system_id}/device", response_model=PVSystemOut)
def put_system_device(
    system_id: UUID,
    payload: DeviceLinkIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return link_device(db, system=system, device_id=payload.device_id)


@router.delete("/{system_id}/device", response_model=PVSystemOut)
def delete_system_device(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return unlink_device(db, system=system)


@router.post("/{system_id}/start-training", response_model=PVSystemOut)
def post_start_training(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PVSystem:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return start_training(db, system=system)


@router.get("/{system_id}/readings", response_model=list[ReadingOut])
def get_readings(
    system_id: UUID,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SensorReading]:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    end = to or datetime.now(UTC)
    start = from_ or end - timedelta(days=30)
    return list_readings(db, system=system, start=start, end=end)


@router.get("/{system_id}/readings/latest", response_model=ReadingOut | None)
def get_latest_system_reading(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SensorReading | None:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return get_latest_reading(db, system=system)


@router.get("/{system_id}/inverter/latest", response_model=InverterReadingOut | None)
def get_latest_system_inverter_reading(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InverterReadingOut | None:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return get_latest_inverter_reading(db, system=system)


@router.get("/{system_id}/hourly", response_model=list[PlantHourlyOut])
def get_plant_hourly(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlantHourly]:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return list_plant_hourly(db, system=system)


@router.get("/{system_id}/predictions", response_model=list[HourlyComparisonOut])
def get_predictions(
    system_id: UUID,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    kind: Literal["observed", "forecast"] = "observed",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HourlyComparisonOut]:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    end = to or datetime.now(UTC)
    start = from_ or end - timedelta(days=7)
    return list_hourly_comparison(db, system=system, start=start, end=end, kind=kind)


@router.get("/{system_id}/energy/overview", response_model=EnergyOverviewOut)
def get_energy_overview(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnergyOverviewOut:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return energy_overview_service.get_overview(db, system=system)


@router.get("/{system_id}/energy/series", response_model=list[EnergyBucketOut])
def get_energy_series(
    system_id: UUID,
    period: energy_overview_service.Period = "week",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EnergyBucketOut]:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return energy_overview_service.get_series(db, system=system, period=period)


@router.get("/{system_id}/model", response_model=ModelReportOut)
def get_model(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelReportOut:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    report = model_report_service.get_model_report(str(system.id))
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema sem modelo treinado")
    return report


@router.get("/{system_id}/alerts", response_model=list[OverheatAlertOut])
def get_alerts(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OverheatAlert]:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return list_alerts(db, system=system)


@router.get("/{system_id}/ml-metrics", response_model=MLPredictionOut | None)
def get_ml_metrics(
    system_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MLPrediction | None:
    system = get_owned_system_or_404(db, system_id=system_id, owner=current_user)
    return get_latest_prediction(db, system=system)
