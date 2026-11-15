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


# ================================================================== film cast (v2)
_BOLT_SIT = [
    "..................kk..kk....",
    "..................kwk.kwk...",
    "..................kwgkkwgk..",
    ".................kwwwwwwwwk.",
    ".................kwwwwwwwwk.",
    ".................kwwwwdccwk.",
    ".................kgwwwwwwwwk",
    "..............kkkgwwwwwwwddk",
    ".............kwwwwgggwwwwwkk",
    "............kwwwwwwggkkkkkk.",
    "...........kwwwwwwwgk.......",
    "..........kwwyywwwwgk.......",
    ".........kwwwwwwwwgdk.......",
    "........kwwwwwwwwwgkkgk.....",
    "........kggwwwwwwgk.kgk.....",
    "y......kdgggggggdk..kgk.....",
    "kkkk...kddkkkkkddk..kwk.....",
    ".......kkkkkkkkkkk.kkkkk....",
]
_BOLT_SLEEP = [
    "....................kk..kk....",
    "....................kwk.kwk...",
    "...................kwwwwwwwwk.",
    "...................kwwwwddwwk.",
    "..kkkkkkkkkkkkkkkkkgwwwwwwwwkk",
    ".kwwwwwwwwwwwwwwwwwgwwwwwwddk.",
    ".kwwwwwwwyywwwwwwwwggkkkkkkk..",
    ".kgggggggggggggggggggk........",
    "kkdkkkkkkkkkkkkkkkkdddkk......",
    "ky............................",
]
OLD_DOG_PAL = {'w': (222, 170, 96), 'g': (186, 130, 70), 'd': (128, 84, 48), 'c': (34, 22, 20),
               'y': (186, 130, 70), 'k': (58, 34, 24)}
UNIT01_PAL = {'w': (150, 122, 106), 'g': (112, 88, 80), 'd': (70, 56, 58), 'c': EYE_RED, 'y': (255, 120, 40)}
EYE_PALS = {'on': {}, 'off': {'c': EYE_OFF}, 'red': {'c': EYE_RED}, 'blink': {'c': PAL['g']}}

_cache2 = {}


def dog(kind='bolt', pose='A', eye='on'):
    """kind: bolt | old | unit01 ; pose: A B C (legs) | sit | sleep"""
    key = (kind, pose, eye)
    if key in _cache2:
        return _cache2[key]
    rows = {'sit': _BOLT_SIT, 'sleep': _BOLT_SLEEP}.get(pose)
    if rows is None:
        rows = _BOLT_TOP + _LEGS[pose]
    pal = {}
    if kind == 'old':
        pal.update(OLD_DOG_PAL)
    elif kind == 'unit01':
        pal.update(UNIT01_PAL)
    if kind != 'old':
        pal.update(EYE_PALS.get(eye, {}))
    if kind == 'unit01' and eye == 'off':
        pal['c'] = (60, 30, 30)
    _cache2[key] = Sprite(rows, pal)
    return _cache2[key]


_MIRA_WALK = [
    "..kOOYYYYYYk..",
    "..kOOOOOOOOk..",
    "...kkjjjjkk...",
    "...kjjk.kjjk..",
    "..kjjk...kjjk.",
    "..kjjk...kjjk.",
    ".kRRRk...kRRRk",
    ".kRRRRk..kRRRk",
    ".kkkkkk..kkkkk",
]
_MIRA_BODY = [
    "..kOYYYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOYkYYYYYk..",
    "..kOskYYYYYk..",
]
_MIRA_KNEEL = [
    "..kOYYYYYYYYkk",
    "..kOYYYYYYYYss",
    "..kOOYYYYYYk..",
    "..kOOOOOOOOk..",
    ".kjjjjjjjjjk..",
    ".kRRRkkkkkk...",
    ".kkkkk........",
]
_HOME = {'Y': 'p', 'O': 'q'}


