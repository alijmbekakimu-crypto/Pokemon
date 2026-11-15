"""Render the film.

    python3 render.py stills            # storyboard sheet per chapter -> out/film/stills/
    python3 render.py chapter 3         # one chapter -> out/film/chapters/03_*.mp4
    python3 render.py all [-j 4]        # every chapter in parallel, then concat
    python3 render.py concat            # join chapters -> out/film/GOOD_BOY_EXE_film.mp4
"""
import os
import subprocess
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]

import numpy as np
from PIL import Image

import script
import score
from engine import SCALE
from tl import W, H, FPS

OUT = os.path.join(os.path.dirname(HERE), 'out', 'film')
CH_DIR = os.path.join(OUT, 'chapters')


def upscale(a):
    return a.repeat(SCALE, 0).repeat(SCALE, 1)


def stills():
    sdir = os.path.join(OUT, 'stills')
    os.makedirs(sdir, exist_ok=True)
    total = 0
    for k, mk in enumerate(script.CHAPTERS):
        ch = mk()
        total += ch.dur
        imgs = [s.render(min(s.dur * 0.62, s.dur - 0.05)) for s in ch.shots]
        cols = 6
        rows = (len(imgs) + cols - 1) // cols
        sheet = np.zeros((rows * (H + 4), cols * (W + 4), 3), np.uint8)
        for i, im in enumerate(imgs):
            r, c = divmod(i, cols)
            sheet[r * (H + 4):r * (H + 4) + H, c * (W + 4):c * (W + 4) + W] = im
        Image.fromarray(sheet).save(os.path.join(sdir, f'{ch.name}.png'))
        print(f'{ch.name}: {len(ch.shots)} shots, {ch.dur:.1f}s')
    print(f'TOTAL {total / 60:.2f} min')


def chapter(k):
    os.makedirs(CH_DIR, exist_ok=True)
    ch = script.CHAPTERS[k]()
    wav = os.path.join(CH_DIR, f'{ch.name}.wav')
    score.chapter_audio(ch, wav, seed=k * 1000)
    mp4 = os.path.join(CH_DIR, f'{ch.name}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * SCALE}x{H * SCALE}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-threads', '1', '-c:a', 'pcm_s16le', '-shortest', mp4.replace('.mp4', '.mkv')]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(round(ch.dur * FPS))
    for i in range(n):
        p.stdin.write(upscale(ch.frame(i / FPS)).tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print('done', ch.name, flush=True)
    return ch.name


def concat():
    names = sorted(f for f in os.listdir(CH_DIR) if f.endswith('.mkv'))
    lst = os.path.join(CH_DIR, 'list.txt')
    with open(lst, 'w') as fh:
        for nme in names:
            fh.write(f"file '{os.path.join(CH_DIR, nme)}'\n")
    out = os.path.join(OUT, 'GOOD_BOY_EXE_film.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if cmd == 'stills':
        stills()
    elif cmd == 'chapter':
        for k in sys.argv[2:]:
            chapter(int(k))
    elif cmd == 'all':
        j = int(sys.argv[sys.argv.index('-j') + 1]) if '-j' in sys.argv else 4
        with Pool(j) as pool:
            pool.map(chapter, range(len(script.CHAPTERS)))
        concat()
    elif cmd == 'concat':
        concat()
