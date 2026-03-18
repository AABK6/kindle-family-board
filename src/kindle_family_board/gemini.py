from __future__ import annotations

import json
from datetime import date

from .config import BoardConfig
from .models import ReadingSnippet, WeatherSnapshot


READING_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["story", "joke"]},
        "title": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["kind", "title", "body"],
    "additionalProperties": False,
}


def build_prompt(
    target_date: date,
    location_name: str,
    family_message: str,
    practice_words: tuple[str, str],
    weather: WeatherSnapshot,
) -> str:
    return "\n".join(
        [
            "Write one very short reading item for a 9-year-old child.",
            "Return only valid JSON following the provided schema.",
            "The tone must be warm, light, family-safe, and easy to read aloud.",
            "Choose either a tiny joke or a tiny micro-story.",
            "Use 30 to 55 words for the body.",
            "Keep the title very short: 1 to 4 words.",
            "Use short sentences and simple vocabulary.",
            "Keep it compact enough to fit inside a 600x800 Kindle e-ink card.",
            "Do not use markdown, bullets, lists, or emojis.",
            f"Date: {target_date.isoformat()}",
            f"Location: {location_name}",
            f"Family message of the day: {family_message}",
            f"Words of the day for the younger child: {practice_words[0]}, {practice_words[1]}",
            (
                f"Weather summary: now {weather.current_condition} {weather.current_temperature_c:.0f}C, "
                f"morning {weather.morning.condition} {weather.morning.temperature_c:.0f}C, "
                f"afternoon {weather.afternoon.condition} {weather.afternoon.temperature_c:.0f}C"
            ),
        ]
    )


def generate_reading(
    config: BoardConfig,
    target_date: date,
    family_message: str,
    practice_words: tuple[str, str],
    weather: WeatherSnapshot,
) -> ReadingSnippet:
    if not config.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed.") from exc

    client = genai.Client(api_key=config.gemini_api_key)
    response = client.models.generate_content(
        model=config.gemini_model,
        contents=build_prompt(
            target_date=target_date,
            location_name=config.location_name,
            family_message=family_message,
            practice_words=practice_words,
            weather=weather,
        ),
        config={
            "response_mime_type": "application/json",
            "response_json_schema": READING_SCHEMA,
        },
    )

    payload = json.loads(response.text)
    return ReadingSnippet(
        kind=str(payload["kind"]).strip().lower(),
        title=str(payload["title"]).strip(),
        body=str(payload["body"]).strip(),
        source=f"gemini:{config.gemini_model}",
    )
