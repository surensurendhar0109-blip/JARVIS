"""Tiny JSON persistence for notes, tasks, reminders, contacts and facts."""
import json
import threading

from .config import DATA_DIR

_lock = threading.Lock()


def load(name, default):
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(name, data):
    with _lock:
        (DATA_DIR / f"{name}.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
