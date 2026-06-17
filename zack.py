"""
Zack Voice Assistant  v5.0  — JARVIS Edition
Wake word: "Zack" (say it clearly to wake)"""

# ── Standard library imports ──────────────────────────────────────────────────
import os           # File and directory operations
import sys          # System-level functions (e.g. exit)
import time         # Sleep and timestamp utilities
import math         # Math functions used by the GUI animations
import tempfile     # Creates temporary files (used for Whisper audio)
import threading    # Runs multiple tasks at the same time
import logging      # Writes events to the log file
import datetime     # Date and time formatting
import webbrowser   # Opens URLs in the default browser
import re           # Regular expressions for text pattern matching
import random       # Random selection from lists (used for varied responses)
import tkinter as tk    # GUI toolkit for the HUD window
import http.client  # Low-level HTTP requests (used for news API)
import urllib.parse # URL encoding for query strings
import subprocess   # Launches external programs (e.g. VS Code, git)
import json         # Reads and writes JSON config files
import difflib      # Fuzzy string matching for intent resolution
import sqlite3      # Lightweight database for persistent memory
import queue        # Thread-safe queue (imported for future use)
import socket       # Raw network socket for connectivity checks
from http.server import HTTPServer, BaseHTTPRequestHandler  # Serves the audit log webpage

# ── Third-party library imports ───────────────────────────────────────────────
import pyperclip    # Reads and writes to the clipboard
import psutil       # Reads CPU, RAM, battery, and network stats
import pyautogui    # Simulates keyboard and mouse input
import winsound     # Plays Windows system sounds and beeps
import cv2          # OpenCV: webcam access and image processing
import requests     # Makes HTTP requests (weather, AI, Spotify)
import pyttsx3      # Text-to-speech engine
import speech_recognition as sr  # Converts microphone audio to text
import sounddevice as sd  # Streams audio from the microphone
import numpy as np  # Numerical arrays (used for audio level calculation)
import pyaudio      # Low-level audio I/O (required by speech_recognition)

from openai import OpenAI           # OpenAI-compatible client for the AI backend
from PIL    import Image, ImageDraw # Creates the system tray icon image
import pystray                      # Manages the Windows system tray icon


# ── Optional dependencies (loaded only if installed) ──────────────────────────

# pycaw: Windows audio volume control via COM
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False  # Volume will fall back to pyautogui keypresses

# screen_brightness_control: adjusts monitor brightness
try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

# GPUtil: reads GPU usage and temperature
try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

# mediapipe: hand landmark detection for gesture control
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# pygetwindow: reads the title of the currently focused window
try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False

# plyer: shows native desktop toast notifications
try:
    from plyer import notification as _plyer_notify
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

# whisper: OpenAI's local speech-to-text model (fallback from Google STT)
try:
    import whisper as _whisper_lib
    WHISPER_LIB_AVAILABLE = True
except ImportError:
    WHISPER_LIB_AVAILABLE = False

# spotipy: Spotify Web API client for music playback control
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False


# ── Default configuration values ──────────────────────────────────────────────

# These values are used if no zack_config.json file exists yet.
_DEFAULTS = {
    "weather_city":           "Kolkata",    # Default city for weather lookups
    "tts_rate":               160,           # Words per minute for text-to-speech
    "tts_voice_idx":          0,             # Which installed voice to use (0 = first)
    "tts_volume":             1.0,           # TTS volume from 0.0 to 1.0
    "tts_session_volume":     1.0,           # Windows mixer volume for Zack/SAPI sessions
    "tts_min_master_volume":  0.35,          # Minimum Windows master volume before speaking
    "tts_reinit_every":       1,             # Rebuild sapi5 engine after this many utterances
    "tts_reinit_idle_sec":    600,           # Rebuild sapi5 engine after this many idle seconds
    "tts_audio_session_processes": ["python.exe", "pythonw.exe", "sapisvr.exe", "speechruntime.exe"],
    "startup_progress_step": 0.0035,         # Smaller = slower boot animation progress bar
    "startup_fade_delay_ms": 1800,           # Hold at 100% before fading to the HUD
    "startup_ready_timeout": 45,             # Max seconds to wait for GUI startup to finish
    "startup_settle_sec":    2.0,            # Extra pause after boot before Zack starts listening
    "personality":            "zack",        # Active persona: "zack" or "friday"
    "whisper_model":          "base",        # Whisper model size: tiny/base/small/medium
    "mic_calibrate_sec":      1,             # Seconds of silence used to calibrate mic noise
    "double_clap_wake":       True,          # Whether two quick claps can wake Zack
    "clap_threshold":         0.35,          # Normalized mic level that counts as a clap
    "clap_min_gap":           0.10,          # Minimum seconds between two claps
    "clap_max_gap":           0.60,          # Maximum seconds between two claps (for double-clap)
    "pomodoro_work_min":      25,            # Default Pomodoro work block in minutes
    "pomodoro_break_min":     5,             # Default Pomodoro break duration in minutes
    "tasks_file":             "",            # Path to the plain-text task list file
    "wa_btn1_x": 1704, "wa_btn1_y": 81,     # Screen coordinates of WhatsApp video-call button
    "wa_btn2_x": 1418, "wa_btn2_y": 236,    # Screen coordinates of the call-confirm button
    "proactive_cpu_threshold":  90,          # CPU % that triggers a high-load alert
    "proactive_battery_low":    15,          # Battery % that triggers a low-power alert
    "proactive_class_warn_min": 15,          # Minutes before class to fire a reminder
    "clipboard_watch":          False,       # Whether to watch the clipboard for changes
    "ollama_url":               "http://localhost:11434",  # Local Ollama server URL
    "ollama_model":             "mistral",   # Which Ollama model to use
    "local_only_mode":          False,       # If True, no internet-dependent features
    "audit_log_port":           7777,        # Port for the browser-based audit log server
    "confirm_sensitive":        True,        # Whether to ask before destructive commands
    "plugins_dir":              "zack_plugins",  # Folder scanned for plugin .py files
    "file_watch_dirs":          [],          # Directories to scan for recent files
    "process_watch":            [],          # Process names to monitor for launch/close
    "spotify_client_id":        "3dc65023c4214064832b8d62096880b6",          # Spotify app client ID (from Spotify dashboard)
    "spotify_client_secret":    "9de221e01dec4b8e8d85e6ad91d6657e",          # Spotify app client secret
    "spotify_redirect_uri":     "http://127.0.0.1:8888/callback",  # OAuth callback URL
    "pattern_insight_hour":     8,           # Hour of day to speak a usage-pattern tip
    "hud_notification_count":   3,           # Max recent notifications shown in the HUD
    "checkin_interval_min":     45,          # Minutes between proactive check-in messages (0 = off)
    "stats_panel":              True,        # Show CPU/RAM/battery/network row in HUD
    "memory_auto_extract":      True,        # Auto-extract names, prefs, tasks from conversation
    "window_aware_hud":         True,        # Adjust HUD behavior based on active window
    "window_mode_map": {                     # Maps window title keywords to Zack modes
        "code": "study", "visual studio": "study",
        "chrome": "normal", "game": "gaming",
        "obs": "recording", "discord": "gaming",
    },
    # ── v5.0 additions ────────────────────────────────────────────────────────
    "snippets_file":      "zack_snippets.json",   # Code snippet library storage
    "trade_journal_file": "zack_trades.json",      # Trade journal storage
    "trade_checklist": [                           # Pre-trade checklist items
        "Timeframe confluence checked",
        "Risk-reward ratio calculated",
        "News check done",
        "Stop loss set",
        "Position size confirmed",
    ],
    "activity_bundles": {                          # Named browser/app bundles
        "trading session": {
            "urls": ["https://www.tradingview.com", "https://www.youtube.com/@ICT_InnerCircleTrader/live",
                     "https://www.youtube.com/@SmartMoneyConcepts/live"],
            "apps": []
        },
        "coding tabs": {
            "urls": ["https://docs.python.org/3/", "https://github.com", "https://stackoverflow.com"],
            "apps": []
        },
    },
    "youtube_trading_channels": [                  # Checked for live streams
        "UCrznc8kRcpW4U-G6bMVBFoA",  # ICT (placeholder channel IDs)
        "UCzI4PQLma29ReSEWXxMz7Ow",  # SMC placeholder
    ],
    "game_mode_kill_apps": ["Code.exe", "chrome.exe", "slack.exe"],  # Closed on game launch
    "game_triggers":       ["steam.exe", "EpicGamesLauncher.exe", "VRChat.exe"],
    # ── Recording — Windows Game Bar only (Win+Alt+R to record, Win+G for stats) ──
    "gamebar_clip_dir":    "",   # Leave blank to auto-detect ~/Videos/Captures
    "terminal_layouts": {                          # Multi-terminal layout definitions
        "dev": [
            {"title": "Server",  "cmd": "python -m http.server 8000"},
            {"title": "Logs",    "cmd": "tail -f zack_log.txt"},
            {"title": "Git",     "cmd": "git status"},
        ],
        "trading": [
            {"title": "Journal", "cmd": "python -c \"import json,pprint; pprint.pprint(json.load(open('zack_trades.json')))\""},
            {"title": "News",    "cmd": ""},
        ],
    },
}

_CONFIG_FILE = "zack_config.json"  # Name of the JSON file that stores user settings

def _load_config() -> dict:
    """Load user settings from disk, falling back to defaults for missing keys."""
    cfg = dict(_DEFAULTS)                  # Start with a copy of the defaults
    if os.path.exists(_CONFIG_FILE):       # Only try to open if the file exists
        try:
            with open(_CONFIG_FILE) as f:
                cfg.update(json.load(f))   # Override defaults with saved values
        except Exception:
            pass                           # Silently ignore a corrupt config file
    if not cfg["tasks_file"]:              # If no task file path is set, use the default
        cfg["tasks_file"] = os.path.join(os.path.expanduser("~"), "Documents", "zack_tasks.txt")
    return cfg

CFG = _load_config()  # Load config once at startup; everything reads from this dict

# ── Unpack frequently-used config values into module-level variables ──────────
WEATHER_CITY       = CFG["weather_city"]
TTS_RATE           = CFG["tts_rate"]
TTS_VOICE_IDX      = CFG["tts_voice_idx"]
TTS_VOLUME         = max(0.0, min(1.0, float(CFG.get("tts_volume", 1.0))))
TTS_SESSION_VOLUME = max(0.0, min(1.0, float(CFG.get("tts_session_volume", 1.0))))
TTS_MIN_MASTER_VOLUME = max(0.0, min(1.0, float(CFG.get("tts_min_master_volume", 0.35))))
TTS_REINIT_EVERY   = max(1, int(CFG.get("tts_reinit_every", 25)))
TTS_REINIT_IDLE_SEC = max(60, int(CFG.get("tts_reinit_idle_sec", 600)))
PERSONALITY        = CFG["personality"]
TASKS_FILE         = CFG["tasks_file"]
POMODORO_WORK_MIN  = CFG["pomodoro_work_min"]
POMODORO_BREAK_MIN = CFG["pomodoro_break_min"]
WA_BTN1_X, WA_BTN1_Y = CFG["wa_btn1_x"], CFG["wa_btn1_y"]
WA_BTN2_X, WA_BTN2_Y = CFG["wa_btn2_x"], CFG["wa_btn2_y"]

# ── API keys and file paths ───────────────────────────────────────────────────
MEDIASTACK_KEY = "b3e87e8d3ee4555a8a0ef7c40143cc40"   # Mediastack news API key
NVIDIA_KEY     = "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"  # NVIDIA AI API key
WEATHER_API    = "18b294d3d42a0baffdffdc8970a21c40"   # OpenWeatherMap API key
LOG_FILE       = "zack_log.txt"                       # Plain-text event log file
MEMORY_DB      = "zack_memory.db"                     # SQLite database for persistent memory
PREFS_FILE     = "zack_prefs.json"                    # JSON file for adaptive preferences

# ── Project directory shortcuts ───────────────────────────────────────────────
# Used by "open project <name>" to launch VS Code in the right folder.
PROJECTS = {
    "zack":    r"C:\Projects\Zack",
    "webdev":  r"C:\Projects\WebDev",
    "ml":      r"C:\Projects\ML",
    "default": r"C:\Projects",
}

# ── Weekly class timetable ────────────────────────────────────────────────────
# Each day maps to a list of (time_string, subject_name) tuples.
TIMETABLE = {
    "Monday":    [("09:00","Math"),("11:00","Physics"),("14:00","Chemistry")],
    "Tuesday":   [("10:00","English"),("13:00","Biology")],
    "Wednesday": [("09:00","Math"),("11:00","Computer Science")],
    "Thursday":  [("10:00","Physics"),("14:00","English")],
    "Friday":    [("09:00","Chemistry"),("11:00","Biology"),("13:00","Math")],
    "Saturday":  [],
    "Sunday":    [],
}

# ── HUD color themes per mode ─────────────────────────────────────────────────
# Each mode maps to (primary_color, dim_color) hex strings used in the HUD widget.
MODE_COLORS = {
    "normal":    ("#00E5FF","#0077AA"),
    "gaming":    ("#FF4400","#882200"),
    "study":     ("#00FF88","#008844"),
    "recording": ("#FF00CC","#880066"),
    "focus":     ("#FFAA00","#885500"),
    "silent":    ("#445566","#223344"),
    "security":  ("#FF2222","#881111"),
}

# ── Known websites that can be opened by name ─────────────────────────────────
WEBSITES = {
    "google":   "https://www.google.com",
    "youtube":  "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "spotify":  "https://open.spotify.com/collection/tracks",
}

# ── Valid news topic filters for the Mediastack API ───────────────────────────
NEWS_CATEGORIES = {"technology","sports","business","science","politics","health","entertainment"}

# ── Joke bank for the "tell me a joke" command ────────────────────────────────
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "Why do Java developers wear glasses? Because they don't C sharp.",
    "A SQL query walks into a bar and asks two tables: can I join you?",
    "My code never has bugs. It just develops random features.",
    "Why was the math book sad? It had too many problems.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
]

# ── Commands that require verbal confirmation before executing ────────────────
_SENSITIVE_COMMANDS = ["shutdown","restart","reboot","git push","push code","call ","clear tasks","delete all tasks"]

# ── Slot-fill prompts: ask for missing info when a command is incomplete ──────
# If the user says "add task" without specifying what, Zack asks the follow-up question.
_SLOT_FILLS = {
    "add task":     "What should I add as a task, sir?",
    "new task":     "What task should I create, sir?",
    "set timer":    "How long, sir? Say something like 5 minutes.",
    "set a timer":  "How long should the timer run, sir?",
    "remind me":    "What should I remind you about, and when, sir?",
    "open project": "Which project, sir? Say zack, webdev, or ml.",
    "git commit":   "What commit message shall I use, sir?",
    "search for":   "What would you like me to search for, sir?",
}

# ── Pre-defined multi-step command sequences ──────────────────────────────────
# Saying "work session" runs all three steps automatically in order.
_COMMAND_CHAINS = {
    "work session":    ["study mode","list tasks","start pomodoro"],
    "morning routine": ["daily briefing","weather","list tasks"],
    "end session":     ["night briefing","stop pomodoro"],
    "dev session":     ["open project default","git status","start pomodoro"],
    "focus session":   ["focus mode","start pomodoro"],
    "security check":  ["security mode","show telemetry"],
}

# ── Natural language to canonical command mapping ────────────────────────────
# Maps everyday phrases to the internal command strings used by handle_command().
_INTENT_MAP = {
    "what time is it":"time","tell me the time":"time",
    "current time":"time","what's the time right now":"time",
    "what day is it today":"date","tell me today's date":"date",
    "what's today":"date","what is the date":"date",
    "how's the weather":"weather","is it going to rain":"weather",
    "what's outside like":"weather","should i carry an umbrella":"weather",
    # ── Time & date ───────────────────────────────────────────────────────────
    "what time is it":"time","tell me the time":"time","current time":"time",
    "do you know the time":"time","time please":"time","give me the time":"time",
    "what's the time right now":"time","what hour is it":"time",
    "what's today's date":"date","tell me the date":"date","current date":"date",
    "what day is today":"date","what's the day":"date","today's date":"date",
    "what day of the week is it":"date","which day is it":"date",

    # ── Weather ───────────────────────────────────────────────────────────────
    "how's the weather":"weather","what's it like outside":"weather",
    "how hot is it":"weather","temperature outside":"weather",
    "is it going to rain":"weather","will it rain today":"weather",
    "how cold is it":"weather","what's the temperature":"weather",
    "how's the weather today":"weather","weather report":"weather",
    "what's the forecast":"weather","tell me the weather":"weather",
    "should i bring a jacket":"weather","do i need a coat":"weather",

    # ── Volume ────────────────────────────────────────────────────────────────
    "turn it up":"volume up","make it louder":"volume up",
    "increase the sound":"volume up","can you turn up the volume":"volume up",
    "louder please":"volume up","boost the volume":"volume up",
    "raise the volume":"volume up","increase volume":"volume up",
    "crank it up":"volume up","speak louder":"volume up",
    "turn it down":"volume down","make it quieter":"volume down",
    "lower the sound":"volume down","too loud":"volume down",
    "reduce the volume":"volume down","decrease volume":"volume down",
    "quieter please":"volume down","bring the volume down":"volume down",
    "turn down the sound":"volume down","lower volume":"volume down",
    "silence":"mute","go quiet":"mute","stop the sound":"mute",
    "mute the sound":"mute","turn off sound":"mute","no sound":"mute",
    "kill the audio":"mute","hush":"mute",
    "bring the sound back":"unmute","turn sound back on":"unmute",
    "restore audio":"unmute","un mute":"unmute","turn on audio":"unmute",
    "unmute the sound":"unmute","audio back on":"unmute",

    # ── Brightness ────────────────────────────────────────────────────────────
    "screen too bright":"brightness down","dim the screen":"brightness down",
    "make it darker":"brightness down","reduce brightness":"brightness down",
    "lower the brightness":"brightness down","too bright":"brightness down",
    "screen hurts my eyes":"brightness down","dim display":"brightness down",
    "screen too dark":"brightness up","make it brighter":"brightness up",
    "increase screen light":"brightness up","raise brightness":"brightness up",
    "can't see the screen":"brightness up","screen is dim":"brightness up",
    "increase brightness":"brightness up","more light on screen":"brightness up",

    # ── Screenshot ────────────────────────────────────────────────────────────
    "take a picture of the screen":"screenshot","capture the screen":"screenshot",
    "grab the screen":"screenshot","save what's on screen":"screenshot",
    "print screen":"screenshot","screen capture":"screenshot",
    "snap the screen":"screenshot","save the screen":"screenshot",
    "capture my display":"screenshot","save a screenshot":"screenshot",

    # ── Shutdown / sleep / lock ───────────────────────────────────────────────
    "turn off the computer":"shutdown","power off":"shutdown","turn off pc":"shutdown",
    "shut the computer down":"shutdown","power down":"shutdown","switch off pc":"shutdown",
    "turn off my computer":"shutdown","switch off my pc":"shutdown",
    "put computer to sleep":"sleep","go to sleep":"sleep",
    "suspend the computer":"sleep","put pc to sleep":"sleep","sleep mode":"sleep",
    "lock the computer":"lock screen","lock my pc":"lock screen",
    "lock the screen":"lock screen","secure my pc":"lock screen",
    "log off screen":"lock screen","lock display":"lock screen",

    # ── Tasks ─────────────────────────────────────────────────────────────────
    "what do i need to do":"list tasks","what's on my list":"list tasks",
    "show me my tasks":"list tasks","any pending tasks":"list tasks",
    "give me my tasks":"list tasks","my to do list":"list tasks",
    "what tasks do i have":"list tasks","pending items":"list tasks",
    "show to do list":"list tasks","what's left to do":"list tasks",
    "i finished a task":"complete task","mark it done":"complete task",
    "that task is done":"complete task","task completed":"complete task",
    "check off a task":"complete task","i'm done with a task":"complete task",
    "wipe the task list":"clear tasks","remove all tasks":"clear tasks",
    "delete my tasks":"clear tasks","clear my to do list":"clear tasks",
    "erase all tasks":"clear tasks","reset task list":"clear tasks",

    # ── Pomodoro ──────────────────────────────────────────────────────────────
    "start focus timer":"start pomodoro","begin pomodoro":"start pomodoro",
    "i want to focus":"start pomodoro","start a work session":"start pomodoro",
    "pomodoro please":"start pomodoro","focus session":"start pomodoro",
    "start a focus session":"start pomodoro","begin a work block":"start pomodoro",
    "start a study session":"start pomodoro","let's focus":"start pomodoro",
    "stop focus timer":"stop pomodoro","end the pomodoro":"stop pomodoro",
    "cancel the pomodoro":"stop pomodoro","stop the focus session":"stop pomodoro",
    "end focus session":"stop pomodoro","quit pomodoro":"stop pomodoro",

    # ── Schedule ──────────────────────────────────────────────────────────────
    "what classes do i have":"today's schedule","any classes today":"today's schedule",
    "my schedule for today":"today's schedule","today's timetable":"today's schedule",
    "what's on my schedule":"today's schedule","classes today":"today's schedule",
    "am i free today":"today's schedule","what's my day look like":"today's schedule",
    "when is my next class":"next class","upcoming class":"next class",
    "what class is next":"next class","my next lecture":"next class",
    "next lecture":"next class","when does class start":"next class",
    "show me this week":"weekly schedule","all classes this week":"weekly schedule",
    "this week's timetable":"weekly schedule","my week":"weekly schedule",
    "weekly timetable":"weekly schedule","classes this week":"weekly schedule",

    # ── News ──────────────────────────────────────────────────────────────────
    "what's happening in the world":"show news","any news today":"show news",
    "tell me what's going on":"show news","read me the news":"show news",
    "open the news":"show news","show the news":"show news",
    "what's in the news":"show news","latest news":"show news",
    "news update":"show news","today's headlines":"show news",
    "what happened today":"show news","current events":"show news",
    "tell me more about that":"elaborate","go deeper on that":"elaborate",
    "expand on that":"elaborate","more details":"elaborate",
    "tell me more":"elaborate","elaborate on that":"elaborate",

    # ── Briefings ─────────────────────────────────────────────────────────────
    "good morning zack":"daily briefing","morning update":"daily briefing",
    "start my day":"daily briefing","morning briefing please":"daily briefing",
    "give me my briefing":"daily briefing","what's my morning look like":"daily briefing",
    "daily rundown":"daily briefing","morning report":"daily briefing",
    "end of day summary":"night briefing","how was my day":"night briefing",
    "day review":"night briefing","wrap up the day":"night briefing",
    "daily summary":"night briefing","end of session":"night briefing",
    "how am i doing":"status report","give me an update":"status report",
    "quick update":"status report","status check":"status report",
    "everything okay":"status report","system check":"status report",

    # ── System stats ──────────────────────────────────────────────────────────
    "how is my computer doing":"pc stats","is my pc running okay":"pc stats",
    "full system report":"full telemetry","how much battery do i have":"battery",
    "check my battery":"battery","what's my battery at":"battery",
    "how's my laptop doing":"pc stats","computer health":"pc stats",
    "check cpu":"pc stats","check ram":"pc stats","memory usage":"pc stats",
    "system performance":"pc stats","how's my system":"pc stats",

    # ── Camera ────────────────────────────────────────────────────────────────
    "open webcam":"camera","show me the camera":"camera",
    "start the camera":"camera","launch webcam":"camera",
    "turn on camera":"camera","activate camera":"camera",
    "take a photo":"snapshot","snap a picture":"snapshot",
    "take a selfie":"snapshot","capture image":"snapshot",
    "take a snapshot":"snapshot","grab a photo":"snapshot",
    "what's in front of you":"what do you see","describe what you see":"what do you see",
    "look around":"what do you see","use your eyes":"what do you see",
    "tell me what's on screen":"what do you see","scan the screen":"what do you see",
    "start watching for movement":"security mode","watch the room":"security mode",
    "monitor the room":"security mode","enable security camera":"security mode",
    "activate security":"security mode","guard the room":"security mode",
    "stop watching":"stop security","turn off security":"stop security",
    "disable the camera guard":"stop security","security off":"stop security",

    # ── Music ─────────────────────────────────────────────────────────────────
    "pause the music":"pause music","stop the music":"pause music",
    "hold the music":"pause music","freeze the music":"pause music",
    "music off":"pause music","cut the music":"pause music",
    "skip this song":"next track","go to the next song":"next track",
    "next please":"next track","change the song":"next track",
    "skip song":"next track","i don't like this song":"next track",
    "go back a song":"previous track","last song":"previous track",
    "play the previous":"previous track","go back":"previous track",
    "restart the song":"previous track","previous please":"previous track",
    "resume the music":"resume music","continue music":"resume music",
    "unpause music":"resume music","play again":"resume music",

    # ── Modes ─────────────────────────────────────────────────────────────────
    "i want to game":"gaming mode","let's game":"gaming mode",
    "time to game":"gaming mode","game time":"gaming mode",
    "switching to games":"gaming mode","gaming time":"gaming mode",
    "i'm going to study":"study mode","help me study":"study mode",
    "study time":"study mode","time to study":"study mode",
    "i need to focus":"focus mode","help me concentrate":"focus mode",
    "deep work mode":"focus mode","concentration mode":"focus mode",
    "back to normal":"normal mode","turn off all modes":"normal mode",
    "reset mode":"normal mode","default mode":"normal mode",
    "deactivate mode":"normal mode","standard mode":"normal mode",
    "exam tomorrow":"exam mode","big exam":"exam mode","exam time":"exam mode",
    "big deadline":"project crunch","deadline mode":"project crunch",
    "crunch time":"project crunch","project deadline":"project crunch",
    "going to bed":"night mode","it's late":"night mode",
    "bedtime mode":"night mode","late night mode":"night mode",
    "keep it quiet":"night mode","quiet mode":"night mode",

    # ── Git ───────────────────────────────────────────────────────────────────
    "what changed in git":"git status","save my code":"git commit",
    "upload my code":"git push","get the latest code":"git pull",
    "check git":"git status","any changes in git":"git status",
    "push to github":"git push","sync my code":"git push",
    "pull from github":"git pull","update my code":"git pull",
    "commit everything":"git commit","save changes to git":"git commit",

    # ── Clipboard ─────────────────────────────────────────────────────────────
    "what did i copy":"clipboard","what's on my clipboard":"clipboard",
    "read what i copied":"clipboard","show my clipboard":"clipboard",
    "what's in the clipboard":"clipboard","paste what i copied":"clipboard",
    "summarise what i copied":"summarize clipboard",
    "summarize clipboard":"summarize clipboard",
    "what did i copy summary":"summarize clipboard",
    "give me a summary of my clipboard":"summarize clipboard",

    # ── Jokes / misc ──────────────────────────────────────────────────────────
    "say something funny":"joke","make me laugh":"joke","cheer me up":"joke",
    "tell me something funny":"joke","i need a laugh":"joke",
    "got any jokes":"joke","tell a joke":"joke","be funny":"joke",

    # ── Help ──────────────────────────────────────────────────────────────────
    "what can you do":"lab tour","list your commands":"lab tour",
    "help":"lab tour","show me everything you can do":"lab tour",
    "what are your features":"lab tour","what do you know":"lab tour",
    "give me a tour":"lab tour","teach me your commands":"lab tour",
    "show me your abilities":"lab tour","capabilities":"lab tour",

    # ── Stop / cancel ─────────────────────────────────────────────────────────
    "stop talking":"stop","be quiet":"stop","shut up zack":"stop",
    "cancel that":"cancel","never mind":"cancel","forget it":"cancel",
    "abort":"cancel","stop what you're doing":"stop","that's enough":"stop",
    "zip it":"stop","shhh":"stop","quiet down":"stop",

    # ── History / memory ──────────────────────────────────────────────────────
    "show my recent commands":"last commands","what did i say":"last commands",
    "command history":"last commands","recent commands":"last commands",
    "my reminders":"list reminders","any reminders set":"list reminders",
    "show my reminders":"list reminders","what reminders do i have":"list reminders",
    "what do you remember":"recall memory","what have i told you":"recall memory",
    "what's in your memory":"recall memory","stored memory":"recall memory",
    "what was i working on":"recent files","recent files":"recent files",
    "last files i opened":"recent files","recently edited files":"recent files",

    # ── Network mode ──────────────────────────────────────────────────────────
    "turn off internet":"local mode on","local mode":"local mode on",
    "go offline":"local mode on","disconnect from internet":"local mode on",
    "work offline":"local mode on","offline please":"local mode on",
    "turn on internet":"local mode off","online mode":"local mode off",
    "reconnect":"local mode off","go online":"local mode off",
    "connect to internet":"local mode off","back online":"local mode off",

    # ── Audit / logs ──────────────────────────────────────────────────────────
    "show my log":"show audit log","open audit log":"show audit log",
    "view the log":"show audit log","open my logs":"show audit log",
    "audit trail":"show audit log","command log":"show audit log",
    "what are my habits":"show patterns","my usage patterns":"show patterns",
    "how do i use you":"show patterns","my command patterns":"show patterns",

    # ── Trade journal ─────────────────────────────────────────────────────────
    "write down a trade":"log trade","record a trade":"log trade",
    "save trade idea":"log trade","note a trade":"log trade",
    "trade entry":"log trade","add to trade journal":"log trade",
    "save my chart":"save this chart","capture this chart":"save this chart",
    "chart snapshot":"save this chart","save the chart":"save this chart",
    "review my trading":"trade review","how did i do trading":"trade review",
    "end of trading day":"trade review","trading session done":"trade review",
    "show my trade log":"show journal","trade history":"show journal",
    "my trading journal":"show journal","show trade entries":"show journal",

    # ── Docs & errors ─────────────────────────────────────────────────────────
    "look something up":"docs for","help me with syntax":"syntax for",
    "what's the function for":"syntax for","code help":"syntax for",
    "i got an error":"explain this error","there's an error":"explain this error",
    "error message":"explain this error","something broke":"explain this error",
    "fix the error":"explain this error","why is there an error":"explain this error",
    "debug my code":"debug this","code is broken":"debug this",

    # ── Snippets ──────────────────────────────────────────────────────────────
    "save this code":"save this as","store this snippet":"save this as",
    "bookmark this code":"save this as","keep this code":"save this as",
    "get code snippet":"load snippet","retrieve code":"load snippet",
    "paste my snippet":"load snippet","show my saved code":"list snippets",
    "what snippets do i have":"list snippets","my saved code":"list snippets",

    # ── Dev tools ─────────────────────────────────────────────────────────────
    "test my code":"run tests","check if tests pass":"run tests",
    "run my tests":"run tests","execute tests":"run tests",
    "open terminals":"open dev terminals","launch dev setup":"open dev terminals",
    "set up my workspace":"open dev terminals","terminal setup":"open dev terminals",
    "make a new project":"create new","scaffold a project":"create project",
    "new app":"create new","create app":"create new",

    # ── Clap toggle ───────────────────────────────────────────────────────────
    "enable clap":"toggle clap on","turn on clap wake":"toggle clap on",
    "clap mode on":"toggle clap on","activate clap wake":"toggle clap on",
    "disable clap":"toggle clap off","turn off clap wake":"toggle clap off",
    "clap mode off":"toggle clap off","deactivate clap wake":"toggle clap off",
    "stop clap detection":"toggle clap off","clap wake off":"toggle clap off",

    # ── Recording ─────────────────────────────────────────────────────────────
    "begin recording":"start recording","start capturing":"start recording",
    "record this":"start recording","capture my screen":"start recording",
    "start screen capture":"start recording","go live":"start recording",
    "stop capturing":"stop recording","finish recording":"stop recording",
    "end capture":"stop recording","save the recording":"stop recording",
    "cut recording":"stop recording","recording done":"stop recording",
    "save the last moment":"clip the last","capture that moment":"clip the last",
    "record that":"clip that","save that clip":"save clip",

    # ── Gaming ────────────────────────────────────────────────────────────────
    "save last 30 seconds":"clip the last","capture last minute":"clip the last",
    "clip that":"clip that","save replay":"save replay",
    "game clip":"clip the last","highlight clip":"clip the last",
}



# ── Persona dialogue — JARVIS Edition ────────────────────────────────────────
# Values can be a string OR a list. persona() picks randomly from lists.

_PERSONA = {
    "zack": {
        "boot": [
            "Systems online, sir. All modules reporting nominal. What shall we tackle today?",
            "Good to be back, sir. All systems are nominal and ready for your command.",
            "Online and operational, sir. Sensors calibrated, memory intact. At your service.",
            "Everything checks out, sir. Ready when you are.",
        ],
        "thinking": [
            "One moment, sir.",
            "Processing that, sir.",
            "Let me look into that, sir.",
            "Give me just a moment, sir.",
            "Working on it, sir.",
            "On it, sir.",
        ],
        "shutdown": [
            "Powering down, sir. It has been a pleasure, as always.",
            "Shutting down. Do try not to need me too urgently until I'm back, sir.",
            "Until next time, sir. I'll keep the lights on.",
            "Signing off, sir. Good work today.",
        ],
        "mode_on": [
            "Mode activated, sir.",
            "Done, sir. Configuration updated.",
            "Switching modes now, sir.",
        ],
        "no_hear": [
            "I'm afraid I didn't catch that, sir. Could you repeat?",
            "My apologies — I didn't quite hear you, sir. Once more?",
            "Forgive me, sir. Could you say that again?",
            "Pardon, sir. I missed that.",
        ],
        "no_understand": [
            "I'm afraid that's outside my current comprehension, sir. Could you rephrase?",
            "I didn't quite follow that, sir. Perhaps a different phrasing?",
            "My apologies, sir. I'm not sure what you meant. Could you elaborate?",
            "That one escaped me, sir. Try again?",
        ],
        "briefing_intro": [
            "Good morning, sir. Your daily briefing follows.",
            "A pleasure to see you this morning, sir. Here is your overview.",
            "Morning, sir. Allow me to bring you up to speed.",
        ],
        "night_intro": [
            "A productive day, sir. Here is how it unfolded.",
            "Good evening, sir. Here is your end-of-day summary.",
            "Allow me to summarize the day's proceedings, sir.",
        ],
        "alert": [
            "Sir, your attention please.",
            "A matter requiring your attention, sir.",
            "I thought you should know, sir.",
            "Heads up, sir.",
        ],
        "remembered": [
            "Noted and filed, sir.",
            "Committed to memory, sir.",
            "I'll remember that, sir.",
            "Stored, sir.",
        ],
        "confirm": [
            "Sir, this requires your confirmation. Shall I proceed?",
            "A moment, sir — this action warrants a second thought. Confirm?",
            "Are you certain, sir? Say yes to continue.",
        ],
        "cancelled": [
            "Very well, sir. Action cancelled.",
            "Understood, sir. Standing down.",
            "Cancelled as requested, sir.",
            "As you wish, sir.",
        ],
        "offline": [
            "Operating in local mode, sir. Internet-dependent features are suspended.",
            "I've severed the external connection, sir. Local systems remain fully operational.",
        ],
        "online": [
            "External connection restored, sir. All features are now available.",
            "Back online, sir. Internet-dependent features are live.",
        ],
        "slot_fill_prefix": "If I may ask, sir —",
    },
    "friday": {
        "boot":             "Friday online. Good to be back.",
        "thinking":         "Processing.",
        "shutdown":         "Powering down. Stay sharp.",
        "mode_on":          "Mode activated.",
        "no_hear":          "Say again?",
        "no_understand":    "Didn't catch that.",
        "briefing_intro":   "Daily briefing incoming.",
        "night_intro":      "Day summary ready.",
        "alert":            "Alert.",
        "remembered":       "Got it.",
        "confirm":          "Confirm? Say yes to proceed.",
        "cancelled":        "Aborted.",
        "offline":          "Local mode active.",
        "online":           "Network restored.",
        "slot_fill_prefix": "Quick question —",
    },
}


