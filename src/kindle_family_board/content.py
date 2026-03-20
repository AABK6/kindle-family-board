from __future__ import annotations

import hashlib
import random
from datetime import date
from pathlib import Path

from .models import ReadingSnippet


CAROUSEL_EPOCH = date(2026, 1, 1)


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


def load_reading_carousel(path: Path) -> list[ReadingSnippet]:
    readings: list[ReadingSnippet] = []
    seen: set[tuple[str, str, str]] = set()

    current_kind: str | None = None
    current_title: str | None = None
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_kind
        nonlocal current_title
        nonlocal current_body_lines

        if current_kind is None or current_title is None:
            return

        body = " ".join(line.strip() for line in current_body_lines if line.strip())
        if not body:
            raise ValueError(f"Missing body for carousel entry {current_title!r} in {path}")

        key = (current_kind, current_title.casefold(), body.casefold())
        if key not in seen:
            readings.append(
                ReadingSnippet(
                    kind=current_kind,
                    title=current_title,
                    body=body,
                    source="carousel",
                )
            )
            seen.add(key)

        current_kind = None
        current_title = None
        current_body_lines = []

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if not line.startswith("## "):
                continue
            flush_current()
            header = line[3:]
            if "|" not in header:
                raise ValueError(f"Invalid carousel header at {path}:{lineno}: {line}")
            kind, title = (part.strip() for part in header.split("|", 1))
            if not kind or not title:
                raise ValueError(f"Invalid carousel header at {path}:{lineno}: {line}")
            current_kind = kind.lower()
            current_title = title
            current_body_lines = []
            continue

        if current_kind is None:
            raise ValueError(f"Body text found before any carousel header at {path}:{lineno}")
        current_body_lines.append(raw_line.rstrip())

    flush_current()
    if not readings:
        raise ValueError(f"No carousel readings in {path}")
    return readings


def _carousel_order(length: int, cycle: int, *, avoid_first: int | None = None) -> list[int]:
    if length <= 0:
        raise ValueError("Carousel length must be positive.")

    order = list(range(length))
    seed = hashlib.sha256(f"reading-carousel:{cycle}".encode("utf-8")).hexdigest()
    random.Random(seed).shuffle(order)

    if avoid_first is not None and length > 1 and order[0] == avoid_first:
        for index in range(1, length):
            if order[index] != avoid_first:
                order[0], order[index] = order[index], order[0]
                break
    return order


def pick_carousel_reading(readings: list[ReadingSnippet], target_date: date) -> ReadingSnippet:
    if not readings:
        raise ValueError("Need at least one carousel reading.")

    day_offset = target_date.toordinal() - CAROUSEL_EPOCH.toordinal()
    cycle, position = divmod(day_offset, len(readings))

    avoid_first: int | None = None
    if len(readings) > 1:
        previous_order = _carousel_order(len(readings), cycle - 1)
        avoid_first = previous_order[-1]

    order = _carousel_order(len(readings), cycle, avoid_first=avoid_first)
    reading = readings[order[position]]
    return ReadingSnippet(
        kind=reading.kind,
        title=reading.title,
        body=reading.body,
        source=reading.source,
    )
