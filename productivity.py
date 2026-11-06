"""Timers, alarms, reminders, notes, to-dos, long-term facts, daily briefing."""
import datetime
import re
import threading
import time

from .. import config, store
from ..router import skill, first_group

_UNITS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600, "day": 86400}
_NUM = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30}
_DUR = re.compile(
    r"(\d+(?:\.\d+)?|%s)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)\b" % "|".join(_NUM), re.I)
_CLOCK = re.compile(r"\b(?:at|for)\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?", re.I)


def parse_duration(text):
    """'in 5 minutes and 30 seconds' -> 330. None if no duration present."""
    t = text.lower()
    if re.search(r"half an? hour", t):
        return 1800
    total, found = 0.0, False
    for m in _DUR.finditer(t):
        n = m.group(1)
        n = float(n) if n[0].isdigit() else _NUM[n]
        total += n * _UNITS[m.group(2).rstrip("s")]
        found = True
    return int(total) if found else None


def parse_clock(text):
    """'at 6:30 pm' -> seconds from now until the next 6:30 pm."""
    m = _CLOCK.search(text)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    ap = (m.group(3) or "").lower().replace(".", "")
    if h > 23 or mi > 59:
        return None
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    now = datetime.datetime.now()
    candidates = [h] if (ap or h >= 12) else [h, h + 12]
    waits = []
    for hh in candidates:
        due = now.replace(hour=hh % 24, minute=mi, second=0, microsecond=0)
        if due <= now:
            due += datetime.timedelta(days=1)
        waits.append(int((due - now).total_seconds()))
    return min(waits)


def _fmt(seconds):
    seconds = int(seconds)
    parts = []
    for name, size in (("hour", 3600), ("minute", 60), ("second", 1)):
        n, seconds = divmod(seconds, size)
        if n:
            parts.append(f"{n} {name}{'s' if n != 1 else ''}")
    return " and ".join(parts) or "0 seconds"


# ---------------------------------------------------------------- reminders
def _fire(ctx, rid, text):
    store.save("reminders", [r for r in store.load("reminders", []) if r["id"] != rid])
    ctx.say(f"{config.USER_NAME}, {text}")


def schedule(ctx, text, delay, rid=None, persist=True):
    due = time.time() + delay
    rid = rid or str(int(due * 1000))
    if persist:
        items = store.load("reminders", [])
        items.append({"id": rid, "text": text, "due": due})
        store.save("reminders", items)
    t = threading.Timer(delay, _fire, (ctx, rid, text))
    t.daemon = True
    t.start()


def restore(ctx):
    """Re-arm reminders that were saved before the last shutdown."""
    for r in store.load("reminders", []):
        schedule(ctx, r["text"], max(r["due"] - time.time(), 2), r["id"], persist=False)


def _strip_time(text):
    t = _DUR.sub("", text)
    t = re.sub(r"half an? hour", "", t, flags=re.I)
    t = _CLOCK.sub("", t)
    t = re.sub(r"\b(?:in|after|remind me|to|about|that)\b", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" ,.")


@skill(r"\b(?:set|start|create)\b.*\b(?:timer|alarm)\b", r"\btimer for\b", r"\balarm (?:at|for)\b")
def timer(m, ctx):
    text = m.string
    delay = parse_duration(text) or parse_clock(text)
    if not delay:
        return "For how long should I set it?"
    kind = "Alarm" if "alarm" in text else "Timer"
    schedule(ctx, f"your {kind.lower()} is up.", delay)
    return f"{kind} set for {_fmt(delay)} from now."


@skill(r"\bremind me\b")
def reminder(m, ctx):
    text = m.string
    delay = parse_duration(text) or parse_clock(text)
    task = _strip_time(text)
    if not delay:
        return "When should I remind you?"
    if not task:
        task = "this is your reminder"
    schedule(ctx, f"reminder: {task}.", delay)
    return f"Understood. I'll remind you in {_fmt(delay)}."


