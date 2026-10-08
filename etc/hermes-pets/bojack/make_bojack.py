"""Generate a BoJack Horseman pet spritesheet for Hermes Agent (petdex format).

Draws a chibi pixel-art BoJack on a 48x52 grid, upscales 4x to 192x208 frames,
and packs them into the Codex/petdex atlas: 8 cols x 9 rows (1536x1872), rows:
idle, running-right, running-left, waving, jumping, failed, waiting, running, review.
Hermes plays the first 6 frames of each row.

    pip install pillow
    python make_bojack.py            # writes spritesheet.webp, pet.json, preview.gif
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

W, H = 48, 52            # logical pixel grid
SCALE = 4                # 48x52 -> 192x208
COLS, ROWS, FRAMES = 8, 9, 6
OUT = Path(__file__).resolve().parent

# Palette (sampled by eye from the show)
INK = (27, 20, 32, 255)
FUR = (150, 84, 48, 255)
FUR_DARK = (118, 62, 34, 255)
BLAZE = (246, 240, 228, 255)
MANE = (30, 26, 30, 255)
EYE_WHITE = (255, 255, 255, 255)
SWEATER = (58, 84, 168, 255)
SWEATER_DOT = (132, 168, 226, 255)
BLAZER = (124, 126, 136, 255)
BLAZER_DARK = (96, 98, 108, 255)
JEANS = (46, 178, 168, 255)
SHOE = (214, 44, 52, 255)
SOLE = (250, 250, 250, 255)
PAPER = (250, 248, 236, 255)
TEAR = (120, 196, 255, 255)
HEART = (236, 72, 120, 255)


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def outline(img):
    """Add a 1px ink outline around everything opaque in *img*."""
    alpha = img.getchannel("A").point(lambda a: 255 if a else 0)
    grown = alpha
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown = ImageChops.lighter(grown, ImageChops.offset(alpha, dx, dy))
    ring = ImageChops.subtract(grown, alpha)
    out = layer()
    out.paste(INK, mask=ring)
    out.alpha_composite(img)
    return out


class Canvas:
    def __init__(self):
        self.img = layer()

    def part(self, fn, *args, ink=True):
        lay = layer()
        fn(ImageDraw.Draw(lay), *args)
        self.img.alpha_composite(outline(lay) if ink else lay)


# ---------------------------------------------------------------- body parts

def draw_leg(d, hip, foot):
    d.line([hip, foot], fill=JEANS, width=4)
    fx, fy = foot
    d.rectangle([fx - 2, fy, fx + 3, fy + 1], fill=SHOE)
    d.line([(fx - 2, fy + 2), (fx + 3, fy + 2)], fill=SOLE)


def draw_torso(d, dy):
    d.rounded_rectangle([13, 28 + dy, 27, 41 + dy], radius=3, fill=BLAZER)
    # sweater peeking out of the open blazer
    d.polygon([(17, 28 + dy), (23, 28 + dy), (22, 41 + dy), (18, 41 + dy)], fill=SWEATER)
    for y in range(30 + dy, 41 + dy, 2):
        for x in range(18 + (y % 4 == 0), 23, 2):
            d.point((x, y), fill=SWEATER_DOT)
    d.line([(17, 28 + dy), (18, 41 + dy)], fill=BLAZER_DARK)   # lapels
    d.line([(23, 28 + dy), (22, 41 + dy)], fill=BLAZER_DARK)


def draw_arm(d, shoulder, hand):
    d.line([shoulder, hand], fill=BLAZER, width=4)
    hx, hy = hand
    d.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=FUR)


def draw_head(d, dy, eye, mouth, look):
    o = dy
    # ears
    d.polygon([(14, 10 + o), (16, 1 + o), (20, 8 + o)], fill=FUR)
    d.polygon([(19, 8 + o), (22, 1 + o), (25, 9 + o)], fill=FUR)
    d.point((16, 4 + o), fill=FUR_DARK)
    d.point((22, 4 + o), fill=FUR_DARK)
    # neck + skull + snout
    d.polygon([(14, 18 + o), (23, 18 + o), (23, 30 + o), (15, 30 + o)], fill=FUR)
    d.ellipse([11, 6 + o, 28, 23 + o], fill=FUR)
    d.rounded_rectangle([20, 12 + o, 38, 24 + o], radius=5, fill=FUR)
    # white blaze down the face
    d.polygon([(19, 7 + o), (22, 7 + o), (36, 13 + o), (38, 16 + o), (35, 16 + o), (20, 11 + o)], fill=BLAZE)
    # nostril + jaw shading
    d.rectangle([34, 18 + o, 35, 19 + o], fill=INK)
    d.line([(22, 24 + o), (35, 24 + o)], fill=FUR_DARK)
    # mane: forelock + strip down the back of the neck
    d.polygon([(17, 5 + o), (22, 4 + o), (21, 9 + o), (18, 10 + o)], fill=MANE)
    d.polygon([(12, 9 + o), (15, 7 + o), (15, 29 + o), (12, 28 + o), (11, 18 + o)], fill=MANE)

    # eye (BoJack's signature half-lidded look by default)
    ex, ey = 24, 14 + o
    if eye == "closed":
        d.line([(ex - 2, ey), (ex + 2, ey)], fill=INK)
    elif eye == "sad":
        d.line([(ex - 2, ey), (ex + 2, ey + 1)], fill=INK)
        d.point((ex - 1, ey + 2), fill=TEAR)
        d.point((ex - 1, ey + 3), fill=TEAR)
    else:
        d.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=EYE_WHITE)
        px = ex + look
        d.rectangle([px, ey, px + 1, ey + 1], fill=INK)
        if eye == "half":
            d.rectangle([ex - 2, ey - 2, ex + 2, ey - 1], fill=FUR)
            d.line([(ex - 2, ey - 1), (ex + 2, ey - 1)], fill=INK)
        else:  # wide open, brow up
            d.line([(ex - 2, ey - 4), (ex + 2, ey - 4)], fill=INK)

    # mouth
    my = 21 + o
    if mouth == "smirk":
        d.line([(28, my), (35, my)], fill=INK)
        d.point((36, my - 1), fill=INK)
    elif mouth == "frown":
        d.line([(28, my), (35, my)], fill=INK)
        d.point((36, my + 1), fill=INK)
    elif mouth == "open":
        d.rectangle([29, my - 1, 35, my + 1], fill=INK)
        d.line([(30, my), (34, my)], fill=SHOE)
    else:
        d.line([(28, my), (36, my)], fill=INK)


# ---------------------------------------------------------------- props

def draw_paper(d, x, y):
    d.rectangle([x, y, x + 8, y + 10], fill=PAPER)
    for ly in range(y + 2, y + 10, 2):
        d.line([(x + 1, ly), (x + 7, ly)], fill=(170, 170, 180, 255))
    d.line([(x + 1, y + 1), (x + 5, y + 1)], fill=INK)  # script title


def draw_dots(d, n):
    d.rounded_rectangle([31, 1, 46, 8], radius=3, fill=(255, 255, 255, 255))
    for i in range(n):
        d.rectangle([34 + i * 4, 4, 35 + i * 4, 5], fill=INK)


def draw_cloud(d, dy):
    d.ellipse([27, 1 + dy, 37, 7 + dy], fill=(150, 156, 170, 255))
    d.ellipse([33, 0 + dy, 45, 7 + dy], fill=(150, 156, 170, 255))


def draw_rain(d, phase):
    for i, x in enumerate((30, 34, 38, 42)):
        y = 9 + (phase * 2 + i * 3) % 6
        d.line([(x, y), (x, y + 1)], fill=TEAR)


def draw_heart(d, x, y):
    d.point([(x, y), (x + 2, y)], fill=HEART)
    d.line([(x - 1, y + 1), (x + 3, y + 1)], fill=HEART)
    d.line([(x, y + 2), (x + 2, y + 2)], fill=HEART)
    d.point((x + 1, y + 3), fill=HEART)


def draw_speed(d, dy):
    for y in (30, 35, 40):
        d.line([(2, y + dy), (7, y + dy)], fill=(200, 200, 210, 255))


def draw_dust(d, phase):
    r = 1 + phase % 3
    d.ellipse([8 - r, 49 - r, 8 + r, 49 + r], fill=(214, 206, 190, 255))


# ---------------------------------------------------------------- frames

def frame(dy=0, head_dy=0, l_arm=(12, 40), r_arm=(28, 40), l_foot=(17, 48), r_foot=(23, 48),
          eye="half", mouth="smirk", look=0, front_arm=False, props=()):
    c = Canvas()
    for kind, *args in props:
        if kind in ("cloud",):
            c.part(draw_cloud, *args)
    c.part(draw_leg, (17, 40 + dy), l_foot)
    c.part(draw_leg, (23, 40 + dy), r_foot)
    c.part(draw_arm, (14, 30 + dy), (l_arm[0], l_arm[1] + dy))
    c.part(draw_torso, dy)
    if not front_arm:
        c.part(draw_arm, (26, 30 + dy), (r_arm[0], r_arm[1] + dy))
    c.part(draw_head, dy + head_dy, eye, mouth, look)
    if front_arm:
        c.part(draw_arm, (26, 30 + dy), (r_arm[0], r_arm[1] + dy))
    for kind, *args in props:
        if kind == "paper":
            c.part(draw_paper, args[0], args[1] + dy)
            c.part(draw_arm, (26, 30 + dy), (args[0] + 1, args[1] + 8 + dy))
        elif kind == "dots":
            c.part(draw_dots, *args)
        elif kind == "rain":
            c.part(draw_rain, *args, ink=False)
        elif kind == "heart":
            c.part(draw_heart, *args, ink=False)
        elif kind == "speed":
            c.part(draw_speed, dy, ink=False)
        elif kind == "dust":
            c.part(draw_dust, *args, ink=False)
    out = layer()
    out.paste(c.img, (0, 1))  # 1px headroom for the ears
    return out


def run_cycle(i, extra=()):
    s = math.sin(i / FRAMES * 2 * math.pi)
    stride = round(4 * s)
    bob = -1 if i % 3 == 0 else 0
    return frame(dy=bob, l_foot=(17 + stride, 48 - (stride > 0)), r_foot=(23 - stride, 48 - (stride < 0)),
                 l_arm=(12 - stride, 39), r_arm=(28 + stride, 39), eye="open", mouth="flat", props=extra)


def row_idle(i):
    bob = 1 if i in (2, 3, 4) else 0
    return frame(dy=bob, eye="closed" if i == 4 else "half")


def row_run_right(i):
    return run_cycle(i, (("speed",),))


def row_run_left(i):
    return ImageOps.mirror(run_cycle(i, (("speed",),)))


def row_wave(i):
    hand_x = (31, 34, 31, 34, 31, 34)[i]
    return frame(r_arm=(hand_x, 22), front_arm=True, mouth="open" if i % 2 else "smirk", eye="open")


def row_jump(i):
    lift = (1, -1, -2, -2, -1, 1)[i]           # crouch, spring, hang, land
    tuck = (0, 3, 5, 5, 3, 0)[i]
    feet_y = 48 + lift - tuck
    props = (("heart", 39, 6 - i % 2),) if i in (2, 3) else ()
    return frame(dy=lift, l_foot=(15, feet_y), r_foot=(25, feet_y), l_arm=(9, 24), r_arm=(31, 24),
                 eye="open", mouth="open", props=props)


def row_failed(i):
    slump = min(i, 3)
    return frame(dy=slump // 2, head_dy=slump, l_arm=(13, 42), r_arm=(27, 42), eye="sad", mouth="frown",
                 props=(("cloud", 0), ("rain", i)))


def row_waiting(i):
    tap = i % 2
    return frame(r_foot=(24, 48 - tap), l_arm=(22, 34), r_arm=(18, 35), front_arm=True,
                 look=(-1, -1, 0, 1, 1, 0)[i], mouth="flat", props=(("dots", 1 + i % 3),))


def row_running(i):
    return run_cycle(i, (("dust", i),))


def row_review(i):
    return frame(look=(-1, 0, 1, 1, 0, -1)[i], dy=0, eye="half", mouth="flat",
                 l_arm=(13, 40), props=(("paper", 31, 22),))


ROW_FNS = [row_idle, row_run_right, row_run_left, row_wave, row_jump, row_failed, row_waiting, row_running, row_review]


def main():
    sheet = Image.new("RGBA", (COLS * W * SCALE, ROWS * H * SCALE), (0, 0, 0, 0))
    preview = []
    for r, fn in enumerate(ROW_FNS):
        frames = [fn(i) for i in range(FRAMES)]
        frames += [frames[-1]] * (COLS - FRAMES)  # pad unused columns
        for col, f in enumerate(frames):
            big = f.resize((W * SCALE, H * SCALE), Image.NEAREST)
            sheet.paste(big, (col * W * SCALE, r * H * SCALE))
            if col < FRAMES:
                preview.append(big)
    sheet.save(OUT / "spritesheet.webp", format="WEBP", lossless=True, quality=100, method=6, exact=True)

    bg = (238, 234, 246, 255)
    gif = []
    for f in preview:
        g = Image.new("RGBA", f.size, bg)
        g.alpha_composite(f)
        gif.append(g.convert("P", palette=Image.ADAPTIVE))
    gif[0].save(OUT / "preview.gif", save_all=True, append_images=gif[1:], duration=1100 // FRAMES, loop=0)

    meta = {"id": "bojack", "displayName": "BoJack Horseman",
            "description": "Back in the 90s he was in a very famous TV show.",
            "spritesheetPath": "spritesheet.webp"}
    (OUT / "pet.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {sheet.size[0]}x{sheet.size[1]} sheet to {OUT}")


if __name__ == "__main__":
    main()
