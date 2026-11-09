"""--record: one WAV per session in recordings/, your mic and Bit's voice on one timeline.

Stereo, 24 kHz: LEFT = your mic, RIGHT = Bit's voice (+ wake chime), each placed at the
moment it was heard. Kept as separate channels so Bit isn't doubled (the mic also hears
him from the speaker); split or mix them in the editor. Line it up with camera footage
using the wall-clock start time printed when recording begins.
"""
import datetime as dt
import threading
import time
import wave

import numpy as np

from .config import ROOT, log

OUT_RATE = 24000
MIC_RATE = 16000
REC_DIR = ROOT / "recordings"

_active = None


class Recorder:
    def __init__(self):
        REC_DIR.mkdir(exist_ok=True)
        self.t0 = time.monotonic()
        self.started = dt.datetime.now()
        self.path = REC_DIR / f"bit-{self.started:%Y-%m-%d_%H-%M-%S}.wav"
        self.mic: list[np.ndarray] = []
        self.mic_t0 = None
        self.voice: list[tuple[float, np.ndarray, int]] = []
        self.lock = threading.Lock()

    def add_mic(self, block: np.ndarray):
        with self.lock:
            if self.mic_t0 is None:  # the mic stream is continuous from its first block
                self.mic_t0 = time.monotonic() - len(block) / MIC_RATE
            self.mic.append(block.copy())

    def add_voice(self, pcm: np.ndarray, rate: int, heard_at: float):
        if pcm.dtype != np.int16:
            pcm = (np.clip(pcm, -1, 1) * 32767).astype(np.int16)
        with self.lock:
            self.voice.append((heard_at, pcm.copy(), rate))

    def save(self) -> tuple[str, float]:
        from scipy.signal import resample_poly
        with self.lock:
            mic = np.concatenate(self.mic) if self.mic else np.zeros(0, np.int16)
            voice = list(self.voice)
        mic_off = (self.mic_t0 or self.t0) - self.t0
        ends = [mic_off + len(mic) / MIC_RATE] + [t - self.t0 + len(p) / r for t, p, r in voice]
        n = int(max(ends + [time.monotonic() - self.t0]) * OUT_RATE) + 1
        left = np.zeros(n, np.float32)
        right = np.zeros(n, np.float32)
        if len(mic):
            m = resample_poly(mic.astype(np.float32), 3, 2)  # 16 kHz -> 24 kHz
            i = max(0, int(mic_off * OUT_RATE))
            left[i:i + len(m)] = m[: n - i]
        for t, p, r in voice:
            v = p.astype(np.float32) if r == OUT_RATE else resample_poly(p.astype(np.float32), OUT_RATE, r)
            i = max(0, int((t - self.t0) * OUT_RATE))
            seg = v[: n - i]
            right[i:i + len(seg)] += seg
        stereo = np.stack([left, right], axis=1)
        with wave.open(str(self.path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(OUT_RATE)
            w.writeframes(np.clip(stereo, -32768, 32767).astype(np.int16).tobytes())
        secs = n / OUT_RATE
        log.info("recording saved: %s (%.1fs)", self.path.name, secs)
        return str(self.path.relative_to(ROOT)), secs


def start() -> Recorder:
    global _active
    _active = Recorder()
    log.info("recording started %s -> %s", _active.started.isoformat(timespec="milliseconds"), _active.path.name)
    return _active


def stop():
    """Save the session WAV (call once, on exit). Returns (path, seconds) or None."""
    global _active
    rec, _active = _active, None
    return rec.save() if rec else None


def mic(block):
    if _active:
        _active.add_mic(block)


def voice(pcm, rate, heard_at):
    if _active:
        _active.add_voice(pcm, rate, heard_at)
