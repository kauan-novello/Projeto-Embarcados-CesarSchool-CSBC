from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import settings
from app.schemas.model_report import (
    FoldScoreOut,
    HourResidualOut,
    ModelReportOut,
    ModelScoreOut,
)
from app.services.inference_service import CHAMPION_ALIAS
from app.services.refreshing_cache import RefreshingCache

BASELINE_NAME = "baseline"
SCORE_METRICS = {
    "train_rmse_wh": "train_rmse",
    "cv_train_rmse_wh": "timeseries_train_rmse_mean",
    "cv_rmse_wh": "timeseries_rmse_mean",
    "cv_rmse_std_wh": "timeseries_rmse_std",
    "day_out_rmse_wh": "day_out_rmse_mean",
    "kfold_shuffled_rmse_wh": "kfold_shuffled_rmse_mean",
    "test_rmse_wh": "test_rmse",
    "test_mae_wh": "test_mae",
    "test_r2": "test_r2",
    "test_daily_mape_pct": "test_daily_mape_pct",
}


@dataclass(frozen=True)
class SystemModelReport:
    system_id: str | None
    report: ModelReportOut


def load_report_from_mlflow() -> SystemModelReport:
    import mlflow
    from mlflow import MlflowClient

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    client = MlflowClient()
    version = client.get_model_version_by_alias(settings.registered_model_name, CHAMPION_ALIAS)
    if version.run_id is None:
        raise ValueError(f"champion v{version.version} has no training run")
    parent = client.get_run(version.run_id)
    champion = parent.data.params["champion"]
    children = client.search_runs(
        [parent.info.experiment_id],
        filter_string=f"tags.mlflow.parentRunId = '{parent.info.run_id}'",
    )
    runs = {run.data.tags["mlflow.runName"]: run for run in children}

    models = [
        ModelScoreOut(
            name=name,
            is_champion=name == champion,
            is_baseline=name == BASELINE_NAME,
            **{field: run.data.metrics[metric] for field, metric in SCORE_METRICS.items()},
        )
        for name, run in runs.items()
    ]
    champion_run = runs[champion].info.run_id
    validation = client.get_metric_history(champion_run, "timeseries_fold_rmse")
    training = {
        m.step: m.value for m in client.get_metric_history(champion_run, "timeseries_fold_train_rmse")
    }
    residuals = mlflow.artifacts.load_dict(f"runs:/{parent.info.run_id}/residuals_by_hour.json")

    report = ModelReportOut(
        version=str(version.version),
        model_type=champion,
        trained_at=datetime.fromtimestamp(parent.info.start_time / 1000, tz=UTC),
        train_period=parent.data.params["train_period"],
        test_period=parent.data.params["test_period"],
        n_hours=int(parent.data.params["n_hours"]),
        performance_ratio=float(runs[BASELINE_NAME].data.params["performance_ratio"]),
        gain_over_baseline_pct=parent.data.metrics["champion_gain_over_baseline_pct"],
        models=sorted(models, key=lambda m: m.cv_rmse_wh),
        champion_folds=[
            FoldScoreOut(fold=m.step, train_rmse_wh=training[m.step], validation_rmse_wh=m.value)
            for m in sorted(validation, key=lambda m: m.step)
        ],
        residuals_by_hour=[HourResidualOut(**row) for row in residuals["hours"]],
    )
    return SystemModelReport(system_id=version.tags.get("system_id"), report=report)


report_cache = RefreshingCache(load_report_from_mlflow)


def get_model_report(
    system_id: str, cache: RefreshingCache[SystemModelReport] | None = None
) -> ModelReportOut | None:
    loaded = (cache or report_cache).get()
    if loaded is None or loaded.system_id != system_id:
        return None
    return loaded.report
