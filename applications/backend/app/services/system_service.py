from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pv_system import PVSystem, SystemStatus
from app.models.user import User
from app.schemas.pv_system import PVSystemCreate, PVSystemUpdate


def list_systems(db: Session, *, owner: User) -> list[PVSystem]:
    return db.query(PVSystem).filter(PVSystem.owner_id == owner.id).order_by(PVSystem.created_at).all()


def create_system(db: Session, *, owner: User, data: PVSystemCreate) -> PVSystem:
    system = PVSystem(owner_id=owner.id, **data.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


def get_owned_system_or_404(db: Session, *, system_id: UUID, owner: User) -> PVSystem:
    system = db.query(PVSystem).filter(PVSystem.id == system_id, PVSystem.owner_id == owner.id).first()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    return system


def update_system(db: Session, *, system: PVSystem, data: PVSystemUpdate) -> PVSystem:
    for field, value in data.model_dump().items():
        setattr(system, field, value)
    db.commit()
    db.refresh(system)
    return system


def delete_system(db: Session, *, system: PVSystem) -> None:
    db.delete(system)
    db.commit()


def start_training(db: Session, *, system: PVSystem) -> PVSystem:
    if system.status != SystemStatus.ONLINE_UNTRAINED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot start training from status '{system.status.value}'",
        )
    system.status = SystemStatus.TRAINING
    system.training_started_at = datetime.now(UTC)
    db.commit()
    db.refresh(system)
    return system
