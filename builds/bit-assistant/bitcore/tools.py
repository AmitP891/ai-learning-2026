"""Bit's hands: an allow-list of Mac actions. One function + one schema each.

Rules (from the brief): no free-form shell, no deleting, no messages/emails,
no purchases. Every call is logged to logs/bit.log. To add a tool later
(v2 list), write a function, add a schema to SCHEMAS, and register it in FUNCS.
"""
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path

import requests

from .config import NOTES_DIR, ROOT, log

REPO_ROOT = ROOT.parent.parent  # ~/ai-learning-2026

APPS = {  # spoken name -> macOS app name
    "Spotify": "Spotify",
    "Chrome": "Google Chrome",
    "VS Code": "Visual Studio Code",
    "Terminal": "Terminal",
    "Notes": "Notes",
    "Calendar": "Calendar",
}

BOOKMARKS = {
    "YouTube Studio": "https://studio.youtube.com",
    "GitHub repo": "https://github.com/AmitP891/ai-learning-2026",
    "vibewithamit.com": "https://vibewithamit.com",
    "content plan": os.getenv("BIT_CONTENT_PLAN_URL", ""),
}

# Spotify playlists per mood; override in .env with BIT_PLAYLIST_CHILL etc.
PLAYLISTS = {
    "chill": os.getenv("BIT_PLAYLIST_CHILL", "spotify:playlist:37i9dQZF1DX4WYpdgoIcn6"),
    "focus": os.getenv("BIT_PLAYLIST_FOCUS", "spotify:playlist:37i9dQZF1DWZeKCadgRdKQ"),
    "happy": os.getenv("BIT_PLAYLIST_HAPPY", "spotify:playlist:37i9dQZF1DXdPec7aLTmlC"),
}

# "what's next": first unticked "- [ ]" line of this markdown file (override with BIT_CONTENT_PLAN)
CONTENT_PLAN_FILE = os.getenv("BIT_CONTENT_PLAN", "") or str(NOTES_DIR / "next.md")
HOME_CITY = os.getenv("BIT_HOME_CITY", "")


class ToolError(Exception):
    """A failure Bit should say out loud (sent back to Claude as is_error)."""


