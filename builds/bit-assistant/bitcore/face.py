"""Bit's face: a local web page (face/index.html) driven over a WebSocket.

    face.start()            # serve http://localhost:8765 (page + Bit's SVG + /ws)
    face.set_state("listening" | "thinking" | "talking" | "idle")
    face.mic(int16_block)   # listening sound bars
    face.MouthTrack(rate)   # talking: loudness 30x a second, timed to playback

Everything is local (127.0.0.1 only). If the face isn't started, every call is a no-op.
"""
import asyncio
import json
import os
import threading
import time

import numpy as np

from .config import ROOT, log

PORT = int(os.getenv("BIT_FACE_PORT", "8765"))
FPS = 30
# extra delay for the mouth, e.g. ~200 ms for a Bluetooth speaker that buffers audio
AV_OFFSET_S = float(os.getenv("BIT_AV_OFFSET_MS", "0")) / 1000
PAGE = ROOT / "face" / "index.html"
BIT_SVG = ROOT.parent.parent / "brand" / "bit" / "bit.svg"
STATES = ("idle", "listening", "thinking", "talking")

_loop: asyncio.AbstractEventLoop | None = None
_clients: set = set()
_state = "idle"


def url() -> str:
    return f"http://localhost:{PORT}/"


def running() -> bool:
    return _loop is not None


def start():
    """Start the face server in a background thread (idempotent)."""
    global _loop
    if _loop:
        return
    ready = threading.Event()
    err: list[BaseException] = []

    def run():
        global _loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_serve_forever(loop, ready))
        except BaseException as e:  # port in use etc.
            err.append(e)
            ready.set()

    threading.Thread(target=run, daemon=True, name="face").start()
    ready.wait(5)
    if err:
        raise RuntimeError(f"face server failed to start on port {PORT}: {err[0]}")
    log.info("face: serving %s", url())


async def _serve_forever(loop, ready):
    global _loop
    from websockets.asyncio.server import serve
    from websockets.datastructures import Headers
    from websockets.http11 import Response

    def http(conn, request):
        path = request.path.split("?")[0]
        if path == "/ws":
            return None  # let the WebSocket handshake continue
        files = {"/": (PAGE, "text/html; charset=utf-8"), "/bit.svg": (BIT_SVG, "image/svg+xml")}
        if path not in files:
            return conn.respond(404, "not found\n")
        f, ctype = files[path]
        body = f.read_bytes()  # read each time so edits show on reload
        return Response(200, "OK", Headers([("Content-Type", ctype), ("Cache-Control", "no-store"),
                                            ("Content-Length", str(len(body)))]), body)

    async def handler(ws):
        _clients.add(ws)
        try:
            await ws.send(json.dumps({"type": "state", "state": _state}))
            async for _ in ws:  # the page never sends anything we need
                pass
        finally:
            _clients.discard(ws)

    async with serve(handler, "127.0.0.1", PORT, process_request=http):
        _loop = loop
        ready.set()
        await asyncio.Future()


def _send(msg: dict):
    if not _loop:
        return
    from websockets.asyncio.server import broadcast
    data = json.dumps(msg)
    _loop.call_soon_threadsafe(lambda: broadcast(set(_clients), data))


def set_state(state: str):
    global _state
    assert state in STATES, state
    if state != _state:
        _state = state
        log.info("face: %s", state)
    _send({"type": "state", "state": state})


def state() -> str:
    return _state


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x.astype(np.float32) / 32768.0) ** 2))) if len(x) else 0.0


_mic_peak = 0.05


def mic(block: np.ndarray):
    """Mic loudness for the listening sound bars (call from the audio callback)."""
    global _mic_peak
    if not _loop or _state != "listening":
        return
    r = _rms(block)
    _mic_peak = max(0.03, r, _mic_peak * 0.97)
    _send({"type": "mic", "v": round(min(1.0, max(0.0, (r - 0.004) / _mic_peak)), 3)})


class MouthTrack:
    """Turns PCM being played into mouth openness, 30 values a second, each sent
    at the moment that slice of audio comes out of the speaker.

    Same idea as the video build scripts (RMS per 1/30 s, minus a noise floor,
    divided by a loud reference), but live: the reference is a decaying peak.
    """

    def __init__(self, rate: int, output_latency: float = 0.0):
        self.rate = rate
        self.hop = rate // FPS
        self.latency = output_latency + AV_OFFSET_S
        self.carry = np.zeros(0, dtype=np.int16)
        self.t_next = None  # monotonic time the next written sample will be heard
        self.peak = 0.08

    def feed(self, pcm: np.ndarray):
        """Call right before writing `pcm` (int16 mono) to the output stream."""
        if not _loop:
            return
        now = time.monotonic()
        # after a network stall the buffer ran dry: new audio is heard 'latency' from now
        self.t_next = max(self.t_next or 0.0, now + self.latency)
        data = np.concatenate([self.carry, pcm])
        n = len(data) // self.hop
        t0 = self.t_next - len(self.carry) / self.rate
        frames = []
        for i in range(n):
            r = _rms(data[i * self.hop:(i + 1) * self.hop])
            self.peak = max(r, self.peak * 0.995, 0.06)
            level = min(1.0, max(0.0, (r - 0.01) / (0.8 * self.peak - 0.01)))
            frames.append((t0 + i / FPS, round(level, 3)))
        self.carry = data[n * self.hop:]
        self.t_next += len(pcm) / self.rate
        _loop.call_soon_threadsafe(self._schedule, frames)

    def end(self):
        """Close the mouth once the last audio has been heard."""
        if _loop and self.t_next:
            _loop.call_soon_threadsafe(self._schedule, [(self.t_next, 0.0)])

    def _schedule(self, frames):
        loop = asyncio.get_running_loop()
        # loop.time() is time.monotonic() on macOS, so the clocks match
        for t, v in frames:
            loop.call_at(t, _send, {"type": "mouth", "v": v})
