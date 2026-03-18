from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .config import BoardConfig
from .models import BoardContent

WEEKDAY_NAMES = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche",
}

MONTH_NAMES = {
    1: "janvier",
    2: "fevrier",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "aout",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "decembre",
}


def _existing(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def load_font(size: int, *, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windows = Path("C:/Windows/Fonts")
    candidates = []
    if serif and bold:
        candidates.extend([windows / "georgiab.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")])
    elif serif:
        candidates.extend([windows / "georgia.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")])
    elif bold:
        candidates.extend(
            [windows / "arialbd.ttf", windows / "calibrib.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]
        )
    else:
        candidates.extend([windows / "arial.ttf", windows / "calibri.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")])

    font_path = _existing(candidates)
    if font_path is None:
        return ImageFont.load_default()
    return ImageFont.truetype(str(font_path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    x: int,
    y: int,
    max_width: int,
    max_height: int,
    font: ImageFont.ImageFont,
    fill: int = 0,
    line_gap: int = 6,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    if not lines:
        return y

    _, _, _, sample_height = draw.textbbox((0, 0), "Ay", font=font)
    line_height = sample_height + line_gap
    available_lines = max(1, max_height // max(line_height, 1))

    visible_lines = lines[:available_lines]
    if len(lines) > available_lines:
        last = visible_lines[-1]
        ellipsis = "..."
        while last and draw.textlength(f"{last}{ellipsis}", font=font) > max_width:
            last = last[:-1]
        visible_lines[-1] = f"{last.rstrip()}{ellipsis}"

    cursor_y = y
    for line in visible_lines:
        draw.text((x, cursor_y), line, font=font, fill=fill)
        cursor_y += line_height
    return cursor_y


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: int = 245, outline: int = 0) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=2)


def _polar_points(cx: float, cy: float, outer_radius: float, inner_radius: float, count: int, rotation_deg: float = -90) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(count * 2):
        radius = outer_radius if index % 2 == 0 else inner_radius
        angle = math.radians(rotation_deg + (360 / (count * 2)) * index)
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def draw_badge_base(draw: ImageDraw.ImageDraw, center: tuple[int, int], style: str, radius: int = 31) -> None:
    cx, cy = center
    left, top, right, bottom = cx - radius, cy - radius, cx + radius, cy + radius

    if style == "burst":
        points = _polar_points(cx, cy, radius, radius * 0.78, 10)
        draw.polygon(points, fill=250, outline=0)
        draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=255, outline=0, width=2)
        return

    if style == "ticket":
        points = [
            (cx - 26, cy - 12),
            (cx - 10, cy - 28),
            (cx + 18, cy - 26),
            (cx + 30, cy - 4),
            (cx + 18, cy + 24),
            (cx - 14, cy + 28),
            (cx - 30, cy + 6),
        ]
        draw.polygon(points, fill=252, outline=0)
        draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=255, outline=0, width=2)
        return

    draw.ellipse((left, top, right, bottom), fill=255, outline=0, width=3)
    draw.arc((left - 6, top - 6, right + 8, bottom + 8), start=210, end=25, fill=0, width=2)
    draw.ellipse((right - 8, cy - 19, right + 3, cy - 8), fill=0)


def draw_cloud(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: float) -> None:
    cx, cy = center
    draw.ellipse((cx - 18 * scale, cy - 6 * scale, cx + 18 * scale, cy + 12 * scale), outline=0, width=2)
    draw.ellipse((cx - 24 * scale, cy - 2 * scale, cx - 4 * scale, cy + 14 * scale), outline=0, width=2)
    draw.ellipse((cx - 2 * scale, cy - 11 * scale, cx + 21 * scale, cy + 10 * scale), outline=0, width=2)
    draw.line((cx - 20 * scale, cy + 10 * scale, cx + 18 * scale, cy + 10 * scale), fill=255, width=max(1, int(3 * scale)))
    draw.line((cx - 20 * scale, cy + 11 * scale, cx + 18 * scale, cy + 11 * scale), fill=0, width=2)


def draw_sun(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int) -> None:
    cx, cy = center
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=0, width=2)
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        x1 = cx + math.cos(angle) * (radius + 5)
        y1 = cy + math.sin(angle) * (radius + 5)
        x2 = cx + math.cos(angle) * (radius + 11)
        y2 = cy + math.sin(angle) * (radius + 11)
        draw.line((x1, y1, x2, y2), fill=0, width=2)


