"""Сборка видео: озвучка (RHVoice) + фоны + субтитры + музыка -> mp4.

    python3 build.py long    # горизонтальное видео 1920x1080 для YouTube
    python3 build.py short   # вертикальное 1080x1920 для Shorts/TikTok/Reels
    python3 build.py thumb   # превью 1280x720
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import scenes
from script import CHAPTERS, SHORT, TTS_FIXES

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "output")
SR = 44100
FPS = 30
VOICE = "aleksandr-hq"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

MODES = {
    "long": dict(chapters=CHAPTERS, size=(1920, 1080), bg=(2304, 1296), name="gta6_syuzhet_razbor.mp4"),
    "short": dict(chapters=SHORT, size=(1080, 1920), bg=(1296, 2304), name="gta6_short.mp4"),
}


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ---------- озвучка ----------

def tts(text, path):
    if os.path.exists(path):
        return
    spoken = text
    for k, v in sorted(TTS_FIXES.items(), key=lambda kv: -len(kv[0])):
        spoken = spoken.replace(k, v)
    raw = path + ".raw.wav"
    subprocess.run(["RHVoice-test", "-p", VOICE, "-o", raw], input=spoken.encode(), check=True)
    # ресемплинг + лёгкая «радийная» обработка голоса
    run(["ffmpeg", "-y", "-i", raw, "-ar", str(SR), "-ac", "1",
         "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
                "equalizer=f=180:t=q:w=1:g=3,silenceremove=start_periods=1:start_threshold=-50dB,"
                "areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse", path])
    os.remove(raw)


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def write_wav(path, data, channels=1):
    data = np.clip(data, -1, 1)
    with wave.open(path, "w") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


# ---------- музыка (синтвейв-подложка, синтезируется с нуля) ----------

def music(seconds, bpm=84):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    beat = 60 / bpm
    bar = beat * 4
    # Am - F - C - G
    prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    roots = [45, 41, 48, 43]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    idx = (t // bar).astype(int) % 4
    pad = np.zeros(n, np.float32)
    bass = np.zeros(n, np.float32)
    for ci, chord in enumerate(prog):
        mask = idx == ci
        tt = t[mask]
        for m in chord:
            for det in (-0.12, 0.0, 0.12):
                f = hz(m + det)
                pad[mask] += (2 * ((tt * f) % 1) - 1) * 0.06
        f = hz(roots[ci])
        ph = (tt % (beat / 2)) / (beat / 2)  # восьмые
        bass[mask] = np.sin(2 * np.pi * f * tt) * np.exp(-ph * 4) * 0.5
    # простой однополюсный ФНЧ для мягкости пэда
    a = math.exp(-2 * math.pi * 900 / SR)
    pad = np.asarray(_lowpass(pad, a), np.float32)
    pad *= 0.75 + 0.25 * np.sin(2 * np.pi * t / (bar * 2))
    bt = t % beat
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-bt * 30)) * bt) * np.exp(-bt * 9) * 0.55
    off = (t - beat / 2) % beat
    rng = np.random.default_rng(1)
    hat = rng.standard_normal(n) * np.exp(-off * 60) * 0.05
    mix = pad + bass * 0.6 + kick + hat
    fade = np.minimum(1, np.minimum(t / 3, (seconds - t) / 4)).clip(0, 1)
    return (mix * fade).astype(np.float32)


def _lowpass(x, a):
    from scipy.signal import lfilter  # noqa
    return lfilter([1 - a], [1, -a], x)


# ---------- вставка записей геймплея ----------
# Свои записи игры кладутся в clips/<сцена>/ (например clips/prison/*.mp4).
# Если для сцены есть клипы, они заменяют нарисованный фон: режутся на
# короткие куски (CUT сек) и чередуются, чтобы картинка часто менялась.

CLIPS = os.path.join(HERE, "clips")
CUT = 3.2           # длина одного куска, сек
SKIP_START = 1.0    # пропустить начало каждого файла (меню, загрузка)
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi")


def find_clips(scene):
    folder = os.path.join(CLIPS, scene)
    if not os.path.isdir(folder):
        return []
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(VIDEO_EXT))


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out or 0)


def clip_segment(clips, dur_v, w, h, vertical, seg, tag):
    """Нарезка клипов в сегмент главы длиной dur_v (звук игры не берём —
    в нём бывает музыка с радио, на которую YouTube выдаёт претензии)."""
    lens = {c: probe_duration(c) for c in clips}
    offsets = {c: SKIP_START for c in clips}
    n = max(1, round(dur_v / CUT))
    piece = dur_v / n
    if vertical:  # вертикаль: размытый фон + кадр игры по ширине в центре
        vf = (f"split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"boxblur=30:2,eq=brightness=-0.15[bg];[b]scale={w}:-2[fg];"
              f"[bg][fg]overlay=0:(H-h)/2-120")
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    parts = []
    for i in range(n):
        c = clips[i % len(clips)]
        if offsets[c] + piece > lens[c]:
            offsets[c] = min(SKIP_START, max(0, lens[c] - piece))
        start = offsets[c]
        offsets[c] += piece + 0.6
        # лёгкий наезд или отъезд камеры на каждом куске
        z = "1+0.0006*on" if i % 2 == 0 else "1.06-0.0006*on"
        part = os.path.join(BUILD, f"part_{tag}_{i:03d}.mp4")
        run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{piece + 0.1:.3f}", "-i", c, "-an",
             "-filter_complex",
             f"[0:v]fps={FPS},{vf},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
             f":d=1:s={w}x{h}:fps={FPS},setsar=1,format=yuv420p",
             "-frames:v", str(int(round(piece * FPS))),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", part])
        parts.append(part)
    lst = os.path.join(BUILD, f"parts_{tag}.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-vf", f"fade=t=in:st=0:d=0.3,fade=t=out:st={dur_v - 0.4:.3f}:d=0.4,format=yuv420p",
         "-frames:v", str(int(round(dur_v * FPS))), "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", seg])
    for p in parts:
        os.remove(p)


# ---------- субтитры (ASS) ----------

def ts(sec):
    cs = int(round(sec * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_header(w, h, vertical):
    sub_size, sub_margin = (68, 460) if vertical else (48, 90)
    title_size = 96 if vertical else 92
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,{sub_size},&H00FFFFFF,&H00FFFFFF,&H64000000,&H64000000,1,0,0,0,100,100,0,0,3,10,0,2,{90 if vertical else 220},{90 if vertical else 220},{sub_margin},1
Style: Title,DejaVu Sans,{title_size},&H00BE50FF,&H00FFFFFF,&H00200010,&H96000000,1,0,0,0,100,100,2,0,1,5,3,{8 if vertical else 7},90,90,{260 if vertical else 110},1
Style: Kicker,DejaVu Sans,{int(title_size * 0.45)},&H00FFDC3C,&H00FFFFFF,&H00200010,&H96000000,1,0,0,0,100,100,6,0,1,3,2,{8 if vertical else 7},90,90,{380 if vertical else 215},1
Style: Hero,DejaVu Sans,{230 if vertical else 240},&H00FFFFFF,&H00FFFFFF,&H00BE50FF,&H96000000,1,1,0,0,100,100,6,0,1,8,0,5,60,60,0,1
Style: HeroSub,DejaVu Sans,{70 if vertical else 66},&H00FFDC3C,&H00FFFFFF,&H00200010,&H96000000,1,0,0,0,100,100,8,0,1,4,2,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build(mode):
    cfg = MODES[mode]
    chapters = cfg["chapters"]
    w, h = cfg["size"]
    bw, bh = cfg["bg"]
    vertical = h > w
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    voice = []
    events = []
    segments = []
    cur = 0.0
    for ci, ch in enumerate(chapters):
        intro = ch.get("intro")
        lead = 2.6 if intro else 1.6
        ch_start = cur
        chunk = [np.zeros(int(lead * SR), np.float32)]
        t = cur + lead
        for li, line in enumerate(ch["lines"]):
            p = os.path.join(BUILD, f"tts_{mode}_{ci:02d}_{li:02d}.wav")
            tts(line, p)
            a = read_wav(p)
            d = len(a) / SR
            events.append(("Sub", t, t + d + 0.15, line))
            chunk += [a, np.zeros(int(0.45 * SR), np.float32)]
            t += d + 0.45
        chunk.append(np.zeros(int(0.5 * SR), np.float32))
        audio = np.concatenate(chunk)
        dur = len(audio) / SR
        voice.append(audio)

        # заголовки главы
        if intro:
            events.append(("Hero", ch_start + 0.3, ch_start + lead + 1.2,
                           "{\\fad(500,500)\\fscx120\\fscy120\\t(0,2000,\\fscx100\\fscy100)}" + ch["title"],
                           f"\\pos({w // 2},{int(h * (0.4 if vertical else 0.42))})"))
            if ch["subtitle"]:
                events.append(("HeroSub", ch_start + 0.8, ch_start + lead + 1.2,
                               "{\\fad(500,500)}" + ch["subtitle"].upper(),
                               f"\\pos({w // 2},{int(h * (0.5 if vertical else 0.6))})"))
        else:
            end = min(ch_start + dur - 0.4, ch_start + lead + 3.5)
            events.append(("Title", ch_start + 0.2, end, "{\\fad(400,400)}" + ch["title"], ""))
            if ch["subtitle"]:
                events.append(("Kicker", ch_start + 0.5, end, "{\\fad(400,400)}" + ch["subtitle"].upper(), ""))

        # фон и видеосегмент главы
        bg = os.path.join(BUILD, f"bg_{mode}_{ch['scene']}.png")
        if not os.path.exists(bg):
            scenes.render(ch["scene"], bg, seed=ci + 11, size=(bw, bh))
        seg = os.path.join(BUILD, f"seg_{mode}_{ci:02d}.mp4")
        frames = int(round(dur * FPS))
        dur_v = frames / FPS
        clips = find_clips(ch["scene"])
        if clips:
            clip_segment(clips, dur_v, w, h, vertical, seg, f"{mode}_{ci:02d}")
        else:
            if vertical:
                x = f"(iw-ow)/2+(iw-ow)/2*sin(t/{dur_v:.3f}*PI-PI/2)*{1 if ci % 2 else -1}"
                y = f"(ih-oh)*{'t' if ci % 2 else f'({dur_v:.3f}-t)'}/{dur_v:.3f}"
            else:
                x = f"(iw-ow)*{'t' if ci % 2 == 0 else f'({dur_v:.3f}-t)'}/{dur_v:.3f}"
                y = "(ih-oh)/2"
            run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", bg, "-frames:v", str(frames),
                 "-vf", f"crop={w}:{h}:x='{x}':y='{y}',fade=t=in:st=0:d=0.4,"
                        f"fade=t=out:st={dur_v - 0.4:.3f}:d=0.4,format=yuv420p",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-r", str(FPS), seg])
        segments.append(seg)
        # синхронизируем звук с точной длиной видео
        voice[-1] = np.pad(audio, (0, max(0, int(dur_v * SR) - len(audio))))[: int(dur_v * SR)]
        cur += dur_v
        print(f"[{mode}] глава {ci + 1}/{len(chapters)}: {ch['title']} ({dur_v:.1f} c)", flush=True)

    total = cur
    vo = np.concatenate(voice)
    mu = music(total)[: len(vo)]
    # приглушаем музыку, когда говорит диктор
    env = np.abs(vo)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = np.where(env > 0.01, 0.35, 1.0)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mix = vo * 0.95 + mu * 0.22 * duck
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    wav = os.path.join(BUILD, f"mix_{mode}.wav")
    write_wav(wav, mix)

    ass = os.path.join(BUILD, f"subs_{mode}.ass")
    with open(ass, "w") as f:
        f.write(ass_header(w, h, vertical))
        for ev in events:
            style, a, b, text = ev[:4]
            pos = ev[4] if len(ev) > 4 else ""
            if pos:
                text = "{" + pos + "}" + text
            f.write(f"Dialogue: 0,{ts(a)},{ts(b)},{style},,0,0,0,,{text}\n")

    lst = os.path.join(BUILD, f"list_{mode}.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segments)
    out = os.path.join(OUT, cfg["name"])
    vf = f"subtitles={ass},noise=alls=5:allf=t,format=yuv420p"
    if not vertical:  # кинематографичные полосы
        vf = "drawbox=x=0:y=0:w=iw:h=56:color=black:t=fill,drawbox=x=0:y=ih-56:w=iw:h=56:color=black:t=fill," + vf
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
         "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    print(f"готово: {out} ({total:.1f} c)")


# ---------- превью ----------

def thumb():
    os.makedirs(OUT, exist_ok=True)
    bg = os.path.join(BUILD, "bg_thumb.png")
    scenes.render("night_vice", bg, seed=11, size=(1280, 720))
    img = Image.open(bg).convert("RGB")
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 250)
    mid = ImageFont.truetype(FONT, 74)
    glow_layer = Image.new("RGB", img.size)
    ImageDraw.Draw(glow_layer).text((70, 40), "GTA 6", font=big, fill=(255, 60, 180))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(22))
    img = Image.fromarray(np.minimum(np.asarray(img, np.int32) + np.asarray(glow_layer, np.int32) * 2, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.text((70, 40), "GTA 6", font=big, fill=(255, 255, 255), stroke_width=8, stroke_fill=(255, 60, 180))
    d.rectangle([60, 360, 1220, 470], fill=(60, 220, 255))
    d.text((84, 372), "ЧТО ИЗВЕСТНО", font=mid, fill=(10, 6, 30))
    d.rectangle([60, 490, 920, 600], fill=(255, 220, 60))
    d.text((84, 502), "О СЮЖЕТЕ", font=mid, fill=(10, 6, 30))
    img.save(os.path.join(OUT, "gta6_thumbnail.png"))
    print("готово: превью")


if __name__ == "__main__":
    what = sys.argv[1:] or ["long", "short", "thumb"]
    for m in what:
        thumb() if m == "thumb" else build(m)
