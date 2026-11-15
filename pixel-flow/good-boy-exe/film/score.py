"""Music, ambience and sound effects for the film — all synthesized."""
import functools
import numpy as np
import audio as A

SR = A.SR
NOTE = {n: 440.0 * 2 ** ((i - 9) / 12) for i, n in enumerate(
    ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def f(name, octave):
    return NOTE[name] * 2 ** (octave - 4)


def chord(root, kind='min', octave=3):
    r = f(root, octave)
    iv = {'min': (0, 3, 7), 'maj': (0, 4, 7), 'sus': (0, 5, 7), 'dim': (0, 3, 6)}[kind]
    return [r * 2 ** (i / 12) for i in iv]


def n(x):
    return int(x * SR)


# ---------------------------------------------------------------- instruments
def musicbox(fr, dur=1.2):
    t = np.arange(n(dur)) / SR
    s = np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(2 * np.pi * fr * 4.01 * t) * np.exp(-t * 9)
    return s * np.exp(-t * 3.5) * A.env(len(t), 0.002, 0.05)


def glass(freqs, dur):
    t = np.arange(n(dur)) / SR
    s = sum(np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(2 * np.pi * fr * 3 * t) for fr in freqs) / max(1, len(freqs))
    return s * A.env(len(t), dur * 0.4, dur * 0.4)


def saw(fr, dur):
    t = np.arange(n(dur)) / SR
    return 2 * ((t * fr) % 1) - 1


def kick():
    t = np.arange(n(0.25)) / SR
    fr = 120 * np.exp(-t * 25) + 45
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 12)


def hat(seed=0):
    return A.highpass(A.noise(0.05, seed), 6000, 63) * A.decay(n(0.05), 0.012)


# ---------------------------------------------------------------- moods
PROGS = {
    'sad': ([('A', 'min'), ('F', 'maj'), ('C', 'maj'), ('G', 'maj'), ('A', 'min'), ('F', 'maj'), ('C', 'maj'), ('E', 'maj')], 2.4),
    'tender': ([('C', 'maj'), ('G', 'maj'), ('A', 'min'), ('F', 'maj')], 2.0),
    'hope': ([('C', 'maj'), ('F', 'maj'), ('A', 'min'), ('G', 'maj'), ('F', 'maj'), ('C', 'maj'), ('G', 'sus'), ('G', 'maj')], 2.4),
    'mystery': ([('E', 'min'), ('C', 'maj'), ('E', 'min'), ('B', 'maj')], 3.2),
    'chase': ([('D', 'min'), ('A#', 'maj'), ('C', 'maj'), ('A', 'maj')], 3.43),
}


def _melody_notes(ch, rng, octave=5):
    tones = chord(ch[0], ch[1], octave)
    return [rng.choice(tones) * (2 if rng.random() < 0.2 else 1)]


def gen_mood(mood, dur, seed=0):
    out = np.zeros(n(dur) + n(4))
    rng = np.random.default_rng(seed)

    def add(sig, t, g=1.0):
        i = n(t)
        if i >= len(out):
            return
        sig = sig[:len(out) - i]
        out[i:i + len(sig)] += sig * g

    if mood in ('sad', 'tender', 'hope', 'mystery'):
        prog, cd = PROGS[mood]
        t, k = 0.0, 0
        while t < dur:
            root, kind = prog[k % len(prog)]
            ch = chord(root, kind, 3)
            grow = min(1.0, t / max(dur, 1)) if mood == 'hope' else 0.0
            if mood == 'mystery':
                add(A.lowpass(glass([c * 2 for c in ch], cd + 0.8), 3000), t, 0.10)
                add(A.sine(f(root, 1), cd) * A.env(n(cd), 0.3, 0.6), t, 0.10)
                if rng.random() < 0.8:
                    add(A.piano(rng.choice(chord(root, kind, 5)), 2.5, 0.9), t + rng.uniform(0, cd * 0.6), 0.09)
            else:
                add(A.lowpass(A.pad(ch, cd + 0.6, a=0.5, r=0.7), 1800), t, 0.12 + 0.08 * grow)
                add(A.sine(f(root, 2), cd) * A.env(n(cd), 0.05, 0.6), t, 0.10 + 0.04 * grow)
                if mood == 'tender':
                    arp = chord(root, kind, 5) + [chord(root, kind, 5)[0] * 2]
                    for j in range(int(cd / 0.25)):
                        add(musicbox(arp[(j * 2 + k) % len(arp)] if j % 4 != 3 else arp[1]), t + j * 0.25, 0.06)
                else:
                    steps = [0, 0.8, 1.6] if mood == 'sad' else ([0, 0.6, 1.2, 1.8] if grow < 0.5 else [0, 0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1])
                    for s in steps:
                        if rng.random() < 0.85:
                            add(A.piano(_melody_notes((root, kind), rng)[0], 1.8), t + s, 0.11 + 0.04 * grow)
            t += cd
            k += 1
    elif mood == 'chase':
        prog, cd = PROGS['chase']
        beat = cd / 8
        t, k = 0.0, 0
        while t < dur:
            root, kind = prog[k % len(prog)]
            for j in range(8):
                tt = t + j * beat
                add(kick(), tt, 0.45 if j % 2 == 0 else 0.0)
                add(hat(j + k), tt + beat / 2, 0.12)
                b = A.lowpass(np.sign(A.sine(f(root, 2), beat * 0.9)), 700) * A.env(n(beat * 0.9), 0.003, 0.05)
                add(b, tt, 0.10)
                b2 = A.lowpass(np.sign(A.sine(f(root, 2), beat * 0.45)), 700) * A.env(n(beat * 0.45), 0.003, 0.03)
                add(b2, tt + beat / 2, 0.08)
            arp = chord(root, kind, 5)
            for j in range(16):
                add(A.lowpass(saw(arp[j % 3] * (2 if j % 8 == 7 else 1), beat / 2 * 0.8), 2500)
                    * A.env(n(beat / 2 * 0.8), 0.002, 0.03), t + j * beat / 2, 0.035)
            add(A.lowpass(A.pad(chord(root, kind, 4), cd, a=0.1, r=0.3), 1500), t, 0.06)
            t += cd
            k += 1
    elif mood in ('tense', 'glitch'):
        d = dur + 1
        t = np.arange(n(d)) / SR
        drone = (np.sin(2 * np.pi * 36.7 * t) + 0.6 * np.sin(2 * np.pi * 38.9 * t)
                 + 0.3 * np.sign(np.sin(2 * np.pi * 73.4 * t)))
        drone *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t)
        add(A.lowpass(drone, 400) * A.env(len(t), 1.5, 1.0), 0, 0.16)
        hi = sum(np.sin(2 * np.pi * fr * t) for fr in (1174.7, 1244.5, 1318.5)) / 3
        add(hi * (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t)) * A.env(len(t), 3, 1), 0, 0.025)
        for tt in np.arange(0.5, dur, 1.1):
            add(A.sine(46, 0.2) * A.decay(n(0.2), 0.06), tt, 0.35)
            add(A.sine(46, 0.2) * A.decay(n(0.2), 0.06), tt + 0.28, 0.22)
        if mood == 'glitch':
            for tt in rng.uniform(0, dur, int(dur * 1.5)):
                add(np.sign(A.sine(rng.uniform(200, 3000), 0.05)) * A.decay(n(0.05), 0.02), tt, 0.04)
    return out[:n(dur)]


