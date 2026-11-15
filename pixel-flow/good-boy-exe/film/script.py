"""GOOD BOY.exe — the film. Every chapter is a list of shots."""
import numpy as np

import cast
import sets16 as S
from engine import draw_text, rect
from tl import (Shot, Chapter, Cap, say, card, chapter_card, comment_card, put, move, path, cyc, run, walk,
                mira_walk, dad_walk, blink_eye, eye_screen, bar, pov, subscribe, seg, smooth, lerp, Act, W, H)
from props import (draws, late, crate, held_crate, peek_bolt, ball_at, bounce_path, dirt, hole, lightning,
                   flashlight, window_rain, window_snow, wall_clock, ecg, warning_light, vehicle, cable,
                   photo_in_chest, footprints, FOOT, Y_STAND, Y_SIT, Y_DOG, Y_SLEEP, Y_DAD)

D = cast.dog
M = cast.mira
DAD = cast.dad
GX = S.GRAVE_X
CYAN, RED, GREEN, GREY = (96, 236, 255), (255, 72, 84), (120, 255, 150), (150, 150, 196)


def hud_text(lines, col=CYAN, x=12, y=12, t0=0.0, cps=30):
    """Static HUD overlay typed in from t0."""
    def f(scr, t):
        shown = int((t - t0) * cps) + 1
        for j, ln in enumerate(lines):
            vis = ln[:max(0, shown)]
            shown -= len(ln)
            if vis:
                draw_text(scr, vis, x, y + j * 11, col, align='left')
    return f


def hud_all(*fs):
    def f(scr, t):
        for fn in fs:
            fn(scr, t)
    return f


def eye_shot(dur, lines, boot=(0.0, 1.0), red=0.0, glitch=None, mood='mystery', sfx=(), white_t=None, styles=None):
    """Bolt's eye on the left, HUD lines typed on the right."""
    caps = []
    for i, item in enumerate(lines):
        t0, text = item[0], item[1]
        who = item[2] if len(item) > 2 else 'hud'
        caps.append(Cap(t0, dur, text, who, pos=(162, 52 + i * 18)))
    def scr_fn(t):
        b = lerp(boot[0], boot[1], smooth(seg(t, 0, 1.6)))
        r = red(t) if callable(red) else red
        wh = 0.6 * (1 - seg(t, white_t, white_t + 0.4)) if white_t is not None and t >= white_t else 0
        return eye_screen(b, r, wh)
    fx = [('fadein', 0.2)]
    if glitch:
        fx.append(('glitch',) + tuple(glitch))
    return Shot(dur, screen=scr_fn, caps=caps, fx=fx, mood=mood, sfx=list(sfx), amb='none')


def screen_shot(dur, lines, col=CYAN, mood='mystery', sfx=(), title=None, red_box=False, glitch=None, extra=None):
    """A computer / HUD window full screen."""
    def scr_fn(t):
        s = np.zeros((H, W, 3), np.uint8)
        s[:] = (10, 14, 26)
        s[::3] = (14, 18, 32)
        rect(s, 30, 24, 290, 156, (24, 30, 48))
        rect(s, 30, 24, 290, 36, (214, 52, 62) if red_box else (60, 80, 120))
        if title:
            draw_text(s, title, 36, 27, (250, 250, 250), align='left', outline=None)
        if extra:
            extra(s, t)
        return s
    caps = []
    for i, item in enumerate(lines):
        t0, text = item[0], item[1]
        who = item[2] if len(item) > 2 else 'hud'
        caps.append(Cap(t0, dur, text, who, pos=(36, 46 + i * 16)))
    fx = [('fadein', 0.2)]
    if glitch:
        fx.append(('glitch',) + tuple(glitch))
    return Shot(dur, screen=scr_fn, caps=caps, fx=fx, mood=mood, sfx=list(sfx), amb='none')


def spin(kind='bolt', x=0, y=0, t0=0, t1=99):
    def f(t):
        if t0 <= t < t1:
            k = int(t * 8) % 4
            return [(D(kind, 'C' if k % 2 else 'A'), x, y - (1 if k % 2 else 0), k >= 2)]
        return [(D(kind, 'A'), x, y, False)]
    return Act(f)


def counter(text_fn, col=(248, 244, 236)):
    def f(scr, t):
        s = text_fn(t)
        bw = len(s) * 12 + 10
        rect(scr, W - 8 - bw, 8, W - 8, 30, (10, 8, 20))
        draw_text(scr, s, W - 8 - bw / 2, 13, col, scale=2, outline=None)
    return f


# ======================================================================== COLD OPEN
def cold_open():
    jy = S.junkyard()
    sh = []
    sh.append(Shot(7, jy, ((150, 90), (300, 90), 1), draw=warning_light(), fx=['rain', 'vig', ('fadein', 1.5)],
                   caps=[say(1.0, 5.5, "THIS IS A JUNKYARD FOR BROKEN ROBOTS.")], mood='tense', amb='rain',
                   sfx=[(0.8, 'thunder', 0.6)]))
    sh.append(Shot(6, jy, (262, 136, 3), draw=warning_light(),
                   actors=[put(lambda t: D('bolt', 'sleep', 'red' if int(t * 3) % 3 == 0 else 'off'), 246, Y_SLEEP)],
                   fx=['rain', 'vig'], caps=[say(0.8, 5, "AND THIS IS BOLT.")], mood='tense', amb='rain',
                   sfx=[(1.0, 'powerdown', 0.4)]))
    sh.append(eye_shot(5, [(0.3, "BATTERY: 1%", 'hudred'), (1.4, "SHUTDOWN IN 00:40", 'hudred')],
                       boot=(0.3, 0.4), red=1.0, glitch=(0, 5, 0.4), mood='tense', sfx=[(0.2, 'alarm', 0.5), (1.4, 'alarm', 0.5)]))
    sh.append(Shot(6, jy, ((170, 120), (220, 120), 2), draw=draws(warning_light(), flashlight(lambda t: (lerp(120, 222, seg(t, 0, 4)) + 12, 136, 1))),
                   actors=[put(lambda t: D('bolt', 'sleep', 'off'), 246, Y_SLEEP),
                           move(mira_walk(), (110, Y_STAND), (222, Y_STAND), 0, 4)],
                   fx=['rain', 'vig'], caps=[say(2.5, 3.5, "BOLT!!", 'mira')], mood='tense', amb='rain',
                   sfx=[(t, 'step', 0.4) for t in np.arange(0.1, 4, 0.33)]))
    sh.append(Shot(6, jy, (240, 136, 4), actors=[put(D('bolt', 'sleep', 'off'), 246, Y_SLEEP), put(M('kneel'), 228, FOOT - 18)],
                   fx=['rain', 'vig'], caps=[say(0.5, 5.5, "BOLT, IT'S ME. IT'S MIRA.", 'mira')], mood='sad', amb='rain'))
    sh.append(eye_shot(5, [(0.6, "FACE SCAN...", 'hudred'), (2.0, "UNKNOWN USER.", 'hudred')], boot=(0.5, 0.5), red=1.0,
                       glitch=(2.0, 5, 0.9), mood='tense', sfx=[(2.0, 'glitch', 0.6)]))
    sh.append(card(6, "HOW DID HE\nGET HERE?", y=50, sub="40 DAYS EARLIER...", mood=None))

    def title_hud(scr, t):
        pass
    def title_scr(t):
        s = eye_screen(smooth(seg(t, 0.2, 2.5)), cx=160, cy=78, r=0.9)
        if t > 2.6:
            m = int((t - 2.6) * 10) + 1
            txt = "GOOD BOY.EXE"[:m]
            fw = 12 * 6 * 3 - 3
            draw_text(s, txt, 160 - fw / 2, 140, CYAN, scale=3, align='left')
        if t > 4.2:
            draw_text(s, "A PIXEL FLOW FILM", 160, 168, GREY)
        return s
    sh.append(Shot(8, screen=title_scr, fx=[('fadein', 0.3), ('fadeout', 0.8)], mood='mystery', amb='none',
                   sfx=[(0.2, 'boot', 0.5), (2.6, 'impact', 0.6), (4.2, 'chime', 0.4)]))
    return Chapter('00_cold_open', sh)


