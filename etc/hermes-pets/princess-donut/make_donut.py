"""Generate a Princess Donut pet spritesheet for Hermes Agent (petdex format).

Princess Donut (Dungeon Crawler Carl): a tortoiseshell Persian with a tiara,
round black sunglasses, butterfly pendant and scale-mail pauldron, plus Mongo,
her velociraptor. Drawn on a 96x104 grid, upscaled 2x to 192x208 frames, packed
into the Codex/petdex atlas: 8 cols x 9 rows (1536x1872), rows:
idle, running-right, running-left, waving, jumping, failed, waiting, running, review.
Hermes plays the first 6 frames of each row.

    pip install pillow
    python make_donut.py            # writes spritesheet.webp, pet.json, preview.gif
"""

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

W, H = 96, 104           # logical pixel grid
SCALE = 2                # 96x104 -> 192x208
COLS, ROWS, FRAMES = 8, 9, 6
OUT = Path(__file__).resolve().parent

INK = (30, 20, 34, 255)
FUR = (84, 60, 48, 255)
FUR_DARK = (52, 36, 32, 255)
FUR_LIGHT = (122, 92, 70, 255)
GINGER = (186, 128, 74, 255)
CREAM = (214, 180, 140, 255)
PINK = (232, 150, 160, 255)
SILVER = (196, 200, 210, 255)
SILVER_DARK = (130, 136, 150, 255)
GEM = (128, 52, 196, 255)
GEM_LIGHT = (214, 160, 255, 255)
LENS = (18, 18, 22, 255)
VELVET = (150, 20, 36, 255)
VELVET_LIGHT = (196, 46, 62, 255)
GOLD = (222, 180, 92, 255)
WHITE = (255, 255, 255, 255)
RAPTOR = (78, 150, 76, 255)
RAPTOR_DARK = (48, 102, 56, 255)
RAPTOR_BELLY = (178, 214, 132, 255)
SADDLE = (110, 46, 150, 255)
EYE_YELLOW = (250, 210, 60, 255)
MAGIC = (255, 120, 230, 255)
MAGIC_GLOW = (170, 90, 255, 255)
TEAR = (120, 196, 255, 255)
CLOUD = (150, 156, 170, 255)


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def outline(img):
    alpha = img.getchannel("A").point(lambda a: 255 if a else 0)
    grown = alpha
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown = ImageChops.lighter(grown, ImageChops.offset(alpha, dx, dy))
    out = layer()
    out.paste(INK, mask=ImageChops.subtract(grown, alpha))
    out.alpha_composite(img)
    return out


class Xf:
    """Maps sprite-local coordinates to the canvas: (ox + x*s, oy + y*s)."""

    def __init__(self, ox=0.0, oy=0.0, s=1.0):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, x, y):
        return (round(self.ox + x * self.s), round(self.oy + y * self.s))

    def pts(self, *xy):
        return [self.p(x, y) for x, y in xy]

    def box(self, cx, cy, rx, ry):
        x0, y0 = self.p(cx - rx, cy - ry)
        x1, y1 = self.p(cx + rx, cy + ry)
        return [x0, y0, max(x0, x1), max(y0, y1)]

    def w(self, width):
        return max(1, round(width * self.s))


class Canvas:
    def __init__(self):
        self.img = layer()

    def part(self, fn, *args, ink=True):
        lay = layer()
        fn(ImageDraw.Draw(lay), *args)
        self.img.alpha_composite(outline(lay) if ink else lay)