@skill(r"\b(?:list|show|what are) (?:my )?(?:reminders|timers|alarms)\b")
def list_reminders(m, ctx):
    items = store.load("reminders", [])
    if not items:
        return "You have no pending reminders."
    parts = [f"{r['text']} in {_fmt(r['due'] - time.time())}" for r in items if r["due"] > time.time()]
    return "Pending: " + "; ".join(parts) if parts else "You have no pending reminders."


# ---------------------------------------------------------------- notes
@skill(r"\b(?:take|make|add|write(?: down)?|save) (?:a )?note(?: that| about| saying)?:? (.+)")
def add_note(m, ctx):
    notes = store.load("notes", [])
    notes.append({"text": m.group(1), "at": datetime.datetime.now().isoformat(timespec="minutes")})
    store.save("notes", notes)
    return "Noted."


@skill(r"\b(?:read|show|what are) (?:me )?(?:my )?notes\b")
def read_notes(m, ctx):
    notes = store.load("notes", [])
    if not notes:
        return "You have no notes."
    return "Your notes: " + ". ".join(n["text"] for n in notes[-8:])


@skill(r"\b(?:clear|delete) (?:all )?(?:my )?notes\b")
def clear_notes(m, ctx):
    store.save("notes", [])
    return "All notes cleared."


# ---------------------------------------------------------------- to-do
@skill(r"\badd (.+?) to (?:my )?(?:to-?do|task|tasks)(?: list)?\b")
def todo_add(m, ctx):
    items = store.load("todos", [])
    items.append({"text": m.group(1), "done": False})
    store.save("todos", items)
    return f"Added {m.group(1)} to your list."


@skill(r"\b(?:show|read|list|what'?s on|what is on)\b.*\b(?:to-?do|tasks?)\b")
def todo_list(m, ctx):
    items = [t["text"] for t in store.load("todos", []) if not t["done"]]
    if not items:
        return "Your task list is empty."
    return f"You have {len(items)} open tasks: " + ", ".join(items)


@skill(r"\b(?:complete|finish|remove) task (.+)", r"\bmark (.+?) (?:as )?(?:done|complete|completed)\b")
def todo_done(m, ctx):
    target = first_group(m)
    items = store.load("todos", [])
    for t in items:
        if not t["done"] and target in t["text"].lower():
            t["done"] = True
            store.save("todos", items)
            return f"Marked {t['text']} as done."
    return f"I couldn't find a task matching {target}."


# ---------------------------------------------------------------- long-term memory
@skill(r"\bremember that (.+)")
def remember(m, ctx):
    facts = store.load("facts", [])
    facts.append(m.group(1))
    store.save("facts", facts)
    return "I'll remember that."


@skill(r"\bwhat do you (?:remember|know about me)\b")
def recall(m, ctx):
    facts = store.load("facts", [])
    return ("Here's what I remember: " + ". ".join(facts)) if facts else "You haven't asked me to remember anything yet."


@skill(r"\bforget everything\b")
def forget(m, ctx):
    store.save("facts", [])
    ctx.brain.reset()
    return "Memory wiped."


# ---------------------------------------------------------------- briefing
@skill(r"\b(?:good morning|morning briefing|daily briefing|brief me|daily brief)\b")
def briefing(m, ctx):
    from . import web
    now = datetime.datetime.now()
    parts = [f"Good morning, {config.USER_NAME}. It's {now:%A, %d %B}, {now.strftime('%I:%M %p').lstrip('0')}."]
    for label, fn in (("weather", web.get_weather), ("headlines", lambda: "Top stories: " + "; ".join(web.get_headlines(3)))):
        try:
            parts.append(fn())
        except Exception:
            parts.append(f"I couldn't fetch the {label}.")
    todos = [t["text"] for t in store.load("todos", []) if not t["done"]]
    if todos:
        parts.append(f"You have {len(todos)} open tasks, starting with {todos[0]}.")
    pending = [r for r in store.load("reminders", []) if r["due"] > time.time()]
    if pending:
        parts.append(f"{len(pending)} reminders are pending.")
    return " ".join(parts)
