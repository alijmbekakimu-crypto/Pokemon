"""Tiny synth: every sound in the episode is generated here (no samples)."""
import wave
import numpy as np

SR = 44100


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def sine(f, dur, phase=0.0):
    return np.sin(2 * np.pi * np.asarray(f) * _t(dur) + phase)


def sweep(f0, f1, dur, shape='sine'):
    t = _t(dur)
    f = f0 + (f1 - f0) * t / max(dur, 1e-6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if shape == 'sine' else np.sign(np.sin(ph))


def square(f, dur):
    return np.sign(sine(f, dur))


def noise(dur, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, int(dur * SR))


def env(n, a=0.005, r=0.1, hold=None):
    """Attack / hold / release envelope over n samples."""
    e = np.ones(n)
    na = max(1, int(a * SR))
    nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)[:n] if na <= n else np.linspace(0, 1, n)
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def decay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lowpass(x, fc, taps=129):
    """Windowed-sinc FIR low-pass (numpy only)."""
    n = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * fc / SR * n) * np.hamming(taps)
    h /= h.sum()
    return np.convolve(x, h, mode='same')


def highpass(x, fc, taps=129):
    return x - lowpass(x, fc, taps)


def piano(f, dur=1.6, tau=0.55):
    t = _t(dur)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
         + 0.12 * np.sin(6 * np.pi * f * t) + 0.05 * np.sin(8 * np.pi * f * t))
    s *= decay(len(t), tau)
    s *= env(len(t), a=0.004, r=0.2)
    return s


def pad(freqs, dur, a=0.8, r=1.0):
    t = _t(dur)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.6, 0.6):
            s += np.sin(2 * np.pi * (f + det) * t)
            s += 0.25 * np.sin(2 * np.pi * 2 * (f + det) * t)
    s /= max(1, len(freqs) * 2)
    return s * env(len(t), a=a, r=r)


class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.L = np.zeros(self.n)
        self.R = np.zeros(self.n)

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= self.n:
            return
        sig = np.asarray(sig)[:self.n - i]
        a = (pan + 1) * np.pi / 4
        self.L[i:i + len(sig)] += sig * gain * np.cos(a)
        self.R[i:i + len(sig)] += sig * gain * np.sin(a)

    def gate(self, t0, t1=None):
        """Hard silence from t0 (to t1)."""
        i0 = int(t0 * SR)
        i1 = self.n if t1 is None else int(t1 * SR)
        self.L[i0:i1] = 0
        self.R[i0:i1] = 0

    def write(self, path, peak=0.89):
        st = np.stack([self.L, self.R], axis=1)
        m = np.abs(st).max()
        if m > 0:
            st = st / m * peak
        data = (st * 32767).astype('<i2')
        with wave.open(path, 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(data.tobytes())