def draw_raindrops(draw: ImageDraw.ImageDraw, start: tuple[int, int], spacing: int) -> None:
    x, y = start
    for offset in (-spacing, 0, spacing):
        draw.line((x + offset, y, x + offset - 2, y + 8), fill=0, width=2)


def draw_snow(draw: ImageDraw.ImageDraw, center: tuple[int, int], spacing: int) -> None:
    cx, cy = center
    for offset in (-spacing, spacing):
        x = cx + offset
        draw.line((x - 3, cy, x + 3, cy), fill=0, width=1)
        draw.line((x, cy - 3, x, cy + 3), fill=0, width=1)
        draw.line((x - 2, cy - 2, x + 2, cy + 2), fill=0, width=1)
        draw.line((x - 2, cy + 2, x + 2, cy - 2), fill=0, width=1)


def draw_lightning(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    cx, cy = center
    draw.line((cx, cy - 10, cx - 5, cy + 2, cx + 1, cy + 2, cx - 4, cy + 14), fill=0, width=3, joint="curve")


def draw_condition_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], weather_code: int, *, scale: float = 1.0) -> None:
    if weather_code in {0, 1}:
        draw_sun(draw, center, max(8, int(10 * scale)))
        return

    if weather_code == 2:
        draw_sun(draw, (center[0] - int(10 * scale), center[1] - int(8 * scale)), max(7, int(8 * scale)))
        draw_cloud(draw, (center[0] + int(3 * scale), center[1] + int(3 * scale)), 0.75 * scale)
        return

    if weather_code in {3, 45, 48}:
        draw_cloud(draw, center, 0.95 * scale)
        return

    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        draw_cloud(draw, (center[0], center[1] - int(3 * scale)), 0.95 * scale)
        draw_raindrops(draw, (center[0], center[1] + int(14 * scale)), max(5, int(7 * scale)))
        return

    if weather_code in {71, 73, 75, 77, 85, 86}:
        draw_cloud(draw, (center[0], center[1] - int(3 * scale)), 0.95 * scale)
        draw_snow(draw, (center[0], center[1] + int(14 * scale)), max(5, int(7 * scale)))
        return

    if weather_code in {95, 96, 99}:
        draw_cloud(draw, (center[0], center[1] - int(4 * scale)), 0.95 * scale)
        draw_lightning(draw, (center[0] + int(2 * scale), center[1] + int(11 * scale)))
        return

    draw_cloud(draw, center, 0.95 * scale)


def draw_thermometer(draw: ImageDraw.ImageDraw, x: int, y: int, *, scale: float = 1.0) -> None:
    bulb_radius = int(4 * scale)
    tube_width = max(2, int(3 * scale))
    draw.ellipse((x - bulb_radius, y + 8 - bulb_radius, x + bulb_radius, y + 8 + bulb_radius), outline=0, width=2)
    draw.line((x, y - 9, x, y + 6), fill=0, width=tube_width)
    draw.ellipse((x - bulb_radius + 1, y + 8 - bulb_radius + 1, x + bulb_radius - 1, y + 8 + bulb_radius - 1), fill=255, outline=0)
    draw.line((x, y - 7, x, y + 8), fill=0, width=tube_width)


def draw_drop(draw: ImageDraw.ImageDraw, x: int, y: int, *, scale: float = 1.0) -> None:
    points = [
        (x, y - 10 * scale),
        (x + 6 * scale, y),
        (x + 3 * scale, y + 8 * scale),
        (x - 3 * scale, y + 8 * scale),
        (x - 6 * scale, y),
    ]
    draw.polygon(points, outline=0, fill=255)
    draw.line(points + [points[0]], fill=0, width=2)


def draw_heart(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: float = 1.0) -> None:
    cx, cy = center
    draw.ellipse((cx - 16 * scale, cy - 10 * scale, cx - 1 * scale, cy + 6 * scale), outline=0, width=2)
    draw.ellipse((cx + 1 * scale, cy - 10 * scale, cx + 16 * scale, cy + 6 * scale), outline=0, width=2)
    draw.line((cx - 14 * scale, cy + 2 * scale, cx, cy + 20 * scale, cx + 14 * scale, cy + 2 * scale), fill=0, width=2, joint="curve")