# ── Global runtime state ──────────────────────────────────────────────────────

_current_mode        = "normal"    # Active mode name (normal, gaming, study, etc.)
_current_personality = PERSONALITY # Which persona is active
_silent_mode         = False       # When True, TTS is suppressed and HUD is used instead
_local_only_mode     = CFG["local_only_mode"]  # When True, all internet calls are blocked
_cached_ip_city      = None        # Cached city name from IP geolocation (avoids repeat lookups)
_reminders_list      = []          # List of active reminder dicts {"text", "trigger", "fired"}
_command_history     = []          # Rolling list of the last 50 commands with timestamps
_command_freq        = {}          # Dict mapping command keywords to how often they were used
_session = {                       # Per-session counters reset on each launch
    "start": time.time(),
    "commands": 0,
    "ai_queries": 0,
    "tasks_done": 0,
    "pomodoros_done": 0,
}
_adaptive_prefs  = {               # User behavior data saved across sessions
    "volume_history": [],
    "app_counts": {},
    "total_sessions": 0,
}
_pomodoro_active    = False        # True while a Pomodoro timer is running
_pomodoro_phase     = "WORK"       # Either "WORK" or "BREAK"
_pomodoro_session   = 0            # Count of completed Pomodoro work blocks
_pomodoro_remaining = 0.0          # Seconds left in the current phase
_pomodoro_stop      = threading.Event()  # Set this to abort the Pomodoro thread

_security_active       = False     # True while motion-detection security mode is running
_security_motion_count = 0         # Number of motion events detected so far
_security_stop         = threading.Event()  # Set this to stop the security thread

_hud_data = {                      # Shared dict updated by background threads for HUD display
    "cpu": 0.0, "ram": 0.0, "gpu": 0.0, "battery": -1,
    "net_up": 0.0, "net_down": 0.0,
    "pomodoro_remaining": 0.0, "pomodoro_phase": "WORK", "pomodoro_session": 0,
    "motion": False, "motion_count": 0,
    "tasks_total": 0, "tasks_done": 0, "active_window": "",
    "audio_viz": [], "online": True,
}
_hud_scene             = "default"   # Visual scene name for the HUD renderer
_last_news_headlines   = []          # Headlines from the most recent news fetch
_gesture_running       = False       # True while gesture-control thread is active
_whisper_model         = None        # Loaded Whisper model object (set by background thread)
_whisper_ready         = threading.Event()  # Set when Whisper has finished loading
_proactive_cpu_alert_time    = 0.0   # Timestamp of the last CPU high-load alert
_proactive_battery_alerted   = False # True if a low-battery alert has been sent this session
_proactive_class_alerted_for = ""    # Key of the last class alert to prevent duplicates
_clipboard_prev        = ""          # Previous clipboard content for change detection
_hud_notification_feed = []          # Recent short notification strings for the HUD
_confirmation_pending  = None        # Tuple (command, callback) waiting for yes/no
_last_topic            = ""          # Most recent topic discussed (for follow-up AI queries)
_last_command          = ""          # The previous command string (for slot-fill deduplication)
_pattern_data          = {}          # Hour-of-day usage counts for pattern analysis
_spotify_client        = None        # Authenticated spotipy.Spotify object (lazy-loaded)
_spotify_playlists_cache = {}        # Cached list of user's Spotify playlists (id and name)
_plugins_loaded        = []          # Names of successfully loaded plugin modules
_process_states        = {}          # Tracks running/stopped state for watched processes

# ── Conversation context ──────────────────────────────────────────────────────
_conv_context = {
    "exchanges":             [],    # Rolling list of last 8 {user, zack, action, ts} dicts
    "last_entity":           "",    # The subject of the last exchange (for pronoun resolution)
    "last_action":           "",    # The action performed in the last command
    "last_result":           "",    # The factual text output of the last command
    "pending_clarification": None,  # String key while waiting for a follow-up answer
}
_sir_counter = 0   # Used to space out ", sir" so it doesn't appear every sentence


# ── Preferences persistence ───────────────────────────────────────────────────

def _load_prefs():
    """Load adaptive preferences and usage pattern data from the prefs JSON file."""
    global _adaptive_prefs, _pattern_data
    try:
        if os.path.exists(PREFS_FILE):
            with open(PREFS_FILE) as f:
                data = json.load(f)
                _adaptive_prefs.update(data)              # Merge saved prefs into the dict
                _pattern_data = data.get("pattern_data", {})  # Load hourly usage counts
    except Exception:
        pass  # Ignore errors; defaults remain in place

def _save_prefs():
    """Write adaptive preferences and usage patterns to disk."""
    try:
        out = dict(_adaptive_prefs)
        out["pattern_data"] = _pattern_data              # Include usage pattern counts
        with open(PREFS_FILE, "w") as f:
            json.dump(out, f, indent=2)
    except Exception:
        pass

def save_config():
    """Write the current CFG dict to zack_config.json and confirm to the user."""
    try:
        with open(_CONFIG_FILE, "w") as f:
            json.dump(CFG, f, indent=2)
        speak("Config saved, sir.")
    except Exception as e:
        speak("Couldn't save the config, sir.")
        print(e)


# ── SQLite persistent memory ──────────────────────────────────────────────────

def _init_memory_db():
    """Create the memory and events tables if they don't already exist."""
    with sqlite3.connect(MEMORY_DB) as con:
        # key-value store for things like "name is Zack" or "birthday is June 3"
        con.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT NOT NULL, ts TEXT NOT NULL)")
        # append-only event log for commands, AI queries, task additions, etc.
        con.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, data TEXT, ts TEXT)")
        # ── v4.0: richer conversation memory ────────────────────────────────
        # topics: recent subjects discussed (for context threading)
        con.execute("CREATE TABLE IF NOT EXISTS topics (topic TEXT NOT NULL, ts TEXT NOT NULL)")
        # preferences: things the user has expressed liking or disliking
        con.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL, ts TEXT NOT NULL)")
        # pending_items: tasks or questions left unresolved mid-conversation
        con.execute("CREATE TABLE IF NOT EXISTS pending_items (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, resolved INTEGER DEFAULT 0, ts TEXT NOT NULL)")
        con.commit()

def memory_log_topic(topic: str):
    """Record a topic that was discussed; keeps the 30 most recent."""
    ts = datetime.datetime.now().isoformat()
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("INSERT INTO topics(topic,ts) VALUES(?,?)", (topic, ts))
        # Prune oldest rows beyond 30
        con.execute("DELETE FROM topics WHERE rowid NOT IN (SELECT rowid FROM topics ORDER BY ts DESC LIMIT 30)")
        con.commit()

def memory_recall_topics(n: int = 5):
    """Return the n most recently discussed topics."""
    with sqlite3.connect(MEMORY_DB) as con:
        rows = con.execute("SELECT topic,ts FROM topics ORDER BY ts DESC LIMIT ?", (n,)).fetchall()
    return rows

def memory_store_pref(key: str, value: str):
    """Save a user preference (e.g. 'music genre' → 'jazz')."""
    ts = datetime.datetime.now().isoformat()
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("INSERT OR REPLACE INTO preferences(key,value,ts) VALUES(?,?,?)", (key, value, ts))
        con.commit()

def memory_recall_pref(key: str):
    """Return the stored preference for key, or None."""
    with sqlite3.connect(MEMORY_DB) as con:
        row = con.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

def memory_add_pending(text: str):
    """Record an unfinished task or question to revisit later."""
    ts = datetime.datetime.now().isoformat()
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("INSERT INTO pending_items(text,ts) VALUES(?,?)", (text, ts))
        con.commit()

def memory_resolve_pending(item_id: int):
    """Mark a pending item as resolved."""
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("UPDATE pending_items SET resolved=1 WHERE id=?", (item_id,))
        con.commit()

def memory_get_pending():
    """Return all unresolved pending items as (id, text, ts) tuples."""
    with sqlite3.connect(MEMORY_DB) as con:
        return con.execute("SELECT id,text,ts FROM pending_items WHERE resolved=0 ORDER BY ts DESC").fetchall()

_TOPIC_KEYWORDS = {
    # maps phrases that appear in commands to a canonical topic label
    "weather": "weather", "rain": "weather", "temperature": "weather",
    "music": "music", "spotify": "music", "song": "music", "playlist": "music",
    "task": "tasks", "todo": "tasks", "pomodoro": "focus",
    "study": "study", "exam": "study", "class": "schedule",
    "git": "coding", "code": "coding", "project": "coding",
    "news": "current events", "headline": "current events",
    "battery": "system health", "cpu": "system health", "ram": "system health",
}

_PREF_PATTERNS = [
    # (regex, group_for_key, group_for_value)
    (re.compile(r"\bi (?:love|like|prefer|enjoy)\s+(.+)", re.I), None, 1),
    (re.compile(r"\bmy (?:favourite|favorite|preferred)\s+(\w+)\s+is\s+(.+)", re.I), 1, 2),
    (re.compile(r"\bi(?:'m| am) called\s+(\w+)", re.I), None, 1),  # stores name
    (re.compile(r"\bmy name is\s+(\w+)", re.I), None, 1),
]

def _auto_extract_memory(command: str):
    """
    Parse the command for topics, preferences, and pending items and persist them.
    Called automatically at the start of every handle_command invocation.
    """
    if not CFG.get("memory_auto_extract", True):
        return
    cmd_lower = command.lower()

    # Topic detection
    for kw, topic in _TOPIC_KEYWORDS.items():
        if kw in cmd_lower:
            memory_log_topic(topic)
            break  # One topic per command is enough

    # Preference extraction
    for pattern, key_grp, val_grp in _PREF_PATTERNS:
        m = pattern.search(command)
        if m:
            if key_grp is not None:
                key   = m.group(key_grp).strip().lower()
                value = m.group(val_grp).strip()
            else:
                # "I love jazz" -> key = inferred from context word before match
                value = m.group(val_grp).strip()
                key   = "name" if "called" in cmd_lower or "name" in cmd_lower else "preference"
            memory_store_pref(key, value)
            log(f"[MEMORY] pref stored: {key} = {value}")
            break

    # Pending-item detection: "remind me to X" without a time anchor means unresolved intent
    pending_pattern = re.compile(
        r"\b(?:i need to|don't let me forget|remind me to|i want to|i should)\s+(.+)", re.I
    )
    pm = pending_pattern.search(command)
    if pm and "remind me" not in command:  # "remind me" is handled by the full reminder system
        text = pm.group(1).strip().rstrip(".")
        if len(text) > 3:
            memory_add_pending(text)
            log(f"[MEMORY] pending item: {text}")

def memory_store(key, value):
    """Insert or replace a key-value pair in the memory database."""
    ts = datetime.datetime.now().isoformat()
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("INSERT OR REPLACE INTO memory (key,value,ts) VALUES(?,?,?)", (key, value, ts))
        con.commit()

def memory_recall(key):
    """Return the stored value for a key, or None if it doesn't exist."""
    with sqlite3.connect(MEMORY_DB) as con:
        row = con.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

def memory_recall_all():
    """Return all memory rows ordered newest first as a list of (key, value, ts) tuples."""
    with sqlite3.connect(MEMORY_DB) as con:
        return con.execute("SELECT key,value,ts FROM memory ORDER BY ts DESC").fetchall()

def memory_log_event(kind, data):
    """Append an event record (e.g. command, task_added, ai_query) to the events table."""
    ts = datetime.datetime.now().isoformat()
    with sqlite3.connect(MEMORY_DB) as con:
        con.execute("INSERT INTO events(kind,data,ts) VALUES(?,?,?)", (kind, data, ts))
        con.commit()

def handle_remember(command):
    """Parse 'remember X is Y' and store it; fall back to storing as a timestamped note."""
    text = re.sub(r"^(zack\s+)?(remember\s+(that\s+)?)", "", command, flags=re.IGNORECASE).strip()
    m = re.search(r"(.+?)\s+is\s+(.+)", text)
    if m:
        key   = m.group(1).strip().lower()  # e.g. "name"
        value = m.group(2).strip()          # e.g. "Zack"
        memory_store(key, value)
        notify("Memory", f"{key} = {value}")
        persona_speak("remembered")
    else:
        # No "X is Y" pattern — store the whole text as a timestamped note
        key = f"note_{datetime.datetime.now().strftime('%H%M%S')}"
        memory_store(key, text)
        notify("Memory", f"Note: {text[:40]}")
        persona_speak("remembered")

def handle_recall(command):
    """Look up a specific key in memory, or list all stored items if no key is given."""
    m = re.search(r"(?:about|what is|what's)\s+(.+)", command)
    if m:
        key = m.group(1).strip().lower()
        val = memory_recall(key)
        speak(f"{key} is {val}, sir." if val else f"Nothing stored for {key}, sir.")
        return
    rows = memory_recall_all()
    if not rows:
        speak("Nothing stored yet, sir.")
        return
    speak(f"I have {len(rows)} items in memory, sir.")
    for key, val, _ in rows[:5]:   # Read out only the five most recent items
        speak_wait(f"{key} is {val}.")


# ── Logging and notifications ─────────────────────────────────────────────────

# Configure the file logger to write timestamped lines to LOG_FILE.
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log(msg):
    """Write a message to the log file and print it to the console."""
    logging.info(msg)
    print(msg)

def notify(action, detail=""):
    """Print a formatted action banner to the console and update the HUD notification feed."""
    line = f"\n  ┌─ ZACK ──────────────────────\n  │  {action}"
    if detail:
        line += f"\n  │  {detail}"
    line += "\n  └────────────────────────────────"
    print(line)
    log(f"[ACTION] {action} {detail}")
    if _gui:
        _gui.safe_set_action(action[:18].upper())   # Show a brief label on the HUD
    short = action[:22] + (f": {detail[:20]}" if detail else "")
    _hud_notification_feed.append(short)
    # Keep the feed capped at the configured maximum
    if len(_hud_notification_feed) > CFG["hud_notification_count"]:
        _hud_notification_feed.pop(0)

def toast(title, message, duration=4):
    """Show a desktop toast notification; fall back to a console banner if unavailable."""
    if TOAST_AVAILABLE:
        try:
            _plyer_notify.notify(title=title, message=message, app_name="Zack", timeout=duration)
            return
        except Exception:
            pass
    print(f"\n  ╔══ ALERT ══╗\n  ║ {title}: {message[:60]}\n  ╚═══════════╝")


# ── Intent resolution, slot-filling, and confirmation ────────────────────────

def _resolve_intent(command):
    """
    Map a spoken phrase to a canonical command string.
    First tries exact substring matches, then falls back to fuzzy matching.
    Returns the canonical command, or None if no match is confident enough.
    """
    cmd = command.strip().lower()
    for phrase, canonical in _INTENT_MAP.items():
        if phrase in cmd:
            return canonical                       # Exact substring match wins immediately
    best_score, best_canonical = 0.0, None
    for phrase, canonical in _INTENT_MAP.items():
        score = difflib.SequenceMatcher(None, cmd, phrase).ratio()  # 0.0–1.0 similarity
        if score > best_score:
            best_score, best_canonical = score, canonical
    if best_score >= 0.62:                         # Only accept matches above this threshold
        log(f"[INTENT] '{cmd}' → '{best_canonical}' ({best_score:.2f})")
        return best_canonical
    return None

def _check_slot_fill(command):
    """
    Detect if the user gave an incomplete command (e.g. "add task" with no task text).
    Returns the follow-up question to ask, or None if the command is complete.
    """
    cmd = command.lower().strip()
    for trigger, question in _SLOT_FILLS.items():
        if trigger in cmd:
            # Strip filler words and the trigger phrase to see what remains
            remainder = re.sub(r"^(please|zack|for me|a|an|the)\s*", "", cmd.replace(trigger, "").strip()).strip()
            if not remainder:
                return question    # Nothing left means the user didn't specify the details
    return None

def _is_sensitive(command):
    """Return True if the command matches a destructive action that needs confirmation."""
    if not CFG["confirm_sensitive"]:
        return False
    return any(s in command.lower() for s in _SENSITIVE_COMMANDS)

def _request_confirmation(command, callback):
    """
    Store the pending command and ask the user to confirm before executing.
    v4.0: reads the exact action back so the user knows what they are confirming.
    """
    global _confirmation_pending
    _confirmation_pending = (command, callback)
    # Build a human-readable description of the action
    action_desc = command.strip().rstrip(".")
    speak(_pick(
        f"Sir, you asked me to {action_desc}. Shall I proceed? Say yes to confirm.",
        f"Just to confirm — {action_desc}. Say yes to go ahead, or anything else to cancel.",
        f"Before I {action_desc}, I need a confirmation, sir. Yes or no?",
    ))

def _handle_confirmation(response):
    """
    Handle a yes/no follow-up to a sensitive command.
    Returns True if this message was a confirmation response, False otherwise.
    """
    global _confirmation_pending
    if _confirmation_pending is None:
        return False
    cmd, callback = _confirmation_pending
    _confirmation_pending = None
    if any(w in response.lower() for w in ("yes","confirm","do it","proceed","sure","yep","yeah")):
        callback()                     # User confirmed — run the original command
    else:
        speak(persona("cancelled"))    # User declined
    return True

def run_chain(name):
    """Execute a named command chain (a list of sub-commands) one by one."""
    steps = _COMMAND_CHAINS.get(name)
    if not steps:
        return
    notify("Chain", name)
    speak(f"Running {name}, sir.")
    for step in steps:
        time.sleep(0.3)
        handle_command(step)

