"""Skill loader. Import order = routing priority (first match wins)."""


def load_all():
    from . import (productivity, files, system, media, comms, web, vision, meta)  # noqa: F401
