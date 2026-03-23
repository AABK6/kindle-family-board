from __future__ import annotations

import math
from dataclasses import dataclass
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


@dataclass(frozen=True)
class TextBlockMetrics:
    line_height: int
    available_lines: int
    total_lines: int
    visible_lines: list[str]
    truncated: bool


@dataclass(frozen=True)
class LayoutVariant:
    name: str
    weather_height: int
    message_height: int
    words_height: int
    weather_mode: str
    weather_label_size: int
    weather_value_size: int
    weather_small_size: int
    note_font_size: int
    note_line_gap: int
    reading_title_size: int
    reading_title_gap: int
    reading_body_size: int
    reading_body_gap: int
    message_text_top: int
    message_text_left: int
    message_text_right: int
    words_pill_top: int
    words_pill_height: int


LAYOUT_VARIANTS: dict[str, LayoutVariant] = {
    "baseline": LayoutVariant(
        name="baseline",
        weather_height=138,
        message_height=114,
        words_height=100,
        weather_mode="stacked",
        weather_label_size=16,
        weather_value_size=24,
        weather_small_size=20,
        note_font_size=21,
        note_line_gap=7,
        reading_title_size=24,
        reading_title_gap=6,
        reading_body_size=19,
        reading_body_gap=7,
        message_text_top=34,
        message_text_left=92,
        message_text_right=108,
        words_pill_top=28,
        words_pill_height=44,
    ),
    "balanced": LayoutVariant(
        name="balanced",
        weather_height=118,
        message_height=102,
        words_height=94,
        weather_mode="paired",
        weather_label_size=15,
        weather_value_size=22,
        weather_small_size=15,
        note_font_size=20,
        note_line_gap=6,
        reading_title_size=24,
        reading_title_gap=5,
        reading_body_size=19,
        reading_body_gap=6,
        message_text_top=24,
        message_text_left=90,
        message_text_right=100,
        words_pill_top=23,
        words_pill_height=44,
    ),
    "story_plus": LayoutVariant(
        name="story_plus",
        weather_height=108,
        message_height=94,
        words_height=90,
        weather_mode="inline",
        weather_label_size=15,
        weather_value_size=20,
        weather_small_size=17,
        note_font_size=19,
        note_line_gap=6,
        reading_title_size=23,
        reading_title_gap=5,
        reading_body_size=18,
        reading_body_gap=6,
        message_text_top=24,
        message_text_left=86,
        message_text_right=96,
        words_pill_top=22,
        words_pill_height=40,
    ),
    "story_max": LayoutVariant(
        name="story_max",
        weather_height=102,
        message_height=90,
        words_height=86,
        weather_mode="inline",
        weather_label_size=14,
        weather_value_size=19,
        weather_small_size=16,
        note_font_size=18,
        note_line_gap=5,
        reading_title_size=22,
        reading_title_gap=4,
        reading_body_size=18,
        reading_body_gap=5,
        message_text_top=22,
        message_text_left=84,
        message_text_right=92,
        words_pill_top=21,
        words_pill_height=38,
    ),
}


def get_layout_variant(config: BoardConfig) -> LayoutVariant:
    return LAYOUT_VARIANTS.get(config.layout_variant, LAYOUT_VARIANTS["balanced"])


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


def measure_text_block(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    max_width: int,
    max_height: int,
    font: ImageFont.ImageFont,
    line_gap: int = 6,
) -> TextBlockMetrics:
    lines = wrap_text(draw, text, font, max_width)
    if not lines:
        return TextBlockMetrics(
            line_height=0,
            available_lines=0,
            total_lines=0,
            visible_lines=[],
            truncated=False,
        )

    _, _, _, sample_height = draw.textbbox((0, 0), "Ay", font=font)
    line_height = sample_height + line_gap
    available_lines = max(1, max_height // max(line_height, 1))
    visible_lines = lines[:available_lines]
    truncated = len(lines) > available_lines

    if truncated:
        last = visible_lines[-1]
        ellipsis = "..."
        while last and draw.textlength(f"{last}{ellipsis}", font=font) > max_width:
            last = last[:-1]
        visible_lines[-1] = f"{last.rstrip()}{ellipsis}"

    return TextBlockMetrics(
        line_height=line_height,
        available_lines=available_lines,
        total_lines=len(lines),
        visible_lines=visible_lines,
        truncated=truncated,
    )


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
) -> tuple[int, bool]:
    metrics = measure_text_block(
        draw,
        text=text,
        max_width=max_width,
        max_height=max_height,
        font=font,
        line_gap=line_gap,
    )
    if not metrics.visible_lines:
        return y, False

    cursor_y = y
    for line in metrics.visible_lines:
        draw.text((x, cursor_y), line, font=font, fill=fill)
        cursor_y += metrics.line_height
    return cursor_y, metrics.truncated


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