def _osascript(script: str, *args: str, timeout=20) -> str:
    """Run a fixed AppleScript. User text only ever goes in as argv, never into the script."""
    r = subprocess.run(["osascript", "-e", script, *args],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.strip()
        if "-1743" in err or "Not authorized" in err:
            raise ToolError("macOS hasn't given Bit Automation permission for that app yet "
                            "(System Settings > Privacy & Security > Automation).")
        raise ToolError(f"AppleScript failed: {err[:200]}")
    return r.stdout.strip()


def _open(*args: str):
    r = subprocess.run(["open", *args], capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise ToolError(r.stderr.strip()[:200] or "couldn't open it")


# ---- tools ----------------------------------------------------------------
def get_time() -> str:
    now = dt.datetime.now().astimezone()
    return now.strftime("%A %-d %B %Y, %H:%M (%Z)")


_CAL_SCRIPT = '''
on run argv
    set offsetDays to (item 1 of argv) as integer
    set d0 to current date
    set time of d0 to 0
    set d0 to d0 + offsetDays * days
    set d1 to d0 + 1 * days
    set out to {}
    tell application "Calendar"
        repeat with c in calendars
            set evs to (every event of c whose start date < d1 and end date > d0)
            repeat with e in evs
                set s to start date of e
                set end of out to ((s as «class isot» as string) & "|" & (allday event of e as string) & "|" & (summary of e))
            end repeat
        end repeat
    end tell
    set AppleScript's text item delimiters to linefeed
    return out as text
end run
'''


def get_calendar(day: str) -> str:
    offset = {"today": 0, "tomorrow": 1}[day]
    raw = _osascript(_CAL_SCRIPT, str(offset), timeout=30)
    events = []
    for line in filter(None, raw.splitlines()):
        start, allday, title = line.split("|", 2)
        when = "all day" if allday == "true" else start[11:16]
        events.append((when != "all day", start, f"{when} {title}"))
    if not events:
        return f"No events {day}."
    events.sort()
    return f"Events {day}:\n" + "\n".join(e[2] for e in events)


_REMINDER_SCRIPT = '''
on run argv
    set t to item 1 of argv
    set d to current date
    set year of d to (item 2 of argv) as integer
    set day of d to 1
    set month of d to (item 3 of argv) as integer
    set day of d to (item 4 of argv) as integer
    set hours of d to (item 5 of argv) as integer
    set minutes of d to (item 6 of argv) as integer
    set seconds of d to 0
    tell application "Reminders"
        make new reminder with properties {name:t, remind me date:d}
    end tell
    return "ok"
end run
'''


def add_reminder(text: str, time: str, day: str = "auto") -> str:
    try:
        hh, mm = (int(x) for x in time.split(":"))
        target_t = dt.time(hh, mm)
    except ValueError:
        raise ToolError(f"time must be HH:MM in 24-hour format, got {time!r}")
    now = dt.datetime.now()
    when = dt.datetime.combine(now.date(), target_t)
    if day == "tomorrow" or (day == "auto" and when <= now):
        when += dt.timedelta(days=1)
    _osascript(_REMINDER_SCRIPT, text, str(when.year), str(when.month), str(when.day),
               str(when.hour), str(when.minute))
    return f"Reminder added: '{text}' at {when:%H:%M on %A %-d %B}."


def open_app(name: str) -> str:
    app = APPS[name]
    _open("-a", app)
    return f"Opened {name}."


def play_music(mood: str) -> str:
    if subprocess.run(["open", "-Ra", "Spotify"], capture_output=True).returncode != 0:
        raise ToolError("Spotify isn't installed on this Mac.")
    _osascript('on run argv\ntell application "Spotify" to play track (item 1 of argv)\nend run',
               PLAYLISTS[mood])
    return f"Playing a {mood} playlist in Spotify."


def open_url(name: str) -> str:
    url = BOOKMARKS[name]
    if not url:
        raise ToolError(f"No link is set for '{name}' yet.")
    _open("-a", "Google Chrome", url)
    return f"Opened {name} in Chrome."


def add_note(text: str) -> str:
    path = NOTES_DIR / "bit-notes.md"
    if not path.exists():
        path.write_text("# Bit notes\n\n")
    with path.open("a") as f:
        f.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} {text.strip()}\n")
    return "Note saved."


_WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain",
        65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
        81: "rain showers", 82: "heavy showers", 95: "thunderstorms", 96: "thunderstorms with hail",
        99: "thunderstorms with hail"}


def get_weather(city: str = "") -> str:
    city = city.strip() or HOME_CITY
    if not city:
        raise ToolError("I don't know which city. Set BIT_HOME_CITY in .env or name a city.")
    g = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                     params={"name": city, "count": 1}, timeout=8).json()
    if not g.get("results"):
        raise ToolError(f"Couldn't find a place called {city}.")
    p = g["results"][0]
    w = requests.get("https://api.open-meteo.com/v1/forecast", timeout=8, params={
        "latitude": p["latitude"], "longitude": p["longitude"], "timezone": "auto",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 1,
    }).json()
    c, d = w["current"], w["daily"]
    return (f"{p['name']}, {p.get('country', '')}: {c['temperature_2m']:.0f}°C "
            f"(feels {c['apparent_temperature']:.0f}°C), {_WMO.get(c['weather_code'], 'mixed')}, "
            f"wind {c['wind_speed_10m']:.0f} km/h. Today {d['temperature_2m_min'][0]:.0f} to "
            f"{d['temperature_2m_max'][0]:.0f}°C, {d['precipitation_probability_max'][0]}% chance of rain.")


def _next_content_item() -> str:
    if not CONTENT_PLAN_FILE:
        return "No content plan is set."
    path = Path(CONTENT_PLAN_FILE).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        return f"Content plan file not found: {path.name}."
    for line in path.read_text().splitlines():
        if line.strip().startswith("- [ ]"):
            return "Next on the content plan: " + line.strip()[5:].strip()
    return "Everything on the content plan is ticked off."


