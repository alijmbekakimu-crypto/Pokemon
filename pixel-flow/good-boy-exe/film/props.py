"""Reusable draw hooks for shots (things that change over time inside a set)."""
import numpy as np
import cast
from engine import rect, px, line, ellipse, dither_blend, bayer, draw_text, text_mask, _stamp
from tl import seg, smooth, lerp

G = 150
FOOT = 152          # bottom row for characters standing on the ground
Y_STAND = FOOT - 25  # mira standing
Y_SIT = FOOT - 17    # mira sitting
Y_DOG = FOOT - 18    # bolt standing / sitting
Y_SLEEP = FOOT - 10
Y_DAD = FOOT - 38


def draws(*fns):
    def f(w, t):
        for fn in fns:
            fn(w, t)
    posts = [getattr(fn, 'post', None) for fn in fns if getattr(fn, 'post', None)]
    if posts:
        def post(w, t):
            for p in posts:
                p(w, t)
        f.post = post
    return f


def late(fn):
    """Draw hook that runs after the actors (in front of them)."""
    def f(w, t):
        pass
    f.post = fn
    return f


def crate(x, ybot, open_t=None, glow_t=None, shake=None, hidden_after=None):
    def f(w, t):
        if hidden_after is not None and t >= hidden_after:
            return
        xx = x
        if shake and shake[0] <= t < shake[1]:
            xx += (0, 1, 0, -1)[int(t * 24) % 4]
        o = seg(t, open_t, open_t + 0.15) if open_t is not None else 0
        g = 0.0
        if glow_t is not None and t >= glow_t:
            g = 0.9 * (1 - seg(t, glow_t, glow_t + 4)) + 0.15
        cast.crate_glow(w, xx, ybot, g)
        f.state = (xx, o)
    def post(w, t):
        if hidden_after is not None and t >= hidden_after:
            return
        xx, o = getattr(f, 'state', (x, 0))
        cast.draw_crate(w, xx, ybot, o)
    f.post = post
    return f


def held_crate(dad_x_fn, t1=1e9):
    def f(w, t):
        pass
    def post(w, t):
        if t < t1:
            cast.draw_crate(w, dad_x_fn(t) + 8, FOOT - 12)
    f.post = post
    return f


def peek_bolt(x, ybot, t0, t1, eye_on_t, height=8):
    """Bolt rising inside a crate (call before the crate's post)."""
    top = ybot - cast.CRATE_H + 1
    def f(w, t):
        if t < t0:
            return
        p = lerp(0, height, smooth(seg(t, t0, t1)))
        eye = 'off' if t < eye_on_t else ('blink' if (t - eye_on_t) % 3 > 2.88 else 'on')
        cast.blit_clip(w, cast.dog('bolt', 'A', eye), x + 1, top - p, ymax=top)
        if eye == 'on':
            cast.eye_glow(w, x + 1 + cast.BOLT_EYE[0] + 0.5, top - p + cast.BOLT_EYE[1], density=0.35)
    return f


def ball_at(fn):
    """fn(t) -> (x, y) or None"""
    def f(w, t):
        pass
    def post(w, t):
        p = fn(t)
        if p is not None:
            from engine import blit
            blit(w, cast.BALL, *p)
    f.post = post
    return f


def bounce_path(x0, y0, x1, yg, t0):
    """Ball dropped at (x0,y0) at t0, bounces twice and rolls to x1."""
    def fn(t):
        if t < t0:
            return None
        if t < t0 + 0.3:
            u = seg(t, t0, t0 + 0.3)
            return x0, lerp(y0, yg, u * u)
        if t < t0 + 0.7:
            u = seg(t, t0 + 0.3, t0 + 0.7)
            return lerp(x0, x0 - 1, u), yg - 4 * np.sin(np.pi * u)
        if t < t0 + 0.95:
            u = seg(t, t0 + 0.7, t0 + 0.95)
            return lerp(x0 - 1, x0 - 2, u), yg - 1.5 * np.sin(np.pi * u)
        u = smooth(seg(t, t0 + 0.95, t0 + 1.8))
        return lerp(x0 - 2, x1, u), yg
    return fn


def dirt(x, y, t0, t1, direction=1):
    def f(w, t):
        pass
    def post(w, t):
        if not (t0 <= t < t1 + 0.6):
            return
        rng = np.random.default_rng(42)
        for s in np.arange(t0, t1, 1 / 24):
            r = rng.random(3)
            age = t - s
            if 0 <= age < 0.6:
                xx = x + direction * (40 + 40 * r[0]) * age
                yy = y - (45 + 35 * r[1]) * age + 160 * age * age
                px(w, xx, yy, (96, 68, 54) if r[2] < 0.6 else (130, 96, 70))
    f.post = post
    return f


