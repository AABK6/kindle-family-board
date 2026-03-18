from __future__ import annotations

from datetime import date, datetime
from typing import Any

import requests

from .config import BoardConfig
from .models import WeatherPeriod, WeatherSnapshot


WEATHER_CODES = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Heavy showers",
    82: "Violent showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunder and hail",
    99: "Severe thunder and hail",
}


def _get_first(values: list[Any], fallback: Any) -> Any:
    return values[0] if values else fallback


def _pick_period(hourly: dict[str, list[Any]], target_date: date, target_hour: int, label: str) -> WeatherPeriod:
    times = [datetime.fromisoformat(raw) for raw in hourly.get("time", [])]
    matching = [
        (index, timestamp)
        for index, timestamp in enumerate(times)
        if timestamp.date() == target_date
    ]
    if not matching:
        matching = list(enumerate(times))
    if not matching:
        return WeatherPeriod(label=label, weather_code=0, condition="Clear", temperature_c=0.0, precipitation_probability=0)

    best_index, _ = min(matching, key=lambda item: abs(item[1].hour - target_hour))
    weather_code = int(_get_first([hourly.get("weather_code", [0])[best_index]], 0))
    precipitation_values = hourly.get("precipitation_probability", [])
    precipitation_probability = (
        int(precipitation_values[best_index]) if precipitation_values and precipitation_values[best_index] is not None else None
    )
    return WeatherPeriod(
        label=label,
        weather_code=weather_code,
        condition=WEATHER_CODES.get(weather_code, "Weather"),
        temperature_c=float(_get_first([hourly.get("temperature_2m", [0.0])[best_index]], 0.0)),
        precipitation_probability=precipitation_probability,
    )


def fetch_weather(config: BoardConfig, target_date: date | None = None) -> WeatherSnapshot:
    params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "timezone": config.timezone,
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
    }
    if target_date is None:
        params["forecast_days"] = 1
    else:
        params["start_date"] = target_date.isoformat()
        params["end_date"] = target_date.isoformat()

    response = requests.get(config.weather_url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    current = payload.get("current", {})
    daily = payload.get("daily", {})
    hourly = payload.get("hourly", {})
    weather_code = int(current.get("weather_code", 0))
    resolved_date = target_date or datetime.fromisoformat(current.get("time")).date()

    return WeatherSnapshot(
        current_condition=WEATHER_CODES.get(weather_code, "Weather"),
        current_temperature_c=float(current.get("temperature_2m", 0.0)),
        high_c=float(_get_first(daily.get("temperature_2m_max", []), current.get("temperature_2m", 0.0))),
        low_c=float(_get_first(daily.get("temperature_2m_min", []), current.get("temperature_2m", 0.0))),
        morning=_pick_period(hourly, resolved_date, 8, "Morning"),
        afternoon=_pick_period(hourly, resolved_date, 15, "Afternoon"),
    )
