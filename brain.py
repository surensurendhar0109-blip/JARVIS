"""The language core: Claude via the Anthropic API."""
import base64
import datetime

from . import config, store

SYSTEM = """You are J.A.R.V.I.S., a personal AI assistant running on the user's computer.
Personality: calm, razor-sharp, quietly witty, unfailingly loyal. Address the user as "{user}".
Your replies are SPOKEN ALOUD, so: 1-3 short sentences unless asked for more, plain prose only,
no markdown, no bullet points, no emojis, no URLs read out letter by letter.
If you don't know something or can't do it, say so briefly. Never invent facts.
Current date and time: {now}."""


class Brain:
    def __init__(self):
        self.client = None
        self.history = []
        if config.ANTHROPIC_API_KEY:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    @property
    def online(self):
        return self.client is not None

    def _system(self):
        s = SYSTEM.format(
            user=config.USER_NAME,
            now=datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p"),
        )
        facts = store.load("facts", [])
        if facts:
            s += "\nThings the user asked you to remember:\n" + "\n".join(f"- {f}" for f in facts)
        return s

    def _call(self, messages, max_tokens=400):
        r = self.client.messages.create(
            model=config.MODEL, max_tokens=max_tokens, system=self._system(), messages=messages
        )
        return "".join(b.text for b in r.content if b.type == "text").strip()

    def _trim(self):
        self.history = self.history[-20:]
        while self.history and self.history[0]["role"] != "user":
            self.history.pop(0)

    def ask(self, text):
        if not self.online:
            return "My language core is offline. Add your Anthropic API key to the dot env file."
        self.history.append({"role": "user", "content": text})
        self._trim()
        try:
            reply = self._call(self.history)
        except Exception as e:
            self.history.pop()
            return f"I couldn't reach my language core: {e}"
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def ask_image(self, png_bytes, question):
        if not self.online:
            return "Vision needs my language core. Add your Anthropic API key first."
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(png_bytes).decode()}},
            {"type": "text", "text": question},
        ]
        try:
            reply = self._call([{"role": "user", "content": content}], max_tokens=500)
        except Exception as e:
            return f"Vision failed: {e}"
        self.history.append({"role": "user", "content": f"[showed an image] {question}"})
        self.history.append({"role": "assistant", "content": reply})
        self._trim()
        return reply

    def reset(self):
        self.history.clear()
