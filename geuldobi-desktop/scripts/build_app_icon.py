from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "UI" / "char_preview" / "phone1_96.png"
BUILD_DIR = ROOT / "geuldobi-desktop" / "build"
ICON_PNG = BUILD_DIR / "icon.png"
ICON_ICO = BUILD_DIR / "icon.ico"


def _extract_sprite() -> Image.Image:
    sheet = Image.open(SOURCE).convert("RGBA")
    cell_width = sheet.width // 8
    cell_height = sheet.height
    col = 1
    row = 0
    sprite = sheet.crop(
        (
            col * cell_width,
            row * cell_height,
            (col + 1) * cell_width,
            (row + 1) * cell_height,
        )
    )
    sprite = sprite.crop((0, 0, sprite.width, 176))

    bg = sprite.getpixel((0, 0))
    pixels = []
    for red, green, blue, alpha in sprite.getdata():
        if (
            abs(red - bg[0]) <= 12
            and abs(green - bg[1]) <= 12
            and abs(blue - bg[2]) <= 12
        ):
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append((red, green, blue, alpha))
    sprite.putdata(pixels)
    return sprite.crop(sprite.getbbox())


def _render_icon(sprite: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((116, 132, 908, 924), fill=(14, 22, 36, 220))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(shadow)

    background = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(background)
    bg_draw.ellipse((120, 120, 904, 904), fill=(31, 54, 85, 255))
    bg_draw.ellipse((164, 164, 860, 860), fill=(76, 165, 214, 255))
    bg_draw.ellipse((220, 220, 804, 804), fill=(238, 247, 255, 255))
    canvas.alpha_composite(background)

    sprite = sprite.resize((520, 520), Image.Resampling.NEAREST)
    shadow_pad = 32
    sprite_shadow = Image.new(
        "RGBA",
        (sprite.width + (shadow_pad * 2), sprite.height + (shadow_pad * 2)),
        (0, 0, 0, 0),
    )
    sprite_shadow.paste(
        (0, 0, 0, 120),
        (shadow_pad, shadow_pad),
        mask=sprite.split()[-1],
    )
    sprite_shadow = sprite_shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(
        sprite_shadow,
        (286 - shadow_pad, 292 - shadow_pad),
    )
    canvas.alpha_composite(sprite, (252, 252))
    return canvas


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    icon = _render_icon(_extract_sprite())
    icon.save(ICON_PNG)
    icon.save(
        ICON_ICO,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"wrote {ICON_PNG}")
    print(f"wrote {ICON_ICO}")


if __name__ == "__main__":
    main()
