"""GOOD BOY.exe — Episode 1: "They Replaced Her Dog With AI… It Remembered Everything"

Renders out/ep01.mp4 (1080x1920, 24 fps, ~40 s) + preview stills.
    python3 ep01.py            # full render
    python3 ep01.py --stills   # only key frames (fast)
"""
import os
import subprocess
import sys
import numpy as np
from PIL import Image

import audio as A
import cast
import sets
from engine import (SW, SH, SCALE, blit, draw_text, shoot, rain_layers, vignette, flash, scanlines,
                    glitch, upscale, line, px, ellipse, rect, bayer, SCREEN_BAYER)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
FPS = 24
DUR = 40.0

WHITE, CYAN, CYAN_DIM, RED, GREEN, TAG = ((248, 244, 236), (96, 236, 255), (70, 150, 176),
                                          (255, 72, 84), (120, 255, 150), (150, 150, 196))

# ---------------------------------------------------------------- captions
# (start, end, [(text, colour), ...], y, scale, chars per second)
CAPS = [
    (0.25, 2.5, [("BOOTING...", CYAN_DIM)], 52, 1, 14),
    (1.15, 2.5, [("BOLT.EXE", CYAN)], 66, 2, 10),
    (2.8, 7.9, [("SHE BURIED", WHITE), ("HER DOG", WHITE), ("YESTERDAY.", WHITE)], 84, 2, 16),
    (8.3, 14.9, [("TODAY, DAD", WHITE), ("BROUGHT", WHITE), ("THIS.", CYAN)], 84, 2, 16),
    (18.05, 24.8, [("STOP!", RED)], 66, 3, 40),
    (18.45, 24.8, [("BOLT, NO!", WHITE)], 96, 2, 14),
    (35.5, 38.0, [("MEMORY FILE:", CYAN_DIM)], 52, 1, 20),
    (36.3, 38.0, [("BOLT_2019", CYAN)], 66, 2, 12),
    (37.2, 38.0, [("RESTORED", GREEN)], 88, 2, 12),
    (38.1, 39.6, [("...HOW DO", WHITE), ("YOU KNOW?", WHITE)], 140, 2, 12),
]


def caption_blips():
    """Times at which each caption character appears (for typing sounds)."""
    out = []
    for t0, t1, lines, y, sc, cps in CAPS:
        i = 0
        for text, _ in lines:
            for ch in text:
                if ch != ' ':
                    out.append((t0 + i / cps, sc))
                i += 1
    return out


def draw_captions(scr, t):
    for t0, t1, lines, y, sc, cps in CAPS:
        if not (t0 <= t < t1):
            continue
        shown = int((t - t0) * cps) + 1
        for j, (text, col) in enumerate(lines):
            vis = text[:max(0, shown)]
            shown -= len(text)
            if vis:
                # centre on the full line so typing doesn't jitter
                full_w = len(text) * 6 * sc - sc
                x0 = SW / 2 - full_w / 2
                draw_text(scr, vis, x0, y + j * (7 * sc + 6), col, scale=sc, align='left')


# ---------------------------------------------------------------- helpers
def lerp(a, b, u):
    return a + (b - a) * u


def clamp01(u):
    return max(0.0, min(1.0, u))