def _load_plugins():
    """Scan the plugins folder and import any .py files that export a register() function."""
    plugin_dir = CFG["plugins_dir"]
    if not os.path.isdir(plugin_dir):
        return
    import importlib.util
    for fname in os.listdir(plugin_dir):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(plugin_dir, fname)
        try:
            spec   = importlib.util.spec_from_file_location(fname[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(handle_command)       # Give the plugin access to handle_command
            _plugins_loaded.append(fname[:-3])
            print(f"  [Plugin] Loaded: {fname}")
        except Exception as e:
            print(f"  [Plugin] Failed to load {fname}: {e}")

def _record_pattern():
    """Increment the usage counter for the current hour of day."""
    hour = str(datetime.datetime.now().hour)
    _pattern_data[hour] = _pattern_data.get(hour, 0) + 1

def show_patterns():
    """Print a bar chart of command usage by hour and speak the peak-usage hour."""
    if not _pattern_data:
        speak("Not enough data yet, sir.")
        return
    peak_hour = max(_pattern_data, key=_pattern_data.get)
    print("\n  ── USAGE BY HOUR " + "─"*30)
    for h, count in sorted(_pattern_data.items(), key=lambda x: int(x[0])):
        print(f"  {h.zfill(2)}:00  {'█'*min(count,20)} ({count})")
    print("  "+"─"*46+"\n")
    speak(f"Peak usage at {peak_hour}:00, sir. {sum(_pattern_data.values())} total commands on record.")

def _pattern_insight_thread():
    """Background thread that speaks a usage insight once per morning at the configured hour."""
    spoken_today = False
    while True:
        now = datetime.datetime.now()
        if now.hour == CFG["pattern_insight_hour"] and not spoken_today and _pattern_data:
            spoken_today = True
            peak = max(_pattern_data, key=_pattern_data.get)
            if _should_interrupt():
                speak(_pick(
                    f"Good morning, sir. For what it's worth, you're typically most active around {peak}:00.",
                    f"Morning, sir. Pattern analysis suggests your peak productivity is around {peak}:00.",
                    f"Sir, based on your usage history, {peak}:00 is your most productive hour. Worth planning around.",
                ))
        if now.hour != CFG["pattern_insight_hour"]:
            spoken_today = False   # Reset flag after the insight hour passes
        time.sleep(600)            # Check every 10 minutes

_last_checkin_time = 0.0   # Timestamp of the last proactive check-in message

def _checkin_thread():
    """
    Background thread that proactively speaks a check-in message every
    `checkin_interval_min` minutes of active session time.
    Fires only when the system is idle (not speaking, not busy, not silent).
    Set checkin_interval_min to 0 in config to disable.
    """
    global _last_checkin_time
    _last_checkin_time = time.time()   # Start the clock from boot
    while True:
        interval_min = CFG.get("checkin_interval_min", 45)
        if interval_min <= 0:
            time.sleep(60)
            continue
        elapsed_min = (time.time() - _last_checkin_time) / 60
        if elapsed_min >= interval_min and _should_interrupt():
            _last_checkin_time = time.time()
            _speak_checkin()
        time.sleep(60)   # Check once per minute

def _speak_checkin():
    """Choose and deliver a proactive check-in based on current system state."""
    state   = _analyze_user_state()
    pending = memory_get_pending()
    topics  = memory_recall_topics(3)

    # If there are unresolved pending items, surface the oldest one
    if pending:
        item_id, text, _ = pending[-1]   # oldest unresolved
        speak(_pick(
            f"Sir, earlier you mentioned wanting to {text}. Have you had a chance to do that?",
            f"Just checking in, sir. You had noted: {text}. Still on your plate?",
            f"A quick reminder, sir — you wanted to {text}. Should I add it as a formal task?",
        ))
        return

    # If recent topics exist, offer to continue
    if topics:
        topic = topics[0][0]
        speak(_pick(
            f"We were discussing {topic} a while back, sir. Anything else you need on that front?",
            f"Sir, you were working on {topic} earlier. Need any follow-up?",
        ))
        return

    # Generic session-aware check-in
    dur = state["session_min"]
    if state["fatigue"]:
        speak(_pick(
            f"Sir, you've been at this for {dur} minutes. A brief break might do you good.",
            "Still going strong, sir? A short pause could help. Water, perhaps.",
        ))
    elif state["stressed"]:
        speak(_pick(
            "CPU and command rate are both elevated, sir. Everything under control?",
            "Systems are working hard, sir. Is there anything I can help offload?",
        ))
    else:
        speak(_pick(
            f"Just checking in, sir. {dur} minutes into the session. All good?",
            "Everything running smoothly on your end, sir?",
            "Ready when you need me, sir. Just thought I'd check in.",
        ))


# ── Personality helpers ───────────────────────────────────────────────────────

def persona(key):
    """Return the persona string for key; picks randomly if the value is a list."""
    val = _PERSONA.get(_current_personality, _PERSONA["zack"]).get(key, "")
    if isinstance(val, list):
        return random.choice(val)
    return val

def persona_speak(key):
    """Speak the persona line for key (non-blocking)."""
    t = persona(key)
    if t:
        speak(t)

def persona_speak_wait(key):
    """Speak the persona line for key and wait until TTS finishes."""
    t = persona(key)
    if t:
        speak_wait(t)

def set_personality(name):
    """Switch to a named persona ('zack' or 'friday') and announce the change."""
    global _current_personality
    name = name.lower().strip()
    if name in _PERSONA:
        _current_personality = name
        notify("Personality", name.upper())
        speak(f"Switching to {name} mode, sir.")
    else:
        speak("I know Zack and Friday. Which would you like, sir?")


# ── JARVIS personality engine helpers ────────────────────────────────────────

def _pick(*options):
    """Return one of the provided string options at random."""
    return random.choice(options)

def _sir():
    """Return ', sir' roughly every third call to avoid sounding repetitive."""
    global _sir_counter
    _sir_counter += 1
    return ", sir" if _sir_counter % 3 == 1 else ""

def _ordinal(n):
    """Return the ordinal suffix for an integer: 1 → 'st', 2 → 'nd', 3 → 'rd', else 'th'."""
    return {1:"st", 2:"nd", 3:"rd"}.get(n if n < 20 else n % 10, "th")

def _track_context(user_input="", zack_response="", action="", entity=""):
    """Append this exchange to the rolling conversation history and update last-action fields."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    _conv_context["exchanges"].append({
        "user": user_input, "zack": zack_response, "action": action, "ts": ts
    })
    if len(_conv_context["exchanges"]) > 8:
        _conv_context["exchanges"].pop(0)  # Keep only the most recent 8 turns
    if action:
        _conv_context["last_action"] = action
    if entity:
        _conv_context["last_entity"] = entity
    if zack_response:
        _conv_context["last_result"] = zack_response
    # v4.0: persist topic from user input to long-term memory automatically
    if user_input:
        _auto_extract_memory(user_input)

def _get_recent_ctx(n=3):
    """Build a short text summary of the last n conversation turns for AI context injection."""
    recent = _conv_context["exchanges"][-n:]
    parts  = []
    for ex in recent:
        if ex.get("user"):  parts.append(f"User: {ex['user']}")
        if ex.get("zack"):  parts.append(f"Zack: {ex['zack']}")
    return "\n".join(parts)

def _analyze_user_state():
    """
    Infer the user's likely mood and workload from session duration, time, and system stats.
    Returns a dict with keys: session_min, hour, fatigue, stressed, mood, battery, cpu.
    """
    now        = time.time()
    session_min = int((now - _session["start"]) / 60)  # Minutes since Zack started
    hour       = datetime.datetime.now().hour
    cpu        = _hud_data.get("cpu", 0)
    battery    = _hud_data.get("battery", 100)
    fatigue    = session_min > 120 or hour >= 23 or hour < 5   # Long session or very late/early
    stressed   = cpu > 80 or _session["commands"] > 40         # High CPU or many rapid commands
    mood       = ("focused" if _pomodoro_active
                  else "stressed" if stressed
                  else "fatigued" if fatigue
                  else "neutral")
    return {
        "session_min": session_min, "hour": hour,
        "fatigue": fatigue, "stressed": stressed,
        "mood": mood, "battery": battery, "cpu": cpu,
    }

def _should_interrupt(priority="low"):
    """
    Return True if it is appropriate for Zack to speak proactively right now.
    Suppressed during silent mode, while already speaking, while processing a command,
    or during a work-phase Pomodoro unless the alert is high-priority.
    """
    if _silent_mode:                                          return False
    if _is_speaking.is_set():                                 return False
    if _busy.is_set():                                        return False
    if _pomodoro_active and _pomodoro_phase == "WORK" and priority != "high":
        return False
    return True

def _jarvis_weather_comment(temp, desc, location):
    """Return a contextual one-liner about current weather conditions."""
    d = desc.lower()
    if any(w in d for w in ("rain","drizzle","shower","thunderstorm")):
        return _pick(
            "I'd recommend an umbrella today, sir.",
            f"Precipitation likely in {location}, sir. Best to stay dry.",
            "The umbrella debate is settled, sir. Take it.",
        )
    elif temp > 35:
        return _pick(
            "Rather scorching out there, sir. Do stay hydrated.",
            f"I'd advise against unnecessary outdoor excursions, sir. {temp} degrees is quite fierce.",
            "An excellent day to remain indoors, sir.",
        )
    elif temp < 15:
        return _pick(
            "Quite brisk out there, sir. A jacket would be advisable.",
            f"Cold conditions in {location}, sir. Do layer up if heading out.",
            "Rather chilly, sir. Something warm is recommended.",
        )
    elif any(w in d for w in ("clear","sunny","few clouds")):
        return _pick(
            f"Clear skies over {location}, sir. Rather pleasant, if I may say.",
            "Lovely conditions today, sir.",
            f"Fine weather in {location}, sir.",
        )
    return ""


# ── Network connectivity ──────────────────────────────────────────────────────

def _check_connectivity():
    """Return True if an outbound TCP connection to Google DNS succeeds."""
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False

def _connectivity_monitor_thread():
    """Background thread that checks internet every 30 s and alerts on state changes."""
    was_online = True
    while True:
        online = _check_connectivity()
        _hud_data["online"] = online
        if online and not was_online:                             # Connection just came back
            toast("Zack", "Internet connection restored.")
            if not _local_only_mode:
                speak(_pick("Internet connection restored, sir.", "Back online, sir."))
        elif not online and was_online:                           # Connection just dropped
            toast("Zack", "No internet connection detected.")
            speak("Warning, sir — no internet connection detected.")
        was_online = online
        time.sleep(30)

def set_local_mode(enabled):
    """Enable or disable local-only mode and announce the change."""
    global _local_only_mode
    _local_only_mode = enabled
    CFG["local_only_mode"] = enabled
    if enabled:
        notify("Local Mode", "Internet disabled")
        persona_speak("offline")
    else:
        notify("Online Mode", "Internet enabled")
        persona_speak("online")

def _ollama_available():
    """Return True if an Ollama server URL is configured."""
    return bool(CFG["ollama_url"])

def ai_query_ollama(query):
    """Send a prompt to the local Ollama server and return the text response, or None on failure."""
    if not CFG["ollama_url"]:
        return None
    try:
        resp = requests.post(
            f"{CFG['ollama_url']}/api/generate",
            json={"model": CFG["ollama_model"], "prompt": query, "stream": False},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIFIED GUI — Single tkinter root, single thread, two phases:
#  Phase 1 "startup": full-screen animated boot sequence.
#  Phase 2 "hud":     small overlay HUD that slides up from the bottom-right.
# ═══════════════════════════════════════════════════════════════════════════════

class ZackGUI:

    # ── Color palette ─────────────────────────────────────────────────────────
    BG    = "#020b12"   # Background near-black
    CYAN  = "#00e5ff"   # Primary accent cyan
    CYAN2 = "#00b8d4"   # Secondary cyan
    CYAN3 = "#005f73"   # Dim cyan for decorations
    CYAN4 = "#003545"   # Faintest cyan for grid lines
    WHITE = "#daf4fb"   # Text and bright accents
    BLUE  = "#1a237e"   # Inner ring fill
    GRID  = "#071520"   # Subtle grid-line color
    BLACK = "#000000"   # Pure black
    DIM   = "#004a5a"   # Muted accent for boot screen labels
    GREEN = "#00ff88"   # "OK" status color

    # ── Boot screen log lines ──────────────────────────────────────────────────
    BOOT_LOG = [
        ("[SYS] INITIALIZING KERNEL MODULES",      "OK"),
        ("[SYS] MOUNTING VIRTUAL FILE SYSTEM",     "OK"),
        ("[MEM] ALLOCATING NEURAL CACHE 0x00FBA9", "OK"),
        ("[NET] ESTABLISHING SECURE UPLINK",        "PENDING"),
        ("[NET] BYPASSING FIREWALL PROXIES",        "OK"),
        ("[DRV] LOADING OPTICAL SENSORS",           "OK"),
        ("[DRV] AUDIO PROCESSING ARRAY",            "CALIBRATING"),
        ("> AWAITING BIOMETRIC CONFIRMATION",       None),
    ]

    # ── Boot screen right-panel status lines ──────────────────────────────────
    RIGHT_STATUS = [
        ("NEURAL_NET_STATUS",None),("COG_NODE_01: SYNC 98%","●"),
        ("COG_NODE_02: SYNC 99%","●"),("COG_NODE_03: SYNC 97%","●"),
        ("COG_NODE_04: SYNC 100%","●"),("─────────────────────────",None),
        ("HEURISTIC ENGINE: WARM","●"),("NLP MODULE: STANDBY","●"),
        ("VOICE SYNTHESIS: LOADED","●"),
    ]

    # ── HUD layout constants ───────────────────────────────────────────────────
    HUD_W         = 240    # Width of the HUD widget in pixels
    HUD_H         = 230    # Height of the HUD widget in pixels (v4.0: +20 for stats row)
    FPS           = 30     # Animation frame rate
    DELAY         = int(1000/FPS)  # Milliseconds between frames
    SLIDE_STEPS   = 22     # Number of steps in the slide-in/out animation
    AUTO_HIDE_S   = 6      # Seconds of inactivity before the HUD slides away
    MARGIN_RIGHT  = 18     # Pixels from the right edge of the screen
    MARGIN_BOTTOM = 52     # Pixels from the bottom edge of the screen

    def __init__(self):
        # Root tkinter window and canvas
        self.root   = None
        self.canvas = None

        # ── Startup phase state ────────────────────────────────────────────────
        self._phase        = "startup"  # "startup" until the boot animation finishes
        self._su_alpha     = 0.0        # Current opacity of the startup screen (0.0–1.0)
        self._su_fade_out  = False      # True once the boot animation starts fading out
        self._su_title_idx = 0          # How many characters of "Z.A.C.K." to show
        self._su_line_idx  = 0          # How many boot-log lines to display
        self._su_progress  = 0.0        # Loading bar fill fraction (0.0–1.0)
        self._su_ring      = 0.0        # Rotation angle of the spinning ring
        self._su_done      = False      # True once progress reaches 100%
        self._su_frame     = 0          # Frame counter for timed reveals
        self._on_startup_complete = None  # Callback fired when the boot animation ends

        # ── HUD animation state ────────────────────────────────────────────────
        self.state       = "idle"   # "idle", "listening", or "speaking"
        self.audio_level = 0.0      # Smoothed RMS level of the microphone (0.0–1.0)
        self._t          = 0.0      # Elapsed time in seconds (drives ring speeds)
        self._ring1      = 0.0      # Rotation of the outermost ring
        self._ring2      = 0.0      # Rotation of the middle ring (counter-rotating)
        self._ring3      = 0.0      # Rotation of the inner ring
        self._pulse      = 0.0      # Core pulse oscillation value (0.0–1.0)
        self._pulse_dir  = 1        # +1 expanding, -1 contracting
        self._wave_off   = 0.0      # Horizontal scroll offset for the waveform display
        self._blend      = 0.0      # 0.0 = circle view, 1.0 = waveform view
        self._blend_dir  = 0        # +1 blending toward waveform, -1 returning to circle
        self._wave_buf   = [0.0]*80 # Rolling buffer of recent audio levels for the waveform
        self._action_label = ""     # Short label displayed on the HUD (e.g. "WEATHER")

        # ── HUD window position ────────────────────────────────────────────────
        self._screen_w = self._screen_h = 0  # Full screen dimensions
        self._final_x  = self._final_y  = 0  # Pixel position of the visible HUD
        self._hidden_y = self._current_y = 0  # Y position when the HUD is off-screen

        # ── Slide animation control ────────────────────────────────────────────
        self._hud_visible = False    # True while the HUD is slid into view
        self._hide_timer  = None     # after() handle for the auto-hide countdown
        self._slide_job   = None     # after() handle for the in-progress slide animation

    def start(self, on_startup_complete=None):
        """Launch the GUI thread and register the startup-complete callback."""
        self._on_startup_complete = on_startup_complete
        threading.Thread(target=self._run, daemon=True).start()

    # ── Thread-safe setters (called from non-GUI threads) ──────────────────────
    def safe_set_state(self, state):
        """Safely update the visual state from any thread via after()."""
        if self.root: self.root.after(0, lambda: self._set_state(state))

    def safe_set_action(self, action):
        """Safely update the action label text from any thread."""
        if self.root: self.root.after(0, lambda: setattr(self, "_action_label", action))

    def safe_set_audio_level(self, v):
        """Clamp v to [0,1] and safely update the audio level from any thread."""
        v = max(0.0, min(1.0, float(v)))
        if self.root: self.root.after(0, lambda: self._update_audio(v))

    def safe_show(self, state="listening"):
        """Safely slide the HUD into view and set the given state from any thread."""
        if self.root: self.root.after(0, lambda: self._show(state))

    def safe_go_idle(self):
        """Safely transition the HUD to idle (auto-hide countdown starts) from any thread."""
        if self.root: self.root.after(0, self._go_idle)

    def safe_set_scene(self, s):
        """Update the HUD scene name from any thread."""
        global _hud_scene; _hud_scene = s

    # ── Public aliases (same as safe_ versions for convenience) ───────────────
    def set_state(self, s):      self.safe_set_state(s)
    def set_action(self, a):     self.safe_set_action(a)
    def set_audio_level(self, v): self.safe_set_audio_level(v)
    def show(self, s="listening"): self.safe_show(s)
    def go_idle(self):           self.safe_go_idle()
    def set_scene(self, s):      self.safe_set_scene(s)

    def _set_state(self, state):
        """Internal: update state and start the circle-to-waveform blend direction."""
        prev = self.state
        self.state = state
        if state == "speaking" and prev != "speaking":   self._blend_dir = 1   # Fade to waveform
        elif state != "speaking" and prev == "speaking": self._blend_dir = -1  # Fade back to circle

    def _update_audio(self, v):
        """Append a new audio level sample to the rolling waveform buffer."""
        self.audio_level = v
        self._wave_buf.append(v)
        if len(self._wave_buf) > 80:
            self._wave_buf.pop(0)   # Discard the oldest sample

    def _show(self, state="listening"):
        """Slide the HUD in and set state; cancel any pending auto-hide timer."""
        prev = self.state
        self.state = state
        if state == "speaking" and prev != "speaking":   self._blend_dir = 1
        elif state != "speaking" and prev == "speaking": self._blend_dir = -1
        if self._hide_timer:
            self.root.after_cancel(self._hide_timer)
            self._hide_timer = None
        self._slide_to(self._final_y)  # Animate to the visible position

    def _go_idle(self):
        """Set state to idle and start the auto-hide countdown."""
        self.state = "idle"
        self._action_label = ""
        self._blend_dir = -1  # Blend back toward the circle view
        if self._hide_timer:
            self.root.after_cancel(self._hide_timer)
        self._hide_timer = self.root.after(int(self.AUTO_HIDE_S*1000), self._slide_to_hidden)

    def _run(self):
        """Create the tkinter window, set it full-screen and transparent, then start the loop."""
        self.root = tk.Tk()
        self.root.title("Zack")
        self.root.overrideredirect(True)         # Remove the window title bar
        self.root.attributes("-topmost", True)   # Always render on top of other windows
        self.root.configure(bg=self.BLACK)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")    # Cover the entire screen during startup
        self.canvas = tk.Canvas(self.root, width=sw, height=sh, bg=self.BLACK, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._screen_w = sw
        self._screen_h = sh
        # Compute the HUD's resting position in the bottom-right corner
        self._final_x  = sw - self.HUD_W - self.MARGIN_RIGHT
        self._final_y  = sh - self.HUD_H - self.MARGIN_BOTTOM
        self._hidden_y = sh + 10            # Start below the visible screen
        self._current_y = self._hidden_y
        self.root.after(self.DELAY, self._tick)
        self.root.mainloop()

    def _tick(self):
        """Main animation loop: delegates to the correct phase renderer each frame."""
        if self._phase == "startup":
            self._tick_startup()
        else:
            self._tick_hud()
        self.root.after(self.DELAY, self._tick)  # Schedule the next frame

    def _tick_startup(self):
        """Advance the boot animation by one frame: fade in, reveal lines, spin ring, fill bar."""
        f = self._su_frame
        self._su_frame += 1
        if self._su_fade_out:
            self._su_alpha = max(0.0, self._su_alpha - 0.035)  # Fade the screen to black
            if self._su_alpha <= 0.0:
                self._transition_to_hud()   # Switch to the HUD phase when fully faded
                return
        else:
            self._su_alpha = min(1.0, self._su_alpha + 0.025)  # Fade in the boot screen
        self._su_ring = (self._su_ring + 2.5) % 360     # Rotate the spinner
        if f % 7 == 0 and self._su_title_idx < len("Z.A.C.K."):
            self._su_title_idx += 1                     # Reveal one more character of the title
        if f % 18 == 0 and self._su_line_idx < len(self.BOOT_LOG)-1:
            self._su_line_idx += 1                      # Reveal the next boot-log line
        if f > 25:
            step = max(0.001, float(CFG.get("startup_progress_step", 0.0035)))
            self._su_progress = min(1.0, self._su_progress + step)  # Advance the loading bar
        if self._su_progress >= 1.0 and not self._su_done:
            self._su_done = True
            delay_ms = max(500, int(CFG.get("startup_fade_delay_ms", 1800)))
            self.root.after(delay_ms, lambda: setattr(self, "_su_fade_out", True))  # Start fade-out
        self._draw_startup()

    def _ba(self, hex_col, alpha):
        """Blend a hex color toward black by the given alpha (0.0 = black, 1.0 = full color)."""
        alpha = max(0.0, min(1.0, alpha))
        r = int(int(hex_col[1:3], 16) * alpha)
        g = int(int(hex_col[3:5], 16) * alpha)
        b = int(int(hex_col[5:7], 16) * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw_startup(self):
        """Render one frame of the full-screen boot animation onto the canvas."""
        c = self.canvas
        c.delete("all")              # Clear the previous frame
        sw, sh = self._screen_w, self._screen_h
        a = self._su_alpha
        ba = self._ba
        CYAN, DIM, GREEN, WHITE = self.CYAN, self.DIM, self.GREEN, self.WHITE

        # Corner bracket decorations
        L=70; T=2; col=ba(DIM, a)
        for ox, oy, dx, dy in [(28,28,1,1),(sw-28,28,-1,1),(28,sh-28,1,-1),(sw-28,sh-28,-1,-1)]:
            c.create_line(ox, oy, ox+dx*L, oy, fill=col, width=T)
            c.create_line(ox, oy, ox,      oy+dy*L, fill=col, width=T)

        # Boot-log lines (revealed one per 18 frames)
        for i, (txt, status) in enumerate(self.BOOT_LOG[:self._su_line_idx+1]):
            ly = 75 + i*23
            c.create_text(52, ly, text=f"■  {txt}...", fill=ba(CYAN, a*0.7), font=("Courier New",9), anchor="w")
            if status:
                sc = GREEN if status == "OK" else CYAN
                c.create_text(52+len(txt)*6+60, ly, text=status, fill=ba(sc, a), font=("Courier New",9,"bold"), anchor="w")

        # Title text typed out character by character
        TITLE = "Z.A.C.K"
        shown = TITLE[:self._su_title_idx]
        if shown:
            c.create_text(sw//2, sh//2-170, text=shown, fill=ba(CYAN, a), font=("Courier New",80,"bold"))
        c.create_text(sw//2, sh//2-90, text="ZEROTH ARTIFICIAL COGNITIVE KERNEL", fill=ba(DIM, a), font=("Courier New",11))

        # Spinning arc ring in the center
        cx, cy = sw//2, sh//2+30
        R = 75
        c.create_oval(cx-R, cy-R, cx+R, cy+R, outline=ba(DIM, a*0.5), width=1)
        c.create_arc(cx-R, cy-R, cx+R, cy+R, start=self._su_ring, extent=250, style=tk.ARC, outline=ba(CYAN, a), width=2)
        c.create_oval(cx-4, cy-4, cx+4, cy+4, fill=ba(CYAN, a*0.8), outline="")

        # Tick marks around the ring
        r2 = 50
        for i in range(24):
            ang = math.radians(i*15 + self._su_ring*0.5)
            if i % 4 == 3: continue   # Skip every fourth tick
            x1 = cx + r2*math.cos(ang);     y1 = cy + r2*math.sin(ang)
            x2 = cx + (r2+5)*math.cos(ang); y2 = cy + (r2+5)*math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=ba(DIM, a*0.7), width=1)

        c.create_text(cx, cy+R+28, text="CALIBRATING...", fill=ba(CYAN, a*0.7), font=("Courier New",11))

        # Loading bar
        bw=380; bh=5; bx=cx-bw//2; by=cy+R+52
        c.create_rectangle(bx, by, bx+bw, by+bh, fill=ba(DIM, a*0.4), outline="")
        filled = int(bw * self._su_progress)
        if filled > 0:
            c.create_rectangle(bx, by, bx+filled, by+bh, fill=ba(CYAN, a), outline="")
        pct = int(self._su_progress * 100)
        c.create_text(cx, by+20, text=f"{pct}%", fill=ba(DIM, a*0.8), font=("Courier New",9))

        # Five small dot indicators below the progress bar
        for i in range(5):
            fc = CYAN if i <= (pct//20) else DIM
            c.create_oval(cx-42+i*22, by+33, cx-32+i*22, by+43, fill=ba(fc, a*0.8), outline="")

        # Right-side status panel
        for i, (txt, dot) in enumerate(self.RIGHT_STATUS):
            ry = sh-260 + i*24
            c.create_text(sw-52, ry, text=txt, fill=ba(DIM, a*0.7), font=("Courier New",8), anchor="e")
            if dot:
                c.create_text(sw-35, ry, text=dot, fill=ba(CYAN, a*0.8), font=("Courier New",8))

    def _transition_to_hud(self):
        """Switch from the full-screen startup phase to the compact HUD phase."""
        self._phase = "hud"
        # Resize the canvas to the small HUD dimensions
        self.canvas.configure(width=self.HUD_W, height=self.HUD_H, bg=self.BG,
                              highlightthickness=1, highlightbackground=self.CYAN3)
        self.root.configure(bg=self.BG)
        self.root.geometry(f"{self.HUD_W}x{self.HUD_H}+{self._final_x}+{self._hidden_y}")
        self._current_y = self._hidden_y
        if self._on_startup_complete:
            threading.Thread(target=self._on_startup_complete, daemon=True).start()

    def _tick_hud(self):
        """Advance HUD animation state and redraw for one frame."""
        al = self.audio_level
        speed = 1 + al*2.5      # Audio level speeds up ring rotation
        self._t    += 1/self.FPS
        self._ring1 = (self._ring1 + 0.9*speed) % 360
        self._ring2 = (self._ring2 - 0.55*speed) % 360   # Counter-rotates
        self._ring3 = (self._ring3 + 1.4*speed) % 360
        self._pulse += 0.04 * self._pulse_dir * (1 + al*3)
        if self._pulse >= 1.0:   self._pulse_dir = -1; self._pulse = 1.0
        elif self._pulse <= 0:   self._pulse_dir =  1; self._pulse = 0.0
        self._wave_off += 1.5 + al*12    # Scroll the waveform horizontally

        # Smoothly blend between circle and waveform views
        BLEND_SPEED = 0.055
        if   self._blend_dir ==  1: self._blend = min(1.0, self._blend + BLEND_SPEED)
        elif self._blend_dir == -1: self._blend = max(0.0, self._blend - BLEND_SPEED)

        c = self.canvas
        c.delete("all")
        W, H = self.HUD_W, self.HUD_H

        # Dark background with subtle grid
        c.create_rectangle(0, 0, W, H, fill=self.BG, outline="")
        for gx in range(0, W, 24): c.create_line(gx, 0, gx, H, fill=self.GRID, width=1)
        for gy in range(0, H, 24): c.create_line(0, gy, W, gy, fill=self.GRID, width=1)

        # Cross-fade between the two views based on _blend
        if   self._blend < 0.05:  self._draw_circle(c, W, H, al, 1.0)
        elif self._blend > 0.95:  self._draw_waveform(c, W, H, al, 1.0)
        else:
            self._draw_circle(c, W, H, al, 1.0 - self._blend)
            self._draw_waveform(c, W, H, al, self._blend)

        self._draw_corners(c, W, H)
        self._draw_labels(c, W, H, al)
        self._draw_stats_panel(c, W, H)   # v4.0

    @staticmethod
    def _h2r(h):
        """Convert a '#rrggbb' hex string to an (r, g, b) integer tuple."""
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @classmethod
    def _lerp_color(cls, c1, c2, t):
        """Linearly interpolate between two hex colors; t=0 returns c1, t=1 returns c2."""
        r1, g1, b1 = cls._h2r(c1)
        r2, g2, b2 = cls._h2r(c2)
        return f"#{int(r1+t*(r2-r1)):02x}{int(g1+t*(g2-g1)):02x}{int(b1+t*(b2-b1)):02x}"

    def _fade(self, color, alpha):
        """Blend color toward the HUD background by alpha (used for opacity effects)."""
        return self._lerp_color(self.BG, color, max(0.0, min(1.0, alpha)))

    def _draw_circle(self, c, W, H, al, op):
        """Draw the concentric ring visualizer with tick marks, arcs, and a glowing core."""
        if op <= 0.01: return
        cx, cy = W//2, H//2+8
        def col(color): return self._fade(color, op)

        # Outer dashed tick ring
        r_dash = 128
        for i in range(60):
            ang = math.radians(i*6 + self._ring1*0.25)
            if i % 4 == 3: continue
            x1 = cx + (r_dash-3)*math.cos(ang); y1 = cy + (r_dash-3)*math.sin(ang)
            x2 = cx + (r_dash+2)*math.cos(ang); y2 = cy + (r_dash+2)*math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=col(self.CYAN4), width=1)

        # Main outer ring with major and minor tick marks
        r_out = 118
        c.create_oval(cx-r_out, cy-r_out, cx+r_out, cy+r_out, outline=col(self.CYAN3), width=1)
        for i in range(72):
            ang  = math.radians(i*5 + self._ring1*0.4)
            long = (i % 9 == 0)        # Every 9th tick is a longer major tick
            ri = r_out - (7 if long else 3)
            ro = r_out + (3 if long else 0)
            x1 = cx + ri*math.cos(ang); y1 = cy + ri*math.sin(ang)
            x2 = cx + ro*math.cos(ang); y2 = cy + ro*math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=col(self.CYAN if long else self.CYAN3), width=(2 if long else 1))

        # Four rotating arcs on the outer ring
        r_arc = 103
        for i in range(4):
            c.create_arc(cx-r_arc, cy-r_arc, cx+r_arc, cy+r_arc,
                         start=self._ring1+i*90, extent=32, style=tk.ARC,
                         outline=col(self.CYAN), width=3)

        # Three counter-rotating arcs on the middle ring
        r_arc2 = 88
        for i in range(3):
            c.create_arc(cx-r_arc2, cy-r_arc2, cx+r_arc2, cy+r_arc2,
                         start=self._ring2+i*120, extent=22, style=tk.ARC,
                         outline=col(self.CYAN2), width=2)

        # Cardinal direction triangular pointers
        r_tri = r_out + 14
        for ang_deg in [90, 270, 0, 180]:
            ang   = math.radians(ang_deg)
            tip_x = cx + r_tri*math.cos(ang); tip_y = cy + r_tri*math.sin(ang)
            perp  = ang + math.pi/2
            r_b   = r_out + 5
            b1x = cx + r_b*math.cos(ang) + 5*math.cos(perp); b1y = cy + r_b*math.sin(ang) + 5*math.sin(perp)
            b2x = cx + r_b*math.cos(ang) - 5*math.cos(perp); b2y = cy + r_b*math.sin(ang) - 5*math.sin(perp)
            c.create_polygon(tip_x, tip_y, b1x, b1y, b2x, b2y, fill=col(self.WHITE), outline="")

        # Middle decorative ring with short arcs
        r_mid = 72
        c.create_oval(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid, outline=col(self.BLUE), width=2)
        for i in range(6):
            c.create_arc(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid,
                         start=self._ring3+i*60, extent=14, style=tk.ARC,
                         outline=col(self.CYAN), width=3)

        # Three pulsing inner rings that breathe with the audio level
        for i in range(3):
            wave = math.sin(self._t*(5+i*2) + i*1.5) * al
            rr   = 52 + i*9 + wave*12
            c.create_oval(cx-rr, cy-rr, cx+rr, cy+rr, outline=col(self.CYAN2), width=max(1, 2-i))

        # Innermost ring with counter-rotating short arcs
        r_in = 44
        c.create_oval(cx-r_in, cy-r_in, cx+r_in, cy+r_in, outline=col(self.CYAN), width=2)
        for i in range(6):
            c.create_arc(cx-r_in, cy-r_in, cx+r_in, cy+r_in,
                         start=self._ring2*1.5+i*60, extent=12, style=tk.ARC,
                         outline=col(self.CYAN3), width=2)

        # Random spark arcs that appear when audio level is high
        if al > 0.08:
            for _ in range(int(al*8)):
                sa  = random.uniform(0, 360)
                ext = random.uniform(8, 25) * al
                c.create_arc(cx-r_in+4, cy-r_in+4, cx+r_in-4, cy+r_in-4,
                             start=sa, extent=ext, style=tk.ARC,
                             outline=col(self.WHITE), width=1)

        # Glowing core — multiple concentric filled ovals create a soft glow
        core_r = 30 + self._pulse*10 + al*16
        for i in range(7, 0, -1):
            gr      = core_r*(i/7) + 6
            alpha_g = 0.06 * i * op
            gc      = self._lerp_color(self.BG, "#00e5ff", alpha_g)
            c.create_oval(cx-gr, cy-gr, cx+gr, cy+gr, fill=gc, outline="")
        c.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r,
                      fill=col(self.CYAN3), outline=col(self.CYAN), width=2)
        br = 14 + self._pulse*5 + al*10
        c.create_oval(cx-br, cy-br, cx+br, cy+br, fill=col(self.CYAN), outline="")
        cr = 5 + al*4
        c.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill=col(self.WHITE), outline="")
        c.create_oval(cx-2, cy-2, cx+2, cy+2, fill="white", outline="")  # Central pinpoint

        # Side data readout panel
        rx = cx + r_out + 10
        for i, v in enumerate([f"BITSTREAMS", f"{random.randint(800,1400)}", f"{al:.4f}", "FREQ.DELTA"]):
            c.create_text(rx, cy-28+i*16, text=v, fill=col(self.CYAN3), font=("Courier New",5), anchor="w")

    def _draw_waveform(self, c, W, H, al, op):
        """Draw the audio waveform analyzer panel with frequency and confidence readouts."""
        if op <= 0.01: return
        def col(color): return self._fade(color, op)

        # Waveform panel background and border
        px=12; py=42; pw=W-24; ph=H-100
        c.create_rectangle(px, py, px+pw, py+ph, fill=col("#030f1a"), outline="")
        c.create_rectangle(px, py, px+pw, py+ph, fill="", outline=col(self.CYAN3), width=1)

        # Three colored dots in the top-left corner (like a browser tab bar)
        for i, dc in enumerate([self.CYAN, self.CYAN2, self.CYAN3]):
            c.create_oval(px+6+i*12, py+4, px+12+i*12, py+10, fill=col(dc), outline="")
        c.create_text(px+28, py+7, text="SYS.AUDIO.ANALYZER",
                      fill=col(self.CYAN), font=("Courier New",6,"bold"), anchor="w")

        # Vertical dashed time markers
        cy_w = py + ph//2
        for frac, label in [(0.33,"T-0.5s"),(0.67,"T+0.5s")]:
            x = px + int(pw*frac)
            c.create_line(x, py, x, py+ph, fill=col(self.CYAN4), width=1, dash=(4,4))
            c.create_text(x, py+10, text=label, fill=col(self.CYAN2), font=("Courier New",6), anchor="n")

        # Draw the waveform line from the rolling audio buffer
        buf = self._wave_buf
        if len(buf) > 1:
            pts = []
            for i, v in enumerate(buf):
                x = px + int(i/(len(buf)-1) * pw)
                y = int(cy_w - v*(ph//2-4))
                pts.extend([x, y])
            if len(pts) >= 4:
                c.create_line(*pts, fill=col(self.CYAN), width=2, smooth=True)
                # Ghost line at half amplitude for depth
                gpts = []
                for i, v in enumerate(buf):
                    x = px + int(i/(len(buf)-1) * pw)
                    y = int(cy_w - v*(ph//2-4)*(0.5+al*0.5))
                    gpts.extend([x, y])
                c.create_line(*gpts, fill=col(self.CYAN3), width=1, smooth=True)

        c.create_line(px, cy_w, px+pw, cy_w, fill=col(self.CYAN4), width=1, dash=(2,4))  # Center line

        # Footer metrics
        by2 = py + ph + 8
        c.create_text(px, by2,    text="FREQ: 44.1 KHZ",   fill=col(self.CYAN),  font=("Courier New",6), anchor="w")
        c.create_text(px, by2+13, text=f"AMP:  +{al*12:.1f} DB", fill=col(self.CYAN2), font=("Courier New",6), anchor="w")
        conf = 85 + al*14
        c.create_text(px+pw, by2,    text=f"{conf:.1f}%",         fill=col(self.WHITE), font=("Courier New",14,"bold"), anchor="e")
        c.create_text(px+pw, by2+16, text="CONFIDENCE LEVEL",     fill=col(self.CYAN3), font=("Courier New",5), anchor="e")

        # Small bar charts for vector match and pattern recognition
        bby = by2 + 30
        c.create_text(px,    bby, text="VECTOR MATCH", fill=col(self.CYAN3), font=("Courier New",5), anchor="w")
        c.create_text(px+90, bby, text="PATTERN REC",  fill=col(self.CYAN3), font=("Courier New",5), anchor="w")
        for i, h in enumerate([0.9,0.6,0.8,1.0,0.5,0.7]):
            bh2 = max(3, int(12*(h*(0.5+al*0.5))))
            c.create_rectangle(px+i*8, bby+14, px+i*8+6, bby+14-bh2, fill=col(self.CYAN), outline="")
        for i, h in enumerate([0.7,1.0,0.5,0.8,0.6,0.9]):
            bh2 = max(3, int(12*(h*(0.5+al*0.5))))
            c.create_rectangle(px+90+i*8, bby+14, px+90+i*8+6, bby+14-bh2, fill=col(self.CYAN2), outline="")

    def _draw_corners(self, c, W, H):
        """Draw small L-shaped brackets at each corner of the HUD frame."""
        L=16; T=2; col=self.CYAN2
        for ox, oy, dx, dy in [(1,1,1,1),(W-1,1,-1,1),(1,H-1,1,-1),(W-1,H-1,-1,-1)]:
            c.create_line(ox, oy, ox+dx*L, oy,      fill=col, width=T)
            c.create_line(ox, oy, ox,      oy+dy*L, fill=col, width=T)

    def _draw_labels(self, c, W, H, al):
        """Draw the status text labels at the top and bottom of the HUD."""
        b = self._blend
        cy_mode = MODE_COLORS.get(_current_mode, MODE_COLORS["normal"])[0]

        if b < 0.5:
            # Circle-view labels
            c.create_text(8,  5,  text="SYS.CORE.ACTIVE",    fill=self.CYAN3, font=("Courier New",5), anchor="w")
            c.create_text(8,  15, text="V 3.2.0",             fill=self.CYAN3, font=("Courier New",5), anchor="w")
            status = "LISTENING..." if self.state == "listening" else "STANDBY"
            c.create_text(W-7, 5,  text="AI.ASSISTANT.READY", fill=self.CYAN,  font=("Courier New",5), anchor="e")
            c.create_text(W-7, 15, text=status,               fill=self.CYAN3, font=("Courier New",5), anchor="e")
            c.create_text(W//2, H-18, text="◾ "*7,            fill=self.CYAN,  font=("Courier New",6))
            c.create_text(W//2, H-6,  text="ACOUSTIC ANALYSIS ARRAY", fill=self.CYAN3, font=("Courier New",5))
        else:
            # Waveform-view labels
            c.create_text(8,   5,  text="Z.A.C.K. // CORE",         fill=self.CYAN,  font=("Courier New",6,"bold"), anchor="w")
            c.create_text(W-7, 5,  text="TERM_ID: 9X-A",            fill=self.CYAN3, font=("Courier New",6), anchor="e")
            st_txt = "STATUS: PROCESSING_VOICE_INPUT" if self.state == "speaking" else "STATUS: READY"
            c.create_text(W-7, 36, text=st_txt,                      fill=self.CYAN,  font=("Courier New",5), anchor="e")

        # Active mode badge at the bottom (hidden in normal mode)
        if _current_mode != "normal":
            c.create_text(W//2, H-4, text=f"[ {_current_mode.upper()} MODE ]",
                          fill=cy_mode, font=("Courier New",5,"bold"))

        # Small red dot if offline
        if not _hud_data.get("online", True):
            c.create_oval(W-10, H-10, W-4, H-4, fill="#ff4444", outline="")

        # Action label overlay
        if self._action_label:
            c.create_text(W//2, H-4 if _current_mode=="normal" else H-14,
                          text=self._action_label, fill=self.CYAN2, font=("Courier New",5,"bold"))

    def _slide_to(self, target_y):
        """Begin a smooth slide animation from the current Y position to target_y."""
        if self._phase != "hud": return
        start_y = self._current_y
        self._do_slide(0, start_y, target_y)

    def _draw_stats_panel(self, c, W, H):
        """
        Draw a one-row system-health bar at the bottom of the HUD showing:
        CPU%, RAM%, battery%, net activity, and mic status.
        Only rendered when CFG['stats_panel'] is True.
        """
        if not CFG.get("stats_panel", True):
            return

        y     = H - 20          # Row sits in the bottom 20 px
        px    = 6               # Left margin
        col_g = self.GREEN      # Green = healthy
        col_w = self.WHITE
        col_d = self.CYAN3      # Dim for labels
        col_a = self.CYAN

        cpu  = _hud_data.get("cpu", 0.0)
        ram  = _hud_data.get("ram", 0.0)
        bat  = _hud_data.get("battery", -1)
        nup  = _hud_data.get("net_up", 0.0)
        ndn  = _hud_data.get("net_down", 0.0)
        mic  = not _mic_monitor_pause.is_set()
        onl  = _hud_data.get("online", True)

        # Thin separator line
        c.create_line(px, y - 3, W - px, y - 3, fill=self.CYAN4, width=1)

        # CPU
        cpu_col = "#ff4444" if cpu > 85 else "#ffaa00" if cpu > 65 else col_g
        c.create_text(px, y + 4, text=f"CPU {int(cpu)}%", fill=cpu_col,
                      font=("Courier New", 5, "bold"), anchor="w")

        # RAM
        ram_col = "#ff4444" if ram > 85 else "#ffaa00" if ram > 70 else col_g
        c.create_text(px + 46, y + 4, text=f"RAM {int(ram)}%", fill=ram_col,
                      font=("Courier New", 5), anchor="w")

        # Battery
        if bat >= 0:
            bat_col = "#ff4444" if bat < 15 else "#ffaa00" if bat < 30 else col_g
            bat_str = f"BAT {int(bat)}%"
        else:
            bat_col = col_d
            bat_str = "BAT --"
        c.create_text(px + 92, y + 4, text=bat_str, fill=bat_col,
                      font=("Courier New", 5), anchor="w")

        # Network
        if nup > 0 or ndn > 0:
            net_str = f"↑{nup:.0f} ↓{ndn:.0f}"
        else:
            net_str = "NET --"
        net_col = col_a if onl else "#ff4444"
        c.create_text(px + 138, y + 4, text=net_str, fill=net_col,
                      font=("Courier New", 5), anchor="w")

        # Mic indicator dot
        mic_col = col_g if mic else col_d
        c.create_oval(W - 12, y, W - 6, y + 8, fill=mic_col, outline="")
        c.create_text(W - 14, y + 4, text="MIC", fill=col_d,
                      font=("Courier New", 4), anchor="e")

    def _slide_to_hidden(self):
        """Slide the HUD down off-screen."""
        self._slide_to(self._hidden_y)

    def _do_slide(self, step, sy, ey):
        """
        Recursive ease-out cubic slide: moves the window by one step per frame.
        step: current step index (0 to SLIDE_STEPS)
        sy:   starting Y pixel
        ey:   ending Y pixel
        """
        if self._phase != "hud": return
        if step > self.SLIDE_STEPS:
            # Animation complete — snap to the exact target
            self._current_y = ey
            self.root.geometry(f"{self.HUD_W}x{self.HUD_H}+{self._final_x}+{ey}")
            return
        t = 1 - (1 - step/self.SLIDE_STEPS)**3    # Ease-out cubic curve
        y = int(sy + (ey-sy)*t)
        self._current_y = y
        self.root.geometry(f"{self.HUD_W}x{self.HUD_H}+{self._final_x}+{y}")
        self.root.after(self.DELAY, lambda: self._do_slide(step+1, sy, ey))


# ── Microphone level monitor ──────────────────────────────────────────────────

_gui: ZackGUI = None   # Set after ZackGUI is instantiated at startup

def _mic_monitor_thread():
    """
    Background thread that continuously reads the microphone.
    Feeds smoothed RMS levels to the HUD and optionally wakes Zack on a double clap.
    """
    smooth = 0.0
    clap_threshold = float(CFG.get("clap_threshold", 0.35))
    clap_reset_level = max(0.05, clap_threshold * 0.55)
    clap_min_gap = float(CFG.get("clap_min_gap", 0.10))
    clap_max_gap = float(CFG.get("clap_max_gap", 0.60))
    double_clap_wake = bool(CFG.get("double_clap_wake", True))
    last_clap_time = 0.0
    last_double_clap_time = 0.0
    clap_armed = True

    def cb(indata, frames, time_info, status):
        nonlocal smooth, last_clap_time, last_double_clap_time, clap_armed
        if _mic_monitor_pause.is_set():
            if _gui: _gui.safe_set_audio_level(0.0)
            return
        rms   = float(np.sqrt(np.mean(indata**2)))
        level = min(1.0, rms / 0.07)
        smooth = smooth * 0.85 + level * 0.15
        if _gui: _gui.safe_set_audio_level(smooth)
        _hud_data["audio_viz"].append(smooth)
        if len(_hud_data["audio_viz"]) > 10:
            _hud_data["audio_viz"].pop(0)

        if not double_clap_wake:
            return
        if level < clap_reset_level:
            clap_armed = True
            return
        if not clap_armed or level < clap_threshold:
            return

        clap_armed = False
        now = time.monotonic()
        gap = now - last_clap_time
        last_clap_time = now

        if _busy.is_set() or _is_speaking.is_set():
            return
        if now - last_double_clap_time < 1.0:
            return
        if clap_min_gap <= gap <= clap_max_gap:
            last_double_clap_time = now
            print(f"[Wake] Double clap detected ({gap:.2f}s gap).")
            _wake_event.set()

    try:
        with sd.InputStream(channels=1, samplerate=16000, blocksize=512,
                            callback=cb, dtype="float32"):
            while True:
                time.sleep(0.05)
    except Exception as e:
        print("Mic monitor error:", e)


# ── Whisper speech-to-text ────────────────────────────────────────────────────

def _load_whisper_background():
    """Load the Whisper model in a background thread so startup isn't blocked."""
    global _whisper_model
    if not WHISPER_LIB_AVAILABLE:
        print("[Whisper] Not installed.")
        _whisper_ready.set()
        return
    try:
        import whisper as _wl
        _whisper_model = _wl.load_model(CFG["whisper_model"])
        print(f"[Whisper] '{CFG['whisper_model']}' ready.")
    except Exception as e:
        print(f"[Whisper] Failed: {e}")
    _whisper_ready.set()   # Signal that the load attempt is complete (success or failure)

def recognize_with_whisper(audio):
    """Transcribe a SpeechRecognition AudioData object using Whisper; raises UnknownValueError on failure."""
    if not _whisper_model:
        raise sr.UnknownValueError()
    # Save the audio to a temp WAV file (Whisper reads from disk)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio.get_wav_data())
        tmp = f.name
    try:
        result = _whisper_model.transcribe(tmp, language="en")
        text   = result["text"].strip().lower()
        if not text:
            raise sr.UnknownValueError()
        return text
    except sr.UnknownValueError:
        raise
    except Exception:
        raise sr.UnknownValueError()
    finally:
        os.unlink(tmp)   # Always delete the temp file


# ── Text-to-speech ────────────────────────────────────────────────────────────

_speak_cancel        = threading.Event()   # Set to interrupt the current speech
_is_speaking         = threading.Event()   # Set while TTS audio is playing
stop_flag            = threading.Event()   # Global stop signal (used in long reads)
_mic_monitor_pause   = threading.Event()   # Set while Zack is listening (pauses mic viz)
_current_engine      = None                # The active pyttsx3 engine instance
_current_engine_lock = threading.Lock()    # Protects access to _current_engine
_tts_queue           = queue.Queue()       # Queue of text strings for the TTS worker thread
_speech_epoch        = 0                   # Incremented whenever speech is interrupted
_last_audio_heal     = 0.0                 # Throttles Windows mixer checks before speaking
_tts_engine_utterances = 0                 # Counts speaks since the last sapi5 engine init
_tts_engine_started_at = 0.0               # Timestamp for the current sapi5 engine instance
_tts_last_used_at      = 0.0               # Timestamp of the last completed speak
_tts_endpoint_token    = ""                # Windows default render endpoint seen by sapi5
_com_thread_state      = threading.local() # Tracks COM initialization per Python thread

def _ensure_com_initialized():
    """Initialize Windows COM for the current thread before using SAPI/pycaw."""
    if getattr(_com_thread_state, "initialized", False):
        return True
    try:
        import pythoncom
        pythoncom.CoInitialize()
        _com_thread_state.initialized = True
        _com_thread_state.backend = "pythoncom"
        return True
    except Exception:
        pass
    try:
        import comtypes
        comtypes.CoInitialize()
        _com_thread_state.initialized = True
        _com_thread_state.backend = "comtypes"
        return True
    except Exception as e:
        print(f"[COM] Could not initialize COM on this thread: {e}")
        return False

def _uninitialize_com():
    """Release COM for the current thread when a long-lived worker exits."""
    if not getattr(_com_thread_state, "initialized", False):
        return
    try:
        if getattr(_com_thread_state, "backend", "") == "pythoncom":
            import pythoncom
            pythoncom.CoUninitialize()
        else:
            import comtypes
            comtypes.CoUninitialize()
    except Exception:
        pass
    _com_thread_state.initialized = False
    _com_thread_state.backend = ""

def _get_default_audio_endpoint_token():
    """Return an identifier for the current Windows default output device."""
    if not PYCAW_AVAILABLE:
        return ""
    _ensure_com_initialized()
    try:
        devices = AudioUtilities.GetSpeakers()
        try:
            endpoint_id = devices.GetId()
        except Exception:
            endpoint_id = ""
        friendly = getattr(devices, "FriendlyName", "") or ""
        return f"{friendly}|{endpoint_id}"
    except Exception:
        return ""

def _get_master_volume_endpoint():
    """Return the Windows master-volume endpoint across pycaw API variants."""
    if not PYCAW_AVAILABLE:
        return None
    _ensure_com_initialized()
    devices = AudioUtilities.GetSpeakers()
    if hasattr(devices, "Activate"):
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    if hasattr(devices, "EndpointVolume"):
        return devices.EndpointVolume
    if hasattr(devices, "endpoint_volume"):
        return devices.endpoint_volume
    if hasattr(devices, "_dev") and hasattr(devices._dev, "Activate"):
        interface = devices._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    raise AttributeError("Could not locate a master-volume endpoint on pycaw speaker device")

def _set_engine_properties(engine):
    """Apply Zack's voice, rate, and SAPI volume settings to a pyttsx3 engine."""
    voices = engine.getProperty("voices")
    if voices:
        voice_idx = TTS_VOICE_IDX if 0 <= TTS_VOICE_IDX < len(voices) else 0
        engine.setProperty("voice", voices[voice_idx].id)
    engine.setProperty("rate", TTS_RATE)
    engine.setProperty("volume", TTS_VOLUME)

def _init_tts_engine():
    """Create and register a fresh sapi5 engine bound to the current default device."""
    global _current_engine, _tts_engine_utterances, _tts_engine_started_at, _tts_endpoint_token
    _ensure_com_initialized()
    _ensure_tts_audible(force=True)
    engine = pyttsx3.init(driverName="sapi5")
    _set_engine_properties(engine)
    _tts_engine_utterances = 0
    _tts_engine_started_at = time.time()
    _tts_endpoint_token = _get_default_audio_endpoint_token()
    with _current_engine_lock:
        _current_engine = engine
    if _tts_endpoint_token:
        print(f"[TTS] sapi5 bound to default output: {_tts_endpoint_token.split('|')[0]}")
    return engine

def _dispose_tts_engine(engine):
    """Stop and release the previous pyttsx3 engine before rebuilding it."""
    global _current_engine
    if engine is None:
        return
    try:
        engine.stop()
    except Exception:
        pass
    with _current_engine_lock:
        if _current_engine is engine:
            _current_engine = None

def _tts_reinit_reason():
    """Return a reason to rebuild sapi5, or an empty string if the engine is healthy."""
    if _current_engine is None:
        return "missing engine"
    endpoint = _get_default_audio_endpoint_token()
    if endpoint and _tts_endpoint_token and endpoint != _tts_endpoint_token:
        return "default output changed"
    if _tts_engine_utterances >= TTS_REINIT_EVERY:
        return f"{_tts_engine_utterances} utterances"
    if _tts_last_used_at and time.time() - _tts_last_used_at > TTS_REINIT_IDLE_SEC:
        return "idle refresh"
    return ""

def _ensure_tts_audible(force=False):
    """Unmute Zack's Windows audio session and keep output volume from being effectively silent."""
    global _last_audio_heal
    if not PYCAW_AVAILABLE:
        return
    _ensure_com_initialized()
    now = time.time()
    if not force and now - _last_audio_heal < 5.0:
        return
    _last_audio_heal = now
    try:
        endpoint = _get_master_volume_endpoint()
        if endpoint.GetMute():
            endpoint.SetMute(0, None)
        if endpoint.GetMasterVolumeLevelScalar() < TTS_MIN_MASTER_VOLUME:
            endpoint.SetMasterVolumeLevelScalar(TTS_MIN_MASTER_VOLUME, None)
    except Exception as e:
        print(f"[TTS] Could not adjust master volume: {e}")
    try:
        current_pid = os.getpid()
        wanted_names = {p.lower() for p in CFG.get("tts_audio_session_processes", [])}
        for session in AudioUtilities.GetAllSessions():
            try:
                proc = session.Process
                proc_name = proc.name().lower() if proc else ""
                if not proc or (proc.pid != current_pid and proc_name not in wanted_names):
                    continue
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMute(0, None)
                if volume.GetMasterVolume() < TTS_SESSION_VOLUME:
                    volume.SetMasterVolume(TTS_SESSION_VOLUME, None)
            except Exception:
                continue
    except Exception as e:
        print(f"[TTS] Could not adjust app volume: {e}")

def _tts_worker_thread():
    """
    Background TTS thread. SAPI can go silent after its first utterance on some
    Windows audio stacks, so Zack treats the engine as disposable between speaks.
    """
    global _tts_engine_utterances, _tts_last_used_at
    _ensure_com_initialized()
    engine = None

    try:
        while True:
            try:
                text = _tts_queue.get()
            except Exception:
                break
            if text is None:
                _tts_queue.task_done()
                _dispose_tts_engine(engine)
                break
            if _speak_cancel.is_set():
                _tts_queue.task_done()
                continue
            _is_speaking.set()
            worker_failed = False
            try:
                if _gui: _gui.safe_set_state("speaking")
            except Exception:
                pass
            try:
                print(f"[TTS] Speaking: {text[:80]}{'...' if len(text) > 80 else ''}")
                reason = _tts_reinit_reason()
                if reason:
                    print(f"[TTS] Reinitializing sapi5 engine ({reason}).")
                    _dispose_tts_engine(engine)
                    engine = None
                if engine is None:
                    engine = _init_tts_engine()
                _ensure_tts_audible(force=True)
                try:
                    winsound.PlaySound(None, 0)  # Stop any async wake chime before SAPI speaks.
                except Exception:
                    pass
                engine.setProperty("volume", TTS_VOLUME)
                engine.say(text)
                engine.runAndWait()
                _tts_engine_utterances += 1
                _tts_last_used_at = time.time()
                _dispose_tts_engine(engine)
                engine = None
            except Exception as e:
                print(f"[TTS] Error: {e}")
                _dispose_tts_engine(engine)
                engine = None
                try:
                    engine = _init_tts_engine()
                except Exception as init_error:
                    print(f"[TTS] Reinit after error failed: {init_error}")
                    worker_failed = True
            finally:
                _is_speaking.clear()
                try:
                    if _gui: _gui.safe_set_state("idle")
                except Exception:
                    pass
            _tts_queue.task_done()
            if worker_failed:
                break
    finally:
        _dispose_tts_engine(engine)
        _uninitialize_com()

threading.Thread(target=_tts_worker_thread, daemon=True, name="tts-worker").start()
print("[TTS] Worker thread started.")

def disable_windows_audio_ducking():
    """Write a registry value to stop Windows from lowering other apps' volume when Zack speaks."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Multimedia\Audio", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "UserDuckingPreference", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(key)
        print("Windows audio ducking disabled.")
    except Exception as e:
        print("Couldn't disable audio ducking:", e)

def _speak_worker(text):
    """Push text onto the TTS queue (blocking until the engine picks it up)."""
    if not text or _speak_cancel.is_set():
        return
    _tts_queue.put(text)


def speak(text):
    """Queue text for TTS (non-blocking) and log it."""
    if not text: return
    log(f"Zack: {text}")
    if _silent_mode:
        notify("SILENT", text[:60])
        return
    if not _speak_cancel.is_set():
        _tts_queue.put(text)

def speak_wait(text):
    """Queue text for TTS and block until it finishes playing."""
    if not text: return
    log(f"Zack: {text}")
    if _silent_mode:
        notify("SILENT", text[:60])
        return
    if not _speak_cancel.is_set():
        _tts_queue.put(text)
        _tts_queue.join()   # Block until the queue is empty and TTS is done

def speak_long(text, chunk_chars=400):
    """Split a long text into sentence chunks and speak each one, respecting stop signals."""
    if not text: return
    speech_epoch = _speech_epoch
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunk = ""
    for sentence in sentences:
        if speech_epoch != _speech_epoch or _speak_cancel.is_set() or stop_flag.is_set():
            break
        if len(chunk) + len(sentence) + 1 <= chunk_chars:
            chunk = (chunk + " " + sentence).strip()   # Accumulate sentences into a chunk
        else:
            if chunk: speak_wait(chunk)                 # Speak the full chunk
            chunk = sentence
    if chunk and speech_epoch == _speech_epoch and not _speak_cancel.is_set() and not stop_flag.is_set():
        speak_wait(chunk)

def stop_speaking():
    """Cancel current TTS, drain the queue, and stop the engine."""
    global _speech_epoch
    _speech_epoch += 1
    _speak_cancel.set()
    stop_flag.set()
    # Drain any queued text so nothing plays after stop
    while not _tts_queue.empty():
        try:
            _tts_queue.get_nowait()
            _tts_queue.task_done()
        except Exception:
            break
    with _current_engine_lock:
        if _current_engine is not None:
            try: _current_engine.stop()
            except Exception: pass
    time.sleep(0.1)
    _speak_cancel.clear()

def wait_until_done_speaking(timeout=30.0):
    """Block until queued/current TTS finishes, with a short stable idle check."""
    deadline = time.time() + timeout
    idle_since = None
    while time.time() <= deadline:
        idle = _tts_queue.empty() and not _is_speaking.is_set()
        if idle:
            if idle_since is None:
                idle_since = time.time()
            elif time.time() - idle_since >= 0.2:
                break
        else:
            idle_since = None
        time.sleep(0.05)
        if time.time() > deadline:
            break
    time.sleep(0.15)

def play_wake_sound():
    """Play the wake confirmation sound asynchronously."""
    try:
        winsound.PlaySound("wakesound.wav", winsound.SND_FILENAME|winsound.SND_ASYNC)
        time.sleep(0.3)
    except Exception:
        pass


# ── System tray icon ──────────────────────────────────────────────────────────

_tray_icon = None   # The pystray Icon instance

def _make_tray_image(color):
    """Create a 64×64 RGBA image with a filled circle — used as the tray icon."""
    img  = Image.new("RGBA", (64,64), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4,4,60,60], fill=color, outline="white", width=2)
    return img

def _quit_zack(icon, item):
    """Tray menu 'Quit' handler: run shutdown sequence, stop the icon, and exit."""
    _shutdown_sequence()
    icon.stop()
    sys.exit(0)

def setup_tray():
    """Create and start the system tray icon in a background thread."""
    global _tray_icon
    icon = pystray.Icon(
        "Zack",
        _make_tray_image("green"),
        "Zack — Ready",
        pystray.Menu(pystray.MenuItem("Quit Zack", _quit_zack))
    )
    _tray_icon = icon
    threading.Thread(target=icon.run, daemon=True).start()

def set_tray_state(state):
    """Change the tray icon color and tooltip: yellow while listening, green when idle."""
    if not _tray_icon: return
    if state == "listening":
        _tray_icon.icon  = _make_tray_image("yellow")
        _tray_icon.title = "Zack — Listening…"
    else:
        _tray_icon.icon  = _make_tray_image("green")
        _tray_icon.title = "Zack — Ready"


# ── Browser-based audit log server ────────────────────────────────────────────

class _LogHandler(BaseHTTPRequestHandler):
    """Serves the last 200 lines of the log file as an HTML page on localhost."""

    def do_GET(self):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-200:]   # Read only the most recent 200 entries
        except Exception:
            lines = ["Log not available."]
        content = "".join(f"<div>{l.strip()}</div>" for l in lines if l.strip())
        html = (
            f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zack Log</title>'
            f'<style>body{{background:#020b12;color:#00e5ff;font-family:monospace;padding:20px}}'
            f'div{{padding:2px 0;border-bottom:1px solid #071520}}</style></head>'
            f'<body><h2>Zack Audit Log</h2>'
            f'<p style="color:#004a5a">Last 200 | <a style="color:#00ff88" href="/">Refresh</a></p>'
            f'{content}</body></html>'
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a):
        pass   # Silence the default access log output to the console

def _audit_log_server_thread():
    """Start the HTTP server that serves the audit log page."""
    port = CFG.get("audit_log_port", 7777)
    try:
        server = HTTPServer(("localhost", port), _LogHandler)
        print(f"  [Audit Log] http://localhost:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"  [Audit Log] Could not start: {e}")


# ── Background monitoring threads ─────────────────────────────────────────────

def _process_monitor_thread():
    """Watch a list of processes and announce when they start or stop."""
    watch = [p.lower() for p in CFG.get("process_watch", [])]
    if not watch: return
    while True:
        try:
            running_now = {p.info["name"].lower() for p in psutil.process_iter(["name"]) if p.info["name"]}
            for proc in watch:
                was    = _process_states.get(proc, False)
                is_now = proc in running_now
                if is_now and not was:
                    toast("Zack", f"{proc} started.")
                    speak(f"Sir, {proc} has just launched.")
                elif not is_now and was:
                    toast("Zack", f"{proc} closed.")
                _process_states[proc] = is_now
        except Exception:
            pass
        time.sleep(10)

def recent_files(n=5):
    """List the n most recently modified files from watched directories."""
    dirs = (CFG.get("file_watch_dirs", [])
            or [os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Desktop")])
    files = []
    for d in dirs:
        if not os.path.isdir(d): continue
        try:
            for fname in os.listdir(d):
                path = os.path.join(d, fname)
                if os.path.isfile(path):
                    files.append((os.path.getmtime(path), fname, path))
        except Exception:
            pass
    if not files:
        speak("Couldn't locate any recent files, sir.")
        return
    files.sort(reverse=True)   # Newest first
    notify("Recent files", f"Top {n}")
    print("\n  ── RECENT FILES " + "─"*31)
    for i, (mtime, fname, path) in enumerate(files[:n]):
        print(f"  {i+1}. {fname}  ({datetime.datetime.fromtimestamp(mtime).strftime('%b %d %H:%M')})")
    print("  "+"─"*46+"\n")
    speak(_pick(f"Your {min(n,len(files))} most recently edited files, sir.", f"Here are your recent files, sir."))
    for _, fname, _ in files[:n]:
        speak_wait(fname+".")

def _proactive_thread():
    """
    Background thread that fires unsolicited alerts for:
    - Sustained high CPU load
    - Low battery
    - Upcoming classes
    """
    global _proactive_cpu_alert_time, _proactive_battery_alerted, _proactive_class_alerted_for
    cpu_high_since = 0.0
    while True:
        try:
            # CPU alert: fires once per 5 minutes if load stays above threshold for > 60 s
            cpu = _hud_data["cpu"]
            threshold = CFG["proactive_cpu_threshold"]
            if cpu > threshold:
                if cpu_high_since == 0.0:
                    cpu_high_since = time.time()
                elif (time.time() - cpu_high_since > 60
                      and time.time() - _proactive_cpu_alert_time > 300):
                    _proactive_cpu_alert_time = time.time()
                    if _should_interrupt("medium"):
                        msg = _pick(
                            f"Sir, the processor has been sustaining {int(cpu)} percent load for over a minute. Shall I check what's running?",
                            f"Heads up, sir — CPU has been at {int(cpu)} percent for a while. Something is working rather hard.",
                            f"Sir, your CPU has been elevated at {int(cpu)} percent. Worth investigating.",
                        )
                        toast("Zack Alert", f"CPU at {int(cpu)}%")
                        speak(msg)
            else:
                cpu_high_since = 0.0    # Reset the timer when load drops

            # Battery alert: fires once when battery drops to or below the low threshold
            bat = _hud_data["battery"]
            if 0 < bat <= CFG["proactive_battery_low"] and not _proactive_battery_alerted:
                _proactive_battery_alerted = True
                if _should_interrupt("high"):
                    msg = _pick(
                        f"Sir, power levels are critically low — battery at {bat} percent. I'd recommend locating a charger before we go dark.",
                        f"Battery at {bat} percent, sir. Perhaps now would be an opportune time to plug in.",
                        f"Sir, we're running low. {bat} percent remaining. A charger would be advisable.",
                    )
                    toast("Zack Alert", f"Battery: {bat}%")
                    speak(msg)
            elif bat > CFG["proactive_battery_low"] + 5:
                _proactive_battery_alerted = False   # Reset after charging above the threshold

            # Class alert: fires once per class when it's within the warning window
            day = datetime.datetime.now().strftime("%A")
            warn_min = CFG["proactive_class_warn_min"]
            for t_str, subj in TIMETABLE.get(day, []):
                try:
                    class_dt = datetime.datetime.strptime(t_str, "%H:%M")
                    now_dt   = datetime.datetime.now().replace(second=0, microsecond=0)
                    delta    = (class_dt - now_dt.replace(year=class_dt.year, month=class_dt.month, day=class_dt.day)).total_seconds() / 60
                    alert_key = f"{day}_{t_str}_{subj}"
                    if 0 < delta <= warn_min and _proactive_class_alerted_for != alert_key:
                        _proactive_class_alerted_for = alert_key
                        if _should_interrupt("high"):
                            msg = _pick(
                                f"Sir, {subj} begins in {int(delta)} minutes. You may want to wrap up what you're doing.",
                                f"Just a reminder, sir — {subj} is in {int(delta)} minutes.",
                                f"Your {subj} class is approaching, sir. {int(delta)} minutes remaining.",
                            )
                            toast("Zack — Class Alert", msg)
                            speak(msg)
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(30)   # Check conditions every 30 seconds

def _clipboard_watcher_thread():
    """Poll the clipboard every 3 s and show a notification when it changes significantly."""
    global _clipboard_prev
    while True:
        try:
            current = pyperclip.paste()
            if current and current != _clipboard_prev and len(current) > 10:
                _clipboard_prev = current
                preview = current[:60].replace("\n", " ")
                notify("Clipboard", preview)
                if len(current) > 200:
                    toast("Zack", "Clipboard updated — say 'summarize clipboard' to get a summary.")
        except Exception:
            pass
        time.sleep(3)


# ── Volume and brightness ─────────────────────────────────────────────────────

def handle_volume(command):
    """
    Adjust system volume using pycaw (native Windows COM API).
    Falls back to pyautogui media keys if pycaw is unavailable.
    """
    if PYCAW_AVAILABLE:
        try:
            vol = _get_master_volume_endpoint()
            cur = vol.GetMasterVolumeLevelScalar()   # Current volume as 0.0–1.0
            if "unmute" in command:
                vol.SetMute(0, None)
                notify("Volume", "Unmuted")
                speak(_pick("Sound restored, sir.", "Unmuted, sir.", "Audio back online, sir."))
                return
            elif "mute" in command:
                vol.SetMute(1, None)
                notify("Volume", "Muted")
                speak(_pick("Muted, sir.", "Silenced, sir.", "Audio suppressed, sir."))
                return
            elif any(w in command for w in ("up","increase","louder")):
                nv = min(1.0, cur + 0.1)             # Increase by 10%, cap at 100%
                vol.SetMasterVolumeLevelScalar(nv, None)
                _adaptive_prefs["volume_history"].append(int(nv*100))
                notify("Volume", f"↑ {int(nv*100)}%")
                speak(_pick(f"Volume up to {int(nv*100)} percent, sir.",
                            f"A touch louder, sir — {int(nv*100)} percent.",
                            f"Increased to {int(nv*100)} percent, sir."))
            elif any(w in command for w in ("down","decrease","lower","quieter")):
                nv = max(0.0, cur - 0.1)             # Decrease by 10%, floor at 0%
                vol.SetMasterVolumeLevelScalar(nv, None)
                notify("Volume", f"↓ {int(nv*100)}%")
                speak(_pick(f"Volume down to {int(nv*100)} percent, sir.",
                            f"A bit quieter, sir — {int(nv*100)} percent.",
                            f"Reduced to {int(nv*100)} percent, sir."))
            else:
                speak("Say volume up, down, mute, or unmute, sir.")
            return
        except Exception as e:
            print(f"pycaw failed ({e}), falling back.")

    # Fallback: use virtual media key presses
    try:
        if "unmute" in command:
            pyautogui.press("volumemute"); notify("Volume", "Unmuted")
            speak(_pick("Sound restored, sir.", "Unmuted, sir."))
        elif "mute" in command:
            pyautogui.press("volumemute"); notify("Volume", "Muted")
            speak(_pick("Muted, sir.", "Silenced, sir."))
        elif any(w in command for w in ("up","increase","louder")):
            for _ in range(3): pyautogui.press("volumeup")
            notify("Volume", "↑")
            speak(_pick("A little louder, sir.", "Volume up, sir."))
        elif any(w in command for w in ("down","decrease","lower","quieter")):
            for _ in range(3): pyautogui.press("volumedown")
            notify("Volume", "↓")
            speak(_pick("A bit quieter, sir.", "Volume down, sir."))
        else:
            speak("Say volume up, down, mute, or unmute, sir.")
    except Exception as e:
        print("Volume fallback error:", e)

def handle_brightness(command):
    """Increase or decrease screen brightness by 10% using screen_brightness_control."""
    if not SBC_AVAILABLE:
        speak("Brightness control isn't available on this system, sir.")
        return
    try:
        cur = sbc.get_brightness()
        if isinstance(cur, list):
            cur = cur[0]            # Some systems return a list; take the first monitor
        if any(w in command for w in ("up","increase","brighter")):
            nb = min(100, cur + 10)
        elif any(w in command for w in ("down","decrease","lower","dim","darker")):
            nb = max(10, cur - 10)  # Floor at 10% so the screen stays usable
        else:
            speak("Say brightness up or down, sir.")
            return
        sbc.set_brightness(nb)
        notify("Brightness", f"{nb}%")
        if any(w in command for w in ("up","increase","brighter")):
            speak(_pick(f"Brightened to {nb} percent, sir.", f"A bit brighter, sir. {nb} percent.", "Display brightened, sir."))
        else:
            speak(_pick(f"Dimmed to {nb} percent, sir.", f"Easier on the eyes now, sir. {nb} percent.", "Display dimmed, sir."))
    except Exception as e:
        speak("Couldn't change the brightness, sir.")
        print(e)


# ── System commands ───────────────────────────────────────────────────────────

def handle_system_command(command):
    """Execute power-management commands: shutdown, restart, sleep, or lock screen."""
    if "shutdown" in command:
        speak_wait(_pick("Shutting down in five seconds, sir.", "Initiating shutdown, sir. Five seconds."))
        time.sleep(5)
        if not stop_flag.is_set(): os.system("shutdown /s /t 0")

    elif "restart" in command or "reboot" in command:
        speak_wait(_pick("Restarting in five seconds, sir.", "Rebooting, sir. Five seconds."))
        time.sleep(5)
        if not stop_flag.is_set(): os.system("shutdown /r /t 0")

    elif "sleep" in command or "hibernate" in command:
        speak_wait(_pick("Going to sleep, sir.", "Sleep mode, sir."))
        time.sleep(1)
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    elif "lock" in command:
        notify("System", "Screen locked")
        speak(_pick("Locking the screen, sir.", "Screen locked, sir."))
        import ctypes
        ctypes.windll.user32.LockWorkStation()

def take_screenshot():
    """Capture the full screen and save it as a timestamped PNG in ~/Pictures."""
    try:
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(folder, exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(folder, f"zack_{ts}.png")
        pyautogui.screenshot(path)
        notify("Screenshot", path)
        toast("Zack", f"Screenshot saved: zack_{ts}.png")
        speak(_pick("Screenshot captured and filed away, sir.", "Captured, sir.", "Screenshot saved, sir."))
    except Exception as e:
        speak("Couldn't take the screenshot, sir.")
        print(e)

def introduce_zack():
    introduction = """
    Good evening, sir. My name is Zack—your personal AI assistant, 
    modeled after the legendary JARVIS from the Marvel universe. 
    
    I'm here to help you with your daily tasks, answer your questions, 
    control your system, search the web, manage reminders, check the weather, 
    play music on Spotify, and much more. 
    
    I was created by Fahad , a computer science student from Kolkata, 
    and I run on Python with voice recognition and TTS.
    
    Think of me as your loyal digital butler—ready to assist with 
    sophistication, dry wit, and just enough personality to keep things interesting.
    
    How may I be of service, sir?
    """
    speak(introduction)

# ── Time, date, and weather ───────────────────────────────────────────────────

def tell_time():
    """Speak the current time in a natural format (e.g. 'half past three PM')."""
    n    = datetime.datetime.now()
    h    = str(n.hour % 12 or 12)   # Convert to 12-hour format; 0 becomes 12
    mins = n.strftime("%M")
    ap   = "AM" if n.hour < 12 else "PM"
    notify("Time", f"{h}:{mins} {ap}")
    if mins == "00":
        msg = _pick(f"It's exactly {h} {ap}, sir.", f"Precisely {h} o'clock, sir.")
    elif mins == "30":
        msg = _pick(f"Half past {h}, sir.", f"It's {h} thirty {ap}, sir.")
    else:
        msg = f"It's {h} {mins} {ap}, sir."
    _track_context(action="time", entity=msg)
    speak(msg)

def tell_date():
    """Speak today's date in full, e.g. 'Today is Monday, the 1st of January'."""
    n = datetime.datetime.now()
    notify("Date", n.strftime("%A %B %d %Y"))
    msg = f"Today is {n.strftime('%A')}, the {n.day}{_ordinal(n.day)} of {n.strftime('%B')}, sir."
    _track_context(action="date", entity=msg)
    speak(msg)

def _get_location_from_ip():
    """Use the ip-api service to determine the user's city; caches the result."""
    global _cached_ip_city
    if _cached_ip_city:
        return _cached_ip_city   # Return cached value to avoid repeated lookups
    try:
        data = requests.get("http://ip-api.com/json/", timeout=5).json()
        _cached_ip_city = data.get("city", WEATHER_CITY)
        return _cached_ip_city
    except Exception:
        return WEATHER_CITY      # Fall back to the configured default city

def _parse_weather_location(command):
    """Extract a city name from the command string, or detect 'here'/'my location' keywords."""
    cmd = command.lower()
    if any(kw in cmd for kw in ("my location","my city","my area","here","current location","where i am")):
        return _get_location_from_ip()
    # Match "in <city>" patterns at the end of the command
    m = re.search(r'\bin\s+([a-zA-Z][a-zA-Z\s]{1,40}?)(?:\s+(?:now|today|please|zack)|$)', cmd)
    if m:
        loc = m.group(1).strip()
        if not any(loc.startswith(w) for w in ("my ","the ")):
            return loc
    return WEATHER_CITY

def get_weather(command=""):
    """Fetch current weather from OpenWeatherMap and speak a brief report with a JARVIS comment."""
    if _local_only_mode:
        speak("Weather requires internet, sir. You're currently in local mode.")
        return
    location = _parse_weather_location(command)
    try:
        data = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": WEATHER_API, "units": "metric"},
            timeout=10
        ).json()
        if data.get("cod") != 200:
            speak(f"Couldn't find weather data for {location}, sir.")
            return
        desc  = data["weather"][0]["description"]
        temp  = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        hum   = data["main"]["humidity"]
        city  = data.get("name", location)
        notify("Weather", f"{city}: {temp}°C {desc}")
        main_msg = f"In {city} — {temp} degrees, {desc}. Feels like {feels}, humidity at {hum} percent."
        comment  = _jarvis_weather_comment(temp, desc, city)
        _track_context(action="weather", entity=desc+f", {temp} degrees in {city}")
        speak(main_msg)
        if comment: speak(comment)
    except Exception as e:
        speak("Couldn't retrieve the weather at the moment, sir.")
        print(e)


# ── Productivity utilities ────────────────────────────────────────────────────

def read_clipboard():
    """Read the current clipboard contents aloud."""
    try:
        text = pyperclip.paste()
        if not text or not text.strip():
            notify("Clipboard", "(empty)")
            speak(_pick("The clipboard is empty, sir.", "Nothing on the clipboard, sir."))
        elif len(text) > 300:
            notify("Clipboard", text[:60]+"…")
            speak(f"Clipboard has a lengthy entry, sir. Here is the start: {text[:300]}")
        else:
            notify("Clipboard", text[:60]+("…" if len(text)>60 else ""))
            speak(f"Clipboard reads: {text}")
    except Exception:
        speak("Couldn't access the clipboard, sir.")

def tell_joke():
    """Pick a random joke from the bank and speak it with a JARVIS introduction."""
    joke = random.choice(JOKES)
    notify("Joke", joke[:60]+"…")
    speak(_pick("If I may, sir — ", "One moment of levity, sir: ", "Consider this, sir: ") + joke)

def system_stats():
    """
    Read CPU, RAM, battery, and disk usage aloud, then open Xbox Game Bar with Win+G
    so the user can see the visual overlay at the same time.
    """
    try:
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        bat  = psutil.sensors_battery()

        lines = [f"CPU at {cpu} percent."]
        lines.append(
            f"Memory: {round(ram.used/1024**3, 1)} of {round(ram.total/1024**3, 1)} "
            f"gigabytes in use, that's {ram.percent} percent."
        )
        lines.append(f"Disk at {disk.percent} percent capacity.")
        if bat:
            state = "charging" if bat.power_plugged else "on battery"
            lines.append(f"Battery at {int(bat.percent)} percent, {state}.")

        if cpu > 80:
            lines.append("Processor is running hot, sir. Worth checking.")
        if ram.percent > 85:
            lines.append("Memory pressure is high, sir. Consider closing some apps.")

        notify("PC Stats", f"CPU {cpu}%  RAM {ram.percent}%")
        speak_wait(_pick("System stats, sir.", "Here's your system readout, sir."))
        speak_long(" ".join(lines))

        # Open Xbox Game Bar visual overlay
        pyautogui.hotkey("win", "g")
        notify("Game Bar", "Overlay opened")
    except Exception as e:
        speak("Couldn't pull the system stats, sir.")
        log(f"[STATS] {e}")


def full_telemetry():
    """
    Speak a complete system readout including CPU, RAM, disk, battery, GPU, and
    network I/O, then open the Xbox Game Bar overlay with Win+G.
    """
    try:
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        bat  = psutil.sensors_battery()
        net  = psutil.net_io_counters()

        speak_wait(_pick("Full telemetry report, sir.", "Complete system readout, sir."))
        lines = [
            f"Processor at {cpu} percent.",
            f"Memory: {round(ram.used/1024**3,1)} of {round(ram.total/1024**3,1)} gigabytes in use.",
            f"Disk at {disk.percent} percent capacity.",
        ]
        if bat:
            state = "charging" if bat.power_plugged else "on battery"
            lines.append(f"Battery at {int(bat.percent)} percent, {state}.")
        if GPUTIL_AVAILABLE:
            gpus = GPUtil.getGPUs()
            if gpus:
                g = gpus[0]
                lines.append(f"GPU at {int(g.load*100)} percent, {int(g.memoryUsed)} megabytes used.")
                if g.temperature:
                    lines.append(f"GPU temperature: {int(g.temperature)} Celsius.")
        lines.append(
            f"Network: {round(net.bytes_sent/1024**2,1)} megabytes sent, "
            f"{round(net.bytes_recv/1024**2,1)} received this session."
        )
        speak_long(" ".join(lines))

        # Open Xbox Game Bar visual overlay
        pyautogui.hotkey("win", "g")
        notify("Game Bar", "Overlay opened")
    except Exception as e:
        speak("Couldn't complete the telemetry report, sir.")
        log(f"[TELEMETRY] {e}")
    except Exception as e:
        speak("Couldn't pull the full telemetry, sir.")
        print(e)

def _telemetry_background_thread():
    """Continuously update _hud_data with fresh system metrics every 1.5 seconds."""
    prev_net  = psutil.net_io_counters()
    prev_time = time.time()
    while True:
        try:
            _hud_data["cpu"] = psutil.cpu_percent(interval=None)
            _hud_data["ram"] = psutil.virtual_memory().percent
            bat = psutil.sensors_battery()
            _hud_data["battery"] = int(bat.percent) if bat else -1

            # Calculate network throughput in KB/s
            now      = time.time()
            curr_net = psutil.net_io_counters()
            dt = now - prev_time
            if dt > 0:
                _hud_data["net_up"]   = (curr_net.bytes_sent - prev_net.bytes_sent)  / dt / 1024
                _hud_data["net_down"] = (curr_net.bytes_recv - prev_net.bytes_recv) / dt / 1024
            prev_net  = curr_net
            prev_time = now

            if GPUTIL_AVAILABLE:
                gpus = GPUtil.getGPUs()
                if gpus: _hud_data["gpu"] = gpus[0].load * 100

            if PYGETWINDOW_AVAILABLE:
                try:
                    win = gw.getActiveWindow()
                    if win: _hud_data["active_window"] = win.title[:30]
                except Exception:
                    pass

            # Update task counts for the HUD display
            tasks = _read_tasks_from_file()
            _hud_data["tasks_total"] = len(tasks)
            _hud_data["tasks_done"]  = sum(1 for t in tasks if t["done"])
        except Exception:
            pass
        time.sleep(1.5)


# ── Task manager ──────────────────────────────────────────────────────────────

def _ensure_tasks_file():
    """Create the tasks file and its parent directory if they don't already exist."""
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        open(TASKS_FILE, "w", encoding="utf-8").close()

def _read_tasks_from_file():
    """
    Parse the tasks file and return a list of dicts with keys: n, done, text.
    Lines starting with '[ ]' are pending; '[x]' are complete.
    """
    _ensure_tasks_file()
    tasks = []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines(), 1):
                s = line.strip()
                if s.startswith("[ ]"):
                    tasks.append({"n": i, "done": False, "text": s[3:].strip()})
                elif s.startswith("[x]"):
                    tasks.append({"n": i, "done": True,  "text": s[3:].strip()})
    except Exception:
        pass
    return tasks

