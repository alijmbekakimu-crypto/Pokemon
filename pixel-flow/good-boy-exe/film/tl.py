"""Timeline DSL for the film: shots made of a set, a camera, actors, captions, fx and sounds."""
import math
import numpy as np

import cast
from engine import (blit, draw_text, shoot, rain_layers, snow, vignette, flash, fade, tint, scanlines,
                    glitch, rect, px, line, bayer, text_mask, _stamp)

W, H = 320, 180
SIZE = (W, H)
FPS = 24


# ---------------------------------------------------------------- easing
def lerp(a, b, u):
    return a + (b - a) * u


def clamp01(u):
    return max(0.0, min(1.0, u))


def smooth(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def seg(t, t0, t1):
    return clamp01((t - t0) / max(t1 - t0, 1e-6))


# ---------------------------------------------------------------- actors
class Act:
    """fn(t) -> list of (sprite, x, y, flip)"""

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, t):
        return self.fn(t) or []


def _spr(s, t):
    return s(t) if callable(s) else s


def put(s, x, y, flip=False, t0=-1e9, t1=1e9):
    return Act(lambda t: [(_spr(s, t), x, y, flip)] if t0 <= t < t1 else None)


def move(s, p0, p1, t0, t1, flip=False, ease=False, hold=(True, True)):
    """Move from p0 to p1 between t0..t1 (holds before/after unless hold=False)."""
    def f(t):
        if t < t0 and not hold[0]:
            return None
        if t >= t1 and not hold[1]:
            return None
        u = seg(t, t0, t1)
        u = smooth(u) if ease else u
        return [(_spr(s, t), lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u), flip)]
    return Act(f)


def path(s, pts, flip=False):
    """pts = [(t, x, y), ...] piecewise linear; sprite may be callable(t)."""
    def f(t):
        if t <= pts[0][0]:
            return [(_spr(s, t), pts[0][1], pts[0][2], flip)]
        for (ta, xa, ya), (tb, xb, yb) in zip(pts, pts[1:]):
            if ta <= t < tb:
                u = (t - ta) / (tb - ta)
                return [(_spr(s, t), lerp(xa, xb, u), lerp(ya, yb, u), flip)]
        return [(_spr(s, t), pts[-1][1], pts[-1][2], flip)]
    return Act(f)


def cyc(frames, fps):
    return lambda t: frames[int(t * fps) % len(frames)]


def run(kind='bolt', eye='on'):
    return lambda t: cast.dog(kind, 'ABCB'[int(t * 12) % 4], eye)


def walk(kind='bolt', eye='on'):
    return lambda t: cast.dog(kind, 'ABCB'[int(t * 8) % 4], eye)


def mira_walk(home=False):
    return lambda t: cast.mira('walk' if int(t * 6) % 2 == 0 else 'stand', home)


def dad_walk(look='lit'):
    return lambda t: cast.dad('walk' if int(t * 6) % 2 == 0 else 'stand', look)


def blink_eye(kind='bolt', pose='A', period=3.0):
    return lambda t: cast.dog(kind, pose, 'blink' if (t % period) > period - 0.12 else 'on')


# ---------------------------------------------------------------- captions
STYLES = {
    'narr': dict(col=(248, 244, 236), cps=30, blip=None),
    'mira': dict(col=(255, 214, 90), cps=24, blip=880),
    'dad': dict(col=(160, 196, 236), cps=22, blip=420),
    'kid': dict(col=(200, 220, 200), cps=24, blip=1100),
    'fake': dict(col=(255, 96, 104), cps=20, blip=300),
    'dealer': dict(col=(120, 255, 150), cps=22, blip=240),
    'unit': dict(col=(255, 150, 70), cps=22, blip=520),
    'hud': dict(col=(96, 236, 255), cps=30, blip='hud'),
    'hudred': dict(col=(255, 72, 84), cps=30, blip='hud'),
    'hudgreen': dict(col=(120, 255, 150), cps=30, blip='hud'),
    'title': dict(col=(248, 244, 236), cps=16, blip=None),
    'big': dict(col=(255, 72, 84), cps=40, blip=None),
}