def smooth(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def seg(t, t0, t1):
    return clamp01((t - t0) / (t1 - t0))


# ---------------------------------------------------------------- the robot's eye (screen space)
_yy, _xx = np.mgrid[0:SH, 0:SW]
_EC = (90, 168)
_ED = np.hypot(_xx - _EC[0], _yy - _EC[1])
_EA = (np.arctan2(_yy - _EC[1], _xx - _EC[0]) + np.pi) / (2 * np.pi)


def eye_screen(boot, red=0.0, white=0.0):
    s = np.zeros((SH, SW, 3), np.uint8)
    s[:] = (6, 8, 16)
    s[::12, :] = (12, 18, 32)
    s[:, ::12] = (12, 18, 32)
    housing = _ED <= 60
    s[housing] = (54, 58, 82)
    lit = housing & ((-(_xx - _EC[0]) - (_yy - _EC[1])) / 85 > SCREEN_BAYER)
    s[lit] = (92, 98, 128)
    s[(_ED > 58) & (_ED <= 60)] = (22, 18, 38)
    for a in (0.785, 2.356, 3.927, 5.498):
        x, y = _EC[0] + 52 * np.cos(a), _EC[1] + 52 * np.sin(a)
        rect(s, x - 1, y - 1, x + 2, y + 2, (150, 158, 182))
        px(s, x, y, (60, 64, 88))
    s[_ED <= 47] = (20, 22, 34)
    ring = (_ED >= 39) & (_ED <= 45)
    seg_i = np.floor(_EA * 16)
    gap = ((_EA * 16) % 1) < 0.12
    on_col = np.array(CYAN) * (1 - red) + np.array(RED) * red
    s[ring] = (34, 38, 56)
    s[ring & ~gap & (seg_i < int(boot * 16))] = on_col.astype(np.uint8)
    iris = _ED <= 33
    b = clamp01((boot - 0.25) / 0.75)
    edge = np.array((14, 70, 100)) * (1 - red) + np.array((90, 10, 20)) * red
    core = np.array((110, 240, 255)) * (1 - red) + np.array((255, 90, 90)) * red
    lv = np.clip(1 - _ED / 33, 0, 1) * b
    q = np.floor(np.clip(lv * 4 + SCREEN_BAYER * 0.99, 0, 4)) / 4
    col = edge[None, None, :] * (1 - q[..., None]) + core[None, None, :] * q[..., None]
    col = col * (0.25 + 0.75 * b) + (np.array(WHITE) - col) * white
    s[iris] = np.clip(col[iris], 0, 255).astype(np.uint8)
    s[_ED <= 10] = (8, 14, 24)
    for k in range(6):
        a = k / 6 * 2 * np.pi + 0.3
        line(s, _EC[0] + 10 * np.cos(a), _EC[1] + 10 * np.sin(a),
             _EC[0] + 18 * np.cos(a + 0.5), _EC[1] + 18 * np.sin(a + 0.5), (10, 30, 44))
    if b > 0.2:
        rect(s, _EC[0] - 16, _EC[1] - 18, _EC[0] - 11, _EC[1] - 15, (240, 250, 255))
        rect(s, _EC[0] - 9, _EC[1] - 22, _EC[0] - 7, _EC[1] - 20, (240, 250, 255))
    scanlines(s, 0.78)
    return s


# ---------------------------------------------------------------- world state
YARD = sets.yard()
CRATE_X, CRATE_Y = 18, 124


def dad_state(t):
    if t < 8.0:
        return None
    if t < 10.0:
        u = seg(t, 8.0, 10.0)
        x = lerp(-12, 6, u)
        legs = 'walk' if int(t * 8) % 2 == 0 else 'stand'
        return x, legs
    return 6, 'stand'


def crate_state(t):
    """-> (x, ybot, open_amt, glow) or None"""
    if t < 8.0:
        return None
    d = dad_state(t)
    if t < 10.0:
        return d[0] + 8, 112, 0, 0
    if t < 11.0:
        u = smooth(seg(t, 10.0, 11.0))
        return lerp(14, CRATE_X, u), lerp(112, CRATE_Y, u), 0, 0
    x = CRATE_X
    if 12.3 <= t < 13.0:
        x += (0, 1, 0, -1)[int(t * 24) % 4]
    opened = seg(t, 13.0, 13.15)
    glow = 0.0
    if t >= 13.0:
        glow = 0.9 * (1 - seg(t, 13.0, 16.0)) + 0.15
    return x, CRATE_Y, opened, glow


BOLT_Y = 110   # top row when standing on the grass in front (bottom row 127)


def bolt_state(t):
    """-> dict(x, y, legs, eye, flip, clip) or None"""
    if t < 13.2:
        return None
    top = CRATE_Y - cast.CRATE_H + 1
    if t < 15.0:
        peek = lerp(0, 7, smooth(seg(t, 13.2, 13.9))) + (1 if t > 14.2 else 0)
        eye = 'off' if t < 14.0 else ('blink' if 14.55 <= t < 14.65 else 'on')
        return dict(x=CRATE_X + 1, y=top - peek, legs='A', eye=eye, flip=False, clip=CRATE_Y - cast.CRATE_H + 1)
    if t < 15.6:
        u = seg(t, 15.0, 15.6)
        y0 = top - 8
        return dict(x=lerp(CRATE_X + 1, 36, u), y=lerp(y0, BOLT_Y, u) - 16 * np.sin(np.pi * u),
                    legs='B', eye='on', flip=False, clip=None)
    if t < 17.4:
        u = seg(t, 15.6, 17.4)
        legs = 'ABCB'[int(t * 12) % 4]
        return dict(x=lerp(36, 106, u), y=BOLT_Y - (1 if legs == 'C' else 0), legs=legs, eye='on', flip=False, clip=None)
    if t < 17.6:
        return dict(x=104, y=BOLT_Y, legs='C', eye='on', flip=False, clip=None)
    if t < 23.0:
        bob = (0, 2, 0, 1)[int(t * 12) % 4]
        return dict(x=100, y=BOLT_Y + bob, legs='AC'[int(t * 12) % 2], eye='on', flip=True, clip=None)
    if t < 23.8:
        return dict(x=100, y=BOLT_Y + 3, legs='A', eye='on', flip=True, clip=None)
    if t < 25.0:
        eye = 'red' if 24.40 <= t < 24.50 else 'on'
        return dict(x=100, y=BOLT_Y, legs='A', eye=eye, flip=True, clip=None)
    if t < 28.0:
        u = seg(t, 25.0, 28.0)
        legs = 'ABCB'[int(t * 8) % 4]
        return dict(x=lerp(100, 80, u), y=BOLT_Y, legs=legs, eye='on', flip=True, clip=None)
    return dict(x=80, y=BOLT_Y, legs='A', eye='on', flip=True, clip=None)


def ball_pos(t, b):
    """Top-left of the ball (world px) or None."""
    if t < 23.8:
        return None
    if t < 28.5:
        return b['x'] - 2, b['y'] + 7
    x0, y0 = 78, BOLT_Y + 7
    yg = 124
    if t < 28.8:
        u = seg(t, 28.5, 28.8)
        return x0, lerp(y0, yg, u * u)
    if t < 29.2:
        u = seg(t, 28.8, 29.2)
        return x0 - 1 * u, yg - 4 * np.sin(np.pi * u)
    if t < 29.45:
        u = seg(t, 29.2, 29.45)
        return x0 - 1 - 1 * u, yg - 1.5 * np.sin(np.pi * u)
    u = smooth(seg(t, 29.45, 30.3))
    return x0 - 2 - 2 * u, yg


def mira_state(t):
    if t < 18.0:
        sob = (int(t * 2) % 2) if t < 8.0 else 0
        return cast.MIRA_SIT, 62, 105 + sob
    spr = cast.MIRA_SHOUT if t < 20.5 else cast.MIRA_STAND
    return spr, 64, 98


def dirt(w, t):
    if not (17.8 <= t < 23.2):
        return
    rng = np.random.default_rng(42)
    births = np.arange(17.8, 23.0, 1 / 24)
    for i, s in enumerate(births):
        age = t - s
        if not (0 <= age < 0.6):
            continue
        r = rng.random(3)
        x = 104 + (40 + 40 * r[0]) * age
        y = 121 - (45 + 35 * r[1]) * age + 160 * age * age
        px(w, x, y, (96, 68, 54) if r[2] < 0.6 else (130, 96, 70))
        if r[2] > 0.7:
            px(w, x + 1, y, (96, 68, 54))


def lightning(w, t):
    if not (19.0 <= t < 19.3):
        return
    rng = np.random.default_rng(9)
    x, y = 52.0, 0.0
    pts = [(x, y)]
    while y < 98:
        x += rng.integers(-4, 5)
        y += rng.integers(4, 9)
        pts.append((x, y))
    for (a, b), (c, d) in zip(pts, pts[1:]):
        line(w, a, b, c, d, (240, 240, 255))
        line(w, a + 1, b, c + 1, d, (170, 170, 230))
    bx, by = pts[4]
    line(w, bx, by, bx + 10, by + 14, (200, 200, 250))


def build_world(t):
    w = YARD.copy()
    lightning(w, t)
    sets.splashes(w, t)
    # hole + dirt pile
    if t >= 17.8:
        p = seg(t, 17.8, 23.0)
        ellipse(w, 102, 121, 1 + 5 * p, 0.6 + 1.6 * p, (16, 10, 14))
        ellipse(w, 134, 125, 1 + 4 * p, 0.6 + 1.8 * p, (74, 52, 44))
    d = dad_state(t)
    if d:
        blit(w, cast.DAD[d[1]], d[0], 124 - 38 + 1)
    spr, mx, my = mira_state(t)
    blit(w, spr, mx, my)
    if 32.8 <= t < 34.4:      # a tear
        u = seg(t, 32.8, 34.2)
        px(w, mx + cast.MIRA_EYE[0], my + cast.MIRA_EYE[1] + 1 + 5 * u, (200, 236, 255))
    b = bolt_state(t)
    c = crate_state(t)
    if c:
        cast.crate_glow(w, c[0], c[1], c[3])
    if b and b['clip'] is not None:
        cast.blit_clip(w, cast.bolt(b['legs'], b['eye']), b['x'], b['y'], b['flip'], ymax=b['clip'])
    if c:
        cast.draw_crate(w, c[0], c[1], c[2])
    if b and b['clip'] is not None and b['eye'] == 'on':
        ex, ey = b['x'] + cast.BOLT_EYE[0], b['y'] + cast.BOLT_EYE[1]
        cast.eye_glow(w, ex + 0.5, ey, density=0.45 if t < 14.4 else 0.25)
    if b and b['clip'] is None:
        blit(w, cast.bolt(b['legs'], b['eye']), b['x'], b['y'], b['flip'])
        ex = b['x'] + (27 - cast.BOLT_EYE[0] - 1 if b['flip'] else cast.BOLT_EYE[0])
        cast.eye_glow(w, ex + 0.5, b['y'] + cast.BOLT_EYE[1],
                      col=(255, 120, 120) if b['eye'] == 'red' else (130, 240, 255), density=0.2)
    dirt(w, t)
    if b:
        bp = ball_pos(t, b)
        if bp:
            blit(w, cast.BALL, *bp)
    return w


# ---------------------------------------------------------------- shots
def camera(t):
    """-> (cx, cy, z)"""
    if t < 5.5:
        return lerp(45, 85, smooth(seg(t, 2.5, 5.5))), 80, 2
    if t < 8.0:
        return 86, 106, 4
    if t < 11.5:
        return 45, 80, 2
    if t < 15.0:
        return 33, 112, 4
    if t < 18.0:
        b = bolt_state(t)
        return min(max(b['x'] + 14, 30), 110), 100, 3
    if t < 20.0:
        sh = 0
        if 18.05 <= t < 18.45:
            sh = (1.5, -1.5, 1, -1)[int(t * 24) % 4]
        return 92 + sh, 80, 2
    if t < 25.0:
        return 112, 112, 4
    if t < 29.0:
        return 88, 104, 3
    if t < 32.0:
        return 76, 118, 6
    return 72, 103, 9


def render(t):
    if t < 2.5:
        boot = seg(t, 0.1, 2.2)
        scr = eye_screen(boot)
        if t < 0.35:
            scr = glitch(scr, np.random.default_rng(int(t * 24)), 0.8)
    elif t < 35.0:
        cx, cy, z = camera(t)
        scr = shoot(build_world(t), cx, cy, z)
        rain_layers(scr, t, strength=1.0 if z <= 3 else 0.7)
        vignette(scr)
        if 19.0 <= t < 19.3:
            flash(scr, 0.85 if t < 19.1 else 0.35)
        draw_text(scr, "GOOD BOY.EXE  EP 1", 8, 12, TAG, align='left')
    elif t < 38.0:
        red = 0.5 + 0.5 * np.sin(t * 9) if t > 36.0 else 0.0
        red = 1.0 if (int(t * 24) % 7 == 0) else red
        white = 0.6 * (1 - seg(t, 37.2, 37.6)) if t >= 37.2 else 0
        scr = eye_screen(1.0, red=red, white=white)
        rng = np.random.default_rng(int(t * 24) + 999)
        amt = 1.0 - seg(t, 35.0, 35.4)
        if int(t * 24) % 11 == 0:
            amt = max(amt, 0.4)
        scr = glitch(scr, rng, amt)
    else:
        scr = np.zeros((SH, SW, 3), np.uint8)
    draw_captions(scr, t)
    return scr


# ---------------------------------------------------------------- sound
def soundtrack(path):
    m = A.Mix(DUR)
    # boot
    m.add(A.sweep(180, 1200, 1.0, 'sq') * A.env(int(A.SR), 0.02, 0.3), 0.05, 0.10)
    m.add(A.lowpass(A.noise(0.35, 1), 3000) * A.env(int(0.35 * A.SR), 0.001, 0.2), 0.0, 0.3)
    for f, d in ((880, 0.0), (1320, 0.09)):
        m.add(A.sine(f, 0.08) * A.env(int(0.08 * A.SR), 0.002, 0.04), 2.05 + d, 0.18)
    # typing blips
    for tt, sc in caption_blips():
        if tt < 2.5 or tt >= 35.0:
            sig = A.square(1500, 0.03) * A.decay(int(0.03 * A.SR), 0.008)
            m.add(sig, tt, 0.07)
        else:
            sig = A.sine(1180, 0.04) * A.decay(int(0.04 * A.SR), 0.01)
            m.add(sig, tt, 0.06 if sc < 3 else 0.12)
    # rain bed
    r = A.noise(32.5, 2)
    r = A.highpass(A.lowpass(r, 4200), 250)
    r *= 0.85 + 0.15 * np.sin(np.arange(len(r)) / A.SR * 0.7)
    r *= A.env(len(r), 0.4, 0.05)
    m.add(r, 2.5, 0.35)
    drops = np.zeros(int(32.5 * A.SR))
    rng = np.random.default_rng(4)
    for i in rng.integers(0, len(drops) - 2000, 420):
        drops[i:i + 400] += rng.uniform(0.2, 1) * A.sine(rng.uniform(1800, 4200), 400 / A.SR) * A.decay(400, 0.002)
    m.add(drops, 2.5, 0.12)
    # music: Am F C G Am F C E (2.4 s per chord)
    chords = [((220, 261.63, 329.63), 110, (659.25, 523.25, 440.0)),
              ((174.61, 220, 261.63), 87.31, (440.0, 523.25, 659.25)),
              ((196, 261.63, 329.63), 130.81, (392.0, 659.25, 587.33)),
              ((196, 246.94, 293.66), 98.0, (587.33, 493.88, 392.0))]
    prog = chords + chords[:3] + [((164.81, 207.65, 246.94), 82.41, (493.88, 415.3, 329.63))] + chords[:1]
    t = 2.6
    for i, (pad_f, bass, mel) in enumerate(prog):
        if t >= 25.0:
            break
        fade = 1.0 - clamp01((t - 21.5) / 3.0)
        m.add(A.lowpass(A.pad(pad_f, 2.9, a=0.6, r=0.9), 1800), t, 0.16 * fade)
        m.add(A.sine(bass, 2.4) * A.env(int(2.4 * A.SR), 0.05, 0.6), t, 0.12 * fade)
        for k, f in enumerate(mel):
            if i == 0 and k == 0:
                continue
            m.add(A.piano(f, 1.8), t + k * 0.8, 0.15 * fade, pan=0.15)
        t += 2.4
    # dad footsteps
    for k in range(8):
        tt = 8.05 + k * 0.25
        thud = A.lowpass(A.noise(0.08, 10 + k), 400) * A.decay(int(0.08 * A.SR), 0.02)
        m.add(thud + 0.5 * A.sine(70, 0.08) * A.decay(int(0.08 * A.SR), 0.03), tt, 0.5, pan=-0.4)
    m.add(A.lowpass(A.noise(0.2, 20), 300) * A.decay(int(0.2 * A.SR), 0.05), 11.0, 0.8)
    # crate rattles, burst, shimmer
    for k in range(8):
        knock = A.lowpass(A.noise(0.06, 30 + k), 900) * A.decay(int(0.06 * A.SR), 0.012)
        m.add(knock + 0.6 * A.sine(180, 0.06) * A.decay(int(0.06 * A.SR), 0.02), 12.3 + k * 0.09, 0.45,
              pan=(-0.2 if k % 2 else 0.2))
    m.add(A.lowpass(A.noise(0.25, 40), 1400) * A.decay(int(0.25 * A.SR), 0.06), 13.0, 0.7)
    m.add(A.sweep(140, 55, 0.3) * A.decay(int(0.3 * A.SR), 0.1), 13.0, 0.6)
    shimmer = sum(A.sine(f, 1.6) for f in (880, 1108.73, 1318.5)) / 3
    m.add(shimmer * A.env(int(1.6 * A.SR), 0.3, 1.0), 13.05, 0.10)
    m.add(A.lowpass(A.sweep(300, 620, 0.5, 'sq'), 1200) * A.env(int(0.5 * A.SR), 0.05, 0.1), 13.2, 0.07)
    m.add(A.sweep(800, 1700, 0.12) * A.env(int(0.12 * A.SR), 0.005, 0.03), 14.0, 0.16)
    m.add(A.sine(1700, 0.08) * A.decay(int(0.08 * A.SR), 0.03), 14.13, 0.14)
    # leap + run
    wh = A.highpass(A.noise(0.45, 50), 1200)
    m.add(wh * np.sin(np.linspace(0, np.pi, len(wh))), 15.0, 0.25)
    m.add(A.lowpass(A.noise(0.1, 51), 500) * A.decay(int(0.1 * A.SR), 0.03), 15.6, 0.5)
    k = 0
    for tt in np.arange(15.7, 17.45, 0.125):
        clk = A.sine(2400, 0.03) * A.decay(int(0.03 * A.SR), 0.006) + 0.5 * A.sine(3600, 0.03) * A.decay(int(0.03 * A.SR), 0.004)
        m.add(clk, tt, 0.12, pan=(-0.3 if k % 2 else 0.3))
        k += 1
    # STOP impact + thunder
    m.add(A.sine(55, 0.9) * A.decay(int(0.9 * A.SR), 0.3), 18.05, 0.9)
    m.add(A.lowpass(A.noise(0.4, 60), 600) * A.decay(int(0.4 * A.SR), 0.08), 18.05, 0.6)
    th = A.lowpass(A.noise(3.0, 61), 160)
    th *= A.env(len(th), 0.03, 0.5) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 9, len(th))))) * A.decay(len(th), 1.0)
    m.add(th, 19.15, 2.6)
    m.add(A.highpass(A.noise(0.25, 62), 2000) * A.decay(int(0.25 * A.SR), 0.05), 19.0, 0.4)
    # digging
    for i, tt in enumerate(np.arange(17.9, 23.0, 0.165)):
        sc = A.lowpass(A.highpass(A.noise(0.09, 70 + i), 300), 2200) * A.env(int(0.09 * A.SR), 0.01, 0.05)
        m.add(sc, tt, 0.35, pan=0.35)
    m.add(A.lowpass(A.sweep(420, 260, 0.35, 'sq'), 900) * A.env(int(0.35 * A.SR), 0.03, 0.1), 23.0, 0.06)
    m.add(A.lowpass(A.sweep(260, 520, 0.35, 'sq'), 900) * A.env(int(0.35 * A.SR), 0.03, 0.1), 23.8, 0.06)
    m.add(A.sine(620, 0.05) * A.decay(int(0.05 * A.SR), 0.015), 23.82, 0.15)
    m.add(A.sine(110, 0.6) * A.env(int(0.6 * A.SR), 0.01, 0.4) + 0.3 * A.square(55, 0.6) * A.decay(int(0.6 * A.SR), 0.1), 24.4, 0.10)
    # walking + ball
    for i, tt in enumerate(np.arange(25.05, 28.0, 0.25)):
        m.add(A.sine(2100, 0.025) * A.decay(int(0.025 * A.SR), 0.006), tt, 0.07, pan=(-0.2 if i % 2 else 0.2))
    for tt, g in ((28.8, 0.6), (29.2, 0.35), (29.45, 0.18)):
        bounce = A.sweep(170, 90, 0.09) * A.decay(int(0.09 * A.SR), 0.03)
        m.add(bounce + 0.3 * A.lowpass(A.noise(0.09, int(tt * 10)), 2000) * A.decay(int(0.09 * A.SR), 0.01), tt, g)
    m.add(A.lowpass(A.noise(0.8, 80), 700) * A.env(int(0.8 * A.SR), 0.05, 0.6), 29.5, 0.06)
    # tear
    pl = A.sine(1760, 0.6) * A.decay(int(0.6 * A.SR), 0.15)
    for k, g in enumerate((0.08, 0.04, 0.02)):
        m.add(pl, 34.2 + k * 0.18, g)
    # the machine's mind
    m.add(A.lowpass(np.sign(A.noise(0.45, 90)) * (A.noise(0.45, 91) > 0.3), 5000) * A.env(int(0.45 * A.SR), 0.001, 0.1), 35.0, 0.35)
    for tt in (36.0, 36.95, 37.6):
        m.add(A.lowpass(np.sign(A.noise(0.08, int(tt * 7))), 6000) * A.env(int(0.08 * A.SR), 0.001, 0.03), tt, 0.25)
    drone = (A.sine(55, 4.6) + 0.7 * A.sine(82.6, 4.6) + 0.4 * A.sine(110.7, 4.6) + 0.15 * A.square(27.5, 4.6))
    m.add(A.lowpass(drone, 600) * A.env(int(4.6 * A.SR), 0.6, 0.2), 35.0, 0.35)
    m.add(A.piano(1318.5, 1.5) + A.piano(1760, 1.5) * 0.6, 37.2, 0.20)
    for tt in (38.2, 38.48, 39.05, 39.33):
        hb = A.sine(48, 0.18) * A.decay(int(0.18 * A.SR), 0.05)
        m.add(hb, tt, 0.55 if tt in (38.2, 39.05) else 0.35)
    m.gate(39.6)
    m.write(path)