def _home_rows(rows, n_head=9):
    out = []
    for i, r in enumerate(rows):
        r = r.replace('Y', 'h') if i < n_head else r
        out.append(''.join(_HOME.get(ch, ch) if i >= n_head else ch for ch in r))
    return out


def _mk_mira(head, body, legs, home):
    rows = head + body + legs
    return Sprite(_home_rows(rows) if home else rows)


_shout_head2 = list(_MIRA_HEAD)
_shout_head2[7] = "..kYYhSsssek.."
_mira_cache = {}


def mira(pose='stand', home=False):
    """pose: stand walk sit shout kneel"""
    key = (pose, home)
    if key in _mira_cache:
        return _mira_cache[key]
    if pose == 'sit':
        s = MIRA_SIT if not home else Sprite(_home_rows([
            "......kkkkk.......", ".....kYYYYYk......", "....kYYYYYYYk.....", "....kYYYhhhhhk....",
            "....kYYhhhhsssk...", "....kYYhhhssesk...", "....kYYhhsssssk...", "....kYYYhSssssk...",
            ".....kYYYSSssk....", ".....kOYYYk.......", "....kOYYYYYk.kkk..", "...kOYYYYYYskjjjk.",
            "...kOYYYYYYskjjjk.", "...kOYYYYYYYkjjjk.", "...kOOYYYYYYkjjjk.", "..kjjOOOOOOkkRRRk.",
            "..kkkkkkkkkkkRRRRk"]))
    elif pose == 'walk':
        s = _mk_mira(_MIRA_HEAD, _MIRA_BODY, _MIRA_WALK, home)
    elif pose == 'shout':
        s = _mk_mira(_shout_head2, ["..kOYYYYYYYYkk", "..kOYkYYYYYYss", "..kOYkYYYYYkkk",
                                    "..kOYkYYYYYk..", "..kOYkYYYYYk.."], _MIRA_LEGS, home)
    elif pose == 'kneel':
        s = _mk_mira(_MIRA_HEAD, [], _MIRA_KNEEL, home)
    else:
        s = _mk_mira(_MIRA_HEAD, _MIRA_BODY, _MIRA_LEGS, home)
    _mira_cache[key] = s
    return s


MIRA_BED_HEAD = Sprite([
    "..kkkkk...",
    ".khhhhhk..",
    "khhhhsssk.",
    "khhhsssesk",
    "khhhssssk.",
    ".khhSsssk.",
    "..kkkkkk..",
])

_DADL_HEAD = [
    "....kkkkk.....",
    "...kHHHHHk....",
    "..kHHHHHHHk...",
    "..kHHsssssk...",
    "..kHsGGsGGk...",
    "..kHssssssk...",
    "..kHHSssbbk...",
    "...kSbbbbk....",
]
_ANDROID_HEAD = [
    "....kkkkk.....",
    "...kgggggk....",
    "..kgwwwwwgk...",
    "..kgwwwwwwk...",
    "..kgwxxwxxk...",
    "..kgwwwwwwk...",
    "..kggdddddk...",
    "...kgddddk....",
]
_DADL_BODY = ["..kkVVVVVVkk.."] + [".kVVVVVVVVVWk."] * 21 + [".kkVVVVVVVVkk."]
_DADL_LEGS = {
    'stand': ["...kJJkkJJk..."] * 7 + ["..kKKKkkKKKk.."],
    'walk': ["...kJJkkJJk...", "..kJJk..kJJk..", "..kJJk..kJJk..", ".kJJk....kJJk.",
             ".kJJk....kJJk.", ".kJJk....kJJk.", ".kJJk....kJJk.", "kKKKk....kKKKk"],
}
_dad_cache = {}


def dad(pose='stand', look='lit'):
    """look: silhouette | lit | fake | android"""
    key = (pose, look)
    if key in _dad_cache:
        return _dad_cache[key]
    if look == 'silhouette':
        s = DAD[pose]
    else:
        head = {'lit': _DADL_HEAD, 'fake': _DADL_HEAD, 'android': _ANDROID_HEAD}[look]
        pal = {'G': EYE_RED} if look == 'fake' else {}
        s = Sprite(head + _DADL_BODY + _DADL_LEGS[pose], pal)
    _dad_cache[key] = s
    return s


