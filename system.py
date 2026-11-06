"""Time, system stats, volume, brightness, apps, screenshots, power."""
import datetime
import os
import platform
import socket
import subprocess
import time
import webbrowser

from .. import config
from ..config import DATA_DIR
from ..router import skill

OS = platform.system()  # Windows / Darwin / Linux

SITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com",
    "gmail": "https://mail.google.com", "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com", "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com", "twitter": "https://x.com",
    "claude": "https://claude.ai", "maps": "https://maps.google.com",
    "netflix": "https://www.netflix.com", "spotify": "https://open.spotify.com",
    "drive": "https://drive.google.com", "calendar": "https://calendar.google.com",
}
APPS = {
    "notepad": {"Windows": "notepad", "Darwin": "TextEdit", "Linux": "gedit"},
    "calculator": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "chrome": {"Windows": "chrome", "Darwin": "Google Chrome", "Linux": "google-chrome"},
    "firefox": {"Windows": "firefox", "Darwin": "Firefox", "Linux": "firefox"},
    "vs code": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
    "terminal": {"Windows": "cmd", "Darwin": "Terminal", "Linux": "gnome-terminal"},
    "word": {"Windows": "winword", "Darwin": "Microsoft Word", "Linux": "libreoffice --writer"},
    "excel": {"Windows": "excel", "Darwin": "Microsoft Excel", "Linux": "libreoffice --calc"},
    "powerpoint": {"Windows": "powerpnt", "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice --impress"},
    "paint": {"Windows": "mspaint", "Darwin": "Preview", "Linux": "gimp"},
    "file explorer": {"Windows": "explorer", "Darwin": "Finder", "Linux": "nautilus"},
    "settings": {"Windows": "ms-settings:", "Darwin": "System Settings", "Linux": "gnome-control-center"},
    "task manager": {"Windows": "taskmgr", "Darwin": "Activity Monitor", "Linux": "gnome-system-monitor"},
}


def _launch(cmd):
    if OS == "Windows":
        subprocess.Popen(f'start "" "{cmd}"', shell=True)
    elif OS == "Darwin":
        subprocess.Popen(["open", "-a", cmd])
    else:
        subprocess.Popen(cmd.split())


# ------------------------------------------------------------ time / date
@skill(r"\bwhat(?:'s| is)? the time\b", r"\bwhat time is it\b", r"\bcurrent time\b", r"^time$", r"\btell me the time\b")
def tell_time(m, ctx):
    return f"It's {datetime.datetime.now().strftime('%I:%M %p').lstrip('0')}, {config.USER_NAME}."


@skill(r"\bwhat(?:'s| is) (?:the |today'?s )?date\b", r"\bwhat day is (?:it|today)\b", r"^date$")
def tell_date(m, ctx):
    return f"Today is {datetime.datetime.now():%A, %d %B %Y}."


# ------------------------------------------------------------ stats
@skill(r"\b(?:system (?:status|stats)|cpu|ram usage|memory usage|battery|disk space)\b")
def stats(m, ctx):
    import psutil
    parts = [f"CPU at {psutil.cpu_percent(interval=0.5):.0f} percent",
             f"memory at {psutil.virtual_memory().percent:.0f} percent",
             f"disk {psutil.disk_usage(os.path.abspath(os.sep)).percent:.0f} percent full"]
    b = psutil.sensors_battery()
    if b:
        parts.append(f"battery {b.percent:.0f} percent{', charging' if b.power_plugged else ''}")
    return ", ".join(parts) + "."


@skill(r"\b(?:my )?ip address\b")
def ip(m, ctx):
    import requests
    local = socket.gethostbyname(socket.gethostname())
    try:
        pub = requests.get("https://api.ipify.org", timeout=5).text
        return f"Local address {local}, public address {pub}."
    except Exception:
        return f"Local address {local}. I couldn't reach the internet for the public one."


# ------------------------------------------------------------ volume / brightness
def _volume(direction):
    if OS == "Darwin":
        delta = 10 if direction == "up" else -10
        subprocess.run(["osascript", "-e",
                        f"set volume output volume ((output volume of (get volume settings)) + {delta})"])
    else:
        import pyautogui
        for _ in range(5):
            pyautogui.press("volumeup" if direction == "up" else "volumedown")


@skill(r"\b(?:volume up|increase (?:the )?volume|louder|turn it up)\b")
def vol_up(m, ctx):
    _volume("up")
    return "Volume up."


@skill(r"\b(?:volume down|decrease (?:the )?volume|lower (?:the )?volume|quieter|turn it down)\b")
def vol_down(m, ctx):
    _volume("down")
    return "Volume down."


