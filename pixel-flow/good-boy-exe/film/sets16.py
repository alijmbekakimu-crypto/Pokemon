"""Film locations (16:9). World height 180, ground row G=150. All procedural."""
import functools
import numpy as np
from engine import bayer, rect, line, px, ellipse, dither_blend, text_mask, _stamp
import cast

H = 180
G = 150
K = (22, 18, 38)

SKIES = {
    'night': [(10, 10, 26), (16, 15, 38), (26, 22, 56), (40, 32, 76), (58, 42, 90), (76, 52, 100)],
    'dawn': [(40, 50, 100), (90, 80, 140), (170, 110, 150), (236, 150, 130), (255, 196, 140), (255, 220, 160)],
    'dusk': [(30, 26, 70), (70, 46, 100), (140, 70, 110), (220, 110, 100), (250, 150, 100), (255, 180, 120)],
    'day': [(120, 140, 170), (138, 156, 184), (156, 170, 196), (172, 184, 206), (188, 198, 216), (200, 208, 222)],
}


def _sky(w, kind, ground=G):
    Hh, W = w.shape[:2]
    bay = bayer(Hh, W)
    sky = SKIES[kind]
    for y in range(ground):
        t = y / max(ground - 1, 1) * (len(sky) - 1)
        i = int(t)
        f = t - i
        i2 = min(i + 1, len(sky) - 1)
        w[y] = np.where((f > bay[y])[:, None], sky[i2], sky[i])


def _stars(w, n, ymax, seed=5):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, w.shape[1]), rng.integers(0, ymax)
        w[y, x] = (150, 150, 200) if rng.random() < 0.7 else (232, 232, 255)


def _moon(w, mx, my, mr, ground=G):
    Hh, W = w.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    bay = bayer(Hh, W)
    d = np.hypot(xx - mx, yy - my)
    out = (d > mr) & (yy < ground)
    dither_blend(w, out, (52, 46, 98), np.clip(1 - (d - mr) / (mr * 2), 0, 1) * 0.9, bay)
    dither_blend(w, out, (84, 76, 132), np.clip(1 - (d - mr) / (mr * 0.8), 0, 1) * 0.8, bay)
    moon = d <= mr
    w[moon] = (238, 234, 214)
    w[moon & (np.hypot(xx - (mx + mr * 0.45), yy - (my - mr * 0.3)) > mr)] = (198, 192, 196)
    rng = np.random.default_rng(int(mx))
    for _ in range(5):
        cx, cy = mx + rng.uniform(-mr * .6, mr * .5), my + rng.uniform(-mr * .5, mr * .6)
        w[moon & (np.hypot(xx - cx, yy - cy) <= rng.uniform(1, mr * .25))] = (212, 206, 202)


def _sun(w, sx, sy, r, ground=G):
    Hh, W = w.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.hypot(xx - sx, yy - sy)
    bay = bayer(Hh, W)
    above = yy < ground
    dither_blend(w, above & (d > r), (255, 226, 170), np.clip(1 - (d - r) / (r * 3), 0, 1) * 0.8, bay)
    w[above & (d <= r)] = (255, 244, 210)


def _clouds(w, blobs, body, edge):
    Hh, W = w.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    m = np.zeros((Hh, W), bool)
    for cx, cy, rx, ry in blobs:
        m |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    w[m] = body
    w[m & ~np.roll(m, 1, axis=0)] = edge


def _hills(w, ground, c1, c2, seed=0):
    W = w.shape[1]
    for x in range(W):
        h1 = int(ground - 18 + 5 * np.sin(x * 0.03 + seed) + 3 * np.sin(x * 0.11 + 1 + seed))
        w[h1:ground, x] = c1
        h2 = int(ground - 9 + 3 * np.sin(x * 0.07 + 2 + seed))
        w[h2:ground, x] = c2


def _ground(w, ground, top, bot, speck, seed=1):
    Hh, W = w.shape[:2]
    top, bot = np.array(top), np.array(bot)
    for y in range(ground, Hh):
        f = (y - ground) / max(Hh - ground, 1)
        w[y] = (top * (1 - f) + bot * f).astype(np.uint8)
    rng = np.random.default_rng(seed)
    yy = np.mgrid[0:Hh, 0:W][0]
    w[(rng.random((Hh, W)) < 0.07) & (yy >= ground)] = speck