DEALER = Sprite([
    ".....kkkkk......",
    "....kQQQQQk.....",
    "...kQQQQQQQk....",
    "...kQQkkkkQk....",
    "...kQkzzkzzk....",
    "...kQkkkkkkk....",
    "...kQQkkkkQk....",
    "..kQQQQQQQQQk...",
] + ["..kQQQQQQQQQk..."] * 4 + ["..kQQQQQQQQsk...", "..kQQQQQQQQsk..."] + ["..kQQQQQQQQQk..."] * 2
  + [".kQQQQQQQQQQQk.."] * 10 + ["kQQQQQQQQQQQQQk."] * 6 + ["kkkkkkkkkkkkkkk."])


def kid(coat=(90, 140, 200), hair=(98, 66, 46)):
    return Sprite(_MIRA_HEAD + _MIRA_BODY + _MIRA_LEGS,
                  {'Y': coat, 'O': tuple(int(c * 0.75) for c in coat), 'h': hair})


# ------------------------------------------------------------------ vehicles & props (procedural)
def van(w, x, ybot, label="NEXA", body=(222, 226, 236), stripe=(255, 64, 76), lights=False, t=0.0):
    x, ybot = int(x), int(ybot)
    k = (22, 18, 38)
    rect(w, x, ybot - 22, x + 52, ybot - 4, body)
    rect(w, x + 38, ybot - 28, x + 52, ybot - 20, body)          # cab roof
    rect(w, x + 40, ybot - 26, x + 50, ybot - 19, (60, 90, 120))  # windshield
    rect(w, x, ybot - 12, x + 52, ybot - 10, stripe)
    m = text_mask(label)
    _stamp(w, m, x + 6, ybot - 20, (40, 40, 60))
    for wx in (x + 8, x + 40):
        rect(w, wx, ybot - 6, wx + 7, ybot + 1, k)
        rect(w, wx + 2, ybot - 4, wx + 5, ybot - 1, (120, 120, 140))
    rect(w, x - 1, ybot - 22, x, ybot - 4, k)
    rect(w, x + 52, ybot - 28, x + 53, ybot - 4, k)
    rect(w, x, ybot - 23, x + 38, ybot - 22, k)
    if lights:
        on = int(t * 6) % 2
        rect(w, x + 42, ybot - 30, x + 45, ybot - 28, (255, 60, 70) if on else (90, 30, 40))
        rect(w, x + 46, ybot - 30, x + 49, ybot - 28, (60, 120, 255) if not on else (30, 40, 90))


def ambulance(w, x, ybot, t=0.0):
    van(w, x, ybot, label="", body=(236, 236, 240), stripe=(214, 52, 62), lights=True, t=t)
    rect(w, x + 14, ybot - 20, x + 17, ybot - 13, (214, 52, 62))
    rect(w, x + 12, ybot - 18, x + 19, ybot - 15, (214, 52, 62))


def radio(w, x, ybot, glow=0.0):
    x, ybot = int(x), int(ybot)
    rect(w, x, ybot - 9, x + 16, ybot + 1, (110, 70, 50))
    rect(w, x + 1, ybot - 8, x + 9, ybot, (60, 40, 34))
    for yy in range(ybot - 7, ybot, 2):
        rect(w, x + 2, yy, x + 8, yy + 1, (90, 64, 50))
    rect(w, x + 10, ybot - 7, x + 15, ybot - 4, (255, 200, 110) if glow > 0.5 else (120, 96, 60))
    px(w, x + 11 + int(glow * 3) % 4, ybot - 6, (200, 40, 40))
    line(w, x + 14, ybot - 10, x + 20, ybot - 20, (150, 150, 170))
    rect(w, x + 11, ybot - 2, x + 13, ybot, (40, 30, 26))
