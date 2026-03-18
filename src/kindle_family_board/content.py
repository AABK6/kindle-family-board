from __future__ import annotations

import hashlib
import json
import random
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


def _daily_rng(namespace: str, target_date: date) -> random.Random:
    seed = hashlib.sha256(f"{namespace}:{target_date.isoformat()}".encode("utf-8")).hexdigest()
    return random.Random(seed)


def pick_rotating_item(items: list[str], target_date: date) -> str:
    rng = _daily_rng("family-message", target_date)
    return rng.choice(items)


def pick_practice_words(words: list[str], target_date: date, count: int = 2) -> tuple[str, str]:
    if len(words) < count:
        raise ValueError("Need at least two words in the word bank.")

    rng = _daily_rng("practice-words", target_date)
    selected = rng.sample(words, count)
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
    rng = _daily_rng("fallback-reading", target_date)
    reading = rng.choice(readings)
    return ReadingSnippet(
        kind=reading.kind,
        title=reading.title,
        body=reading.body,
        source=reading.source,
    )
