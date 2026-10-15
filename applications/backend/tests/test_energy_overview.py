from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest

from app.models.hourly_prediction import FORECAST, OBSERVED, HourlyPrediction
from app.models.inverter_reading import InverterReading
from app.models.monthly_typical_energy import MonthlyTypicalEnergy
from app.models.plant_hourly import PlantHourly
from app.models.pv_system import PVSystem
from app.services.energy_overview_service import (
    get_overview,
    get_series,
    health_state,
)
from tests.helpers import signup_and_create_plant

NOW = datetime(2026, 11, 11, 15, 30, tzinfo=UTC)
TODAY = date(2026, 11, 11)
SUN_HOURS = range(6, 16)
EXPECTED_WH = 10_000.0
TYPICAL_NOVEMBER_WH = 3_000_000.0


def local_hour(day: date, hour: int) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC) + timedelta(hours=hour + 3)


def add_day(db_session, system_id: str, day: date, *, kind: str, real_wh: float | None) -> None:
    for hour in range(24):
        sunny = hour in SUN_HOURS
        db_session.add(
            HourlyPrediction(
                system_id=UUID(system_id),
                hour_start=local_hour(day, hour),
                kind=kind,
                predicted_energy_wh=EXPECTED_WH if sunny else 0.0,
                model_version="3",
            )
        )
        if real_wh is not None:
            db_session.add(
                PlantHourly(
                    system_id=UUID(system_id),
                    hour_start=local_hour(day, hour),
                    energy_wh=real_wh if sunny else 0.0,
                    radiation_wh_m2=600.0 if sunny else 0.0,
                    air_temp_c=28.0,
                    humidity_pct=70.0,
                    humidity_estimated=False,
                    pressure_hpa=1010.0,
                    wind_speed_m_s=3.0,
                )
            )
        db_session.flush()
    db_session.commit()


def add_typical_november(db_session, system_id: str) -> None:
    db_session.add(
        MonthlyTypicalEnergy(
            system_id=UUID(system_id),
            month=11,
            energy_wh=TYPICAL_NOVEMBER_WH,
            low_wh=2_800_000.0,
            high_wh=3_200_000.0,
            n_years=10,
            model_version="3",
        )
    )
    db_session.commit()


def system_of(db_session, system_id: str) -> PVSystem:
    return db_session.get(PVSystem, UUID(system_id))


@pytest.mark.parametrize(
    ("ratio", "state"),
    [
        (1.02, "normal"),
        (0.90, "normal"),
        (0.899, "attention"),
        (0.80, "attention"),
        (0.799, "maintenance"),
    ],
)
def test_health_state_cuts(ratio, state):
    assert health_state(ratio) == state


@pytest.mark.parametrize(
    ("real_wh", "state", "pct"),
    [(9_500.0, "normal", 95), (8_500.0, "attention", 85), (7_000.0, "maintenance", 70)],
)
def test_health_compares_the_last_seven_days(client, db_session, real_wh, state, pct):
    system_id = signup_and_create_plant(client)["id"]
    for back in range(1, 8):
        add_day(
            db_session,
            system_id,
            TODAY - timedelta(days=back),
            kind=OBSERVED,
            real_wh=real_wh,
        )

    health = get_overview(db_session, system=system_of(db_session, system_id), now=NOW).health

    assert health is not None
    assert (health.state, health.performance_pct) == (state, pct)