def _house(w, x, ground, snow=False, lit=True, door_open=0.0):
    """Two-storey house, front at x..x+96."""
    roof, wall, rim = (26, 20, 40), (22, 18, 36), (70, 64, 108)
    for y in range(ground - 92, ground - 66):
        half = (y - (ground - 92)) * 54 / 26
        rect(w, x + 48 - half, y, x + 49 + half, y + 1, roof)
        px(w, x + 48 + half, y, rim)
        if snow:
            px(w, x + 48 + half, y - 1, (220, 226, 244))
            px(w, x + 48 - half, y - 1, (200, 206, 230))
    rect(w, x + 66, ground - 96, x + 72, ground - 80, roof)
    rect(w, x + 2, ground - 66, x + 96, ground, wall)
    rect(w, x + 95, ground - 66, x + 96, ground, (50, 46, 80))
    warm, warm2, frame = (255, 196, 110), (236, 150, 76), (92, 58, 40)
    for wx, wy in ((x + 14, ground - 56), (x + 62, ground - 56), (x + 62, ground - 30)):
        if lit:
            rect(w, wx, wy, wx + 16, wy + 14, warm)
            rect(w, wx, wy + 8, wx + 16, wy + 14, warm2)
        else:
            rect(w, wx, wy, wx + 16, wy + 14, (30, 30, 54))
        rect(w, wx + 7, wy, wx + 9, wy + 14, frame)
        rect(w, wx, wy + 6, wx + 16, wy + 8, frame)
        rect(w, wx - 1, wy + 14, wx + 17, wy + 15, (60, 50, 70))
        if snow:
            rect(w, wx - 1, wy - 1, wx + 17, wy, (220, 226, 244))
    # door
    dx = x + 22
    rect(w, dx, ground - 34, dx + 18, ground, (12, 10, 20))
    if door_open > 0:
        ow = int(18 * door_open)
        rect(w, dx, ground - 34, dx + ow, ground, (255, 214, 150))
    rect(w, dx - 2, ground - 36, dx + 20, ground - 34, (40, 32, 54))
    px(w, dx + 24, ground - 30, (255, 222, 150))
    # porch light glow
    Hh, W = w.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.hypot(xx - (dx + 24), yy - (ground - 30))
    dither_blend(w, (d < 7) & (d > 1), (120, 96, 80), 0.3)


def _fence(w, x0, x1, ground, snow=False, col=(30, 26, 48)):
    for x in range(x0, x1, 9):
        rect(w, x, ground - 18, x + 3, ground, col)
        px(w, x + 1, ground - 19, col)
        px(w, x + 2, ground - 18, (60, 56, 92))
        if snow:
            rect(w, x, ground - 20, x + 3, ground - 18, (226, 230, 248))
    for y in (ground - 14, ground - 7):
        rect(w, x0, y, x1, y + 2, (28, 24, 44))
        rect(w, x0, y - 1, x1, y, (220, 226, 244) if snow else (48, 44, 76))


def _tree(w, x, ground, s=1.0, col=(18, 14, 30), snow=False):
    for dx in range(int(3 * s)):
        line(w, x + dx, ground, x + dx - 1, ground - 46 * s, col)
    br = (((0, -36), (-14, -56)), ((0, -40), (14, -62)), ((-14, -56), (-22, -64)), ((14, -62), (18, -74)),
          ((0, -46), (-2, -72)), ((-2, -72), (-8, -84)), ((-2, -72), (6, -88)), ((-14, -56), (-15, -70)),
          ((-22, -64), (-30, -66)), ((14, -62), (24, -66)))
    for (ax, ay), (bx, by) in br:
        a = (x + ax * s, ground + ay * s)
        b = (x + bx * s, ground + by * s)
        line(w, *a, *b, col)
        line(w, a[0] + 1, a[1], b[0] + 1, b[1], col)
        if snow:
            line(w, a[0], a[1] - 1, b[0], b[1] - 1, (200, 206, 232))


def _puddles(w, spots, moon_idx=None):
    for i, (cx, cy, rx, ry) in enumerate(spots):
        ellipse(w, cx, cy, rx, ry, (40, 38, 74))
        ellipse(w, cx, cy - 0.6, rx - 2, max(ry - 1.2, 0.5), (70, 64, 112))
        if i == moon_idx:
            rect(w, cx - 1, cy - 1, cx + 2, cy + 1, (206, 200, 196))


def _grave(w, gx, gy, collar=True, flowers=True, extra_tag=False):
    ellipse(w, gx, gy, 12, 4, (58, 40, 38))
    ellipse(w, gx, gy - 1, 10, 2.4, (80, 56, 48))
    sx = gx + 8
    rect(w, sx, gy - 18, sx + 2, gy + 1, (112, 82, 60))
    rect(w, sx - 4, gy - 14, sx + 6, gy - 13, (112, 82, 60))
    rect(w, sx + 1, gy - 18, sx + 2, gy + 1, (150, 116, 86))
    if collar:
        for p in ((sx - 4, gy - 13), (sx - 4, gy - 12), (sx - 3, gy - 11), (sx - 2, gy - 11), (sx - 1, gy - 12)):
            px(w, *p, (196, 54, 64))
        px(w, sx - 3, gy - 10, (255, 204, 72))
    if extra_tag:
        px(w, sx + 4, gy - 12, (150, 160, 190))
        px(w, sx + 4, gy - 11, (96, 236, 255))
    if flowers:
        for p, c in (((gx - 8, gy - 3), (232, 232, 242)), ((gx - 6, gy - 4), (240, 168, 190)),
                     ((gx - 4, gy - 3), (232, 232, 242)), ((gx - 7, gy - 2), (60, 110, 70))):
            px(w, *p, c)


GRAVE_X = 262


@functools.lru_cache(None)
def yard(weather='rain', door=0.0, hole=False):
    """weather: rain | snow | dawn | day"""
    W = 440
    w = np.zeros((H, W, 3), np.uint8)
    snow = weather == 'snow'
    sky = {'rain': 'night', 'snow': 'night', 'dawn': 'dawn', 'day': 'day'}[weather]
    _sky(w, sky)
    if sky == 'night':
        _stars(w, 60, 70)
        _moon(w, 350, 40, 16)
        _clouds(w, [(320, 56, 26, 5), (372, 52, 22, 6), (410, 58, 18, 5), (60, 66, 30, 6), (120, 62, 20, 4),
                    (200, 76, 24, 4)], (34, 28, 64), (90, 80, 130))
    elif sky == 'dawn':
        _sun(w, 360, 118, 14)
        _clouds(w, [(300, 60, 30, 5), (120, 50, 34, 6), (220, 80, 26, 4)], (220, 140, 150), (255, 210, 190))
    else:
        _clouds(w, [(100, 40, 50, 10), (280, 50, 60, 12), (400, 36, 40, 9)], (176, 184, 204), (210, 216, 230))
    hc = {'night': ((24, 20, 46), (18, 15, 34)), 'dawn': ((120, 80, 120), (90, 60, 100)),
          'day': ((110, 130, 150), (90, 110, 130))}[sky]
    _hills(w, G, *hc)
    _house(w, 10, G, snow=snow, lit=(sky != 'day'), door_open=door)
    _fence(w, 112, W, G, snow=snow, col=(30, 26, 48) if sky == 'night' else (70, 60, 70))
    _tree(w, 380, G, 1.0, snow=snow, col=(18, 14, 30) if sky == 'night' else (60, 44, 50))
    if snow:
        _ground(w, G, (200, 208, 232), (150, 160, 196), (230, 236, 250))
    elif sky == 'night':
        _ground(w, G, (32, 42, 46), (18, 22, 30), (38, 52, 54))
        _puddles(w, [(70, 166, 14, 2.5), (170, 174, 10, 2), (340, 166, 12, 2.5)], moon_idx=2)
    else:
        _ground(w, G, (70, 110, 70), (50, 80, 54), (90, 130, 80))
    _grave(w, GRAVE_X, G + 3, flowers=(weather != 'snow'), extra_tag=(weather == 'dawn'))
    if hole:
        ellipse(w, GRAVE_X + 3, G + 2, 6, 2, (16, 10, 14))
    return w


# ------------------------------------------------------------------ interiors
def _wall(w, col, stripe, y1):
    rect(w, 0, 0, w.shape[1], y1, col)
    for x in range(0, w.shape[1], 12):
        rect(w, x, 0, x + 1, y1, stripe)
    rect(w, 0, y1 - 4, w.shape[1], y1, tuple(max(0, c - 14) for c in col))


def _floor(w, y0, a, b):
    rect(w, 0, y0, w.shape[1], w.shape[0], a)
    for y in range(y0 + 3, w.shape[0], 5):
        rect(w, 0, y, w.shape[1], y + 1, b)
    rng = np.random.default_rng(3)
    for y in range(y0, w.shape[0], 5):
        for x in rng.integers(0, w.shape[1], 10):
            rect(w, x, y, x + 1, y + 5, b)


