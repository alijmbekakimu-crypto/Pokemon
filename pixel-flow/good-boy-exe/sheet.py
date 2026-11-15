"""Character sheet + location still -> out/cast_sheet.png, out/set_yard.png"""
import os
import numpy as np
from PIL import Image
from engine import SW, SH, Sprite, blit, draw_text, upscale, shoot, rect, vignette
import cast
import sets

OUT = os.path.join(os.path.dirname(__file__), 'out')


def big(spr, k):
    s = Sprite.__new__(Sprite)
    s.rgba = spr.rgba.repeat(k, 0).repeat(k, 1)
    s.h, s.w = s.rgba.shape[:2]
    return s


def sheet():
    c = np.zeros((SH, SW, 3), np.uint8)
    c[:] = (14, 12, 28)
    for y in range(0, SH, 8):
        c[y, :] = (20, 18, 40)
    draw_text(c, "GOOD BOY.EXE", 90, 10, (96, 236, 255), scale=2)
    draw_text(c, "CAST SHEET", 90, 30, (150, 150, 196))

    blit(c, big(cast.bolt('A'), 4), 90 - 56, 46)
    draw_text(c, "BOLT - K-9 UNIT", 90, 122, (240, 240, 250))
    for i, legs in enumerate("ABC"):
        blit(c, big(cast.bolt(legs), 2), 4 + i * 60, 136)
    blit(c, big(cast.bolt('A', 'red'), 2), 62, 178)
    draw_text(c, "RED MODE", 90, 216, (255, 64, 76))

    blit(c, big(cast.MIRA_SIT, 2), 8, 240)
    blit(c, big(cast.MIRA_STAND, 2), 50, 234)
    blit(c, big(cast.MIRA_SHOUT, 2), 84, 234)
    blit(c, big(cast.DAD['stand'], 2), 142, 226)
    draw_text(c, "MIRA", 52, 290, (242, 194, 66))
    draw_text(c, "DAD", 156, 306, (150, 150, 196))
    blit(c, big(cast.BALL, 3), 6, 296)
    cr = np.zeros((20, 34, 3), np.uint8)
    cr[:] = (14, 12, 28)
    cast.draw_crate(cr, 2, 18)
    blit(c, big(Sprite_from(cr), 1), 24, 296)
    return c


def Sprite_from(arr):
    s = Sprite.__new__(Sprite)
    s.h, s.w = arr.shape[:2]
    s.rgba = np.concatenate([arr, np.full(arr.shape[:2] + (1,), 255, np.uint8)], axis=2)
    return s


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(upscale(sheet())).save(os.path.join(OUT, 'cast_sheet.png'))
    w = sets.yard()
    blit(w, cast.MIRA_SIT, 62, 105)
    scr = shoot(w, 85, 80, 2)
    vignette(scr)
    Image.fromarray(upscale(scr)).save(os.path.join(OUT, 'set_yard.png'))
    print("ok")
