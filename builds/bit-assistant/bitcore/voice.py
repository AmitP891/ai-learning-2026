"""Bit's voice: ElevenLabs (cloned voice), streamed. Falls back to macOS `say`."""
import subprocess
import tempfile
import time
import wave

import numpy as np
import requests

from . import face, speaker
from .config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID, log

RATE = 22050
_http = requests.Session()  # keep-alive: saves a TLS handshake (~0.1-0.3 s) on every reply


def warm():
    """Open the connection to ElevenLabs ahead of the first reply (no API call, no cost)."""
    try:
        _http.head("https://api.elevenlabs.io/", timeout=5)
    except requests.RequestException:
        pass


def speak(text: str) -> dict:
    """Say `text` out loud. Returns timing info: first_sound_s, engine."""
    t0 = time.perf_counter()
    try:
        first = _speak_elevenlabs(text, t0)
        return {"engine": "elevenlabs", "first_sound_s": first}
    except Exception as e:  # never die on camera
        log.warning("elevenlabs failed (%s), using say", e)
        print(f"[voice] ElevenLabs failed ({e}); falling back to macOS say")
        first = _speak_say(text, t0)
        return {"engine": "say", "first_sound_s": first}


def _speak_elevenlabs(text, t0):
    if not (ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID):
        raise RuntimeError("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID missing")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    r = _http.post(
        url,
        params={"output_format": f"pcm_{RATE}", "optimize_streaming_latency": 2},
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        json={"text": text, "model_id": ELEVENLABS_MODEL},
        stream=True,
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    out = None
    first = None
    try:
        for chunk in r.iter_content(chunk_size=4096):
            if not chunk:
                continue
            if out is None:
                out = speaker.PCMStream(RATE)
                first = time.perf_counter() - t0
                face.set_state("talking")
            out.write(chunk)
    finally:
        if out:
            out.close()
    if out is None:
        raise RuntimeError("no audio returned")
    log.info("voice: elevenlabs first sound %.2fs: %r", first, text)
    return first


def _speak_say(text, t0):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(
            ["say", "-o", f.name, "--file-format=WAVE", f"--data-format=LEI16@{RATE}", text],
            check=True,
        )
        with wave.open(f.name) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            rate = w.getframerate()
    first = time.perf_counter() - t0
    face.set_state("talking")
    speaker.play(pcm, rate, mouth=True)
    log.info("voice: say first sound %.2fs: %r", first, text)
    return first