def start_build_session() -> str:
    done, failed = [], []
    for label, fn in (("Terminal", lambda: _open("-a", "Terminal", str(REPO_ROOT))),
                      ("VS Code", lambda: _open("-a", "Visual Studio Code", str(REPO_ROOT))),
                      ("YouTube Studio", lambda: open_url("YouTube Studio"))):
        try:
            fn()
            done.append(label)
        except ToolError as e:
            failed.append(f"{label} ({e})")
    out = f"Opened {', '.join(done) or 'nothing'}."
    if failed:
        out += f" Failed: {'; '.join(failed)}."
    return out + " " + _next_content_item()


# ---- schemas (what Claude sees) -------------------------------------------
def _schema(name, description, props=None, required=None):
    return {"name": name, "description": description, "strict": True,
            "input_schema": {"type": "object", "properties": props or {},
                             "required": required or [], "additionalProperties": False}}


SCHEMAS = [
    _schema("get_time", "Current local time and date."),
    _schema("get_calendar", "Amit's calendar events for today or tomorrow.",
            {"day": {"type": "string", "enum": ["today", "tomorrow"]}}, ["day"]),
    _schema("add_reminder", "Add a reminder to Apple Reminders.",
            {"text": {"type": "string", "description": "What to be reminded about, short."},
             "time": {"type": "string", "description": "24-hour HH:MM. A bare hour from 1 to 11 "
                      "('at 7', 'at 7 o'clock') means the evening: 'at 7' -> '19:00'. Use a morning time "
                      "only if Amit says 'am' or 'morning'."},
             "day": {"type": "string", "enum": ["auto", "today", "tomorrow"],
                     "description": "Use 'auto' unless Amit says 'today' or 'tomorrow'. 'auto' = today, "
                     "or tomorrow if that time has already passed."}},
            ["text", "time", "day"]),
    _schema("open_app", "Open an app on the Mac (allow-list only).",
            {"name": {"type": "string", "enum": list(APPS)}}, ["name"]),
    _schema("play_music", "Play music in Spotify for a mood.",
            {"mood": {"type": "string", "enum": list(PLAYLISTS)}}, ["mood"]),
    _schema("open_url", "Open a saved bookmark in Chrome (only these names, never arbitrary URLs).",
            {"name": {"type": "string", "enum": list(BOOKMARKS)}}, ["name"]),
    _schema("add_note", "Append a dated note to Amit's Bit notes file.",
            {"text": {"type": "string"}}, ["text"]),
    _schema("get_weather", "Current weather and today's forecast. Empty city = Amit's home city.",
            {"city": {"type": "string"}}, ["city"]),
    _schema("start_build_session", "Amit's build session macro: opens Terminal and VS Code in the "
            "repo, YouTube Studio in Chrome, and returns what's next on the content plan."),
]

FUNCS = {
    "get_time": get_time, "get_calendar": get_calendar, "add_reminder": add_reminder,
    "open_app": open_app, "play_music": play_music, "open_url": open_url,
    "add_note": add_note, "get_weather": get_weather, "start_build_session": start_build_session,
}


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    """Run one allow-listed tool. Returns (result_text, is_error). Never raises."""
    t0 = time.perf_counter()
    if name not in FUNCS:
        result, is_error = f"'{name}' is not an allowed tool.", True
    else:
        try:
            result, is_error = FUNCS[name](**args), False
        except (ToolError, KeyError, TypeError) as e:
            result, is_error = str(e) if isinstance(e, ToolError) else f"bad input: {e}", True
        except Exception as e:  # network, timeouts...
            result, is_error = f"{type(e).__name__}: {e}"[:200], True
    log.info("tool %s(%s) %.2fs %s -> %s", name, json.dumps(args, ensure_ascii=False),
             time.perf_counter() - t0, "ERROR" if is_error else "ok", result[:300].replace("\n", " | "))
    return result, is_error
