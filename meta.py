"""About Jarvis, help, resets, small talk shortcuts."""
from ..router import skill

CAPABILITIES = (
    "I can tell you the time, weather and news; set timers, alarms and reminders; keep notes and a task list; "
    "open apps and websites; control volume, brightness and power; take screenshots; play music and YouTube; "
    "send WhatsApp messages and emails; search the web and Wikipedia; convert currency and do maths; "
    "describe your screen or camera; and chat about anything else using Claude."
)


@skill(r"\bwho are you\b", r"\bwhat can you do\b", r"^help$", r"\bcapabilities\b")
def about(m, ctx):
    return "I'm JARVIS, your personal assistant. " + CAPABILITIES


@skill(r"\b(?:reset|clear) (?:the )?conversation\b", r"\bnew conversation\b")
def reset(m, ctx):
    ctx.brain.reset()
    return "Conversation cleared."


@skill(r"^(?:thanks|thank you)(?: jarvis)?$")
def thanks(m, ctx):
    return "My pleasure."