# ---------------------------------------------------------------- ambience (looped)
@functools.lru_cache(None)
def _amb_loop(kind):
    L = 12.0
    if kind == 'rain':
        x = A.highpass(A.lowpass(A.noise(L, 2), 4200), 250) * 0.9
        rng = np.random.default_rng(4)
        for i in rng.integers(0, n(L) - 2000, 160):
            x[i:i + 400] += rng.uniform(0.2, 1) * A.sine(rng.uniform(1800, 4200), 400 / SR) * A.decay(400, 0.002) * 0.4
    elif kind == 'snow':
        x = A.lowpass(A.noise(L, 3), 500)
        x *= 0.6 + 0.4 * np.sin(np.linspace(0, 2 * np.pi * 2, len(x)))
        x = x * 1.6
    elif kind == 'city':
        x = A.lowpass(A.noise(L, 5), 250) * 1.2 + 0.2 * A.sine(60, L)
    elif kind == 'room':
        x = A.lowpass(A.noise(L, 6), 200) * 0.25
        for tt in np.arange(0, L, 1.0):
            i = n(tt)
            x[i:i + n(0.02)] += A.sine(3000, 0.02) * A.decay(n(0.02), 0.004) * 0.08
    elif kind == 'junk':
        x = A.lowpass(A.noise(L, 7), 300) * 0.8
        for tt in (2.0, 7.5):
            i = n(tt)
            c = A.sweep(300, 240, 1.2) * A.env(n(1.2), 0.3, 0.6) * 0.06
            x[i:i + len(c)] += c
    else:
        return None
    fade = n(0.5)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x


