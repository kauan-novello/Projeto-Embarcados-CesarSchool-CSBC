import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402


def daily_mape(y_true: pd.Series, y_pred: np.ndarray, local_dates: pd.Series) -> float:
    daily = pd.DataFrame({"true": y_true.to_numpy(), "pred": y_pred, "date": local_dates.to_numpy()})
    daily = daily.groupby("date")[["true", "pred"]].sum()
    return float((np.abs(daily["true"] - daily["pred"]) / daily["true"]).mean() * 100)


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray, local_dates: pd.Series) -> dict[str, float]:
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": float(mse),
        "rmse": rmse,
        "r2": float(r2_score(y_true, y_pred)),
        "nrmse_pct": rmse / float(y_true.mean()) * 100,
        "daily_mape_pct": daily_mape(y_true, y_pred, local_dates),
    }


def plot_real_vs_predicted(index: pd.DatetimeIndex, y_true: pd.Series, y_pred: np.ndarray, title: str) -> Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(index, y_true.to_numpy() / 1000, ".-", label="Real", linewidth=1)
    ax.plot(index, y_pred / 1000, ".-", label="Previsto", linewidth=1)
    ax.set_ylabel("Energia na hora (kWh)")
    ax.set_title(title)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_scatter(y_true: pd.Series, y_pred: np.ndarray, title: str) -> Figure:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_true / 1000, y_pred / 1000, s=6, alpha=0.4)
    top = max(float(y_true.max()), float(y_pred.max())) / 1000
    ax.plot([0, top], [0, top], "k--", linewidth=1)
    ax.set_xlabel("Real (kWh)")
    ax.set_ylabel("Previsto (kWh)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_feature_importance(importances: np.ndarray, names: list[str], title: str) -> Figure:
    order = np.argsort(importances)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(np.array(names)[order], importances[order])
    ax.set_xlabel("Importância (redução de impureza)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_loss_curve(loss_curve: list[float], title: str) -> Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(range(1, len(loss_curve) + 1), loss_curve)
    ax.set_xlabel("Época")
    ax.set_ylabel("Loss (MSE/2)")
    ax.set_yscale("log")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_residuals(test: pd.DataFrame, residual: np.ndarray, y_pred: np.ndarray, title: str) -> Figure:
    kwh = residual / 1000
    by_hour = pd.Series(kwh, index=test["hour"].to_numpy())
    by_month = pd.Series(kwh, index=pd.to_datetime(test["local_date"]).dt.month.to_numpy())
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].hist(kwh, bins=60)
    axes[0, 0].axvline(0, color="k", linewidth=1)
    axes[0, 0].set_xlabel("Resíduo (kWh)")
    axes[0, 0].set_ylabel("Horas")
    axes[0, 0].set_title(f"Distribuição (média {kwh.mean():+.2f} kWh)")

    axes[0, 1].scatter(y_pred / 1000, kwh, s=5, alpha=0.3)
    axes[0, 1].axhline(0, color="k", linewidth=1)
    axes[0, 1].set_xlabel("Previsto (kWh)")
    axes[0, 1].set_ylabel("Resíduo (kWh)")
    axes[0, 1].set_title("Resíduo × previsto")

    for ax, series, label in ((axes[1, 0], by_hour, "Hora local"), (axes[1, 1], by_month, "Mês")):
        groups = sorted(series.index.unique())
        ax.boxplot([series[series.index == g].to_numpy() for g in groups], tick_labels=groups, showfliers=False)
        ax.axhline(0, color="k", linewidth=1)
        ax.set_xlabel(label)
        ax.set_ylabel("Resíduo (kWh)")
    axes[1, 0].set_title("Por hora do dia")
    axes[1, 1].set_title("Por mês (teste)")

    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_train_vs_validation(summary: pd.DataFrame) -> Figure:
    columns = [
        ("train_rmse", "Treino inteiro"),
        ("timeseries_train_rmse_mean", "Treino (folds)"),
        ("timeseries_rmse_mean", "Validação (folds)"),
        ("test_rmse", "Teste"),
    ]
    x = np.arange(len(summary))
    width = 0.2
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (key, label) in enumerate(columns):
        ax.bar(x + (i - 1.5) * width, summary[key] / 1000, width, label=label)
    ax.set_xticks(x, summary.index)
    ax.set_ylabel("RMSE (kWh)")
    ax.set_title("Treino × validação × teste")
    ax.legend(fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    return fig


def plot_fold_rmse(fold_rmse: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(7, 4))
    for model_name, row in fold_rmse.iterrows():
        ax.plot(range(1, len(row) + 1), row.to_numpy() / 1000, "o-", label=model_name)
    ax.set_xlabel("Fold do TimeSeriesSplit (mais recente →)")
    ax.set_ylabel("RMSE (kWh)")
    ax.set_xticks(range(1, fold_rmse.shape[1] + 1))
    ax.legend()
    ax.set_title("RMSE por fold")
    fig.tight_layout()
    return fig


def plot_validation_comparison(summary: pd.DataFrame) -> Figure:
    strategies = [("timeseries", "TimeSeriesSplit"), ("day_out", "Um dia fora"), ("kfold_shuffled", "KFold embaralhado")]
    x = np.arange(len(summary))
    width = 0.27
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, (key, label) in enumerate(strategies):
        ax.bar(
            x + (i - 1) * width,
            summary[f"{key}_rmse_mean"] / 1000,
            width,
            yerr=summary[f"{key}_rmse_std"] / 1000,
            capsize=3,
            label=label,
        )
    ax.scatter(x, summary["test_rmse"] / 1000, color="k", marker="D", zorder=3, label="Holdout (teste)")
    if "baseline" in summary.index:
        ax.axhline(summary.loc["baseline", "timeseries_rmse_mean"] / 1000, color="gray", linestyle="--",
                   linewidth=1, label="Baseline físico (TimeSeriesSplit)")
    ax.set_xticks(x, summary.index)
    ax.set_ylabel("RMSE (kWh)")
    ax.set_title("RMSE por estratégia de validação (média ± desvio)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig
