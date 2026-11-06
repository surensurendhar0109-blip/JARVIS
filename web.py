"""Weather, news, search, Wikipedia, dictionary, currency, jokes, calculator."""
import ast
import operator
import random
import re
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET

from .. import config
from ..router import skill

WMO = {0: "clear skies", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
       51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain",
       65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
       81: "rain showers", 82: "violent showers", 95: "thunderstorms", 96: "thunderstorms with hail",
       99: "thunderstorms with hail"}


def _get(url, **kw):
    import requests
    r = requests.get(url, timeout=10, headers={"User-Agent": "JARVIS/1.0"}, **kw)
    r.raise_for_status()
    return r


# ------------------------------------------------------------ weather
def get_weather(city=None):
    city = city or config.CITY
    geo = _get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}).json()
    if not geo.get("results"):
        return f"I couldn't find a place called {city}."
    p = geo["results"][0]
    w = _get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": p["latitude"], "longitude": p["longitude"], "timezone": "auto", "forecast_days": 1,
        "current": "temperature_2m,apparent_temperature,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max"}).json()
    c, d = w["current"], w["daily"]
    return (f"In {p['name']} it's {c['temperature_2m']:.0f} degrees with {WMO.get(c['weather_code'], 'mixed conditions')}, "
            f"feeling like {c['apparent_temperature']:.0f}. Today's high is {d['temperature_2m_max'][0]:.0f}, "
            f"low {d['temperature_2m_min'][0]:.0f}, with a {d['precipitation_probability_max'][0] or 0} percent chance of rain.")


@skill(r"\b(?:weather|temperature|forecast)\b")
def weather(m, ctx):
    mm = re.search(r"\bin ([a-z .]+?)(?: today| now| right now| tonight| tomorrow)?$", m.string)
    return get_weather(mm.group(1).strip() if mm else None)


# ------------------------------------------------------------ news
def get_headlines(n=5, topic=None):
    r, reg = config.NEWS_REGION, config.NEWS_REGION
    tail = f"hl=en-{r}&gl={reg}&ceid={reg}:en"
    url = (f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(topic)}&{tail}" if topic
           else f"https://news.google.com/rss?{tail}")
    root = ET.fromstring(_get(url).content)
    titles = [t.text.rsplit(" - ", 1)[0] for t in root.findall(".//item/title") if t.text]
    return titles[:n]


@skill(r"\b(?:news|headlines)\b(?: (?:about|on|for) (.+))?")
def news(m, ctx):
    topic = m.group(1)
    titles = get_headlines(5, topic)
    if not titles:
        return "I found no headlines."
    return "Here are the top stories. " + ". ".join(titles) + "."


# ------------------------------------------------------------ search / lookup
@skill(r"^(?:google|search(?: google)?(?: for)?|look up|search for) (.+)")
def google(m, ctx):
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(m.group(1)))
    return f"Searching for {m.group(1)}."


@skill(r"^(?:wikipedia|search wikipedia for|wikipedia search) (.+)")
def wikipedia(m, ctx):
    q = m.group(1)
    hits = _get("https://en.wikipedia.org/w/api.php", params={
        "action": "opensearch", "search": q, "limit": 1, "format": "json"}).json()
    if not hits[1]:
        return f"Wikipedia has nothing on {q}."
    s = _get("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(hits[1][0])).json()
    sentences = re.split(r"(?<=[.!?])\s+", s.get("extract", ""))
    return " ".join(sentences[:2]) or f"I found {hits[1][0]} but no summary."


@skill(r"^(?:define|definition of|meaning of) (\w+)$", r"\bwhat does (\w+) mean\b")
def define(m, ctx):
    word = m.group(1) or m.group(2)
    try:
        d = _get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()[0]
        meaning = d["meanings"][0]
        return f"{word}, {meaning['partOfSpeech']}: {meaning['definitions'][0]['definition']}"
    except Exception:
        return None  # let Claude answer


_CODES = {"dollar": "USD", "dollars": "USD", "rupee": "INR", "rupees": "INR", "euro": "EUR", "euros": "EUR",
          "pound": "GBP", "pounds": "GBP", "yen": "JPY", "dirham": "AED", "dirhams": "AED"}


@skill(r"\bconvert (\d+(?:\.\d+)?)\s*([a-z]+) (?:to|into|in) ([a-z]+)")
def currency(m, ctx):
    amount = float(m.group(1))
    a = _CODES.get(m.group(2), m.group(2).upper())
    b = _CODES.get(m.group(3), m.group(3).upper())
    if len(a) != 3 or len(b) != 3:
        return None
    data = _get(f"https://open.er-api.com/v6/latest/{a}").json()
    rate = data.get("rates", {}).get(b)
    if not rate:
        return f"I don't have a rate for {a} to {b}."
    return f"{amount:g} {a} is about {amount * rate:,.2f} {b}."


@skill(r"\bjoke\b")
def joke(m, ctx):
    try:
        import pyjokes
        return pyjokes.get_joke()
    except Exception:
        return random.choice([
            "There are 10 kinds of people: those who understand binary and those who don't.",
            "I would tell you a UDP joke, but you might not get it."])


# ------------------------------------------------------------ calculator
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(b) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](a, b)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported")


def calculate(text):
    """Return a numeric result for a spoken/typed expression, or None if it isn't maths."""
    t = text.lower().strip(" ?")
    t = re.sub(r"^(?:what(?:'s| is)|calculate|compute|how much is)\s+", "", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:percent|%) of (\d+(?:\.\d+)?)", r"(\1/100*\2)", t)
    t = re.sub(r"square root of (\d+(?:\.\d+)?)", r"(\1**0.5)", t)
    for word, sym in ((r"multiplied by|times", "*"), (r"divided by|over", "/"), (r"plus", "+"),
                      (r"minus", "-"), (r"to the power of|power", "**"), (r"\^", "**"), (r"\bx\b|×", "*"), ("÷", "/")):
        t = re.sub(word, sym, t)
    if not re.fullmatch(r"[\d\s\.\+\-\*/\(\)%]+", t) or not re.search(r"\d", t) or not re.search(r"[\+\-\*/%]", t):
        return None
    try:
        r = _eval(ast.parse(t.strip(), mode="eval"))
    except Exception:
        return None
    return int(r) if float(r).is_integer() else round(r, 6)


@skill(r"^(.+)$")
def maths(m, ctx):
    r = calculate(m.group(1))
    return None if r is None else f"That comes to {r}."
