import argparse
import os
import sys

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.base import clone
from sklearn.ensemble import AdaBoostRegressor, RandomForestRegressor
from sklearn.model_selection import (
    GridSearchCV,
    KFold,
    LeaveOneGroupOut,
    TimeSeriesSplit,
    cross_val_score,
    cross_validate,
)
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from baseline import PerformanceRatioBaseline
from db import (
    add_system_id_argument,
    get_engine,
    load_installed_power_kw,
    load_inverter_yield,
    load_max_ac_power_kw,
    mark_model_active,
)
from evaluation import (
    plot_feature_importance,
    plot_fold_rmse,
    plot_loss_curve,
    plot_real_vs_predicted,
    plot_residuals,
    plot_train_vs_validation,
    plot_scatter,
    plot_validation_comparison,
    regression_metrics,
)
from features import FEATURE_COLUMNS, TARGET_COLUMN, build_hourly_dataset, split_xy, trusted_hourly_energy
from weather import OPEN_METEO_SOURCE_ID, load_open_meteo_hourly

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))

EXPERIMENT_NAME = "solarsense-energy-hourly-openmeteo"
REGISTERED_MODEL_NAME = "solarsense-energy-hourly"
CHAMPION_ALIAS = "champion"
TEST_FRACTION = 0.2
BASELINE_NAME = "baseline"
N_SPLITS = 5
RANDOM_STATE = 42
SCORING = "neg_root_mean_squared_error"
PLOT_DAYS = 7

CANDIDATE_MODELS = {
    "knn": (
        KNeighborsRegressor(),
        {"model__n_neighbors": [5, 10, 20, 40], "model__weights": ["uniform", "distance"]},
    ),
    "decision_tree": (
        DecisionTreeRegressor(random_state=RANDOM_STATE),
        {"model__max_depth": [4, 6, 8, 12, None], "model__min_samples_leaf": [1, 5, 20]},
    ),
    "random_forest": (
        RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=1),
        {
            "model__n_estimators": [100, 300],
            "model__max_depth": [8, 16, None],
            "model__min_samples_leaf": [1, 5],
        },
    ),
    "adaboost": (
        AdaBoostRegressor(estimator=DecisionTreeRegressor(), random_state=RANDOM_STATE),
        {
            "model__n_estimators": [50, 100, 200],
            "model__learning_rate": [0.05, 0.1, 0.5, 1.0],
            "model__estimator__max_depth": [3, 5],
        },
    ),
    "mlp": (
        MLPRegressor(max_iter=2000, early_stopping=True, random_state=RANDOM_STATE),
        {
            "model__hidden_layer_sizes": [(32,), (64,), (64, 32)],
            "model__alpha": [1e-4, 1e-3, 1e-2],
            "model__learning_rate_init": [1e-3, 1e-2],
        },
    ),
}


def make_pipeline(estimator) -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("model", clone(estimator))])


def load_dataset(system_id: str) -> pd.DataFrame:
    engine = get_engine()
    weather = load_open_meteo_hourly()
    energy = trusted_hourly_energy(
        load_inverter_yield(system_id, engine),
        load_inverter_yield(system_id, engine, counter="daily_yield_wh"),
        weather["radiation_wh_m2"],
        load_max_ac_power_kw(system_id, engine),
    )
    return build_hourly_dataset(energy, weather)