def _sv(value: float, scale: float) -> int:
    return int(round(value * scale))


def draw_badge_canvas(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> tuple[int, int]:
    left = box[0] - 6
    top = box[1] - 14
    right = left + 74
    bottom = top + 58
    draw.rounded_rectangle((left, top, right, bottom), radius=14, fill=255)
    return left, top


def draw_envelope_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    stroke = 2
    left = ox + 10
    top = oy + 18
    right = ox + 58
    bottom = oy + 52

    letter_left = left + 8
    letter_top = top - 10
    letter_right = right - 8
    letter_bottom = top + 8
    draw.rounded_rectangle((letter_left, letter_top, letter_right, letter_bottom), radius=4, outline=0, width=stroke)
    for row in range(3):
        y = letter_top + 5 + row * 4
        draw.line((letter_left + 6, y, letter_right - 6 - row * 4, y), fill=0, width=1)

    draw.rounded_rectangle((left, top, right, bottom), radius=4, outline=0, width=stroke)
    draw.line((left, top, (left + right) / 2, top + 15, right, top), fill=0, width=stroke)
    draw.line((left, bottom, (left + right) / 2, top + 22, right, bottom), fill=0, width=stroke)
    draw.line((left, top, left + 16, top + 14), fill=0, width=stroke)
    draw.line((right, top, right - 16, top + 14), fill=0, width=stroke)
    draw_heart(draw, ((left + right) // 2, top + 21), 0.58)


def draw_book_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    stroke = 2
    left_page = (ox + 10, oy + 19, ox + 34, oy + 49)
    right_page = (ox + 34, oy + 19, ox + 58, oy + 49)
    draw.rounded_rectangle(left_page, radius=5, outline=0, width=stroke)
    draw.rounded_rectangle(right_page, radius=5, outline=0, width=stroke)
    draw.line((ox + 34, oy + 19, ox + 34, oy + 49), fill=0, width=stroke)
    draw.arc((ox + 16, oy + 41, ox + 34, oy + 53), start=180, end=355, fill=0, width=1)
    draw.arc((ox + 34, oy + 41, ox + 52, oy + 53), start=185, end=360, fill=0, width=1)
    for row in range(4):
        y = oy + 25 + row * 5
        draw.arc((ox + 15, y - 2, ox + 31, y + 3), start=190, end=342, fill=0, width=1)
        draw.arc((ox + 37, y - 2, ox + 53, y + 3), start=198, end=350, fill=0, width=1)

    block_a = (ox + 46, oy + 34, ox + 65, oy + 53)
    block_c = (ox + 59, oy + 42, ox + 78, oy + 61)
    draw.polygon(
        [
            (block_a[0], block_a[1]),
            (block_a[2] - 5, block_a[1] - 3),
            (block_a[2], block_a[1] + 2),
            (block_a[2], block_a[3] - 4),
            (block_a[0] + 5, block_a[3]),
            (block_a[0], block_a[3] - 5),
        ],
        outline=0,
        fill=255,
    )
    draw.line((block_a[0], block_a[1], block_a[2] - 5, block_a[1] - 3, block_a[2], block_a[1] + 2, block_a[2], block_a[3] - 4, block_a[0] + 5, block_a[3], block_a[0], block_a[3] - 5, block_a[0], block_a[1]), fill=0, width=2)
    draw.line((block_a[0] + 5, block_a[3], block_a[0] + 5, block_a[1] + 5), fill=0, width=1)
    font = load_font(14, bold=True)
    draw.text((block_a[0] + 5, block_a[1] + 6), "A", font=font, fill=0)

    draw.polygon(
        [
            (block_c[0], block_c[1]),
            (block_c[2] - 5, block_c[1] - 3),
            (block_c[2], block_c[1] + 2),
            (block_c[2], block_c[3] - 4),
            (block_c[0] + 5, block_c[3]),
            (block_c[0], block_c[3] - 5),
        ],
        outline=0,
        fill=255,
    )
    draw.line((block_c[0], block_c[1], block_c[2] - 5, block_c[1] - 3, block_c[2], block_c[1] + 2, block_c[2], block_c[3] - 4, block_c[0] + 5, block_c[3], block_c[0], block_c[3] - 5, block_c[0], block_c[1]), fill=0, width=2)
    draw.line((block_c[0] + 5, block_c[3], block_c[0] + 5, block_c[1] + 5), fill=0, width=1)
    draw.text((block_c[0] + 5, block_c[1] + 6), "C", font=font, fill=0)


def draw_speech_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    bubble = (ox + 8, oy + 12, ox + 62, oy + 49)
    draw.rounded_rectangle(bubble, radius=10, outline=0, width=2)
    draw.polygon([(ox + 16, oy + 49), (ox + 13, oy + 61), (ox + 24, oy + 51)], fill=255, outline=0)
    draw.line((ox + 16, oy + 49, ox + 13, oy + 61, ox + 24, oy + 51), fill=0, width=2)

    for col in range(4):
        for row in range(5):
            x = ox + 42 + col * 5
            y = oy + 17 + row * 5
            draw.ellipse((x, y, x + 1, y + 1), fill=0)

    font = load_font(12, bold=True)
    draw.text((ox + 17, oy + 17), "HA", font=font, fill=0, stroke_width=1, stroke_fill=255)
    draw.text((ox + 17, oy + 30), "HA", font=font, fill=0, stroke_width=1, stroke_fill=255)

    face_center = (ox + 59, oy + 48)
    draw.ellipse((face_center[0] - 10, face_center[1] - 10, face_center[0] + 10, face_center[1] + 10), outline=0, width=2)
    draw.ellipse((face_center[0] - 5, face_center[1] - 3, face_center[0] - 3, face_center[1] - 1), fill=0)
    draw.ellipse((face_center[0] + 3, face_center[1] - 3, face_center[0] + 5, face_center[1] - 1), fill=0)
    draw.arc((face_center[0] - 6, face_center[1] - 1, face_center[0] + 6, face_center[1] + 7), start=15, end=165, fill=0, width=2)


def draw_weather_badge_scene(draw: ImageDraw.ImageDraw, origin: tuple[int, int], weather_icon_style: str) -> None:
    ox, oy = origin
    draw_sun(draw, (ox + 16, oy + 24), 8)
    draw_cloud(draw, (ox + 43, oy + 28), 0.72)
    for offset in (-10, 0, 10):
        draw_precip_drop(draw, (ox + 43 + offset, oy + 46), scale=0.5)


def draw_badge_icon_illustrated(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    icon_name: str,
    *,
    weather_icon_style: str,
) -> None:
    origin = draw_badge_canvas(draw, box)
    if icon_name == "weather":
        draw_weather_badge_scene(draw, origin, weather_icon_style)
        return
    if icon_name == "note":
        draw_envelope_badge(draw, origin)
        return
    if icon_name == "words":
        draw_book_badge(draw, origin)
        return
    if icon_name == "story":
        draw_speech_badge(draw, origin)
        return


def draw_cloud(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: float) -> None:
    cx, cy = center
    stroke = max(2, _sv(2.3, scale))
    draw.arc(
        (cx - _sv(30, scale), cy - _sv(1, scale), cx - _sv(4, scale), cy + _sv(21, scale)),
        start=180,
        end=322,
        fill=0,
        width=stroke,
    )
    draw.arc(
        (cx - _sv(12, scale), cy - _sv(16, scale), cx + _sv(18, scale), cy + _sv(14, scale)),
        start=180,
        end=360,
        fill=0,
        width=stroke,
    )
    draw.arc(
        (cx + _sv(5, scale), cy - _sv(9, scale), cx + _sv(30, scale), cy + _sv(16, scale)),
        start=218,
        end=360,
        fill=0,
        width=stroke,
    )
    baseline_y = cy + _sv(12, scale)
    draw.line((cx - _sv(23, scale), baseline_y, cx + _sv(24, scale), baseline_y), fill=0, width=stroke)


def draw_sun(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int) -> None:
    cx, cy = center
    stroke = max(2, radius // 5)
    ray_inner = radius + max(5, radius // 2)
    ray_outer = radius + max(10, radius)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=0, width=stroke)
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        x1 = cx + math.cos(angle) * ray_inner
        y1 = cy + math.sin(angle) * ray_inner
        x2 = cx + math.cos(angle) * ray_outer
        y2 = cy + math.sin(angle) * ray_outer
        draw.line((x1, y1, x2, y2), fill=0, width=stroke)


def draw_precip_drop(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    points = [
        (cx, cy - _sv(8, scale)),
        (cx + _sv(5, scale), cy),
        (cx + _sv(3, scale), cy + _sv(8, scale)),
        (cx - _sv(3, scale), cy + _sv(8, scale)),
        (cx - _sv(5, scale), cy),
    ]
    draw.polygon(points, fill=0)


def draw_rain(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud(draw, (cx, cy - _sv(8, scale)), 0.95 * scale)
    for offset in (-18, -6, 6, 18):
        draw_precip_drop(draw, (cx + _sv(offset, scale), cy + _sv(20, scale)), scale=0.85 * scale)


def draw_showers(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    stroke = max(2, _sv(2.2, scale))
    draw_cloud(draw, (cx, cy - _sv(8, scale)), 0.95 * scale)
    top_y = cy + _sv(12, scale)
    bottom_y = cy + _sv(25, scale)
    for offset in (-18, -8, 2, 12, 22):
        start_x = cx + _sv(offset, scale)
        draw.line((start_x, top_y, start_x - _sv(4, scale), bottom_y), fill=0, width=stroke)


def draw_lightning(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    points = [
        (cx + _sv(3, scale), cy - _sv(15, scale)),
        (cx - _sv(7, scale), cy + _sv(1, scale)),
        (cx + _sv(1, scale), cy + _sv(1, scale)),
        (cx - _sv(10, scale), cy + _sv(22, scale)),
        (cx + _sv(13, scale), cy - _sv(4, scale)),
        (cx + _sv(4, scale), cy - _sv(4, scale)),
    ]
    draw.polygon(points, fill=0)


def draw_storm(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud(draw, (cx, cy - _sv(8, scale)), 0.95 * scale)
    draw_lightning(draw, (cx + _sv(2, scale), cy + _sv(17, scale)), scale=0.9 * scale)


def draw_snowflake(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    radius = _sv(22, scale)
    stroke = max(2, _sv(2.0, scale))
    for angle_deg in range(0, 180, 30):
        angle = math.radians(angle_deg)
        dx = math.cos(angle) * radius
        dy = math.sin(angle) * radius
        x1 = cx - dx
        y1 = cy - dy
        x2 = cx + dx
        y2 = cy + dy
        draw.line((x1, y1, x2, y2), fill=0, width=stroke)

        for sign in (-1, 1):
            branch_x = cx + math.cos(angle) * radius * 0.58 * sign
            branch_y = cy + math.sin(angle) * radius * 0.58 * sign
            for branch_angle_deg in (angle_deg + 60, angle_deg - 60):
                branch_angle = math.radians(branch_angle_deg)
                bx = branch_x + math.cos(branch_angle) * radius * 0.24 * sign
                by = branch_y + math.sin(branch_angle) * radius * 0.24 * sign
                draw.line((branch_x, branch_y, bx, by), fill=0, width=max(1, stroke - 1))


def draw_wave_line(draw: ImageDraw.ImageDraw, left: int, y: int, *, scale: float = 1.0) -> None:
    segment = _sv(10, scale)
    amplitude = _sv(3.5, scale)
    stroke = max(2, _sv(1.8, scale))
    x = left
    for _ in range(4):
        draw.arc((x, y - amplitude, x + segment, y + amplitude), start=180, end=360, fill=0, width=stroke)
        x += segment
        draw.arc((x, y - amplitude, x + segment, y + amplitude), start=0, end=180, fill=0, width=stroke)
        x += segment


def draw_fog(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud(draw, (cx, cy - _sv(10, scale)), 0.95 * scale)
    left = cx - _sv(24, scale)
    for row in range(3):
        draw_wave_line(draw, left, cy + _sv(10 + row * 8, scale), scale=0.9 * scale)


def draw_condition_icon_classic(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    weather_code: int,
    *,
    scale: float = 1.0,
) -> None:
    if weather_code == 0:
        draw_sun(draw, center, max(8, int(10 * scale)))
        return

    if weather_code in {1, 2}:
        draw_sun(draw, (center[0] - _sv(14, scale), center[1] - _sv(10, scale)), max(8, _sv(10, scale)))
        draw_cloud(draw, (center[0] + _sv(5, scale), center[1] + _sv(4, scale)), 0.82 * scale)
        return

    if weather_code == 3:
        draw_cloud(draw, center, 0.95 * scale)
        return

    if weather_code in {45, 48}:
        draw_fog(draw, center, scale=0.95 * scale)
        return

    if weather_code in {51, 53, 55, 56, 57, 80, 81, 82}:
        draw_showers(draw, center, scale=0.95 * scale)
        return

    if weather_code in {61, 63, 65, 66, 67}:
        draw_rain(draw, center, scale=0.95 * scale)
        return

    if weather_code in {71, 73, 75, 77, 85, 86}:
        draw_snowflake(draw, center, scale=0.95 * scale)
        return

    if weather_code in {95, 96, 99}:
        draw_storm(draw, center, scale=0.95 * scale)
        return

    draw_cloud(draw, center, 0.95 * scale)


def draw_sun_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0, partial: bool = False) -> None:
    cx, cy = center
    radius = max(9, _sv(12, scale))
    stroke = max(2, _sv(2.4, scale))
    inner = radius + _sv(6, scale)
    outer = radius + _sv(15, scale)

    for angle_deg in range(0, 360, 45):
        if partial and 90 <= angle_deg <= 225:
            continue
        angle = math.radians(angle_deg)
        x1 = cx + math.cos(angle) * inner
        y1 = cy + math.sin(angle) * inner
        x2 = cx + math.cos(angle) * outer
        y2 = cy + math.sin(angle) * outer
        draw.line((x1, y1, x2, y2), fill=0, width=stroke)

    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=0, width=stroke)


def draw_cloud_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    stroke = max(2, _sv(2.5, scale))
    draw.arc(
        (cx - _sv(34, scale), cy - _sv(2, scale), cx - _sv(8, scale), cy + _sv(22, scale)),
        start=180,
        end=320,
        fill=0,
        width=stroke,
    )
    draw.arc(
        (cx - _sv(18, scale), cy - _sv(20, scale), cx + _sv(16, scale), cy + _sv(14, scale)),
        start=180,
        end=356,
        fill=0,
        width=stroke,
    )
    draw.arc(
        (cx + _sv(6, scale), cy - _sv(12, scale), cx + _sv(34, scale), cy + _sv(16, scale)),
        start=208,
        end=360,
        fill=0,
        width=stroke,
    )
    draw.line((cx - _sv(28, scale), cy + _sv(12, scale), cx + _sv(27, scale), cy + _sv(12, scale)), fill=0, width=stroke)


def draw_drop_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    points = [
        (cx, cy - _sv(9, scale)),
        (cx + _sv(5, scale), cy - _sv(1, scale)),
        (cx + _sv(4, scale), cy + _sv(8, scale)),
        (cx, cy + _sv(11, scale)),
        (cx - _sv(4, scale), cy + _sv(8, scale)),
        (cx - _sv(5, scale), cy - _sv(1, scale)),
    ]
    draw.polygon(points, fill=0)


def draw_rain_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud_refined(draw, (cx, cy - _sv(8, scale)), scale=scale)
    for offset in (-20, -7, 7, 20):
        draw_drop_refined(draw, (cx + _sv(offset, scale), cy + _sv(21, scale)), scale=0.9 * scale)


def draw_showers_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    stroke = max(2, _sv(2.2, scale))
    draw_cloud_refined(draw, (cx, cy - _sv(8, scale)), scale=scale)
    top_y = cy + _sv(11, scale)
    bottom_y = cy + _sv(28, scale)
    for offset in (-20, -10, 0, 10, 20):
        x = cx + _sv(offset, scale)
        draw.line((x, top_y, x - _sv(5, scale), bottom_y), fill=0, width=stroke)


def draw_lightning_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    points = [
        (cx + _sv(4, scale), cy - _sv(17, scale)),
        (cx - _sv(6, scale), cy + _sv(1, scale)),
        (cx + _sv(2, scale), cy + _sv(1, scale)),
        (cx - _sv(11, scale), cy + _sv(24, scale)),
        (cx + _sv(14, scale), cy - _sv(4, scale)),
        (cx + _sv(5, scale), cy - _sv(4, scale)),
    ]
    draw.polygon(points, fill=0)


def draw_storm_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud_refined(draw, (cx, cy - _sv(8, scale)), scale=scale)
    draw_lightning_refined(draw, (cx + _sv(2, scale), cy + _sv(17, scale)), scale=0.95 * scale)


def draw_snowflake_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    radius = _sv(23, scale)
    stroke = max(2, _sv(2.0, scale))
    for angle_deg in (0, 60, 120):
        angle = math.radians(angle_deg)
        dx = math.cos(angle) * radius
        dy = math.sin(angle) * radius
        x1 = cx - dx
        y1 = cy - dy
        x2 = cx + dx
        y2 = cy + dy
        draw.line((x1, y1, x2, y2), fill=0, width=stroke)

        for sign in (-1, 1):
            branch_x = cx + math.cos(angle) * radius * 0.58 * sign
            branch_y = cy + math.sin(angle) * radius * 0.58 * sign
            for branch_offset in (-35, 35):
                branch_angle = math.radians(angle_deg + branch_offset)
                bx = branch_x + math.cos(branch_angle) * radius * 0.22 * sign
                by = branch_y + math.sin(branch_angle) * radius * 0.22 * sign
                draw.line((branch_x, branch_y, bx, by), fill=0, width=max(1, stroke - 1))


def draw_wave_refined(draw: ImageDraw.ImageDraw, left: int, y: int, *, scale: float = 1.0) -> None:
    segment = _sv(11, scale)
    amplitude = _sv(3.5, scale)
    stroke = max(2, _sv(1.9, scale))
    x = left
    for _ in range(4):
        draw.arc((x, y - amplitude, x + segment, y + amplitude), start=180, end=360, fill=0, width=stroke)
        x += segment
        draw.arc((x, y - amplitude, x + segment, y + amplitude), start=0, end=180, fill=0, width=stroke)
        x += segment


def draw_fog_refined(draw: ImageDraw.ImageDraw, center: tuple[int, int], *, scale: float = 1.0) -> None:
    cx, cy = center
    draw_cloud_refined(draw, (cx, cy - _sv(12, scale)), scale=scale)
    left = cx - _sv(29, scale)
    for row in range(3):
        draw_wave_refined(draw, left, cy + _sv(10 + row * 8, scale), scale=0.95 * scale)


def draw_condition_icon_refined(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    weather_code: int,
    *,
    scale: float = 1.0,
) -> None:
    if weather_code == 0:
        draw_sun_refined(draw, center, scale=scale)
        return

    if weather_code in {1, 2}:
        draw_sun_refined(draw, (center[0] - _sv(16, scale), center[1] - _sv(12, scale)), scale=0.98 * scale, partial=True)
        draw_cloud_refined(draw, (center[0] + _sv(5, scale), center[1] + _sv(4, scale)), scale=0.9 * scale)
        return

    if weather_code == 3:
        draw_cloud_refined(draw, center, scale=scale)
        return

    if weather_code in {45, 48}:
        draw_fog_refined(draw, center, scale=scale)
        return

    if weather_code in {51, 53, 55, 56, 57, 80, 81, 82}:
        draw_showers_refined(draw, center, scale=scale)
        return

    if weather_code in {61, 63, 65, 66, 67}:
        draw_rain_refined(draw, center, scale=scale)
        return

    if weather_code in {71, 73, 75, 77, 85, 86}:
        draw_snowflake_refined(draw, center, scale=scale)
        return

    if weather_code in {95, 96, 99}:
        draw_storm_refined(draw, center, scale=scale)
        return

    draw_cloud_refined(draw, center, scale=scale)


def draw_condition_icon(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    weather_code: int,
    *,
    scale: float = 1.0,
    style: str = "refined",
) -> None:
    if style == "classic":
        draw_condition_icon_classic(draw, center, weather_code, scale=scale)
        return
    draw_condition_icon_refined(draw, center, weather_code, scale=scale)


def draw_thermometer(draw: ImageDraw.ImageDraw, x: int, y: int, *, scale: float = 1.0) -> None:
    bulb_radius = int(4 * scale)
    tube_width = max(2, int(3 * scale))
    draw.ellipse((x - bulb_radius, y + 8 - bulb_radius, x + bulb_radius, y + 8 + bulb_radius), outline=0, width=2)
    draw.line((x, y - 9, x, y + 6), fill=0, width=tube_width)
    draw.ellipse((x - bulb_radius + 1, y + 8 - bulb_radius + 1, x + bulb_radius - 1, y + 8 + bulb_radius - 1), fill=255, outline=0)
    draw.line((x, y - 7, x, y + 8), fill=0, width=tube_width)


def draw_drop(draw: ImageDraw.ImageDraw, x: int, y: int, *, scale: float = 1.0) -> None:
    stroke = max(2, _sv(1.8, scale))
    radius_x = _sv(5.0, scale)
    radius_y = _sv(6.0, scale)
    point_y = y - _sv(9.0, scale)
    ellipse_top = y - _sv(2.0, scale)
    ellipse_bottom = y + _sv(9.0, scale)

    draw.polygon(
        [
            (x, point_y),
            (x + radius_x - 1, ellipse_top + _sv(2.0, scale)),
            (x - radius_x + 1, ellipse_top + _sv(2.0, scale)),
        ],
        fill=255,
        outline=0,
    )
    draw.ellipse((x - radius_x, ellipse_top, x + radius_x, ellipse_bottom), fill=255, outline=0)
    draw.line((x, point_y, x + radius_x - 1, ellipse_top + _sv(2.0, scale)), fill=0, width=stroke)
    draw.line((x, point_y, x - radius_x + 1, ellipse_top + _sv(2.0, scale)), fill=0, width=stroke)
    draw.arc((x - radius_x, ellipse_top, x + radius_x, ellipse_bottom), start=18, end=162, fill=0, width=stroke)
    draw.arc((x - radius_x, ellipse_top, x + radius_x, ellipse_bottom), start=198, end=342, fill=0, width=stroke)


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


def draw_corner_badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    icon_name: str,
    style: str,
    *,
    weather_icon_style: str,
) -> None:
    if style == "legacy":
        center = (box[0] + 36, box[1] + 8)
        draw_badge_base(draw, center, style="burst")
        draw_badge_icon(draw, center, icon_name=icon_name)
        return
    draw_badge_icon_illustrated(draw, box, icon_name, weather_icon_style=weather_icon_style)


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
    weather_icon_style: str,
    mode: str,
) -> None:
    left, top, right, bottom = box
    rain_value = precipitation_probability if precipitation_probability is not None else 0
    temperature_text = f"{temperature_c:.0f}\N{DEGREE SIGN}C"

    if mode == "paired":
        draw.text((left, top), label, font=label_font, fill=0)

        icon_center = (left + 34, top + 49)
        draw_condition_icon(draw, icon_center, weather_code, scale=0.94, style=weather_icon_style)

        metrics_x = left + 82
        temp_y = top + 23
        draw.text((metrics_x, temp_y), temperature_text, font=value_font, fill=0)

        drop_x = metrics_x + 6
        drop_y = top + 58
        draw_drop(draw, drop_x, drop_y, scale=0.62)
        draw.text((metrics_x + 18, top + 48), f"{rain_value}%", font=small_font, fill=0)
        return

    if mode == "inline":
        draw.text((left, top), label, font=label_font, fill=0)
        row_y = top + 34
        icon_center = (left + 21, row_y + 6)
        draw_condition_icon(draw, icon_center, weather_code, scale=0.64, style=weather_icon_style)

        thermo_x = left + 48
        draw_thermometer(draw, thermo_x, row_y + 6, scale=0.78)
        draw.text((thermo_x + 12, row_y - 6), temperature_text, font=value_font, fill=0)

        temp_text_width = draw.textlength(temperature_text, font=value_font)
        drop_x = min(int(thermo_x + 14 + temp_text_width + 20), right - 52)
        draw_drop(draw, drop_x, row_y + 7, scale=0.7)
        draw.text((drop_x + 12, row_y - 5), f"{rain_value}%", font=small_font, fill=0)
        return

    center_x = (left + right) // 2
    draw.text((left, top), label, font=label_font, fill=0)
    draw_condition_icon(draw, (center_x, top + 43), weather_code, scale=1.04, style=weather_icon_style)

    thermo_x = left + 16
    temp_y = top + 76
    draw_thermometer(draw, thermo_x, temp_y, scale=1.0)
    draw.text((thermo_x + 14, temp_y - 12), temperature_text, font=value_font, fill=0)

    drop_x = left + 16
    rain_y = top + 106
    draw_drop(draw, drop_x, rain_y - 1, scale=0.85)
    draw.text((drop_x + 14, rain_y - 12), f"{rain_value}%", font=small_font, fill=0)


def draw_word_pill(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
) -> None:
    radius = max(14, (box[3] - box[1]) // 2)
    draw.rounded_rectangle(box, radius=radius, fill=251, outline=160, width=1)
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


def reading_card_metrics(content: BoardContent, config: BoardConfig) -> dict[str, int | bool | str]:
    layout = get_layout_variant(config)
    image = Image.new("L", (config.image_width, config.image_height), color=255)
    draw = ImageDraw.Draw(image)

    margin = 26
    card_gap = 16
    y = 28 + 50 + 14 + 32
    y += layout.weather_height + card_gap
    y += layout.message_height + card_gap
    y += layout.words_height + card_gap
    reading_box = (margin, y, config.image_width - margin, config.image_height - 26)

    reading_title_font = load_font(layout.reading_title_size, bold=True, serif=True)
    reading_body_font = load_font(layout.reading_body_size)
    title_metrics = measure_text_block(
        draw,
        text=content.reading.title,
        max_width=reading_box[2] - reading_box[0] - 112,
        max_height=66,
        font=reading_title_font,
        line_gap=layout.reading_title_gap,
    )
    title_bottom = reading_box[1] + 30 + len(title_metrics.visible_lines) * title_metrics.line_height
    body_metrics = measure_text_block(
        draw,
        text=content.reading.body,
        max_width=reading_box[2] - reading_box[0] - 64,
        max_height=reading_box[3] - title_bottom - 34,
        font=reading_body_font,
        line_gap=layout.reading_body_gap,
    )
    return {
        "variant": layout.name,
        "title_truncated": title_metrics.truncated,
        "body_truncated": body_metrics.truncated,
        "body_lines": body_metrics.total_lines,
        "body_capacity": body_metrics.available_lines,
        "reading_height": reading_box[3] - reading_box[1],
        "fits": (not title_metrics.truncated) and (not body_metrics.truncated),
    }


def render_board(content: BoardContent, config: BoardConfig, output_path: Path) -> Path:
    layout = get_layout_variant(config)
    width = config.image_width
    height = config.image_height
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)

    title_font = load_font(38, bold=True, serif=True)
    date_font = load_font(18)
    note_font = load_font(layout.note_font_size)
    word_font = load_font(26, bold=True)
    reading_title_font = load_font(layout.reading_title_size, bold=True, serif=True)
    reading_body_font = load_font(layout.reading_body_size)
    weather_label_font = load_font(layout.weather_label_size, bold=True)
    weather_value_font = load_font(layout.weather_value_size, bold=True)
    weather_small_font = load_font(layout.weather_small_size)

    margin = 26
    card_gap = 16
    y = 28

    draw.text((margin, y), content.greeting, font=title_font, fill=0)
    y += 50
    draw.text((margin, y), format_french_date(content), font=date_font, fill=0)
    y += 14
    draw.line((margin, y + 14, width - margin, y + 14), fill=0, width=2)
    y += 32

    weather_box = (margin, y, width - margin, y + layout.weather_height)
    draw_card(draw, weather_box, fill=246)
    draw_corner_badge(draw, weather_box, "weather", config.icon_style, weather_icon_style=config.weather_icon_style)
    divider_x = (weather_box[0] + weather_box[2]) // 2 + 10
    divider_fill = 220 if layout.weather_mode == "paired" else 210
    divider_width = 1 if layout.weather_mode == "paired" else 2
    draw.line((divider_x, weather_box[1] + 24, divider_x, weather_box[3] - 16), fill=divider_fill, width=divider_width)

    left_period_box = (weather_box[0] + 96, weather_box[1] + 18, divider_x - 18, weather_box[3] - 14)
    right_period_box = (divider_x + 20, weather_box[1] + 18, weather_box[2] - 20, weather_box[3] - 14)
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
        weather_icon_style=config.weather_icon_style,
        mode=layout.weather_mode,
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
        weather_icon_style=config.weather_icon_style,
        mode=layout.weather_mode,
    )
    y = weather_box[3] + card_gap

    message_box = (margin, y, width - margin, y + layout.message_height)
    draw_card(draw, message_box, fill=248)
    draw_corner_badge(draw, message_box, "note", config.icon_style, weather_icon_style=config.weather_icon_style)
    message_x = message_box[0] + layout.message_text_left
    message_max_width = message_box[2] - message_box[0] - layout.message_text_right
    message_area_top = message_box[1] + layout.message_text_top
    message_area_bottom = message_box[3] - 16
    message_metrics = measure_text_block(
        draw,
        text=content.family_message,
        max_width=message_max_width,
        max_height=message_area_bottom - message_area_top,
        font=note_font,
        line_gap=layout.note_line_gap,
    )
    message_height = len(message_metrics.visible_lines) * message_metrics.line_height
    centered_message_y = message_area_top + max(0, ((message_area_bottom - message_area_top) - message_height) // 2)
    draw_text_block(
        draw,
        text=content.family_message,
        x=message_x,
        y=centered_message_y,
        max_width=message_max_width,
        max_height=message_area_bottom - centered_message_y,
        font=note_font,
        line_gap=layout.note_line_gap,
    )
    y = message_box[3] + card_gap

    words_box = (margin, y, width - margin, y + layout.words_height)
    draw_card(draw, words_box, fill=245)
    draw_corner_badge(draw, words_box, "words", config.icon_style, weather_icon_style=config.weather_icon_style)
    pill_top = words_box[1] + layout.words_pill_top
    left_pill = (words_box[0] + 104, pill_top, words_box[0] + 292, pill_top + layout.words_pill_height)
    right_pill = (words_box[0] + 306, pill_top, words_box[2] - 18, pill_top + layout.words_pill_height)
    draw_word_pill(draw, box=left_pill, text=content.practice_words[0], font=word_font)
    draw_word_pill(draw, box=right_pill, text=content.practice_words[1], font=word_font)
    y = words_box[3] + card_gap

    reading_box = (margin, y, width - margin, height - 26)
    draw_card(draw, reading_box, fill=246)
    draw_corner_badge(draw, reading_box, "story", config.icon_style, weather_icon_style=config.weather_icon_style)
    title_bottom, _ = draw_text_block(
        draw,
        text=content.reading.title,
        x=reading_box[0] + 94,
        y=reading_box[1] + 30,
        max_width=reading_box[2] - reading_box[0] - 112,
        max_height=66,
        font=reading_title_font,
        line_gap=layout.reading_title_gap,
    )
    draw_text_block(
        draw,
        text=content.reading.body,
        x=reading_box[0] + 32,
        y=title_bottom + 10,
        max_width=reading_box[2] - reading_box[0] - 64,
        max_height=reading_box[3] - title_bottom - 34,
        font=reading_body_font,
        line_gap=layout.reading_body_gap,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path
