"""Ears and mouth: speech recognition + text-to-speech."""
import threading

from . import config


class Speech:
    def __init__(self):
        import pyttsx3
        import speech_recognition as sr

        self.sr = sr
        self.rec = sr.Recognizer()
        self.rec.pause_threshold = 0.8
        self.rec.dynamic_energy_threshold = True
        if not sr.Microphone.list_microphone_names():
            raise RuntimeError("no microphone found")
        self.mic = sr.Microphone()
        with self.mic as src:
            self.rec.adjust_for_ambient_noise(src, duration=1)

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", config.VOICE_RATE)
        self._pick_voice()
        self._lock = threading.Lock()

    def _pick_voice(self):
        voices = self.engine.getProperty("voices") or []
        for v in voices:  # prefer an English male voice for the full effect
            name = (v.name or "").lower()
            if any(k in name for k in ("david", "daniel", "george", "male", "english")):
                self.engine.setProperty("voice", v.id)
                return

    def say(self, text):
        with self._lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def listen(self, timeout=5, phrase_limit=12):
        """Return recognised text, or '' if nothing intelligible was heard."""
        try:
            with self.mic as src:
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            return self.rec.recognize_google(audio, language=config.SPEECH_LANG).strip()
        except (self.sr.WaitTimeoutError, self.sr.UnknownValueError):
            return ""
        except self.sr.RequestError:
            print("[speech service unreachable - check your internet]")
            return ""
