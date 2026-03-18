from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat


TARGET_SIZE = (600, 800)
DOWNLOADS = Path(r"C:\Users\aabec\Downloads")
OUTPUT_DIR = Path(r"C:\Users\aabec\Scripts\kindle-family-board\output\new-screensavers")
EXPORT_DIR = DOWNLOADS / "kindle-screensavers-600x800"


@dataclass(frozen=True)
class CropSpec:
    filename: str
    box: tuple[int, int, int, int]


CROPS = (
    CropSpec("IMG_0164.jpg", (250, 520, 2774, 3885)),
    CropSpec("IMG_0050.jpg", (0, 120, 2418, 3344)),
    CropSpec("20250628_181005.jpg", (1150, 0, 2839, 2252)),
    CropSpec("20250812_183249.jpg", (0, 850, 2252, 3852)),
)


def prepare_image(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)

    contrast = ImageEnhance.Contrast(gray).enhance(1.18)
    sharp = contrast.filter(ImageFilter.UnsharpMask(radius=1.4, percent=130, threshold=3))

    # Keep faces readable on e-ink without flattening midtones too much.
    mean = ImageStat.Stat(sharp).mean[0]
    if mean < 110:
        sharp = ImageEnhance.Brightness(sharp).enhance(1.07)
    elif mean > 170:
        sharp = ImageEnhance.Brightness(sharp).enhance(0.94)

    return sharp


def render_contact_sheet(paths: list[Path]) -> None:
    thumb_width = 300
    thumb_height = 400
    gap = 28
    margin = 36
    label_height = 34
    canvas = Image.new(
        "L",
        (
            margin * 2 + thumb_width * 2 + gap,
            margin * 2 + (thumb_height + label_height) * 2 + gap,
        ),
        color=245,
    )

    for index, path in enumerate(paths):
        image = Image.open(path).convert("L")
        x = margin + (index % 2) * (thumb_width + gap)
        y = margin + (index // 2) * (thumb_height + label_height + gap)
        thumb = ImageOps.fit(image, (thumb_width, thumb_height), method=Image.Resampling.LANCZOS)
        canvas.paste(thumb, (x, y))

    canvas.save(OUTPUT_DIR / "contact-sheet.png")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for spec in CROPS:
        source = DOWNLOADS / spec.filename
        image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
        cropped = image.crop(spec.box)
        fitted = ImageOps.fit(cropped, TARGET_SIZE, method=Image.Resampling.LANCZOS)
        prepared = prepare_image(fitted)
        output = OUTPUT_DIR / f"{source.stem}-kindle.png"
        prepared.save(output, optimize=True)
        prepared.save(EXPORT_DIR / output.name, optimize=True)
        outputs.append(output)

    render_contact_sheet(outputs)
    Image.open(OUTPUT_DIR / "contact-sheet.png").save(EXPORT_DIR / "contact-sheet.png", optimize=True)


if __name__ == "__main__":
    main()
