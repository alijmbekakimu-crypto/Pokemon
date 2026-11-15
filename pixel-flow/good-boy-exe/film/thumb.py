"""YouTube thumbnails (1280x720) for the film -> out/film/thumb_*.png"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]

import numpy as np
from PIL import Image

import cast
import sets16 as S
from engine import blit, shoot, draw_text, rect, vignette, rain_layers
from props import FOOT, Y_SLEEP, Y_DOG
from tl import W, H

OUT = os.path.join(os.path.dirname(HERE), 'out', 'film')


def big(spr, k):
    from engine import Sprite
    s = Sprite.__new__(Sprite)
    s.rgba = spr.rgba.repeat(k, 0).repeat(k, 1)
    s.h, s.w = s.rgba.shape[:2]
    return s


def thumb_a():
    w = S.junkyard().copy()
    S.warning_light(w, 0.1)
    blit(w, cast.mira('kneel'), 222, FOOT - 18)
    blit(w, cast.dog('bolt', 'sleep', 'red'), 240, Y_SLEEP)
    scr = shoot(w, 218, 134, 3, size=(W, H))
    rain_layers(scr, 0.4)
    vignette(scr, 1.3)
    scr[:, :150] = (scr[:, :150].astype(np.float32) * 0.45).astype(np.uint8)
    rect(scr, 10, 14, 146, 36, (10, 8, 20))
    draw_text(scr, "UNKNOWN USER", 78, 19, (255, 72, 84), scale=2, outline=None)
    draw_text(scr, "HE", 78, 56, (248, 244, 236), scale=4)
    draw_text(scr, "FORGOT", 78, 92, (248, 244, 236), scale=4)
    draw_text(scr, "HER", 78, 128, (255, 72, 84), scale=4)
    return scr


def thumb_b():
    w = S.yard('rain').copy()
    blit(w, cast.mira('stand'), 216, FOOT - 25)
    blit(w, cast.dog('bolt', 'A', 'red'), 238, Y_DOG + 4, True)
    blit(w, cast.BALL, 236, Y_DOG + 11)
    scr = shoot(w, 232, 132, 3, size=(W, H))
    rain_layers(scr, 0.4)
    vignette(scr, 1.3)
    draw_text(scr, "IT REMEMBERED", 160, 14, (248, 244, 236), scale=3)
    draw_text(scr, "EVERYTHING", 160, 42, (255, 72, 84), scale=3)
    return scr


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (('a', thumb_a), ('b', thumb_b)):
        img = fn().repeat(4, 0).repeat(4, 1)
        Image.fromarray(img).save(os.path.join(OUT, f'thumb_{name}.png'))
    print('ok')
