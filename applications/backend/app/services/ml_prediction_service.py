from sqlalchemy.orm import Session

from app.models.ml_prediction import MLPrediction
from app.models.pv_system import PVSystem


def get_latest_prediction(db: Session, *, system: PVSystem) -> MLPrediction | None:
    return (
        db.query(MLPrediction)
        .filter(MLPrediction.system_id == system.id)
        .order_by(MLPrediction.created_at.desc())
        .first()
    )
