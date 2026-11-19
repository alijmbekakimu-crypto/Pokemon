"""Автонарезка ярких моментов из видео стримера (с его разрешения) в вертикальные клипы.

    python3 cut_highlights.py ВИДЕО.mp4 --author "@ник_стримера" [--count 5] [--len 30]
                              [--title "GTA 6 — первый день"] [--horizontal]

Как работает:
  1. Считает громкость звука по секундам. Самые громкие места — обычно
     реакции, крики, взрывы, погони: их и берём.
  2. Вокруг каждого пика вырезает клип (по умолчанию 30 с, пик ближе к началу,
     чтобы зритель сразу попадал в момент).
  3. Делает вертикальный кадр 1080x1920: размытый фон + видео по центру,
     сверху заголовок, снизу подпись автора (обязательно при нарезках).
Звук стримера сохраняется. Результат: output/highlights/<имя>_01.mp4 ...
"""
import argparse
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SR = 8000


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def loudness_per_second(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = len(a) // SR
    if n == 0:
        return np.zeros(0)
    rms = np.sqrt((a[: n * SR].reshape(n, SR) ** 2).mean(axis=1) + 1e-9)
    db = 20 * np.log10(rms)
    # сравниваем с фоном вокруг (минутное окно), чтобы искать именно всплески
    k = 60
    pad = np.pad(db, (k // 2, k // 2), mode="edge")
    base = np.array([np.median(pad[i:i + k]) for i in range(n)])
    return db - base


def pick_peaks(score, count, clip_len, lead):
    """Лучшие всплески, не пересекающиеся между собой."""
    sm = np.convolve(score, np.ones(3) / 3, mode="same")
    order = np.argsort(sm)[::-1]
    chosen = []
    for t in order:
        if sm[t] <= 3:  # меньше 3 дБ над фоном — не момент
            break
        start = max(0, t - lead)
        if all(abs(start - c) >= clip_len for c in chosen):
            chosen.append(start)
        if len(chosen) == count:
            break
    return sorted(chosen)


def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def render(src, start, length, out, author, title, horizontal):
    if horizontal:
        vf = ("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
              f"drawtext=fontfile={FONT}:text='{esc(author)}':fontsize=40:fontcolor=white:"
              "box=1:boxcolor=black@0.55:boxborderw=14:x=w-tw-40:y=40")
        fc = f"[0:v]{vf}[v]"
    else:
        fc = ("[0:v]split[a][b];"
              "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "boxblur=30:2,eq=brightness=-0.2[bg];"
              "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[m];"
              f"[m]drawtext=fontfile={FONT}:text='{esc(author)}':fontsize=46:fontcolor=white:"
              "box=1:boxcolor=black@0.55:boxborderw=16:x=(w-tw)/2:y=h*0.72")
        if title:
            fc += (f",drawtext=fontfile={FONT}:text='{esc(title)}':fontsize=64:fontcolor=white:"
                   "borderw=5:bordercolor=black:x=(w-tw)/2:y=h*0.2")
        fc += "[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", src,
                    "-filter_complex", fc + ";[0:a]loudnorm=I=-14:TP=-1.5,afade=t=out:st="
                    f"{length - 0.6:.2f}:d=0.6[a]",
                    "-map", "[v]", "-map", "[a]", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--author", required=True, help="подпись автора, например @streamer (twitch.tv/streamer)")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--len", type=float, default=30.0)
    p.add_argument("--title", default="")
    p.add_argument("--horizontal", action="store_true", help="16:9 вместо вертикального 9:16")
    p.add_argument("--out", default=os.path.join(HERE, "output", "highlights"))
    a = p.parse_args()

    os.makedirs(a.out, exist_ok=True)
    total = duration(a.video)
    length = min(a.len, total)
    score = loudness_per_second(a.video)
    starts = pick_peaks(score, a.count, int(length), lead=int(length * 0.3))
    if not starts:
        starts = list(np.linspace(0, max(0, total - length), a.count))  # тихое видео: равномерно
    name = os.path.splitext(os.path.basename(a.video))[0]
    for i, s in enumerate(starts, 1):
        s = min(float(s), max(0.0, total - length))
        out = os.path.join(a.out, f"{name}_{i:02d}.mp4")
        render(a.video, s, length, out, a.author, a.title, a.horizontal)
        print(f"{out}  (с {int(s) // 60:02d}:{int(s) % 60:02d})", flush=True)


if __name__ == "__main__":
    sys.exit(main())