def ambience(kind, dur):
    loop = _amb_loop(kind)
    if loop is None:
        return None
    hop = len(loop) - n(0.5)
    out = np.zeros(n(dur) + len(loop))
    i = 0
    while i < n(dur):
        out[i:i + len(loop)] += loop
        i += hop
    return out[:n(dur)]


AMB_GAIN = {'rain': 0.30, 'snow': 0.28, 'city': 0.25, 'room': 0.5, 'junk': 0.35}


# ---------------------------------------------------------------- sfx
def P(*arrs):
    """Sum arrays of different lengths."""
    out = np.zeros(max(len(a) for a in arrs))
    for a in arrs:
        out[:len(a)] += a
    return out


def sfx(name, seed=0):
    N = A.noise
    if name == 'boot':
        return A.sweep(180, 1200, 1.0, 'sq') * A.env(n(1.0), 0.02, 0.3) * 0.5
    if name in ('chirp', 'powerup'):
        d = 0.15 if name == 'chirp' else 0.8
        return A.sweep(600, 1700, d) * A.env(n(d), 0.005, 0.05)
    if name == 'powerdown':
        return A.sweep(900, 80, 1.2, 'sq') * A.env(n(1.2), 0.005, 0.4) * 0.4
    if name == 'hud':
        return A.square(1500, 0.03) * A.decay(n(0.03), 0.008) * 0.6
    if name == 'step':
        return A.lowpass(N(0.08, seed), 400) * A.decay(n(0.08), 0.02) + 0.5 * A.sine(70, 0.08) * A.decay(n(0.08), 0.03)
    if name == 'snowstep':
        return A.lowpass(N(0.12, seed), 1500) * A.env(n(0.12), 0.02, 0.08) * 0.6
    if name == 'paw':
        return A.sine(2400, 0.03) * A.decay(n(0.03), 0.006) + 0.5 * A.sine(3600, 0.03) * A.decay(n(0.03), 0.004)
    if name == 'thud':
        return A.lowpass(N(0.25, seed), 300) * A.decay(n(0.25), 0.05) * 1.5
    if name == 'knock':
        return A.lowpass(N(0.06, seed), 900) * A.decay(n(0.06), 0.012) + 0.6 * A.sine(180, 0.06) * A.decay(n(0.06), 0.02)
    if name == 'burst':
        return A.lowpass(N(0.3, seed), 1400) * A.decay(n(0.3), 0.06) + A.sweep(140, 55, 0.3) * A.decay(n(0.3), 0.1)
    if name == 'shimmer':
        s = sum(A.sine(fr, 1.6) for fr in (880, 1108.73, 1318.5)) / 3
        return s * A.env(n(1.6), 0.3, 1.0) * 0.5
    if name == 'whoosh':
        w = A.highpass(N(0.45, seed), 1200)
        return w * np.sin(np.linspace(0, np.pi, len(w)))
    if name == 'impact':
        return P(A.sine(55, 0.9) * A.decay(n(0.9), 0.3), A.lowpass(N(0.4, seed), 600) * A.decay(n(0.4), 0.08) * 0.7)
    if name == 'thunder':
        th = A.lowpass(N(3.0, seed), 160)
        return th * A.env(len(th), 0.03, 0.5) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 9, len(th))))) * A.decay(len(th), 1.0) * 2.5
    if name == 'dig':
        return A.lowpass(A.highpass(N(0.09, seed), 300), 2200) * A.env(n(0.09), 0.01, 0.05)
    if name == 'servo':
        return A.lowpass(A.sweep(300, 620, 0.4, 'sq'), 1200) * A.env(n(0.4), 0.05, 0.1) * 0.3
    if name == 'bounce':
        return A.sweep(170, 90, 0.09) * A.decay(n(0.09), 0.03)
    if name == 'plink':
        return A.sine(1760, 0.6) * A.decay(n(0.6), 0.15) * 0.5
    if name == 'glitch':
        return A.lowpass(np.sign(N(0.4, seed)) * (N(0.4, seed + 1) > 0.3), 5000) * A.env(n(0.4), 0.001, 0.1) * 0.6
    if name == 'heartbeat':
        hb = A.sine(48, 0.18) * A.decay(n(0.18), 0.05)
        out = np.zeros(n(0.6))
        out[:len(hb)] += hb
        out[n(0.28):n(0.28) + len(hb)] += hb * 0.6
        return out * 1.5
    if name == 'beep':
        return A.sine(1000, 0.12) * A.env(n(0.12), 0.003, 0.02) * 0.4
    if name == 'flatline':
        return A.sine(1000, 2.5) * A.env(n(2.5), 0.003, 0.3) * 0.35
    if name == 'siren':
        t = np.arange(n(3.0)) / SR
        fr = 700 + 250 * np.sin(2 * np.pi * 0.8 * t)
        return np.sin(2 * np.pi * np.cumsum(fr) / SR) * A.env(len(t), 0.3, 0.8) * 0.3
    if name == 'doorbell':
        return np.concatenate([A.piano(659.25, 0.5, 0.4), A.piano(523.25, 1.0, 0.5)]) * 0.8
    if name == 'phone':
        t = np.arange(n(1.6)) / SR
        ring = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * ((t * 20).astype(int) % 2) * (t < 1.0)
        return ring * 0.3
    if name == 'door':
        return P(A.lowpass(A.sweep(200, 120, 0.5, 'sq'), 500) * A.env(n(0.5), 0.05, 0.3) * 0.3, A.lowpass(N(0.15, seed), 400) * A.decay(n(0.15), 0.04))
    if name == 'bark':
        b = A.lowpass(A.sweep(700, 380, 0.16, 'sq'), 2200) * A.env(n(0.16), 0.005, 0.06)
        return b * 0.7 + A.lowpass(N(0.16, seed), 2000) * A.env(n(0.16), 0.005, 0.06) * 0.2
    if name == 'growl':
        t = np.arange(n(1.2)) / SR
        g = np.sign(np.sin(2 * np.pi * (70 + 8 * np.sin(2 * np.pi * 7 * t)) * t))
        return A.lowpass(g, 500) * A.env(len(t), 0.1, 0.3) * 0.5
    if name == 'static':
        return A.highpass(N(1.5, seed), 1500) * A.env(n(1.5), 0.05, 0.3) * 0.4
    if name == 'engine':
        t = np.arange(n(3.0)) / SR
        e = np.sign(np.sin(2 * np.pi * (40 + 20 * t) * t))
        return A.lowpass(e, 300) * A.env(len(t), 0.2, 1.2) * 0.4
    if name == 'alarm':
        return np.concatenate([A.square(880, 0.15), np.zeros(n(0.05)), A.square(660, 0.15)]) * 0.12
    if name == 'zap':
        return A.highpass(N(0.25, seed), 2000) * A.decay(n(0.25), 0.05) + A.sweep(2000, 200, 0.25) * 0.3
    if name == 'chime':
        return P(A.piano(1318.5, 1.6, 0.6), 0.6 * A.piano(1975.5, 1.6, 0.5)) * 0.6
    if name == 'ding':
        return (A.piano(1318.5, 1.5) + A.piano(1760, 1.5) * 0.6)
    if name == 'crash':
        return A.lowpass(N(0.8, seed), 3000) * A.decay(n(0.8), 0.15) * 1.2
    if name == 'delete':
        return np.concatenate([A.sweep(1200, 300, 0.25, 'sq') * 0.3, np.zeros(n(0.05)), A.sine(200, 0.15) * 0.4])
    if name == 'sync':
        return A.sweep(200, 2000, 2.0) * A.env(n(2.0), 0.3, 0.3) * 0.3
    if name == 'tick':
        return A.sine(3000, 0.02) * A.decay(n(0.02), 0.004)
    if name == 'cough':
        return A.lowpass(N(0.25, seed), 1200) * A.env(n(0.25), 0.01, 0.15) * 0.8
    raise KeyError(name)