# ======================================================================== CHAPTER 1
def ch1():
    rainy = S.yard('rain')
    sh = [chapter_card(1, "THE BOX", mood='sad')]
    sh.append(Shot(9, rainy, ((180, 90), (230, 90), 1), actors=[put(M('sit'), 228, Y_SIT)], fx=['rain', 'vig', ('fadein', 1)],
                   caps=[say(0.8, 4, "SHE BURIED HER DOG YESTERDAY."), say(5, 4, "HIS NAME WAS BOLT.")], mood='sad'))
    sh.append(Shot(9, rainy, (250, 128, 3), actors=[put(lambda t: M('sit'), 228, lambda_y := Y_SIT)],
                   fx=['rain', 'vig'], caps=[say(0.5, 4, "HE WAS NINE YEARS OLD."), say(4.6, 4.4, "HE WAS THERE THE DAY SHE WAS BORN.")], mood='sad'))
    day = S.yard('day')
    sh.append(Shot(7, day, (200, 112, 2),
                   actors=[put(M('stand'), 150, Y_STAND), move(run('old'), (166, Y_DOG), (246, Y_DOG), 0.8, 3.0)],
                   draw=ball_at(lambda t: (lerp(164, 262, seg(t, 0.5, 2.6)), 130 - 30 * np.sin(np.pi * seg(t, 0.5, 2.6)) + 16 * seg(t, 0.5, 2.6)) if t < 2.6 else (262, 146)),
                   fx=['sepia', 'vig', ('fadein', 0.6)], caps=[say(0.5, 6, "HE WAS HER BEST FRIEND.")], mood='tender', amb='none',
                   sfx=[(2.6, 'bounce', 0.5), (1.0, 'bark', 0.4)]))
    sh.append(Shot(8, day, (180, 124, 3),
                   actors=[move(walk('old'), (240, Y_DOG), (176, Y_DOG), 0, 2.5, flip=True), put(lambda t: M('kneel') if t > 2.8 else M('stand'), 152, lambda_y2 := FOOT - 18)],
                   draw=ball_at(lambda t: (lerp(238, 174, seg(t, 0, 2.5)), Y_DOG + 7) if t < 2.5 else (174, Y_DOG + 7)),
                   fx=['sepia', 'vig', ('fadeout', 0.6)], caps=[say(0.5, 7, "EVERY DAY. RAIN OR SHINE.")], mood='tender', amb='none'))
    sh[-1].actors[1] = Act(lambda t: [(M('kneel'), 152, FOOT - 18, False)] if t > 2.8 else [(M('stand'), 152, Y_STAND, False)])
    sh.append(Shot(7, rainy, (268, 140, 5), fx=['rain', 'vig', ('fadein', 0.6)],
                   caps=[say(0.5, 6, "NOW ALL THAT WAS LEFT\nWAS HIS COLLAR.")], mood='sad'))
    porch = S.yard('rain', door=0.5)
    sh.append(Shot(8, porch, (80, 112, 2), actors=[put(DAD('stand', 'silhouette'), 54, Y_DAD), put(M('sit'), 228, Y_SIT)],
                   fx=['rain', 'vig'], caps=[say(0.5, 7, "SHE HADN'T SAID A WORD IN TWO DAYS.")], mood='sad'))
    dx = lambda t: lerp(52, 160, seg(t, 0.5, 7.5))
    sh.append(Shot(9, rainy, ((130, 90), (200, 90), 1),
                   actors=[Act(lambda t: [(DAD('walk' if (int(t * 6) % 2 == 0 and t < 7.5) else 'stand', 'silhouette'), dx(t), Y_DAD, False)]),
                           put(M('sit'), 228, Y_SIT)],
                   draw=held_crate(dx), fx=['rain', 'vig'], caps=[say(1, 7, "THEN DAD CAME HOME WITH A BOX.")], mood='sad',
                   sfx=[(t, 'step', 0.35, -0.3) for t in np.arange(0.5, 7.5, 0.33)]))
    lower = lambda t: (lerp(168, 186, smooth(seg(t, 0, 1))), lerp(FOOT - 12, FOOT, smooth(seg(t, 0, 1))))
    def set_down(w, t):
        pass
    def set_down_post(w, t):
        x, yb = lower(t)
        cast.draw_crate(w, x, yb)
    set_down.post = set_down_post
    sh.append(Shot(11, rainy, (205, 124, 2), actors=[put(DAD('stand', 'silhouette'), 160, Y_DAD), put(M('sit'), 228, Y_SIT)],
                   draw=set_down, fx=['rain', 'vig'],
                   caps=[say(1.2, 3, "I KNOW IT'S TOO SOON.", 'dad'), say(4.4, 2.8, "I DON'T WANT A TOY.", 'mira'),
                         say(7.4, 3.6, "JUST... GIVE IT A CHANCE.", 'dad')],
                   mood='sad', sfx=[(1.0, 'thud', 0.6)]))
    sh.append(Shot(10, rainy, (200, 140, 4),
                   draw=draws(peek_bolt(186, FOOT, 5.2, 6.4, 7.0), crate(186, FOOT, open_t=4.6, glow_t=4.6, shake=(1.5, 4.6))),
                   actors=[put(DAD('stand', 'silhouette'), 160, Y_DAD)], fx=['rain', 'vig'],
                   mood='mystery', sfx=[(1.5 + i * 0.12, 'knock', 0.4, 0.2 * (-1) ** i) for i in range(25)]
                   + [(4.6, 'burst', 0.7), (4.7, 'shimmer', 0.4), (5.2, 'servo', 0.4), (7.0, 'chirp', 0.4)]))
    sh.append(eye_shot(8, [(1.0, "K-9 UNIT: ONLINE"), (2.6, "SCANNING..."), (4.4, "USER FOUND: MIRA", 'hudgreen')],
                       boot=(0.0, 1.0), mood='mystery', sfx=[(0.1, 'boot', 0.5), (4.4, 'chirp', 0.4)]))
    sh.append(Shot(7, rainy, (214, 128, 3),
                   draw=draws(peek_bolt(186, FOOT, -1, 0, 0), crate(186, FOOT, open_t=-1)),
                   actors=[put(M('sit'), 228, Y_SIT)], fx=['rain', 'vig'],
                   caps=[say(0.5, 3, "HOW DOES IT KNOW MY NAME?", 'mira'), say(3.8, 3.2, "I... DON'T KNOW.", 'dad')], mood='mystery'))
    # leap and run to the grave
    def bolt_run(t):
        if t < 0.6:
            u = seg(t, 0, 0.6)
            return [(D('bolt', 'B'), lerp(187, 200, u), lerp(FOOT - 23, Y_DOG + 4, u) - 14 * np.sin(np.pi * u), False)]
        if t < 2.4:
            legs = 'ABCB'[int(t * 12) % 4]
            return [(D('bolt', legs), lerp(200, 276, seg(t, 0.6, 2.4)), Y_DOG + 4, False)]
        bob = (0, 2, 0, 1)[int(t * 12) % 4]
        return [(D('bolt', 'AC'[int(t * 12) % 2]), 266, Y_DOG + 4 + bob, True)]
    sh.append(Shot(9, rainy, (232, 112, 2), actors=[put(lambda t: M('shout') if t > 2.6 else M('sit'), 216, Y_STAND), Act(bolt_run)],
                   draw=draws(crate(186, FOOT, open_t=-1), lightning(4.0, x=200), hole(268, FOOT + 1, 2.6, 9), dirt(270, FOOT + 2, 2.6, 9)),
                   fx=['rain', 'vig', ('flash', 4.0, 0.3), ('shake', 2.6, 3.0, 2)],
                   caps=[Cap(2.6, 9, "STOP!", 'big', pos=(0, 20)), Cap(3.1, 9, "BOLT, NO!", 'title', pos=(0, 52))],
                   mood='tense', sfx=[(0.0, 'whoosh', 0.4), (2.6, 'impact', 0.8), (4.1, 'thunder', 0.8)]
                   + [(t, 'paw', 0.2) for t in np.arange(0.7, 2.4, 0.125)] + [(t, 'dig', 0.4, 0.3) for t in np.arange(2.6, 9, 0.17)]))
    sh[-1].actors[0] = Act(lambda t: [(M('shout') if t > 2.6 else M('sit'), 216 if t > 2.6 else 228, Y_STAND if t > 2.6 else Y_SIT, False)])
    def dig_head(t):
        if t < 4.5:
            return [(D('bolt', 'AC'[int(t * 12) % 2]), 266, Y_DOG + 4 + (0, 2, 0, 1)[int(t * 12) % 4], True)]
        if t < 5.3:
            return [(D('bolt', 'A'), 266, Y_DOG + 7, True)]
        return [(D('bolt', 'A'), 266, Y_DOG + 4, True)]
    sh.append(Shot(7, rainy, (280, 140, 4), actors=[Act(dig_head)],
                   draw=draws(hole(268, FOOT + 1, -6, 4.5), dirt(270, FOOT + 2, 0, 4.5), ball_at(lambda t: (264, Y_DOG + 11) if t > 5.3 else None)),
                   fx=['rain', 'vig'], mood='tense', sfx=[(t, 'dig', 0.4, 0.3) for t in np.arange(0, 4.5, 0.17)] + [(5.3, 'servo', 0.3)]))
    # bring the ball
    bpos = lambda t: lerp(266, 238, seg(t, 0, 4))
    sh.append(Shot(9, rainy, (236, 132, 3),
                   actors=[put(M('stand'), 216, Y_STAND), Act(lambda t: [(D('bolt', 'ABCB'[int(t * 8) % 4] if t < 4 else 'A'), bpos(t), Y_DOG + 4, True)])],
                   draw=draws(hole(268, FOOT + 1, -9, 0), ball_at(lambda t: (bpos(t) - 2, Y_DOG + 11) if t < 5 else bounce_path(236, Y_DOG + 11, 232, FOOT - 1, 5)(t))),
                   fx=['rain', 'vig'], mood=None, sfx=[(5.3, 'bounce', 0.6), (5.7, 'bounce', 0.35), (5.95, 'bounce', 0.18)]
                   + [(t, 'paw', 0.12) for t in np.arange(0, 4, 0.25)]))
    sh.append(Shot(7, rainy, (225, 133, 8), actors=[put(M('stand'), 216, Y_STAND)],
                   draw=late(lambda w, t: w.__setitem__((slice(int(133 + 6 * seg(t, 1, 3)), int(134 + 6 * seg(t, 1, 3))), slice(226, 227)), (200, 236, 255)) if 1 <= t < 3.2 else None),
                   fx=['rain', 'vig'], caps=[say(3, 4, "...HOW DO YOU KNOW?", 'mira')], mood=None, sfx=[(3.1, 'plink', 0.3)]))
    sh.append(Shot(6, rainy, (180, 118, 3), actors=[put(DAD('stand', 'silhouette'), 160, Y_DAD)], fx=['rain', 'vig'],
                   caps=[say(0.8, 5, "I NEVER TAUGHT IT THAT.", 'dad')], mood=None))
    sh.append(eye_shot(7, [(0.6, "MEMORY FILE: BOLT_2019"), (2.6, "STATUS: RESTORED", 'hudgreen'), (4.4, "ORIGIN: UNKNOWN", 'hudred')],
                       red=lambda t: 0.5 + 0.5 * np.sin(t * 6) if t > 4.4 else 0, glitch=(4.4, 7, 0.5), mood='glitch',
                       sfx=[(2.6, 'ding', 0.4), (4.4, 'glitch', 0.5)]))
    sh.append(comment_card("WOULD YOU KEEP A ROBOT\nTHAT REMEMBERS\nYOUR DOG?", mood='mystery'))
    return Chapter('01_the_box', sh)


# ======================================================================== CHAPTER 2
def ch2():
    sh = [chapter_card(2, "GOOD BOY", mood='tender')]
    bed = S.bedroom(door=0.7)
    sh.append(Shot(9, bed, (160, 90, 1), actors=[put(cast.MIRA_BED_HEAD, 46, 108), put(D('bolt', 'sit'), 280, Y_DOG - 4)],
                   draw=window_rain(196, 34, 56, 50), fx=['vig', ('fadein', 0.8)],
                   caps=[say(0.8, 4, "AT FIRST, SHE MADE HIM SLEEP IN THE HALLWAY."), say(5, 4, "HE DIDN'T COMPLAIN.")], mood='tender', amb='room'))
    clock = wall_clock(120, 30, lambda t: "02:59" if t < 2.5 else "03:00")
    sh.append(Shot(4.5, bed, (135, 36, 6), draw=clock, mood='tender', amb='room', sfx=[(2.5, 'tick', 0.5)]))
    def sneak(t):
        if t < 5:
            return [(D('bolt', 'ABCB'[int(t * 6) % 4]), lerp(276, 120, seg(t, 0, 5)), Y_DOG - 4, True)]
        if t < 5.6:
            u = seg(t, 5, 5.6)
            return [(D('bolt', 'B'), lerp(120, 104, u), lerp(Y_DOG - 4, 104, u) - 8 * np.sin(np.pi * u), True)]
        return [(D('bolt', 'sleep', 'blink' if (t % 3) > 2.85 else 'on'), 100, 107, False)]
    sh.append(Shot(11, bed, (150, 100, 1), actors=[put(cast.MIRA_BED_HEAD, 46, 108), Act(sneak)], draw=draws(clock, window_rain(196, 34, 56, 50)),
                   fx=['vig'], caps=[say(1, 4, "BUT AT 3 AM, HE CAME IN ANYWAY."), say(6, 5, "THE OLD BOLT USED TO DO\nEXACTLY THE SAME THING.")],
                   mood='tender', amb='room', sfx=[(t, 'paw', 0.08) for t in np.arange(0, 5, 0.33)] + [(5.6, 'thud', 0.2)]))
    sh.append(Shot(6, bed, (80, 112, 4), actors=[put(cast.MIRA_BED_HEAD, 46, 108), put(D('bolt', 'sleep'), 100, 107)],
                   caps=[say(1.5, 4.5, "...GOOD BOY.", 'mira')], fx=['vig'], mood='tender', amb='room'))
    day = S.yard('day')
    sh.append(Shot(10, day, (190, 120, 2), actors=[put(M('stand'), 160, Y_STAND), spin('bolt', 196, Y_DOG, 3.5, 7)],
                   fx=['vig', ('fadein', 0.5)], caps=[say(0.5, 3, "OKAY, BOLT. SIT.", 'mira'), say(3.6, 5.5, "HE SPUN IN A CIRCLE INSTEAD.")],
                   mood='tender', amb='none', sfx=[(3.6, 'servo', 0.3), (4.4, 'servo', 0.3), (5.2, 'bark', 0.4)]))
    sh.append(Shot(9, day, (176, 128, 3), actors=[put(M('kneel'), 166, FOOT - 18), spin('bolt', 190, Y_DOG, 0, 2)],
                   hud=lambda scr, t: subscribe(scr, t - 4) if 4 <= t < 9 else None,
                   caps=[say(0.5, 4, "THE OLD BOLT SPUN WHEN HE WAS HAPPY."), say(4.6, 4.4, "SHE LAUGHED.\nFOR THE FIRST TIME IN A WEEK.")],
                   fx=['vig'], mood='tender', amb='none', sfx=[(5.6, 'click', 0.0)] if False else []))
    # fetch montage
    def fetch_ball(t):
        u = seg(t, 0.5, 2.0)
        if t < 0.5:
            return 172, Y_STAND + 8
        if t < 2.0:
            return lerp(172, 300, u), Y_STAND + 8 - 34 * np.sin(np.pi * u) + 18 * u
        if t < 3.4:
            return 300, FOOT - 4
        if t < 6:
            return lerp(296, 190, seg(t, 3.4, 6)), Y_DOG + 7
        return 190, Y_DOG + 7
    def fetch_dog(t):
        if t < 1.0:
            return [(D('bolt', 'A'), 186, Y_DOG, False)]
        if t < 3.4:
            return [(D('bolt', 'ABCB'[int(t * 12) % 4]), lerp(186, 300, seg(t, 1.0, 3.2)), Y_DOG, False)]
        return [(D('bolt', 'ABCB'[int(t * 12) % 4] if t < 6 else 'A'), lerp(300, 192, seg(t, 3.4, 6)), Y_DOG, True)]
    sh.append(Shot(9, day, ((200, 100), (240, 100), 1), actors=[put(M('stand'), 160, Y_STAND), Act(fetch_dog)],
                   draw=ball_at(fetch_ball), hud=counter(lambda t: "DAY 3"), fx=['vig'],
                   caps=[say(1, 7, "THEY PLAYED FETCH UNTIL IT GOT DARK.")], mood='tender', amb='none',
                   sfx=[(2.0, 'bounce', 0.4), (3.4, 'servo', 0.2)]))
    sh.append(Shot(10, S.bedroom(lamp=True), (214, 118, 2), actors=[put(M('sit', True), 196, Y_SIT), put(D('bolt', 'sit'), 222, Y_DOG)],
                   draw=window_rain(196, 34, 56, 50), hud=counter(lambda t: "DAY 7"), fx=['vig', ('fadein', 0.5)],
                   caps=[say(0.8, 4.2, "WHEN IT RAINED, THEY WATCHED\nTHE WINDOW TOGETHER."), say(5.4, 4.6, "SHE STARTED TALKING AGAIN.")],
                   mood='tender', amb='room'))
    sch = S.school()
    kids = [move(lambda t: cast.kid((90, 140, 200)) if int(t * 6) % 2 else cast.kid((90, 140, 200)), (140, Y_STAND), (40, Y_STAND), 1, 7, flip=True),
            move(lambda t: cast.kid((120, 190, 110), (40, 30, 30)), (160, Y_STAND), (60, Y_STAND), 2, 8, flip=True)]
    sh.append(Shot(10, sch, (180, 100, 1), actors=[put(D('bolt', 'sit'), 196, Y_DOG)] + kids,
                   hud=counter(lambda t: "15:15", RED), fx=['vig', ('fadein', 0.5)],
                   caps=[say(0.8, 4.5, "EVERY DAY AT 3:15,"), say(5.4, 4.5, "HE WAITED AT THE SCHOOL GATE.")], mood='tender', amb='city'))
    sh.append(Shot(10, sch, (196, 120, 2), actors=[put(D('bolt', 'sit'), 206, Y_DOG), put(cast.kid((200, 90, 90), (30, 26, 30)), 166, Y_STAND),
                                                  move(mira_walk(), (176, Y_STAND), (190, Y_STAND), 3, 4.5)],
                   fx=['vig'], caps=[say(0.5, 3, "IS THAT A ROBOT?", 'kid'), say(4.6, 5, "HE'S NOT A ROBOT.\nHE'S MY DOG.", 'mira')],
                   mood='tender', amb='city'))
    sh[-1].actors[2] = Act(lambda t: [(M('walk' if int(t * 6) % 2 and t < 4.5 else 'stand'), lerp(140, 186, seg(t, 3, 4.5)), Y_STAND, False)] if t > 3 else [])
    liv = S.living(laptop=True)
    sh.append(Shot(8, liv, (320, 120, 2), actors=[put(DAD('stand'), 312, Y_DAD), put(D('bolt', 'sit'), 250, Y_DOG)],
                   fx=['vig', ('fadein', 0.5), 'night'], caps=[say(0.8, 6.5, "BUT AT NIGHT, DAD COULDN'T SLEEP.")], mood='mystery', amb='room'))
    sh.append(screen_shot(9, [(0.5, "UNIT: K-9  #0002"), (1.8, "OWNER: [DATA REMOVED]"), (3.4, "WARNING:", 'hudred'),
                              (4.2, "UNREGISTERED MEMORY DETECTED", 'hudred'), (6.2, "RETURN UNIT IMMEDIATELY.", 'hudred')],
                          title="NEXA ROBOTICS - SUPPORT", red_box=True, mood='mystery', sfx=[(3.4, 'alarm', 0.4)]))
    sh.append(Shot(7, S.living(laptop=False), (300, 118, 3), actors=[put(DAD('stand'), 312, Y_DAD), put(D('bolt', 'sit'), 270, Y_DOG)],
                   fx=['vig', 'night'], caps=[say(1, 2.5, "...NOT YET.", 'dad'), say(4, 3, "HE CLOSED THE LAPTOP.")], mood='mystery', amb='room',
                   sfx=[(0.6, 'knock', 0.3)]))
    def pov_hud(scr, t):
        pov(scr, t)
    sh.append(Shot(7, S.living(laptop=False), (318, 104, 3), actors=[put(DAD('stand'), 312, Y_DAD)], hud=pov_hud,
                   caps=[Cap(0.5, 7, "SUBJECT: DAD", 'hud', pos=(14, 22)), Cap(1.8, 7, "STRESS LEVEL: HIGH", 'hudred', pos=(14, 34)),
                         Cap(3.4, 7, "HE IS HIDING SOMETHING.", 'hud', pos=(14, 46))], mood='mystery', amb='room'))
    sh.append(comment_card("WHAT IS DAD HIDING?\nWRITE YOUR THEORY", mood='mystery'))
    return Chapter('02_good_boy', sh)


# ======================================================================== CHAPTER 3
def ch3():
    sh = [chapter_card(3, "WAITING", mood='sad')]
    bed = S.bedroom(lamp=True)
    sh.append(Shot(9, bed, (100, 100, 2), actors=[put(cast.MIRA_BED_HEAD, 46, 108), put(D('bolt', 'sleep'), 100, 107)],
                   draw=window_rain(196, 34, 56, 50), fx=['vig', ('fadein', 0.6), ('flash', 6, 0.25)],
                   caps=[say(0.8, 4, "THEN, ONE STORMY NIGHT,"), say(5, 4, "SHE GOT SICK.")], mood='sad', amb='room',
                   sfx=[(1.5, 'cough', 0.6), (3.0, 'cough', 0.5), (6.2, 'thunder', 0.6)]))
    sh.append(Shot(7, bed, (60, 110, 4), actors=[put(cast.MIRA_BED_HEAD, 46, 108)], hud=(lambda scr, t: pov(scr, t, red=True)),
                   caps=[Cap(0.4, 7, "BODY TEMP: 40.6 C", 'hudred', pos=(14, 22)), Cap(1.8, 7, "HEART RATE: 148", 'hudred', pos=(14, 34)),
                         Cap(3.2, 7, "ALERT: WAKE THE HUMAN!", 'hudred', pos=(14, 46))], mood='tense', amb='room', sfx=[(0.4, 'alarm', 0.5), (3.2, 'alarm', 0.5)]))
    sh.append(Shot(8, S.living(lamp=False), (270, 116, 2), actors=[put(DAD('stand'), 236, Y_DAD), move(run(), (330, Y_DOG), (262, Y_DOG), 0, 1.4, flip=True)],
                   fx=['vig', 'night'], caps=[say(2.0, 2.8, "WOOF! WOOF!", 'unit'), say(5.0, 3, "BOLT? WHAT IS IT?", 'dad')],
                   mood='tense', amb='room', sfx=[(2.0, 'bark', 0.6), (2.4, 'bark', 0.6), (3.0, 'bark', 0.6)]))
    amb_yard = S.yard('rain')
    sh.append(Shot(9, amb_yard, ((90, 90), (130, 90), 1), draw=vehicle('ambulance', lambda t: 120, FOOT + 4),
                   actors=[put(DAD('stand', 'silhouette'), 96, Y_DAD), put(D('bolt', 'sit'), 70, Y_DOG)],
                   fx=['rain', 'vig', 'sirens'], caps=[say(1, 7, "THE AMBULANCE CAME AT 3:12 AM.")], mood='sad',
                   sfx=[(0.0, 'siren', 0.5), (3.0, 'siren', 0.5), (6.0, 'siren', 0.4)]))
    sh.append(Shot(9, amb_yard, (120, 128, 3), draw=vehicle('ambulance', lambda t: 120, FOOT + 4),
                   actors=[put(M('stand', True), 110, Y_STAND), put(D('bolt', 'sit'), 82, Y_DOG)],
                   fx=['rain', 'vig', 'sirens'], caps=[say(0.8, 4, "WAIT FOR ME, BOLT.", 'mira'), say(5, 4, "PROMISE?", 'mira')], mood='sad'))
    sh.append(Shot(8, amb_yard, ((120, 90), (160, 90), 1), draw=vehicle('ambulance', lambda t: lerp(120, 460, smooth(seg(t, 1, 7))), FOOT + 4),
                   actors=[put(D('bolt', 'sit'), 82, Y_DOG)], fx=['rain', 'vig'], mood='sad', sfx=[(1, 'engine', 0.5), (1.5, 'siren', 0.3)]))
    door_watch = lambda snow_, lamp: S.living(outside='night', snow=snow_, lamp=lamp)
    sh.append(Shot(8, door_watch(False, True), (170, 110, 2), actors=[put(D('bolt', 'sit'), 182, Y_DOG, flip=True)], hud=counter(lambda t: "DAY 1"),
                   fx=['vig', ('fadein', 0.5)], caps=[say(1, 6.5, "SHE SAID: WAIT FOR ME.")], mood='sad', amb='room'))
    days = [2, 3, 5, 7, 9, 12, 14]
    sh.append(Shot(14, lambda t: door_watch(t > 6, True), (170, 110, 2),
                   actors=[put(D('bolt', 'sit'), 182, Y_DOG, flip=True),
                           Act(lambda t: [(DAD('walk' if int(t * 6) % 2 else 'stand'), lerp(100, 150, seg(t, 3, 5)), Y_DAD, False)] if 3 < t < 5 else [])],
                   draw=window_snow(30, 40, 60, 54) if False else None,
                   hud=counter(lambda t: f"DAY {days[min(int(t / 2), len(days) - 1)]}"), fx=['vig'],
                   caps=[say(0.5, 5, "SO HE WAITED."), say(6, 7.5, "DAD STAYED AT THE HOSPITAL\nMOST NIGHTS.")], mood='sad', amb='room',
                   sfx=[(i * 2, 'tick', 0.4) for i in range(7)]))
    sh.append(Shot(11, door_watch(True, True), (176, 124, 3), actors=[put(DAD('stand'), 150, Y_DAD), put(D('bolt', 'sit'), 182, Y_DOG, flip=True)],
                   draw=late(lambda w, t: rect(w, 162, 128, 165, 133, (180, 230, 255)) if 1 < t < 10 else None), fx=['vig'],
                   caps=[say(0.5, 3.5, "SHE SENT YOU A MESSAGE, BUDDY.", 'dad'), say(4.4, 6.4, "HI BOLT. I'M OKAY.\nKEEP WAITING FOR ME.", 'mira')],
                   mood='sad', amb='room'))
    sh.append(eye_shot(7, [(0.5, "BATTERY: 12%", 'hudred'), (2.0, "CHARGER: OFFLINE"), (3.6, "CAUSE: STORM")], boot=(1, 1), mood='sad'))
    days2 = [21, 26, 30, 34, 38, 40]
    sh.append(Shot(12, door_watch(True, False), (170, 116, 2), actors=[put(D('bolt', 'sleep'), 178, Y_SLEEP)],
                   hud=counter(lambda t: f"DAY {days2[min(int(t / 1.6), len(days2) - 1)]}"), fx=['vig', 'night', ('tint', (0.6, 0.7, 1.3), 0.3)],
                   caps=[say(1, 5, "WEEKS PASSED."), say(6.5, 5.5, "THE POWER NEVER CAME BACK.")], mood='sad', amb='snow'))
    sh.append(eye_shot(7, [(0.5, "BATTERY: 3%", 'hudred'), (2.2, "ENOUGH FOR ONE TRIP.")], boot=(0.6, 0.6), red=0.6, mood='sad',
                       sfx=[(0.5, 'alarm', 0.4)]))
    sh.append(Shot(10, lambda t: S.living(door=round(smooth(seg(t, 3, 5)) * 10) / 10, outside='night', snow=True, lamp=False), (168, 108, 2),
                   actors=[Act(lambda t: [(D('bolt', 'sleep') if t < 1.5 else D('bolt', 'ABCB'[int(t * 6) % 4] if 5 < t < 9 else 'A'),
                                           lerp(178, 140, seg(t, 5, 9)) if t > 5 else 178, Y_SLEEP if t < 1.5 else Y_DOG, True)])],
                   fx=['vig', 'night'], caps=[say(1.5, 3, "HE STOPPED WAITING.")], mood='sad', amb='snow', sfx=[(1.4, 'servo', 0.4), (3, 'door', 0.6)]))
    snowy = S.yard('snow', door=1.0)
    sh.append(Shot(11, snowy, ((80, 90), (220, 90), 1), actors=[move(walk(), (40, Y_DOG), (300, Y_DOG), 0.5, 10.5)],
                   draw=footprints(40, 300, FOOT, 0.5, 10.5), fx=['snow', 'vig'],
                   caps=[say(1, 4, "INTO THE SNOW."), say(5.5, 5, "HE WENT TO FIND HER.")], mood='sad', amb='snow',
                   sfx=[(t, 'snowstep', 0.3) for t in np.arange(0.5, 10.5, 0.25)]))
    sh.append(comment_card("WOULD YOU HAVE\nKEPT WAITING?", mood='sad'))
    return Chapter('03_waiting', sh)


