"""
voice_system.py - Areesha ki awaaz.
- ElevenLabs se awaaz (TTS) - Sarah voice
- Deepgram se sun'na (STT) - Urdu samajhta hai
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah
ELEVENLABS_MODEL = "eleven_multilingual_v2"
TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_URL = "https://api.deepgram.com/v1/listen?model=nova-2&language=ur&smart_format=true"

# Mood ke hisaab se voice settings
VOICE_SETTINGS = {
    "normal":  {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3},
    "happy":   {"stability": 0.4, "similarity_boost": 0.8, "style": 0.6},
    "sad":     {"stability": 0.7, "similarity_boost": 0.8, "style": 0.1},
    "caring":  {"stability": 0.6, "similarity_boost": 0.8, "style": 0.2},
}


def clean_for_speech(text: str) -> str:
    """Tags aur emojis hata do, sirf bolne layak text rakho."""
    text = re.sub(r"\[(VOICE|IMAGE|CARING_MODE|SPECIAL_MOMENT)\]", "", text)
    text = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2764\uFE0F]", "", text)
    return text.strip()


def speak(text: str, mood: str = "normal") -> bytes | None:
    """Text ko Areesha ki awaaz mein convert karo (mp3 bytes return)."""
    text = clean_for_speech(text)
    if not text or not ELEVENLABS_API_KEY:
        return None

    settings = VOICE_SETTINGS.get(mood, VOICE_SETTINGS["normal"])
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": settings,
    }
    try:
        response = requests.post(TTS_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.content  # mp3 bytes
    except requests.exceptions.RequestException:
        return None


def transcribe(audio_bytes: bytes, mimetype: str = "audio/webm") -> str | None:
    """Audio ko text mein convert karo (Deepgram STT - Urdu)."""
    if not audio_bytes or not DEEPGRAM_API_KEY:
        return None

    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    files = {"audio": ("audio.webm", audio_bytes, mimetype)}
    try:
        response = requests.post(DEEPGRAM_URL, headers=headers, files=files, timeout=30)
        response.raise_for_status()
        result = response.json()
        transcript = result.get("results", {}).get("channels", [{}])[0] \
                             .get("alternatives", [{}])[0].get("transcript", "")
        return transcript.strip() if transcript else None
    except (requests.exceptions.RequestException, IndexError, KeyError):
        return None


def wants_voice(reply: str) -> bool:
    """Kya Areesha ka reply bol'na chahiye?"""
    return "[VOICE]" in reply


def detect_sad_needs_voice(reply: str) -> bool:
    """Caring mode mein bol'na zyada natural lagta hai."""
    return "[CARING_MODE]" in reply
