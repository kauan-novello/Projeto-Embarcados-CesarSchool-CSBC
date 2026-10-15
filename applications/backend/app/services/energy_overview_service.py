from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.models.hourly_prediction import FORECAST, OBSERVED, HourlyPrediction
from app.models.monthly_typical_energy import MonthlyTypicalEnergy
from app.models.plant_hourly import PlantHourly
from app.models.pv_system import PVSystem
from app.schemas.energy_overview import (
    EnergyBucketOut,
    EnergyOverviewOut,
    ExpectedKind,
    HealthOut,
    HealthState,
    MonthOutlookOut,
)
from app.services.inverter_service import get_latest_inverter_reading
from app.services.prediction_service import (
    HOUR,
    PLANT_TZ,
    _as_utc,
    real_hourly_energy,
)

Period = Literal["day", "week", "month", "year"]

KIND_BY_UNCERTAINTY: tuple[ExpectedKind, ...] = ("typical", "forecast", "observed")
HEALTH_DAYS = 7
NORMAL_MIN_RATIO = 0.90
ATTENTION_MIN_RATIO = 0.80
MIN_COMPARED_HOURS = 24
LIVE_REAL_WINDOW = timedelta(hours=48)
MIN_HOURS_FOR_A_DAY = 20
WEEK_DAYS_BACK = 7
WEEK_DAYS_AHEAD = 6


@dataclass
class HourEnergy:
    real_wh: float | None = None
    expected_wh: float | None = None
    kind: ExpectedKind | None = None


def _local_midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=PLANT_TZ).astimezone(UTC)


def _days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _month_last_day(day: date) -> date:
    return day.replace(day=monthrange(day.year, day.month)[1])


def load_hours(
    db: Session, *, system: PVSystem, start: datetime, end: datetime, now: datetime
) -> dict[datetime, HourEnergy]:
    hours: dict[datetime, HourEnergy] = {}

    predictions = (
        db.query(
            HourlyPrediction.hour_start,
            HourlyPrediction.kind,
            HourlyPrediction.predicted_energy_wh,
        )
        .filter(
            HourlyPrediction.system_id == system.id,
            HourlyPrediction.hour_start >= start,
            HourlyPrediction.hour_start < end,
        )
        .all()
    )
    for at, kind, value in predictions:
        hour = hours.setdefault(_as_utc(at), HourEnergy())
        if kind == OBSERVED or hour.kind != OBSERVED:
            hour.expected_wh, hour.kind = value, kind

    clean = (
        db.query(PlantHourly.hour_start, PlantHourly.energy_wh)
        .filter(
            PlantHourly.system_id == system.id,
            PlantHourly.hour_start >= start,
            PlantHourly.hour_start < end,
        )
        .all()
    )
    for at, value in clean:
        hours.setdefault(_as_utc(at), HourEnergy()).real_wh = value

    recent = [
        at
        for at, hour in hours.items()
        if hour.real_wh is None and now - LIVE_REAL_WINDOW <= at and at + HOUR <= now
    ]
    for at, value in real_hourly_energy(db, system=system, hours=recent).items():
        hours[at].real_wh = value
    return hours


def load_typical(db: Session, *, system: PVSystem) -> dict[int, MonthlyTypicalEnergy]:
    rows = db.query(MonthlyTypicalEnergy).filter(MonthlyTypicalEnergy.system_id == system.id).all()
    return {row.month: row for row in rows}


def _typical_day_wh(typical: dict[int, MonthlyTypicalEnergy], day: date) -> float | None:
    month = typical.get(day.month)
    return month.energy_wh / monthrange(day.year, day.month)[1] if month else None


def day_bucket(
    day: date,
    *,
    hours: dict[datetime, HourEnergy],
    typical: dict[int, MonthlyTypicalEnergy],
    today: date,
) -> EnergyBucketOut:
    start = _local_midnight(day)
    slots = [hours[at] for i in range(24) if (at := start + i * HOUR) in hours]
    real = [s.real_wh for s in slots if s.real_wh is not None]
    predicted = [s for s in slots if s.expected_wh is not None]

    expected: float | None = None
    kind: ExpectedKind | None = None
    if len(predicted) >= MIN_HOURS_FOR_A_DAY or (day < today and predicted):
        expected = sum(s.expected_wh or 0.0 for s in predicted)
        kind = "forecast" if any(s.kind == FORECAST for s in predicted) else "observed"
    elif day >= today and (typical_wh := _typical_day_wh(typical, day)) is not None:
        expected, kind = typical_wh, "typical"
    return EnergyBucketOut(
        start=start,
        real_energy_wh=sum(real) if real else None,
        expected_energy_wh=expected,
        expected_kind=kind,
    )


def health_state(ratio: float) -> HealthState:
    if ratio >= NORMAL_MIN_RATIO:
        return "normal"
    return "attention" if ratio >= ATTENTION_MIN_RATIO else "maintenance"


def plant_health(hours: dict[datetime, HourEnergy], *, now: datetime) -> HealthOut | None:
    since = now - timedelta(days=HEALTH_DAYS)
    compared = [h for at, h in hours.items() if since <= at < now and h.real_wh is not None and h.expected_wh]
    if len(compared) < MIN_COMPARED_HOURS:
        return None
    real = sum(h.real_wh or 0.0 for h in compared)
    expected = sum(h.expected_wh or 0.0 for h in compared)
    return HealthOut(
        state=health_state(real / expected),
        performance_pct=round(100 * real / expected),
        real_energy_wh=real,
        expected_energy_wh=expected,
        days=HEALTH_DAYS,
    )


