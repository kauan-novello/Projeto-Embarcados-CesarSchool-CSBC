import numpy as np
import pandas as pd

LOCAL_TZ = "America/Recife"

TARGET_COLUMN = "energy_wh"
FEATURE_COLUMNS = [
    "radiation_wh_m2",
    "air_temp_c",
    "hour",
    "day_of_year_sin",
    "day_of_year_cos",
]

MIN_DAILY_ENERGY_WH = 1_000
MIN_DAYLIGHT_RADIATION_WH_M2 = 2.0
FROZEN_COUNTER_RADIATION_WH_M2 = 50.0
NIGHT_ENDS_HOUR = 7
NIGHT_STARTS_HOUR = 17
SATURATED_HUMIDITY_PCT = 100.0


def hourly_energy(total_yield_wh: pd.Series, max_ac_power_kw: float) -> pd.Series:
    grid = pd.date_range(total_yield_wh.index.min().ceil("h"), total_yield_wh.index.max().floor("h"), freq="h")
    counter = total_yield_wh.reindex(grid)
    energy = counter.shift(-1) - counter
    max_possible_wh = max_ac_power_kw * 1000.0
    energy = energy.where(energy.between(0, max_possible_wh))
    return energy.rename(TARGET_COLUMN).rename_axis("hour_start")


def fill_counter_gaps(
    daily_yield_wh: pd.Series, energy: pd.Series, radiation: pd.Series, max_ac_power_kw: float
) -> tuple[pd.Series, pd.Series]:
    cap_wh = max_ac_power_kw * 1000.0
    counter = daily_yield_wh.reindex(energy.index)
    weights = radiation.reindex(energy.index).fillna(0.0).clip(lower=0.0)
    local_date = pd.Series(energy.index.tz_convert(LOCAL_TZ).date, index=energy.index)
    filled = energy.copy()
    estimated = pd.Series(False, index=energy.index)

    known = counter.dropna()
    for (start, before), (end, after) in zip(known.items(), known.iloc[1:].items(), strict=False):
        hours = pd.date_range(start, end, freq="h", inclusive="left")
        if len(hours) == 1 and pd.notna(energy.get(start)):
            continue
        if len(hours) == 1:
            hours = _with_stuck_hours_before(hours, after - before, cap_wh, energy, local_date)
        if local_date[hours].nunique() != 1 or local_date[end] != local_date[hours[0]]:
            continue
        shares = _spread(after - counter[hours[0]], weights[hours], cap_wh)
        if shares is not None:
            filled[hours] = shares
            estimated[hours] = True
    return filled, estimated


def _with_stuck_hours_before(
    hours: pd.DatetimeIndex, total_wh: float, cap_wh: float, energy: pd.Series, local_date: pd.Series
) -> pd.DatetimeIndex:
    first = hours[0]
    while True:
        previous = first - pd.Timedelta(hours=1)
        if previous not in energy.index or local_date[previous] != local_date[first]:
            break
        too_big = total_wh > cap_wh * len(pd.date_range(first, hours[-1], freq="h"))
        if not (energy[previous] == 0 or too_big):
            break
        if pd.notna(energy[previous]):
            total_wh += energy[previous]
        first = previous
    return pd.date_range(first, hours[-1], freq="h")


def _spread(total_wh: float, weights: pd.Series, cap_wh: float) -> pd.Series | None:
    if total_wh < 0 or total_wh > cap_wh * len(weights):
        return None
    shares = pd.Series(0.0, index=weights.index)
    free = weights.index
    remaining = total_wh
    while remaining > 1e-6:
        free_weights = weights[free]
        if free_weights.sum() <= 0:
            return None
        part = remaining * free_weights / free_weights.sum()
        over = part > cap_wh
        if not over.any():
            shares[free] += part
            return shares
        shares[part.index[over]] = cap_wh
        remaining -= cap_wh * over.sum()
        free = free[~over.to_numpy()]
    return shares


def trusted_hourly_energy(
    total_yield_wh: pd.Series, daily_yield_wh: pd.Series, radiation: pd.Series, max_ac_power_kw: float
) -> pd.Series:
    energy = hourly_energy(total_yield_wh, max_ac_power_kw)
    _, estimated = fill_counter_gaps(daily_yield_wh, energy, radiation, max_ac_power_kw)
    return energy.mask(estimated)


def drop_outage_days(df: pd.DataFrame) -> pd.DataFrame:
    local_date = df.index.tz_convert(LOCAL_TZ).date
    daily = df[TARGET_COLUMN].groupby(local_date).transform("sum")
    return df[daily >= MIN_DAILY_ENERGY_WH]


def clean_energy_hours(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=[TARGET_COLUMN])
    df = drop_outage_days(df)
    return df[~((df[TARGET_COLUMN] == 0) & (df["radiation_wh_m2"] > FROZEN_COUNTER_RADIATION_WH_M2))]


def fill_night_radiation(radiation: pd.Series) -> pd.Series:
    local_hour = radiation.index.tz_convert(LOCAL_TZ).hour
    is_night = (local_hour < NIGHT_ENDS_HOUR) | (local_hour >= NIGHT_STARTS_HOUR)
    return radiation.mask(radiation.isna() & is_night, 0.0)


def fill_saturated_humidity(humidity: pd.Series) -> tuple[pd.Series, pd.Series]:
    return humidity.fillna(SATURATED_HUMIDITY_PCT), humidity.isna()


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    local = df.index.tz_convert(LOCAL_TZ)
    df["hour"] = local.hour.astype("int64")
    df["local_date"] = local.date
    angle = 2 * np.pi * local.dayofyear / 365.25
    df["day_of_year_sin"] = np.sin(angle)
    df["day_of_year_cos"] = np.cos(angle)
    return df


def build_hourly_dataset(energy: pd.Series, weather: pd.DataFrame) -> pd.DataFrame:
    df = clean_energy_hours(weather.join(energy, how="inner"))
    df = df[(df["radiation_wh_m2"] > MIN_DAYLIGHT_RADIATION_WH_M2) | (df[TARGET_COLUMN] > 0)]
    df = add_calendar_features(df)
    return df.dropna(subset=FEATURE_COLUMNS).sort_index()


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[FEATURE_COLUMNS], df[TARGET_COLUMN]
