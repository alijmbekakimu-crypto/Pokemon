"""Pixel Flow — a tiny pixel-art engine built on numpy.

Everything (sprites, backgrounds, font, effects) is drawn in code, so every
frame is original. The screen is 180x320 "fat pixels", upscaled x6 to a
1080x1920 vertical Short with nearest-neighbour scaling.
"""
import numpy as np

SW, SH = 180, 320          # low-res screen
SCALE = 6                  # 180x320 -> 1080x1920

BAYER4 = np.array([[0, 8, 2, 10],
                   [12, 4, 14, 6],
                   [3, 11, 1, 9],
                   [15, 7, 13, 5]], dtype=np.float32) / 16.0


def bayer(h, w):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


SCREEN_BAYER = bayer(SH, SW)

# --------------------------------------------------------------- palette
PAL = {
    'k': (22, 18, 38),     # outline
    'w': (208, 214, 230),  # robot light
    'g': (146, 154, 182),  # robot mid
    'd': (84, 88, 118),    # robot dark
    'c': (96, 236, 255),   # robot eye (cyan)
    'y': (255, 204, 72),   # robot LED
    'h': (64, 38, 44),     # hair
    's': (238, 190, 160),  # skin
    'S': (200, 140, 122),  # skin shade
    'e': (28, 22, 40),     # eye
    'Y': (242, 194, 66),   # raincoat
    'O': (194, 134, 42),   # raincoat shade
    'R': (196, 54, 64),    # boots
    'j': (72, 84, 136),    # jeans
    'D': (46, 40, 64),     # dad head
    'C': (54, 48, 78),     # dad coat
    'L': (156, 150, 206),  # moon rim light
    'P': (24, 22, 36),     # dad pants
    'B': (16, 14, 24),     # dad boots
    'r': (214, 52, 62),    # ball
    'l': (255, 176, 176),  # ball highlight
    'm': (140, 30, 44),    # ball shade
}

EYE_OFF = (36, 44, 58)
EYE_RED = (255, 64, 76)


class Sprite:
    def __init__(self, rows, pal=None):
        pal = {**PAL, **(pal or {})}
        w = len(rows[0])
        for i, r in enumerate(rows):
            assert len(r) == w, f"sprite row {i} has len {len(r)} != {w}: {r!r}"
        self.h, self.w = len(rows), w
        self.rgba = np.zeros((self.h, w, 4), np.uint8)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.':
                    self.rgba[y, x, :3] = pal[ch]
                    self.rgba[y, x, 3] = 255


def blit(dst, spr, x, y, flip=False):
    a = spr.rgba[:, ::-1] if flip else spr.rgba
    x, y = int(round(x)), int(round(y))
    H, W = dst.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + spr.w, W), min(y + spr.h, H)
    if x0 >= x1 or y0 >= y1:
        return
    sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
    m = sub[..., 3] > 0
    dst[y0:y1, x0:x1][m] = sub[..., :3][m]


# --------------------------------------------------------------- primitives
def rect(dst, x0, y0, x1, y1, col):
    """Fill [x0,x1) x [y0,y1) with clipping."""
    H, W = dst.shape[:2]
    x0, y0 = max(int(x0), 0), max(int(y0), 0)
    x1, y1 = min(int(x1), W), min(int(y1), H)
    if x0 < x1 and y0 < y1:
        dst[y0:y1, x0:x1] = col


