from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError


ROOT_DIR = Path(__file__).resolve().parents[2]


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    raw_path = Path(value) if value else default
    return raw_path.expanduser()


@dataclass(slots=True)
class BoardConfig:
    location_name: str
    latitude: float
    longitude: float
    timezone: str
    gemini_api_key: str | None
    gemini_model: str
    output_dir: Path
    data_dir: Path
    board_url: str
    icon_style: str
    image_width: int = 600
    image_height: int = 800
    weather_url: str = "https://api.open-meteo.com/v1/forecast"

    @classmethod
    def from_env(cls) -> "BoardConfig":
        return cls(
            location_name=os.getenv("KFB_LOCATION_NAME", "Wassenaar"),
            latitude=_env_float("KFB_LATITUDE", 52.1450),
            longitude=_env_float("KFB_LONGITUDE", 4.4028),
            timezone=os.getenv("KFB_TIMEZONE", "Europe/Amsterdam"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("KFB_GEMINI_MODEL", "gemini-2.5-flash"),
            output_dir=_env_path("KFB_OUTPUT_DIR", ROOT_DIR / "output"),
            data_dir=ROOT_DIR / "data",
            board_url=os.getenv("KFB_BOARD_URL", "https://example.com/kindle-family-board/latest.png"),
            icon_style=os.getenv("KFB_ICON_STYLE", "burst"),
        )

    @property
    def tzinfo(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise RuntimeError(
                f"Timezone data for {self.timezone!r} is unavailable. Install the tzdata package."
            ) from exc

    def now(self) -> datetime:
        return datetime.now(self.tzinfo)