def draw_sparkle(draw: ImageDraw.ImageDraw, center: tuple[int, int], size: int = 5) -> None:
    cx, cy = center
    draw.line((cx - size, cy, cx + size, cy), fill=0, width=1)
    draw.line((cx, cy - size, cx, cy + size), fill=0, width=1)
    draw.line((cx - size + 1, cy - size + 1, cx + size - 1, cy + size - 1), fill=0, width=1)
    draw.line((cx - size + 1, cy + size - 1, cx + size - 1, cy - size + 1), fill=0, width=1)


def draw_letter_tiles(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    cx, cy = center
    left_box = (cx - 24, cy - 18, cx + 2, cy + 8)
    right_box = (cx - 2, cy - 8, cx + 24, cy + 18)
    draw.rounded_rectangle(left_box, radius=6, fill=255, outline=0, width=2)
    draw.rounded_rectangle(right_box, radius=6, fill=255, outline=0, width=2)
    font = load_font(16, bold=True)
    draw.text((left_box[0] + 7, left_box[1] + 4), "A", font=font, fill=0)
    draw.text((right_box[0] + 8, right_box[1] + 4), "B", font=font, fill=0)


def draw_open_book(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    cx, cy = center
    left = (cx - 24, cy - 14, cx - 2, cy + 16)
    right = (cx + 2, cy - 14, cx + 24, cy + 16)
    draw.rounded_rectangle(left, radius=5, fill=255, outline=0, width=2)
    draw.rounded_rectangle(right, radius=5, fill=255, outline=0, width=2)
    draw.line((cx, cy - 14, cx, cy + 16), fill=0, width=2)
    draw.line((cx - 16, cy - 4, cx - 6, cy - 1), fill=0, width=1)
    draw.line((cx + 6, cy - 1, cx + 16, cy - 4), fill=0, width=1)


def draw_badge_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], icon_name: str) -> None:
    if icon_name == "weather":
        draw_sun(draw, (center[0] - 9, center[1] - 7), 7)
        draw_cloud(draw, (center[0] + 4, center[1] + 4), 0.6)
        return
    if icon_name == "note":
        draw_heart(draw, (center[0], center[1] + 2), 0.75)
        draw_sparkle(draw, (center[0] + 17, center[1] - 12), 4)
        return
    if icon_name == "words":
        draw_letter_tiles(draw, center)
        return
    if icon_name == "story":
        draw_open_book(draw, (center[0], center[1] + 1))
        draw_sparkle(draw, (center[0] + 17, center[1] - 14), 4)
        return


def draw_corner_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], icon_name: str, style: str) -> None:
    center = (box[0] + 36, box[1] + 8)
    draw_badge_base(draw, center, style=style)
    draw_badge_icon(draw, center, icon_name=icon_name)


def draw_weather_period(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    label: str,
    weather_code: int,
    temperature_c: float,
    precipitation_probability: int | None,
    label_font: ImageFont.ImageFont,
    value_font: ImageFont.ImageFont,
    small_font: ImageFont.ImageFont,
) -> None:
    left, top, right, bottom = box
    center_x = (left + right) // 2
    draw.text((left, top), label, font=label_font, fill=0)
    draw_condition_icon(draw, (center_x, top + 42), weather_code, scale=1.0)

    thermo_x = left + 16
    temp_y = top + 76
    draw_thermometer(draw, thermo_x, temp_y, scale=1.0)
    draw.text((thermo_x + 14, temp_y - 12), f"{temperature_c:.0f}C", font=value_font, fill=0)

    drop_x = left + 16
    rain_y = top + 106
    draw_drop(draw, drop_x, rain_y - 1, scale=0.85)
    rain_value = precipitation_probability if precipitation_probability is not None else 0
    draw.text((drop_x + 14, rain_y - 12), f"{rain_value}%", font=small_font, fill=0)


def draw_word_pill(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
) -> None:
    draw.rounded_rectangle(box, radius=14, fill=255, outline=0, width=2)
    text_width = draw.textlength(text, font=font)
    _, _, _, text_height = draw.textbbox((0, 0), text, font=font)
    x = box[0] + ((box[2] - box[0]) - text_width) / 2
    y = box[1] + ((box[3] - box[1]) - text_height) / 2 - 2
    draw.text((x, y), text, font=font, fill=0)


