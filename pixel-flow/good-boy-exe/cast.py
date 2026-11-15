"""The cast of GOOD BOY.exe — every sprite is hand-placed pixel by pixel."""
import numpy as np
from engine import Sprite, PAL, EYE_OFF, EYE_RED, rect, line, px, blit, text_mask, _stamp, ellipse_mask, bayer

# ------------------------------------------------------------------ BOLT (robot dog, faces right)
_BOLT_TOP = [
    "..................kk..kk....",
    ".y................kwk.kwk...",
    ".k................kwgkkwgk..",
    "..k..............kwwwwwwwwk.",
    "...k.............kwwwwwwwwk.",
    "...k.............kwwwwdccwk.",
    "...k.............kgwwwwwwwwk",
    "...kkkkkkkkkkkkkkgwwwwwwwddk",
    "...kwwwwwwwwwwwwwgggwwwwwkk.",
    "...kwwwwwwwwwwwwwwggkkkkkk..",
    "...kgwwwwyywwwwwwwgk........",
    "...kggwwwwwwwwwwwwgk........",
    "...kdgggggggggggggdk........",
    "....kdddkkkkkkkdddk.........",
]
_LEGS = {
    'A': [".....kgk.......kgk..........",
          ".....kgk.......kgk..........",
          ".....kwk.......kwk..........",
          ".....kkkk......kkkk........."],
    'B': ["....kgk.........kgk.........",
          "...kgk...........kgk........",
          "..kwk.............kwk.......",
          ".kkk...............kkkk....."],
    'C': ["......kgk....kgk............",
          ".......kgk..kgk.............",
          "........kwkkwk..............",
          "........kkkkkkk............."],
}
BOLT_EYE = (23, 5)      # eye pixel (col, row) in the unflipped sprite
BOLT_MOUTH = (26, 8)

_bolt_cache = {}


def bolt(legs='A', eye='on'):
    key = (legs, eye)
    if key not in _bolt_cache:
        pal = {}
        if eye == 'off':
            pal['c'] = EYE_OFF
        elif eye == 'red':
            pal['c'] = EYE_RED
        elif eye == 'blink':
            pal['c'] = PAL['g']
        _bolt_cache[key] = Sprite(_BOLT_TOP + _LEGS[legs], pal)
    return _bolt_cache[key]


# ------------------------------------------------------------------ MIRA (yellow raincoat, faces right)
MIRA_SIT = Sprite([
    "......kkkkk.......",
    ".....kYYYYYk......",
    "....kYYYYYYYk.....",
    "....kYYYhhhhhk....",
    "....kYYhhhhsssk...",
    "....kYYhhhssesk...",
    "....kYYhhsssssk...",
    "....kYYYhSssssk...",
    ".....kYYYSSssk....",
    ".....kOYYYk.......",
    "....kOYYYYYk.kkk..",
    "...kOYYYYYYskjjjk.",
    "...kOYYYYYYskjjjk.",
    "...kOYYYYYYYkjjjk.",
    "...kOOYYYYYYkjjjk.",
    "..kjjOOOOOOkkRRRk.",
    "..kkkkkkkkkkkRRRRk",
])

_MIRA_HEAD = [
    "....kkkkk.....",
    "...kYYYYYk....",
    "..kYYYYYYYk...",
    "..kYYhhhhhk...",
    "..kYhhhhsssk..",
    "..kYhhhssesk..",
    "..kYhhsssssk..",
    "..kYYhSssssk..",
    "...kYYSSssk...",
    "...kOYYkkk....",
    "..kOYYYYYYk...",
]
_MIRA_LEGS = [
    "..kOOYYYYYYk..",
    "..kOOOOOOOOk..",
    "...kkjjjjkk...",
    "....kjjkjjk...",
    "....kjjkjjk...",
    "....kjjkjjk...",
    "...kRRRkRRRk..",
    "...kRRRkRRRRk.",
    "...kkkkkkkkkk.",
]
MIRA_STAND = Sprite(_MIRA_HEAD + [
    "..kOYYYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOskYYYYYk..",
] + _MIRA_LEGS)

_shout_head = list(_MIRA_HEAD)
_shout_head[7] = "..kYYhSsssek.."      # open mouth
MIRA_SHOUT = Sprite(_shout_head + [
    "..kOYYYYYYYYkk",
    "..kOYkYYYYYYss",
    "..kOYkYYYYYkkk",
    "..kOYkYYYYYk..",
    "..kOYkYYYYYk..",
] + _MIRA_LEGS)
MIRA_EYE = (9, 5)