def voice(freq, seed=0):
    d = 0.045
    return A.lowpass(np.sign(A.sine(freq * (1 + 0.08 * ((seed % 5) - 2)), d)), 2500) * A.env(n(d), 0.003, 0.02) * 0.25


# ---------------------------------------------------------------- chapter mix
def chapter_audio(ch, path, seed=0):
    m = A.Mix(ch.dur + 0.1)
    # music: merge consecutive moods
    segs, cur = [], None
    for s, st in zip(ch.shots, ch.starts):
        if cur and cur[2] == s.mood:
            cur[1] = st + s.dur
        else:
            if cur:
                segs.append(cur)
            cur = [st, st + s.dur, s.mood]
    segs.append(cur)
    for t0, t1, mood in segs:
        if not mood:
            continue
        mus = gen_mood(mood, t1 - t0 + 1.0, seed=int(t0 * 10) + seed)
        e = np.ones(len(mus))
        fi, fo = n(1.0), n(1.5)
        e[:fi] = np.linspace(0, 1, fi)
        e[-fo:] = np.linspace(1, 0, fo)
        m.add(mus * e, t0, 1.0)
    # ambience per shot
    for s, st in zip(ch.shots, ch.starts):
        kind = s.amb
        if kind is None and s.screen is None:
            names = [f if isinstance(f, str) else f[0] for f in s.fx]
            kind = 'rain' if 'rain' in names else 'snow' if 'snow' in names else 'room'
        if kind and kind != 'none':
            a = ambience(kind, s.dur + 0.3)
            if a is not None:
                e = np.ones(len(a))
                k = min(n(0.3), len(a) // 2)
                e[:k] = np.linspace(0, 1, k)
                e[-k:] = np.linspace(1, 0, k)
                m.add(a * e, st, AMB_GAIN[kind])
        for item in s.sfx:
            tt, name = item[0], item[1]
            g = item[2] if len(item) > 2 else 0.5
            pan = item[3] if len(item) > 3 else 0.0
            m.add(sfx(name, seed=int((st + tt) * 100) % 997), st + tt, g, pan)
        for c in s.caps:
            for i, (tt, kind_b) in enumerate(c.blips()):
                if st + tt >= st + s.dur:
                    continue
                if kind_b == 'hud':
                    m.add(sfx('hud'), st + tt, 0.10)
                else:
                    m.add(voice(kind_b, i), st + tt, 0.16)
    m.write(path, gain=0.9)