def _remaining_today_wh(hours: dict[datetime, HourEnergy], *, now: datetime, today: date) -> float | None:
    current = now.replace(minute=0, second=0, microsecond=0)
    left_of_current = 1 - (now - current) / HOUR
    end = _local_midnight(today + timedelta(days=1))
    remaining = [
        (at, h.expected_wh) for at, h in hours.items() if current <= at < end and h.expected_wh is not None
    ]
    if not remaining:
        return None
    return sum(wh * (left_of_current if at == current else 1.0) for at, wh in remaining)


def _generated_today_wh(
    db: Session, *, system: PVSystem, today: date, today_bucket: EnergyBucketOut
) -> float | None:
    reading = get_latest_inverter_reading(db, system=system)
    if (
        reading is not None
        and reading.daily_yield_wh is not None
        and _as_utc(reading.recorded_at).astimezone(PLANT_TZ).date() == today
    ):
        return reading.daily_yield_wh
    return today_bucket.real_energy_wh


def get_overview(db: Session, *, system: PVSystem, now: datetime | None = None) -> EnergyOverviewOut:
    now = now or datetime.now(UTC)
    today = now.astimezone(PLANT_TZ).date()
    tomorrow = today + timedelta(days=1)
    month_first, month_last = today.replace(day=1), _month_last_day(today)

    first = min(month_first, today - timedelta(days=HEALTH_DAYS + 1))
    last = max(month_last, tomorrow)
    hours = load_hours(
        db,
        system=system,
        start=_local_midnight(first),
        end=_local_midnight(last + timedelta(days=1)),
        now=now,
    )
    typical = load_typical(db, system=system)

    def bucket(day: date) -> EnergyBucketOut:
        return day_bucket(day, hours=hours, typical=typical, today=today)

    generated_today = _generated_today_wh(db, system=system, today=today, today_bucket=bucket(today))
    remaining_today = _remaining_today_wh(hours, now=now, today=today)

    past = [bucket(day) for day in _days(month_first, today - timedelta(days=1))]
    generated_month = sum(b.real_energy_wh or 0.0 for b in past) + (generated_today or 0.0)
    ahead = [bucket(day).expected_energy_wh for day in _days(tomorrow, month_last)]
    projected = None
    if all(wh is not None for wh in ahead):
        projected = generated_month + (remaining_today or 0.0) + sum(wh or 0.0 for wh in ahead)

    month_typical = typical.get(today.month)
    return EnergyOverviewOut(
        health=plant_health(hours, now=now),
        generated_today_wh=generated_today,
        remaining_today_wh=remaining_today,
        tomorrow_wh=bucket(tomorrow).expected_energy_wh,
        month=MonthOutlookOut(
            month_start=month_first,
            generated_wh=generated_month,
            projected_wh=projected,
            typical_wh=month_typical.energy_wh if month_typical else None,
            typical_low_wh=month_typical.low_wh if month_typical else None,
            typical_high_wh=month_typical.high_wh if month_typical else None,
        ),
    )


def _month_bucket(month_first: date, days: list[EnergyBucketOut]) -> EnergyBucketOut:
    real = [d.real_energy_wh for d in days if d.real_energy_wh is not None]
    expected = [d.expected_energy_wh for d in days if d.expected_energy_wh is not None]
    kinds = {d.expected_kind for d in days}
    kind = next((k for k in KIND_BY_UNCERTAINTY if k in kinds), None)
    return EnergyBucketOut(
        start=_local_midnight(month_first),
        real_energy_wh=sum(real) if real else None,
        expected_energy_wh=sum(expected) if expected else None,
        expected_kind=kind,
    )


def get_series(
    db: Session, *, system: PVSystem, period: Period, now: datetime | None = None
) -> list[EnergyBucketOut]:
    now = now or datetime.now(UTC)
    today = now.astimezone(PLANT_TZ).date()
    if period == "day":
        first = last = today
    elif period == "week":
        first = today - timedelta(days=WEEK_DAYS_BACK)
        last = today + timedelta(days=WEEK_DAYS_AHEAD)
    elif period == "month":
        first, last = today.replace(day=1), _month_last_day(today)
    else:
        first, last = date(today.year, 1, 1), date(today.year, 12, 31)

    hours = load_hours(
        db,
        system=system,
        start=_local_midnight(first),
        end=_local_midnight(last + timedelta(days=1)),
        now=now,
    )
    if period == "day":
        start = _local_midnight(today)
        return [
            EnergyBucketOut(
                start=at,
                real_energy_wh=hour.real_wh,
                expected_energy_wh=hour.expected_wh,
                expected_kind=hour.kind,
            )
            for at in (start + i * HOUR for i in range(24))
            if (hour := hours.get(at)) is not None
        ]

    typical = load_typical(db, system=system)
    days = {day: day_bucket(day, hours=hours, typical=typical, today=today) for day in _days(first, last)}
    generated_today = _generated_today_wh(db, system=system, today=today, today_bucket=days[today])
    days[today] = days[today].model_copy(update={"real_energy_wh": generated_today})
    if period != "year":
        return list(days.values())
    return [
        _month_bucket(
            date(today.year, month, 1),
            [bucket for day, bucket in days.items() if day.month == month],
        )
        for month in range(1, 13)
    ]