def fluffy(d, t, cx, cy, rx, ry, color, n=16, spike=3, phase=0.0):
    """Ellipse with a jagged, fur-tufted edge."""
    pts = []
    for k in range(n * 2):
        a = math.pi * k / n + phase
        r = 1 + (spike / max(rx, ry) if k % 2 == 0 else 0)
        pts.append(t.p(cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    d.polygon(pts, fill=color)


def fur_texture(d, t, cx, cy, rx, ry, seed, colors=(FUR_DARK, FUR_LIGHT)):
    rnd = random.Random(seed)
    for _ in range(int(rx * ry * t.s * t.s / 6) + 1):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, 0.85) ** 0.5
        x, y = t.p(cx + rx * r * math.cos(a), cy + ry * r * math.sin(a))
        d.line([(x, y), (x, y + 1)], fill=rnd.choice(colors))


# ---------------------------------------------------------------- Princess Donut
# Cat space: sitting, facing the viewer; tiara top ~y1, paws ~y91, centre x48.

def cat_tail(d, t, swish):
    fluffy(d, t, 70, 86 - swish, 18, 7, FUR, n=12, spike=3)
    fluffy(d, t, 84, 84 - swish * 1.5, 6, 5, GINGER, n=8, spike=2)


def cat_body(d, t, seed):
    fluffy(d, t, 48, 68, 24, 23, FUR, n=18, spike=3)
    fur_texture(d, t, 48, 68, 22, 21, seed)
    d.polygon(t.pts((28, 60), (36, 52), (34, 74), (26, 78)), fill=GINGER)  # tortie patch
    fluffy(d, t, 46, 64, 12, 15, CREAM, n=12, spike=2)
    fur_texture(d, t, 46, 64, 10, 13, seed + 1, (GINGER, CREAM))


def cat_pauldron(d, t):
    d.ellipse(t.box(65, 63, 10, 12), fill=SILVER)
    for row, y in enumerate(range(55, 75, 4)):
        for x in range(57 + (row % 2) * 2, 74, 4):
            d.arc(t.box(x, y, 2, 2), 0, 180, fill=SILVER_DARK)
    d.arc(t.box(65, 63, 10, 12), 200, 340, fill=WHITE)


def cat_paw(d, t, x, y):
    d.ellipse(t.box(x, y, 5, 3.5), fill=FUR_LIGHT)
    for k in (-2, 0, 2):
        d.point(t.p(x + k, y + 2), fill=FUR_DARK)


def cat_raised_paw(d, t, x, y):
    d.line(t.pts((36, 60), (x, y)), fill=FUR, width=t.w(7))
    d.ellipse(t.box(x, y, 4.5, 4.5), fill=FUR_LIGHT)
    d.ellipse(t.box(x, y + 1, 2, 1.5), fill=PINK)


def cat_head(d, t, ears_flat=False):
    if ears_flat:
        d.polygon(t.pts((22, 22), (18, 14), (32, 16)), fill=FUR)
        d.polygon(t.pts((64, 16), (78, 14), (74, 22)), fill=FUR)
    else:
        d.polygon(t.pts((25, 20), (27, 7), (37, 13)), fill=FUR)
        d.polygon(t.pts((59, 13), (69, 7), (71, 20)), fill=GINGER)
        d.polygon(t.pts((28, 16), (28, 11), (33, 14)), fill=PINK)
        d.polygon(t.pts((63, 14), (68, 11), (68, 16)), fill=PINK)
    fluffy(d, t, 48, 31, 25, 19, FUR, n=18, spike=3, phase=0.1)
    fur_texture(d, t, 48, 31, 22, 16, 7)
    d.polygon(t.pts((44, 12), (54, 12), (60, 20), (50, 26), (40, 20)), fill=GINGER)  # forehead blaze
    d.polygon(t.pts((60, 34), (70, 28), (72, 40), (62, 44)), fill=GINGER)          # cheek patch
    d.ellipse(t.box(48, 41, 9, 6), fill=CREAM)
    d.polygon(t.pts((46, 36), (50, 36), (48, 39)), fill=PINK)                      # nose
    d.line(t.pts((48, 39), (48, 41)), fill=INK)
    d.line(t.pts((44, 43), (46, 42), (48, 41), (50, 42), (52, 43)), fill=INK)   # tiny grumpy mouth


def cat_eyes(d, t, mood):
    """Real eyes, visible only when the sunglasses slip."""
    for x in (39, 57):
        if mood == "sad":
            d.ellipse(t.box(x, 33, 4, 3), fill=EYE_YELLOW)
            d.rectangle(t.box(x, 33, 1, 2), fill=INK)
            d.line(t.pts((x - 4, 29), (x + 4, 31 if x < 48 else 27)), fill=INK)
    d.line(t.pts((37, 37), (37, 41)), fill=TEAR, width=t.w(2))


def cat_glasses(d, t, dy=0, glow=0):
    lens = LENS if not glow else (MAGIC if glow > 1 else MAGIC_GLOW)
    d.line(t.pts((24, 26 + dy), (31, 27 + dy)), fill=INK, width=t.w(2))
    d.line(t.pts((65, 27 + dy), (72, 26 + dy)), fill=INK, width=t.w(2))
    d.line(t.pts((45, 27 + dy), (51, 27 + dy)), fill=INK, width=t.w(2))
    for x in (38, 58):
        d.ellipse(t.box(x, 28 + dy, 8, 8), fill=(60, 60, 66, 255))
        d.ellipse(t.box(x, 28 + dy, 6.5, 6.5), fill=lens)
        d.point(t.p(x - 3, 25 + dy), fill=WHITE)
        d.point(t.p(x - 2, 24 + dy), fill=WHITE)


def cat_tiara(d, t, sparkle=False):
    d.polygon(t.pts((34, 14), (37, 6), (41, 10), (44, 3), (48, 1), (52, 3), (55, 10), (59, 6), (62, 14)), fill=SILVER)
    d.line(t.pts((35, 13), (61, 13)), fill=SILVER_DARK)
    d.ellipse(t.box(48, 8, 4, 4), fill=GEM)
    d.arc(t.box(48, 8, 2, 2), 180, 450, fill=GEM_LIGHT)
    if sparkle:
        x, y = t.p(54, 2)
        d.line([(x - 2, y), (x + 2, y)], fill=WHITE)
        d.line([(x, y - 2), (x, y + 2)], fill=WHITE)


def cat_pendant(d, t):
    d.polygon(t.pts((48, 50), (44, 47), (44, 53)), fill=SILVER)
    d.polygon(t.pts((48, 50), (52, 47), (52, 53)), fill=SILVER)


def draw_donut(c, t, *, swish=0, paw=None, glasses_dy=0, glow=0, sparkle=False, sad=False, tail=True):
    if tail:
        c.part(cat_tail, t, swish)
    c.part(cat_body, t, 3)
    c.part(cat_pauldron, t)
    c.part(cat_pendant, t)
    c.part(cat_paw, t, 54, 89)
    if paw is None:
        c.part(cat_paw, t, 40, 89)
    c.part(cat_head, t, sad)
    if sad:
        c.part(cat_eyes, t, "sad", ink=False)
    if glasses_dy is None:  # knocked off: they land on the cushion
        c.part(cat_glasses, Xf(t.ox + 48 * t.s * 0.4, t.oy + (95 - 28 * 0.6) * t.s, t.s * 0.6))
    else:
        c.part(cat_glasses, t, glasses_dy, glow)
    c.part(cat_tiara, t, sparkle)
    if paw is not None:
        c.part(cat_raised_paw, t, *paw)


# ---------------------------------------------------------------- Mongo
# Raptor space: side view facing right, feet on y~100.

def raptor_leg(d, t, hip, foot, color):
    hx, hy = hip
    fx, fy = foot
    knee = (hx + 6, hy + 10)
    d.ellipse(t.box(hx, hy, 8, 10), fill=color)
    d.line(t.pts(knee, (fx - 2, fy - 7)), fill=color, width=t.w(5))
    d.line(t.pts((fx - 2, fy - 7), (fx, fy - 1)), fill=color, width=t.w(4))
    d.polygon(t.pts((fx - 3, fy - 3), (fx + 8, fy - 2), (fx + 9, fy), (fx - 3, fy)), fill=color)
    d.line(t.pts((fx + 1, fy - 3), (fx + 2, fy - 7)), fill=WHITE)   # sickle claw


def raptor_body(d, t, tail_y):
    d.polygon(t.pts((30, 56), (12, 50 + tail_y), (2, 47 + tail_y * 1.5), (4, 51 + tail_y * 1.5), (14, 56 + tail_y), (30, 70)), fill=RAPTOR)
    d.ellipse(t.box(44, 64, 18, 12), fill=RAPTOR)
    d.ellipse(t.box(47, 70, 12, 6), fill=RAPTOR_BELLY)
    for x in (32, 40, 48):
        d.line(t.pts((x, 54), (x + 3, 60)), fill=RAPTOR_DARK, width=t.w(2))
    d.line(t.pts((14, 51 + tail_y), (8, 49 + tail_y)), fill=RAPTOR_DARK, width=t.w(2))


def raptor_head(d, t, head_y, jaw_open):
    o = head_y
    d.polygon(t.pts((56, 58), (64, 45 + o), (73, 45 + o), (66, 66)), fill=RAPTOR)
    d.ellipse(t.box(75, 42 + o, 11, 7), fill=RAPTOR)
    d.rounded_rectangle(t.box(84, 44 + o, 8, 4.5), radius=t.w(3), fill=RAPTOR)
    jaw = 47 + o + jaw_open
    d.polygon(t.pts((68, 47 + o), (92, 47 + o), (90, jaw + 2), (70, 50 + o)), fill=RAPTOR_BELLY)
    for x in range(74, 92, 3):
        d.polygon(t.pts((x, 47 + o), (x + 1, 49 + o), (x + 2, 47 + o)), fill=WHITE)
    d.line(t.pts((66, 38 + o), (78, 37 + o)), fill=RAPTOR_DARK, width=t.w(2))  # brow ridge
    d.ellipse(t.box(74, 40 + o, 2.5, 2), fill=EYE_YELLOW)
    d.line(t.pts((74, 39 + o), (74, 41 + o)), fill=INK)
    d.point(t.p(90, 42 + o), fill=INK)


def raptor_arm(d, t, swing):
    d.line(t.pts((62, 60), (68, 66 + swing)), fill=RAPTOR, width=t.w(3))
    d.line(t.pts((68, 66 + swing), (71, 68 + swing)), fill=WHITE)


def saddle(d, t):
    d.rounded_rectangle(t.box(43, 52, 10, 4), radius=t.w(2), fill=SADDLE)
    d.line(t.pts((34, 55), (52, 55)), fill=GOLD)
    d.line(t.pts((44, 56), (44, 70)), fill=SADDLE, width=t.w(2))  # girth strap


def reins(d, t, head_y, paw):
    d.line([paw, t.p(80, 46 + head_y)], fill=GOLD)


def draw_mongo_ride(c, *, lift=0, stride=0.0, head_y=0, jaw=0, tail_y=0, tuck=0, cheer=False, sparkle=False):
    r = Xf(0, lift)
    far = (40 + stride * -10, 100 - max(0, stride) * 4 - tuck)
    near = (40 + stride * 10, 100 - max(0, -stride) * 4 - tuck)
    c.part(raptor_leg, r, (38, 72), far, RAPTOR_DARK)
    c.part(raptor_body, r, tail_y)
    c.part(raptor_head, r, head_y, jaw)
    c.part(raptor_arm, r, round(stride * 2))
    c.part(saddle, r)
    # Donut rides at 45% scale, seated on the saddle
    ct = Xf(22, 10 + lift, 0.45)
    draw_donut(c, ct, paw=(30, 40) if cheer else None, sparkle=sparkle, tail=False)
    if not cheer:
        c.part(reins, r, head_y, ct.p(42, 86), ink=False)
    c.part(raptor_leg, r, (44, 72), near, RAPTOR)


# ---------------------------------------------------------------- scenery & props

def cushion(d, dy=0):
    d.rounded_rectangle([12, 84 + dy, 84, 98], radius=6, fill=VELVET)
    d.line([(18, 86 + dy), (78, 86 + dy)], fill=VELVET_LIGHT)
    for x in range(13, 84, 2):
        d.line([(x, 99), (x, 102 - (x // 2) % 2)], fill=GOLD)


def missile(d, x, y, trail):
    for k in range(trail, 0, -1):
        r = max(1, 3 - k // 2)
        tx = x - k * 4
        d.ellipse([tx - r, y - r + (k % 2), tx + r, y + r + (k % 2)], fill=MAGIC_GLOW)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=MAGIC_GLOW)
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=MAGIC)
    d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=WHITE)


def burst(d, x, y, r):
    for a in range(0, 360, 45):
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line([(x + dx * r * 0.4, y + dy * r * 0.4), (x + dx * r, y + dy * r)], fill=MAGIC)
    d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=WHITE)


def dots_bubble(d, n):
    d.rounded_rectangle([66, 2, 94, 14], radius=5, fill=WHITE)
    d.polygon([(70, 13), (74, 13), (68, 18)], fill=WHITE)
    for i in range(n):
        d.rectangle([71 + i * 7, 7, 73 + i * 7, 9], fill=INK)


def storm_cloud(d, phase):
    d.ellipse([60, 0, 76, 10], fill=CLOUD)
    d.ellipse([70, -2, 90, 10], fill=CLOUD)
    for i, x in enumerate((64, 70, 76, 82, 88)):
        y = 12 + (phase * 3 + i * 4) % 10
        d.line([(x, y), (x - 1, y + 3)], fill=TEAR)


def spellbook(d, page):
    d.polygon([(30, 58), (48, 62), (66, 58), (66, 82), (48, 86), (30, 82)], fill=SADDLE)
    d.polygon([(32, 59), (47, 63), (47, 83), (32, 80)], fill=(250, 246, 230, 255))
    d.polygon([(49, 63), (64, 59), (64, 80), (49, 83)], fill=(250, 246, 230, 255))
    for k in range(4):
        d.line([(35, 66 + k * 4), (44, 68 + k * 4)], fill=(170, 160, 190, 255))
        d.line([(52, 68 + k * 4), (61, 66 + k * 4)], fill=(170, 160, 190, 255))
    if page:  # a page mid-flip
        d.polygon([(48, 62), (48 + page * 3, 56), (48 + page * 3, 78), (48, 84)], fill=WHITE)
    d.ellipse([46, 70, 50, 74], fill=GEM)


def hearts_sparkles(d, i):
    for k, (x, y) in enumerate(((10, 20), (84, 30), (14, 60), (88, 64))):
        if (i + k) % 2 == 0:
            d.line([(x - 2, y), (x + 2, y)], fill=GOLD)
            d.line([(x, y - 2), (x, y + 2)], fill=GOLD)


# ---------------------------------------------------------------- rows

def sitting(i, **kw):
    bob = kw.pop("bob", 0)
    extra = kw.pop("extra", ())
    c = Canvas()
    c.part(cushion)
    draw_donut(c, Xf(0, bob), **kw)
    for fn, *args in extra:
        c.part(fn, *args, ink=fn not in (missile, burst, hearts_sparkles))
    return c.img


def row_idle(i):
    return sitting(i, bob=1 if i in (2, 3) else 0, swish=(0, 1, 2, 2, 1, 0)[i], sparkle=i == 4)


def ride(i):
    s = math.sin(i / FRAMES * 2 * math.pi)
    c = Canvas()
    draw_mongo_ride(c, lift=-1 if i % 3 == 0 else 0, stride=s, head_y=round(s), jaw=0, tail_y=round(-s * 2))
    return c.img


def row_run_right(i):
    return ride(i)


def row_run_left(i):
    return ImageOps.mirror(ride(i))


def row_wave(i):
    return sitting(i, paw=((26, 30), (22, 26), (26, 30), (22, 26), (26, 30), (22, 26))[i], swish=i % 2)


def row_jump(i):
    lift = (2, -2, -7, -8, -4, 2)[i]
    tuck = (0, 4, 8, 8, 4, 0)[i]
    c = Canvas()
    draw_mongo_ride(c, lift=lift, stride=0.0, head_y=-2 if lift < 0 else 0, jaw=3 if lift < -4 else 0,
                    tail_y=-lift // 2, tuck=tuck, cheer=lift < 0, sparkle=True)
    if lift < 0:
        c.part(hearts_sparkles, i, ink=False)
    return c.img


def row_failed(i):
    return sitting(i, bob=1, glasses_dy=(2, 5, None, None, None, None)[i], sad=i >= 2, swish=-1,
                   extra=((storm_cloud, i),))


def row_waiting(i):
    return sitting(i, swish=(0, 3, 0, 3, 0, 3)[i], extra=((dots_bubble, 1 + i % 3),))


def row_missiles(i):
    # charge, fire, fly, fly, impact, recharge
    glow = (1, 2, 2, 2, 2, 1)[i]
    extra = []
    if 1 <= i <= 3:
        for ex, ey, dy in ((38, 28, -1), (58, 28, 1)):
            x = ex + 10 + (i - 1) * 18
            extra.append((missile, x, ey + dy * (i - 1) * 3, min(i + 1, 4)))
    if i == 4:
        extra += [(burst, 86, 18, 8), (burst, 90, 40, 7)]
    if i == 5:
        extra += [(burst, 88, 26, 4)]
    return sitting(i, glow=glow, extra=extra)


def row_review(i):
    page = (0, 0, 2, 4, 0, 0)[i]
    return sitting(i, extra=((spellbook, page),), swish=i % 2)


ROW_FNS = [row_idle, row_run_right, row_run_left, row_wave, row_jump, row_failed, row_waiting, row_missiles, row_review]


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

    bg = (34, 26, 48, 255)  # dungeon purple, so the neon magic pops
    gif = []
    for f in preview:
        g = Image.new("RGBA", f.size, bg)
        g.alpha_composite(f)
        gif.append(g.convert("P", palette=Image.ADAPTIVE))
    gif[0].save(OUT / "preview.gif", save_all=True, append_images=gif[1:], duration=1100 // FRAMES, loop=0)

    meta = {"id": "princess-donut", "displayName": "Princess Donut",
            "description": "Crawler, Grand Champion show cat, and Mongo's mom.",
            "spritesheetPath": "spritesheet.webp"}
    (OUT / "pet.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {sheet.size[0]}x{sheet.size[1]} sheet to {OUT}")


if __name__ == "__main__":
    main()