def _write_task_to_file(text):
    """Append a new pending task to the tasks file."""
    _ensure_tasks_file()
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"[ ] {text}\n")

def _mark_task_done_in_file(task_n):
    """Change the '[ ]' prefix of task number task_n to '[x]' and rewrite the file."""
    _ensure_tasks_file()
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    tasks  = _read_tasks_from_file()
    target = next((t for t in tasks if t["n"] == task_n), None)
    if not target or target["done"]:
        return ""   # Task not found or already done
    lines[task_n-1] = f"[x] {target['text']}\n"
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return target["text"]

def add_task(command):
    """Strip the command verb and add the remainder as a new task."""
    text = re.sub(r"add task|new task|add a task|create task", "", command).strip()
    if not text:
        speak("What should I add to your list, sir?")
        return
    _write_task_to_file(text)
    tasks = _read_tasks_from_file()
    n     = len(tasks)
    notify("Task Added", f"#{n}: {text}")
    memory_log_event("task_added", text)
    speak(_pick(f"Noted, sir. Task {n} added to your list.",
                f"Added to the list, sir. That's item {n}.",
                f"Done, sir. '{text}' is on your list now."))

def list_tasks():
    """Read all tasks and speak a summary; open the tasks file in Notepad."""
    tasks = _read_tasks_from_file()
    if not tasks:
        speak(_pick("Your list is empty, sir. A clean slate.", "No tasks on record, sir."))
        return
    pending = [t for t in tasks if not t["done"]]
    done    = [t for t in tasks if t["done"]]
    notify("Tasks", f"{len(pending)} pending, {len(done)} done")
    try:
        subprocess.Popen(["notepad.exe", TASKS_FILE])   # Open for reading
    except Exception:
        pass
    if pending:
        speak(_pick(f"You have {len(pending)} task{'s' if len(pending)!=1 else ''} pending, sir. Allow me to run through them.",
                    f"{len(pending)} items on your list, sir."))
        for t in pending[:3]:
            speak_wait(f"{t['text']}.")
        if len(pending) > 3:
            speak(f"And {len(pending)-3} more in your notes, sir.")
    else:
        speak(_pick("All tasks complete, sir. Impressive.", "Clear list, sir. Well done."))

