"""All settings come from .env (never committed)."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")

# Output device for Bit's voice, matched by (part of) its name, e.g. "JBL Go".
BIT_AUDIO_DEVICE = os.getenv("BIT_AUDIO_DEVICE", "")
# Mic, matched by name. Empty = system default input.
BIT_MIC_DEVICE = os.getenv("BIT_MIC_DEVICE", "")

# Wake word. Default: Bit's own "hey bit" model (trained by wakeword/train_hey_bit.py).
# To switch back, set WAKE_MODEL=hey_jarvis in .env (or another built-in openWakeWord name).
HEY_BIT_MODEL = "models/hey_bit.onnx"
_default_wake = HEY_BIT_MODEL if (ROOT / HEY_BIT_MODEL).exists() else "hey_jarvis"
WAKE_MODEL = os.getenv("WAKE_MODEL", _default_wake)
WAKE_NAME = Path(WAKE_MODEL).stem.replace("_", " ")  # "hey bit", "hey jarvis"
# 0.85 for hey_bit (tested: 100% caught, fewest sound-alikes); 0.5 suits the built-in models
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.85" if WAKE_MODEL == HEY_BIT_MODEL else "0.5"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")

LOG_DIR = ROOT / "logs"
NOTES_DIR = ROOT / "notes"
LOG_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "bit.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bit")
