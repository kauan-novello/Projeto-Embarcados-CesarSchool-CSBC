import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

MIN_RADIATION_FOR_PR_WH_M2 = 200


class PerformanceRatioBaseline(RegressorMixin, BaseEstimator):
    def __init__(self, installed_power_kw: float = 36.0, max_ac_power_kw: float = 28.6) -> None:
        self.installed_power_kw = installed_power_kw
        self.max_ac_power_kw = max_ac_power_kw

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "PerformanceRatioBaseline":
        radiation = X["radiation_wh_m2"].to_numpy()
        sunny = radiation >= MIN_RADIATION_FOR_PR_WH_M2
        ideal = radiation[sunny] * self.installed_power_kw
        self.performance_ratio_ = float(np.median(np.asarray(y)[sunny] / ideal))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        energy = X["radiation_wh_m2"].to_numpy() * self.installed_power_kw * self.performance_ratio_
        return np.clip(energy, 0, self.max_ac_power_kw * 1000)
