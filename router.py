"""Skill registry. A skill is a function (match, ctx) -> str | None.

Returning None means "not for me" and routing continues, so broad patterns are
safe. If no skill answers, the request falls through to the Claude brain.
"""
import re

_SKILLS = []


def skill(*patterns):
    def deco(fn):
        for p in patterns:
            _SKILLS.append((re.compile(p, re.I), fn))
        return fn
    return deco


def dispatch(text, ctx):
    for rx, fn in _SKILLS:
        m = rx.search(text)
        if not m:
            continue
        try:
            result = fn(m, ctx)
        except Exception as e:
            return f"I hit a problem running that: {e}"
        if result is not None:
            return result
    return None


def first_group(m):
    """First non-empty capture group (for skills registered with several patterns)."""
    return next((g for g in m.groups() if g), "").strip()
