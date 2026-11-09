"""Audio out: pick the speaker hidden in the real Bit, play PCM, chime."""
import numpy as np
import sounddevice as sd

import time

from . import face, recorder
from .config import BIT_AUDIO_DEVICE, log

_device_cache = None


def output_device():
    """Index of BIT_AUDIO_DEVICE if connected, else None (system default)."""
    global _device_cache
    if _device_cache is not None:
        return _device_cache if _device_cache >= 0 else None
    _device_cache = -1
    if BIT_AUDIO_DEVICE:
        for i, d in enumerate(sd.query_devices()):
            if d["max_output_channels"] > 0 and BIT_AUDIO_DEVICE.lower() in d["name"].lower():
                _device_cache = i
                log.info("speaker: using '%s' (#%d)", d["name"], i)
                return i
        log.warning("speaker: '%s' not found, falling back to default output", BIT_AUDIO_DEVICE)
        print(f"[speaker] '{BIT_AUDIO_DEVICE}' not connected - using Mac speakers")
    else:
        log.info("speaker: BIT_AUDIO_DEVICE not set, using default output")
    return None


def device_name():
    i = output_device()
    return sd.query_devices(i if i is not None else sd.default.device[1])["name"]


def play(samples: np.ndarray, rate: int, mouth: bool = False):
    """Play float32 or int16 mono audio and block until done. mouth=True drives the face."""
    recorder.voice(samples, rate, time.monotonic() + 0.05)
    if mouth and samples.dtype == np.int16:
        track = face.MouthTrack(rate, output_latency=0.05)
        track.feed(samples)
        track.end()
    sd.play(samples, rate, device=output_device())
    sd.wait()


def chime():
    """Short rising two-note 'I heard you' chime."""
    rate = 24000
    out = []
    for freq, dur in ((880, 0.07), (1320, 0.11)):
        t = np.linspace(0, dur, int(rate * dur), endpoint=False)
        env = np.minimum(1, np.minimum(t, dur - t) * 60)
        out.append(0.25 * np.sin(2 * np.pi * freq * t) * env)
    play(np.concatenate(out).astype(np.float32), rate)


class PCMStream:
    """Play 16-bit mono PCM as chunks arrive (low latency streaming TTS)."""

    def __init__(self, rate: int):
        self.stream = sd.RawOutputStream(
            samplerate=rate, channels=1, dtype="int16", device=output_device()
        )
        self.stream.start()
        self._carry = b""
        self.rate = rate
        self.mouth = face.MouthTrack(rate, output_latency=self.stream.latency)
        self._heard_at = 0.0  # when the next written sample will come out of the speaker

    def write(self, chunk: bytes):
        data = self._carry + chunk
        cut = len(data) - (len(data) % 2)
        self._carry = data[cut:]
        if cut:
            pcm = np.frombuffer(data[:cut], dtype=np.int16)
            self._heard_at = max(self._heard_at, time.monotonic() + self.stream.latency)
            recorder.voice(pcm, self.rate, self._heard_at)
            self._heard_at += len(pcm) / self.rate
            self.mouth.feed(pcm)
            self.stream.write(data[:cut])

    def close(self):
        self.mouth.end()
        self.stream.stop()
        self.stream.close()
