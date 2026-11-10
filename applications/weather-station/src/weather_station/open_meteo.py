from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARIABLES = "shortwave_radiation,temperature_2m,relative_humidity_2m,surface_pressure"


@dataclass(frozen=True)
class HourlyWeather:
    hour_start: datetime
    irradiance_w_m2: float
    air_temp_c: float
    humidity_pct: float
    pressure_hpa: float


def fetch_closed_hours(
    client: httpx.Client, latitude: float, longitude: float, now: datetime
) -> list[HourlyWeather]:
    response = client.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": HOURLY_VARIABLES,
            "timezone": "UTC",
            "past_days": 1,
            "forecast_days": 1,
        },
        timeout=30,
    )
    response.raise_for_status()
    hourly = response.json()["hourly"]
    ends = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in hourly["time"]]
    return [
        HourlyWeather(
            hour_start=end - timedelta(hours=1),
            irradiance_w_m2=float(hourly["shortwave_radiation"][i]),
            air_temp_c=float(hourly["temperature_2m"][i]),
            humidity_pct=float(hourly["relative_humidity_2m"][i]),
            pressure_hpa=float(hourly["surface_pressure"][i]),
        )
        for i, end in enumerate(ends)
        if end <= now
    ]