def test_health_ignores_days_before_the_window(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    for back in range(1, 8):
        add_day(
            db_session,
            system_id,
            TODAY - timedelta(days=back),
            kind=OBSERVED,
            real_wh=9_500.0,
        )
    add_day(db_session, system_id, TODAY - timedelta(days=9), kind=OBSERVED, real_wh=0.0)

    health = get_overview(db_session, system=system_of(db_session, system_id), now=NOW).health

    assert health is not None and health.performance_pct == 95


def test_no_health_without_enough_compared_hours(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_day(db_session, system_id, TODAY - timedelta(days=1), kind=OBSERVED, real_wh=5_000.0)

    overview = get_overview(db_session, system=system_of(db_session, system_id), now=NOW)

    assert overview.health is None


def test_today_tomorrow_and_month_projection(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_typical_november(db_session, system_id)
    for day in range(1, 11):
        add_day(db_session, system_id, date(2026, 11, day), kind=OBSERVED, real_wh=9_000.0)
    for day in range(11, 14):
        add_day(db_session, system_id, date(2026, 11, day), kind=FORECAST, real_wh=None)

    overview = get_overview(db_session, system=system_of(db_session, system_id), now=NOW)

    assert overview.remaining_today_wh == pytest.approx(3.5 * EXPECTED_WH)
    assert overview.tomorrow_wh == pytest.approx(10 * EXPECTED_WH)
    assert overview.generated_today_wh is None
    month = overview.month
    assert month.generated_wh == pytest.approx(10 * 10 * 9_000.0)
    assert month.projected_wh == pytest.approx(900_000.0 + 35_000.0 + 2 * 100_000.0 + 17 * 100_000.0)
    assert (month.typical_low_wh, month.typical_high_wh) == (2_800_000.0, 3_200_000.0)


def test_month_is_not_projected_without_typical_days(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_day(db_session, system_id, TODAY, kind=FORECAST, real_wh=None)

    month = get_overview(db_session, system=system_of(db_session, system_id), now=NOW).month

    assert month.projected_wh is None and month.typical_wh is None


def test_week_series_goes_from_observed_to_forecast_to_typical(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_typical_november(db_session, system_id)
    add_day(db_session, system_id, TODAY - timedelta(days=1), kind=OBSERVED, real_wh=9_000.0)
    add_day(db_session, system_id, TODAY + timedelta(days=1), kind=FORECAST, real_wh=None)

    series = get_series(db_session, system=system_of(db_session, system_id), period="week", now=NOW)
    by_day = {b.start.astimezone(UTC).date(): b for b in series}

    assert len(series) == 14
    yesterday = by_day[TODAY - timedelta(days=1)]
    assert (yesterday.expected_kind, yesterday.real_energy_wh) == ("observed", 90_000.0)
    assert by_day[TODAY - timedelta(days=3)].expected_energy_wh is None
    assert by_day[TODAY + timedelta(days=1)].expected_kind == "forecast"
    beyond = by_day[TODAY + timedelta(days=5)]
    assert (beyond.expected_kind, beyond.real_energy_wh) == ("typical", None)
    assert beyond.expected_energy_wh == pytest.approx(100_000.0)


def test_today_uses_the_inverter_daily_counter_over_gappy_hours(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_day(db_session, system_id, TODAY, kind=FORECAST, real_wh=None)
    db_session.add(
        InverterReading(
            system_id=UUID(system_id),
            recorded_at=NOW - timedelta(minutes=5),
            source="cloud",
            daily_yield_wh=61_000.0,
        )
    )
    db_session.commit()
    system = system_of(db_session, system_id)

    month = get_series(db_session, system=system, period="month", now=NOW)

    assert month[TODAY.day - 1].real_energy_wh == 61_000.0
    assert get_overview(db_session, system=system, now=NOW).generated_today_wh == 61_000.0


def test_year_series_sums_months_and_uses_typical_ahead(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    add_typical_november(db_session, system_id)
    add_day(db_session, system_id, date(2026, 10, 20), kind=OBSERVED, real_wh=9_000.0)
    add_day(db_session, system_id, date(2026, 10, 21), kind=OBSERVED, real_wh=9_000.0)

    series = get_series(db_session, system=system_of(db_session, system_id), period="year", now=NOW)

    assert len(series) == 12
    october, november, december = series[9], series[10], series[11]
    assert october.real_energy_wh == pytest.approx(180_000.0)
    assert (october.expected_energy_wh, october.expected_kind) == (
        200_000.0,
        "observed",
    )
    assert november.expected_kind == "typical"
    assert november.expected_energy_wh == pytest.approx(20 * 100_000.0)
    assert december.expected_energy_wh is None


def test_energy_endpoints_are_owner_only(client, db_session):
    system_id = signup_and_create_plant(client)["id"]
    assert client.get(f"/systems/{system_id}/energy/overview").status_code == 200
    assert client.get(f"/systems/{system_id}/energy/series?period=day").json() == []
    assert client.get(f"/systems/{system_id}/energy/series?period=decade").status_code == 422

    client.post("/auth/logout")
    signup_and_create_plant(client, email="other@example.com")
    assert client.get(f"/systems/{system_id}/energy/overview").status_code == 404