class Cap:
    def __init__(self, t0, t1, text, who='narr', pos=None):
        self.t0, self.t1, self.text, self.who = t0, t1, text.upper(), who
        self.st = STYLES[who]
        self.pos = pos

    def draw(self, scr, t):
        if not (self.t0 <= t < self.t1):
            return
        lines = self.text.split('\n')
        shown = int((t - self.t0) * self.st['cps']) + 1
        who = self.who
        if who in ('hud', 'hudred', 'hudgreen'):
            x0, y0 = self.pos or (12, 12)
            for j, ln in enumerate(lines):
                vis = ln[:max(0, shown)]
                shown -= len(ln)
                if vis:
                    draw_text(scr, ('> ' if j == 0 else '  ') + vis, x0, y0 + j * 11, self.st['col'], align='left')
            return
        if who in ('title', 'big'):
            sc = 2 if who == 'title' else 3
            y0 = self.pos[1] if self.pos else 70
            for j, ln in enumerate(lines):
                vis = ln[:max(0, shown)]
                shown -= len(ln)
                if vis:
                    fw = len(ln) * 6 * sc - sc
                    draw_text(scr, vis, W / 2 - fw / 2, y0 + j * (7 * sc + 6), self.st['col'], scale=sc, align='left')
            return
        # subtitles: dark band + centred lines at the bottom
        y0 = H - 8 - 12 * len(lines) if not self.pos else self.pos[1]
        band = np.zeros((H, W), bool)
        band[y0 - 3:y0 + 12 * len(lines) - 2, :] = True
        m = band & (bayer(H, W) < 0.55)
        scr[m] = (scr[m].astype(np.float32) * 0.25).astype(np.uint8)
        for j, ln in enumerate(lines):
            vis = ln[:max(0, shown)]
            shown -= len(ln)
            if vis:
                fw = len(ln) * 6 - 1
                draw_text(scr, vis, W / 2 - fw / 2, y0 + j * 12, self.st['col'], align='left')

    def blips(self):
        """(time, kind) list for typing sounds."""
        b = self.st['blip']
        if b is None:
            return []
        out, i = [], 0
        for ch in self.text:
            if ch not in ' \n':
                if b == 'hud' or i % 2 == 0:
                    out.append((self.t0 + i / self.st['cps'], b))
            if ch != '\n':
                i += 1
        return out


def say(t0, dur, text, who='narr', pos=None):
    return Cap(t0, t0 + dur, text, who, pos)


# ---------------------------------------------------------------- screen widgets
_yy, _xx = np.mgrid[0:H, 0:W]


def eye_screen(boot=1.0, red=0.0, white=0.0, cx=84, cy=90, r=1.0):
    s = np.zeros((H, W, 3), np.uint8)
    s[:] = (6, 8, 16)
    s[::12, :] = (12, 18, 32)
    s[:, ::12] = (12, 18, 32)
    d = np.hypot(_xx - cx, _yy - cy) / r
    a = (np.arctan2(_yy - cy, _xx - cx) + np.pi) / (2 * np.pi)
    b = bayer(H, W)
    hous = d <= 60
    s[hous] = (54, 58, 82)
    s[hous & ((-(_xx - cx) - (_yy - cy)) / (85 * r) > b)] = (92, 98, 128)
    s[(d > 58) & (d <= 60)] = (22, 18, 38)
    s[d <= 47] = (20, 22, 34)
    ring = (d >= 39) & (d <= 45)
    gap = ((a * 16) % 1) < 0.12
    on = np.array((96, 236, 255)) * (1 - red) + np.array((255, 72, 84)) * red
    s[ring] = (34, 38, 56)
    s[ring & ~gap & (np.floor(a * 16) < int(boot * 16))] = on.astype(np.uint8)
    iris = d <= 33
    bb = clamp01((boot - 0.25) / 0.75)
    edge = np.array((14, 70, 100)) * (1 - red) + np.array((90, 10, 20)) * red
    core = np.array((110, 240, 255)) * (1 - red) + np.array((255, 90, 90)) * red
    lv = np.clip(1 - d / 33, 0, 1) * bb
    q = np.floor(np.clip(lv * 4 + b * 0.99, 0, 4)) / 4
    col = edge * (1 - q[..., None]) + core * q[..., None]
    col = col * (0.25 + 0.75 * bb) + (np.array((248, 244, 236)) - col) * white
    s[iris] = np.clip(col[iris], 0, 255).astype(np.uint8)
    s[d <= 10] = (8, 14, 24)
    if bb > 0.2:
        rect(s, cx - 16 * r, cy - 18 * r, cx - 11 * r, cy - 15 * r, (240, 250, 255))
        rect(s, cx - 9 * r, cy - 22 * r, cx - 7 * r, cy - 20 * r, (240, 250, 255))
    scanlines(s, 0.78)
    return s


def bar(scr, x, y, w, frac, col=(96, 236, 255), label=None):
    rect(scr, x - 1, y - 1, x + w + 1, y + 8, (60, 70, 90))
    rect(scr, x, y, x + w, y + 7, (10, 14, 24))
    rect(scr, x + 1, y + 1, x + 1 + int((w - 2) * clamp01(frac)), y + 6, col)
    if label:
        draw_text(scr, label, x + w + 6, y, col, align='left')