def _window(w, x, y, ww, hh, sky='night', snow=False):
    sub = np.zeros((hh, ww, 3), np.uint8)
    _sky(sub, sky, ground=hh)
    if sky == 'night':
        _stars(sub, 8, hh // 2, seed=x)
        cx, cy = ww * 0.7, hh * 0.3
        yy, xx = np.mgrid[0:hh, 0:ww]
        sub[np.hypot(xx - cx, yy - cy) <= 5] = (238, 234, 214)
    if snow:
        rect(sub, 0, hh - 4, ww, hh, (210, 216, 240))
    w[y:y + hh, x:x + ww] = sub
    fr = (96, 70, 56)
    rect(w, x - 2, y - 2, x + ww + 2, y, fr)
    rect(w, x - 2, y + hh, x + ww + 2, y + hh + 3, fr)
    rect(w, x - 2, y, x, y + hh, fr)
    rect(w, x + ww, y, x + ww + 2, y + hh, fr)
    rect(w, x + ww // 2 - 1, y, x + ww // 2 + 1, y + hh, fr)
    rect(w, x, y + hh // 2 - 1, x + ww, y + hh // 2 + 1, fr)


def _frame_photo(w, x, y, ww=16, hh=12, dog=True, people=False):
    rect(w, x - 1, y - 1, x + ww + 1, y + hh + 1, (120, 90, 60))
    rect(w, x, y, x + ww, y + hh, (200, 220, 230))
    rect(w, x, y + hh - 4, x + ww, y + hh, (110, 160, 110))
    if dog:
        rect(w, x + 3, y + 5, x + 10, y + 8, (222, 170, 96))
        rect(w, x + 9, y + 3, x + 13, y + 7, (222, 170, 96))
        px(w, x + 12, y + 4, (30, 20, 20))
        rect(w, x + 4, y + 8, x + 5, y + 10, (186, 130, 70))
        rect(w, x + 8, y + 8, x + 9, y + 10, (186, 130, 70))
    if people:
        rect(w, x + 2, y + 4, x + 5, y + 10, (242, 194, 66))
        rect(w, x + 2, y + 2, x + 5, y + 4, (238, 190, 160))


@functools.lru_cache(None)
def bedroom(lamp=False, door=0.0, sky='night', snow=False):
    W = 320
    w = np.zeros((H, W, 3), np.uint8)
    wall = (38, 40, 76) if not lamp else (60, 52, 80)
    _wall(w, wall, tuple(c + 6 for c in wall), 140)
    _floor(w, 140, (72, 50, 42), (58, 40, 34))
    _window(w, 196, 34, 56, 50, sky=sky, snow=snow)
    # moonlight patch on floor
    dither_blend(w, np.pad(np.ones((16, 70), bool), ((150, 14), (190, 60))), (110, 110, 160), 0.25)
    # bed
    rect(w, 36, 104, 42, 150, (110, 76, 52))
    rect(w, 134, 112, 140, 150, (110, 76, 52))
    rect(w, 42, 118, 134, 136, (230, 226, 236))
    rect(w, 42, 112, 70, 120, (240, 240, 248))      # pillow
    rect(w, 64, 116, 134, 136, (200, 120, 150))     # blanket
    rect(w, 64, 116, 134, 118, (230, 150, 180))
    rect(w, 42, 136, 134, 140, (90, 62, 44))
    # nightstand + lamp
    rect(w, 146, 120, 166, 150, (96, 66, 48))
    rect(w, 148, 126, 164, 128, (70, 48, 36))
    rect(w, 154, 108, 158, 120, (60, 60, 70))
    rect(w, 150, 100, 162, 108, (255, 220, 150) if lamp else (120, 100, 90))
    if lamp:
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.hypot(xx - 156, yy - 104)
        dither_blend(w, (d < 40) & (d > 6), (150, 110, 90), np.clip(1 - d / 40, 0, 1) * 0.5)
    # wall decor
    _frame_photo(w, 92, 66)
    rect(w, 20, 40, 44, 74, (70, 120, 160))         # poster
    rect(w, 28, 46, 36, 64, (230, 230, 240))
    rect(w, 30, 42, 34, 46, (255, 120, 90))
    # door
    rect(w, 276, 62, 304, 140, (90, 62, 46))
    if door > 0:
        rect(w, 276, 62, 276 + int(28 * door), 140, (230, 196, 140))
    rect(w, 298, 100, 300, 103, (200, 170, 90))
    # toy box
    rect(w, 230, 128, 262, 150, (180, 90, 80))
    rect(w, 230, 126, 262, 129, (210, 120, 100))
    return w


@functools.lru_cache(None)
def living(door=0.0, outside='night', snow=False, laptop=False, lamp=True):
    W = 360
    w = np.zeros((H, W, 3), np.uint8)
    _wall(w, (58, 44, 56), (64, 50, 62), 138)
    _floor(w, 138, (84, 60, 46), (70, 48, 38))
    rect(w, 0, 150, W, 151, (60, 42, 34))
    _window(w, 30, 40, 60, 54, sky=outside, snow=snow)
    # front door (opening shows outside)
    dx, dw = 150, 30
    rect(w, dx - 3, 54, dx + dw + 3, 140, (70, 50, 40))
    rect(w, dx, 58, dx + dw, 140, (120, 80, 56))
    rect(w, dx + 3, 64, dx + dw - 3, 96, (104, 70, 50))
    rect(w, dx + 3, 102, dx + dw - 3, 134, (104, 70, 50))
    px(w, dx + dw - 5, 100, (220, 190, 110))
    if door > 0:
        ow = int(dw * door)
        sub = np.zeros((82, ow, 3), np.uint8) if ow > 0 else None
        if ow > 0:
            _sky(sub, outside, ground=60)
            rect(sub, 0, 60, ow, 82, (200, 208, 232) if snow else (30, 40, 44))
            w[58:140, dx:dx + ow] = sub
    rect(w, dx - 10, 60, dx - 8, 62, (60, 44, 34))
    rect(w, dx - 14, 62, dx - 6, 84, (200, 160, 60))  # yellow raincoat on hook
    # family photos
    _frame_photo(w, 104, 50)
    _frame_photo(w, 104, 72, dog=False, people=True)
    _frame_photo(w, 200, 46, 22, 14, dog=True, people=True)
    # sofa
    rect(w, 220, 108, 300, 140, (90, 70, 110))
    rect(w, 216, 100, 304, 112, (110, 86, 132))
    rect(w, 216, 112, 226, 140, (110, 86, 132))
    rect(w, 294, 112, 304, 140, (110, 86, 132))
    # lamp
    rect(w, 316, 70, 318, 140, (60, 60, 70))
    rect(w, 308, 60, 326, 72, (255, 210, 140) if lamp else (120, 100, 90))
    if lamp:
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.hypot(xx - 317, yy - 66)
        dither_blend(w, (d < 46) & (d > 8), (150, 110, 90), np.clip(1 - d / 46, 0, 1) * 0.5)
    # desk + laptop
    rect(w, 320, 116, 358, 120, (96, 66, 48))
    rect(w, 324, 120, 327, 150, (96, 66, 48))
    rect(w, 352, 120, 355, 150, (96, 66, 48))
    rect(w, 330, 104, 350, 116, (40, 44, 60))
    rect(w, 331, 105, 349, 115, (110, 200, 230) if laptop else (20, 24, 36))
    rect(w, 328, 115, 352, 117, (140, 140, 160))
    return w


@functools.lru_cache(None)
def school():
    W = 380
    w = np.zeros((H, W, 3), np.uint8)
    _sky(w, 'dusk')
    _sun(w, 300, 132, 12)
    _clouds(w, [(80, 40, 40, 6), (250, 30, 50, 7)], (200, 110, 120), (255, 180, 150))
    rect(w, 60, 54, 300, G, (120, 74, 70))
    rect(w, 60, 50, 300, 54, (90, 54, 56))
    for r in range(3):
        for c in range(10):
            x, y = 72 + c * 23, 62 + r * 26
            rect(w, x, y, x + 14, y + 16, (255, 210, 130) if (r * 7 + c * 3) % 5 else (60, 50, 70))
            rect(w, x + 6, y, x + 8, y + 16, (90, 54, 56))
    m = text_mask("SCHOOL")
    rect(w, 154, 40, 206, 52, (230, 220, 200))
    _stamp(w, m, 180 - m.shape[1] // 2, 43, (90, 54, 56))
    _ground(w, G, (130, 120, 130), (100, 90, 104), (150, 140, 150))
    rect(w, 0, G, W, G + 2, (160, 150, 160))
    for x in range(110, 250, 5):
        rect(w, x, G - 22, x + 1, G, (40, 34, 50))
    rect(w, 110, G - 22, 250, G - 20, (40, 34, 50))
    rect(w, 110, G - 10, 250, G - 9, (40, 34, 50))
    rect(w, 316, G - 54, 318, G, (40, 34, 50))
    rect(w, 310, G - 56, 322, G - 52, (40, 34, 50))
    rect(w, 312, G - 52, 320, G - 50, (255, 230, 160))
    _tree(w, 30, G, 1.0, col=(50, 34, 44))
    return w


@functools.lru_cache(None)
def hospital_ext(door=0.0):
    W = 400
    w = np.zeros((H, W, 3), np.uint8)
    _sky(w, 'night')
    _stars(w, 40, 60, seed=9)
    _hills(w, G, (24, 20, 46), (18, 15, 34), seed=3)
    rect(w, 110, 30, 370, G, (54, 60, 78))
    rect(w, 110, 30, 370, 33, (80, 88, 110))
    rng = np.random.default_rng(2)
    for r in range(6):
        for c in range(13):
            x, y = 118 + c * 19, 40 + r * 16
            on = rng.random() < 0.55
            rect(w, x, y, x + 10, y + 9, (210, 228, 240) if on else (34, 40, 60))
    rect(w, 214, 6, 262, 28, (40, 40, 56))
    rect(w, 234, 9, 242, 25, (255, 64, 76))
    rect(w, 226, 13, 250, 21, (255, 64, 76))
    m = text_mask("HOSPITAL")
    rect(w, 240 - m.shape[1] // 2 - 4, G - 44, 240 + m.shape[1] // 2 + 4, G - 33, (30, 34, 50))
    _stamp(w, m, 240 - m.shape[1] // 2, G - 42, (255, 230, 230))
    dx = 222
    rect(w, dx - 2, G - 30, dx + 38, G, (30, 34, 50))
    rect(w, dx, G - 28, dx + 36, G, (140, 190, 210))
    if door > 0:
        o = int(18 * door)
        rect(w, dx + 18 - o, G - 28, dx + 18 + o, G, (255, 240, 220))
    rect(w, dx + 17, G - 28, dx + 19, G, (30, 34, 50))
    _ground(w, G, (200, 208, 232), (150, 160, 196), (230, 236, 250))
    for lx in (60, 380):
        rect(w, lx, G - 50, lx + 2, G, (40, 34, 50))
        rect(w, lx - 4, G - 52, lx + 6, G - 48, (255, 236, 180))
    cast.ambulance(w, 20, G + 6)
    return w


@functools.lru_cache(None)
def hospital_room(door=0.0):
    W = 320
    w = np.zeros((H, W, 3), np.uint8)
    _wall(w, (64, 80, 100), (70, 86, 106), 140)
    _floor(w, 140, (110, 120, 130), (96, 106, 116))
    _window(w, 230, 30, 60, 50, sky='night', snow=True)
    rect(w, 70, 112, 200, 132, (230, 236, 240))
    rect(w, 66, 96, 72, 150, (180, 186, 196))
    rect(w, 198, 108, 204, 150, (180, 186, 196))
    rect(w, 72, 106, 100, 116, (246, 248, 252))
    rect(w, 96, 112, 198, 130, (150, 190, 210))
    rect(w, 96, 112, 198, 114, (180, 216, 230))
    rect(w, 72, 132, 198, 136, (140, 150, 160))
    rect(w, 210, 66, 246, 96, (40, 44, 56))         # monitor
    rect(w, 212, 68, 244, 94, (8, 20, 16))
    rect(w, 226, 96, 229, 150, (140, 140, 150))
    rect(w, 46, 40, 48, 150, (180, 186, 196))       # IV
    rect(w, 40, 40, 54, 42, (180, 186, 196))
    rect(w, 42, 42, 50, 56, (190, 220, 240))
    rect(w, 252, 116, 278, 150, (200, 206, 214))    # drawer
    rect(w, 254, 126, 276, 128, (150, 156, 166))
    rect(w, 4, 58, 30, 140, (150, 160, 176))
    if door > 0:
        rect(w, 4, 58, 4 + int(26 * door), 140, (240, 244, 250))
    return w


def ecg(w, t, alive=True, x0=212, y0=68, ww=32, hh=26):
    """Animated heart monitor trace."""
    for i in range(ww):
        ph = (t * 1.2 * ww + i) % ww
        y = y0 + hh // 2 + 3
        if alive and 12 <= ph < 16:
            y += (0, -8, 6, -2)[int(ph - 12)]
        c = (60, 255, 140) if (i - (t * 1.2 * ww) % ww) % ww > ww - 6 else (30, 140, 80)
        px(w, x0 + i, y, c)
    m = text_mask("72" if alive else "--")
    _stamp(w, m, x0 + 20, y0 + 2, (60, 255, 140))


@functools.lru_cache(None)
def city(snowing=True):
    W = 720
    w = np.zeros((H, W, 3), np.uint8)
    _sky(w, 'night')
    _stars(w, 50, 40, seed=12)
    rng = np.random.default_rng(7)
    x = 0
    while x < W:                                   # far skyline
        bw, bh = rng.integers(14, 30), rng.integers(40, 100)
        rect(w, x, G - bh, x + bw, G, (26, 24, 50))
        for yy in range(G - bh + 4, G - 10, 6):
            for xx in range(x + 2, x + bw - 2, 5):
                if rng.random() < 0.25:
                    px(w, xx, yy, (200, 180, 120))
        x += bw + rng.integers(0, 4)
    x = 0
    signs = ["NOODLES", "24/7", "NEXA", "HOTEL", "BAR", "REPAIR"]
    si = 0
    while x < W:                                   # near facades
        bw, bh = rng.integers(50, 90), rng.integers(70, 110)
        col = tuple(int(c) for c in rng.integers(36, 60, 3))
        rect(w, x, G - bh, x + bw, G, col)
        rect(w, x, G - bh, x + bw, G - bh + 2, tuple(c + 20 for c in col))
        for yy in range(G - bh + 8, G - 26, 12):
            for xx in range(x + 6, x + bw - 10, 12):
                on = rng.random() < 0.45
                rect(w, xx, yy, xx + 7, yy + 7, (255, 210, 130) if on else (24, 22, 40))
        if rng.random() < 0.8:
            txt = signs[si % len(signs)]
            si += 1
            m = text_mask(txt)
            sx, sy = x + bw // 2 - m.shape[1] // 2, G - 32
            nc = [(255, 80, 180), (96, 236, 255), (255, 200, 80)][si % 3]
            rect(w, sx - 3, sy - 3, sx + m.shape[1] + 3, sy + 10, (20, 16, 30))
            _stamp(w, m, sx, sy, nc)
        x += bw + rng.integers(2, 10)
    # NEXA billboard
    rect(w, 380, 24, 480, 60, (20, 20, 34))
    rect(w, 382, 26, 478, 58, (230, 236, 244))
    m = text_mask("NEXA K-9")
    _stamp(w, m, 430 - m.shape[1] // 2, 30, (214, 52, 62))
    m = text_mask("NEVER LOSE")
    _stamp(w, m, 430 - m.shape[1] // 2, 40, (40, 40, 60))
    m = text_mask("A FRIEND")
    _stamp(w, m, 430 - m.shape[1] // 2, 49, (40, 40, 60))
    rect(w, 428, 60, 432, 84, (30, 26, 48))
    _ground(w, G, (190, 198, 226), (120, 130, 170), (230, 236, 250))
    rect(w, 0, G + 10, W, G + 12, (100, 108, 140))
    for lx in range(40, W, 140):
        rect(w, lx, G - 56, lx + 2, G, (30, 26, 48))
        rect(w, lx - 6, G - 58, lx + 6, G - 54, (40, 34, 60))
        rect(w, lx - 4, G - 54, lx + 4, G - 52, (255, 236, 180))
        yy, xx = np.mgrid[0:H, 0:W]
        cone = (yy > G - 52) & (yy < G + 4) & (np.abs(xx - lx) < (yy - (G - 52)) * 0.45 + 2)
        dither_blend(w, cone, (120, 110, 110), 0.22)
    for cx in (120, 330, 560):                       # parked cars under snow
        rect(w, cx, G - 10, cx + 34, G + 2, (60, 70, 100))
        rect(w, cx + 6, G - 16, cx + 26, G - 10, (60, 70, 100))
        rect(w, cx, G - 12, cx + 34, G - 10, (220, 226, 244))
        rect(w, cx + 6, G - 18, cx + 26, G - 16, (220, 226, 244))
    return w


@functools.lru_cache(None)
def market():
    W = 360
    w = np.zeros((H, W, 3), np.uint8)
    rect(w, 0, 0, W, G, (34, 24, 34))
    for y in range(0, G, 6):                        # bricks
        off = 0 if (y // 6) % 2 else 6
        for x in range(off, W, 12):
            rect(w, x, y, x + 11, y + 5, (44, 30, 40))
    for x0, x1, txt, nc in ((20, 120, "PARTS", (255, 80, 180)), (140, 250, "CHIPS", (96, 236, 255)),
                            (270, 350, "REPAIR", (255, 200, 80))):
        rect(w, x0, 70, x1, 112, (24, 18, 26))
        for i, x in enumerate(range(x0, x1, 10)):    # awning
            rect(w, x, 64, x + 10, 72, (170, 50, 70) if i % 2 else (220, 210, 200))
        rect(w, x0, 112, x1, 150, (70, 50, 46))
        rect(w, x0, 110, x1, 114, (100, 74, 60))
        m = text_mask(txt)
        sx = (x0 + x1) // 2 - m.shape[1] // 2
        rect(w, sx - 3, 46, sx + m.shape[1] + 3, 58, (16, 12, 20))
        _stamp(w, m, sx, 49, nc)
        rng = np.random.default_rng(x0)
        for _ in range(14):                         # gadgets on the counter
            gx = rng.integers(x0 + 4, x1 - 8)
            c = tuple(int(v) for v in rng.integers(80, 200, 3))
            rect(w, gx, 104, gx + rng.integers(3, 8), 110, c)
            if rng.random() < 0.3:
                px(w, gx + 1, 103, (96, 236, 255))
    for x in range(0, W, 2):                         # string lights
        y = int(30 + 6 * np.sin(x * 0.05))
        px(w, x, y, (40, 34, 50))
        if x % 14 == 0:
            px(w, x, y + 1, (255, 220, 150))
    for a, b in (((0, 20), (360, 36)), ((0, 10), (200, 40)), ((120, 0), (360, 24))):
        line(w, *a, *b, (20, 16, 26))
    _ground(w, G, (44, 40, 52), (24, 22, 32), (60, 56, 70))
    _puddles(w, [(80, 166, 16, 3), (240, 172, 12, 2.5)])
    return w


@functools.lru_cache(None)
def junkyard():
    W = 480
    w = np.zeros((H, W, 3), np.uint8)
    _sky(w, 'night')
    _stars(w, 60, 60, seed=21)
    _moon(w, 90, 36, 14)
    _clouds(w, [(130, 50, 30, 5), (300, 40, 40, 6), (420, 60, 30, 5)], (34, 28, 64), (80, 70, 120))
    for x in range(0, W, 6):                         # back fence + barbed wire
        rect(w, x, G - 48, x + 1, G, (36, 32, 56))
    for y in (G - 48, G - 30):
        rect(w, 0, y, W, y + 1, (40, 36, 60))
    for x in range(0, W, 4):
        px(w, x, G - 50 + (x // 4) % 2, (60, 56, 84))
    rect(w, 400, 30, 404, G, (60, 50, 50))           # crane
    line(w, 402, 32, 330, 50, (60, 50, 50))
    line(w, 402, 34, 330, 52, (60, 50, 50))
    line(w, 340, 50, 340, 90, (40, 36, 40))
    rect(w, 334, 90, 348, 96, (70, 60, 60))
    rng = np.random.default_rng(13)
    yy, xx = np.mgrid[0:H, 0:W]
    for cx in range(-10, W + 20, 46):                # scrap mounds
        rx, ry = rng.integers(30, 50), rng.integers(22, 40)
        m = (((xx - cx) / rx) ** 2 + ((yy - G) / ry) ** 2 <= 1) & (yy <= G)
        w[m] = (44, 40, 58)
        for _ in range(60):
            a = rng.uniform(np.pi, 2 * np.pi)
            r = rng.uniform(0.2, 1.0)
            x = int(cx + np.cos(a) * rx * r)
            y = int(G + np.sin(a) * ry * r)
            c = tuple(int(v) for v in rng.choice([(90, 84, 100), (120, 90, 70), (70, 66, 86), (150, 150, 170)]))
            rect(w, x, y, x + rng.integers(2, 7), y + rng.integers(1, 4), c)
    _ground(w, G, (40, 36, 48), (24, 22, 32), (60, 54, 66))
    # broken K-9 units scattered (the failed copies)
    spots = [(30, G - 18, False), (150, G - 26, True), (210, G - 8, False), (300, G - 22, True), (360, G - 6, False),
             (440, G - 14, True), (100, G + 4, True), (260, G + 8, False)]
    for x, y, fl in spots:
        s = cast.dog('unit01', 'sleep', 'off')
        a = s.rgba.copy()
        a[..., :3] = (a[..., :3].astype(np.float32) * 0.6).astype(np.uint8)
        a = a[::-1] if fl else a
        sub = w[y:y + a.shape[0], x:x + a.shape[1]]
        mm = a[:sub.shape[0], :sub.shape[1], 3] > 0
        sub[mm] = a[:sub.shape[0], :sub.shape[1], :3][mm]
    # ground fog
    dither_blend(w, (yy > G - 16) & (yy < G + 6), (70, 66, 96), 0.18)
    return w


def warning_light(w, t, x=402, y=28):
    on = int(t * 2) % 2 == 0
    rect(w, x - 2, y - 2, x + 3, y + 2, (255, 60, 70) if on else (90, 30, 40))
    if on:
        Hh, W = w.shape[:2]
        yy, xx = np.mgrid[0:Hh, 0:W]
        d = np.hypot(xx - x, yy - y)
        dither_blend(w, (d < 30) & (d > 3), (140, 40, 60), np.clip(1 - d / 30, 0, 1) * 0.35)


def void(col=(0, 0, 0)):
    w = np.zeros((H, 320, 3), np.uint8)
    w[:] = col
    return w


SETS = {
    'yard': yard, 'bedroom': bedroom, 'living': living, 'school': school,
    'hospital_ext': hospital_ext, 'hospital_room': hospital_room, 'city': city,
    'market': market, 'junkyard': junkyard, 'void': void,
}
