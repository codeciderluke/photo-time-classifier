"""Generate the application icon (PNG + ICO).

The concept is the app itself: a photo, and the time it was taken. A white
photo card sits on the app's blue accent gradient, with a clock badge cut into
its lower-right corner. Both glyphs stay bold and unfilled by detail so they
survive being scaled down to a 16x16 taskbar icon.

Run: python assets/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512
ACCENT_TOP = (92, 157, 255)    # #5c9dff
ACCENT_BOT = (47, 116, 208)    # #2f74d0
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)

# Photo card
CARD = (64, 104, 384, 366)     # left, top, right, bottom
CARD_RADIUS = 30

# Clock badge, overlapping the card's lower-right corner
CLOCK_C = (386, 380)
CLOCK_R = 96
CLOCK_GAP = 16                 # gradient ring separating badge from card

OUT_DIR = Path(__file__).resolve().parent


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def gradient(size: int) -> Image.Image:
    base = Image.new("RGB", (size, size), ACCENT_TOP)
    top, bot = ACCENT_TOP, ACCENT_BOT
    px = base.load()
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(size):
            px[x, y] = (r, g, b)
    return base


def draw_photo_card(layer: Image.Image) -> None:
    """White card holding a sun-over-mountains glyph, punched out of the card."""
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(list(CARD), radius=CARD_RADIUS, fill=WHITE)

    # The glyph is cut out of the card so the gradient shows through it,
    # which keeps the icon to two tones at any size.
    cut = Image.new("RGBA", layer.size, CLEAR)
    cd = ImageDraw.Draw(cut)
    cd.ellipse([132, 152, 196, 216], fill=WHITE)                       # sun
    cd.polygon([(96, 330), (206, 196), (316, 330)], fill=WHITE)        # back peak
    cd.polygon([(214, 330), (286, 242), (358, 330)], fill=WHITE)       # front peak

    # Keep the cut inside the card's rounded outline.
    card_only = Image.new("L", layer.size, 0)
    ImageDraw.Draw(card_only).rounded_rectangle(
        list(CARD), radius=CARD_RADIUS, fill=255
    )
    cut.putalpha(Image.composite(cut.getchannel("A"),
                                 Image.new("L", layer.size, 0), card_only))

    layer.paste(CLEAR, (0, 0), cut)


def punch_clock_gap(layer: Image.Image) -> None:
    """Erase a disc from the card so the gradient rings the clock badge."""
    gap = Image.new("L", layer.size, 0)
    r = CLOCK_R + CLOCK_GAP
    ImageDraw.Draw(gap).ellipse(
        [CLOCK_C[0] - r, CLOCK_C[1] - r, CLOCK_C[0] + r, CLOCK_C[1] + r], fill=255
    )
    layer.paste(CLEAR, (0, 0), gap)


def draw_clock(img: Image.Image) -> None:
    cx, cy = CLOCK_C
    d = ImageDraw.Draw(img)
    d.ellipse([cx - CLOCK_R, cy - CLOCK_R, cx + CLOCK_R, cy + CLOCK_R], fill=WHITE)

    # Hands read as "10:10"-ish: unambiguous as a clock even at small sizes.
    hand = ACCENT_BOT + (255,)
    d.line([(cx, cy), (cx, cy - 56)], fill=hand, width=17, joint="curve")
    d.line([(cx, cy), (cx + 44, cy + 26)], fill=hand, width=17, joint="curve")
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=hand)


def build() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), CLEAR)
    grad = gradient(SIZE).convert("RGBA")
    img.paste(grad, (0, 0), rounded_mask(SIZE, radius=112))

    card = Image.new("RGBA", (SIZE, SIZE), CLEAR)
    draw_photo_card(card)
    punch_clock_gap(card)
    img.alpha_composite(card)

    draw_clock(img)
    return img


def main() -> None:
    icon = build()
    png = OUT_DIR / "icon.png"
    icon.save(png)
    ico = OUT_DIR / "icon.ico"
    icon.save(ico, sizes=[(16, 16), (32, 32), (48, 48),
                          (64, 64), (128, 128), (256, 256)])
    print("wrote", png, "and", ico)


if __name__ == "__main__":
    main()