# ------------------------------------------------------------------ DAD (moonlit silhouette, faces right)
_DAD_TOP = [
    "....kkkkk.....",
    "...kDDDLLk....",
    "..kDDDDDDLk...",
    "..kDDDDDDLk...",
    "..kDDDDDDLk...",
    "...kDDDDLk....",
    "....kDDLk.....",
    "..kkCCCCCLkk..",
] + [".kCCCCCCCCCLk."] * 21 + [".kkCCCCCCCCkk."]
_DAD_LEGS = {
    'stand': ["...kPPkkPPk..."] * 7 + ["..kBBBkkBBBk.."],
    'walk': ["...kPPkkPPk...",
             "..kPPk..kPPk..",
             "..kPPk..kPPk..",
             ".kPPk....kPPk.",
             ".kPPk....kPPk.",
             ".kPPk....kPPk.",
             ".kPPk....kPPk.",
             "kBBBk....kBBBk"],
}
DAD = {k: Sprite(_DAD_TOP + v) for k, v in _DAD_LEGS.items()}

# ------------------------------------------------------------------ props
BALL = Sprite([
    ".rr.",
    "rlrr",
    "rrrm",
    ".mm.",
])

CRATE_W, CRATE_H = 30, 15


def draw_crate(w, x, ybot, open_amt=0.0, glow=0.0):
    """Wooden shipping crate; (x, ybot) = left, bottom row. Front face only, so
    anything drawn before it appears to be inside."""
    x, ybot = int(round(x)), int(round(ybot))
    top = ybot - CRATE_H + 1
    body, dark, light, ink = (148, 102, 62), (110, 74, 46), (176, 128, 80), (96, 62, 38)
    rect(w, x, top, x + CRATE_W, ybot + 1, body)
    for yy in (top + 5, top + 10):
        rect(w, x, yy, x + CRATE_W, yy + 1, dark)
    rect(w, x + 1, top, x + 3, ybot + 1, (128, 88, 54))
    rect(w, x + CRATE_W - 3, top, x + CRATE_W - 1, ybot + 1, (128, 88, 54))
    # stencil
    m = text_mask("K-9")
    _stamp(w, m, x + (CRATE_W - m.shape[1]) // 2, top + 4, ink)
    # outline
    k = (22, 18, 38)
    rect(w, x - 1, top, x, ybot + 1, k)
    rect(w, x + CRATE_W, top, x + CRATE_W + 1, ybot + 1, k)
    rect(w, x - 1, ybot + 1, x + CRATE_W + 1, ybot + 2, k)
    # moon rim on the right edge
    rect(w, x + CRATE_W - 1, top, x + CRATE_W, ybot + 1, (196, 150, 100))
    if open_amt <= 0:
        rect(w, x - 1, top - 2, x + CRATE_W + 1, top, light)
        rect(w, x - 1, top - 3, x + CRATE_W + 1, top - 2, k)
        rect(w, x + 13, top - 2, x + 17, top + 3, (204, 178, 128))   # tape
    else:
        a = min(1.0, open_amt)
        lx, ly = x - 1 - 6 * a, top - 1 - 7 * a
        rx, ry = x + CRATE_W + 6 * a, top - 1 - 7 * a
        for d in (0, 1):
            line(w, x - 1 + d, top - 1, lx + d, ly, light)
            line(w, x + CRATE_W - d, top - 1, rx - d, ry, light)
        line(w, x - 2, top - 1, lx - 1, ly, k)
        line(w, x + CRATE_W + 1, top - 1, rx + 1, ry, k)


def blit_clip(dst, spr, x, y, flip=False, ymax=None):
    """Blit but only rows < ymax (used to hide Bolt inside the crate)."""
    if ymax is None:
        return blit(dst, spr, x, y, flip)
    keep = dst[int(ymax):].copy()
    blit(dst, spr, x, y, flip)
    dst[int(ymax):] = keep


def eye_glow(w, ex, ey, col=(130, 240, 255), r=3, density=0.35):
    H, W = w.shape[:2]
    m = ellipse_mask(H, W, ex, ey, r, r)
    m &= bayer(H, W) < density
    w[m] = ((w[m].astype(np.float32) + col) / 2).astype(np.uint8)


def crate_glow(w, x, ybot, glow):
    """Cyan light spilling out of the open crate — drawn *behind* Bolt."""
    if glow <= 0:
        return
    H, W = w.shape[:2]
    top = int(round(ybot)) - CRATE_H + 1
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = x + CRATE_W / 2, top - 2
    d = np.hypot((xx - cx) / 1.7, yy - cy)
    amt = np.clip(1 - d / 13, 0, 1) * glow * 0.6
    m = (yy < top) & (amt > bayer(H, W))
    w[m] = ((w[m].astype(np.float32) + (70, 190, 220)) / 2).astype(np.uint8)
