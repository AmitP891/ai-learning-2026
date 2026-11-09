"""Bit's ears: always-on local wake word, hold-SPACE backup, VAD recording, Whisper.

Nothing leaves the Mac here: wake word, VAD and Whisper all run on-device.
"""
import queue
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import webrtcvad

from . import face, speaker
from .config import BIT_MIC_DEVICE, WAKE_MODEL, WAKE_THRESHOLD, WHISPER_MODEL, log

RATE = 16000
BLOCK = 1280            # 80 ms, what openWakeWord wants
VAD_FRAME = 160         # 10 ms frames for webrtcvad
SILENCE_END_S = 1.0     # stop recording after this much silence
NO_SPEECH_GIVEUP_S = 5.0
MAX_RECORD_S = 15.0
WAKE_COOLDOWN_S = 1.5


def _mic_device():
    if not BIT_MIC_DEVICE:
        return None
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and BIT_MIC_DEVICE.lower() in d["name"].lower():
            return i
    log.warning("mic '%s' not found, using default", BIT_MIC_DEVICE)
    return None


class Ears:
    def __init__(self, load_whisper=True):
        from openwakeword.model import Model

        wm = WAKE_MODEL
        if wm.endswith((".onnx", ".tflite")) and not Path(wm).is_absolute():
            wm = str(Path(__file__).resolve().parent.parent / wm)
        self.wake = Model(wakeword_models=[wm], inference_framework="onnx")
        self.wake_name = WAKE_MODEL
        self.vad = webrtcvad.Vad(2)
        self.whisper = None
        if load_whisper:
            from faster_whisper import WhisperModel
            self.whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            # warm up so the first real transcription is fast
            self.whisper.transcribe(np.zeros(RATE, dtype=np.float32), language="en")
        self.q: "queue.Queue[np.ndarray]" = queue.Queue()
        self.space_down = threading.Event()
        self._last_wake = 0.0
        self._stream = None

    # ---- plumbing -------------------------------------------------------
    def start(self, space=True):
        self._stream = sd.InputStream(
            samplerate=RATE, channels=1, dtype="int16", blocksize=BLOCK,
            device=_mic_device(), callback=self._on_audio,
        )
        self._stream.start()
        if space:
            self._start_space_listener()

    def _on_audio(self, indata, frames, t, status):
        block = indata[:, 0].copy()
        self.q.put(block)
        face.mic(block)

    def _start_space_listener(self):
        try:
            from pynput import keyboard
        except Exception as e:
            print(f"[ears] space-bar trigger unavailable: {e}")
            return

        def on_press(k):
            if k == keyboard.Key.space:
                self.space_down.set()

        def on_release(k):
            if k == keyboard.Key.space:
                self.space_down.clear()

        keyboard.Listener(on_press=on_press, on_release=on_release, daemon=True).start()

    def drain(self):
        while not self.q.empty():
            self.q.get_nowait()

    # ---- wake word ------------------------------------------------------
    def wake_score(self, frame: np.ndarray) -> float:
        return max(self.wake.predict(frame).values())

    def heard_wake(self, frame) -> bool:
        score = self.wake_score(frame)
        now = time.monotonic()
        if score >= WAKE_THRESHOLD and now - self._last_wake > WAKE_COOLDOWN_S:
            self._last_wake = now
            self.wake.reset()
            log.info("wake: %s score=%.2f", self.wake_name, score)
            return True
        return False

    # ---- recording ------------------------------------------------------
    def _is_speech(self, frame: np.ndarray) -> bool:
        return any(
            self.vad.is_speech(frame[i:i + VAD_FRAME].tobytes(), RATE)
            for i in range(0, len(frame), VAD_FRAME)
        )

    def record_until_silence(self) -> np.ndarray:
        frames, started, silent, t0 = [], False, 0.0, time.monotonic()
        block_s = BLOCK / RATE
        while True:
            f = self.q.get()
            speech = self._is_speech(f)
            if speech:
                started, silent = True, 0.0
            elif started:
                silent += block_s
            if started or speech:
                frames.append(f)
            elapsed = time.monotonic() - t0
            if started and silent >= SILENCE_END_S:
                break
            if not started and elapsed > NO_SPEECH_GIVEUP_S:
                break
            if elapsed > MAX_RECORD_S:
                break
        return np.concatenate(frames) if frames else np.zeros(0, dtype=np.int16)

    def record_while_space(self) -> np.ndarray:
        frames = []
        while self.space_down.is_set():
            try:
                frames.append(self.q.get(timeout=0.2))
            except queue.Empty:
                pass
        return np.concatenate(frames) if frames else np.zeros(0, dtype=np.int16)

    # ---- speech to text -------------------------------------------------
    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) < RATE * 0.3:
            return ""
        segs, _ = self.whisper.transcribe(
            audio.astype(np.float32) / 32768.0, language="en", beam_size=1,
        )
        return " ".join(s.text.strip() for s in segs).strip()

    # ---- the main loop: yields one utterance at a time -----------------
    def utterances(self):
        """Yield dicts: {trigger, text, record_s, stt_s, released_at}."""
        while True:
            f = self.q.get()
            if self.space_down.is_set():
                trigger = "space"
                face.set_state("listening")
                speaker.chime()
                audio = self.record_while_space()
            elif self.heard_wake(f):
                trigger = "wake"
                face.set_state("listening")
                speaker.chime()
                self.drain()  # don't record the chime itself
                audio = self.record_until_silence()
            else:
                continue
            released = time.perf_counter()
            face.set_state("thinking")
            text = self.transcribe(audio)
            stt_s = time.perf_counter() - released
            self.wake.reset()
            self.drain()
            log.info("heard (%s, recorded %.1fs, stt %.2fs): %r", trigger, len(audio) / RATE, stt_s, text)
            yield {"trigger": trigger, "text": text, "record_s": len(audio) / RATE,
                   "stt_s": stt_s, "released_at": released}
