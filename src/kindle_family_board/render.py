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


def _sv(value: float, scale: float) -> int:
    return int(round(value * scale))


def draw_badge_canvas(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> tuple[int, int]:
    left = box[0] + 6
    top = box[1] - 12
    right = left + 88
    bottom = top + 70
    draw.rounded_rectangle((left, top + 8, right, bottom), radius=18, fill=255)
    return left, top


def draw_envelope_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    stroke = 3
    left = ox + 12
    top = oy + 20
    right = ox + 70
    bottom = oy + 62

    letter_left = left + 8
    letter_top = top - 12
    letter_right = right - 8
    letter_bottom = top + 10
    draw.rounded_rectangle((letter_left, letter_top, letter_right, letter_bottom), radius=4, outline=0, width=stroke)
    for row in range(3):
        y = letter_top + 7 + row * 5
        draw.line((letter_left + 8, y, letter_right - 8 - row * 4, y), fill=0, width=2)

    draw.rounded_rectangle((left, top, right, bottom), radius=4, outline=0, width=stroke)
    draw.line((left, top, (left + right) / 2, top + 18, right, top), fill=0, width=stroke)
    draw.line((left, bottom, (left + right) / 2, top + 26, right, bottom), fill=0, width=stroke)
    draw.line((left, top, left + 19, top + 16), fill=0, width=stroke)
    draw.line((right, top, right - 19, top + 16), fill=0, width=stroke)
    draw_heart(draw, ((left + right) // 2, top + 25), 0.75)


def draw_book_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    stroke = 3
    left_page = (ox + 12, oy + 21, ox + 40, oy + 60)
    right_page = (ox + 40, oy + 21, ox + 68, oy + 60)
    draw.rounded_rectangle(left_page, radius=5, outline=0, width=stroke)
    draw.rounded_rectangle(right_page, radius=5, outline=0, width=stroke)
    draw.line((ox + 40, oy + 21, ox + 40, oy + 60), fill=0, width=stroke)
    draw.arc((ox + 18, oy + 52, ox + 40, oy + 64), start=180, end=355, fill=0, width=2)
    draw.arc((ox + 40, oy + 52, ox + 62, oy + 64), start=185, end=360, fill=0, width=2)
    for row in range(4):
        y = oy + 28 + row * 7
        draw.arc((ox + 17, y - 2, ox + 36, y + 4), start=190, end=342, fill=0, width=2)
        draw.arc((ox + 44, y - 2, ox + 63, y + 4), start=198, end=350, fill=0, width=2)

    block_a = (ox + 52, oy + 43, ox + 74, oy + 65)
    block_c = (ox + 68, oy + 52, ox + 90, oy + 74)
    draw.polygon(
        [
            (block_a[0], block_a[1]),
            (block_a[2] - 6, block_a[1] - 4),
            (block_a[2], block_a[1] + 2),
            (block_a[2], block_a[3] - 4),
            (block_a[0] + 6, block_a[3]),
            (block_a[0], block_a[3] - 6),
        ],
        outline=0,
        fill=255,
    )
    draw.line((block_a[0], block_a[1], block_a[2] - 6, block_a[1] - 4, block_a[2], block_a[1] + 2, block_a[2], block_a[3] - 4, block_a[0] + 6, block_a[3], block_a[0], block_a[3] - 6, block_a[0], block_a[1]), fill=0, width=2)
    draw.line((block_a[0] + 6, block_a[3], block_a[0] + 6, block_a[1] + 6), fill=0, width=2)
    font = load_font(18, bold=True)
    draw.text((block_a[0] + 7, block_a[1] + 8), "A", font=font, fill=0)

    draw.polygon(
        [
            (block_c[0], block_c[1]),
            (block_c[2] - 6, block_c[1] - 4),
            (block_c[2], block_c[1] + 2),
            (block_c[2], block_c[3] - 4),
            (block_c[0] + 6, block_c[3]),
            (block_c[0], block_c[3] - 6),
        ],
        outline=0,
        fill=255,
    )
    draw.line((block_c[0], block_c[1], block_c[2] - 6, block_c[1] - 4, block_c[2], block_c[1] + 2, block_c[2], block_c[3] - 4, block_c[0] + 6, block_c[3], block_c[0], block_c[3] - 6, block_c[0], block_c[1]), fill=0, width=2)
    draw.line((block_c[0] + 6, block_c[3], block_c[0] + 6, block_c[1] + 6), fill=0, width=2)
    draw.text((block_c[0] + 7, block_c[1] + 8), "C", font=font, fill=0)


def draw_speech_badge(draw: ImageDraw.ImageDraw, origin: tuple[int, int]) -> None:
    ox, oy = origin
    bubble = (ox + 8, oy + 12, ox + 74, oy + 58)
    draw.rounded_rectangle(bubble, radius=12, outline=0, width=3)
    draw.polygon([(ox + 18, oy + 58), (ox + 14, oy + 72), (ox + 30, oy + 60)], fill=255, outline=0)
    draw.line((ox + 18, oy + 58, ox + 14, oy + 72, ox + 30, oy + 60), fill=0, width=3)

    for col in range(4):
        for row in range(5):
            x = ox + 50 + col * 6
            y = oy + 18 + row * 6
            draw.ellipse((x, y, x + 1, y + 1), fill=0)

    font = load_font(16, bold=True)
    draw.text((ox + 18, oy + 18), "HA", font=font, fill=0, stroke_width=1, stroke_fill=255)
    draw.text((ox + 18, oy + 36), "HA", font=font, fill=0, stroke_width=1, stroke_fill=255)

    face_center = (ox + 72, oy + 56)
    draw.ellipse((face_center[0] - 14, face_center[1] - 14, face_center[0] + 14, face_center[1] + 14), outline=0, width=3)
    draw.ellipse((face_center[0] - 6, face_center[1] - 4, face_center[0] - 3, face_center[1] - 1), fill=0)
    draw.ellipse((face_center[0] + 3, face_center[1] - 4, face_center[0] + 6, face_center[1] - 1), fill=0)
    draw.arc((face_center[0] - 9, face_center[1] - 2, face_center[0] + 9, face_center[1] + 10), start=15, end=165, fill=0, width=3)


def draw_weather_badge_scene(draw: ImageDraw.ImageDraw, origin: tuple[int, int], weather_icon_style: str) -> None:
    ox, oy = origin
    draw_condition_icon(draw, (ox + 24, oy + 29), 0, scale=0.9, style=weather_icon_style)
    draw_condition_icon(draw, (ox + 56, oy + 40), 61, scale=0.95, style=weather_icon_style)


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
) -> None:
    left, top, right, bottom = box
    center_x = (left + right) // 2
    draw.text((left, top), label, font=label_font, fill=0)
    draw_condition_icon(draw, (center_x, top + 43), weather_code, scale=1.04, style=weather_icon_style)

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
    draw_corner_badge(draw, weather_box, "weather", config.icon_style, weather_icon_style=config.weather_icon_style)
    divider_x = (weather_box[0] + weather_box[2]) // 2 + 10
    draw.line((divider_x, weather_box[1] + 28, divider_x, weather_box[3] - 18), fill=210, width=2)

    left_period_box = (weather_box[0] + 108, weather_box[1] + 20, divider_x - 20, weather_box[3] - 14)
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
        weather_icon_style=config.weather_icon_style,
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
    )
    y = weather_box[3] + card_gap

    message_box = (margin, y, width - margin, y + 114)
    draw_card(draw, message_box, fill=248)
    draw_corner_badge(draw, message_box, "note", config.icon_style, weather_icon_style=config.weather_icon_style)
    draw_text_block(
        draw,
        text=content.family_message,
        x=message_box[0] + 102,
        y=message_box[1] + 34,
        max_width=message_box[2] - message_box[0] - 120,
        max_height=64,
        font=note_font,
        line_gap=7,
    )
    y = message_box[3] + card_gap

    words_box = (margin, y, width - margin, y + 100)
    draw_card(draw, words_box, fill=245)
    draw_corner_badge(draw, words_box, "words", config.icon_style, weather_icon_style=config.weather_icon_style)
    pill_top = words_box[1] + 28
    left_pill = (words_box[0] + 116, pill_top, words_box[0] + 298, pill_top + 44)
    right_pill = (words_box[0] + 314, pill_top, words_box[2] - 18, pill_top + 44)
    draw_word_pill(draw, box=left_pill, text=content.practice_words[0], font=word_font)
    draw_word_pill(draw, box=right_pill, text=content.practice_words[1], font=word_font)
    y = words_box[3] + card_gap

    reading_box = (margin, y, width - margin, height - 26)
    draw_card(draw, reading_box, fill=246)
    draw_corner_badge(draw, reading_box, "story", config.icon_style, weather_icon_style=config.weather_icon_style)
    title_bottom = draw_text_block(
        draw,
        text=content.reading.title,
        x=reading_box[0] + 108,
        y=reading_box[1] + 30,
        max_width=reading_box[2] - reading_box[0] - 132,
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
