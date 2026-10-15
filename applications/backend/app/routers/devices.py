from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceOut
from app.services.device_service import list_pairable_devices

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/pairable", response_model=list[DeviceOut])
def get_pairable_devices(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Device]:
    return list_pairable_devices(db)