def temporal_holdout(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    days = np.array(sorted(df["local_date"].unique()))
    first_test_day = days[int(len(days) * (1 - TEST_FRACTION))]
    is_test = df["local_date"] >= first_test_day
    return df[~is_test], df[is_test]


def cv_rmse(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, cv, groups=None) -> tuple[float, float]:
    scores = -cross_val_score(pipeline, X, y, cv=cv, groups=groups, scoring=SCORING, n_jobs=-1)
    return float(scores.mean()), float(scores.std())


def fold_scores(search: GridSearchCV) -> tuple[list[float], list[float]]:
    best = search.best_index_
    validation = [float(-search.cv_results_[f"split{i}_test_score"][best]) for i in range(N_SPLITS)]
    training = [float(-search.cv_results_[f"split{i}_train_score"][best]) for i in range(N_SPLITS)]
    return validation, training


def log_model_plots(name: str, pipeline, test: pd.DataFrame, y_pred: np.ndarray) -> None:
    y_test = test[TARGET_COLUMN]
    last_days = test["local_date"] >= sorted(test["local_date"].unique())[-PLOT_DAYS]
    mlflow.log_figure(
        plot_real_vs_predicted(
            test.index[last_days], y_test[last_days], y_pred[last_days.to_numpy()],
            f"{name}: últimos {PLOT_DAYS} dias do teste",
        ),
        "plots/real_vs_predicted.png",
    )
    mlflow.log_figure(plot_scatter(y_test, y_pred, f"{name}: real × previsto (teste)"), "plots/scatter.png")
    mlflow.log_figure(
        plot_residuals(test, y_test.to_numpy() - y_pred, y_pred, f"{name}: resíduos no teste (real − previsto)"),
        "plots/residuals.png",
    )
    if not isinstance(pipeline, Pipeline):
        return

    model = pipeline.named_steps["model"]
    if hasattr(model, "feature_importances_"):
        mlflow.log_figure(
            plot_feature_importance(model.feature_importances_, FEATURE_COLUMNS, f"{name}: importância das features"),
            "plots/feature_importance.png",
        )
    if hasattr(model, "loss_curve_"):
        mlflow.log_figure(plot_loss_curve(model.loss_curve_, f"{name}: loss por época"), "plots/loss_curve.png")


def validate_and_test(
    name: str, fitted, folds: list[float], train_folds: list[float], train: pd.DataFrame, test: pd.DataFrame
) -> dict:
    X_train, y_train = split_xy(train)
    X_test, y_test = split_xy(test)
    result = {
        "timeseries_rmse_mean": float(np.mean(folds)),
        "timeseries_rmse_std": float(np.std(folds)),
        "timeseries_train_rmse_mean": float(np.mean(train_folds)),
        "train_rmse": float(np.sqrt(np.mean((y_train.to_numpy() - fitted.predict(X_train)) ** 2))),
    }
    for i, (rmse, train_rmse) in enumerate(zip(folds, train_folds, strict=True), start=1):
        mlflow.log_metric("timeseries_fold_rmse", rmse, step=i)
        mlflow.log_metric("timeseries_fold_train_rmse", train_rmse, step=i)

    unfitted = clone(fitted)
    result["day_out_rmse_mean"], result["day_out_rmse_std"] = cv_rmse(
        unfitted, X_train, y_train, LeaveOneGroupOut(), groups=train["local_date"]
    )
    result["kfold_shuffled_rmse_mean"], result["kfold_shuffled_rmse_std"] = cv_rmse(
        unfitted, X_train, y_train, KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    )

    y_pred = fitted.predict(X_test)
    result.update({f"test_{k}": v for k, v in regression_metrics(y_test, y_pred, test["local_date"]).items()})
    mlflow.log_metrics(result)
    log_model_plots(name, fitted, test, y_pred)
    result["y_pred"] = y_pred
    return result


def evaluate_baseline(baseline: PerformanceRatioBaseline, train: pd.DataFrame, test: pd.DataFrame) -> dict:
    X_train, y_train = split_xy(train)
    with mlflow.start_run(run_name=BASELINE_NAME, nested=True):
        scores = cross_validate(
            baseline, X_train, y_train, cv=TimeSeriesSplit(n_splits=N_SPLITS), scoring=SCORING, return_train_score=True
        )
        folds, train_folds = (-scores["test_score"]).tolist(), (-scores["train_score"]).tolist()
        fitted = clone(baseline).fit(X_train, y_train)
        mlflow.log_params({
            "installed_power_kw": baseline.installed_power_kw,
            "max_ac_power_kw": baseline.max_ac_power_kw,
            "performance_ratio": round(fitted.performance_ratio_, 4),
        })
        result = validate_and_test(BASELINE_NAME, fitted, folds, train_folds, train, test)
    result["best_params"] = {"performance_ratio": fitted.performance_ratio_}
    result["fold_rmse"] = folds
    return result


def evaluate_candidate(name: str, estimator, grid: dict, train: pd.DataFrame, test: pd.DataFrame) -> dict:
    X_train, y_train = split_xy(train)
    X_test, y_test = split_xy(test)

    with mlflow.start_run(run_name=name, nested=True):
        search = GridSearchCV(
            make_pipeline(estimator),
            grid,
            cv=TimeSeriesSplit(n_splits=N_SPLITS),
            scoring=SCORING,
            n_jobs=-1,
            return_train_score=True,
        )
        search.fit(X_train, y_train)
        best = search.best_estimator_
        mlflow.log_params({k.removeprefix("model__"): v for k, v in search.best_params_.items()})

        folds, train_folds = fold_scores(search)
        result = validate_and_test(name, best, folds, train_folds, train, test)
        mlflow.sklearn.log_model(
            best,
            name="model",
            serialization_format="pickle",
            signature=infer_signature(X_test, result["y_pred"]),
        )

    result["best_params"] = search.best_params_
    result["fold_rmse"] = folds
    return result


def residuals_by_hour(test: pd.DataFrame, predictions: pd.DataFrame, champion: str) -> dict:
    hours = test["hour"].to_numpy()
    by_hour = {
        name: (predictions["real_wh"] - predictions[name]).groupby(hours).mean()
        for name in (BASELINE_NAME, champion)
    }
    return {
        "champion": champion,
        "hours": [
            {"hour": int(h), "baseline_wh": float(by_hour[BASELINE_NAME][h]), "champion_wh": float(by_hour[champion][h])}
            for h in by_hour[champion].index
        ],
    }


def register_champion(name: str, estimator, best_params: dict, df: pd.DataFrame, system_id: str) -> int:
    X, y = split_xy(df)
    pipeline = make_pipeline(estimator).set_params(**best_params).fit(X, y)
    model_info = mlflow.sklearn.log_model(
        pipeline,
        name="champion_model",
        serialization_format="pickle",
        signature=infer_signature(X, pipeline.predict(X)),
        registered_model_name=REGISTERED_MODEL_NAME,
    )
    version = int(model_info.registered_model_version)
    client = MlflowClient()
    client.set_registered_model_alias(REGISTERED_MODEL_NAME, CHAMPION_ALIAS, version)
    client.set_model_version_tag(REGISTERED_MODEL_NAME, str(version), "model_type", name)
    client.set_model_version_tag(REGISTERED_MODEL_NAME, str(version), "system_id", system_id)
    mark_model_active(system_id)
    return version


def train(system_id: str) -> pd.DataFrame:
    df = load_dataset(system_id)
    train_df, test_df = temporal_holdout(df)
    baseline = PerformanceRatioBaseline(load_installed_power_kw(system_id), load_max_ac_power_kw(system_id))

    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name=f"compare-{system_id[:8]}"):
        mlflow.log_params(
            {
                "system_id": system_id,
                "weather_source": OPEN_METEO_SOURCE_ID,
                "features": ",".join(FEATURE_COLUMNS),
                "target": TARGET_COLUMN,
                "n_hours": len(df),
                "n_days": df["local_date"].nunique(),
                "train_period": f"{train_df['local_date'].min()}..{train_df['local_date'].max()}",
                "test_period": f"{test_df['local_date'].min()}..{test_df['local_date'].max()}",
                "test_fraction": TEST_FRACTION,
                "cv": f"TimeSeriesSplit({N_SPLITS})",
            }
        )

        results = {BASELINE_NAME: evaluate_baseline(baseline, train_df, test_df)}
        print(f"[baseline] TimeSeriesSplit RMSE={results[BASELINE_NAME]['timeseries_rmse_mean']:.0f} Wh", flush=True)
        for name, (estimator, grid) in CANDIDATE_MODELS.items():
            print(f"[{name}] grid search...", flush=True)
            results[name] = evaluate_candidate(name, estimator, grid, train_df, test_df)
            print(
                f"[{name}] TimeSeriesSplit RMSE={results[name]['timeseries_rmse_mean']:.0f} Wh "
                f"| teste RMSE={results[name]['test_rmse']:.0f} Wh R²={results[name]['test_r2']:.3f}",
                flush=True,
            )

        test_predictions = pd.DataFrame(
            {"real_wh": test_df[TARGET_COLUMN]} | {name: r.pop("y_pred") for name, r in results.items()},
            index=test_df.index,
        )
        summary = pd.DataFrame(results).T.drop(columns=["best_params", "fold_rmse"]).astype(float)
        fold_rmse = pd.DataFrame({name: r["fold_rmse"] for name, r in results.items()}).T
        mlflow.log_text(summary.round(4).to_csv(), "comparison.csv")
        mlflow.log_figure(plot_validation_comparison(summary), "plots/validation_comparison.png")
        mlflow.log_figure(plot_fold_rmse(fold_rmse), "plots/fold_rmse.png")
        mlflow.log_figure(plot_train_vs_validation(summary), "plots/train_vs_validation.png")

        champion = summary.drop(index=BASELINE_NAME)["timeseries_rmse_mean"].idxmin()
        mlflow.log_param("champion", champion)
        gain = 1 - summary.loc[champion, "timeseries_rmse_mean"] / summary.loc[BASELINE_NAME, "timeseries_rmse_mean"]
        mlflow.log_metric("champion_gain_over_baseline_pct", gain * 100)
        mlflow.log_text(test_predictions[["real_wh", BASELINE_NAME, champion]].to_csv(), "test_predictions.csv")
        mlflow.log_dict(residuals_by_hour(test_df, test_predictions, champion), "residuals_by_hour.json")
        version = register_champion(
            champion, CANDIDATE_MODELS[champion][0], results[champion]["best_params"], df, system_id
        )
        print(f"Champion: {champion} → {REGISTERED_MODEL_NAME} v{version} (@{CHAMPION_ALIAS})")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and register the hourly energy models")
    add_system_id_argument(parser)
    args = parser.parse_args()

    summary = train(args.system_id)
    columns = ["train_rmse", "timeseries_train_rmse_mean", "timeseries_rmse_mean", "day_out_rmse_mean", "kfold_shuffled_rmse_mean", "test_rmse", "test_r2",
               "test_nrmse_pct", "test_daily_mape_pct"]
    print(summary[columns].round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
