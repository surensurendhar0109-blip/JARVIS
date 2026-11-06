"""Central configuration, read from the environment / .env file."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional at import time
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def _get(name, default=""):
    return os.getenv(name, default) or default


ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
MODEL = _get("JARVIS_MODEL", "claude-sonnet-5-5")

USER_NAME = _get("JARVIS_USER_NAME", "sir")
WAKE_WORD = _get("JARVIS_WAKE_WORD", "jarvis").lower()
WAKE_VARIANTS = {WAKE_WORD, "jervis", "jarves", "jarvis"}
CITY = _get("JARVIS_CITY", "Chennai")
NEWS_REGION = _get("JARVIS_NEWS_REGION", "IN")
SPEECH_LANG = _get("JARVIS_SPEECH_LANG", "en-IN")
VOICE_RATE = int(_get("JARVIS_VOICE_RATE", "185"))
MUSIC_DIR = Path(_get("JARVIS_MUSIC_DIR", str(Path.home() / "Music")))

EMAIL_ADDRESS = _get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = _get("EMAIL_APP_PASSWORD")
SMTP_HOST = _get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_get("SMTP_PORT", "465"))
