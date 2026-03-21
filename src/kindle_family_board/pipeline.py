from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from shutil import copy2

from .config import BoardConfig
from .content import load_lines, load_reading_carousel, pick_carousel_reading, pick_practice_words, pick_rotating_item
from .models import BoardContent
from .render import render_board
from .weather import fetch_weather


def _greeting_for(target_date: date) -> str:
    return "Bonjour la famille."


def _json_default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def build_content(config: BoardConfig, target_date: date | None = None) -> tuple[BoardContent, str | None]:
    if target_date is None:
        target_date = config.now().date()

    messages = load_lines(config.data_dir / "kind_messages.txt")
    words = load_lines(config.data_dir / "easy_words.txt")
    reading_carousel = load_reading_carousel(config.data_dir / "reading_carousel.md")

    family_message = pick_rotating_item(messages, target_date)
    practice_words = pick_practice_words(words, target_date)
    weather = fetch_weather(config, target_date=target_date)
    reading = pick_carousel_reading(reading_carousel, target_date)
    reading_error: str | None = None

    content = BoardContent(
        render_date=target_date,
        greeting=_greeting_for(target_date),
        location_name=config.location_name,
        weather=weather,
        family_message=family_message,
        practice_words=practice_words,
        reading=reading,
    )
    return content, reading_error


def generate_board(config: BoardConfig, target_date: date | None = None) -> tuple[Path, Path]:
    content, reading_error = build_content(config, target_date=target_date)
    target_date = content.render_date

    config.output_dir.mkdir(parents=True, exist_ok=True)
    latest_image = config.output_dir / "latest.png"
    latest_manifest = config.output_dir / "latest.json"
    dated_image_name = f"board-{target_date.isoformat()}.png"
    dated_manifest_name = f"board-{target_date.isoformat()}.json"
    dated_image = config.output_dir / dated_image_name
    dated_manifest = config.output_dir / dated_manifest_name

    render_board(content, config, latest_image)
    copy2(latest_image, dated_image)

    dated_board_url = config.board_url.replace("/latest.png", f"/{dated_image_name}")
    dated_manifest_url = config.board_url.replace("/latest.png", f"/{dated_manifest_name}")

    manifest = {
        "render_date": target_date.isoformat(),
        "location_name": config.location_name,
        "board_url": config.board_url,
        "latest_board_url": config.board_url,
        "dated_board_filename": dated_image_name,
        "dated_board_url": dated_board_url,
        "dated_manifest_filename": dated_manifest_name,
        "dated_manifest_url": dated_manifest_url,
        "reading_error": reading_error,
        "content": asdict(content),
    }
    latest_manifest.write_text(json.dumps(manifest, indent=2, default=_json_default), encoding="utf-8")
    dated_manifest.write_text(json.dumps(manifest, indent=2, default=_json_default), encoding="utf-8")
    return latest_image, latest_manifest
