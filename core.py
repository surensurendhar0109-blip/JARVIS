"""The Jarvis runtime: listen -> route -> speak."""
import datetime
import queue
import re
import threading
import time

from . import config, router
from .brain import Brain

EXIT = re.compile(r"^(?:exit|quit|goodbye|good bye|bye|shut ?down jarvis|power down|that'?s all|go to sleep)\b")
YES = ("yes", "yeah", "yep", "sure", "confirm", "do it", "proceed", "go ahead", "affirmative", "please do")


class Jarvis:
    def __init__(self, text_mode=False, hud=None, require_wake=True):
        self.hud = hud
        self.text_mode = text_mode
        self.require_wake = require_wake and not text_mode
        self.brain = Brain()
        self.typed = queue.Queue()
        self.stop = threading.Event()
        self.awake_until = 0.0
        self._say_lock = threading.Lock()
        self.speech = None

        if not text_mode:
            try:
                from .speech import Speech
                self.speech = Speech()
            except Exception as e:
                print(f"[voice unavailable: {e}] Falling back to text mode.")
                self.text_mode = True
                self.require_wake = False

        from .skills import load_all
        load_all()

    # ---------- I/O ----------
    def state(self, s):
        if self.hud:
            self.hud.set_state(s)

    def say(self, text):
        with self._say_lock:
            print(f"JARVIS> {text}")
            if self.hud:
                self.hud.log("jarvis", text)
            if self.speech:
                self.state("speaking")
                self.speech.say(text)
            self.state("idle")

    def confirm(self, prompt):
        self.say(prompt)
        if self.text_mode:
            return input("(yes/no)> ").strip().lower() in YES
        answer = self.speech.listen(timeout=6) if self.speech else ""
        return any(w in answer.lower() for w in YES)

    # ---------- text handling ----------
    def normalize(self, raw):
        t = raw.lower().strip()
        t = re.sub(r"\b(?:hey|ok|okay|hi|hello)?\s*(?:%s)\b[,]?" % "|".join(config.WAKE_VARIANTS), "", t).strip()
        t = re.sub(r"\bplease\b", "", t)
        return re.sub(r"\s+", " ", t).strip(" .,!?")

    def handle(self, raw):
        """Process one command. Returns False when it's time to quit."""
        text = self.normalize(raw)
        if not text:
            return True
        if self.hud:
            self.hud.log("you", raw)
        if EXIT.search(text):
            self.say(f"Powering down. Goodbye, {config.USER_NAME}.")
            return False
        self.state("thinking")
        reply = router.dispatch(text, self)
        if reply is None:
            reply = self.brain.ask(raw)
        self.say(reply)
        return True

    # ---------- main loop ----------
    def greeting(self):
        h = datetime.datetime.now().hour
        part = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        msg = f"Good {part}, {config.USER_NAME}. All systems online."
        if not self.brain.online:
            msg += " My language core is offline, so I'll stick to built-in commands."
        return msg

    def _next_input(self):
        try:
            return self.typed.get_nowait()
        except queue.Empty:
            pass
        awake = time.time() < self.awake_until
        self.state("listening" if (awake or not self.require_wake) else "idle")
        heard = self.speech.listen()
        if not heard:
            return ""
        low = heard.lower()
        if not self.require_wake or awake:
            self.awake_until = time.time() + 15
            return heard
        hit = next((w for w in config.WAKE_VARIANTS if w in low), None)
        if not hit:
            return ""
        cmd = low.split(hit, 1)[1].strip(" ,.")
        if not cmd:
            self.say("Yes?")
            self.state("listening")
            cmd = self.speech.listen(timeout=8)
        self.awake_until = time.time() + 15
        return cmd

    def run(self):
        from .skills import productivity
        productivity.restore(self)
        self.say(self.greeting())
        while not self.stop.is_set():
            try:
                raw = input("you> ").strip() if self.text_mode and not self.hud else self._next_input()
            except (EOFError, KeyboardInterrupt):
                break
            if not raw:
                continue
            if not self.handle(raw):
                break
        self.shutdown()

    def shutdown(self):
        self.stop.set()
        if self.hud:
            self.hud.close()