def px(dst, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < dst.shape[1] and 0 <= y < dst.shape[0]:
        dst[y, x] = col


def line(dst, x0, y0, x1, y1, col):
    x0, y0, x1, y1 = map(lambda v: int(round(v)), (x0, y0, x1, y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        px(dst, x0, y0, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def ellipse_mask(h, w, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - cx) / max(rx, 1e-6)) ** 2 + ((yy - cy) / max(ry, 1e-6)) ** 2 <= 1.0


def ellipse(dst, cx, cy, rx, ry, col):
    dst[ellipse_mask(*dst.shape[:2], cx, cy, rx, ry)] = col


def disc(dst, cx, cy, r, col):
    ellipse(dst, cx, cy, r, r, col)


def dither_blend(dst, mask, col, amount, bay=None):
    """Pixel-art blend: where mask, set col on a Bayer pattern of density `amount` (0..1 or array)."""
    bay = bayer(*dst.shape[:2]) if bay is None else bay
    m = mask & (np.asarray(amount) > bay)
    dst[m] = col


# --------------------------------------------------------------- font (5x7, original)
_FONT_SRC = {
    'A': "01110 10001 10001 11111 10001 10001 10001",
    'B': "11110 10001 10001 11110 10001 10001 11110",
    'C': "01110 10001 10000 10000 10000 10001 01110",
    'D': "11110 10001 10001 10001 10001 10001 11110",
    'E': "11111 10000 10000 11110 10000 10000 11111",
    'F': "11111 10000 10000 11110 10000 10000 10000",
    'G': "01110 10001 10000 10111 10001 10001 01111",
    'H': "10001 10001 10001 11111 10001 10001 10001",
    'I': "01110 00100 00100 00100 00100 00100 01110",
    'J': "00111 00010 00010 00010 00010 10010 01100",
    'K': "10001 10010 10100 11000 10100 10010 10001",
    'L': "10000 10000 10000 10000 10000 10000 11111",
    'M': "10001 11011 10101 10101 10001 10001 10001",
    'N': "10001 10001 11001 10101 10011 10001 10001",
    'O': "01110 10001 10001 10001 10001 10001 01110",
    'P': "11110 10001 10001 11110 10000 10000 10000",
    'Q': "01110 10001 10001 10001 10101 10010 01101",
    'R': "11110 10001 10001 11110 10100 10010 10001",
    'S': "01111 10000 10000 01110 00001 00001 11110",
    'T': "11111 00100 00100 00100 00100 00100 00100",
    'U': "10001 10001 10001 10001 10001 10001 01110",
    'V': "10001 10001 10001 10001 10001 01010 00100",
    'W': "10001 10001 10001 10101 10101 10101 01010",
    'X': "10001 10001 01010 00100 01010 10001 10001",
    'Y': "10001 10001 01010 00100 00100 00100 00100",
    'Z': "11111 00001 00010 00100 01000 10000 11111",
    '0': "01110 10001 10011 10101 11001 10001 01110",
    '1': "00100 01100 00100 00100 00100 00100 01110",
    '2': "01110 10001 00001 00010 00100 01000 11111",
    '3': "11111 00010 00100 00010 00001 10001 01110",
    '4': "00010 00110 01010 10010 11111 00010 00010",
    '5': "11111 10000 11110 00001 00001 10001 01110",
    '6': "00110 01000 10000 11110 10001 10001 01110",
    '7': "11111 00001 00010 00100 01000 01000 01000",
    '8': "01110 10001 10001 01110 10001 10001 01110",
    '9': "01110 10001 10001 01111 00001 00010 01100",
    '.': "00000 00000 00000 00000 00000 01100 01100",
    ',': "00000 00000 00000 00000 01100 00100 01000",
    '!': "00100 00100 00100 00100 00100 00000 00100",
    '?': "01110 10001 00001 00010 00100 00000 00100",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    '-': "00000 00000 00000 01110 00000 00000 00000",
    ':': "00000 01100 01100 00000 01100 01100 00000",
    '_': "00000 00000 00000 00000 00000 00000 11111",
    '/': "00001 00010 00010 00100 01000 01000 10000",
    '#': "01010 11111 01010 01010 01010 11111 01010",
    ' ': "00000 00000 00000 00000 00000 00000 00000",
}
FONT = {ch: np.array([[c == '1' for c in row] for row in src.split()], dtype=bool)
        for ch, src in _FONT_SRC.items()}


def text_mask(s, scale=1):
    s = s.upper()
    w = max(len(s) * 6 - 1, 1)
    m = np.zeros((7, w), bool)
    for i, ch in enumerate(s):
        m[:, i * 6:i * 6 + 5] = FONT.get(ch, FONT['?'])
    if scale > 1:
        m = m.repeat(scale, 0).repeat(scale, 1)
    return m


def _dilate(m):
    p = np.pad(m, 1)
    out = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out |= np.roll(np.roll(p, dy, 0), dx, 1)
    return out


def draw_text(dst, s, x, y, col, scale=1, outline=(10, 8, 20), align='center'):
    """Draw text; with align='center' x is the centre. Returns drawn width."""
    m = text_mask(s, scale)
    h, w = m.shape
    x0 = int(round(x - w / 2)) if align == 'center' else int(x)
    y0 = int(y)
    if outline is not None:
        o = _dilate(m)
        _stamp(dst, o, x0 - 1, y0 - 1, outline)
        # drop shadow one pixel lower for weight
        _stamp(dst, o, x0 - 1, y0, outline)
    _stamp(dst, m, x0, y0, col)
    return w


def _stamp(dst, m, x0, y0, col):
    H, W = dst.shape[:2]
    h, w = m.shape
    xa, ya = max(x0, 0), max(y0, 0)
    xb, yb = min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb:
        return
    sub = m[ya - y0:yb - y0, xa - x0:xb - x0]
    dst[ya:yb, xa:xb][sub] = col


# --------------------------------------------------------------- camera
def shoot(world, cx, cy, z):
    """Render a 180x320 view of `world` centred on (cx, cy) world px at integer zoom z."""
    H, W = world.shape[:2]
    vw, vh = SW / z, SH / z
    assert W >= vw and H >= vh, "world smaller than view"
    x0 = min(max(cx - vw / 2, 0), W - vw)
    y0 = min(max(cy - vh / 2, 0), H - vh)
    px0, py0 = int(round(x0 * z)), int(round(y0 * z))
    wx0, wy0 = px0 // z, py0 // z
    wx1 = min(W, wx0 + int(np.ceil(vw)) + 2)
    wy1 = min(H, wy0 + int(np.ceil(vh)) + 2)
    big = world[wy0:wy1, wx0:wx1].repeat(z, 0).repeat(z, 1)
    ox, oy = px0 - wx0 * z, py0 - wy0 * z
    out = np.zeros((SH, SW, 3), np.uint8)
    crop = big[oy:oy + SH, ox:ox + SW]
    out[:crop.shape[0], :crop.shape[1]] = crop
    return out


# --------------------------------------------------------------- screen effects
def rain(scr, t, seed=1, n=70, length=4, speed=230, slant=0.3, col=(120, 128, 178)):
    rng = np.random.default_rng(seed)
    xs = rng.uniform(0, SW + 80, n)
    ys = rng.uniform(0, SH + 20, n)
    sp = rng.uniform(0.85, 1.15, n)
    travel = ys + speed * sp * t
    y = travel % (SH + 20) - 10
    x = (xs - slant * travel) % (SW + 80) - 40
    k = np.arange(length)
    X = np.round(x[:, None] - slant * k[None, :]).astype(int).ravel()
    Y = np.round(y[:, None] + k[None, :]).astype(int).ravel()
    ok = (X >= 0) & (X < SW) & (Y >= 0) & (Y < SH)
    scr[Y[ok], X[ok]] = col


def rain_layers(scr, t, strength=1.0):
    rain(scr, t, seed=3, n=int(80 * strength), length=3, speed=190, col=(66, 72, 116))
    rain(scr, t, seed=7, n=int(46 * strength), length=6, speed=330, col=(132, 142, 196))


_yy, _xx = np.mgrid[0:SH, 0:SW]
_VIG = ((_xx - SW / 2) / (SW / 2)) ** 2 * 0.55 + ((_yy - SH / 2) / (SH / 2)) ** 2 * 0.55


def vignette(scr, strength=1.0):
    m = (_VIG * strength) > (0.42 + 0.5 * SCREEN_BAYER)
    scr[m] = (scr[m].astype(np.float32) * 0.62).astype(np.uint8)
    m2 = (_VIG * strength) > (0.85 + 0.5 * SCREEN_BAYER)
    scr[m2] = (scr[m2].astype(np.float32) * 0.6).astype(np.uint8)


def flash(scr, amount, col=(214, 220, 255)):
    if amount <= 0:
        return
    m = SCREEN_BAYER < amount
    scr[m] = ((scr[m].astype(np.float32) + np.array(col)) / 2).astype(np.uint8)


def scanlines(scr, k=0.8):
    scr[1::2] = (scr[1::2].astype(np.float32) * k).astype(np.uint8)


def glitch(scr, rng, amt):
    if amt <= 0:
        return scr
    out = scr.copy()
    for _ in range(int(3 + 10 * amt)):
        y0 = rng.integers(0, SH - 2)
        h = rng.integers(1, int(4 + 14 * amt))
        dx = int(rng.integers(-int(4 + 26 * amt), int(5 + 26 * amt)))
        out[y0:y0 + h] = np.roll(out[y0:y0 + h], dx, axis=1)
    sh = int(1 + 3 * amt)
    out[..., 0] = np.roll(out[..., 0], sh, axis=1)
    out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    for _ in range(int(6 * amt)):
        x, y = rng.integers(0, SW - 10), rng.integers(0, SH - 4)
        out[y:y + rng.integers(1, 4), x:x + rng.integers(3, 20)] = rng.choice(
            [(96, 236, 255), (255, 64, 76), (240, 240, 255), (10, 10, 20)])
    return out


def upscale(scr):
    return scr.repeat(SCALE, 0).repeat(SCALE, 1)
