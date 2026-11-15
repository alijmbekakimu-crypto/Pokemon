"""Locations. The backyard: rainy November night, moon, house, fence, a fresh grave."""
import numpy as np
from engine import bayer, rect, line, px, ellipse, dither_blend

GROUND = 120          # first ground row
GRAVE = (100, 122)    # mound centre
WORLD_W, WORLD_H = 140, 160


def yard():
    W, H = WORLD_W, WORLD_H
    w = np.zeros((H, W, 3), np.uint8)
    bay = bayer(H, W)
    yy, xx = np.mgrid[0:H, 0:W]

    # sky gradient, Bayer-dithered between bands
    sky = [(10, 10, 26), (16, 15, 38), (26, 22, 56), (40, 32, 76), (58, 42, 90), (76, 52, 100)]
    for y in range(GROUND):
        t = y / (GROUND - 1) * (len(sky) - 1)
        i = int(t)
        f = t - i
        i2 = min(i + 1, len(sky) - 1)
        w[y] = np.where((f > bay[y])[:, None], sky[i2], sky[i])

    rng = np.random.default_rng(5)
    for _ in range(30):
        x, y = rng.integers(0, W), rng.integers(0, 54)
        w[y, x] = (150, 150, 200) if rng.random() < 0.7 else (232, 232, 255)

    # moon + halo
    mx, my, mr = 112, 28, 11
    d = np.hypot(xx - mx, yy - my)
    out = (d > mr) & (yy < GROUND)
    dither_blend(w, out, (52, 46, 98), np.clip(1 - (d - mr) / 22, 0, 1) * 0.9, bay)
    dither_blend(w, out, (84, 76, 132), np.clip(1 - (d - mr) / 9, 0, 1) * 0.8, bay)
    moon = d <= mr
    w[moon] = (238, 234, 214)
    shade = moon & (np.hypot(xx - (mx + 5), yy - (my - 3)) > mr)
    w[shade] = (198, 192, 196)
    for cx, cy, r in ((108, 24, 2), (115, 31, 3), (106, 32, 1.5), (117, 22, 1.2)):
        w[moon & (np.hypot(xx - cx, yy - cy) <= r)] = (212, 206, 202)

    # clouds drifting over the moon
    cloud = np.zeros((H, W), bool)
    for cx, cy, rx, ry in ((92, 40, 16, 3.5), (114, 37, 13, 4), (134, 41, 12, 3.5),
                           (18, 50, 18, 4), (42, 47, 12, 3), (64, 58, 14, 2.5)):
        cloud |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    w[cloud] = (34, 28, 64)
    edge = cloud & ~np.roll(cloud, 1, axis=0)
    near = np.hypot(xx - mx, yy - my) < 34
    w[edge & near] = (122, 112, 160)
    w[edge & ~near] = (54, 46, 88)

    # hills
    for x in range(W):
        h1 = int(103 + 4 * np.sin(x * 0.07) + 2 * np.sin(x * 0.19 + 1))
        w[h1:GROUND, x] = (24, 20, 46)
        h2 = int(110 + 3 * np.sin(x * 0.11 + 2))
        w[h2:GROUND, x] = (18, 15, 34)

    # house (left) with one warm window
    for y in range(70, 85):
        half = (y - 70) * 21 / 14
        rect(w, 20 - half, y, 21 + half, y + 1, (26, 20, 40))
        px(w, 20 + half, y, (70, 64, 108))
    rect(w, 29, 71, 33, 80, (26, 20, 40))
    rect(w, 3, 84, 38, GROUND, (20, 17, 34))
    rect(w, 37, 84, 38, GROUND, (50, 46, 80))
    rect(w, 22, 90, 31, 99, (255, 196, 110))
    rect(w, 22, 95, 31, 99, (236, 150, 76))
    rect(w, 26, 90, 27, 99, (92, 58, 40))
    rect(w, 22, 94, 31, 95, (92, 58, 40))
    rect(w, 21, 99, 32, 100, (60, 50, 70))
    rect(w, 7, 88, 14, 95, (30, 30, 54))
    rect(w, 9, 102, 16, GROUND, (12, 10, 20))
    px(w, 18, 101, (255, 222, 150))
    dither_blend(w, (np.hypot(xx - 18, yy - 101) < 5) & ~(np.hypot(xx - 18, yy - 101) < 1),
                 (120, 96, 80), 0.3, bay)

    # fence
    for x in range(40, W, 7):
        rect(w, x, 106, x + 2, GROUND, (30, 26, 48))
        px(w, x, 105, (30, 26, 48))
        px(w, x + 1, 106, (60, 56, 92))
    for y in (109, 114):
        rect(w, 40, y, W, y + 1, (28, 24, 44))
        rect(w, 40, y - 1, W, y, (48, 44, 76))

    # bare tree (right)
    tc = (18, 14, 30)
    for dx in (0, 1, 2):
        line(w, 128 + dx, GROUND, 127 + dx, 86, tc)
    for a, b in (((128, 92), (118, 78)), ((128, 88), (137, 74)), ((118, 78), (112, 72)),
                 ((137, 74), (139, 66)), ((128, 86), (126, 70)), ((126, 70), (121, 62)),
                 ((126, 70), (131, 60)), ((118, 78), (117, 68)), ((112, 72), (106, 70))):
        line(w, *a, *b, tc)
        line(w, a[0] + 1, a[1], b[0] + 1, b[1], tc)

    # ground
    gtop, gbot = np.array((32, 42, 46)), np.array((18, 22, 30))
    for y in range(GROUND, H):
        f = (y - GROUND) / (H - GROUND)
        w[y] = (gtop * (1 - f) + gbot * f).astype(np.uint8)
    speck = rng.random((H, W)) < 0.08
    w[speck & (yy >= GROUND)] = (38, 52, 54)
    for x in range(0, W, 2):
        if rng.random() < 0.6:
            px(w, x, GROUND - 1, (40, 60, 54))
    # window light spilling on the grass
    spill = (yy >= GROUND) & (yy < GROUND + 10) & (xx > 16 + (yy - GROUND)) & (xx < 34 + (yy - GROUND) * 1.5)
    dither_blend(w, spill, (70, 60, 56), 0.35, bay)

    # puddles (one reflects the moon)
    for cx, cy, rx, ry, moonref in ((38, 140, 12, 2.5, False), (72, 152, 9, 2, False), (122, 142, 11, 2.5, True)):
        ellipse(w, cx, cy, rx, ry, (40, 38, 74))
        ellipse(w, cx, cy - 0.6, rx - 2, ry - 1.2, (70, 64, 112))
        if moonref:
            rect(w, cx - 1, cy - 1, cx + 2, cy + 1, (206, 200, 196))

    # the grave
    gx, gy = GRAVE
    ellipse(w, gx, gy, 10, 3.5, (58, 40, 38))
    ellipse(w, gx, gy - 1, 8, 2, (80, 56, 48))
    rect(w, 106, 106, 108, 123, (112, 82, 60))
    rect(w, 103, 109, 111, 110, (112, 82, 60))
    rect(w, 107, 106, 108, 123, (150, 116, 86))
    for p in ((103, 110), (103, 111), (104, 112), (105, 112), (106, 111)):
        px(w, *p, (196, 54, 64))
    px(w, 104, 113, (255, 204, 72))
    for p, c in (((93, 119), (232, 232, 242)), ((95, 118), (240, 168, 190)),
                 ((97, 119), (232, 232, 242)), ((94, 120), (60, 110, 70)), ((96, 120), (60, 110, 70))):
        px(w, *p, c)
    return w


def splashes(w, t, seed=11, n=26):
    """Rain hitting the grass and the puddles; changes 12 times a second."""
    step = int(t * 12)
    rng = np.random.default_rng(seed * 1000 + step)
    H, W = w.shape[:2]
    xs = rng.integers(0, W, n)
    ys = rng.integers(GROUND + 1, H, n)
    for x, y in zip(xs, ys):
        px(w, x, y, (110, 118, 170))
        px(w, x - 1, y, (70, 76, 120))
        px(w, x + 1, y, (70, 76, 120))
    for cx, cy, rx in ((38, 140, 12), (72, 152, 9), (122, 142, 11)):
        k = rng.integers(-rx + 3, rx - 3)
        r = 1 + step % 3
        for dx in range(-r, r + 1):
            px(w, cx + k + dx, cy + (0 if abs(dx) == r else -1 if dx % 2 else 0), (150, 156, 210))