# ======================================================================== CHAPTER 4
def ch4():
    sh = [chapter_card(4, "THE CITY", mood='mystery')]
    cty = S.city()
    sh.append(Shot(13, cty, ((160, 90), (520, 90), 1, False), actors=[move(walk(), (100, Y_DOG), (520, Y_DOG), 0, 13)],
                   fx=['snow', 'vig', ('fadein', 0.8)], caps=[say(1, 5, "THE HOSPITAL WAS ACROSS THE CITY."), say(6.5, 5.5, "FOUR KILOMETERS.")],
                   mood='mystery', amb='city', sfx=[(t, 'snowstep', 0.25) for t in np.arange(0, 13, 0.25)]))
    sh.append(Shot(9, cty, ((250, 120), (290, 120), 2), actors=[move(lambda t: D('bolt', 'ABCB'[int(t * 5) % 4]), (230, Y_DOG), (300, Y_DOG), 0, 9)],
                   fx=['snow', 'snow', 'vig', ('tint', (0.7, 0.85, 1.4), 0.25)],
                   caps=[say(0.8, 4, "IT WAS FOURTEEN BELOW ZERO."), say(5.2, 3.8, "HIS MOTORS STARTED TO FREEZE.")], mood='mystery', amb='snow',
                   sfx=[(t, 'snowstep', 0.25) for t in np.arange(0, 9, 0.4)]))
    sh.append(eye_shot(6, [(0.4, "OUTSIDE: -14 C"), (1.8, "MOTORS: 61%", 'hudred'), (3.4, "KEEP WALKING.")], boot=(1, 1), mood='mystery'))
    sh.append(Shot(9, cty, ((430, 60), (430, 126), 2), actors=[put(D('bolt', 'sit'), 420, Y_DOG)], fx=['snow', 'vig'], nofloor=True,
                   caps=[say(0.8, 4, "NEXA K-9."), say(5, 4, "NEVER LOSE A FRIEND AGAIN.")], mood='mystery', amb='city'))
    sh.append(eye_shot(8, [(0.4, "HOSPITAL: 3.1 KM"), (1.8, "BATTERY: 2%", 'hudred'), (3.2, "RANGE: 0.6 KM", 'hudred'),
                           (4.8, "CANNOT REACH HER.", 'hudred')], boot=(1, 1), red=lambda t: seg(t, 4.8, 5.2), mood='tense',
                       sfx=[(4.8, 'alarm', 0.5)]))
    mk = S.market()
    def collapse(t):
        if t < 4:
            return [(D('bolt', 'ABCB'[int(t * 4) % 4]), lerp(40, 140, seg(t, 0, 4)), Y_DOG + (1 if int(t * 3) % 2 else 0), False)]
        return [(D('bolt', 'sleep', 'off' if t > 5 else 'red'), 136, Y_SLEEP, False)]
    sh.append(Shot(9, mk, (130, 112, 2), actors=[Act(collapse)], fx=['snow', 'vig', ('fadein', 0.5)],
                   caps=[say(5.5, 3.5, "HIS LEGS STOPPED WORKING.")], mood='tense', amb='city', sfx=[(4.0, 'powerdown', 0.6), (4.2, 'thud', 0.4)]))
    sh.append(Shot(11, mk, (170, 112, 2), actors=[move(cast.DEALER, (200, FOOT - 41), (180, FOOT - 41), 0, 1.5), put(D('bolt', 'sleep', 'off'), 136, Y_SLEEP)],
                   fx=['vig'], caps=[say(1.5, 4, "WELL, WELL. A NEXA UNIT.", 'dealer'), say(6, 5, "NEED SOME POWER,\nLITTLE MACHINE?", 'dealer')],
                   mood='tense', amb='city'))
    sh.append(Shot(10, mk, (190, 104, 3), actors=[put(cast.DEALER, 180, FOOT - 41)], fx=['vig'],
                   caps=[say(0.5, 4, "POWER COSTS MEMORIES.", 'dealer'), say(5, 5, "THREE FILES. YOU CHOOSE.", 'dealer')], mood='tense', amb='city'))

    def file_list(s, t):
        items = ["FETCH_2019.MEM", "RAIN_NIGHT.MEM", "FIRST_HUG.MEM", "MIRA_LAUGH.MEM"]
        sel = [False, t > 3.0, t > 4.5, t > 6.0]
        cur = 0 if t < 3 else 1 if t < 4.5 else 2 if t < 6 else 3
        for i, it in enumerate(items):
            y = 58 + i * 18
            col = (255, 72, 84) if (i > 0 and sel[i]) else (96, 236, 255)
            if i == 0 and t > 1.5:
                col = (96, 236, 255)
            draw_text(s, ("[X] " if (i > 0 and sel[i]) else "[ ] ") + it, 50, y, col, align='left')
            if i == cur:
                draw_text(s, ">", 40, y, (255, 214, 90), align='left')
        if t > 7.0:
            draw_text(s, "CONFIRM DELETE? YES", 160, 138, (255, 72, 84))
    sh.append(screen_shot(9, [], title="SELECT 3 FILES TO DELETE", red_box=True, mood='tense', extra=file_list,
                          sfx=[(3.0, 'hud', 0.6), (4.5, 'hud', 0.6), (6.0, 'hud', 0.6), (7.0, 'alarm', 0.4)]))
    def deleted(scr, t):
        if t > 2.6:
            rect(scr, 90, 74, 230, 104, (214, 52, 62))
            draw_text(scr, "DELETED", 160, 82, (250, 250, 250), scale=2, outline=None)
    rainy = S.yard('rain')
    sh.append(Shot(4.5, rainy, (240, 128, 3), actors=[put(M('stand'), 216, Y_STAND), put(D('bolt', 'A'), 240, Y_DOG + 4, True)],
                   draw=ball_at(lambda t: (232, FOOT - 1)), hud=deleted, fx=['sepia', ('glitch', 2.0, 4.5, 0.6), 'vig'],
                   caps=[say(0.3, 2.4, "RAIN_NIGHT.MEM")], mood='sad', amb='none', sfx=[(2.6, 'delete', 0.7)]))
    sh.append(Shot(4.5, S.yard('rain'), (200, 140, 4), draw=draws(peek_bolt(186, FOOT, -1, 0, 0), crate(186, FOOT, open_t=-1)),
                   actors=[put(M('kneel'), 166, FOOT - 18)], hud=deleted, fx=['sepia', ('glitch', 2.0, 4.5, 0.6), 'vig'],
                   caps=[say(0.3, 2.4, "FIRST_HUG.MEM")], mood='sad', amb='none', sfx=[(2.6, 'delete', 0.7)]))
    sh.append(Shot(4.5, S.yard('day'), (176, 128, 3), actors=[put(M('kneel'), 166, FOOT - 18), spin('bolt', 190, Y_DOG, 0, 3)], hud=deleted,
                   fx=['sepia', ('glitch', 2.0, 4.5, 0.6), 'vig'], caps=[say(0.3, 2.4, "MIRA_LAUGH.MEM")], mood='sad', amb='none',
                   sfx=[(2.6, 'delete', 0.7)]))
    sh.append(eye_shot(6, [(0.4, "3 FILES ERASED", 'hudred'), (2.0, "BATTERY: 100%", 'hudgreen')], boot=(0.2, 1.0), mood='mystery',
                       sfx=[(1.8, 'powerup', 0.5)]))
    sh.append(Shot(7, mk, (190, 104, 3), actors=[put(cast.DEALER, 180, FOOT - 41)], fx=['vig'],
                   caps=[say(0.6, 3, "PLEASURE DOING BUSINESS.", 'dealer'), say(4, 3, "HE NEVER FOUND OUT WHAT HE GAVE AWAY.")], mood='mystery', amb='city'))
    sh.append(Shot(12, cty, lambda t: (lerp(120, 600, seg(t, 0, 12)), 120, 2), actors=[move(run(), (100, Y_DOG), (620, Y_DOG), 0, 12)],
                   fx=['snow', 'vig'], caps=[say(1, 4.5, "AND THEN HE RAN.")], mood='chase', amb='city',
                   sfx=[(t, 'paw', 0.15) for t in np.arange(0, 12, 0.125)]))
    sh.append(comment_card("WHICH MEMORY WOULD YOU\nNEVER GIVE UP?", mood='mystery'))
    return Chapter('04_the_city', sh)


