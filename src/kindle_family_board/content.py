from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import ReadingSnippet


def load_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    if not lines:
        raise ValueError(f"No usable lines in {path}")
    return lines


def pick_rotating_item(items: list[str], target_date: date) -> str:
    index = target_date.toordinal() % len(items)
    return items[index]


def pick_practice_words(words: list[str], target_date: date, count: int = 2) -> tuple[str, str]:
    if len(words) < count:
        raise ValueError("Need at least two words in the word bank.")

    base_index = (target_date.toordinal() * 7) % len(words)
    selected = [words[(base_index + step * 17) % len(words)] for step in range(count)]
    if selected[0] == selected[1]:
        selected[1] = words[(base_index + 1) % len(words)]
    return selected[0], selected[1]


def load_fallback_readings(path: Path) -> list[ReadingSnippet]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    readings: list[ReadingSnippet] = []
    for item in payload:
        readings.append(
            ReadingSnippet(
                kind=item["kind"],
                title=item["title"],
                body=item["body"],
                source="fallback",
            )
        )
    if not readings:
        raise ValueError(f"No fallback readings in {path}")
    return readings


def pick_fallback_reading(readings: list[ReadingSnippet], target_date: date) -> ReadingSnippet:
    reading = readings[target_date.toordinal() % len(readings)]
    return ReadingSnippet(
        kind=reading.kind,
        title=reading.title,
        body=reading.body,
        source=reading.source,
    )