@skill(r"\b(?:mute|unmute)\b(?! mic)")
def mute(m, ctx):
    if OS == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output muted not (output muted of (get volume settings))"])
    else:
        import pyautogui
        pyautogui.press("volumemute")
    return "Done."


@skill(r"\bbrightness\b.*?\b(\d{1,3})\b", r"\b(increase|decrease|raise|lower) (?:the )?brightness\b")
def brightness(m, ctx):
    import screen_brightness_control as sbc
    g = m.group(1)
    if g.isdigit():
        level = max(0, min(100, int(g)))
    else:
        cur = sbc.get_brightness()[0]
        level = max(0, min(100, cur + (20 if g in ("increase", "raise") else -20)))
    sbc.set_brightness(level)
    return f"Brightness at {level} percent."


# ------------------------------------------------------------ screenshot / clipboard / typing
@skill(r"\b(?:take|capture) (?:a )?screenshot\b")
def screenshot(m, ctx):
    import pyautogui
    folder = DATA_DIR / "screenshots"
    folder.mkdir(exist_ok=True)
    path = folder / f"shot_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
    pyautogui.screenshot().save(path)
    return f"Screenshot saved as {path.name}."


@skill(r"\b(?:read|what'?s on|what is on) (?:my )?clipboard\b")
def clipboard(m, ctx):
    import pyperclip
    text = pyperclip.paste().strip()
    return f"Your clipboard says: {text[:300]}" if text else "Your clipboard is empty."


@skill(r"^type (.+)")
def type_text(m, ctx):
    import pyautogui
    ctx.say("Typing in three seconds. Click where you want the text.")
    time.sleep(3)
    pyautogui.write(m.group(1), interval=0.03)
    return "Done."


# ------------------------------------------------------------ apps
@skill(r"^(?:open|launch|start|run) (?:the )?(.+?)(?: app| application| website| site)?$")
def open_app(m, ctx):
    name = m.group(1).strip()
    if name in SITES:
        webbrowser.open(SITES[name])
        return f"Opening {name}."
    if name in APPS:
        _launch(APPS[name][OS])
        return f"Opening {name}."
    if "." in name and " " not in name:
        webbrowser.open(name if name.startswith("http") else f"https://{name}")
        return f"Opening {name}."
    try:
        _launch(name)
        return f"Trying to open {name}."
    except Exception:
        return f"I couldn't find an app called {name}."


@skill(r"^(?:close|kill) (?:the )?(.+?)(?: app| application)?$")
def close_app(m, ctx):
    import psutil
    name = m.group(1).strip()
    cmd = APPS.get(name, {}).get(OS, name).split()[0].lower().replace(".exe", "")
    procs = [p for p in psutil.process_iter(["name"]) if cmd in (p.info["name"] or "").lower()]
    if not procs:
        return f"I don't see {name} running."
    if not ctx.confirm(f"Close {name}? Unsaved work will be lost."):
        return "Cancelled."
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    return f"Closed {name}."


# ------------------------------------------------------------ power
def _power(action):
    cmds = {
        "Windows": {"shutdown": "shutdown /s /t 5", "restart": "shutdown /r /t 5",
                    "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "lock": "rundll32.exe user32.dll,LockWorkStation"},
        "Darwin": {"shutdown": "osascript -e 'tell app \"System Events\" to shut down'",
                   "restart": "osascript -e 'tell app \"System Events\" to restart'",
                   "sleep": "pmset sleepnow", "lock": "pmset displaysleepnow"},
        "Linux": {"shutdown": "systemctl poweroff", "restart": "systemctl reboot",
                  "sleep": "systemctl suspend", "lock": "loginctl lock-session"},
    }
    subprocess.Popen(cmds[OS][action], shell=True)


@skill(r"\block (?:the |my )?(?:screen|computer|pc|laptop)\b")
def lock(m, ctx):
    _power("lock")
    return "Locked."


@skill(r"\b(?:shut ?down|power off|turn off) (?:the |my )?(?:computer|pc|laptop|system)\b")
def shutdown(m, ctx):
    if ctx.confirm("Shall I shut the computer down?"):
        _power("shutdown")
        return "Shutting down."
    return "Cancelled."


@skill(r"\brestart (?:the |my )?(?:computer|pc|laptop|system)\b|\breboot\b")
def restart(m, ctx):
    if ctx.confirm("Shall I restart the computer?"):
        _power("restart")
        return "Restarting."
    return "Cancelled."


@skill(r"\b(?:sleep|hibernate) (?:the |my )?(?:computer|pc|laptop|system)\b")
def sleep_pc(m, ctx):
    if ctx.confirm("Put the computer to sleep?"):
        _power("sleep")
        return "Sleeping."
    return "Cancelled."