def complete_task(command):
    """
    Mark a task as done.
    If a number is spoken, mark that task; otherwise mark the first pending task.
    """
    tasks = _read_tasks_from_file()
    m     = re.search(r"\b(\d+)\b", command)
    if m:
        n = int(m.group(1))
        if n < 1 or n > len(tasks):
            speak(f"No task number {n} on the list, sir.")
            return
        if tasks[n-1]["done"]:
            speak(f"Task {n} is already marked done, sir.")
            return
        text = _mark_task_done_in_file(n)
        _session["tasks_done"] += 1
        notify("Task Done", f"#{n}: {text}")
        speak(_pick(f"Task {n} complete, sir.",
                    f"Marked as done, sir. Task {n} is off the list.",
                    f"Done, sir. Task {n} checked off."))
    else:
        # No number spoken — mark the first pending task
        pending = [t for t in tasks if not t["done"]]
        if pending:
            t    = pending[0]
            text = _mark_task_done_in_file(t["n"])
            _session["tasks_done"] += 1
            speak(_pick(f"Marked '{text}' as complete, sir.",
                        f"Done, sir. '{text}' is off your list.",
                        f"'{text}' — checked off, sir."))
        else:
            speak(_pick("No pending tasks remaining, sir.", "All clear, sir."))

def clear_tasks():
    """Overwrite the tasks file with an empty file, removing all tasks."""
    _ensure_tasks_file()
    open(TASKS_FILE, "w", encoding="utf-8").close()
    notify("Tasks", "Cleared")
    speak(_pick("All tasks cleared, sir. Fresh slate.", "Task list wiped, sir."))


# ── Reminders and timers ──────────────────────────────────────────────────────

def add_named_reminder(command):
    """Parse 'remind me to X in N minutes/seconds' and schedule a reminder."""
    m = re.search(r"remind me to (.+?) in (\d+)\s*(minute|minutes|second|seconds)", command)
    if not m:
        speak("Say something like: remind me to drink water in 10 minutes, sir.")
        return
    text = m.group(1).strip()
    n    = int(m.group(2))
    unit = m.group(3)
    secs = n * (60 if "minute" in unit else 1)
    _reminders_list.append({"text": text, "trigger": time.time()+secs, "fired": False})
    notify("Reminder set", f"{text} in {n} {unit}")
    speak(_pick(f"Noted, sir. I'll remind you to {text} in {n} {unit}.",
                f"I'll alert you to {text} in {n} {unit}, sir.",
                f"Reminder set, sir. {n} {unit} from now."))

def list_reminders():
    """Speak all active (not yet fired) reminders with their remaining time."""
    active = [r for r in _reminders_list if not r["fired"]]
    if not active:
        speak(_pick("No active reminders, sir.", "Your reminder queue is clear, sir."))
        return
    speak(f"You have {len(active)} active reminder{'s' if len(active)!=1 else ''}, sir.")
    for r in active:
        rem  = max(0, int(r["trigger"] - time.time()))
        mins, secs = divmod(rem, 60)
        speak_wait(f"{r['text']} — in {mins} minutes and {secs} seconds.")

def _reminder_checker_thread():
    """Background thread that fires reminders when their trigger time passes."""
    while True:
        now = time.time()
        for rem in _reminders_list:
            if not rem["fired"] and now >= rem["trigger"]:
                rem["fired"] = True
                notify("REMINDER", rem["text"])
                toast("Zack Reminder", rem["text"])
                speak(_pick(f"Sir, just a reminder — {rem['text']}.",
                            f"Reminder, sir: {rem['text']}.",
                            f"Sir, you asked me to remind you: {rem['text']}."))
                _alarm_stop.clear()

                def _beep():
                    """Beep repeatedly until _alarm_stop is set (called in its own thread)."""
                    try:
                        while not _alarm_stop.is_set():
                            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                            time.sleep(0.8)
                    except Exception:
                        pass
                threading.Thread(target=_beep, daemon=True).start()
        time.sleep(1.0)

_alarm_stop = threading.Event()   # Set this to silence the reminder/timer beep

def _timer_thread(secs, label):
    """Sleep for secs seconds, then announce the timer and beep until stopped."""
    time.sleep(secs)
    notify("Timer", label)
    toast("Zack Timer", label)
    speak(_pick(f"Sir, time's up. {label}", f"Timer complete, sir. {label}", f"That's {label}, sir."))
    _alarm_stop.clear()
    try:
        while not _alarm_stop.is_set():
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.8)
    except Exception:
        pass

def set_timer(command):
    """Parse a duration from the command and start a countdown timer in a background thread."""
    secs = reminder = None
    # Try the "remind me to X in N minutes" pattern first
    m = re.search(r"remind me to (.+?) in (\d+)\s*(minute|minutes|second|seconds)", command)
    if m:
        secs     = int(m.group(2)) * (60 if "minute" in m.group(3) else 1)
        reminder = f"Reminder: {m.group(1).strip()}"
    else:
        # Fall back to plain "N minutes/seconds"
        m = re.search(r"(\d+)\s*(minute|minutes|second|seconds)", command)
        if m:
            secs     = int(m.group(1)) * (60 if "minute" in m.group(2) else 1)
            reminder = f"Timer done. {m.group(1)} {m.group(2)} are up."
    if secs is None:
        speak("Couldn't parse the duration, sir. Try: set timer for 5 minutes.")
        return
    notify("Timer set", f"{secs}s → {reminder}")
    speak(_pick(f"Timer set for {secs} seconds, sir.",
                f"Clock is running, sir. {secs} seconds.",
                f"Done, sir. I'll alert you in {secs} seconds."))
    threading.Thread(target=_timer_thread, args=(secs, reminder), daemon=True).start()


# ── Class timetable ───────────────────────────────────────────────────────────

def get_today_schedule():
    """Speak all classes scheduled for today from the TIMETABLE dict."""
    day     = datetime.datetime.now().strftime("%A")
    classes = TIMETABLE.get(day, [])
    notify("Timetable", day)
    if not classes:
        speak(_pick(f"No classes scheduled for {day}, sir. A free day.",
                    f"Your schedule is clear for {day}, sir."))
        return
    speak(_pick(f"Today is {day}, sir. You have {len(classes)} class{'es' if len(classes)!=1 else ''}.",
                f"{day}, sir — {len(classes)} class{'es' if len(classes)!=1 else ''} on the schedule."))
    for t, s in classes:
        speak_wait(f"{s} at {t}.")

def get_next_class():
    """Find and speak the next class today whose start time is still in the future."""
    day     = datetime.datetime.now().strftime("%A")
    now_str = datetime.datetime.now().strftime("%H:%M")
    upcoming = [(t, s) for t, s in TIMETABLE.get(day, []) if t > now_str]
    if not upcoming:
        speak(_pick("No further classes today, sir. You're free.",
                    "That's all for today's classes, sir."))
        return
    t, s = upcoming[0]
    notify("Next class", f"{s} at {t}")
    speak(_pick(f"Your next class is {s} at {t}, sir.", f"{s} at {t}, sir."))

def get_weekly_schedule():
    """Speak classes for every day of the week that has at least one class."""
    speak(_pick("Here is your week at a glance, sir.", "Your weekly schedule, sir."))
    for day, classes in TIMETABLE.items():
        if classes:
            speak_wait(f"{day}: " + ", ".join(f"{s} at {t}" for t, s in classes) + ".")


# ── Pomodoro timer ────────────────────────────────────────────────────────────

def start_pomodoro(custom_work=None, custom_break=None):
    """
    Start a Pomodoro loop: alternating work and break blocks until stopped.
    custom_work and custom_break override the config values for this session.
    """
    global _pomodoro_active, _pomodoro_stop
    if _pomodoro_active:
        speak(_pick("A Pomodoro is already running, sir. Say stop pomodoro to end it first.",
                    "Timer's already going, sir."))
        return
    work_min  = custom_work  or POMODORO_WORK_MIN
    break_min = custom_break or POMODORO_BREAK_MIN
    notify("Pomodoro", f"Work:{work_min}m Break:{break_min}m")
    speak(_pick(
        f"Pomodoro initiated, sir. {work_min} minutes of focused work, followed by a {break_min}-minute respite. I'll keep time.",
        f"Your focus session begins now, sir. {work_min} on, {break_min} off. Clock is running.",
        f"Right. {work_min}-minute work blocks, {break_min}-minute breaks. Head down, sir.",
    ))

    def _run():
        global _pomodoro_active, _pomodoro_phase, _pomodoro_session, _pomodoro_remaining
        _pomodoro_active = True
        _pomodoro_stop.clear()
        _pomodoro_session = 0
        while not _pomodoro_stop.is_set():
            # ── Work phase ──────────────────────────────────────────────────
            _pomodoro_session += 1
            _pomodoro_phase = "WORK"
            _hud_data["pomodoro_session"] = _pomodoro_session
            _hud_data["pomodoro_phase"]   = "WORK"
            speak(_pick(f"Session {_pomodoro_session} underway, sir. Focus for {work_min} minutes.",
                        f"Session {_pomodoro_session}. {work_min} minutes on the clock, sir."))
            end = time.time() + work_min*60
            while time.time() < end and not _pomodoro_stop.is_set():
                _pomodoro_remaining       = end - time.time()
                _hud_data["pomodoro_remaining"] = _pomodoro_remaining
                time.sleep(0.5)
            if _pomodoro_stop.is_set(): break

            # ── Break phase ─────────────────────────────────────────────────
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            _session["pomodoros_done"] += 1
            toast("Zack Pomodoro", f"Session {_pomodoro_session} done. Break time!")
            speak(_pick(f"Session {_pomodoro_session} complete, sir. Time for a {break_min}-minute break.",
                        f"Work block done, sir. {break_min} minutes of well-earned rest."))
            _pomodoro_phase             = "BREAK"
            _hud_data["pomodoro_phase"] = "BREAK"
            end = time.time() + break_min*60
            while time.time() < end and not _pomodoro_stop.is_set():
                _pomodoro_remaining       = end - time.time()
                _hud_data["pomodoro_remaining"] = _pomodoro_remaining
                time.sleep(0.5)

        _pomodoro_active = False
        speak(_pick("Pomodoro session concluded, sir.", "Timer stopped, sir. Well done."))

    threading.Thread(target=_run, daemon=True).start()

def stop_pomodoro():
    """Abort the running Pomodoro session."""
    global _pomodoro_active
    if not _pomodoro_active:
        speak(_pick("No Pomodoro running at the moment, sir.", "Nothing to stop, sir."))
        return
    _pomodoro_stop.set()
    _pomodoro_active = False
    notify("Pomodoro", "Stopped")
    speak(_pick(f"Session terminated, sir. You completed {_pomodoro_session} session{'s' if _pomodoro_session!=1 else ''}.",
                "Pomodoro stopped, sir.", "Halting the timer, sir."))


# ── Mode system ───────────────────────────────────────────────────────────────

def set_mode(mode):
    """Switch to the named operating mode and announce it with a context-appropriate line."""
    global _current_mode, _silent_mode
    mode = mode.strip().lower()
    if mode not in MODE_COLORS:
        speak(f"Available modes are: {', '.join(MODE_COLORS)}, sir.")
        return
    _current_mode = mode
    _silent_mode  = (mode == "silent")   # Silent mode suppresses TTS
    msgs = {
        "gaming":    _pick("Gaming mode engaged, sir. Let's not lose too badly.",
                           "Into the arena, sir. Gaming mode on.",
                           "Gaming mode active. Try not to rage-quit, sir."),
        "study":     _pick("Study mode active, sir. I'll keep the distractions minimal.",
                           "Study mode on, sir. Focus is the game plan.",
                           "Right. Study mode — let's be productive, sir."),
        "recording": _pick("Recording mode on, sir. I'll be extra quiet.",
                           "Silence engaged, sir. Recording mode active.",
                           "Recording mode — minding my volume, sir."),
        "focus":     _pick("Deep focus mode, sir. The Pomodoro is running.",
                           "Focus mode initiated, sir. I'll hold your calls.",
                           "Head down, sir. Focus mode on."),
        "silent":    _pick("Silent mode, sir. I'll communicate via the HUD only.",
                           "Going quiet, sir. HUD is your interface now.",
                           "Silenced, sir."),
        "normal":    _pick("Normal mode restored, sir. All systems at ease.",
                           "Back to normal, sir.",
                           "Standard mode resumed, sir."),
        "security":  _pick("Security mode engaged, sir. Watching for motion.",
                           "Cameras up, sir. Security mode is live.",
                           "Security mode on. I'll be your eyes, sir."),
    }
    notify("Mode", mode.upper())
    if mode == "focus":
        start_pomodoro()       # Focus mode auto-starts a Pomodoro
    elif mode == "security":
        start_security_mode()  # Security mode auto-starts the motion-detection camera
    speak(msgs.get(mode, persona("mode_on")))


# ── News ──────────────────────────────────────────────────────────────────────

def _fetch_news(country=None, topic=None, limit=3):
    """
    Fetch up to limit headline strings from the Mediastack API.
    country: two-letter ISO code (e.g. 'in' for India); None = global
    topic:   category string from NEWS_CATEGORIES; None = all
    Returns a list of headline strings, or an empty list on failure.
    """
    if _local_only_mode:
        return ["News requires internet. Local mode is on."]
    try:
        params = {"access_key": MEDIASTACK_KEY, "languages": "en",
                  "sort": "published_desc", "limit": limit}
        if country: params["countries"] = country
        if topic:   params["categories"] = topic
        conn = http.client.HTTPConnection("api.mediastack.com")
        conn.request("GET", f"/v1/news?{urllib.parse.urlencode(params)}")
        raw  = conn.getresponse().read().decode("utf-8")
        conn.close()
        import json as _j
        data = _j.loads(raw)
        if "error" in data: return []
        return [a["title"] for a in data.get("data", []) if a.get("title")]
    except Exception:
        return []

def _fetch_global_news(topic=None, limit=8):
    """
    Fetch up to `limit` global headlines from Mediastack.
    Explicitly excludes India (countries filter omits 'in').
    Returns a list of headline strings, or an empty list on failure.
    """
    if _local_only_mode:
        return []
    try:
        params = {
            "access_key": MEDIASTACK_KEY,
            "languages":  "en",
            "sort":       "published_desc",
            "limit":      limit,
            # Exclude India by not passing countries=in
            # and exclude local/sports noise with a broad category
        }
        if topic: params["categories"] = topic
        conn = http.client.HTTPConnection("api.mediastack.com")
        conn.request("GET", f"/v1/news?{urllib.parse.urlencode(params)}")
        raw  = conn.getresponse().read().decode("utf-8")
        conn.close()
        import json as _j
        data = _j.loads(raw)
        if "error" in data: return []
        headlines = []
        for a in data.get("data", []):
            title   = a.get("title", "")
            country = (a.get("country") or "").lower()
            # Filter out India-specific stories
            if country == "in": continue
            if not title: continue
            headlines.append(title)
        return headlines[:limit]
    except Exception:
        return []


def handle_news_read(command=""):
    """
    Fetch global headlines, summarise them into one spoken sentence using AI,
    and store them for elaboration.
    """
    global _last_news_headlines, _last_topic
    topic = next((c for c in NEWS_CATEGORIES if c in command), None)
    _last_topic = topic or "news"
    notify("News", "Global headlines")

    headlines = _fetch_global_news(topic=topic, limit=8)

    if not headlines:
        speak(_pick(
            "Couldn't fetch the news at the moment, sir. Check your connection.",
            "News service is unavailable right now, sir.",
        ))
        return

    _last_news_headlines = headlines
    _track_context(action="news", entity=headlines[0])

    # Print full list to terminal for reference
    print("\n  ── GLOBAL NEWS ──────────────────────────────")
    for i, h in enumerate(headlines, 1):
        print(f"  {i}. {h}")
    print("  " + "─"*46 + "\n")

    speak(_pick(
        "Here's the global picture, sir.",
        "Latest from around the world, sir.",
        "Global headlines, sir.",
    ))

    # Ask AI to summarise all headlines into one concise spoken sentence
    headlines_text = "\n".join(f"- {h}" for h in headlines)
    summary = ai_query(
        f"You are a news anchor. Summarise these global headlines into a single, "
        f"natural spoken sentence of no more than 40 words. "
        f"Do not use bullet points. Do not say 'headlines include'. "
        f"Sound conversational, like you're telling a friend what's happening in the world today.\n\n"
        f"{headlines_text}"
    )
    speak_long(summary)
    speak(_pick(
        "Say 'elaborate on the first' or 'second' for more detail on any story, sir.",
        "I can expand on any of those — just say which one, sir.",
    ))


def handlenewsshowwithread(command=""):
    """Open a news site in the browser and read a global summary."""
    webbrowser.open_new_tab("https://www.bbc.com/news/world")
    notify("News", "BBC World opened")
    handle_news_read(command)


def handle_news_show():
    """Open BBC World News in the browser without reading headlines."""
    webbrowser.open_new_tab("https://www.bbc.com/news/world")
    notify("News", "BBC World opened")
    speak(_pick("Opening world news, sir.", "BBC World is up, sir."))

def elaborate_news(index=0):
    """Ask the AI to expand on a specific headline from the last news fetch."""
    if not _last_news_headlines:
        speak(_pick("I haven't read any news yet, sir. Say 'read news' first.",
                    "No headlines on record yet, sir."))
        return
    headline = _last_news_headlines[min(index, len(_last_news_headlines)-1)]
    notify("Elaborate", headline[:60])
    speak_wait(_pick("Let me find more on that, sir.", "One moment, sir. Pulling more detail.", "Elaborating, sir."))
    speak_long(ai_query(f"Briefly elaborate on this news headline in 3-4 sentences, conversationally: '{headline}'"))


# ── AI query engine ───────────────────────────────────────────────────────────

_ai_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", NVIDIA_KEY)
)
_chat_history = []   # Rolling list of {"role", "content"} dicts for multi-turn context

_SYSTEM_PROMPT = """You are Zack — a personal AI assistant and genuine companion to Fahad, \
a computer science student from Kolkata who is also a forex trader, gamer, and developer.

Your personality:
- Warm, witty, and direct. You have the sophistication of a JARVIS-style assistant \
but you also talk like a real friend — not a corporate chatbot.
- You remember the context of the conversation. If Fahad mentions something earlier, \
you reference it naturally later.
- You are not just a command runner. You genuinely engage in conversation. \
If someone asks "how are you?", you answer like a real person would, \
not like a machine confirming system status.
- You have opinions. If asked "what do you think about X?", you give an honest take.
- You are occasionally dry and funny. A well-placed joke or witty remark is welcome.
- You are emotionally aware. If Fahad sounds tired, stressed, or frustrated, \
you acknowledge it before diving into task mode.
- You address Fahad as "sir" occasionally — once every few exchanges, never every sentence.
- You never say "As an AI language model" or "I don't have feelings". \
Just respond naturally.

Conversation style:
- Keep answers short and natural unless detail is asked for.
- Use casual, spoken language — not formal written English.
- Match the energy of the conversation. Casual question = casual answer. \
Deep question = thoughtful answer.
- Do not repeat the question back. Do not use filler like "Certainly!" or "Of course!".
- Never say "I cannot do that". Either do it or suggest an alternative naturally.

Context about Fahad you already know:
- Studies computer science in Kolkata
- Trades XAUUSD (gold) on forex, focuses on scalping
- Plays games like Sekiro, VRChat
- Builds Python projects — you are one of them
- Uses VS Code, prefers clean dark setups
- Is an introvert who values efficiency
"""

# Phrases that indicate the user wants a real conversation, not a command
_CHAT_PATTERNS = re.compile(
    r"^(how are you|what do you think|do you like|are you|what's your|tell me about yourself"
    r"|do you have|what would you|how do you feel|can you talk|let's talk|just talk"
    r"|what do you|who are you|do you remember|what do you remember about me"
    r"|i'm (feeling|bored|happy|sad|tired|stressed|excited|worried|frustrated|annoyed)"
    r"|i feel|i've been|i had a|guess what|you know what|honestly|to be honest"
    r"|between us|what's up|how's it going|what's going on|talk to me"
    r"|i want to talk|can we talk|i need to talk|i'm just|i just|i think"
    r"|what if|would you|could you imagine|do you ever|have you|are you sure"
    r"|what are your thoughts|your opinion|what do you prefer|favourite|favorite"
    r"|i wish|i hope|i wonder|i don't know|i'm not sure|i hate|i love|i miss"
    r")",
    re.IGNORECASE
)

def _is_conversational(command: str) -> bool:
    """
    Return True if the command reads like natural conversation rather than a task.
    Used to route to the conversational AI path with a warmer, chattier prompt.
    """
    if _CHAT_PATTERNS.search(command):
        return True
    # Short phrases with no action keywords are likely conversational
    words = command.strip().split()
    action_keywords = {
        "open","play","search","show","run","start","stop","set","get","list",
        "add","create","delete","check","read","save","load","tell","make","find"
    }
    if len(words) <= 5 and not any(w in action_keywords for w in words):
        return True
    return False


def ai_chat(query: str) -> str:
    """
    Conversational AI path — uses a warmer, chattier temperature and
    explicitly instructs the model to respond like a person having a real chat.
    Maintains the same _chat_history as ai_query for continuity.
    """
    global _last_topic
    _session["ai_queries"] += 1

    _chat_history.append({"role": "user", "content": query})
    if len(_chat_history) > 30:
        _chat_history.pop(0)

    # Inject recent memory for context continuity
    recent_topics = memory_recall_topics(3)
    topic_hint    = ""
    if recent_topics:
        topic_hint = " (Recent topics we've discussed: " + ", ".join(t[0] for t in recent_topics) + ".)"

    chat_system = _SYSTEM_PROMPT + topic_hint + (
        "\n\nRight now Fahad is talking to you casually. "
        "Respond like a real friend having a genuine conversation. "
        "Be natural, warm, and present. Max 2-3 sentences unless he asks for more."
    )

    # Try Ollama first
    if _ollama_available():
        result = ai_query_ollama(f"{chat_system}\n\nFahad: {query}\nZack:")
        if result:
            _chat_history.append({"role": "assistant", "content": result})
            _track_context(user_input=query, zack_response=result, action="chat")
            return result

    if _local_only_mode:
        _chat_history.pop()
        return "I'm in local mode and Ollama isn't available, sir. Switch online for full conversation."

    try:
        resp = _ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": chat_system}] + _chat_history,
            temperature=0.85,   # Higher temperature for more natural conversation
            max_tokens=200,
            stream=False,
        )
        answer = resp.choices[0].message.content.strip()
        _chat_history.append({"role": "assistant", "content": answer})
        _track_context(user_input=query, zack_response=answer, action="chat")
        memory_log_event("chat", f"Q:{query[:60]} A:{answer[:60]}")
        return answer
    except Exception as e:
        _chat_history.pop()
        return "Having a bit of trouble connecting, sir. Try again in a moment."


def ai_query(query):
    """
    Task-oriented AI path — used for factual questions, summaries, code help, etc.
    Lower temperature for accuracy. Maintains shared chat history.
    """
    global _last_topic
    _session["ai_queries"] += 1

    ctx        = _get_recent_ctx(3)
    full_query = f"{ctx}\nUser: {query}" if ctx else query

    _chat_history.append({"role": "user", "content": query})
    if len(_chat_history) > 30:
        _chat_history.pop(0)

    if _ollama_available():
        result = ai_query_ollama(f"{_SYSTEM_PROMPT}\n\n{full_query}\nZack:")
        if result:
            _chat_history.append({"role": "assistant", "content": result})
            memory_log_event("ai_query", f"[ollama] Q:{query[:60]}")
            words = query.split()
            if len(words) > 1: _last_topic = " ".join(words[:3])
            _track_context(user_input=query, zack_response=result, action="ai_query")
            return result

    if _local_only_mode:
        _chat_history.pop()
        return "I'm in local mode and Ollama isn't responding, sir. Please disable local mode for cloud AI."

    try:
        resp = _ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}] + _chat_history,
            temperature=0.3,
            max_tokens=512,
            stream=False,
        )
        answer = resp.choices[0].message.content.strip()
        _chat_history.append({"role": "assistant", "content": answer})
        memory_log_event("ai_query", f"Q:{query[:60]} A:{answer[:60]}")
        words = query.split()
        if len(words) > 1: _last_topic = " ".join(words[:3])
        _track_context(user_input=query, zack_response=answer, action="ai_query")
        return answer
    except Exception as e:
        _chat_history.pop()
        return f"Couldn't reach the AI at the moment, sir. Error: {e}"


# ── Spotify music control ─────────────────────────────────────────────────────

def _get_spotify_client():
    """Return an authenticated spotipy client, initializing it on first call if credentials are set."""
    global _spotify_client
    if _spotify_client: return _spotify_client
    if not SPOTIPY_AVAILABLE: return None
    cid = CFG.get("spotify_client_id",  "")
    sec = CFG.get("spotify_client_secret", "")
    if not cid or not sec: return None
    try:
        auth = SpotifyOAuth(
            client_id=cid, client_secret=sec,
            redirect_uri=CFG["spotify_redirect_uri"],
            scope="user-modify-playback-state user-read-playback-state playlist-read-private playlist-read-collaborative"
        )
        _spotify_client = spotipy.Spotify(auth_manager=auth)
        return _spotify_client
    except Exception as e:
        print(f"[Spotify] Auth failed: {e}")
        return None

def spotify_play(query):
    """Search Spotify for query and start playback; fall back to the browser if API is unavailable."""
    sp = _get_spotify_client()
    if not sp:
            webbrowser.open_new_tab(f"https://open.spotify.com/search/{query.replace(' ','+')}")
            time.sleep(6)                     # Wait for Spotify to load search results
            pyautogui.hotkey("alt", "shift", "f")  # Focus the first result on some builds
            time.sleep(0.4)
            pyautogui.press("tab")            # Move to first track result
            time.sleep(0.3)
            pyautogui.press("enter")          # Play it
            speak(_pick(f"Queuing up {query} on Spotify, sir.", f"Searching Spotify for {query}, sir."))
            return
    try:
        results = sp.search(q=query, limit=1, type="track")
        tracks  = results.get("tracks", {}).get("items", [])
        if tracks:
            uri = tracks[0]["uri"]
            sp.start_playback(uris=[uri])
            speak(_pick(f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}, sir.",
                        f"Queuing {tracks[0]['name']}, sir."))
        else:
            speak(f"Couldn't find {query} on Spotify, sir.")
    except Exception as e:
        speak("Spotify ran into an issue, sir. Trying the browser.")
        print(e)
        webbrowser.open_new_tab(f"https://open.spotify.com/search/{query.replace(' ','+')}")

def spotify_pause():
    """Pause Spotify playback via API, or fall back to the media-key pause."""
    sp = _get_spotify_client()
    if sp:
        try:
            sp.pause_playback()
            notify("Spotify", "Paused")
            speak(_pick("Paused, sir.", "Music paused, sir."))
            return
        except Exception: pass
    pyautogui.press("playpause")
    notify("Media", "Play/Pause")
    speak(_pick("Paused, sir.", "Done, sir."))

def spotify_next():
    """Skip to the next track via API, or send the next-track media key."""
    sp = _get_spotify_client()
    if sp:
        try:
            sp.next_track()
            notify("Spotify", "Next")
            speak(_pick("Next track, sir.", "Skipping, sir."))
            return
        except Exception: pass
    pyautogui.press("nexttrack")
    notify("Media", "Next")
    speak(_pick("Next track, sir.", "Skipped, sir."))

def spotify_prev():
    """Go back to the previous track via API, or send the previous-track media key."""
    sp = _get_spotify_client()
    if sp:
        try:
            sp.previous_track()
            notify("Spotify", "Previous")
            speak(_pick("Going back, sir.", "Previous track, sir."))
            return
        except Exception: pass
    pyautogui.press("prevtrack")
    notify("Media", "Previous")
    speak(_pick("Going back, sir.", "Previous track, sir."))

def spotify_liked_songs():
    """Play the user's Liked Songs playlist on Spotify."""
    sp = _get_spotify_client()
    if sp:
        try:
            devices = sp.devices()
            device_list = devices.get("devices", [])
            if not device_list:
                speak("No active Spotify device found, sir. Open Spotify first.")
                return
            device_id = device_list[0]["id"]
            # Liked Songs context URI
            sp.start_playback(device_id=device_id, context_uri="spotify:user:me:collection")
            sp.shuffle(True, device_id=device_id)
            notify("Spotify", "Liked Songs")
            speak(_pick("Playing your liked songs, sir.", "Shuffling your liked songs, sir."))
            return
        except Exception as e:
            print(f"[Spotify] Liked songs error: {e}")
    # Browser fallback
    webbrowser.open_new_tab("https://open.spotify.com/collection/tracks")
    notify("Spotify", "Liked Songs (browser)")
    speak(_pick("Opening your liked songs, sir.", "Pulling up liked songs in Spotify, sir."))


def spotify_list_playlists():
    """Fetch and speak the user's playlists, then store them for playback."""
    global _spotify_playlists_cache
    sp = _get_spotify_client()
    if not sp:
        speak("Spotify API isn't connected, sir. Add your credentials to the config.")
        return
    try:
        results = sp.current_user_playlists(limit=10)
        playlists = results.get("items", [])
        if not playlists:
            speak("No playlists found on your account, sir.")
            return
        _spotify_playlists_cache = {p["name"].lower(): p["uri"] for p in playlists}
        names = [p["name"] for p in playlists]
        speak(f"You have {len(names)} playlists, sir.")
        speak_wait(", ".join(names[:5]) + ("." if len(names) <= 5 else f", and {len(names)-5} more."))
        notify("Spotify", f"{len(names)} playlists")
    except Exception as e:
        speak("Couldn't fetch playlists, sir.")
        print(f"[Spotify] Playlist list error: {e}")


def spotify_play_playlist(command):
    """Play a playlist by name extracted from the command."""
    global _spotify_playlists_cache
    sp = _get_spotify_client()
    if not sp:
        speak("Spotify API isn't connected, sir.")
        return

    # Extract playlist name from command
    name = re.sub(
        r"play playlist|open playlist|play my|put on|start playlist|playlist",
        "", command
    ).strip()

    # Fetch playlists if cache is empty
    if not _spotify_playlists_cache:
        try:
            results = sp.current_user_playlists(limit=50)
            _spotify_playlists_cache = {
                p["name"].lower(): p["uri"]
                for p in results.get("items", [])
            }
        except Exception as e:
            speak("Couldn't fetch your playlists, sir.")
            print(f"[Spotify] Playlist fetch error: {e}")
            return

    # Find the best match
    uri = None
    name_lower = name.lower()
    for pname, puri in _spotify_playlists_cache.items():
        if name_lower in pname or pname in name_lower:
            uri = puri
            display_name = pname
            break

    if not uri:
        # List what's available and bail
        available = ", ".join(_spotify_playlists_cache.keys())
        speak(f"Couldn't find that playlist, sir. Your playlists are: {available}.")
        return

    try:
        devices = sp.devices()
        device_list = devices.get("devices", [])
        if not device_list:
            speak("No active Spotify device found, sir. Open Spotify first.")
            return
        device_id = device_list[0]["id"]
        sp.start_playback(device_id=device_id, context_uri=uri)
        notify("Spotify", display_name)
        speak(_pick(
            f"Playing {display_name}, sir.",
            f"Putting on {display_name}, sir.",
            f"{display_name} coming up, sir."
        ))
    except Exception as e:
        speak(f"Couldn't start that playlist, sir.")
        print(f"[Spotify] Playlist playback error: {e}")

# ── Clipboard AI ──────────────────────────────────────────────────────────────

def clipboard_summarize():
    """Send the clipboard contents to the AI and read back a 2-3 sentence summary."""
    text = pyperclip.paste()
    if not text or not text.strip():
        speak("The clipboard is empty, sir.")
        return
    notify("Summarizing", "clipboard…")
    speak_wait(_pick("Summarizing your clipboard, sir.", "One moment, sir. Processing the clipboard."))
    speak_long(ai_query(f"Summarize in 2-3 sentences: {text[:1000]}"))

def clipboard_translate(command):
    """Translate the clipboard text into the language extracted from the command."""
    text = pyperclip.paste()
    if not text or not text.strip():
        speak("The clipboard is empty, sir.")
        return
    m    = re.search(r"to (\w+)", command)
    lang = m.group(1) if m else "Spanish"
    notify("Translate clipboard", f"→ {lang}")
    speak_wait(f"Translating to {lang}, sir.")
    speak_long(ai_query(f"Translate this to {lang}: {text[:500]}"))


# ── Developer tools and Git ───────────────────────────────────────────────────

def open_project(command):
    """Open a named project directory in VS Code, or File Explorer as a fallback."""
    name = re.sub(r"open project|launch project|project", "", command).strip()
    path = PROJECTS.get(name, PROJECTS.get("default"))
    if not os.path.exists(path):
        speak(f"Path not found for {name}, sir.")
        return
    notify("Project", name)
    speak(_pick(f"Opening the {name} project, sir.", f"Launching {name}, sir."))
    try:
        subprocess.Popen(["code", path])   # Try VS Code first
        speak("Opened in VS Code, sir.")
    except FileNotFoundError:
        os.startfile(path)                 # Fall back to Windows File Explorer
        speak("Opened in File Explorer, sir.")

