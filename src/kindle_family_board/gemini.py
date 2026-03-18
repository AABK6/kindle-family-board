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
            "Ecris en francais un tres court texte a lire pour un enfant de 9 ans.",
            "Renvoie uniquement du JSON valide conforme au schema fourni.",
            "Le ton doit etre chaleureux, leger, familial et facile a lire a voix haute.",
            "Prefere nettement une blague courte et drole.",
            "N'ecris une micro-histoire que si tu ne trouves vraiment pas de bonne blague.",
            "Utilise 30 a 55 mots pour le corps du texte.",
            "Le titre doit rester tres court: 1 a 4 mots.",
            "Utilise des phrases courtes et un vocabulaire simple.",
            "Le texte doit tenir dans une carte Kindle e-ink de 600x800.",
            "N'utilise pas de markdown, de puces, de listes ou d'emojis.",
            f"Date: {target_date.isoformat()}",
            f"Lieu: {location_name}",
            f"Message du jour pour la famille: {family_message}",
            f"Mots du jour pour le plus jeune: {practice_words[0]}, {practice_words[1]}",
            (
                f"Meteo: maintenant {weather.current_condition} {weather.current_temperature_c:.0f}C, "
                f"matin {weather.morning.condition} {weather.morning.temperature_c:.0f}C, "
                f"apres-midi {weather.afternoon.condition} {weather.afternoon.temperature_c:.0f}C"
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
