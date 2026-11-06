"""Music and video control."""
import os
import platform
import random
import subprocess
import urllib.parse
import webbrowser

from .. import config
from ..router import skill

AUDIO = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


@skill(r"^(?:pause|resume|stop)(?: the)?(?: music| song| video| playback| track)?$", r"^play$", r"^play/pause$")
def play_pause(m, ctx):
    import pyautogui
    pyautogui.press("playpause")
    return "Done."


@skill(r"\b(?:next|skip)(?: the)?(?: song| track)?$")
def next_track(m, ctx):
    import pyautogui
    pyautogui.press("nexttrack")
    return "Skipping."


@skill(r"\b(?:previous|last|go back)(?: song| track)$")
def prev_track(m, ctx):
    import pyautogui
    pyautogui.press("prevtrack")
    return "Going back."


@skill(r"^play (?:some |my )?(?:local )?(?:music|songs)(?: from (?:my )?(?:computer|library|laptop))?$")
def local_music(m, ctx):
    if not config.MUSIC_DIR.exists():
        return "I can't find your music folder. Set JARVIS music dir in the dot env file."
    songs = [os.path.join(r, f) for r, _, fs in os.walk(config.MUSIC_DIR) for f in fs if f.lower().endswith(AUDIO)]
    if not songs:
        return "There's no music in your music folder."
    song = random.choice(songs)
    system = platform.system()
    if system == "Windows":
        os.startfile(song)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", song])
    else:
        subprocess.Popen(["xdg-open", song])
    return f"Playing {os.path.splitext(os.path.basename(song))[0]}."


@skill(r"^search youtube for (.+)")
def yt_search(m, ctx):
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(m.group(1)))
    return f"Searching YouTube for {m.group(1)}."


@skill(r"^play (.+?)(?: on youtube)?$")
def play_youtube(m, ctx):
    query = m.group(1)
    try:
        import pywhatkit
        pywhatkit.playonyt(query)
    except Exception:
        webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query))
    return f"Playing {query}."
