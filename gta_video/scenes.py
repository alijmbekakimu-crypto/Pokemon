"""Процедурные фоны для глав видео (рисуются с нуля, без чужих ассетов)."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2304, 1296  # чуть больше 1920x1080, чтобы было куда панорамировать


def gradient(stops):
    """Вертикальный градиент: stops = [(позиция 0..1, (r,g,b)), ...]."""
    ys = np.linspace(0, 1, H)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
        arr[:, :, c] = col[:, None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


def glow(img, xy, radius, color, strength=1.0):
    """Мягкое свечение (солнце, луна, неон)."""
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for i in range(6, 0, -1):
        r = radius * i / 2.2
        k = strength / (i * 1.6)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=tuple(int(c * k) for c in color))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.8))
    return Image.fromarray(np.minimum(
        np.asarray(img, np.int32) + np.asarray(layer, np.int32), 255).astype(np.uint8))


def disc(img, xy, r, color):
    ImageDraw.Draw(img).ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=color)


def skyline(img, base_y, color, rng, min_h, max_h, min_w=40, max_w=140,
            windows=None, density=0.35, spires=False):
    d = ImageDraw.Draw(img)
    x = -20
    while x < W + 20:
        w = rng.randint(min_w, max_w)
        h = rng.randint(min_h, max_h)
        top = base_y - h
        d.rectangle([x, top, x + w, base_y + 400], fill=color)
        if spires and rng.random() < 0.15:
            d.rectangle([x + w // 2 - 3, top - 70, x + w // 2 + 3, top], fill=color)
        if windows:
            for wy in range(top + 12, base_y - 8, 18):
                for wx in range(x + 8, x + w - 10, 16):
                    if rng.random() < density:
                        d.rectangle([wx, wy, wx + 6, wy + 9], fill=rng.choice(windows))
        x += w + rng.randint(0, 12)


def hills(img, base_y, amp, color, rng, freq=3.0):
    d = ImageDraw.Draw(img)
    ph = [rng.random() * 6.28 for _ in range(3)]
    pts = [(0, H)]
    for x in range(0, W + 1, 8):
        t = x / W
        y = base_y - amp * (0.55 * math.sin(t * freq * 3.1 + ph[0])
                            + 0.3 * math.sin(t * freq * 7.3 + ph[1])
                            + 0.15 * math.sin(t * freq * 17 + ph[2]) + 0.5)
        pts.append((x, y))
    pts.append((W, H))
    d.polygon(pts, fill=color)


def palm(img, x, base_y, height, color, lean=0.15):
    d = ImageDraw.Draw(img)
    prev = (x, base_y)
    top = None
    for i in range(1, 31):
        t = i / 30
        px = x + lean * height * t * t
        py = base_y - height * t
        wdt = max(3, int(14 * (1 - t) + 5))
        d.line([prev, (px, py)], fill=color, width=wdt)
        prev = (px, py)
        top = (px, py)
    for a in range(0, 360, 26):
        ang = math.radians(a + 13)
        length = height * 0.36
        upper, lower = [], []
        for j in range(16):
            s = j / 15
            fx = top[0] + math.cos(ang) * length * s
            fy = top[1] - math.sin(ang) * length * s * 0.35 - length * 0.25 * s + (s * s) * length * 0.75
            half = 16 * math.sin(math.pi * min(s * 1.2, 1))  # лист шире в середине
            upper.append((fx, fy - half))
            lower.append((fx, fy + half))
        d.polygon(upper + lower[::-1], fill=color)
    disc(img, top, 18, color)


def snow_flakes(img, rng, n=900, color=(235, 240, 255)):
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y, r = rng.randint(0, W), rng.randint(0, H), rng.choice([1, 1, 2, 2, 3])
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def stars(img, rng, n=400, max_y=0.55):
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rng.randint(0, W), rng.randint(0, int(H * max_y))
        v = rng.randint(140, 255)
        d.point((x, y), fill=(v, v, v))


def finish(img, vignette=0.55):
    """Виньетка и лёгкое смягчение — общий «киношный» вид."""
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    mask = 1 - vignette * np.clip(dist - 0.35, 0, 1) ** 1.4
    arr = np.asarray(img, np.float32) * mask[:, :, None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


# ---------- сцены ----------

def night_city(rng):
    img = gradient([(0, (12, 6, 30)), (0.45, (70, 20, 90)), (0.7, (230, 70, 120)), (1, (40, 10, 40))])
    stars(img, rng, 300, 0.4)
    img = glow(img, (W * 0.5, H * 0.66), 260, (255, 90, 160), 0.8)
    skyline(img, int(H * 0.78), (40, 18, 60), rng, 150, 420, spires=True)
    skyline(img, int(H * 0.86), (14, 8, 24), rng, 120, 560, 70, 180,
            windows=[(255, 210, 120), (255, 160, 90), (120, 220, 255)], density=0.3, spires=True)
    ImageDraw.Draw(img).rectangle([0, int(H * 0.86), W, H], fill=(8, 4, 14))
    for x in (160, 2050):
        palm(img, x, int(H * 0.95), 620, (6, 3, 10), lean=0.2 if x < W / 2 else -0.2)
    return img


def snow_town(rng):
    img = gradient([(0, (8, 14, 34)), (0.6, (40, 60, 100)), (1, (90, 110, 150))])
    img = glow(img, (W * 0.78, H * 0.2), 70, (200, 215, 255), 0.6)
    disc(img, (W * 0.78, H * 0.2), 55, (225, 232, 250))
    hills(img, int(H * 0.62), 120, (30, 42, 70), rng, 2)
    d = ImageDraw.Draw(img)
    base = int(H * 0.8)
    x = 60
    while x < W:
        w, h = rng.randint(160, 300), rng.randint(140, 260)
        d.rectangle([x, base - h, x + w, base], fill=(18, 24, 42))
        d.polygon([(x - 20, base - h), (x + w / 2, base - h - 110), (x + w + 20, base - h)], fill=(225, 232, 245))
        for wx in range(x + 30, x + w - 40, 70):
            if rng.random() < 0.6:
                d.rectangle([wx, base - h + 50, wx + 30, base - h + 95], fill=(255, 196, 110))
        x += w + rng.randint(60, 180)
    # банк с колоннами
    bx = int(W * 0.42)
    d.rectangle([bx, base - 330, bx + 460, base], fill=(28, 32, 52))
    d.polygon([(bx - 30, base - 330), (bx + 230, base - 450), (bx + 490, base - 330)], fill=(220, 228, 242))
    for cx in range(bx + 40, bx + 440, 90):
        d.rectangle([cx, base - 300, cx + 26, base], fill=(60, 68, 96))
    d.rectangle([0, base, W, H], fill=(215, 222, 238))
    for _ in range(6):  # мигалки полиции
        img = glow(img, (rng.randint(100, W - 100), base - 10), 60,
                   rng.choice([(255, 40, 40), (40, 90, 255)]), 0.9)
    snow_flakes(img, rng, 1100)
    return img


def sunset_hills(rng):
    img = gradient([(0, (60, 40, 120)), (0.35, (240, 110, 110)), (0.6, (255, 190, 110)), (1, (120, 60, 70))])
    img = glow(img, (W * 0.35, H * 0.55), 260, (255, 200, 120), 0.9)
    disc(img, (W * 0.35, H * 0.55), 170, (255, 225, 160))
    hills(img, int(H * 0.62), 260, (120, 60, 90), rng, 1.5)
    skyline(img, int(H * 0.8), (80, 40, 70), rng, 80, 330, spires=True)
    hills(img, int(H * 0.9), 120, (40, 18, 36), rng, 2.5)
    for x in (120, 420, 1800, 2120):
        palm(img, x, H + 20, rng.randint(650, 900), (24, 10, 22), lean=rng.uniform(-0.25, 0.25))
    return img


def hood(rng):
    img = gradient([(0, (30, 70, 110)), (0.45, (220, 130, 80)), (0.7, (255, 180, 100)), (1, (60, 40, 40))])
    img = glow(img, (W * 0.7, H * 0.62), 200, (255, 170, 90), 0.8)
    skyline(img, int(H * 0.68), (90, 70, 90), rng, 180, 480, 60, 160, spires=True)
    d = ImageDraw.Draw(img)
    base = int(H * 0.86)
    x = -30
    while x < W:
        w, h = rng.randint(220, 360), rng.randint(150, 220)
        d.rectangle([x, base - h, x + w, base], fill=(26, 18, 26))
        d.polygon([(x - 15, base - h), (x + w / 2, base - h - 70), (x + w + 15, base - h)], fill=(20, 14, 20))
        x += w + rng.randint(30, 90)
    for px in range(80, W, 520):  # столбы и провода
        d.rectangle([px, base - 560, px + 12, base], fill=(15, 10, 15))
        d.rectangle([px - 50, base - 540, px + 62, base - 530], fill=(15, 10, 15))
    for k in range(3):
        pts = [(x2, base - 532 + k * 6 + 40 * math.sin((x2 % 520) / 520 * math.pi)) for x2 in range(0, W, 20)]
        d.line(pts, fill=(15, 10, 15), width=3)
    d.rectangle([0, base, W, H], fill=(22, 16, 20))
    for x in (700, 1500):
        palm(img, x, base, 820, (16, 10, 16), lean=0.12)
    return img


def jewelry(rng):
    img = gradient([(0, (10, 6, 24)), (0.6, (30, 14, 50)), (1, (12, 6, 20))])
    skyline(img, int(H * 0.75), (24, 14, 40), rng, 300, 700, 80, 200,
            windows=[(140, 120, 255), (255, 120, 200)], density=0.2)
    d = ImageDraw.Draw(img)
    d.rectangle([int(W * 0.25), int(H * 0.25), int(W * 0.75), H], fill=(16, 10, 26))
    # неоновый бриллиант
    cx, cy, s = W * 0.5, H * 0.47, 210
    pts = [(cx - s, cy - s * 0.35), (cx - s * 0.55, cy - s * 0.75), (cx + s * 0.55, cy - s * 0.75),
           (cx + s, cy - s * 0.35), (cx, cy + s)]
    layer = Image.new("RGB", img.size)
    ld = ImageDraw.Draw(layer)
    for wdt, col in ((40, (120, 30, 120)), (18, (255, 80, 220)), (6, (255, 220, 255))):
        ld.line(pts + [pts[0]], fill=col, width=wdt, joint="curve")
        ld.line([(cx - s, cy - s * 0.35), (cx + s, cy - s * 0.35)], fill=col, width=max(4, wdt // 2))
    blurred = layer.filter(ImageFilter.GaussianBlur(25))
    arr = np.asarray(img, np.int32) + np.asarray(blurred, np.int32) * 2 + np.asarray(layer, np.int32)
    img = Image.fromarray(np.minimum(arr, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([int(W * 0.3), int(H * 0.78), int(W * 0.7), int(H * 0.8)], fill=(255, 120, 230))
    img = glow(img, (W * 0.5, H * 0.79), 120, (255, 60, 200), 0.6)
    for x in range(int(W * 0.32), int(W * 0.68), 180):  # витрины
        d.rectangle([x, int(H * 0.82), x + 140, H], fill=(60, 30, 80))
        d.rectangle([x + 10, int(H * 0.84), x + 130, H], fill=(140, 110, 200))
    return img


def desert(rng):
    img = gradient([(0, (110, 150, 190)), (0.45, (230, 190, 130)), (0.7, (240, 160, 90)), (1, (150, 90, 50))])
    img = glow(img, (W * 0.2, H * 0.28), 120, (255, 230, 170), 0.8)
    disc(img, (W * 0.2, H * 0.28), 80, (255, 245, 210))
    d = ImageDraw.Draw(img)
    for _ in range(4):  # столовые горы
        x, w, h = rng.randint(0, W), rng.randint(300, 700), rng.randint(120, 260)
        base = int(H * 0.66)
        d.polygon([(x - 80, base), (x, base - h), (x + w, base - h), (x + w + 80, base)], fill=(150, 80, 60))
    d.rectangle([0, int(H * 0.66), W, H], fill=(190, 130, 80))
    hills(img, int(H * 0.82), 80, (120, 70, 45), rng, 1.5)
    base = int(H * 0.88)
    for x in range(100, W, 430):  # трейлеры
        w = rng.randint(260, 340)
        d.rounded_rectangle([x, base - 120, x + w, base], radius=24, fill=(60, 36, 28))
        d.rectangle([x + 30, base - 90, x + 80, base - 55], fill=(255, 200, 120))
    for x in (950, 1900):  # кактусы
        d.rectangle([x, base - 300, x + 36, base], fill=(40, 30, 20))
        d.rectangle([x - 60, base - 200, x, base - 176], fill=(40, 30, 20))
        d.rectangle([x - 60, base - 270, x - 36, base - 176], fill=(40, 30, 20))
        d.rectangle([x + 36, base - 160, x + 90, base - 136], fill=(40, 30, 20))
        d.rectangle([x + 66, base - 240, x + 90, base - 136], fill=(40, 30, 20))
    d.rectangle([0, base, W, H], fill=(70, 42, 30))
    return img


def fib_tower(rng):
    img = gradient([(0, (20, 30, 45)), (0.6, (70, 90, 115)), (1, (30, 38, 50))])
    skyline(img, int(H * 0.82), (40, 52, 70), rng, 200, 520, 60, 160, spires=True)
    d = ImageDraw.Draw(img)
    tx, tw = int(W * 0.4), 520
    d.rectangle([tx, 40, tx + tw, H], fill=(22, 30, 44))
    d.polygon([(tx, 40), (tx + tw // 2, -60), (tx + tw, 40)], fill=(22, 30, 44))
    for wy in range(90, H, 34):
        for wx in range(tx + 20, tx + tw - 20, 40):
            v = rng.random()
            col = (150, 190, 230) if v < 0.25 else (40, 60, 85)
            d.rectangle([wx, wy, wx + 26, wy + 20], fill=col)
    # вертолёт
    hx, hy = int(W * 0.78), int(H * 0.25)
    d.ellipse([hx - 70, hy - 30, hx + 70, hy + 30], fill=(10, 14, 20))
    d.rectangle([hx + 60, hy - 8, hx + 220, hy + 6], fill=(10, 14, 20))
    d.rectangle([hx - 160, hy - 46, hx + 160, hy - 40], fill=(10, 14, 20))
    d.rectangle([hx - 4, hy - 46, hx + 4, hy - 28], fill=(10, 14, 20))
    img = glow(img, (hx, hy + 220), 120, (200, 220, 255), 0.35)
    ImageDraw.Draw(img).polygon([(hx - 20, hy + 20), (hx + 20, hy + 20), (hx + 260, H), (hx - 260, H)],
                                fill=(70, 85, 105))
    return img


def graveyard(rng):
    img = gradient([(0, (4, 6, 16)), (0.65, (26, 34, 60)), (1, (60, 70, 100))])
    stars(img, rng, 450, 0.5)
    img = glow(img, (W * 0.7, H * 0.22), 110, (210, 220, 255), 0.8)
    disc(img, (W * 0.7, H * 0.22), 85, (235, 238, 250))
    hills(img, int(H * 0.7), 100, (20, 26, 44), rng, 2)
    d = ImageDraw.Draw(img)
    base = int(H * 0.82)
    d.rectangle([0, base, W, H], fill=(190, 198, 218))
    for i in range(14):  # надгробия
        x = 80 + i * 165 + rng.randint(-30, 30)
        h = rng.randint(120, 200)
        y = base + rng.randint(-20, 60)
        if rng.random() < 0.4:
            d.rectangle([x + 30, y - h - 40, x + 50, y], fill=(14, 16, 26))
            d.rectangle([x, y - h, x + 80, y - h + 20], fill=(14, 16, 26))
        else:
            d.rounded_rectangle([x, y - h, x + 90, y], radius=40, fill=(14, 16, 26))
    # одна свежая разрытая могила
    d.ellipse([int(W * 0.46), base + 120, int(W * 0.6), base + 190], fill=(40, 30, 28))
    d.line([(int(W * 0.63), base + 160), (int(W * 0.66), base - 40)], fill=(14, 16, 26), width=10)
    snow_flakes(img, rng, 600)
    return img


def gold_vault(rng):
    img = gradient([(0, (10, 8, 4)), (0.5, (40, 28, 10)), (1, (8, 6, 2))])
    img = glow(img, (W * 0.5, H * 0.5), 420, (255, 180, 60), 0.75)
    d = ImageDraw.Draw(img)
    cx, cy = W * 0.5, H * 0.45
    for r, col in ((430, (50, 40, 30)), (400, (90, 75, 50)), (330, (60, 50, 36)), (120, (110, 90, 60)), (60, (60, 50, 36))):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    for a in range(0, 360, 30):
        ang = math.radians(a)
        d.line([(cx + math.cos(ang) * 130, cy + math.sin(ang) * 130),
                (cx + math.cos(ang) * 320, cy + math.sin(ang) * 320)], fill=(40, 32, 22), width=14)
    base = H - 40
    for row in range(5):  # штабель слитков
        n = 8 - row
        for i in range(n):
            x = int(W * 0.5 - n * 115 / 2 + i * 115)
            y = base - row * 52
            d.polygon([(x, y), (x + 110, y), (x + 95, y - 48), (x + 15, y - 48)], fill=(230, 170, 50))
            d.polygon([(x + 15, y - 48), (x + 95, y - 48), (x + 88, y - 42), (x + 22, y - 42)], fill=(255, 225, 120))
    return img


def cliff_sea(rng):
    img = gradient([(0, (40, 10, 30)), (0.4, (180, 40, 40)), (0.58, (255, 120, 60)), (0.6, (120, 30, 40)), (1, (20, 6, 14))])
    sun = (W * 0.6, H * 0.56)
    img = glow(img, sun, 250, (255, 120, 60), 0.9)
    disc(img, sun, 150, (255, 190, 110))
    d = ImageDraw.Draw(img)
    hor = int(H * 0.6)
    d.rectangle([0, hor, W, H], fill=(60, 14, 26))
    for y in range(hor + 6, H, 14):  # отражение солнца на воде
        w = int(260 * (1 - (y - hor) / (H - hor)) + 40)
        if rng.random() < 0.8:
            d.rectangle([sun[0] - w + rng.randint(-30, 30), y, sun[0] + w + rng.randint(-30, 30), y + 4], fill=(255, 150, 90))
    d.polygon([(0, int(H * 0.42)), (520, int(H * 0.44)), (780, int(H * 0.55)), (840, H), (0, H)], fill=(18, 4, 10))
    # машина на краю обрыва
    d.rounded_rectangle([560, int(H * 0.44) - 70, 800, int(H * 0.44) + 4], radius=20, fill=(10, 2, 6))
    disc(img, (610, int(H * 0.44) + 4), 26, (10, 2, 6))
    disc(img, (750, int(H * 0.44) + 4), 26, (10, 2, 6))
    return img


def sunrise_city(rng):
    img = gradient([(0, (120, 150, 210)), (0.45, (255, 200, 170)), (0.65, (255, 220, 150)), (1, (110, 90, 110))])
    img = glow(img, (W * 0.5, H * 0.7), 300, (255, 220, 150), 0.8)
    disc(img, (W * 0.5, H * 0.7), 160, (255, 240, 200))
    skyline(img, int(H * 0.78), (150, 120, 150), rng, 150, 450, spires=True)
    skyline(img, int(H * 0.88), (60, 40, 70), rng, 80, 300, 60, 160)
    ImageDraw.Draw(img).rectangle([0, int(H * 0.88), W, H], fill=(40, 26, 46))
    for x in (90, 2150):
        palm(img, x, H + 30, 900, (30, 18, 36), lean=0.2 if x < W / 2 else -0.2)
    return img


# ---------- сцены для GTA 6 (Леонида / Вайс-Сити) ----------

def night_vice(rng):
    img = gradient([(0, (8, 6, 28)), (0.4, (40, 20, 90)), (0.66, (255, 70, 150)), (0.72, (40, 200, 220)), (1, (6, 10, 24))])
    stars(img, rng, 250, 0.35)
    img = glow(img, (W * 0.5, H * 0.66), 300, (255, 80, 170), 0.9)
    skyline(img, int(H * 0.74), (50, 22, 80), rng, 160, 460, spires=True)
    skyline(img, int(H * 0.8), (12, 8, 28), rng, 100, 520, 70, 180,
            windows=[(255, 90, 200), (60, 230, 255), (255, 220, 140)], density=0.28, spires=True)
    d = ImageDraw.Draw(img)
    hor = int(H * 0.8)
    d.rectangle([0, hor, W, H], fill=(10, 8, 30))
    for y in range(hor + 8, H, 12):  # отражение неона в воде
        for _ in range(10):
            x = rng.randint(0, W)
            d.rectangle([x, y, x + rng.randint(30, 160), y + 3],
                        fill=rng.choice([(255, 80, 190), (60, 210, 240), (120, 60, 160)]))
    for x in (int(W * 0.06), int(W * 0.92)):
        palm(img, x, H + 40, int(min(W, H) * 0.72), (4, 3, 12), lean=0.2 if x < W / 2 else -0.2)
    return img


def beach_vice(rng):
    img = gradient([(0, (60, 170, 230)), (0.5, (255, 190, 200)), (0.62, (255, 210, 170)), (0.63, (40, 170, 190)), (0.8, (60, 200, 200)), (0.81, (245, 220, 170)), (1, (230, 200, 150))])
    img = glow(img, (W * 0.8, H * 0.28), 150, (255, 240, 200), 0.7)
    d = ImageDraw.Draw(img)
    base = int(H * 0.62)
    x = int(W * 0.02)
    pastel = [(255, 170, 200), (130, 220, 220), (255, 230, 160), (200, 180, 255), (255, 255, 240)]
    while x < W * 0.6:  # арт-деко отели
        w, h = rng.randint(180, 280), rng.randint(220, 420)
        col = rng.choice(pastel)
        d.rectangle([x, base - h, x + w, base], fill=col)
        d.rectangle([x + w // 2 - 20, base - h - 60, x + w // 2 + 20, base - h], fill=col)
        for wy in range(base - h + 30, base - 20, 46):
            d.rectangle([x + 16, wy, x + w - 16, wy + 14], fill=tuple(int(c * 0.75) for c in col))
        x += w + rng.randint(10, 40)
    for _ in range(40):  # блики на воде
        y = rng.randint(int(H * 0.64), int(H * 0.79))
        x = rng.randint(0, W)
        d.rectangle([x, y, x + rng.randint(40, 120), y + 3], fill=(220, 255, 255))
    for x in range(int(W * 0.05), W, int(W * 0.17)):
        palm(img, x + rng.randint(-40, 40), H + 30, rng.randint(int(H * 0.55), int(H * 0.75)),
             (30, 60, 50), lean=rng.uniform(-0.25, 0.25))
    return img


def prison(rng):
    img = gradient([(0, (30, 30, 60)), (0.5, (200, 110, 90)), (0.72, (240, 160, 110)), (1, (50, 40, 50))])
    img = glow(img, (W * 0.25, H * 0.66), 200, (255, 170, 110), 0.7)
    d = ImageDraw.Draw(img)
    base = int(H * 0.8)
    d.rectangle([int(W * 0.35), base - 260, int(W * 0.95), base], fill=(40, 34, 44))
    for wx in range(int(W * 0.37), int(W * 0.93), 60):
        d.rectangle([wx, base - 200, wx + 18, base - 150], fill=(255, 220, 140))
    tx = int(W * 0.72)  # вышка с прожектором
    d.rectangle([tx, base - 640, tx + 30, base], fill=(20, 16, 24))
    d.rectangle([tx + 110, base - 640, tx + 140, base], fill=(20, 16, 24))
    d.rectangle([tx - 30, base - 740, tx + 170, base - 640], fill=(20, 16, 24))
    d.polygon([(tx - 50, base - 740), (tx + 70, base - 800), (tx + 190, base - 740)], fill=(20, 16, 24))
    beam = Image.new("RGB", img.size)
    ImageDraw.Draw(beam).polygon([(tx + 70, base - 690), (int(W * 0.05), base + 60), (int(W * 0.3), base + 160)],
                                 fill=(120, 110, 80))
    beam = beam.filter(ImageFilter.GaussianBlur(30))
    img = Image.fromarray(np.minimum(np.asarray(img, np.int32) + np.asarray(beam, np.int32), 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([0, base, W, H], fill=(36, 30, 36))
    fy = int(H * 0.86)  # забор с колючей проволокой
    for x in range(0, W, 150):
        d.rectangle([x, fy - 420, x + 12, H], fill=(14, 12, 16))
    for y in range(fy - 400, H, 34):
        d.line([(0, y), (W, y)], fill=(30, 26, 32), width=2)
    for x in range(-400, W + 400, 34):
        d.line([(x, fy - 400), (x + 400, H)], fill=(30, 26, 32), width=2)
    for x in range(0, W, 46):
        d.ellipse([x, fy - 450, x + 46, fy - 404], outline=(14, 12, 16), width=4)
    return img


def keys(rng):
    img = gradient([(0, (80, 160, 220)), (0.5, (255, 200, 160)), (0.58, (255, 170, 120)), (0.59, (30, 150, 170)), (1, (10, 70, 100))])
    sun = (W * 0.7, H * 0.52)
    img = glow(img, sun, 180, (255, 200, 140), 0.8)
    disc(img, sun, 100, (255, 225, 170))
    d = ImageDraw.Draw(img)
    hor = int(H * 0.59)
    for i in range(3):  # островки
        x = rng.randint(0, int(W * 0.6))
        w = rng.randint(250, 500)
        d.ellipse([x, hor - 25, x + w, hor + 25], fill=(30, 70, 50))
        for k in range(3):
            palm(img, x + w * (k + 1) // 4, hor, rng.randint(120, 200), (20, 50, 40), lean=0.1)
    by = int(H * 0.5)  # длинный мост через острова
    d.rectangle([0, by, W, by + 22], fill=(60, 60, 80))
    for x in range(30, W, 140):
        d.rectangle([x, by + 22, x + 22, hor + 10], fill=(60, 60, 80))
    for y in range(hor + 10, H, 16):
        w = int(220 * (1 - (y - hor) / (H - hor)) + 30)
        d.rectangle([sun[0] - w + rng.randint(-20, 20), y, sun[0] + w, y + 4], fill=(255, 200, 150))
    bx, bb = int(W * 0.18), int(H * 0.82)  # скоростной катер
    d.polygon([(bx, bb), (bx + 520, bb), (bx + 600, bb - 70), (bx + 40, bb - 70)], fill=(15, 20, 30))
    d.polygon([(bx + 180, bb - 70), (bx + 380, bb - 70), (bx + 330, bb - 140), (bx + 220, bb - 140)], fill=(15, 20, 30))
    for k in range(16):  # пена за катером
        d.ellipse([bx - 40 - k * 50, bb - 10 + rng.randint(-8, 8), bx + 20 - k * 50, bb + 14], fill=(230, 245, 250))
    return img


def neon_heist(rng):
    return jewelry(rng)


def night_club(rng):
    img = gradient([(0, (6, 4, 18)), (0.7, (24, 10, 40)), (1, (10, 6, 20))])
    d = ImageDraw.Draw(img)
    # лучи прожекторов
    beams = Image.new("RGB", img.size)
    bd = ImageDraw.Draw(beams)
    for i, col in enumerate([(255, 60, 180), (60, 220, 255), (180, 80, 255), (255, 200, 80)]):
        x0 = int(W * (0.2 + i * 0.2))
        bd.polygon([(x0, int(H * 0.62)), (x0 - 300 + i * 180, 0), (x0 - 140 + i * 180, 0)], fill=col)
    beams = beams.filter(ImageFilter.GaussianBlur(35))
    img = Image.fromarray(np.minimum(np.asarray(img, np.int32) + (np.asarray(beams, np.float32) * 0.55).astype(np.int32), 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    base = int(H * 0.62)
    d.rectangle([int(W * 0.1), base, int(W * 0.9), H], fill=(14, 10, 22))
    layer = Image.new("RGB", img.size)
    ld = ImageDraw.Draw(layer)
    for wdt, col in ((30, (90, 20, 90)), (12, (255, 80, 210)), (4, (255, 220, 255))):
        ld.rounded_rectangle([int(W * 0.22), base + 50, int(W * 0.78), base + 210], radius=60, outline=col, width=wdt)
        for k in range(5):  # «звёзды» на вывеске
            cx = int(W * (0.3 + k * 0.1))
            ld.line([(cx - 40, base + 130), (cx + 40, base + 130)], fill=col, width=max(3, wdt // 2))
            ld.line([(cx, base + 90), (cx, base + 170)], fill=col, width=max(3, wdt // 2))
    img = Image.fromarray(np.minimum(np.asarray(img, np.int32) + np.asarray(layer.filter(ImageFilter.GaussianBlur(18)), np.int32) * 2
                                     + np.asarray(layer, np.int32), 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for x in range(int(W * 0.12), int(W * 0.88), 300):  # ряд машин у входа
        y = H - 40
        d.rounded_rectangle([x, y - 110, x + 260, y - 20], radius=30, fill=(8, 6, 14))
        d.rounded_rectangle([x + 50, y - 160, x + 200, y - 100], radius=26, fill=(8, 6, 14))
        disc(img, (x + 55, y - 20), 28, (4, 3, 8))
        disc(img, (x + 205, y - 20), 28, (4, 3, 8))
    return img


def swamp(rng):
    img = gradient([(0, (6, 14, 18)), (0.55, (30, 60, 60)), (0.62, (120, 150, 120)), (0.63, (20, 40, 40)), (1, (6, 14, 16))])
    stars(img, rng, 200, 0.45)
    moon = (W * 0.3, H * 0.25)
    img = glow(img, moon, 100, (200, 255, 210), 0.7)
    disc(img, moon, 70, (225, 245, 225))
    d = ImageDraw.Draw(img)
    hor = int(H * 0.63)
    for y in range(hor + 6, H, 16):
        w = int(100 * (1 - (y - hor) / (H - hor)) + 20)
        d.rectangle([moon[0] - w, y, moon[0] + w, y + 3], fill=(150, 190, 160))
    for _ in range(10):  # мангровые деревья
        x = rng.randint(0, W)
        h = rng.randint(200, 480)
        col = (6, 16, 14)
        for k in range(6):
            d.line([(x, hor - h * 0.4), (x - 80 + k * 32, hor + rng.randint(0, 30))], fill=col, width=6)
        d.rectangle([x - 10, hor - h, x + 10, hor - h * 0.4], fill=col)
        d.ellipse([x - h * 0.45, hor - h * 1.25, x + h * 0.45, hor - h * 0.75], fill=col)
    ax, ay = int(W * 0.58), int(H * 0.86)  # аэролодка
    d.polygon([(ax, ay), (ax + 420, ay), (ax + 460, ay - 40), (ax - 20, ay - 40)], fill=(4, 10, 10))
    d.ellipse([ax + 260, ay - 260, ax + 440, ay - 40], outline=(4, 10, 10), width=12)
    d.rectangle([ax + 120, ay - 120, ax + 150, ay - 40], fill=(4, 10, 10))
    for _ in range(2):  # глаза аллигатора
        ex = rng.randint(int(W * 0.1), int(W * 0.45))
        ey = rng.randint(int(H * 0.72), int(H * 0.9))
        disc(img, (ex, ey), 7, (255, 220, 80))
        disc(img, (ex + 30, ey), 7, (255, 220, 80))
    return img


def sunrise_vice(rng):
    return sunrise_city(rng)


SCENES = {f.__name__: f for f in (night_city, snow_town, sunset_hills, hood, jewelry, desert,
                                  fib_tower, graveyard, gold_vault, cliff_sea, sunrise_city,
                                  night_vice, beach_vice, prison, keys, neon_heist, night_club,
                                  swamp, sunrise_vice)}


def render(scene, path, seed=7, size=(2304, 1296)):
    """size=(ширина, высота): горизонтальный или вертикальный кадр."""
    global W, H
    W, H = size
    rng = random.Random(seed)
    finish(SCENES[scene](rng)).save(path)