def format_french_date(content: BoardContent) -> str:
    render_date = content.render_date
    weekday = WEEKDAY_NAMES[render_date.weekday()]
    month = MONTH_NAMES[render_date.month]
    return f"{weekday} {render_date.day} {month}"


def render_board(content: BoardContent, config: BoardConfig, output_path: Path) -> Path:
    width = config.image_width
    height = config.image_height
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)

    title_font = load_font(38, bold=True, serif=True)
    date_font = load_font(18)
    note_font = load_font(21)
    word_font = load_font(26, bold=True)
    reading_title_font = load_font(24, bold=True, serif=True)
    reading_body_font = load_font(19)
    weather_label_font = load_font(16, bold=True)
    weather_value_font = load_font(24, bold=True)
    weather_small_font = load_font(20)

    margin = 26
    card_gap = 16
    y = 28

    draw.text((margin, y), content.greeting, font=title_font, fill=0)
    y += 50
    draw.text((margin, y), format_french_date(content), font=date_font, fill=0)
    y += 14
    draw.line((margin, y + 14, width - margin, y + 14), fill=0, width=2)
    y += 32

    weather_box = (margin, y, width - margin, y + 138)
    draw_card(draw, weather_box, fill=246)
    draw_corner_badge(draw, weather_box, "weather", config.icon_style)
    divider_x = (weather_box[0] + weather_box[2]) // 2 + 10
    draw.line((divider_x, weather_box[1] + 28, divider_x, weather_box[3] - 18), fill=210, width=2)

    left_period_box = (weather_box[0] + 92, weather_box[1] + 20, divider_x - 20, weather_box[3] - 14)
    right_period_box = (divider_x + 22, weather_box[1] + 20, weather_box[2] - 20, weather_box[3] - 14)
    draw_weather_period(
        draw,
        box=left_period_box,
        label=content.weather.morning.label,
        weather_code=content.weather.morning.weather_code,
        temperature_c=content.weather.morning.temperature_c,
        precipitation_probability=content.weather.morning.precipitation_probability,
        label_font=weather_label_font,
        value_font=weather_value_font,
        small_font=weather_small_font,
    )
    draw_weather_period(
        draw,
        box=right_period_box,
        label=content.weather.afternoon.label,
        weather_code=content.weather.afternoon.weather_code,
        temperature_c=content.weather.afternoon.temperature_c,
        precipitation_probability=content.weather.afternoon.precipitation_probability,
        label_font=weather_label_font,
        value_font=weather_value_font,
        small_font=weather_small_font,
    )
    y = weather_box[3] + card_gap

    message_box = (margin, y, width - margin, y + 114)
    draw_card(draw, message_box, fill=248)
    draw_corner_badge(draw, message_box, "note", config.icon_style)
    draw_text_block(
        draw,
        text=content.family_message,
        x=message_box[0] + 84,
        y=message_box[1] + 34,
        max_width=message_box[2] - message_box[0] - 102,
        max_height=64,
        font=note_font,
        line_gap=7,
    )
    y = message_box[3] + card_gap

    words_box = (margin, y, width - margin, y + 100)
    draw_card(draw, words_box, fill=245)
    draw_corner_badge(draw, words_box, "words", config.icon_style)
    pill_top = words_box[1] + 28
    left_pill = (words_box[0] + 96, pill_top, words_box[0] + 288, pill_top + 44)
    right_pill = (words_box[0] + 308, pill_top, words_box[2] - 18, pill_top + 44)
    draw_word_pill(draw, box=left_pill, text=content.practice_words[0], font=word_font)
    draw_word_pill(draw, box=right_pill, text=content.practice_words[1], font=word_font)
    y = words_box[3] + card_gap

    reading_box = (margin, y, width - margin, height - 26)
    draw_card(draw, reading_box, fill=246)
    draw_corner_badge(draw, reading_box, "story", config.icon_style)
    title_bottom = draw_text_block(
        draw,
        text=content.reading.title,
        x=reading_box[0] + 88,
        y=reading_box[1] + 30,
        max_width=reading_box[2] - reading_box[0] - 112,
        max_height=66,
        font=reading_title_font,
        line_gap=6,
    )
    draw_text_block(
        draw,
        text=content.reading.body,
        x=reading_box[0] + 32,
        y=title_bottom + 10,
        max_width=reading_box[2] - reading_box[0] - 64,
        max_height=reading_box[3] - title_bottom - 34,
        font=reading_body_font,
        line_gap=7,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path