def pov(scr, t, red=False):
    """Bolt's camera view: corner brackets + scanlines + tint."""
    col = (255, 72, 84) if red else (96, 236, 255)
    tint(scr, (0.55, 1.1, 1.25) if not red else (1.3, 0.5, 0.5), 0.35)
    scanlines(scr, 0.8)
    for (x, y, dx, dy) in ((6, 6, 1, 1), (W - 7, 6, -1, 1), (6, H - 7, 1, -1), (W - 7, H - 7, -1, -1)):
        line(scr, x, y, x + 14 * dx, y, col)
        line(scr, x, y, x, y + 10 * dy, col)
    if int(t * 2) % 2 == 0:
        rect(scr, W - 30, 10, W - 26, 14, (255, 72, 84))
        draw_text(scr, "REC", W - 22, 9, (255, 72, 84), align='left', outline=None)


def subscribe(scr, t, x=12, y=10):
    """Pixel subscribe button with a cursor that clicks it (t: seconds since it appeared)."""
    clicked = t > 1.6
    bw = 84
    rect(scr, x - 1, y - 1, x + bw + 1, y + 17, (10, 8, 20))
    rect(scr, x, y, x + bw, y + 16, (90, 90, 100) if clicked else (214, 40, 52))
    draw_text(scr, "SUBSCRIBED" if clicked else "SUBSCRIBE", x + bw / 2, y + 5, (250, 250, 250), outline=None)
    bx = x + bw + 6
    rect(scr, bx, y + 2, bx + 12, y + 13, (240, 240, 240))
    rect(scr, bx + 4, y + 13, bx + 8, y + 15, (240, 240, 240))
    if 2.2 < t < 3.0 and int(t * 10) % 2:
        line(scr, bx - 2, y, bx - 5, y - 3, (255, 214, 90))
        line(scr, bx + 14, y, bx + 17, y - 3, (255, 214, 90))
    cx = lerp(x + bw + 60, x + bw * 0.6, smooth(seg(t, 0.4, 1.4)))
    cy = lerp(y + 50, y + 9, smooth(seg(t, 0.4, 1.4)))
    if 1.4 < t < 2.2:
        cx, cy = lerp(x + bw * 0.6, bx + 6, smooth(seg(t, 1.8, 2.2))), lerp(y + 9, y + 8, seg(t, 1.8, 2.2))
    if t >= 2.2:
        cx, cy = bx + 6, y + 8
    for i in range(8):
        rect(scr, cx, cy + i, cx + max(1, (i + 1) // 2 + 1), cy + i + 1, (250, 250, 250))
    line(scr, cx - 1, cy, cx - 1, cy + 8, (10, 8, 20))


def card_screen(lines, sub=None, accent=(96, 236, 255)):
    """Black chapter / question card."""
    s = np.zeros((H, W, 3), np.uint8)
    s[:] = (8, 8, 16)
    s[::6, :] = (12, 12, 24)
    return s


# ---------------------------------------------------------------- shots
class Shot:
    def __init__(self, dur, set=None, cam=(160, 90, 1), actors=(), caps=(), fx=(), sfx=(), draw=None,
                 screen=None, hud=None, mood=None, amb=None, name='', nofloor=False):
        self.dur, self.set, self.cam = dur, set, cam
        self.nofloor = nofloor
        self.actors, self.caps, self.fx, self.sfx = list(actors), list(caps), list(fx), list(sfx)
        self.draw, self.screen, self.hud = draw, screen, hud
        self.mood, self.amb, self.name = mood, amb, name

    def camera(self, t):
        c = self.cam
        if callable(c):
            return c(t)
        if len(c) == 3 and not isinstance(c[0], tuple):
            cx, cy, z = c
        else:
            (x0, y0), (x1, y1), z = c[0], c[1], c[2]
            ease = c[3] if len(c) > 3 else True
            u = seg(t, 0, self.dur)
            u = smooth(u) if ease else u
            cx, cy = lerp(x0, x1, u), lerp(y0, y1, u)
        for f in self.fx:
            if isinstance(f, tuple) and f[0] == 'shake' and f[1] <= t < f[2]:
                a = f[3] if len(f) > 3 else 1.5
                cx += (a, -a, a * .6, -a * .6)[int(t * 24) % 4] / z
                cy += (a * .5, -a * .5, 0, a * .3)[int(t * 24) % 4] / z
        if not self.nofloor and z <= 3:
            cy = max(cy, 152 - 66 / z)      # keep feet above the subtitle band
        return cx, cy, z

    def render(self, t):
        if self.screen is not None:
            scr = self.screen(t)
        else:
            world = self.set(t) if callable(self.set) else self.set
            w = world.copy()
            if self.draw:
                self.draw(w, t)
            for a in self.actors:
                for spr, x, y, fl in a(t):
                    blit(w, spr, x, y, fl)
            if self.draw and getattr(self.draw, 'post', None):
                self.draw.post(w, t)
            cx, cy, z = self.camera(t)
            scr = shoot(w, cx, cy, z, size=SIZE)
        names = [f if isinstance(f, str) else f[0] for f in self.fx]
        if 'rain' in names:
            rain_layers(scr, t, 1.0)
        if 'snow' in names:
            snow(scr, t, 1.0)
        if 'vig' in names:
            vignette(scr)
        for f in self.fx:
            if not isinstance(f, tuple):
                if f == 'sepia':
                    tint(scr, (1.25, 1.0, 0.7), 0.75)
                elif f == 'night':
                    tint(scr, (0.5, 0.6, 1.1), 0.4)
                elif f == 'sirens':
                    tint(scr, (1.4, 0.4, 0.5) if int(t * 4) % 2 else (0.4, 0.6, 1.5), 0.25)
                continue
            k = f[0]
            if k == 'flash' and f[1] <= t < f[1] + f[2]:
                flash(scr, 0.85 if t < f[1] + f[2] * 0.4 else 0.35)
            elif k == 'glitch' and f[1] <= t < f[2]:
                amt = f[3] if len(f) > 3 else 0.6
                if (int(t * 24) % 3 == 0) or amt > 0.8:
                    scr = glitch(scr, np.random.default_rng(int(t * 24) + 7), amt)
            elif k == 'tint' and (len(f) < 4 or f[3] <= t < f[4]):
                tint(scr, f[1], f[2])
        if self.hud:
            self.hud(scr, t)
        for c in self.caps:
            c.draw(scr, t)
        for f in self.fx:
            if isinstance(f, tuple):
                if f[0] == 'fadein':
                    fade(scr, 1 - seg(t, 0, f[1]))
                elif f[0] == 'fadeout':
                    fade(scr, seg(t, self.dur - f[1], self.dur))
        return scr


def card(dur, lines, who='title', y=64, sub=None, mood=None, sfx=(), hud=None, extra=()):
    caps = [Cap(0.3, dur, lines, who, pos=(0, y))]
    if sub:
        caps.append(Cap(0.9, dur, sub, 'narr', pos=(0, y + 52)))
    caps += list(extra)
    return Shot(dur, screen=lambda t: card_screen(None), caps=caps,
                fx=[('fadein', 0.4), ('fadeout', 0.4)], mood=mood, sfx=list(sfx), hud=hud)


def chapter_card(n, title, mood=None):
    def hud(scr, t):
        draw_text(scr, f"CHAPTER {n}", W / 2, 52, (96, 236, 255))
        y = 100
        rect(scr, W / 2 - 50 * smooth(seg(t, 0.2, 1.2)), y, W / 2 + 50 * smooth(seg(t, 0.2, 1.2)), y + 1, (96, 236, 255))
    return Shot(4.0, screen=lambda t: card_screen(None), hud=hud,
                caps=[Cap(0.5, 4.0, title, 'title', pos=(0, 70))],
                fx=[('fadein', 0.5), ('fadeout', 0.5)], mood=mood, sfx=[(0.2, 'chime', 0.35)])


def comment_card(question, mood=None):
    def hud(scr, t):
        draw_text(scr, "TELL ME IN THE COMMENTS", W / 2, 128, (150, 150, 196))
        if int(t * 2) % 2 == 0:
            rect(scr, W / 2 - 3, 144, W / 2 + 4, 147, (255, 214, 90))
            rect(scr, W / 2 - 1, 147, W / 2 + 2, 150, (255, 214, 90))
    return Shot(5.5, screen=lambda t: card_screen(None), hud=hud,
                caps=[Cap(0.3, 5.5, question, 'title', pos=(0, 48))],
                fx=[('fadein', 0.4), ('fadeout', 0.4)], mood=mood, sfx=[(0.2, 'chime', 0.3)])


# ---------------------------------------------------------------- chapter assembly
class Chapter:
    def __init__(self, name, shots):
        self.name = name
        self.shots = shots
        self.starts = []
        t = 0.0
        for s in shots:
            self.starts.append(t)
            t += s.dur
        self.dur = t

    def at(self, t):
        for s, st in zip(self.shots, self.starts):
            if st <= t < st + s.dur:
                return s, t - st
        return self.shots[-1], self.shots[-1].dur - 1e-3

    def frame(self, t):
        s, lt = self.at(t)
        return s.render(lt)