def hole(x, y, t0, t1, rmax=6):
    def f(w, t):
        if t < t0:
            return
        p = seg(t, t0, t1)
        ellipse(w, x, y, 1 + rmax * p, 0.6 + 1.6 * p, (16, 10, 14))
        ellipse(w, x + 30, y + 2, 1 + 4 * p, 0.6 + 1.8 * p, (74, 52, 44))
    return f


def lightning(t0, x=120, seed=9):
    def f(w, t):
        if not (t0 <= t < t0 + 0.3):
            return
        rng = np.random.default_rng(seed)
        xx, yy = float(x), 0.0
        pts = [(xx, yy)]
        while yy < 128:
            xx += rng.integers(-5, 6)
            yy += rng.integers(5, 11)
            pts.append((xx, yy))
        for (a, b), (c, d) in zip(pts, pts[1:]):
            line(w, a, b, c, d, (240, 240, 255))
            line(w, a + 1, b, c + 1, d, (170, 170, 230))
    return f


def flashlight(fn, length=56, spread=0.28):
    """fn(t) -> (x, y, dir) origin of a torch beam."""
    def f(w, t):
        pass
    def post(w, t):
        p = fn(t)
        if p is None:
            return
        x0, y0, d = p
        Hh, Ww = w.shape[:2]
        yy, xx = np.mgrid[0:Hh, 0:Ww]
        dx = (xx - x0) * d
        cone = (dx > 0) & (dx < length) & (np.abs(yy - y0 - dx * 0.25) < dx * spread + 1)
        amt = np.clip(1 - dx / length, 0, 1) * 0.32
        m = cone & (amt > bayer(Hh, Ww))
        w[m] = ((w[m].astype(np.float32) + (255, 240, 190)) / 2).astype(np.uint8)
    f.post = post
    return f


def window_rain(x, y, ww, hh, t_scale=1.0):
    def f(w, t):
        rng = np.random.default_rng(int(t * 12))
        for _ in range(int(ww * hh / 40)):
            xx, yy = x + rng.integers(0, ww), y + rng.integers(0, hh - 3)
            px(w, xx, yy, (130, 140, 190))
            px(w, xx, yy + 1, (100, 110, 160))
    return f


def window_snow(x, y, ww, hh):
    def f(w, t):
        rng = np.random.default_rng(3)
        for i in range(int(ww * hh / 60)):
            xx = x + (rng.integers(0, ww) + int(6 * np.sin(t + i))) % ww
            yy = y + (rng.integers(0, hh) + int(t * 10)) % hh
            px(w, xx, yy, (230, 234, 250))
    return f


def wall_clock(x, y, text_fn):
    def f(w, t):
        rect(w, x - 2, y - 2, x + 32, y + 10, (20, 20, 30))
        draw_text(w, text_fn(t), x + 15, y, (255, 72, 84), outline=None)
    return f


def ecg(alive=True):
    import sets16
    return lambda w, t: sets16.ecg(w, t, alive)


def warning_light():
    import sets16
    return lambda w, t: sets16.warning_light(w, t)


def vehicle(kind, x_fn, ybot, lights=False):
    def f(w, t):
        x = x_fn(t)
        if kind == 'ambulance':
            cast.ambulance(w, x, ybot, t)
        else:
            cast.van(w, x, ybot, lights=lights, t=t)
    return f


def cable(a, b, t0, t1):
    def f(w, t):
        pass
    def post(w, t):
        if not (t0 <= t < t1):
            return
        (x0, y0), (x1, y1) = a, b
        k = 24
        for i in range(k + 1):
            u = i / k
            xx = lerp(x0, x1, u)
            yy = lerp(y0, y1, u) + 4 * np.sin(np.pi * u)
            on = (i - int(t * 30)) % 6 == 0
            px(w, xx, yy, (180, 255, 255) if on else (60, 140, 170))
    f.post = post
    return f


def photo_in_chest(x, y, t0):
    def f(w, t):
        pass
    def post(w, t):
        if t < t0:
            return
        o = smooth(seg(t, t0, t0 + 0.6))
        rect(w, x - 1, y - 1, x + 9, y + 8, (70, 56, 58))
        if o > 0.5:
            rect(w, x, y, x + 8, y + 7, (220, 220, 230))
            rect(w, x + 2, y + 2, x + 6, y + 7, (242, 194, 66))
            rect(w, x + 3, y + 1, x + 5, y + 3, (238, 190, 160))
    f.post = post
    return f


def footprints(x0, x1, y, t0, t1):
    def f(w, t):
        if t < t0:
            return
        xe = lerp(x0, x1, seg(t, t0, t1))
        for xx in np.arange(min(x0, xe), max(x0, xe), 4):
            px(w, xx, y + (int(xx) // 4) % 2, (150, 160, 196))
    return f