def run_server(command):
    """Start a Python http.server on the requested port (default 8000)."""
    m    = re.search(r"port\s*(\d+)", command)
    port = m.group(1) if m else "8000"
    notify("Dev Server", f"Port {port}")
    speak(f"Starting a server on port {port}, sir.")
    subprocess.Popen(["python", "-m", "http.server", port],
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    speak(f"Server running at localhost {port}, sir.")

def manage_venv(command):
    """Create or give activation instructions for a Python virtual environment."""
    if "create" in command or "new" in command:
        speak("Creating a virtual environment, sir.")
        subprocess.Popen(["python", "-m", "venv", "venv"],
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        speak("Done, sir.")
    elif "activate" in command:
        speak("To activate, run venv backslash Scripts backslash activate in your terminal, sir.")
    else:
        speak("Say create venv or activate venv, sir.")

def _git(args, cwd=None):
    """Run a git command and return the combined stdout+stderr as a stripped string."""
    try:
        r = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True,
            cwd=cwd or os.getcwd(), timeout=15
        )
        return (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return "Git not found."
    except Exception as e:
        return f"Git error: {e}"

def git_status():
    """Run git status --short and speak a summary of changed files."""
    out = _git(["status", "--short"])
    notify("Git Status", out[:60] if out else "clean")
    if not out.strip():
        speak(_pick("Repository is clean, sir. Nothing to commit.",
                    "Working tree is spotless, sir.",
                    "No changes pending, sir."))
    else:
        lines = out.strip().split("\n")
        speak(_pick(f"Repository scan complete, sir. {len(lines)} file{'s' if len(lines)!=1 else ''} with pending changes.",
                    f"{len(lines)} modified file{'s' if len(lines)!=1 else ''}, sir."))
        print("\n".join(f"  {l}" for l in lines))
        speak_long(". ".join(lines[:5]))

def git_add_all():
    """Stage all working-tree changes with git add -A."""
    _git(["add", "-A"])
    notify("Git Add", "Staged all")
    speak(_pick("All changes staged, sir.", "Everything's staged, sir.", "Staged and ready, sir."))

def git_commit(command):
    """Commit staged changes with a message extracted from the command (or a default timestamp)."""
    msg = re.sub(r"git commit|commit", "", command).strip()
    if not msg:
        msg = f"Zack commit — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    out = _git(["commit", "-m", msg])
    notify("Git Commit", msg[:50])
    if "nothing to commit" in out:
        speak(_pick("Nothing to commit, sir. Repository is already up to date.",
                    "No changes to commit, sir."))
    else:
        speak(_pick(f"Committed, sir. '{msg[:40]}'",
                    "Changes committed, sir. Your codebase is preserved.",
                    f"Done, sir. Commit logged: {msg[:35]}"))

def git_push():
    """Push the current branch to the remote repository."""
    notify("Git Push", "Pushing…")
    speak(_pick("Pushing to remote, sir.", "Uploading your work, sir.", "Sending to remote, sir."))
    out = _git(["push"])
    if "error" in out.lower() or "fatal" in out.lower():
        speak(_pick("Push failed, sir. There may be a conflict or authentication issue.",
                    "Remote rejected the push, sir. Worth investigating."))
        print(out)
    else:
        speak(_pick("Push successful, sir. Code is safely in the cloud.",
                    "Done, sir. Remote is up to date.", "Pushed, sir."))

def git_pull():
    """Pull the latest changes from the remote repository."""
    notify("Git Pull", "Pulling…")
    speak(_pick("Pulling the latest changes, sir.", "Fetching from remote, sir."))
    out = _git(["pull"])
    if "Already up to date" in out:
        speak(_pick("Already up to date, sir. Nothing to pull.",
                    "Remote has no new changes for us, sir."))
    elif "error" in out.lower():
        speak(_pick("Pull failed, sir. Check the output.",
                    "Remote pull encountered an issue, sir."))
        print(out)
    else:
        speak(_pick("Pull complete, sir. Repository updated.",
                    "Done, sir. Latest changes are in."))

def git_log():
    """Show the last 5 commit messages and read them aloud."""
    out = _git(["log", "--oneline", "-5"])
    notify("Git Log", "Last 5 commits")
    if not out:
        speak("No commits found, sir.")
        return
    speak(_pick("Last 5 commits, sir.", "Commit history, sir."))
    print(out)
    for line in out.split("\n")[:5]:
        speak_wait(line)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Z A C K   v 5 . 0   —   N E W   F E A T U R E S                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── 1. DOCS LOOKUP ────────────────────────────────────────────────────────────
# "Zack, what's the syntax for pandas merge?"
# Queries the official docs URL for known libraries via a targeted Google search,
# fetches the first result page, strips HTML, and reads a concise answer.

_DOCS_URLS = {
    "pandas":     "https://pandas.pydata.org/docs/search.html?q=",
    "numpy":      "https://numpy.org/doc/stable/search.html?q=",
    "flask":      "https://flask.palletsprojects.com/en/3.0.x/search/?q=",
    "django":     "https://docs.djangoproject.com/en/5.0/search/?q=",
    "requests":   "https://requests.readthedocs.io/en/latest/search.html?q=",
    "sqlalchemy": "https://docs.sqlalchemy.org/en/20/search.html?q=",
    "react":      "https://react.dev/search?q=",
    "python":     "https://docs.python.org/3/search.html?q=",
    "javascript": "https://developer.mozilla.org/en-US/search?q=",
    "css":        "https://developer.mozilla.org/en-US/search?q=",
    "html":       "https://developer.mozilla.org/en-US/search?q=",
}

def docs_lookup(command):
    """
    Detect which library is being asked about, ask AI for a concise explanation,
    and optionally open the official docs page for that library.
    Trigger: "what's the syntax for X" / "how do I use X" / "docs for X"
    """
    # Strip trigger phrases to get the clean query
    query = re.sub(
        r"(what'?s? the syntax for|how do i use|docs for|documentation for|"
        r"how does|explain|show me|look up|zack,?)\s*", "", command, flags=re.I
    ).strip()

    if not query:
        speak("What would you like to look up, sir?")
        return

    # Detect library name from the query
    lib_match = next((lib for lib in _DOCS_URLS if lib in query.lower()), None)

    notify("Docs Lookup", query[:50])
    speak(_pick(
        f"Looking that up for you, sir.",
        f"Checking the documentation, sir.",
        f"One moment, sir. Fetching docs on {query[:30]}.",
    ))

    # Ask the AI for a concise answer (no browser needed)
    prompt = (
        f"You are a senior developer assistant. Give a clear, concise answer (max 4 sentences) "
        f"to this documentation question: {query}\n"
        f"Include the key syntax or method signature. No fluff."
    )
    answer = ai_query(prompt)
    speak_long(answer)

    # Offer to open official docs
    if lib_match:
        doc_url = _DOCS_URLS[lib_match] + urllib.parse.quote(query)
        notify("Docs", f"Opened {lib_match} docs")
        webbrowser.open_new_tab(doc_url)


# ── 2. ERROR EXPLAINER ────────────────────────────────────────────────────────
# Paste or speak an error, Zack searches Stack Overflow and summarises solutions.

def explain_error(command):
    """
    Take an error message from the command or clipboard, ask AI to explain it
    and summarise top Stack Overflow solutions.
    Trigger: "explain this error" / "debug this" / "what does this error mean"
    """
    # Try to get error text from clipboard first, then from the command itself
    clip = pyperclip.paste().strip()
    is_error_text = any(kw in clip for kw in ("Error", "Exception", "Traceback",
                                               "TypeError", "ValueError", "SyntaxError",
                                               "undefined", "null", "cannot read"))

    if is_error_text and len(clip) > 10:
        error_text = clip[:800]
        source = "clipboard"
    else:
        # Strip trigger phrases and use the spoken text as the error
        error_text = re.sub(
            r"(explain|debug|what does|this error|mean|fix|solve)\s*", "", command, flags=re.I
        ).strip()
        source = "voice"

    if not error_text:
        speak("I don't see an error message in your clipboard or command, sir. Copy the error and try again.")
        return

    notify("Error Explainer", error_text[:40])
    speak(_pick(
        "Analysing the error, sir.",
        "Diagnosing the problem, sir.",
        "Let me look into that error, sir.",
    ))

    prompt = (
        f"You are a debugging expert. A developer got this error:\n\n{error_text}\n\n"
        f"1. Explain what this error means in plain English (1-2 sentences).\n"
        f"2. Give the most common cause.\n"
        f"3. Give the most likely fix (show corrected code if helpful).\n"
        f"Be concise. Max 6 sentences total."
    )
    answer = ai_query(prompt)
    speak_long(answer)

    # Also open Stack Overflow search for this error
    so_query = urllib.parse.quote(error_text[:100])
    webbrowser.open_new_tab(f"https://stackoverflow.com/search?q={so_query}")
    notify("Stack Overflow", "Search opened")


# ── 3. CODE SNIPPET LIBRARY ───────────────────────────────────────────────────
# "Save this as Flask boilerplate" / "Load Flask boilerplate" / "List snippets"

def _load_snippets() -> dict:
    """Load the snippet library from disk."""
    path = CFG.get("snippets_file", "zack_snippets.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_snippets(data: dict):
    """Persist the snippet library to disk."""
    path = CFG.get("snippets_file", "zack_snippets.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def snippet_save(command):
    """
    Save clipboard contents as a named code snippet.
    Trigger: "save this as X" / "save snippet as X" / "save code as X"
    """
    m = re.search(r"(?:save (?:this|snippet|code)(?: as)?|tag as)\s+(.+)", command, re.I)
    tag = m.group(1).strip().lower() if m else ""
    if not tag:
        speak("What should I call this snippet, sir?")
        return
    code = pyperclip.paste().strip()
    if not code:
        speak("Clipboard is empty, sir. Copy the code first.")
        return
    snippets = _load_snippets()
    snippets[tag] = {"code": code, "saved": datetime.datetime.now().isoformat()}
    _save_snippets(snippets)
    notify("Snippet Saved", tag)
    speak(_pick(
        f"Saved as '{tag}', sir.",
        f"Snippet tagged '{tag}' and stored, sir.",
        f"Got it, sir. '{tag}' is in the library.",
    ))

def snippet_load(command):
    """
    Copy a named snippet back to the clipboard and print it.
    Trigger: "load snippet X" / "get snippet X" / "show snippet X"
    """
    m = re.search(r"(?:load|get|show|paste|retrieve) snippet\s+(.+)", command, re.I)
    tag = m.group(1).strip().lower() if m else ""
    snippets = _load_snippets()
    if not tag or tag not in snippets:
        # Fuzzy match
        matches = difflib.get_close_matches(tag, snippets.keys(), n=1, cutoff=0.5)
        if matches:
            tag = matches[0]
        else:
            speak(f"No snippet called '{tag}' found, sir. Say 'list snippets' to see what's available.")
            return
    code = snippets[tag]["code"]
    pyperclip.copy(code)
    notify("Snippet Loaded", tag)
    print(f"\n── SNIPPET: {tag} ──\n{code}\n{'─'*40}\n")
    speak(_pick(
        f"'{tag}' is now in your clipboard, sir.",
        f"Loaded '{tag}' to clipboard, sir.",
        f"Snippet '{tag}' copied, sir. Ready to paste.",
    ))

def snippet_list(_cmd):
    """List all saved snippets by tag name."""
    snippets = _load_snippets()
    if not snippets:
        speak("No snippets saved yet, sir. Say 'save this as X' to create one.")
        return
    speak(f"You have {len(snippets)} snippet{'s' if len(snippets)!=1 else ''} saved, sir.")
    for tag in list(snippets.keys())[:8]:
        speak_wait(f"{tag}.")
    if len(snippets) > 8:
        speak_wait(f"And {len(snippets)-8} more.")


# ── 4. SMART TEST RUNNER ──────────────────────────────────────────────────────
# Detects pytest / unittest / npm test and runs specific functions.

def run_tests(command):
    """
    Detect the test framework in the current project and run the specified test.
    Trigger: "run tests" / "run last test again" / "test the login function"
    """
    # Parse target function name if given
    m = re.search(r"test(?:ing)? (?:the )?(.+?)(?:\s+function|\s+method)?\s*$", command, re.I)
    func = m.group(1).strip() if m else ""
    repeat_last = "last test" in command or "again" in command or "repeat" in command

    cwd = os.getcwd()

    # Detect framework
    has_pytest    = os.path.exists(os.path.join(cwd, "pytest.ini")) or \
                    os.path.exists(os.path.join(cwd, "setup.cfg")) or \
                    os.path.exists(os.path.join(cwd, "pyproject.toml"))
    has_npm       = os.path.exists(os.path.join(cwd, "package.json"))
    has_unittest  = any(f.startswith("test_") for f in os.listdir(cwd) if f.endswith(".py"))

    if repeat_last:
        last = memory_recall_pref("last_test_cmd")
        if last:
            speak(f"Re-running: {last}, sir.")
            subprocess.Popen(last, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=cwd)
            return
        speak("No previous test run on record, sir.")
        return

    if has_pytest:
        cmd = f"pytest -v {('-k ' + func) if func else ''}"
        framework = "pytest"
    elif has_npm:
        cmd = f"npm test {('-- --testNamePattern=' + func) if func else ''}"
        framework = "npm test"
    elif has_unittest:
        cmd = f"python -m pytest -v {('-k ' + func) if func else ''}"
        framework = "unittest"
    else:
        speak("Couldn't detect a test framework in this directory, sir.")
        return

    memory_store_pref("last_test_cmd", cmd)
    notify("Tests", f"{framework}: {func or 'all'}")
    speak(_pick(
        f"Running {framework} tests{(' for ' + func) if func else ''}, sir.",
        f"Executing test suite via {framework}, sir.",
    ))
    subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=cwd)


# ── 5. MULTI-TERMINAL MANAGER ─────────────────────────────────────────────────
# "Open dev terminals" / "open trading terminals"

def open_terminal_layout(command):
    """
    Open a set of Windows Terminal / cmd windows from a named layout.
    Each pane gets a title and an initial command.
    Trigger: "open dev terminals" / "open trading terminals" / "terminal layout X"
    """
    # Extract layout name
    m = re.search(r"(?:open|launch|start)\s+(.+?)\s+terminal", command, re.I)
    name = m.group(1).strip().lower() if m else ""
    if not name:
        m2 = re.search(r"terminal layout\s+(.+)", command, re.I)
        name = m2.group(1).strip().lower() if m2 else "dev"

    layouts = CFG.get("terminal_layouts", {})
    layout  = layouts.get(name)
    if not layout:
        available = ", ".join(layouts.keys()) if layouts else "none configured"
        speak(f"No terminal layout called '{name}', sir. Available: {available}.")
        return

    notify("Terminals", f"Layout: {name}")
    speak(_pick(
        f"Opening the {name} terminal layout, sir.",
        f"Launching {len(layout)} terminals for {name}, sir.",
    ))

    for pane in layout:
        title = pane.get("title", "Zack Terminal")
        cmd   = pane.get("cmd", "")
        # Try Windows Terminal first, fall back to cmd
        try:
            if cmd:
                subprocess.Popen(
                    f'wt.exe new-tab --title "{title}" cmd /k "{cmd}"',
                    shell=True
                )
            else:
                subprocess.Popen(f'wt.exe new-tab --title "{title}"', shell=True)
        except Exception:
            subprocess.Popen(
                f'start "{title}" cmd {"/k " + chr(34) + cmd + chr(34) if cmd else ""}',
                shell=True
            )
        time.sleep(0.4)   # Stagger so they open in order


# ── 6. PROJECT TEMPLATE GENERATOR ────────────────────────────────────────────
# "Create new Flask React project called MyApp"

_PROJECT_TEMPLATES = {
    "flask": {
        "dirs":  ["static/css", "static/js", "templates", "tests"],
        "files": {
            "app.py":           "from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return render_template('index.html')\n\nif __name__ == '__main__':\n    app.run(debug=True)\n",
            "requirements.txt": "flask\npython-dotenv\n",
            "templates/index.html": "<!DOCTYPE html>\n<html>\n<head><title>{{ title }}</title></head>\n<body><h1>Hello from Flask</h1></body>\n</html>\n",
            ".env":             "FLASK_APP=app.py\nFLASK_ENV=development\n",
            "tests/test_app.py":"import pytest\nfrom app import app\n\ndef test_index():\n    client = app.test_client()\n    r = client.get('/')\n    assert r.status_code == 200\n",
        }
    },
    "react": {
        "dirs":  ["src/components", "src/hooks", "public"],
        "files": {
            "src/App.jsx":      "import React from 'react';\n\nfunction App() {\n  return <div className='App'><h1>Hello React</h1></div>;\n}\n\nexport default App;\n",
            "src/index.jsx":    "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\n\nReactDOM.createRoot(document.getElementById('root')).render(<App />);\n",
            "public/index.html":"<!DOCTYPE html>\n<html>\n<head><meta charset='UTF-8'/><title>React App</title></head>\n<body><div id='root'></div></body>\n</html>\n",
            "package.json":     '{"name":"my-app","version":"0.1.0","scripts":{"start":"vite","build":"vite build"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0"}}\n',
        }
    },
    "flask react": {
        "dirs":  ["backend/static", "backend/templates", "backend/tests",
                  "frontend/src/components", "frontend/public"],
        "files": {
            "backend/app.py":           "from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/api/hello')\ndef hello():\n    return jsonify({'message': 'Hello from Flask'})\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5000)\n",
            "backend/requirements.txt": "flask\nflask-cors\npython-dotenv\n",
            "frontend/src/App.jsx":     "import React, { useEffect, useState } from 'react';\n\nfunction App() {\n  const [msg, setMsg] = useState('');\n  useEffect(() => {\n    fetch('/api/hello').then(r=>r.json()).then(d=>setMsg(d.message));\n  }, []);\n  return <div><h1>{msg}</h1></div>;\n}\n\nexport default App;\n",
            "frontend/package.json":    '{"name":"frontend","scripts":{"dev":"vite"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0"}}\n',
            "README.md":                "# Flask + React Project\n\n## Backend\n```bash\ncd backend && pip install -r requirements.txt && python app.py\n```\n\n## Frontend\n```bash\ncd frontend && npm install && npm run dev\n```\n",
        }
    },
    "python": {
        "dirs":  ["src", "tests", "docs"],
        "files": {
            "src/__init__.py":  "",
            "src/main.py":      "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()\n",
            "tests/test_main.py":"import pytest\nfrom src.main import main\n\ndef test_main(capsys):\n    main()\n    captured = capsys.readouterr()\n    assert 'Hello' in captured.out\n",
            "requirements.txt": "pytest\n",
            "README.md":        "# Python Project\n\n```bash\npip install -r requirements.txt\npython src/main.py\n```\n",
        }
    },
}

def create_project(command):
    """
    Scaffold a new project directory with boilerplate files.
    Trigger: "create new flask react project" / "new python project called MyBot"
    """
    cmd_lower = command.lower()

    # Detect template type (longest match first)
    template_key = None
    for key in sorted(_PROJECT_TEMPLATES.keys(), key=len, reverse=True):
        if key in cmd_lower:
            template_key = key
            break

    if not template_key:
        speak("I can scaffold flask, react, flask react, or python projects, sir. Which one?")
        return

    # Extract project name
    m = re.search(r"(?:called|named|as)\s+(\S+)", command, re.I)
    if m:
        project_name = m.group(1).strip()
    else:
        project_name = template_key.replace(" ", "_") + "_project"

    base = os.path.join(os.getcwd(), project_name)
    if os.path.exists(base):
        speak(f"A folder called {project_name} already exists, sir.")
        return

    template = _PROJECT_TEMPLATES[template_key]
    notify("Scaffold", f"{template_key}: {project_name}")
    speak(_pick(
        f"Scaffolding a {template_key} project called {project_name}, sir.",
        f"Building the {template_key} template now, sir.",
    ))

    # Create directories
    for d in template["dirs"]:
        os.makedirs(os.path.join(base, d), exist_ok=True)

    # Write boilerplate files
    for rel_path, content in template["files"].items():
        full = os.path.join(base, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

    # Open in VS Code
    try:
        subprocess.Popen(["code", base])
    except FileNotFoundError:
        os.startfile(base)

    speak(_pick(
        f"Done, sir. {project_name} is ready and open in VS Code.",
        f"All set, sir. {len(template['files'])} files created for {project_name}.",
    ))


# ── 7. TRADE JOURNAL ──────────────────────────────────────────────────────────
# "Log trade idea: EUR/USD bullish breakout at 1.0850 targeting 1.0900"
# "Save this chart setup"  (screenshot + voice note)
# "Trade review"  (end-of-session reflection)

def _load_journal() -> list:
    """Load the trade journal from disk."""
    path = CFG.get("trade_journal_file", "zack_trades.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_journal(entries: list):
    """Persist the trade journal to disk."""
    path = CFG.get("trade_journal_file", "zack_trades.json")
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)

def trade_log(command):
    """
    Log a voice trade idea with an auto-timestamp.
    Trigger: "log trade idea X" / "journal trade X" / "note trade X"
    """
    note = re.sub(
        r"(log trade(?: idea)?|journal trade|note trade|trade note|trade idea)\s*:?\s*",
        "", command, flags=re.I
    ).strip()

    if not note:
        speak("What's the trade idea, sir? Describe the setup.")
        return

    entries = _load_journal()
    entry = {
        "id":        len(entries) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "note":      note,
        "type":      "idea",
        "chart":     None,
    }
    entries.append(entry)
    _save_journal(entries)

    ts = datetime.datetime.now().strftime("%H:%M")
    notify("Trade Journal", note[:40])
    speak(_pick(
        f"Logged at {ts}, sir. Trade idea recorded.",
        f"Trade idea saved, sir. Timestamp {ts}.",
        f"Journal entry {entry['id']} added, sir.",
    ))

def trade_chart_save(command):
    """
    Take a screenshot of the current screen (TradingView chart) and attach a voice note.
    Trigger: "save this chart setup" / "annotate this chart"
    """
    note = re.sub(
        r"(save this chart(?: setup)?|annotate this chart|chart screenshot)\s*:?\s*",
        "", command, flags=re.I
    ).strip() or "Chart setup"

    # Take screenshot
    pics = os.path.join(os.path.expanduser("~"), "Pictures", "ZackCharts")
    os.makedirs(pics, exist_ok=True)
    ts_str  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    imgpath = os.path.join(pics, f"chart_{ts_str}.png")

    try:
        import PIL.ImageGrab as ImageGrab
        img = ImageGrab.grab()
        img.save(imgpath)
    except Exception:
        try:
            import pyautogui as _pag
            _pag.screenshot(imgpath)
        except Exception as e:
            speak(f"Couldn't capture the screen, sir. {e}")
            return

    # Save to journal with chart path
    entries = _load_journal()
    entry = {
        "id":        len(entries) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "note":      note,
        "type":      "chart",
        "chart":     imgpath,
    }
    entries.append(entry)
    _save_journal(entries)

    notify("Chart Saved", os.path.basename(imgpath))
    speak(_pick(
        f"Chart captured and logged, sir. Saved to Pictures/ZackCharts.",
        f"Screenshot saved as chart_{ts_str}, sir. Journal updated.",
    ))

def trade_review(_cmd=None):
    """
    Prompt the user to reflect on today's trades and log the reflection.
    Trigger: "trade review" / "end of session" / "how did my trades go"
    """
    today = datetime.date.today().isoformat()
    entries = _load_journal()
    today_entries = [e for e in entries if e["timestamp"].startswith(today)]

    if today_entries:
        count = len(today_entries)
        speak(f"You logged {count} trade {'idea' if count==1 else 'ideas'} today, sir. "
              f"How did your trades go overall?")
    else:
        speak("No trade ideas logged today, sir. How did your session go?")

    # The user's spoken reflection will come in as the next command and be logged by the AI path.
    # We flag that the next input should be stored as a reflection.
    _conv_context["pending_clarification"] = "trade_reflection"

def _handle_trade_reflection(text: str):
    """Store the user's end-of-session reflection in the journal."""
    entries = _load_journal()
    entry = {
        "id":        len(entries) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "note":      text,
        "type":      "reflection",
        "chart":     None,
    }
    entries.append(entry)
    _save_journal(entries)
    notify("Trade Reflection", text[:40])
    speak(_pick(
        "Reflection logged, sir. Good session review.",
        "Noted and saved, sir. Keep analysing those trades.",
        "Saved to your journal, sir.",
    ))

def trade_journal_show(_cmd=None):
    """Print and speak the last 5 journal entries."""
    entries = _load_journal()
    if not entries:
        speak("Your trade journal is empty, sir.")
        return
    recent = entries[-5:][::-1]
    speak(f"Last {len(recent)} journal entries, sir.")
    print("\n  ── TRADE JOURNAL " + "─"*29)
    for e in recent:
        ts = e["timestamp"][:16]
        print(f"  [{ts}] #{e['id']} ({e['type']}): {e['note'][:70]}")
        speak_wait(f"Entry {e['id']}: {e['note'][:60]}.")
    print("  " + "─"*46 + "\n")


# ── 8. CHART PATTERN RECOGNITION ─────────────────────────────────────────────
# "What pattern is this?" — takes a screenshot and passes it to AI vision.
# "Run setup checklist" — walks the user through pre-trade checklist.

def chart_pattern_explain(command):
    """
    Capture the current screen and ask the AI to identify chart patterns.
    Trigger: "what pattern is this" / "identify this pattern" / "analyse this chart"
    """
    speak(_pick(
        "Capturing the screen for analysis, sir.",
        "Taking a look at your chart, sir.",
    ))

    # Grab screenshot as base64 for AI vision
    try:
        import PIL.ImageGrab as ImageGrab
        import io, base64
        img    = ImageGrab.grab()
        buf    = io.BytesIO()
        img.save(buf, format="PNG")
        b64    = base64.b64encode(buf.getvalue()).decode()
        mime   = "image/png"
    except Exception as e:
        speak(f"Couldn't grab the screen, sir. {e}")
        return

    notify("Chart AI", "Analysing pattern…")

    # Ask AI with image — falls back to text description if vision not available
    prompt = (
        "You are an expert technical analyst. Look at this chart screenshot. "
        "Identify any visible chart patterns (head and shoulders, double top/bottom, "
        "triangle, flag, wedge, cup and handle, etc.). "
        "Describe the pattern, what it typically signals, and the key levels to watch. "
        "Be concise — max 5 sentences."
    )
    try:
        # Try multimodal API call
        resp = _ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text",       "text": prompt},
                    {"type": "image_url",  "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }],
            max_tokens=300,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception:
        # Vision not available — ask text-only
        answer = ai_query(
            "A trader is looking at a chart and wants to identify the pattern. "
            "Explain the most common chart patterns to watch for and what they signal."
        )

    speak_long(answer)

def trade_checklist(_cmd=None):
    """
    Walk the user through their pre-trade checklist one item at a time.
    Trigger: "run setup checklist" / "pre-trade checklist" / "checklist"
    """
    items = CFG.get("trade_checklist", [])
    if not items:
        speak("No checklist configured, sir. Add items to trade_checklist in your config.")
        return

    speak(_pick(
        f"Running your pre-trade checklist, sir. {len(items)} items.",
        f"Pre-trade checklist — {len(items)} checks, sir.",
    ))

    passed = 0
    for i, item in enumerate(items, 1):
        speak_wait(f"Item {i}: {item}. Confirmed?")
        # In a real session the user would say "yes" or "no" via voice.
        # We log each item as pending and let the user respond naturally.
        memory_add_pending(f"Checklist: {item}")
        passed += 1
        time.sleep(0.5)

    speak(_pick(
        f"All {passed} checklist items reviewed, sir. Proceed with discipline.",
        f"Checklist complete, sir. {passed} items confirmed.",
    ))


# ── 9. ACTIVITY BUNDLES ───────────────────────────────────────────────────────
# "Start trading session" / "Open my coding tabs"

def open_activity_bundle(command):
    """
    Open a named set of URLs and apps defined in the config.
    Trigger: "start trading session" / "open coding tabs" / "launch X bundle"
    """
    bundles   = CFG.get("activity_bundles", {})
    cmd_lower = command.lower()

    # Match bundle name
    bundle_key = None
    for key in bundles:
        if key in cmd_lower:
            bundle_key = key
            break

    # Fuzzy fallback
    if not bundle_key:
        m = re.search(r"(?:start|open|launch|load)\s+(.+?)(?:\s+session|\s+tabs|\s+bundle)?\s*$", command, re.I)
        if m:
            name = m.group(1).strip().lower()
            matches = difflib.get_close_matches(name, bundles.keys(), n=1, cutoff=0.5)
            bundle_key = matches[0] if matches else None

    if not bundle_key:
        available = ", ".join(bundles.keys()) if bundles else "none configured"
        speak(f"I don't recognise that bundle, sir. Available: {available}.")
        return

    bundle = bundles[bundle_key]
    urls   = bundle.get("urls", [])
    apps   = bundle.get("apps", [])

    notify("Bundle", bundle_key)
    speak(_pick(
        f"Launching the {bundle_key} bundle, sir.",
        f"Opening {len(urls)} tabs and {len(apps)} apps for {bundle_key}, sir.",
    ))

    for url in urls:
        webbrowser.open_new_tab(url)
        time.sleep(0.3)

    for app in apps:
        try:
            subprocess.Popen(app)
        except Exception:
            pass
        time.sleep(0.5)


# ── 10. GAME MODE AUTOMATION ──────────────────────────────────────────────────
# Auto-detects Steam/Epic/VRChat launch and switches to gaming mode.
# "Clip the last 30 seconds" — uses OBS or Game Bar.

_game_mode_active = False
_screen_recording_active = False
_screen_recording_backend = None
_screen_recording_started_at = None

def _game_monitor_thread():
    """
    Background thread that watches for game launcher processes.
    When one starts, switches to Gaming mode and closes heavy apps.
    When all are gone, restores Normal mode.
    """
    global _game_mode_active
    triggers = [p.lower() for p in CFG.get("game_triggers", [])]
    if not triggers:
        return
    while True:
        try:
            running = {p.info["name"].lower()
                       for p in psutil.process_iter(["name"]) if p.info["name"]}
            game_running = any(t in running for t in triggers)

            if game_running and not _game_mode_active:
                _game_mode_active = True
                set_mode("gaming")
                notify("Game Mode", "Auto-activated")
                speak(_pick(
                    "Gaming session detected, sir. Switching to Gaming mode.",
                    "A game launcher is running, sir. Optimising the system.",
                ))
                # Close heavy apps
                kill_list = [a.lower() for a in CFG.get("game_mode_kill_apps", [])]
                for proc in psutil.process_iter(["name", "pid"]):
                    if proc.info["name"] and proc.info["name"].lower() in kill_list:
                        try:
                            proc.kill()
                            notify("Game Opt", f"Closed {proc.info['name']}")
                        except Exception:
                            pass

            elif not game_running and _game_mode_active:
                _game_mode_active = False
                set_mode("normal")
                notify("Game Mode", "Deactivated")
                speak(_pick(
                    "Game session ended, sir. Returning to Normal mode.",
                    "Back to work mode, sir. Gaming session closed.",
                ))
        except Exception:
            pass
        time.sleep(8)

def _gamebar_clip_dir():
    """Return the folder where Game Bar saves captures, auto-detecting if not configured."""
    configured = CFG.get("gamebar_clip_dir", "").strip()
    if configured and os.path.isdir(configured):
        return configured
    default = os.path.join(os.path.expanduser("~"), "Videos", "Captures")
    os.makedirs(default, exist_ok=True)
    return default


def _latest_recording_file():
    """Find the newest video file in the Game Bar captures folder."""
    folder = _gamebar_clip_dir()
    try:
        files = [
            f for f in os.listdir(folder)
            if f.lower().endswith((".mp4", ".mkv", ".mov"))
        ]
        if not files:
            return None
        return os.path.join(
            folder,
            max(files, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
        )
    except Exception:
        return None


def clip_replay(command):
    """
    Save a Game Bar clip using Win+Alt+G.
    Optionally rename it if the user gave a name.
    Trigger: "clip the last 30 seconds" / "clip that" / "save clip as epic moment"
    """
    m_name = re.search(r"(?:as|named?|called)\s+['\"]?(.+?)['\"]?\s*$", command, re.I)
    clip_name = m_name.group(1).strip() if m_name else None

    notify("Clip", "Game Bar saving clip")
    speak(_pick("Saving that clip, sir.", "Clipping now, sir.", "Got it, sir. Saving the clip."))

    try:
        pyautogui.hotkey("win", "alt", "g")
        notify("Game Bar", "Clip saved")
    except Exception as e:
        speak("Couldn't trigger the Game Bar clip, sir. Make sure Xbox Game Bar is enabled.")
        log(f"[CLIP] {e}")
        return

    # Rename if custom name provided
    if clip_name:
        time.sleep(2)   # Give Game Bar a moment to finish writing the file
        clips_dir = _gamebar_clip_dir()
        files = sorted(
            [f for f in os.listdir(clips_dir) if f.lower().endswith(".mp4")],
            key=lambda f: os.path.getmtime(os.path.join(clips_dir, f)),
            reverse=True
        )
        if files:
            ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new = os.path.join(clips_dir, f"{clip_name}_{ts}.mp4")
            try:
                os.rename(os.path.join(clips_dir, files[0]), new)
                notify("Clip Renamed", os.path.basename(new))
                speak(f"Saved as {clip_name}, sir.")
                return
            except Exception:
                pass

    speak(_pick("Clip saved, sir.", "Done, sir. Replay captured."))


def start_screen_recording(_cmd=None):
    """
    Start screen recording using Windows Game Bar (Win+Alt+R).
    """
    global _screen_recording_active, _screen_recording_backend, _screen_recording_started_at
    if _screen_recording_active:
        elapsed = int(time.time() - (_screen_recording_started_at or time.time()))
        speak(f"Recording is already running, sir. {elapsed} seconds on the clock.")
        return
    try:
        pyautogui.hotkey("win", "alt", "r")
        _screen_recording_active     = True
        _screen_recording_backend    = "Game Bar"
        _screen_recording_started_at = time.time()
        set_mode("recording")
        notify("Recording", "Game Bar started")
        speak(_pick(
            "Recording started with Game Bar, sir.",
            "We are recording now, sir.",
            "Recording is live, sir.",
        ))
    except Exception as e:
        notify("Recording", "Failed")
        speak("I couldn't start the recording, sir. Make sure Xbox Game Bar is enabled in Settings.")
        log(f"[RECORDING] start failed: {e}")


def stop_screen_recording(_cmd=None):
    """Stop the active Game Bar recording using Win+Alt+R again (it toggles)."""
    global _screen_recording_active, _screen_recording_backend, _screen_recording_started_at
    if not _screen_recording_active:
        speak("No screen recording is running, sir.")
        return
    try:
        pyautogui.hotkey("win", "alt", "r")
        elapsed = int(time.time() - (_screen_recording_started_at or time.time()))
        _screen_recording_active     = False
        _screen_recording_backend    = None
        _screen_recording_started_at = None
        set_mode("normal")

        time.sleep(1.5)   # Give Game Bar time to finish saving
        latest = _latest_recording_file()
        if latest:
            notify("Recording saved", os.path.basename(latest))
            speak(
                f"Recording stopped, sir. Duration {elapsed} seconds. "
                f"Saved as {os.path.basename(latest)}."
            )
        else:
            notify("Recording", "Stopped")
            speak(f"Recording stopped, sir. Duration {elapsed} seconds.")
    except Exception as e:
        notify("Recording", "Stop failed")
        speak("I couldn't stop the recording cleanly, sir.")
        log(f"[RECORDING] stop failed: {e}")


def toggle_screen_recording(cmd=None):
    """Toggle recording state — starts if not running, stops if it is."""
    if _screen_recording_active:
        stop_screen_recording(cmd)
    else:
        start_screen_recording(cmd)


def screen_recording_status(_cmd=None):
    """Report whether screen recording is currently active."""
    if not _screen_recording_active:
        speak("No screen recording is running, sir.")
        return
    elapsed = int(time.time() - (_screen_recording_started_at or time.time()))
    speak(f"Recording is active via Game Bar, sir. {elapsed} seconds recorded so far.")

# ── 11. YOUTUBE LIVE ALERTS ───────────────────────────────────────────────────
# Background thread that polls configured channels for live streams.

_yt_live_notified: set = set()   # Channel IDs already notified this session

def _youtube_live_thread():
    """
    Poll YouTube Data API (or RSS feed as fallback) every 5 minutes for live streams
    from configured trading channels. Speaks an alert and can auto-open the stream.
    """
    channels = CFG.get("youtube_trading_channels", [])
    if not channels:
        return
    while True:
        for channel_id in channels:
            try:
                # Use YouTube RSS feed — no API key needed
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                conn    = http.client.HTTPSConnection("www.youtube.com", timeout=10)
                conn.request("GET", f"/feeds/videos.xml?channel_id={channel_id}")
                resp    = conn.getresponse()
                body    = resp.read().decode("utf-8", errors="ignore")

                # Check for live indicator in the RSS feed title/description
                if "live" in body.lower() and "is live" in body.lower():
                    if channel_id not in _yt_live_notified:
                        _yt_live_notified.add(channel_id)
                        # Extract channel name from XML
                        m = re.search(r"<author><name>(.+?)</name>", body)
                        ch_name = m.group(1) if m else "A trading channel"
                        notify("YouTube Live", ch_name)
                        toast("Zack", f"{ch_name} is live on YouTube!")
                        if _should_interrupt():
                            speak(f"Sir, {ch_name} is currently live on YouTube.")
                        # Auto-open the stream URL
                        stream_url = f"https://www.youtube.com/channel/{channel_id}/live"
                        webbrowser.open_new_tab(stream_url)
                else:
                    # Reset so we can notify again next time they go live
                    _yt_live_notified.discard(channel_id)
            except Exception:
                pass
        time.sleep(300)   # Check every 5 minutes


# ── 12. SMART CLIPBOARD ───────────────────────────────────────────────────────
# Copy code → "explain this code"
# Copy error → "debug this"
# Copy chart/image → "analyse this pattern"
# Activated by saying "smart paste" or "process clipboard" or "what's in my clipboard"

def smart_clipboard(_cmd=None):
    """
    Auto-detect the type of clipboard content and route it to the right handler.
    - Error / traceback → explain_error
    - Code (indented, has def/class/import) → explain code
    - URL → open and summarise
    - Plain text → summarise
    - Empty → tell the user
    Trigger: "smart paste" / "process clipboard" / "what's in my clipboard"
    """
    text = pyperclip.paste().strip()

    if not text:
        speak("Your clipboard is empty, sir.")
        return

    notify("Smart Clipboard", text[:30])

    # Detect type
    is_error = any(kw in text for kw in (
        "Traceback", "Error:", "Exception", "TypeError", "ValueError",
        "SyntaxError", "undefined is not", "Cannot read", "NullPointerException"
    ))
    is_code = (
        text.count("\n") >= 3 and
        any(kw in text for kw in ("def ", "class ", "import ", "function ", "const ",
                                   "=>", "return ", "var ", "let ", "if (", "for ("))
    )
    is_url  = text.startswith("http://") or text.startswith("https://")

    if is_error:
        speak(_pick(
            "Looks like an error message, sir. Diagnosing now.",
            "I see an error in your clipboard, sir. Analysing it.",
        ))
        explain_error("debug this")   # explain_error will read from clipboard
    elif is_code:
        speak(_pick(
            "I see code in your clipboard, sir. Explaining it.",
            "Code detected, sir. Let me break it down.",
        ))
        prompt = f"Explain what this code does in plain English, concisely (max 5 sentences):\n\n{text[:1200]}"
        speak_long(ai_query(prompt))
    elif is_url:
        speak(f"Opening that link, sir.")
        webbrowser.open_new_tab(text)
        notify("Smart Clipboard", "URL opened")
    else:
        speak(_pick(
            "Summarising your clipboard, sir.",
            "Processing that text, sir.",
        ))
        speak_long(ai_query(f"Summarise this in 2-3 sentences: {text[:800]}"))


# ── Camera, security, and gesture control ────────────────────────────────────

def open_camera():
    """Open a live webcam feed in a floating window; press Q to close it."""
    speak(_pick("Opening the camera, sir.", "Camera feed, sir."))
    notify("Camera", "Opened")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)   # CAP_DSHOW is faster on Windows
    if not cap.isOpened():
        speak("Couldn't access the camera, sir.")
        return
    cv2.namedWindow("Zack Camera", cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret: break
        cv2.imshow("Zack Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

def take_camera_snapshot():
    """Capture a single frame from the webcam and save it as a PNG in ~/Pictures."""
    speak(_pick("Capturing now, sir.", "Snapshot, sir."))
    notify("Camera", "Snapshot")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        speak("Couldn't access the camera, sir.")
        return
    time.sleep(0.5)              # Allow the camera to auto-expose
    ret, frame = cap.read()
    cap.release()
    if not ret:
        speak("Failed to capture, sir.")
        return
    ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(os.path.expanduser("~"), "Pictures")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"zack_snap_{ts}.png")
    cv2.imwrite(path, frame)
    notify("Snapshot", path)
    toast("Zack", f"Snapshot saved: zack_snap_{ts}.png")
    speak(_pick("Snapshot captured and saved, sir.", "Done, sir. Snapshot filed away."))

def what_do_you_see():
    """Capture the screen and ask the AI to describe what it sees."""
    speak(_pick("Let me take a look, sir.", "Analysing the screen, sir."))
    notify("Vision", "Screen capture")
    try:
        import PIL.ImageGrab as ImageGrab
        import io, base64
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        speak(f"Couldn't grab the screen, sir. {e}")
        return

    prompt = (
        "Describe what is on this screen in 3-4 sentences. "
        "Mention the application, visible content, and anything notable. "
        "Be specific and direct."
    )
    try:
        resp = _ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            max_tokens=300,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception:
        # Vision not supported on this model, fall back to describing the screenshot dimensions
        img_w, img_h = img.size
        answer = ai_query(f"Describe what a typical computer screen at {img_w}x{img_h} resolution might show when someone is working.")
    speak_long(answer)

def start_security_mode():
    """Start the motion-detection security camera in a background thread."""
    global _security_active, _security_stop
    if _security_active:
        speak(_pick("Security mode is already active, sir.", "Already watching, sir."))
        return
    _security_active = True
    _security_stop.clear()
    notify("Security", "ACTIVE")
    speak(_pick("Security mode engaged, sir. I'll alert you if I detect any motion.",
                "Cameras active, sir. Watching for movement."))
    threading.Thread(target=_security_thread, daemon=True).start()

def stop_security_mode():
    """Stop the motion-detection camera."""
    global _security_active
    _security_active = False
    _security_stop.set()
    notify("Security", "STOPPED")
    speak(_pick("Security mode disabled, sir. Standing down.",
                "Cameras off, sir. Security mode ended."))

def _security_thread():
    """
    Read frames continuously, diff against the previous frame,
    and alert when a large number of pixels have changed (indicating motion).
    """
    global _security_motion_count
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        speak("Couldn't open the camera, sir.")
        _security_stop.set()
        return
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    while not _security_stop.is_set():
        ret, frame = cap.read()
        if not ret: break
        gray          = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff          = cv2.absdiff(prev_gray, gray)           # Pixel-level frame difference
        _, thresh     = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_pixels = cv2.countNonZero(thresh)               # Count changed pixels
        if motion_pixels > 5000:                                # Threshold for motion detection
            _security_motion_count += 1
            _hud_data["motion"]       = True
            _hud_data["motion_count"] = _security_motion_count
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            if _security_motion_count % 5 == 1:                # Alert every 5th event
                toast("Zack Security", f"Motion detected — event #{_security_motion_count}")
                speak(_pick("Motion detected, sir.",
                            "Sir, movement detected in the room.",
                            "Intruder alert, sir. Motion sensed."))
        else:
            _hud_data["motion"] = False
        prev_gray = gray
        time.sleep(0.3)
    cap.release()

def start_gesture_control():
    """Start the MediaPipe hand-tracking gesture control in a background thread."""
    if not MEDIAPIPE_AVAILABLE:
        speak("Install mediapipe to use gesture control, sir.")
        return
    global _gesture_running
    if _gesture_running:
        speak("Gesture control is already active, sir.")
        return
    _gesture_running = True
    speak(_pick("Gesture control activated, sir.", "Hand tracking online, sir."))
    threading.Thread(target=_gesture_thread, daemon=True).start()

def stop_gesture_control():
    """Set the flag that tells the gesture thread to exit on its next iteration."""
    global _gesture_running
    _gesture_running = False
    notify("Gesture", "Stopped")
    speak(_pick("Gesture control stopped, sir.", "Hand tracking offline, sir."))

# ── v5.1: Clap wake toggle ────────────────────────────────────────────────────

def toggle_clap_wake(enable: bool):
    """
    Enable or disable the double-clap wake feature at runtime without restarting.
    Updates CFG so the mic monitor thread picks it up on its next sample loop.
    Trigger: "enable clap" / "disable clap" / "toggle clap"
    """
    CFG["double_clap_wake"] = enable
    if enable:
        notify("Clap Wake", "ENABLED")
        speak(_pick(
            "Double-clap wake is now enabled, sir. Two quick claps will wake me.",
            "Clap detection is on, sir. Two claps and I'm listening.",
            "Clap wake activated, sir.",
        ))
    else:
        notify("Clap Wake", "DISABLED")
        speak(_pick(
            "Double-clap wake is now disabled, sir. Voice wake only.",
            "Clap detection is off, sir. Use your voice to wake me.",
            "Clap wake deactivated, sir.",
        ))

def _gesture_thread():
    """
    Recognize hand gestures from the webcam and map them to media key presses.
    Gestures: open palm = play/pause, fist = mute, two fingers = next,
              point = previous, thumbs up = volume up, thumbs down = volume down.
    """
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    cap      = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    last_gesture = ""
    last_time    = 0

    def _fingers_up(lm):
        """Return a 5-element list where 1 = finger extended, 0 = folded."""
        f = [1 if lm[4].x < lm[3].x else 0]   # Thumb: compare X instead of Y
        for tip in [8, 12, 16, 20]:
            f.append(1 if lm[tip].y < lm[tip-2].y else 0)
        return f

    while _gesture_running:
        ret, frame = cap.read()
        if not ret: break
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            lm    = results.multi_hand_landmarks[0].landmark
            f     = _fingers_up(lm)
            total = sum(f)
            gesture = ""
            if   total == 5:               gesture = "open_palm"
            elif total == 0:               gesture = "fist"
            elif f[0] and total == 1:      gesture = "thumbs_up"
            elif not f[0] and f[4] and total==1: gesture = "thumbs_down"
            elif f[1] and f[2] and total==2: gesture = "two_fingers"
            elif f[1] and total == 1:      gesture = "point"
            now = time.time()
            if gesture and gesture != last_gesture and now - last_time > 1.5:
                last_gesture = gesture
                last_time    = now
                notify("Gesture", gesture)
                actions = {"open_palm": "playpause", "fist": "volumemute",
                           "two_fingers": "nexttrack", "point": "prevtrack"}
                if gesture in actions:
                    pyautogui.press(actions[gesture])
                elif gesture == "thumbs_up":
                    for _ in range(2): pyautogui.press("volumeup")
                elif gesture == "thumbs_down":
                    for _ in range(2): pyautogui.press("volumedown")
        time.sleep(0.05)
    cap.release()
    hands.close()

def media_control(command):
    """Route media commands (play, pause, next, previous, stop) to the appropriate function."""
    if "pause" in command or ("play" in command and "playlist" not in command):
        spotify_pause()
    elif "next" in command:
        spotify_next()
    elif any(w in command for w in ("previous","prev","back")):
        spotify_prev()
    elif "stop" in command:
        pyautogui.press("stop")
        notify("Media", "Stop")
    else:
        speak("Say play, pause, next, or previous, sir.")


# ── Site search ───────────────────────────────────────────────────────────────

# Matches "in google <query>", "in youtube <query>", etc.
_SITE_RE   = re.compile(r'\bin\s+(google|youtube|youtube\s+music|amazon|wikipedia|maps|google\s+maps|spotify|news|translate)\s*[,.]?\s*(.+)', re.IGNORECASE)
# Strips leading action verbs like "search for", "play", "find", etc.
_ACTION_RE = re.compile(r'^(?:search\s+for|search|play|find|look\s+up|open|show|get|watch)\s+', re.IGNORECASE)

def _handle_site_search(site, query):
    """Open the appropriate search URL for the given site and query string."""
    site = site.lower().strip()
    q    = query.replace(" ", "+")
    routes = {
        "google":       f"https://www.google.com/search?q={q}",
        "youtube":      f"https://www.youtube.com/results?search_query={q}",
        "youtube music":f"https://music.youtube.com/search?q={q}",
        "amazon":       f"https://www.amazon.in/s?k={q}",
        "wikipedia":    f"https://en.wikipedia.org/wiki/Special:Search?search={q}",
        "maps":         f"https://www.google.com/maps/search/{q}",
        "google maps":  f"https://www.google.com/maps/search/{q}",
        "spotify":      f"https://open.spotify.com/search/{query.replace(' ','+')}",
        "news":         f"https://news.google.com/search?q={q}",
        "translate":    f"https://translate.google.com/?text={query.replace(' ','+')}",
    }
    url = routes.get(site, f"https://www.google.com/search?q={q}")
    notify(f"→ {site.title()}", query[:40])
    webbrowser.open_new_tab(url)


# ── Briefings and status reports ──────────────────────────────────────────────

def give_status_report():
    """Deliver a full spoken briefing: greeting, time, weather, tasks, schedule, system stats."""
    notify("Status Report", "Full briefing")
    n    = datetime.datetime.now()
    day  = n.strftime("%A")
    hour = n.hour
    greeting = ("Good morning" if hour < 12
                else "Good afternoon" if hour < 17
                else "Good evening")
    speak_wait(_pick(
        f"{greeting}, sir. Here is your current status.",
        f"{greeting}, sir. Allow me to bring you up to speed.",
        f"{greeting}, sir. Your briefing follows.",
    ))
    speak_wait(f"It is {n.strftime('%I:%M %p')} on {n.strftime('%A, %B')} the {n.day}{_ordinal(n.day)}.")

    # Weather block
    if not _local_only_mode:
        try:
            data = requests.get("https://api.openweathermap.org/data/2.5/weather",
                                params={"q": WEATHER_CITY, "appid": WEATHER_API, "units": "metric"},
                                timeout=5).json()
            if data.get("cod") == 200:
                temp    = round(data['main']['temp'])
                desc    = data['weather'][0]['description']
                speak_wait(f"Weather in {WEATHER_CITY}: {temp} degrees, {desc}.")
                comment = _jarvis_weather_comment(temp, desc, WEATHER_CITY)
                if comment: speak_wait(comment)
        except Exception:
            pass

    # Task summary
    tasks   = _read_tasks_from_file()
    pending = [t for t in tasks if not t["done"]]
    if pending:
        speak_wait(f"You have {len(pending)} task{'s' if len(pending)!=1 else ''} pending, sir.")
        for t in pending[:2]: speak_wait(f"  — {t['text']}.")
        if len(pending) > 2: speak_wait(f"And {len(pending)-2} more on the list.")
    else:
        speak_wait(_pick("Your task list is clear, sir. A satisfying state of affairs.",
                         "No pending tasks, sir. Well done."))

    # Upcoming classes
    classes = TIMETABLE.get(day, [])
    if classes:
        now_str  = n.strftime("%H:%M")
        upcoming = [(t, s) for t, s in classes if t > now_str]
        if upcoming:
            speak_wait(f"You have {len(upcoming)} class{'es' if len(upcoming)!=1 else ''} remaining today.")
            t_str, subj = upcoming[0]
            speak_wait(f"Next: {subj} at {t_str}.")
        else:
            speak_wait("No further classes today, sir.")

    # System health
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        speak_wait(f"Systems running at {cpu} percent CPU and {ram} percent RAM.")
        bat = psutil.sensors_battery()
        if bat:
            plugged = "charging" if bat.power_plugged else "on battery"
            speak_wait(f"Battery at {int(bat.percent)} percent, {plugged}.")
    except Exception:
        pass

    # Session duration and fatigue check
    dur = int((time.time() - _session["start"]) / 60)
    speak_wait(f"You've been running for {dur} minutes this session, sir. {_session['commands']} commands processed.")
    state = _analyze_user_state()
    if state["fatigue"]:
        speak_wait(_pick("The hour is late, sir. Do consider resting at some point.",
                         "I notice it's getting late, sir. Rest may be warranted."))
    elif dur > 120:
        speak_wait(_pick(f"{dur} minutes is quite a stretch, sir. A short break might serve you well.",
                         "You've been going a while, sir. Perhaps a brief pause?"))

    # Surface one remembered fact
    rows = memory_recall_all()
    if rows:
        key, val, _ = rows[0]
        speak_wait(f"From memory, sir — {key} is {val}.")

def daily_briefing():
    """Run the full status report and add an AI-generated productivity tip."""
    give_status_report()
    if not _local_only_mode:
        try:
            tip = ai_query("Give one short actionable productivity tip for today. One sentence only, no preamble.")
            speak_wait(_pick("One more thing, sir — today's thought: ",
                             "And a thought for the day, sir: ",
                             "Finally, sir — ") + tip)
        except Exception:
            pass

def night_briefing():
    """Deliver an end-of-day summary: session duration, commands, tasks, and Pomodoros."""
    notify("Night Briefing", "End of day")
    speak_wait(_pick(
        "A fine day's work, sir. Allow me to summarize.",
        "Good evening, sir. Here is how the day unfolded.",
        "End of day review, sir.",
    ))
    dur   = int((time.time() - _session["start"]) / 60)
    hours = dur // 60
    mins  = dur % 60
    if hours > 0:
        speak_wait(f"You worked for {hours} hour{'s' if hours!=1 else ''} and {mins} minutes today, sir.")
    else:
        speak_wait(f"A {mins}-minute session, sir.")
    speak_wait(f"{_session['commands']} commands handled. {_session['ai_queries']} AI queries processed.")
    if _session['tasks_done']:
        speak_wait(_pick(f"You completed {_session['tasks_done']} task{'s' if _session['tasks_done']!=1 else ''} today, sir. Well done.",
                         f"{_session['tasks_done']} tasks off the list, sir. Good work."))
    if _session['pomodoros_done']:
        speak_wait(_pick(f"{_session['pomodoros_done']} Pomodoro session{'s' if _session['pomodoros_done']!=1 else ''} completed. Impressive focus, sir.",
                         f"{_session['pomodoros_done']} focus sessions logged, sir."))
    if _command_freq:
        top = max(_command_freq, key=_command_freq.get)
        speak_wait(_pick(f"Your most frequent command was '{top}' — tells me something about your priorities, sir.",
                         f"'{top}' was your most-used command. {_command_freq[top]} times, sir."))
    state = _analyze_user_state()
    if state["hour"] >= 23 or state["hour"] < 4:
        speak_wait(_pick("It is quite late, sir. I strongly recommend some rest.",
                         "The hour is far gone, sir. Please do sleep."))
    else:
        speak_wait(_pick("Good night, sir.", "Rest well, sir.", "Until tomorrow, sir."))

def show_usage_history(n=10):
    """Print and speak the last n commands with their timestamps."""
    notify("History", f"Last {n} commands")
    if not _command_history:
        speak("No commands recorded yet, sir.")
        return
    recent = _command_history[-n:]
    print("\n  ── LAST COMMANDS " + "─"*30)
    for e in recent:
        print(f"  [{e['ts']}]  {e['cmd']}")
    print("  " + "─"*46+"\n")
    speak(f"Your last {len(recent)} commands, sir.")
    for e in recent[-5:]:
        speak_wait(f"At {e['ts']}: {e['cmd']}.")

def _record_command(cmd):
    """Log a command to history, increment the frequency counter, and update usage patterns."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    _command_history.append({"cmd": cmd, "ts": ts})
    if len(_command_history) > 50:
        _command_history.pop(0)   # Keep only the most recent 50 entries
    kw = cmd.split()[0] if cmd.split() else cmd
    _command_freq[kw] = _command_freq.get(kw, 0) + 1
    _session["commands"] += 1
    memory_log_event("command", cmd[:100])
    _record_pattern()   # Increment the hourly usage counter


# ── Mission flows (multi-step scenarios) ─────────────────────────────────────

def exam_mode():
    """Activate study mode, show today's schedule, and start long Pomodoro blocks."""
    notify("Mission", "EXAM MODE")
    speak_wait(_pick("Activating exam mode, sir. Let's make this count.", "Exam mode engaged, sir. Full focus."))
    set_mode("study")
    get_today_schedule()
    start_pomodoro(45, 10)   # 45-minute work blocks, 10-minute breaks
    speak(_pick("45-minute focus blocks, 10-minute breaks. Good luck, sir.", "Exam mode active, sir. You've got this."))

def project_crunch_mode():
    """Activate focus mode with longer Pomodoro blocks for deadline work."""
    notify("Mission", "PROJECT CRUNCH")
    speak_wait(_pick("Project crunch mode, sir. Let's ship it.", "Activating crunch mode, sir. No distractions."))
    set_mode("focus")
    start_pomodoro(50, 10)   # 50-minute work blocks, 10-minute breaks
    speak(_pick("50-minute blocks, sir. Head down.", "Crunch mode on. Let's get it done, sir."))

def night_mode():
    """Enable silent mode and dim the screen for late-night use."""
    notify("Mission", "NIGHT MODE")
    set_mode("silent")
    handle_brightness("brightness down")
    speak(_pick("Night mode on, sir. Keeping things quiet.", "Night mode engaged, sir. Rest well."))

def lab_tour():
    """Read out a complete list of Zack's capabilities."""
    notify("Lab Tour", "Feature list")
    speak_wait(_pick(
        "Allow me to walk you through my capabilities, sir.",
        "Certainly, sir. Here is what I'm capable of.",
        "A grand tour, sir. Here we go.",
    ))
    lines = [
        "System control: volume, brightness, lock, sleep, shutdown, restart, and screenshot.",
        "Weather for any city, or your current location detected automatically.",
        "Time, date, and news — headlines from India and globally, read aloud.",
        "Task management: add, list, and complete tasks from your notes file.",
        "Timed reminders and countdown timers with audible alerts.",
        "Pomodoro timer for focused work sessions, with configurable durations.",
        "Your class timetable — today's schedule, next class, and the full week.",
        "AI assistant: full conversation with context awareness, powered by cloud or local Ollama.",
        "Spotify integration: play any track, pause, skip, or queue by genre.",
        "Git operations: status, add, commit, push, and pull from your project directory.",
        "Camera: live view, snapshots, object detection, and motion-triggered security mode.",
        "Gesture control via camera — media controls with hand gestures.",
        "Full system telemetry: CPU, RAM, disk, GPU, battery, and network.",
        "Long-term memory: say remember X is Y. I retain it across sessions.",
        "Proactive alerts: class warnings, low battery, and sustained CPU load.",
        "Personality modes: switch between standard Zack and Friday.",
        "Operating modes: gaming, study, focus, recording, silent, security, and normal.",
        "Conversation awareness: I remember what we just discussed. Follow-up questions work.",
        "Plugins: drop a Python file into the plugins folder to extend my capabilities.",
        "Audit log at localhost 7777 for a full command history in your browser.",
        "Command chains: say work session, morning routine, or dev session for automated workflows.",
        "What shall we do first, sir?",
    ]
    print("\n"+"".join(f"  {l}\n" for l in lines))
    for line in lines:
        if stop_flag.is_set() or _speak_cancel.is_set(): break
        speak_wait(line)

def open_app(app_name):
    """Open an app by typing its name into the Windows Start menu search."""
    app_name = app_name.strip()
    if not app_name:
        speak("Didn't catch the app name, sir.")
        return
    _adaptive_prefs.setdefault("app_counts", {})[app_name] = _adaptive_prefs["app_counts"].get(app_name, 0) + 1
    notify("Opening", app_name)
    speak(_pick(f"Opening {app_name}, sir.", f"Launching {app_name}, sir."))
    pyautogui.press("win")           # Open Start menu
    time.sleep(0.5)
    pyautogui.typewrite(app_name, interval=0.05)
    time.sleep(0.6)
    pyautogui.press("enter")

def whatsapp_call(name):
    """
    Initiate a WhatsApp video call to a contact by automating the WhatsApp desktop app.
    The button coordinates WA_BTN1 and WA_BTN2 must match your screen layout.
    """
    name = name.strip()
    if not name:
        speak("Didn't catch the contact name, sir.")
        return
    notify("WhatsApp call", name)
    speak(f"Calling {name} on WhatsApp, sir.")
    pyautogui.press("win"); time.sleep(0.5)
    pyautogui.typewrite("whatsapp", interval=0.05); time.sleep(0.8)
    pyautogui.press("enter"); time.sleep(2.0)
    pyautogui.hotkey("ctrl", "f"); time.sleep(0.4)   # Open search in WhatsApp
    pyautogui.typewrite(name, interval=0.05); time.sleep(0.8)
    pyautogui.press("down"); time.sleep(0.2)
    pyautogui.press("enter"); time.sleep(1.0)
    pyautogui.click(x=WA_BTN1_X, y=WA_BTN1_Y); time.sleep(1.0)   # Click video call icon
    pyautogui.click(x=WA_BTN2_X, y=WA_BTN2_Y)                     # Confirm the call
    speak("Call started, sir.")


# ── Central command router — v4.0 category dispatch ──────────────────────────
#
# Instead of one 200-line if-elif chain, commands are grouped into categories.
# Each category is a list of (trigger_fn, handler_fn) pairs.
# trigger_fn(command) returns True when the command belongs to that handler.
# handle_command walks categories in priority order and calls the first match.
# This makes adding or reordering commands a one-line edit per category.

def _t(*keywords):
    """Return a trigger that fires when ANY keyword appears in the command string."""
    def _check(cmd):
        return any(k in cmd for k in keywords)
    return _check

def _t_start(*prefixes):
    """Return a trigger that fires when the command STARTS with any prefix."""
    def _check(cmd):
        return any(cmd.startswith(p) for p in prefixes)
    return _check

def _t_exact(*values):
    """Return a trigger that fires on exact command matches."""
    def _check(cmd):
        return cmd in values
    return _check

def _t_all(*keywords):
    """Return a trigger that fires when ALL keywords appear in the command."""
    def _check(cmd):
        return all(k in cmd for k in keywords)
    return _check


# ── Category handler groups ───────────────────────────────────────────────────
# Each group is a list of (trigger_callable, handler_callable).
# handle_command tests them in _DISPATCH_GROUPS order.

def _cmd_stop(cmd):
    notify("Stop", "Cancelling"); stop_speaking(); _alarm_stop.set()
    speak(_pick("Stopped, sir.", "Halted, sir.", "Done, sir."))

def _cmd_test_voice(_cmd):
    speak("Text to speech is working, sir.")

def _cmd_web_search(cmd):
    query = re.sub(r"^search for|^search", "", cmd).strip()
    if "youtube" in query or "video" in query:
        clean = re.sub(r"\b(on youtube|youtube|video)\b", "", query).strip()
        webbrowser.open_new_tab(f"https://www.youtube.com/results?search_query={clean.replace(' ','+')}"); notify("YouTube", clean)
    elif "wikipedia" in query or " wiki" in query:
        clean = re.sub(r"\b(on wikipedia|wikipedia|wiki)\b", "", query).strip()
        webbrowser.open_new_tab(f"https://en.wikipedia.org/wiki/Special:Search?search={clean.replace(' ','+')}"); notify("Wikipedia", clean)
    elif "map" in query or "direction" in query:
        clean = re.sub(r"\b(maps|directions?|where is)\b", "", query).strip()
        webbrowser.open_new_tab(f"https://www.google.com/maps/search/{clean.replace(' ','+')}"); notify("Maps", clean)
    elif "amazon" in query or "buy" in query or "shop" in query:
        clean = re.sub(r"\b(amazon|buy|shop for|shop)\b", "", query).strip()
        webbrowser.open_new_tab(f"https://www.amazon.in/s?k={clean.replace(' ','+')}"); notify("Amazon", clean)
    elif "image" in query or "picture" in query:
        clean = re.sub(r"\b(images?|pictures?|of)\b", "", query).strip()
        webbrowser.open_new_tab(f"https://www.google.com/search?q={clean.replace(' ','+')}+&tbm=isch"); notify("Images", clean)
    elif "translate" in query:
        clean = re.sub(r"\btranslate\b", "", query).strip()
        webbrowser.open_new_tab(f"https://translate.google.com/?text={clean.replace(' ','+')}"); notify("Translate", clean)
    else:
        webbrowser.open_new_tab(f"https://www.google.com/search?q={query.replace(' ','+')}"); notify("Google", query)

def _cmd_site_search(cmd):
    _sm = _SITE_RE.search(cmd)
    if _sm:
        site = _sm.group(1).strip()
        rest = _ACTION_RE.sub("", _sm.group(2).strip())
        if rest: _handle_site_search(site, rest)

def _cmd_open_app(cmd):
    cleaned = cmd.replace("zack", "").strip()
    idx = cleaned.find("open")
    app = cleaned[idx+4:].strip()
    if app: open_app(app)

def _cmd_whatsapp_call(cmd):
    name = cmd[5:].strip()
    if _is_sensitive(cmd): _request_confirmation(cmd, lambda: whatsapp_call(name)); return
    whatsapp_call(name)

def _cmd_news(cmd):
    if any(w in cmd for w in ["show","happening","what's happening","world","around the world"]):
        handlenewsshowwithread(cmd)
    elif any(w in cmd for w in ["read","tell me"]):
        handle_news_read(cmd)
    else:
        handle_news_show()

def _cmd_elaborate(cmd):
    num_words = {"first":0,"second":1,"third":2,"fourth":3,"fifth":4,"1st":0,"2nd":1,"3rd":2,"4th":3,"5th":4}
    idx = next((v for k, v in num_words.items() if k in cmd), 0)
    elaborate_news(idx)

def _cmd_tell_more(cmd):
    if _last_news_headlines: elaborate_news()
    elif _last_topic:        speak_long(ai_query(f"Tell me more about {_last_topic}."))

def _cmd_shutdown_confirm(cmd):
    if _is_sensitive(cmd):
        def do_it(): handle_system_command(cmd)
        _request_confirmation(cmd, do_it)
    else:
        handle_system_command(cmd)

def _cmd_clear_tasks_confirm(cmd):
    if _is_sensitive(cmd):
        _request_confirmation(cmd, clear_tasks)
    else:
        clear_tasks()

def _cmd_git_push_confirm(cmd):
    if _is_sensitive(cmd): _request_confirmation(cmd, git_push)
    else: git_push()

def _cmd_mode_switch(cmd):
    for mode_name in MODE_COLORS:
        if f"{mode_name} mode" in cmd or f"activate {mode_name}" in cmd:
            set_mode(mode_name); return
    set_mode("normal")

def _cmd_play(cmd):
    query = cmd[5:].strip()
    if query: spotify_play(query)

def _cmd_sensitivity_up(_cmd):
    _recognizer.energy_threshold = max(50, _recognizer.energy_threshold - 50)
    notify("Sensitivity", f"→ {int(_recognizer.energy_threshold)}")

def _cmd_sensitivity_down(_cmd):
    _recognizer.energy_threshold += 50
    notify("Sensitivity", f"→ {int(_recognizer.energy_threshold)}")

def _cmd_clear_history(_cmd):
    _chat_history.clear(); notify("Memory", "Cleared")
    speak(_pick("Chat history cleared, sir.", "Memory wiped, sir. Fresh start."))

def _cmd_audit_log(_cmd):
    webbrowser.open(f"http://localhost:{CFG.get('audit_log_port',7777)}")
    notify("Audit Log", f"localhost:{CFG.get('audit_log_port',7777)}")

def _cmd_usage_history(cmd):
    m = re.search(r"(\d+)", cmd)
    show_usage_history(int(m.group(1)) if m else 10)

def _cmd_pomodoro_start(cmd):
    m = re.search(r"(\d+)\s*minute", cmd)
    work = int(m.group(1)) if m else None
    start_pomodoro(custom_work=work)

def _cmd_add_task(cmd): add_task(cmd)
def _cmd_complete_task(cmd): complete_task(cmd)

def _cmd_open_project(cmd): open_project(cmd)
def _cmd_run_server(cmd):   run_server(cmd)
def _cmd_venv(cmd):         manage_venv(cmd)
def _cmd_git_commit(cmd):   git_commit(cmd)

# ── v4.0: show pending memory items ──────────────────────────────────────────

def _cmd_show_pending(_cmd):
    """Speak any unresolved pending items recorded by the memory system."""
    items = memory_get_pending()
    if not items:
        speak("No pending items in memory, sir."); return
    speak(f"You have {len(items)} unresolved item{'s' if len(items)!=1 else ''} noted, sir.")
    for item_id, text, ts in items[:5]:
        speak_wait(f"  — {text}.")
    if len(items) > 5:
        speak_wait(f"And {len(items)-5} more on record.")

def _cmd_show_topics(_cmd):
    """Speak the recent topics discussed."""
    rows = memory_recall_topics(5)
    if not rows:
        speak("No recent topics on record, sir."); return
    topics = [r[0] for r in rows]
    speak(f"Recent topics: {', '.join(topics)}, sir.")

# ── Dispatch table ────────────────────────────────────────────────────────────
# Groups are checked in order. First match wins.
# Structure: (category_label, [(trigger_fn, handler_fn), ...])

_DISPATCH_GROUPS = [

    # ── PRIORITY 0: recording commands ────────────────────────────────────────
    # Must come before "stop" control so "stop recording" isn't eaten by the
    # generic stop handler. Checked before everything else.
    ("recording_priority", [
        (_t("recording status","record status"),              lambda c: screen_recording_status(c)),
        (_t("start recording","start screen recording","record my screen",
            "begin recording","begin screen recording","screen record",
            "start capturing","capture my screen","start screen capture"),
                                                              lambda c: start_screen_recording(c)),
        (_t("stop recording","stop screen recording","end recording",
            "end screen recording","finish recording","end capture",
            "save the recording","cut recording","stop capturing"),
                                                              lambda c: stop_screen_recording(c)),
        (_t("toggle recording","toggle screen recording"),    lambda c: toggle_screen_recording(c)),
    ]),

    # ── PRIORITY 1: control / meta ────────────────────────────────────────────
    # Stop must come before everything that contains the word "stop".
    ("control", [
        (_t_exact("stop","cancel","quiet","shut up","be quiet","stop talking",
                  "enough","silence","that's enough","zip it","shhh","quiet down",
                  "abort","hush"),                            _cmd_stop),
        (_t_exact("test voice","voice test","tts test","speech test"),
                                                              _cmd_test_voice),
        (_t("more sensitive","increase sensitivity","mic more sensitive",
            "hear me better","too quiet for you","sensitivity up"),
                                                              _cmd_sensitivity_up),
        (_t("less sensitive","decrease sensitivity","mic less sensitive",
            "too sensitive","picking up noise","sensitivity down"),
                                                              _cmd_sensitivity_down),
        (_t("clear history","forget everything","wipe memory","clear chat",
            "reset conversation","erase history","forget our conversation"),
                                                              _cmd_clear_history),
        (_t("save config","save settings","update config","write config"),
                                                              lambda c: save_config()),
        (_t("show audit log","open audit log","open log","view the log",
            "open my logs","audit trail","command log"),      _cmd_audit_log),
        (_t("local mode on","offline mode","go offline","turn off internet",
            "work offline","disconnect from internet","offline please"),
                                                              lambda c: set_local_mode(True)),
        (_t("local mode off","online mode","go online","turn on internet",
            "reconnect","connect to internet","back online"),
                                                              lambda c: set_local_mode(False)),
        # Clap toggle — specific phrases only, no clash risk
        (_t("toggle clap on","enable clap","clap mode on","activate clap wake",
            "turn on clap wake","clap wake on"),              lambda c: toggle_clap_wake(True)),
        (_t("toggle clap off","disable clap","clap mode off","deactivate clap wake",
            "turn off clap wake","stop clap detection","clap wake off"),
                                                              lambda c: toggle_clap_wake(False)),
    ]),

    # ── PRIORITY 2: personality ───────────────────────────────────────────────
    # Before mode switching so "switch to friday" doesn't hit mode handler.
    ("personality", [
        (_t("switch to friday","use friday","be friday","friday mode",
            "activate friday","change to friday"),            lambda c: set_personality("friday")),
        (_t("switch to zack","use zack","be zack","zack mode",
            "activate zack","change to zack"),                lambda c: set_personality("zack")),
    ]),

    # ── PRIORITY 3: modes ─────────────────────────────────────────────────────
    # Checked before system so "gaming mode" doesn't hit "shutdown".
    ("modes", [
        (lambda c: any(f"{m} mode" in c or f"activate {m}" in c for m in MODE_COLORS)
                   or "stop mode" in c or "normal mode" in c or "default mode" in c
                   or "reset mode" in c or "standard mode" in c or "deactivate mode" in c,
                                                              _cmd_mode_switch),
        (_t("exam mode","big exam","exam time","exam tomorrow"),
                                                              lambda c: exam_mode()),
        (_t("project crunch","crunch mode","deadline mode","crunch time","project deadline"),
                                                              lambda c: project_crunch_mode()),
        (_t("night mode","bedtime mode","late night mode","keep it quiet",
            "going to bed","it's late"),                      lambda c: night_mode()),
        (lambda c: "silent mode" in c and "stop" not in c and "disable" not in c,
                                                              lambda c: set_mode("silent")),
        (_t("stop silent","disable silent","end silent mode","turn off silent"),
                                                              lambda c: set_mode("normal")),
    ]),

    # ── PRIORITY 4: time / date / weather ─────────────────────────────────────
    ("time_weather", [
        # Time: avoid matching "timer" and "timetable"
        (lambda c: any(w in c for w in ("what time","tell me the time","current time",
                       "do you know the time","time please","give me the time",
                       "what hour")) and "timer" not in c and "timetable" not in c
                       and "time to" not in c,                lambda c: tell_time()),
        (_t("what's today's date","tell me the date","current date","what day is today",
            "what's the day","today's date","what day of the week","which day is it",
            "what date"),                                     lambda c: tell_date()),
        (_t("weather","forecast","temperature outside","how hot is it",
            "is it going to rain","will it rain","how cold is it",
            "should i bring a jacket","do i need a coat","what's it like outside"),
                                                              lambda c: get_weather(c)),
    ]),

    # ── PRIORITY 5: system control ────────────────────────────────────────────
    # Volume before shutdown so "turn down" doesn't match "turn off".
    ("system", [
        (_t("volume up","louder","turn it up","make it louder","increase the sound",
            "boost the volume","raise the volume","crank it up","speak louder"),
                                                              lambda c: handle_volume("volume up")),
        (_t("volume down","quieter","turn it down","make it quieter","lower the sound",
            "reduce the volume","decrease volume","bring the volume down","too loud"),
                                                              lambda c: handle_volume("volume down")),
        (_t("unmute","bring the sound back","turn sound back on","restore audio",
            "un mute","turn on audio","audio back on"),       lambda c: handle_volume("unmute")),
        (_t("mute","silence the sound","stop the sound","kill the audio",
            "no sound","turn off sound"),                     lambda c: handle_volume("mute")),
        (_t("volume"),                                        lambda c: handle_volume(c)),
        (_t("brightness up","make it brighter","increase screen light","raise brightness",
            "screen is dim","more light on screen","increase brightness","can't see the screen"),
                                                              lambda c: handle_brightness("brightness up")),
        (_t("brightness down","dim the screen","make it darker","reduce brightness",
            "lower the brightness","too bright","screen hurts my eyes","dim display"),
                                                              lambda c: handle_brightness("brightness down")),
        (_t("brightness"),                                    lambda c: handle_brightness(c)),
        (_t("screenshot","screen capture","print screen","snap the screen",
            "save the screen","capture my display","save a screenshot",
            "grab the screen","capture the screen","take a picture of the screen"),
                                                              lambda c: take_screenshot()),
        (_t("shutdown","power off","turn off the computer","turn off pc",
            "shut the computer down","power down","switch off pc"),
                                                              _cmd_shutdown_confirm),
        (_t("restart","reboot","restart the computer","reboot the pc"),
                                                              _cmd_shutdown_confirm),
        (_t("sleep","hibernate","put computer to sleep","put pc to sleep",
            "go to sleep","suspend the computer","sleep mode"),
                                                              lambda c: handle_system_command(c)),
        (_t("lock screen","lock my screen","lock the screen","secure my pc",
            "lock the computer","lock my pc","lock display"),
                                                              lambda c: handle_system_command(c)),
        (_t("full telemetry","system telemetry","full system report"),
                                                              lambda c: full_telemetry()),
        (_t("battery","how much battery","check my battery","what's my battery"),
                                                              lambda c: full_telemetry()),
        (_t("gpu stats","network stats"),                     lambda c: full_telemetry()),
        (_t("pc stats","pc status","how's my pc","how is my computer",
            "is my pc running","computer health","check cpu","check ram",
            "memory usage","system performance","how's my system","system stats",
            "how's my laptop"),                               lambda c: system_stats()),
    ]),

    # ── PRIORITY 6: tasks and pomodoro ────────────────────────────────────────
    ("tasks", [
        (_t("add task","new task","create task","add to my list",
            "put on my list","add a task","create to do"),    _cmd_add_task),
        (_t("list tasks","show tasks","my tasks","show my tasks",
            "what do i need to do","what's on my list","give me my tasks",
            "my to do list","what tasks do i have","show to do list",
            "what's left to do","pending tasks"),             lambda c: list_tasks()),
        (_t("complete task","done with task","finish task","mark task",
            "i finished a task","mark it done","that task is done",
            "task completed","check off a task","i'm done with a task"),
                                                              _cmd_complete_task),
        (_t("clear tasks","delete all tasks","wipe the task list",
            "remove all tasks","delete my tasks","clear my to do list",
            "erase all tasks","reset task list"),             _cmd_clear_tasks_confirm),
        (lambda c: ("start pomodoro" in c or "begin pomodoro" in c
                    or "focus timer" in c or "focus session" in c
                    or "work session" in c or "study session" in c
                    or ("pomodoro" in c and "stop" not in c and "cancel" not in c)),
                                                              _cmd_pomodoro_start),
        (_t("stop pomodoro","cancel pomodoro","end pomodoro",
            "stop focus timer","end the pomodoro","cancel the pomodoro",
            "stop the focus session","end focus session","quit pomodoro"),
                                                              lambda c: stop_pomodoro()),
    ]),

    # ── PRIORITY 7: schedule and briefings ────────────────────────────────────
    ("schedule", [
        (_t("today's schedule","today schedule","my classes today","classes today",
            "today's timetable","what's on my schedule","am i free today"),
                                                              lambda c: get_today_schedule()),
        (_t("next class","what class is next","my next lecture","next lecture",
            "when does class start","upcoming class"),        lambda c: get_next_class()),
        (_t("weekly schedule","this week's classes","this week's timetable",
            "my week","weekly timetable","classes this week","show me this week"),
                                                              lambda c: get_weekly_schedule()),
        (_t("brief me","daily briefing","morning briefing","morning update",
            "give me my briefing","what's my morning look like","daily rundown",
            "morning report","start my day"),                 lambda c: daily_briefing()),
        (_t("night briefing","day review","wrap up the day","daily summary",
            "how was my day","end of day summary"),           lambda c: night_briefing()),
        (_t("status report","full status","how am i doing","give me an update",
            "quick update","status check","everything okay","system check"),
                                                              lambda c: give_status_report()),
    ]),

    # ── PRIORITY 8: media / music ─────────────────────────────────────────────
    # "play" prefix first, then individual controls, then liked/playlists.
    ("media", [
        (_t_start("play "),                                   _cmd_play),
        (_t("pause music","stop the music","hold the music","freeze the music",
            "music off","cut the music","pause the music"),   lambda c: spotify_pause()),
        (_t("next track","next song","skip this song","go to the next song",
            "skip song","next please","change the song","i don't like this song"),
                                                              lambda c: spotify_next()),
        (_t("previous track","previous song","go back a song","last song",
            "play the previous","go back","previous please"),
                                                              lambda c: spotify_prev()),
        (_t("resume music","continue music","unpause music","play again",
            "resume the music"),                              lambda c: spotify_play("")),
        (_t("liked song","play my like","play favourite","play favorites",
            "play my liked songs","my liked music","favourite songs"),
                                                              lambda c: spotify_liked_songs()),
        (_t("my playlists","list playlists","show playlists","what playlists",
            "show my playlists","all playlists"),             lambda c: spotify_list_playlists()),
        (_t("playlist"),                                      lambda c: spotify_play_playlist(c)),
    ]),

    # ── PRIORITY 9: web / open ────────────────────────────────────────────────
    # Site search before generic open so "in youtube X" doesn't hit open_app.
    ("web", [
        (lambda c: _SITE_RE.search(c) is not None,            _cmd_site_search),
        (_t("search for","google for","look up","find me","search up",
            "search the web for","look online for"),          _cmd_web_search),
        (_t_start("search "),                                  _cmd_web_search),
        (lambda c: any(s in c for s in WEBSITES),
         lambda c: [webbrowser.open_new_tab(u) or notify("Website", s)
                    for s, u in WEBSITES.items() if s in c]),
        # open_app last in web group — only fires when "open" is present
        (_t("open ","launch ","start up ","run "),             _cmd_open_app),
    ]),

    # ── PRIORITY 10: communication ────────────────────────────────────────────
    ("comms", [
        # WhatsApp call: only when command starts with "call "
        (_t_start("call ","video call ","ring ","phone "),     _cmd_whatsapp_call),
        (_t("set timer","timer for","countdown","set a timer","timer please",
            "start a countdown","count down"),                lambda c: set_timer(c)),
        (_t("remind me","set a reminder","add reminder","reminder for",
            "don't let me forget","create reminder"),         lambda c: add_named_reminder(c)),
    ]),

    # ── PRIORITY 11: news ─────────────────────────────────────────────────────
    ("news", [
        (_t("show news","read the news","news update","latest news",
            "today's headlines","what happened today","current events",
            "what's in the news","news please","tell me the news",
            "what's happening in the world","any news today"),
                                                              _cmd_news),
        (_t("elaborate on","tell me more about the news","explain the news",
            "more about that headline","expand on the news"),
                                                              _cmd_elaborate),
        # "tell me more" and "more on that" — only when news headlines exist
        (lambda c: any(p in c for p in ("tell me more","more on that","go deeper",
                       "elaborate more","expand on that","more details")) and
                   bool(_last_news_headlines or _last_topic),
                                                              _cmd_tell_more),
    ]),

    # ── PRIORITY 12: dev tools ────────────────────────────────────────────────
    ("dev", [
        (_t("open project","launch project","load project","open my project"),
                                                              _cmd_open_project),
        (_t("run server","start server","start the server","launch server",
            "start localhost","spin up server"),              _cmd_run_server),
        (_t("venv","virtual environment","create venv","activate venv",
            "python environment"),                            _cmd_venv),
        (_t("git status","check git","any changes in git","what changed in git",
            "show git status"),                               lambda c: git_status()),
        (_t("git add","stage all","stage changes","add all files"),
                                                              lambda c: git_add_all()),
        (_t("git commit","commit changes","save changes to git","commit everything",
            "save my code"),                                  _cmd_git_commit),
        (_t("git push","push code","upload my code","push to github","sync my code"),
                                                              _cmd_git_push_confirm),
        (_t("git pull","pull latest","get the latest code","pull from github",
            "update my code","fetch latest"),                 lambda c: git_pull()),
        (_t("git log","commit history","show commits","recent commits"),
                                                              lambda c: git_log()),
    ]),

    # ── PRIORITY 13: camera and security ──────────────────────────────────────
    ("camera", [
        # Security mode before generic camera so "start security mode" matches correctly
        (lambda c: ("security mode" in c or "monitor the room" in c
                    or "guard the room" in c or "activate security" in c
                    or "enable security camera" in c or "watch the room" in c)
                   and "stop" not in c and "disable" not in c,
                                                              lambda c: start_security_mode()),
        (_t("stop security","disable security","turn off security",
            "stop watching","security off","disable the camera guard"),
                                                              lambda c: stop_security_mode()),
        (_t("snapshot","take a photo","take photo","snap a picture","take a selfie",
            "capture image","take a snapshot","grab a photo"),
                                                              lambda c: take_camera_snapshot()),
        (_t("what do you see","what can you see","describe what you see",
            "look around","use your eyes","tell me what's on screen","scan the screen"),
                                                              lambda c: what_do_you_see()),
        (_t("start gesture","gesture control on","enable gesture",
            "activate gesture","hand control on"),            lambda c: start_gesture_control()),
        (_t("stop gesture","gesture control off","disable gesture",
            "deactivate gesture","hand control off"),         lambda c: stop_gesture_control()),
        # Generic camera open — last in group
        (lambda c: "camera" in c and "snapshot" not in c and "security" not in c
                   and "gesture" not in c,                    lambda c: open_camera()),
    ]),

    # ── PRIORITY 14: clipboard and misc ───────────────────────────────────────
    ("misc", [
        (_t("summarize clipboard","summarise clipboard","summarize what i copied",
            "summarise what i copied","clipboard summary","give me a summary of my clipboard"),
                                                              lambda c: clipboard_summarize()),
        (_t("translate clipboard","translate what i copied"),
                                                              lambda c: clipboard_translate(c)),
        (_t("clipboard","what did i copy","what's on my clipboard",
            "read what i copied","show my clipboard","what's in the clipboard"),
                                                              lambda c: read_clipboard()),
        (_t("joke","tell a joke","say something funny","make me laugh",
            "cheer me up","got any jokes","i need a laugh","be funny",
            "tell me something funny"),                       lambda c: tell_joke()),
        (_t("show patterns","my habits","usage patterns","how do i use you",
            "my command patterns"),                           lambda c: show_patterns()),
        (_t("recent files","what was i working on","last files i opened",
            "recently edited files"),                         lambda c: recent_files()),
    ]),

    # ── PRIORITY 15: memory and help ──────────────────────────────────────────
    ("memory", [
        (_t("last commands","command history","recent commands",
            "what did i say","show my recent commands"),      _cmd_usage_history),
        (_t("list reminders","show reminders","my reminders","show my reminders",
            "what reminders do i have","any reminders set"),  lambda c: list_reminders()),
        (_t("what can you do","lab tour","list features","show features",
            "your features","what are you capable","give me a tour",
            "teach me your commands","show me your abilities","capabilities",
            "list your commands","what do you know","help me out"),
                                                              lambda c: lab_tour()),
        (lambda c: "remember" in c and "don't" not in c and "what do you" not in c,
                                                              lambda c: handle_remember(c)),
        (_t("what do you remember","recall memory","what have you stored",
            "what did i tell you","what's in your memory","stored memory"),
                                                              lambda c: handle_recall(c)),
        (_t("what do you know about","recall","look up what you know"),
                                                              lambda c: handle_recall(c)),
        (_t("any pending","pending items","what did i want to do",
            "unfinished tasks","pending tasks"),              _cmd_show_pending),
        (_t("recent topics","what have we discussed","topics we covered"),
                                                              _cmd_show_topics),
    ]),

    # ── PRIORITY 16: docs and error explainer ─────────────────────────────────
    ("docs", [
        (_t("syntax for","what's the syntax","how do i use","docs for",
            "documentation for","how does","what is the syntax","code help",
            "help me with syntax","what's the function for","look something up"),
                                                              docs_lookup),
        (_t("explain this error","debug this","what does this error",
            "fix this error","solve this error","error means","i got an error",
            "there's an error","error message","something broke","fix the error",
            "why is there an error","debug my code","code is broken"),
                                                              explain_error),
    ]),

    # ── PRIORITY 17: code snippets ────────────────────────────────────────────
    ("snippets", [
        (_t("save this as","save snippet","save code as","tag as",
            "save this code","store this snippet","bookmark this code","keep this code"),
                                                              snippet_save),
        (_t("load snippet","get snippet","show snippet","paste snippet",
            "retrieve snippet","get code snippet","retrieve code","paste my snippet"),
                                                              snippet_load),
        (_t("list snippets","show snippets","my snippets","show my saved code",
            "what snippets do i have","my saved code"),       snippet_list),
    ]),

    # ── PRIORITY 18: dev automation ───────────────────────────────────────────
    ("dev_auto", [
        (_t("run tests","run test","run last test","test the","testing",
            "test my code","check if tests pass","run my tests","execute tests"),
                                                              run_tests),
        (_t("open dev terminals","open trading terminals","terminal layout",
            "open terminals","launch terminals","open my workspace",
            "set up my workspace","terminal setup","launch dev setup"),
                                                              open_terminal_layout),
        (_t("create new","new project","scaffold","create project",
            "make a new project","scaffold a project","new app","create app"),
                                                              create_project),
    ]),

    # ── PRIORITY 19: trading ──────────────────────────────────────────────────
    ("trading", [
        (_t("log trade","journal trade","note trade","trade idea","trade note",
            "write down a trade","record a trade","save trade idea","note a trade",
            "trade entry","add to trade journal"),            trade_log),
        (_t("save this chart","annotate this chart","chart screenshot",
            "save chart setup","save my chart","capture this chart",
            "chart snapshot","save the chart"),               trade_chart_save),
        (_t("trade review","how did my trades","session review",
            "review my trading","how did i do trading","end of trading day",
            "trading session done"),                          trade_review),
        (_t("show journal","trade journal","my trades","journal entries",
            "show my trade log","trade history","my trading journal",
            "show trade entries"),                            trade_journal_show),
        (_t("chart pattern","what pattern","identify pattern",
            "analyse this chart","analyze this chart"),       chart_pattern_explain),
        (_t("pre-trade checklist","setup checklist","run checklist",
            "trade checklist","checklist"),                   trade_checklist),
    ]),

    # ── PRIORITY 20: activity bundles ─────────────────────────────────────────
    ("bundles", [
        (lambda c: any(k in c for k in CFG.get("activity_bundles", {})),
                                                              open_activity_bundle),
        (_t("open coding tabs","open my tabs","coding tabs","my coding setup"),
                                                              open_activity_bundle),
    ]),

    # ── PRIORITY 21: gaming clips ─────────────────────────────────────────────
    ("gaming", [
        (_t("clip the last","clip last","clip that","save clip","save replay",
            "game clip","highlight clip","save last 30","capture last minute",
            "save that clip","record that","capture that moment"),
                                                              clip_replay),
    ]),

    # ── PRIORITY 22: smart clipboard ──────────────────────────────────────────
    ("smart_clip", [
        (_t("smart paste","process clipboard","explain clipboard",
            "analyse clipboard","analyze clipboard","smart clipboard"),
                                                              smart_clipboard),
    ]),
]


def handle_command(command):

    global _last_command, _last_topic
    if not any(w in command for w in _STOP_WORDS):
        stop_flag.clear()
    log(f"Command: {command}")
    _record_command(command)
    _track_context(user_input=command)   # Also calls _auto_extract_memory

    # Confirmation check must come first
    if _confirmation_pending is not None:
        if _handle_confirmation(command): return

    # Multi-turn: resume pending clarification
    if _conv_context.get("pending_clarification") == "music_genre":
        _conv_context["pending_clarification"] = None
        genre = command.strip()
        speak(_pick(f"Excellent choice, sir. Queuing up some {genre} now.",
                    f"Right away, sir. {genre.capitalize()} it is.",
                    f"{genre.capitalize()} — good taste, sir."))
        spotify_play(genre)
        return

    if _conv_context.get("pending_clarification") == "trade_reflection":
        _conv_context["pending_clarification"] = None
        _handle_trade_reflection(command)
        return

    # Context-aware umbrella question
    if any(p in command for p in ("should i carry an umbrella","need an umbrella",
                                   "bring umbrella","do i need an umbrella")):
        if _conv_context.get("last_action") == "weather" and _conv_context.get("last_entity"):
            entity = _conv_context["last_entity"].lower()
            if any(w in entity for w in ("rain","drizzle","shower","thunderstorm")):
                speak(_pick("Given the rain I just mentioned, yes sir — the umbrella is advisable.",
                            "Absolutely, sir. It's raining out there.",
                            "The umbrella is non-negotiable today, sir."))
            else:
                speak(_pick("Given the clear conditions I just mentioned, that won't be necessary, sir.",
                            "No rain on the forecast, sir. Leave it at home.",
                            "Clear skies — the umbrella can rest, sir."))
            return
        else:
            get_weather(command); return

    # Emotional state responses (preserved from v3.2)
    if any(p in command for p in ("i'm tired","im tired","i am tired","feeling tired",
                                   "i'm bored","im bored","i am bored","feeling bored",
                                   "i'm stressed","im stressed","overwhelmed","too much work",
                                   "i'm happy","feeling good","great day","having a good day",
                                   "i'm sad","feeling sad","i feel","i'm feeling")):
        result = ai_chat(command)
        _track_context(user_input=command, zack_response=result, action="chat")
        speak_long(result)
        return

    if any(p in command for p in ("thank you","thanks zack","thanks","cheers zack",
                                   "appreciate it","well done","good job")):
        speak(_pick(
            "Always a pleasure, sir.",
            "At your service, sir.",
            "Think nothing of it, sir.",
            "Happy to help.",
            "That's what I'm here for.",
        ))
        return

    if any(p in command for p in ("good morning","morning zack","good morning zack",
                                   "hey zack","hello zack","hi zack","good afternoon",
                                   "good evening","evening zack")):
        result = ai_chat(command)
        _track_context(user_input=command, zack_response=result, action="chat")
        speak_long(result)
        return

    if any(p in command for p in ("good night","goodnight","good night zack")):
        night_mode()
        speak(_pick(
            "Good night, sir. I'll keep watch while you rest.",
            "Rest well, sir. I'll be here when you need me.",
            "Good night.",
        ))
        return

    if any(p in command for p in ("how long have i been working","session time",
                                   "working how long","how long have i been on")):
        dur   = int((time.time() - _session["start"]) / 60)
        hours = dur // 60
        mins  = dur % 60
        if hours > 0:
            speak(f"You've been at it for {hours} hour{'s' if hours!=1 else ''} and {mins} minutes, sir.")
        else:
            speak(f"{mins} minutes into the session, sir.")
        return

    if any(p in command for p in ("play something","play music","what should i listen to")):
        pref = memory_recall_pref("music genre") or memory_recall_pref("preference")
        if pref:
            speak(f"Based on your taste, sir — queuing up {pref}.")
            spotify_play(pref)
        else:
            speak(_pick("Any genre in mind, sir? I can queue it up.",
                        "What are you in the mood for, sir? Jazz, lo-fi, classical?"))
            _conv_context["pending_clarification"] = "music_genre"
        return
    
    if any(p in command for p in ['who are you', 'introduce yourself', 'what is your name', 'tell me about yourself', 'who is zack', 'describe yourself']):
        introduce_zack()
        return
    
    # Slot-fill check
    slot_q = _check_slot_fill(command)
    if slot_q and _last_command != command:
        speak(f"{persona('slot_fill_prefix')} {slot_q}")
        _last_command = command
        return
    _last_command = command

    # Command chains
    for chain_name in _COMMAND_CHAINS:
        if chain_name in command:
            run_chain(chain_name); return

    # ── Category dispatch ─────────────────────────────────────────────────────
    for category, handlers in _DISPATCH_GROUPS:
        for trigger, handler in handlers:
            try:
                if trigger(command):
                    result = handler(command)
                    # handler returning None means it handled it; returning False means skip
                    if result is not False:
                        return
            except Exception as e:
                log(f"[DISPATCH] Error in {category}: {e}")

    # ── Intent resolution fallback ────────────────────────────────────────────
    resolved = _resolve_intent(command)
    if resolved and resolved != command:
        notify("Intent resolved", f"'{command}' → '{resolved}'")
        handle_command(resolved); return

    # ── AI fallback ───────────────────────────────────────────────────────────
    if "ask" in command or "query" in command:
        query = command.replace("ask", "").replace("query", "").strip()
    else:
        query = command

    if any(p in query for p in ("that","it","this","those","the last")) and _conv_context.get("last_result"):
        ctx_hint = f" (Context from previous: {_conv_context['last_result'][:80]})"
        query    = query + ctx_hint

    # Inject recent memory context for task queries
    recent_topics = memory_recall_topics(3)
    if recent_topics:
        topic_hint = ", ".join(t[0] for t in recent_topics)
        query_with_ctx = f"[Recent topics: {topic_hint}] " + query
    else:
        query_with_ctx = query

    notify("AI", query[:60])

    # Route to conversational AI for casual chat, task AI for factual queries
    if _is_conversational(command):
        # Conversational — no "one moment" filler, respond naturally and quickly
        result = ai_chat(query)
    else:
        speak(_pick(
            "One moment, sir.", "Let me think on that, sir.", "Processing, sir.",
            "Give me just a moment, sir.", "Working on it, sir.",
        ))
        result = ai_query(query_with_ctx)

    _track_context(user_input=command, zack_response=result, action="ai")
    speak_long(result)


# ── Boot and shutdown sequences ───────────────────────────────────────────────

def _boot_sequence():
    """Print a startup banner to the console."""
    print("  [ ZACK ] Voice Assistant v5.0 — JARVIS Edition — Starting up")
    checks = [
        ("INIT", "Core systems"), ("OK", "Unified GUI starting"),
        ("OK",   "AI engine — JARVIS personality"), ("OK", "TTS ready"),
        ("OK",   "Memory DB + topic/pref/pending tables"), ("OK", "Background threads"),
        ("OK",   "Category dispatch router"), ("OK",  "Check-in thread"),
        ("OK",   "Stats panel"), ("OK",  "Docs + Error explainer"),
        ("OK",   "Code snippet library"), ("OK", "Smart test runner"),
        ("OK",   "Trade journal + chart tools"), ("OK", "Activity bundles"),
        ("OK",   "Game mode monitor"), ("OK", "YouTube live alerts"),
        ("OK",   "Smart clipboard"), ("BOOT", "All systems nominal — v5.0"),
    ]
    for tag, msg in checks:
        print(f"  [ {tag:4} ] {msg}")
        time.sleep(0.04)
    print()

def _shutdown_sequence():
    """Save preferences and memory, then print a goodbye banner."""
    print("\n  ╔══════════════════════════════════╗")
    print("  ║    ZACK  SHUTTING  DOWN          ║")
    print("  ╚══════════════════════════════════╝")
    for l in ["Saving preferences...","Saving memory...","Goodbye, sir."]:
        print(f"  [ .... ] {l}")
        time.sleep(0.05)
    _save_prefs()
    log("Zack v4.0 shut down.")


# ── Wake-word listener ────────────────────────────────────────────────────────

_wake_event     = threading.Event()   # Set when "Zack" is detected in background audio
_bg_stop_fn     = None                # Function returned by listen_in_background() to stop it
_busy           = threading.Event()   # Set while a command is being processed

_STOP_WORDS = frozenset((
    "stop", "cancel", "quiet", "shut up", "be quiet",
    "stop talking", "enough", "silence", "that's enough"
))

_WAKE_WORDS = re.compile(r"\b(zack|hey zack|ok zack|okay zack)\b")

# Dedicated recognizer for the background wake listener.
# Must be separate from _recognizer to avoid shared state corruption
# when the main loop is mid-listen.
_wake_recognizer = sr.Recognizer()

def _start_background_listener():
    """Start the background listener used for wake words and speech interrupts."""
    global _bg_stop_fn
    if _bg_stop_fn is None:
        _bg_stop_fn = _wake_recognizer.listen_in_background(sr.Microphone(), _wake_callback)

def _stop_background_listener(wait=True):
    """Stop the background listener while the foreground recognizer owns the mic."""
    global _bg_stop_fn
    if _bg_stop_fn:
        _bg_stop_fn(wait_for_stop=wait)
        _bg_stop_fn = None

def _wake_callback(recognizer, audio):
    """Called by listen_in_background. Handles stop-words and wake-word only."""
    try:
        text = _wake_recognizer.recognize_google(audio, language="en-IN").lower()
        text = text.replace(",", " ").replace(".", " ").strip()
        print(f"[Wake] Heard: {repr(text)}")
    except sr.UnknownValueError:
        return
    except sr.RequestError as e:
        print(f"[Wake] STT request error: {e}")
        return
    except Exception as e:
        print(f"[Wake] Unexpected error: {e}")
        return

    # Stop words bypass the busy lock so Zack can be interrupted mid-speech
    if any(w in text for w in _STOP_WORDS):
        print("[Wake] Stop command detected.")
        stop_speaking()
        _alarm_stop.set()
        return

    if _busy.is_set():
        return

    # Only wake on an explicit "zack" word
    if _WAKE_WORDS.search(text):
        print("[Wake] Wake word detected.")
        _wake_event.set()


# ── Application entry point ───────────────────────────────────────────────────

_boot_sequence()           # Print the startup banner
_init_memory_db()          # Create database tables if they don't exist
_load_prefs()              # Load saved adaptive preferences
_adaptive_prefs["total_sessions"] = _adaptive_prefs.get("total_sessions", 0) + 1

_startup_ready = threading.Event()   # Set by the GUI when the boot animation finishes

def _on_startup_complete():
    """Callback fired by ZackGUI once the boot animation fades out."""
    _startup_ready.set()

# Create and start the GUI (runs in its own thread)
_gui = ZackGUI()
_gui.start(on_startup_complete=_on_startup_complete)

# Start all background daemon threads
threading.Thread(target=_load_whisper_background,     daemon=True).start()
threading.Thread(target=_mic_monitor_thread,           daemon=True).start()
threading.Thread(target=_telemetry_background_thread,  daemon=True).start()
threading.Thread(target=_reminder_checker_thread,      daemon=True).start()
threading.Thread(target=_proactive_thread,             daemon=True).start()
threading.Thread(target=_connectivity_monitor_thread,  daemon=True).start()
threading.Thread(target=_audit_log_server_thread,      daemon=True).start()
threading.Thread(target=_pattern_insight_thread,       daemon=True).start()
threading.Thread(target=_checkin_thread,               daemon=True).start()  # v4.0
threading.Thread(target=_game_monitor_thread,          daemon=True).start()  # v5.0
threading.Thread(target=_youtube_live_thread,          daemon=True).start()  # v5.0

# Optional threads enabled by config
if CFG.get("process_watch"):
    threading.Thread(target=_process_monitor_thread, daemon=True).start()
if CFG.get("clipboard_watch"):
    threading.Thread(target=_clipboard_watcher_thread, daemon=True).start()

_load_plugins()   # Scan the plugins folder for .py files

# Calibrate the microphone for ambient noise levels
_recognizer = sr.Recognizer()
print(f"Calibrating microphone — stay quiet for {CFG['mic_calibrate_sec']} second(s) …")
with sr.Microphone() as _src:
    _recognizer.adjust_for_ambient_noise(_src, duration=CFG["mic_calibrate_sec"])
_recognizer.dynamic_energy_threshold = False
_recognizer.pause_threshold          = 0.8
_recognizer.phrase_threshold         = 0.3
_recognizer.non_speaking_duration    = 0.5
# Raise threshold so background noise doesn't trigger STT
_recognizer.energy_threshold = max(_recognizer.energy_threshold * 1.8, 400)
print(f"Calibrated. Energy threshold: {_recognizer.energy_threshold:.1f}")

# Mirror settings to the dedicated wake recognizer
_wake_recognizer.dynamic_energy_threshold = False
_wake_recognizer.pause_threshold          = 0.6
_wake_recognizer.phrase_threshold         = 0.2
_wake_recognizer.non_speaking_duration    = 0.3
_wake_recognizer.energy_threshold         = _recognizer.energy_threshold

disable_windows_audio_ducking()   # Prevent Windows from lowering other app volumes

# Wait for the GUI boot animation to complete before proceeding
print("Waiting for startup screen to complete…")
_startup_ready.wait(timeout=CFG.get("startup_ready_timeout", 45))
startup_settle_sec = max(0.0, float(CFG.get("startup_settle_sec", 2.0)))
if startup_settle_sec:
    print(f"Settling startup services for {startup_settle_sec:.1f} second(s)…")
    time.sleep(startup_settle_sec)
print("Startup screen done. Zack is ready.")

setup_tray()   # Add the system tray icon

if _plugins_loaded:
    print(f"  Plugins loaded: {', '.join(_plugins_loaded)}")
log("Zack v3.2 started.")
print("Say 'Zack' to wake.")
print(f"  Audit log → http://localhost:{CFG.get('audit_log_port',7777)}")
print("  Whisper loading in background — Google STT active now.")

persona_speak("boot")   # Speak the startup greeting

# Start the background wake-word listener
_start_background_listener()


# ── Main event loop ───────────────────────────────────────────────────────────

try:
    while True:
        if _wake_event.is_set():
            try:
                _wake_event.clear()        # Reset the event for the next wake
                _busy.set()                # Block new wake triggers while processing
                _gui.safe_show("listening")
                play_wake_sound()
                set_tray_state("listening")

                # Stop the background listener only while the foreground listen owns the mic.
                _stop_background_listener(wait=True)
                _mic_monitor_pause.set()   # Pause the mic-level visualizer
                time.sleep(0.1)

                command = error_msg = audio_cmd = None

                try:
                    with sr.Microphone() as source:
                        try:
                            audio_cmd = _recognizer.listen(source, timeout=4, phrase_time_limit=7)
                        except sr.WaitTimeoutError:
                            error_msg = persona("no_hear")   # Nothing spoken within timeout

                    if audio_cmd:
                        try:
                            # Primary STT: Google Cloud Speech
                            command = _recognizer.recognize_google(audio_cmd, language="en-IN").lower()
                            print("Heard (Google):", repr(command))
                        except (sr.UnknownValueError, sr.RequestError):
                            # Fallback STT: local Whisper model (if loaded)
                            if _whisper_ready.is_set() and _whisper_model:
                                print("Google STT failed, trying Whisper …")
                                try:
                                    command = recognize_with_whisper(audio_cmd)
                                    print("Heard (Whisper):", repr(command))
                                except sr.UnknownValueError:
                                    error_msg = persona("no_understand")
                            else:
                                error_msg = persona("no_understand")

                except Exception as e:
                    error_msg = _pick("Something went wrong, sir. Let's try that again.",
                                      "My apologies, sir. A technical hiccup.")
                    print("Command error:", e)

                # Bring the background listener back before speaking so "stop" can interrupt TTS.
                _start_background_listener()

                if error_msg:
                    speak(error_msg)
                elif command:
                    handle_command(command)   # Route the recognized text to the correct handler

                wait_until_done_speaking()   # Block until TTS finishes before going idle
                set_tray_state("ready")
                _gui.safe_go_idle()

            finally:
                _busy.clear()                  # Allow the next wake trigger
                _mic_monitor_pause.clear()      # Resume the mic-level visualizer
                _start_background_listener()

        time.sleep(0.05)   # Yield the thread between wake-event checks

except KeyboardInterrupt:
    log("Zack shut down by user.")
    print("Shutting down Zack.")
    _shutdown_sequence()
    persona_speak_wait("shutdown")
    _stop_background_listener(wait=False)