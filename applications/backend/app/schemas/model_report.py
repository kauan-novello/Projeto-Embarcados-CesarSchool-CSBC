from datetime import datetime

from pydantic import BaseModel


class ModelScoreOut(BaseModel):
    name: str
    is_champion: bool
    is_baseline: bool
    train_rmse_wh: float
    cv_train_rmse_wh: float
    cv_rmse_wh: float
    cv_rmse_std_wh: float
    day_out_rmse_wh: float
    kfold_shuffled_rmse_wh: float
    test_rmse_wh: float
    test_mae_wh: float
    test_r2: float
    test_daily_mape_pct: float


class FoldScoreOut(BaseModel):
    fold: int
    train_rmse_wh: float
    validation_rmse_wh: float


class HourResidualOut(BaseModel):
    hour: int
    baseline_wh: float
    champion_wh: float


class ModelReportOut(BaseModel):
    version: str
    model_type: str
    trained_at: datetime
    train_period: str
    test_period: str
    n_hours: int
    performance_ratio: float
    gain_over_baseline_pct: float
    models: list[ModelScoreOut]
    champion_folds: list[FoldScoreOut]
    residuals_by_hour: list[HourResidualOut]
