from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class WeatherPeriod:
    label: str
    weather_code: int
    condition: str
    temperature_c: float
    precipitation_probability: int | None


@dataclass(slots=True)
class WeatherSnapshot:
    current_condition: str
    current_temperature_c: float
    high_c: float
    low_c: float
    morning: WeatherPeriod
    afternoon: WeatherPeriod


@dataclass(slots=True)
class ReadingSnippet:
    kind: str
    title: str
    body: str
    source: str


@dataclass(slots=True)
class BoardContent:
    render_date: date
    greeting: str
    location_name: str
    weather: WeatherSnapshot
    family_message: str
    practice_words: tuple[str, str]
    reading: ReadingSnippet
