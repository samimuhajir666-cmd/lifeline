"""
memory.py - Areesha ki persistent memory.
Ye user ki baatein yaad rakhti hai, app band ho jaye to bhi memory rehti hai.
"""

import json
import os
from datetime import datetime

MEMORY_FILE = "areesha_memory.json"

# Memory ka default structure
DEFAULT_MEMORY = {
    "user_name": None,
    "user_city": None,
    "likes": [],
    "dislikes": [],
    "moods": [],               # [{"mood": "sad", "when": "2025-..."}]
    "important_facts": [],     # key-value style strings
    "special_moments": [],     # [{"what": "...", "when": "..."}]
    "total_messages": 0,
    "stage_points": 0,
    "last_seen": None,
}


def load_memory() -> dict:
    """Disk se memory load karo. File na ho to fresh banado."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                mem = json.load(f)
            # koi naya key missing ho to default se bhar do
            for key, value in DEFAULT_MEMORY.items():
                mem.setdefault(key, value)
            return mem
    except (json.JSONDecodeError, OSError):
        pass
    return json.loads(json.dumps(DEFAULT_MEMORY))  # deep copy


def save_memory(mem: dict):
    """Memory ko disk pe save karo."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Memory save error: {e}")


def update_last_seen(mem: dict):
    mem["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")


def add_mood(mem: dict, mood: str):
    """User ka mood record karo (sirf sad/angry jaise special moods)."""
    if mood in ("sad", "angry", "upset", "lonely"):
        mem["moods"].append({
            "mood": mood,
            "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        # sirf last 50 moods rakho
        mem["moods"] = mem["moods"][-50:]


def add_special_moment(mem: dict, what: str):
    """Koi special/khoobsurat moment yaad rakho."""
    mem["special_moments"].append({
        "what": what,
        "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    mem["special_moments"] = mem["special_moments"][-30:]


def extract_facts(message: str, mem: dict) -> list:
    """Roman Urdu messages se chhote facts nikalo (simple keyword based)."""
    facts = []
    m = message.lower()

    # Naam
    if ("mera naam" in m or "main hoon" in m) and mem.get("user_name") is None:
        # "mera naam X hai" pattern
        for word in message.replace("?", "").replace(".", "").split():
            if word.lower() not in ("mera", "naam", "hai", "main", "hoon", "mujhe", "log", "kehte", "hain", "bulate"):
                if len(word) > 2 and word.isalpha():
                    mem["user_name"] = word.strip()
                    facts.append(f"User ka naam {word} hai")
                    break

    # Sheher
    if "sheher" in m or "city" in m:
        for word in message.split():
            if word.lower() not in ("kaun", "sa", "sheher", "hai", "main", "rehtha", "rehta", "hu", "hun", "city"):
                if len(word) > 2:
                    mem["user_city"] = word.strip()
                    facts.append(f"User {word} mein rehta hai")
                    break

    # Pasand
    like_words = ["pasand", "mujhe pasand", "love", "acha lagta"]
    if any(w in m for w in like_words):
        for word in ["biryani", "chai", "cricket", "music", "coding", "ai", "rain", "kabab", "pizza"]:
            if word in m and word not in mem["likes"]:
                mem["likes"].append(word)
                facts.append(f"User ko {word} pasand hai")

    # Naa pasand
    if "pasand nahi" in m or "nafrat" in m or "burA lagta" in m.lower():
        for word in ["jhoot", "ladai", "tension", "drama"]:
            if word in m and word not in mem["dislikes"]:
                mem["dislikes"].append(word)
                facts.append(f"User ko {word} pasand nahi")

    # Important fact - explicit "yaad rakh" / "remember"
    if "yaad rakh" in m or "remember" in m:
        mem["important_facts"].append(message[:150])
        facts.append("User ne ek baat yaad rakhne ko kahi")

    return facts


def build_memory_summary(mem: dict) -> str:
    """LLM ke liye memory ka short text summary banao."""
    parts = []
    if mem.get("user_name"):
        parts.append(f"User ka naam: {mem['user_name']}")
    if mem.get("user_city"):
        parts.append(f"Sheher: {mem['user_city']}")
    if mem.get("likes"):
        parts.append("Pasand: " + ", ".join(mem["likes"]))
    if mem.get("dislikes"):
        parts.append("Pasand nahi: " + ", ".join(mem["dislikes"]))
    if mem.get("important_facts"):
        parts.append("Yaad rakhi baatein:")
        for fact in mem["important_facts"][-10:]:
            parts.append(f"  - {fact}")
    if mem.get("special_moments"):
        parts.append("Special moments (aakhri 3):")
        for moment in mem["special_moments"][-3:]:
            parts.append(f"  - {moment['what']} ({moment['when']})")
    if mem.get("moods"):
        recent = [x["mood"] for x in mem["moods"][-5:]]
        parts.append("Recent moods: " + ", ".join(recent))
    if mem.get("last_seen"):
        parts.append(f"Aakhri baar mile: {mem['last_seen']}")

    return "\n".join(parts) if parts else "Abhi tak user ke baare mein kuch khaas nahi pata."