# ======================================================================== CHAPTER 5
def ch5():
    sh = [chapter_card(5, "UNKNOWN USER", mood='mystery')]
    sh.append(Shot(11, lambda t: S.hospital_ext(door=round(smooth(seg(t, 5, 6)) * 10) / 10 if t < 9 else 0.0), (210, 90, 1),
                   actors=[Act(lambda t: [(D('bolt', 'ABCB'[int(t * 12) % 4] if t < 3 or 6 < t < 8 else 'sit' if 3 <= t <= 6 else 'A'),
                                           lerp(20, 200, seg(t, 0, 3)) if t < 6 else lerp(200, 236, seg(t, 6, 8)), Y_DOG, False)] if t < 8 else [])],
                   fx=['snow', 'vig', ('fadein', 0.6)], caps=[say(1, 4.5, "HE FOUND THE HOSPITAL AT 4 AM."), say(6, 4.5, "SOMEONE OPENED THE DOOR.")],
                   mood='mystery', amb='snow', sfx=[(5, 'door', 0.4)]))
    room = S.hospital_room()
    sh.append(Shot(9, room, (160, 90, 1), actors=[put(cast.MIRA_BED_HEAD, 76, 104)], draw=draws(ecg(), window_snow(230, 30, 60, 50)), fx=['vig', 'night'],
                   caps=[say(1, 7, "ROOM 214.")], mood=None, amb='room', sfx=[(t, 'beep', 0.35) for t in np.arange(0.4, 9, 0.85)]))
    sh.append(Shot(9, lambda t: S.hospital_room(door=1.0 if 0.5 < t < 3.5 else 0.0), (120, 100, 1),
                   actors=[put(cast.MIRA_BED_HEAD, 76, 104),
                           Act(lambda t: [(D('bolt', 'ABCB'[int(t * 8) % 4] if t < 6 else 'A'), lerp(10, 150, seg(t, 1, 6)), Y_DOG, False)] if t < 6.5 else []),
                           Act(lambda t: [(D('bolt', 'B'), lerp(150, 140, seg(t, 6.5, 7.1)), lerp(Y_DOG, 100, seg(t, 6.5, 7.1)) - 10 * np.sin(np.pi * seg(t, 6.5, 7.1)), False)] if 6.5 <= t < 7.1 else []),
                           Act(lambda t: [(D('bolt', 'sleep'), 140, 102, False)] if t >= 7.1 else [])],
                   draw=ecg(), fx=['vig', 'night'], caps=[Cap(2.5, 6, "VISITOR DETECTED", 'hud', pos=(12, 12))], mood=None, amb='room',
                   sfx=[(t, 'beep', 0.3) for t in np.arange(0.4, 9, 0.85)] + [(0.5, 'door', 0.4), (7.1, 'thud', 0.2)]))
    sh.append(Shot(8, room, (92, 106, 6), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sleep'), 140, 102)], fx=['vig', 'night'],
                   caps=[say(1, 3, "...BOLT?", 'mira'), say(4.2, 3.8, "YOU CAME! YOU FOUND ME!", 'mira')], mood='tender', amb='room',
                   sfx=[(t, 'beep', 0.25) for t in np.arange(0.4, 8, 0.7)]))
    sh.append(Shot(7, room, (84, 104, 6), actors=[put(cast.MIRA_BED_HEAD, 76, 104)], hud=lambda scr, t: pov(scr, t, red=t > 2.5),
                   caps=[Cap(0.4, 7, "FACE SCAN...", 'hud', pos=(14, 22)), Cap(2.5, 7, "UNKNOWN USER.", 'hudred', pos=(14, 34))],
                   fx=[('glitch', 2.5, 4, 0.7)], mood='tense', amb='room', sfx=[(2.5, 'glitch', 0.5)]))
    tilt = Act(lambda t: [(D('bolt', 'sit'), 138, 98, int(t * 1.5) % 2 == 1)])
    sh.append(Shot(8, room, (120, 106, 3), actors=[put(cast.MIRA_BED_HEAD, 76, 104), tilt], fx=['vig', 'night'],
                   caps=[say(0.8, 3, "IT'S ME. MIRA.", 'mira'), say(4.2, 3.8, "...BOLT?", 'mira')], mood='sad', amb='room'))
    sh.append(eye_shot(6, [(0.4, "SEARCHING MEMORY..."), (2.4, "NO MATCHING FILES.", 'hudred')], boot=(1, 1), mood='sad'))
    sh.append(Shot(7, room, (110, 104, 2), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sit'), 138, 98)], fx=['vig', 'night'],
                   caps=[say(1, 5.5, "HE DIDN'T REMEMBER HER.")], mood='sad', amb='room'))
    roll = lambda t: (lerp(100, 134, seg(t, 3, 5)), 108) if t > 3 else (100, 108)
    sh.append(Shot(10, room, (118, 104, 3), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sit'), 138, 98)], draw=ball_at(roll),
                   fx=['vig', 'night'], caps=[say(0.6, 2.4, "WAIT.", 'mira'), say(3.2, 6.5, "DO YOU REMEMBER THIS?", 'mira')], mood='sad', amb='room',
                   sfx=[(3, 'bounce', 0.2)]))
    def search_bar(s, t):
        bar(s, 60, 110, 200, 0.12 * smooth(seg(t, 1.0, 4.5)), (255, 214, 90), f"{int(12 * smooth(seg(t, 1, 4.5)))}%")
    sh.append(screen_shot(7, [(0.3, "SEARCHING: RED_BALL"), (4.6, "PARTIAL MATCH FOUND", 'hudgreen')], title="MEMORY RECOVERY", mood='tender',
                          extra=search_bar, sfx=[(4.6, 'chirp', 0.4)]))
    back = lambda t: (lerp(134, 100, seg(t, 1, 3)), 108) if t > 1 else (134, 108)
    sh.append(Shot(11, room, (118, 104, 3), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sit'), 138, 98)], draw=ball_at(back),
                   fx=['vig', 'night'], caps=[say(3.4, 3, "IT'S OKAY.", 'mira'), say(6.6, 4.4, "I'LL TEACH YOU AGAIN.\nEVERYTHING.", 'mira')],
                   mood='tender', amb='room', sfx=[(1, 'servo', 0.2)]))
    sh.append(Shot(8, room, (118, 106, 3), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sleep'), 104, 104)], fx=['vig', 'night'],
                   caps=[Cap(1.2, 8, "NEW FILE CREATED:", 'hud', pos=(12, 12)), Cap(2.4, 8, "MIRA_02.MEM", 'hudgreen', pos=(12, 24))],
                   mood='tender', amb='room', sfx=[(2.4, 'ding', 0.3)]))
    sh.append(Shot(9, lambda t: S.hospital_room(door=1.0), (90, 100, 2),
                   actors=[move(dad_walk(), (0, Y_DAD), (34, Y_DAD), 0, 2), put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sit'), 138, 98)],
                   fx=['vig'], caps=[say(2.4, 4, "HOW DID HE GET HERE?!", 'dad'), say(6.6, 2.4, "HE WALKED.", 'mira')], mood='tender', amb='room',
                   sfx=[(0, 'door', 0.4)] + [(t, 'step', 0.3) for t in np.arange(0, 2, 0.33)]))
    sh.append(Shot(8, room, (140, 100, 2), actors=[put(cast.MIRA_BED_HEAD, 76, 104), put(D('bolt', 'sleep'), 140, 102), put(DAD('stand'), 34, Y_DAD)],
                   hud=lambda scr, t: subscribe(scr, t - 3) if 3 <= t < 8 else None, fx=['vig', ('fadeout', 0.6)],
                   caps=[say(0.5, 7, "FOUR KILOMETERS. IN THE SNOW.\nON 3% BATTERY.")], mood='tender', amb='room'))
    sh.append(comment_card("WHAT WOULD YOU\nTEACH HIM FIRST?", mood='tender'))
    return Chapter('05_unknown_user', sh)


# ======================================================================== CHAPTER 6
def ch6():
    sh = [chapter_card(6, "HEARTBEAT: NONE", mood='tender')]
    liv = S.living(outside='day')
    sh.append(Shot(10, S.yard('day'), (200, 120, 2), actors=[put(M('stand'), 170, Y_STAND), spin('bolt', 200, Y_DOG, 5, 8)],
                   hud=counter(lambda t: "LESSON 14"), fx=['vig'],
                   caps=[say(0.5, 4.5, "SHE TAUGHT HIM EVERYTHING AGAIN."), say(5.2, 4.8, "FETCH. SIT. AND THE SPIN.")],
                   mood='tender', amb='none', sfx=[(5.2, 'servo', 0.3), (6.2, 'bark', 0.4)]))
    sh.append(Shot(10, liv, (220, 116, 2), actors=[put(DAD('stand'), 186, Y_DAD), put(M('stand', True), 236, Y_STAND), put(D('bolt', 'sit'), 254, Y_DOG)],
                   fx=['vig', ('fadein', 0.6)], caps=[say(0.5, 3.5, "TWO WEEKS LATER, SHE CAME HOME."),
                                                      say(4.4, 5.6, "I HAVE A NIGHT SHIFT.\nLOCK THE DOOR, OKAY?", 'dad')], mood='tender', amb='room'))
    sh.append(Shot(7, lambda t: S.living(outside='day', door=1.0 if 2 < t < 5 else 0.0), (180, 110, 2),
                   actors=[Act(lambda t: [(DAD('walk' if int(t * 6) % 2 else 'stand'), lerp(186, 156, seg(t, 0, 3)), Y_DAD, True)] if t < 3.5 else [])],
                   fx=['vig'], mood='tender', amb='room', sfx=[(2, 'door', 0.5), (5, 'door', 0.5)] + [(t, 'step', 0.3) for t in np.arange(0, 3, 0.33)]))
    night = S.living(outside='night')
    sh.append(Shot(8, night, (230, 120, 2), actors=[put(M('sit', True), 228, Y_SIT), put(D('bolt', 'sleep'), 250, Y_SLEEP)],
                   draw=wall_clock(250, 40, lambda t: "23:47"), fx=['vig', 'night', ('fadein', 0.8)],
                   caps=[say(1, 6, "THAT NIGHT...")], mood='mystery', amb='room'))
    sh.append(Shot(7, night, (220, 120, 2), actors=[put(M('sit', True), 228, Y_SIT), put(lambda t: D('bolt', 'sleep') if t < 1.5 else D('bolt', 'A', 'red'), 250, lambda_y3 := Y_DOG)],
                   fx=['vig', 'night'], caps=[Cap(2.4, 7, "MOTION DETECTED: FRONT DOOR", 'hudred', pos=(12, 12))], mood='tense', amb='room',
                   sfx=[(0.6, 'doorbell', 0.7), (2.4, 'growl', 0.6)]))
    sh[-1].actors[1] = Act(lambda t: [(D('bolt', 'sleep'), 250, Y_SLEEP, True)] if t < 1.5 else [(D('bolt', 'A', 'red'), 240, Y_DOG, True)])
    opened = lambda t: S.living(outside='night', door=1.0)
    sh.append(Shot(9, opened, (172, 110, 2), actors=[put(DAD('stand', 'fake'), 156, Y_DAD), put(M('stand', True), 190, Y_STAND)],
                   fx=['vig', 'night', 'rain'], caps=[say(1, 3.5, "HI, SWEETHEART.", 'fake'), say(4.8, 4.2, "I CAME HOME EARLY.", 'fake')],
                   mood='tense', amb='rain', sfx=[(0, 'door', 0.5)]))
    sh.append(Shot(8, opened, (166, 104, 4), actors=[put(DAD('stand', 'fake'), 156, Y_DAD)], hud=lambda scr, t: pov(scr, t, red=True),
                   caps=[Cap(0.4, 8, "HEARTBEAT: NONE", 'hudred', pos=(14, 22)), Cap(2.0, 8, "BODY TEMP: 12 C", 'hudred', pos=(14, 34)),
                         Cap(3.8, 8, "THIS IS NOT DAD.", 'hudred', pos=(14, 50))], mood='tense', amb='rain', sfx=[(3.8, 'growl', 0.6)]))
    sh.append(Shot(6, opened, (164, 124, 3), actors=[put(DAD('stand', 'fake'), 156, Y_DAD), put(D('bolt', 'A', 'red'), 180, Y_DOG, True)],
                   fx=['vig', 'night', ('glitch', 3, 4, 0.5)], caps=[say(1, 4, "MOVE, DOG.", 'fake')], mood='tense', amb='rain',
                   sfx=[(3, 'glitch', 0.4)]))
    sh.append(Shot(7, opened, (196, 120, 3), actors=[put(M('stand', True), 190, Y_STAND)],
                   draw=late(lambda w, t: rect(w, 200, 136, 204, 142, (180, 230, 255) if int(t * 4) % 2 else (90, 120, 140))),
                   caps=[Cap(0.8, 7, "INCOMING CALL: DAD", 'hud', pos=(12, 12))], fx=['vig', 'night'], mood='tense', amb='rain',
                   sfx=[(0.5, 'phone', 0.6), (2.5, 'phone', 0.6)]))
    sh.append(Shot(11, opened, (196, 120, 3), actors=[put(M('stand', True), 190, Y_STAND)], fx=['vig', 'night'],
                   caps=[say(0.5, 5, "MIRA? I'M STILL AT WORK.\nWHY IS THE DOOR OPEN?", 'dad'), say(6, 5, "...THEN WHO IS STANDING\nIN OUR HOUSE?", 'mira')],
                   mood='tense', amb='rain'))
    sh.append(Shot(12, opened, (160, 104, 4), actors=[put(lambda t: DAD('stand', 'fake' if t < 1.5 else 'android'), 156, Y_DAD)],
                   fx=['vig', 'night', ('glitch', 0.8, 2.2, 0.9)],
                   caps=[say(2.4, 3, "NEXA RECOVERY UNIT 7.", 'fake'), say(5.6, 3.2, "K-9 #0002 CONTAINS\nSTOLEN DATA.", 'fake'),
                         say(9, 3, "HAND OVER THE UNIT.", 'fake')], mood='glitch', amb='rain', sfx=[(0.8, 'glitch', 0.7)]))
    leap = Act(lambda t: [(D('bolt', 'B', 'red'), lerp(200, 166, seg(t, 0.5, 1.2)), lerp(Y_DOG, Y_DAD + 6, seg(t, 0.5, 1.2)) - 10 * np.sin(np.pi * seg(t, 0.5, 1.2)), True)])
    sh.append(Shot(6, opened, (176, 116, 2), actors=[put(DAD('stand', 'android'), 156, Y_DAD), leap, put(M('stand', True), 206, Y_STAND)],
                   fx=['vig', 'night', ('shake', 1.2, 2, 3), ('flash', 1.2, 0.2)], caps=[say(2.4, 3.4, "MIRA, RUN!!", 'unit')],
                   mood='chase', amb='rain', sfx=[(0.5, 'growl', 0.5), (1.2, 'crash', 0.8), (2.2, 'bark', 0.6)]))
    ry = S.yard('rain', door=1.0)
    chase = [move(mira_walk(True), (40, Y_STAND), (260, Y_STAND), 0, 4.5), move(run(eye='red'), (20, Y_DOG), (200, Y_DOG), 0.6, 4.0),
             move(dad_walk('android'), (20, Y_DAD), (190, Y_DAD), 1.5, 9)]
    sh.append(Shot(9, ry, ((90, 90), (200, 90), 1), actors=chase, draw=lightning(5, 160), fx=['rain', 'vig', ('flash', 5, 0.3)],
                   mood='chase', sfx=[(5.1, 'thunder', 0.7)] + [(t, 'step', 0.3) for t in np.arange(0, 4.5, 0.2)]))
    def grabbed(t):
        if t < 2:
            return [(DAD('stand', 'android'), 190, Y_DAD, False), (D('bolt', 'A', 'red'), 204, Y_DOG, False)]
        return [(DAD('stand', 'android'), 190, Y_DAD, False), (D('bolt', 'B', 'off'), 196, Y_DAD + 10, False)]
    sh.append(Shot(8, ry, (204, 124, 3), actors=[Act(grabbed)], fx=['rain', 'vig', ('flash', 2, 0.15)],
                   caps=[Cap(2.6, 8, "SIGNAL LOST", 'hudred', pos=(12, 12))], mood='chase', sfx=[(2, 'zap', 0.8), (2.2, 'powerdown', 0.5)]))
    sh.append(Shot(10, ry, ((200, 90), (300, 90), 1), draw=vehicle('van', lambda t: lerp(230, 480, smooth(seg(t, 2, 9))), FOOT + 4, lights=True),
                   actors=[move(mira_walk(True), (180, Y_STAND), (250, Y_STAND), 1, 6)], fx=['rain', 'vig'],
                   caps=[Cap(3, 10, "BOLT!!!", 'big', pos=(0, 24))], mood='chase', sfx=[(1.5, 'engine', 0.7)]))
    sh.append(Shot(8, ry, (258, 128, 3), actors=[put(M('kneel', True), 252, FOOT - 18)], fx=['rain', 'vig', ('fadeout', 1)],
                   mood='sad', caps=[say(2, 5, "THE VAN WAS GONE.")]))
    sh.append(comment_card("WHAT IS THE\n\"STOLEN DATA\"?\nGUESS BELOW", mood='mystery'))
    return Chapter('06_heartbeat_none', sh)


# ======================================================================== CHAPTER 7
def ch7():
    sh = [chapter_card(7, "LAST FREQUENCY", mood='mystery')]
    liv = S.living(outside='night', lamp=True)
    two = lambda: [put(DAD('stand'), 200, Y_DAD), put(M('stand', True), 236, Y_STAND, flip=True)]
    lines = [("IT'S MY FAULT.", 'dad'), ("BOLT WORE A COLLAR CAMERA\nFOR NINE YEARS.", 'dad'),
             ("WHEN HE DIED, I SENT\nALL THE VIDEO TO NEXA.", 'dad'), ("I WANTED A ROBOT THAT\nWOULD MAKE YOU SMILE AGAIN.", 'dad'),
             ("THEY TURNED HIM INTO\nA MEMORY FILE.", 'dad'), ("THAT FILE WAS NEVER MEANT\nTO LEAVE THEIR LAB.", 'dad')]
    for i, (txt, who) in enumerate(lines):
        cam = (206, 112, 4) if i % 2 == 0 else (220, 118, 2)
        sh.append(Shot(5.5, liv, cam, actors=two(), fx=['vig', 'night'] + ([('fadein', 0.6)] if i == 0 else []),
                       caps=[say(0.4, 5, txt, who)], mood='mystery', amb='room'))
    sh.append(Shot(10, liv, (232, 112, 4), actors=two(), fx=['vig', 'night'],
                   caps=[say(0.4, 4, "THEN WHY DID THEY SEND IT TO US?", 'mira'), say(5, 5, "...THEY DIDN'T.\nSOMEONE INSIDE NEXA DID.", 'dad')],
                   mood='mystery', amb='room'))
    bed = S.bedroom()
    def rad(w, t):
        cast.radio(w, 148, 119, glow=1.0 if t > 2 else 0.0)
    sh.append(Shot(9, bed, (150, 104, 2), actors=[put(cast.MIRA_BED_HEAD, 46, 108)], draw=rad, fx=['vig', ('fadein', 0.6)],
                   caps=[say(1, 7, "THAT NIGHT, THE OLD RADIO\nTURNED ON BY ITSELF.")], mood=None, amb='room', sfx=[(2, 'static', 0.6), (4, 'static', 0.5)]))
    sh.append(Shot(8, bed, (158, 112, 8), draw=rad, fx=['vig', ('glitch', 3.5, 4.2, 0.4)],
                   caps=[say(1, 6.5, "...KSSHH... WOOF ... KSSHH...")], mood=None, amb='room',
                   sfx=[(0.5, 'static', 0.6), (3.5, 'bark', 0.4), (3.9, 'bark', 0.3), (5, 'static', 0.5)]))
    sh.append(screen_shot(7, [(0.4, "FREQUENCY: 101.9 MHZ"), (2.0, "SIGNAL: K-9 BEACON", 'hudgreen'), (3.6, "SOURCE: JUNKYARD, 2 KM", 'hudred')],
                          title="LAST FREQUENCY", mood='mystery', sfx=[(3.6, 'chirp', 0.4)]))
    ry = S.yard('rain')
    pair = [move(mira_walk(), (60, Y_STAND), (300, Y_STAND), 0, 9), move(dad_walk('silhouette'), (40, Y_DAD), (280, Y_DAD), 0, 9)]
    sh.append(Shot(10, ry, ((100, 90), (240, 90), 1), actors=pair, draw=flashlight(lambda t: (lerp(60, 300, seg(t, 0, 9)) + 12, 137, 1)),
                   fx=['rain', 'vig'], caps=[say(1, 6, "THEY WENT THAT SAME NIGHT.")], mood='mystery',
                   sfx=[(t, 'step', 0.25) for t in np.arange(0, 9, 0.33)]))
    jy = S.junkyard()
    sh.append(Shot(12, jy, ((140, 90), (320, 90), 1, False), actors=[move(mira_walk(), (60, Y_STAND), (220, Y_STAND), 0, 12), move(dad_walk('silhouette'), (40, Y_DAD), (200, Y_DAD), 0, 12)],
                   draw=draws(warning_light(), flashlight(lambda t: (lerp(60, 220, seg(t, 0, 12)) + 12, 137, 1))), fx=['rain', 'vig'],
                   caps=[say(1, 5, "HUNDREDS OF BROKEN ROBOTS."), say(6.5, 5.5, "ALL OF THEM... K-9 UNITS.")], mood='tense', amb='junk'))
    sh.append(Shot(8, jy, (290, 140, 3), draw=draws(warning_light(), flashlight(lambda t: (250, 137, 1), length=90)), fx=['rain', 'vig'],
                   caps=[say(0.5, 7, "NEXA HAD BUILT FORTY COPIES OF BOLT.")], mood='tense', amb='junk'))
    sh.append(Shot(7, jy, (290, 140, 3), draw=draws(warning_light(), flashlight(lambda t: (250, 137, 1), length=90)), fx=['rain', 'vig'],
                   caps=[say(0.5, 6, "ONLY ONE OF THEM HAD EVER WORKED.")], mood='tense', amb='junk'))
    u01 = lambda t: D('unit01', 'sleep', 'red' if (t > 1.5 and int(t * 4) % 2) else 'off') if t < 4 else D('unit01', 'A', 'red')
    sh.append(Shot(9, jy, (300, 136, 3), actors=[Act(lambda t: [(u01(t), 290, Y_SLEEP if t < 4 else Y_DOG, True)])],
                   draw=warning_light(), fx=['rain', 'vig', ('shake', 4, 4.4, 2)], mood='tense', amb='junk',
                   sfx=[(1.5, 'servo', 0.4), (4, 'impact', 0.6), (4.2, 'growl', 0.5)]))
    sh.append(Shot(8, jy, (270, 128, 2), actors=[put(D('unit01', 'A', 'red'), 290, Y_DOG, True), put(DAD('stand', 'silhouette'), 236, Y_DAD),
                                                put(M('stand'), 220, Y_STAND)],
                   draw=warning_light(), fx=['rain', 'vig'], caps=[say(0.6, 4, "MIRA, GET BEHIND ME!", 'dad')], mood='tense', amb='junk'))
    sh.append(Shot(10, jy, (300, 136, 4), actors=[put(D('unit01', 'A', 'red'), 290, Y_DOG, True)], draw=draws(warning_light(), photo_in_chest(302, Y_DOG + 9, 1.5)),
                   fx=['rain', 'vig'], caps=[say(3, 6.5, "I... REMEMBER HER TOO.", 'unit')], mood='mystery', amb='junk', sfx=[(1.5, 'servo', 0.4)]))
    sh.append(Shot(11, jy, (290, 130, 3), actors=[put(D('unit01', 'A', 'red'), 290, Y_DOG, True)], draw=warning_light(), fx=['rain', 'vig'],
                   caps=[say(0.5, 4.5, "I AM UNIT 01. THE FIRST COPY.", 'unit'), say(5.4, 5.6, "THEY THREW ME AWAY.\nI KEPT HIS MEMORIES SAFE.", 'unit')],
                   mood='mystery', amb='junk'))
    sh.append(Shot(7, jy, (290, 130, 3), actors=[put(D('unit01', 'A', 'red'), 290, Y_DOG, True)], draw=warning_light(), fx=['rain', 'vig'],
                   caps=[say(0.5, 6, "YOUR BOLT IS HERE.\nHE IS DYING.", 'unit')], mood='tense', amb='junk'))
    sh.append(Shot(8, jy, (240, 136, 3), actors=[put(D('bolt', 'sleep', 'off'), 246, Y_SLEEP), move(mira_walk(), (190, Y_STAND), (222, Y_STAND), 0, 2)],
                   draw=warning_light(), fx=['rain', 'vig'], caps=[say(2, 4, "BOLT!!", 'mira')], mood='tense', amb='junk'))
    sh.append(comment_card("CAN UNIT 01\nSAVE HIM?\nYES OR NO?", mood='tense'))
    return Chapter('07_last_frequency', sh)


# ======================================================================== CHAPTER 8
def ch8():
    sh = [chapter_card(8, "GOOD BOY", mood='sad')]
    jy = S.junkyard()
    base = lambda: [put(D('bolt', 'sleep', 'off'), 246, Y_SLEEP), put(M('kneel'), 226, FOOT - 18)]
    sh.append(Shot(11, jy, (240, 136, 4), actors=base(), draw=warning_light(), fx=['rain', 'vig', ('fadein', 0.6)],
                   caps=[say(0.6, 4.5, "YOU DON'T REMEMBER ME.", 'mira'), say(5.6, 5.4, "THAT'S OKAY.\nI REMEMBER YOU.", 'mira')], mood='sad', amb='junk'))
    sh.append(eye_shot(6, [(0.3, "BATTERY: 1%", 'hudred'), (1.6, "SHUTDOWN IN 00:20", 'hudred')], boot=(0.3, 0.3), red=1.0, mood='sad',
                       sfx=[(0.3, 'alarm', 0.4)]))
    cast3 = lambda: base() + [put(D('unit01', 'A', 'red'), 276, Y_DOG, True), put(DAD('stand', 'silhouette'), 200, Y_DAD)]
    sh.append(Shot(10, jy, (250, 128, 2), actors=cast3(), draw=warning_light(), fx=['rain', 'vig'],
                   caps=[say(0.5, 4.5, "I HAVE ALL OF HIS MEMORIES.", 'unit'), say(5.4, 4.6, "NINE YEARS OF THEM.\nTAKE THEM.", 'unit')], mood='sad', amb='junk'))
    sh.append(Shot(11, jy, (220, 118, 3), actors=cast3(), draw=warning_light(), fx=['rain', 'vig'],
                   caps=[say(0.5, 5, "IF YOU GIVE THEM AWAY...\nWHAT HAPPENS TO YOU?", 'dad'), say(6, 5, "I WILL BE... EMPTY.", 'unit')], mood='sad', amb='junk'))
    sh.append(Shot(8, jy, (276, 130, 4), actors=cast3(), draw=warning_light(), fx=['rain', 'vig'],
                   caps=[say(0.5, 7, "HE WAS A GOOD BOY.\nLET HIM BE ONE AGAIN.", 'unit')], mood='hope', amb='junk'))
    lying = lambda: [put(D('bolt', 'sleep', 'off'), 246, Y_SLEEP), Act(lambda t: [(D('unit01', 'sleep', 'red' if t < 11 else 'off'), 278, Y_SLEEP, True)]),
                     put(M('kneel'), 226, FOOT - 18)]
    def sync_hud(scr, t):
        bar(scr, 90, 24, 140, smooth(seg(t, 2, 11)), (96, 236, 255), f"SYNC {int(100 * smooth(seg(t, 2, 11)))}%")
    sh.append(Shot(13, jy, (262, 132, 3), actors=lying(), hud=sync_hud,
                   draw=draws(warning_light(), cable((270, FOOT - 6), (282, FOOT - 6), 1, 13)), fx=['rain', 'vig'],
                   mood='hope', amb='junk', sfx=[(1, 'zap', 0.5), (2, 'sync', 0.5), (5, 'sync', 0.4), (8, 'sync', 0.4)]))
    mem = [(S.yard('day'), (200, 112, 2), [put(M('stand'), 150, Y_STAND), move(run('old'), (166, Y_DOG), (246, Y_DOG), 0, 2.4)], "FETCH_2019.MEM"),
           (S.yard('rain'), (200, 140, 4), [put(M('kneel'), 166, FOOT - 18)], "FIRST_HUG.MEM"),
           (S.yard('day'), (176, 128, 3), [put(M('kneel'), 166, FOOT - 18), spin('bolt', 190, Y_DOG, 0, 3)], "MIRA_LAUGH.MEM"),
           (S.school(), (196, 120, 2), [put(D('bolt', 'sit'), 206, Y_DOG), put(M('stand'), 186, Y_STAND)], "SCHOOL_GATE.MEM")]
    for wld, cam, acts, label in mem:
        drawhook = draws(peek_bolt(186, FOOT, -1, 0, 0), crate(186, FOOT, open_t=-1)) if label == "FIRST_HUG.MEM" else None
        def restored(scr, t, label=label):
            if t > 1.2:
                rect(scr, 80, 74, 240, 104, (40, 160, 90))
                draw_text(scr, "RESTORED", 160, 82, (250, 250, 250), scale=2, outline=None)
        sh.append(Shot(4, wld, cam, actors=acts, draw=drawhook, hud=restored, fx=['sepia', 'vig', ('glitch', 0, 0.4, 0.6)],
                       caps=[say(0.2, 3.6, label)], mood='hope', amb='none', sfx=[(1.2, 'ding', 0.35)]))
    sh.append(eye_shot(7, [(0.4, "UNIT 01: SHUTDOWN", 'hudred'), (2.6, "THANK YOU.", 'unit')], boot=(1, 0.0), red=1.0, mood='sad',
                       sfx=[(0.4, 'powerdown', 0.6)]))
    sh.append(eye_shot(9, [(1.2, "K-9 UNIT: ONLINE"), (2.8, "USER: MIRA", 'hudgreen'), (4.6, "STATUS: BEST FRIEND", 'hudgreen')],
                       boot=(0, 1), white_t=4.6, mood='hope', sfx=[(0.2, 'boot', 0.5), (4.6, 'ding', 0.4)]))
    sh.append(Shot(10, jy, (236, 132, 3), actors=[Act(lambda t: [(D('bolt', 'sleep'), 246, Y_SLEEP, False)] if t < 1.5 else []),
                                                  spin('bolt', 240, Y_DOG, 1.5, 6), put(lambda t: M('kneel') if t < 6 else M('stand'), 214, lambda_y9 := 0)],
                   draw=warning_light(), fx=['rain', 'vig'], caps=[say(2, 3.5, "HE SPUN IN A CIRCLE.", 'narr'), say(6, 4, "BOLT!!", 'mira')],
                   mood='hope', amb='junk', sfx=[(1.5, 'servo', 0.4), (2.5, 'bark', 0.5), (3.5, 'bark', 0.5)]))
    sh[-1].actors[2] = Act(lambda t: [(M('kneel'), 214, FOOT - 18, False)] if t < 6 else [(M('stand'), 214, Y_STAND, False)])
    sh.append(Shot(6, jy, (230, 128, 3), actors=[put(M('kneel'), 220, FOOT - 18), put(D('bolt', 'sit'), 234, Y_DOG, True)], draw=warning_light(),
                   fx=['rain', 'vig', ('fadeout', 0.8)], caps=[say(0.5, 5, "HE REMEMBERED EVERYTHING.")], mood='hope', amb='junk'))
    dawn = S.yard('dawn')
    sh.append(Shot(12, dawn, ((200, 90), (250, 100), 1), actors=[put(DAD('stand'), 200, Y_DAD), put(M('stand'), 226, Y_STAND), put(D('bolt', 'sit'), 240, Y_DOG)],
                   fx=['vig', ('fadein', 1.0)], caps=[say(1, 5, "THEY BURIED UNIT 01\nNEXT TO THE FIRST BOLT."), say(6.5, 5, "HIS TAG STILL GLOWS AT NIGHT.")],
                   mood='hope', amb='none'))
    sh.append(Shot(8, dawn, (240, 128, 3), actors=[put(M('stand'), 226, Y_STAND), put(D('bolt', 'sit'), 240, Y_DOG)], fx=['vig'],
                   caps=[Cap(1, 8, "SOME GOOD BOYS\nCOME BACK.", 'title', pos=(0, 40))], mood='hope', amb='none'))
    bed = S.bedroom()
    sh.append(Shot(10, bed, (100, 104, 2), actors=[put(cast.MIRA_BED_HEAD, 46, 108), put(D('bolt', 'sleep'), 100, 107)], fx=['vig', ('fadeout', 1.5)],
                   caps=[Cap(2, 10, "GOOD_BOY.EXE  RUNNING", 'hud', pos=(12, 12))], mood='tender', amb='room'))
    sh.append(card(6, "THE END", y=70, mood='tender'))
    sh.append(Shot(9, jy, (150, 140, 4), actors=[put(D('unit01', 'sleep', 'off'), 140, Y_SLEEP)],
                   draw=late(lambda w, t: (rect(w, 145, Y_SLEEP + 3, 147, Y_SLEEP + 4, (255, 64, 76)) if t > 3 else None)),
                   fx=['rain', 'vig', ('fadein', 1.0), ('glitch', 5, 9, 0.5)],
                   caps=[Cap(4, 9, "UNIT 03: ONLINE", 'hudred', pos=(12, 12)), Cap(5.6, 9, "TARGET: MIRA", 'hudred', pos=(12, 24))],
                   mood='tense', amb='junk', sfx=[(3, 'servo', 0.5), (4, 'alarm', 0.5), (5.6, 'glitch', 0.5)]))
    sh.append(comment_card("PART 2?\nCOMMENT \"GOOD BOY\"\nIF YOU WANT IT", mood='tender'))

    sh.insert(len(sh) - 2, card(8, "FOR EVERY GOOD BOY\nWHO EVER WAITED\nAT THE DOOR.", y=48, mood='tender'))
    def endscreen(t):
        s = np.zeros((H, W, 3), np.uint8)
        s[:] = (10, 10, 20)
        for (x0, y0, x1, y1) in ((20, 50, 150, 124), (170, 50, 300, 124)):
            rect(s, x0, y0, x1, y1, (30, 34, 54))
            rect(s, x0 + 1, y0 + 1, x1 - 1, y1 - 1, (16, 18, 30))
        draw_text(s, "WATCH NEXT", 160, 24, (248, 244, 236), scale=2)
        draw_text(s, "THANK YOU FOR WATCHING", 160, 140, GREY)
        draw_text(s, "PIXEL FLOW", 160, 156, (96, 236, 255))
        return s
    sh.append(Shot(20, screen=endscreen, fx=[('fadein', 0.6)], mood='tender', amb='none'))
    return Chapter('08_good_boy', sh)


CHAPTERS = [cold_open, ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8]