# ---------------------------------------------------------------- output
STILLS = [1.6, 4.5, 6.5, 9.2, 13.6, 14.3, 16.2, 18.3, 19.05, 21.0, 24.0, 26.5, 29.0, 30.5, 33.5, 36.5, 37.5, 38.8]


def save_stills():
    sdir = os.path.join(OUT, 'stills')
    os.makedirs(sdir, exist_ok=True)
    thumbs = []
    for t in STILLS:
        img = render(t)
        Image.fromarray(upscale(img)).save(os.path.join(sdir, f'ep01_{t:05.2f}s.png'))
        thumbs.append(img)
    cols = 6
    rows = (len(thumbs) + cols - 1) // cols
    sheet = np.zeros((rows * (SH + 4), cols * (SW + 4), 3), np.uint8)
    for i, im in enumerate(thumbs):
        r, c = divmod(i, cols)
        sheet[r * (SH + 4):r * (SH + 4) + SH, c * (SW + 4):c * (SW + 4) + SW] = im
    Image.fromarray(sheet.repeat(2, 0).repeat(2, 1)).save(os.path.join(OUT, 'ep01_storyboard.png'))


def render_video():
    wav = os.path.join(OUT, 'ep01_audio.wav')
    soundtrack(wav)
    mp4 = os.path.join(OUT, 'ep01.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{SW * SCALE}x{SH * SCALE}', '-r', str(FPS), '-i', '-',
           '-i', wav,
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '44100', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(upscale(render(i / FPS)).tobytes())
        if i % 120 == 0:
            print(f'  frame {i}/{n}', flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print('wrote', mp4)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    save_stills()
    if '--stills' not in sys.argv:
        render_video()
