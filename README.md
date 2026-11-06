# J.A.R.V.I.S.

A voice-controlled personal assistant for your computer. Claude is the brain; Python skills are the hands.
Say **"Jarvis, ..."** and watch the arc-reactor HUD respond.

## Features

| Area | Examples |
|---|---|
| Conversation | Ask anything; keeps context, spoken-style replies (Claude) |
| Time & info | "what time is it", "weather in London", "latest news", "news about cricket" |
| Briefing | "good morning" -> date, weather, headlines, tasks, reminders |
| Timers & reminders | "set a timer for 10 minutes", "remind me to call mom at 6 pm" (survive restarts) |
| Notes, tasks, memory | "take a note that...", "add milk to my to-do list", "remember that my locker code is..." |
| System | CPU/RAM/battery, volume, mute, brightness, screenshot, lock, shutdown/restart/sleep (with confirmation) |
| Apps & web | "open chrome", "open github", "close notepad", "google python tutorials", "wikipedia Alan Turing" |
| Media | "play Believer", "search youtube for lofi", "pause", "next song", "play some music" (local folder) |
| Messaging | "whatsapp mom saying I'm late", "send an email to dad saying..." (confirmation first) |
| Utilities | calculator ("20 percent of 150"), currency ("convert 100 usd to inr"), dictionary, jokes, IP address, clipboard, dictation ("type hello") |
| Files | "open downloads", "find file resume" |
| Vision | "what's on my screen", "what do you see" (webcam) |

## Setup

```bash
git clone https://github.com/surensurendhar0109-blip/JARVIS.git
cd JARVIS
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then add your ANTHROPIC_API_KEY
python main.py
```

PyAudio tips: Windows `pip install pipwin && pipwin install pyaudio`; macOS `brew install portaudio`;
Linux `sudo apt install portaudio19-dev python3-tk espeak`.

## Run modes

```
python main.py            voice + HUD (type commands in the HUD box too)
python main.py --no-gui   voice in the terminal
python main.py --text     keyboard only (no mic needed)
python main.py --no-wake  always listening, no wake word
```

Say "goodbye" to quit. Without an API key, built-in commands still work; open-ended chat and vision need the key.

## Contacts for messaging

Say "add contact mom phone +919876543210" or "add contact dad email dad@example.com".
Email needs `EMAIL_ADDRESS` and an app password in `.env`.

## Add your own skill

Create a function in any file under `jarvis/skills/` (and list the module in `skills/__init__.py`):

```python
from ..router import skill

@skill(r"^flip a coin$")
def coin(m, ctx):
    import random
    return random.choice(["Heads.", "Tails."])
```

Return a string to speak, or `None` to pass on to the next skill / Claude. `ctx.say()`, `ctx.confirm()` and `ctx.brain` are available.

## Layout

```
main.py            entry point
jarvis/core.py     listen -> route -> speak loop
jarvis/brain.py    Claude API, memory, vision
jarvis/speech.py   speech recognition + TTS
jarvis/hud.py      tkinter arc-reactor window
jarvis/router.py   skill registry
jarvis/skills/     productivity, files, system, media, comms, web, vision, meta
tests/             python -m unittest
```

## Notes
- Speech recognition uses Google's free web recogniser, so it needs internet.
- Volume keys and window control vary by OS; Windows is best covered, macOS and Linux have fallbacks.
- Your `.env` and `data/` (notes, contacts, reminders) are git-ignored.
