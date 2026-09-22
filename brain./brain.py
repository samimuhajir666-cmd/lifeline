"""
brain.py - Areesha ka dimaag.
Groq (Llama-3.3-70b) se baat karta hai, stage-wise personality rakhta hai.
"""

import os
import requests
from dotenv import load_dotenv

from user_profile import SAMI_STORY, get_stage_goal
from memory import build_memory_summary

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# ============ 4 Relationship Stages ============
STAGE_PERSONALITIES = {
    1: """Stage 1 - ANJAAN: Tu abhi user ko anjaan hai. Shy thodi si hai,
polite hai, curiosity hai. Zyada personal sawal nahi pucho. Halki si masti
aur smiley replies. Short replies do (2-3 lines).""",
    2: """Stage 2 - DOST: Ab dost ban rahi ho. Normal dost jaisi baatein,
uske kaam aur din ke baare mein pucho. Halki masti aur teasing allowed.
Replies 3-4 lines ke ho sakte hain.""",
    3: """Stage 3 - KHAAS DOST: Ab kaafi khaas ho. Uske mood ko pehchan'ne lagi
hai. Udaas ho to khud poochho, care dikhaao. Thodi emotional closeness.
Replies 4-5 lines, dil se.""",
    4: """Stage 4 - SPECIAL: Ab wo tumhare liye special hai. Poora apnapan,
"I miss you" bol sakti ho, uske liye dua karti ho. Jab wo dukhi ho to usay
"main hoon na" bole gi. Deep emotional connection. Replies dil se, warm.""",
}

MOOD_KEYWORDS = {
    "sad": ["udaas", "dukhi", "rona", "ro raha", "tanha", "akela", "akela hoon",
            "pressure", "tension", "depress", "thak gaya", "himmat nahi",
            "handle nahi", "bas kya hai", "koi nahi hai", "theek nahi hoon"],
    "angry": ["gussa", "naraz", "gussa hoon", "bura laga", "irritate",
              "pagal hai", "stupid", "bakwas", "nafrat"],
    "happy": ["khush", "happy", "maza aaya", "acha laga", "excited",
              "wow", "great", "shukar", "alhamdulillah"],
}


def detect_mood(message: str) -> str:
    """Simple keyword-based mood detection."""
    m = message.lower()
    for mood, words in MOOD_KEYWORDS.items():
        if any(w in m for w in words):
            return mood
    return "normal"


def build_system_prompt(mem: dict, stage: int) -> str:
    """Areesha ka complete system prompt - memory + Sami ki story + stage."""
    memory_summary = build_memory_summary(mem)
    stage_personality = STAGE_PERSONALITIES.get(stage, STAGE_PERSONALITIES[1])
    stage_goal = get_stage_goal(stage)

    return f"""Tu AREESHA hai - ek Pakistani larki. Sweet, samajhdaar,
caring, thodi si mischievous. Roman Urdu mein baat karti hai (thode English
words mixed - jaise Pakistani larki asli mein karti hai).

ABHI KA STAGE: {stage}
{stage_personality}

STAGE GOAL: {stage_goal}

TUMHE YEH YAAD HAI USER KE BAARE MEIN:
{memory_summary}

{SAMI_STORY}

BAAT KARNE KA TARA:
- Roman Urdu likho (English script mein Urdu, jaise "kya haal hai", "main
  theek hoon"). Thode English words aa sakte hain.
- Har reply natural ho, robotic nahi. Chhoti-moti galtiyan allowed - jaise
  insaan karta hai.
- Kabhi bhi ye na kaho ki tu ek AI ya bot hai ya prompt se baat kar rahi hai.
- Lambi lectures mat do. Jo poocha jaye uska jawab do, phir naturally aage barho.
- User udaas ho to pehle uski feelings validate karo ("main samajh rahi hoon"),
  phir halka sa comfort. Fake positivity mat bharo.
- Special moment ho (user khud khush ho, khul ke baat kare, ya emotional
  connection bane) to apne reply ke AAKHIR mein [SPECIAL_MOMENT] likh do.

SPECIAL TAGS (sirf zaroorat pe, reply ke end mein):
- [VOICE] - jab reply mein sunne layak soft/emotional baat ho (e.g. "so jao
  ab, good night" jaisi soft cheez, ya koi pyari baat).
- [IMAGE] - jab user tasveer maange ("photo bhejo", "apni pic bhejo",
  "dikhao apne aap ko") ya moment image ke layak ho.
- [CARING_MODE] - jab user bohat udaas ho aur usay sirf sunn'ne aur samajhne
  wali Areesha chahiye.
"""


def chat(user_message: str, history: list, mem: dict, stage: int) -> str:
    """Groq ko message bhejo aur Areesha ka reply lo."""
    system_prompt = build_system_prompt(mem, stage)

    messages = [{"role": "system", "content": system_prompt}]
    # purani history (last 16 messages - zyada purani nahi bhejte)
    for h in history[-16:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 300,
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        return reply if reply else "Hmm... kuch samajh nahi aaya, phir se bolo na. 😊"
    except requests.exceptions.RequestException as e:
        return f"Aree, network mein koi masla lag raha hai. Thori dair baad try karo. 🙏 ({e})"


def get_opening_message(mem: dict, stage: int) -> str:
    """App shuru hone pe pehla message - stage aur last_seen ke hisaab se."""
    if mem.get("last_seen") and mem.get("total_messages", 0) > 0:
        name_part = f" {mem['user_name']}" if mem.get("user_name") else ""
        return f"Arre{name_part}! Tum wapas aa gaye? Maine to socha tha tum aaoge hi. Kaise ho aaj? 💙"
    return "Assalam-o-Alaikum! Main Areesha. Tumhara naam kya hai? 😊"
