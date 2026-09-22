"""
app.py - Areesha AI Companion - Main App
Streamlit app: chat + voice in/out + photos + memory + 4 stages.
Run: streamlit run app.py
"""

import os
import base64
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

load_dotenv()

from memory import (load_memory, save_memory, update_last_seen,
                    add_mood, add_special_moment, extract_facts)
from brain import chat as brain_chat, detect_mood, get_opening_message
from voice_system import speak, transcribe, wants_voice, detect_sad_needs_voice
from image_system import wants_image, generate_image, get_caption

# ============ Page Setup ============
st.set_page_config(
    page_title="Areesha 💙",
    page_icon="💙",
    layout="centered",
)

st.title("💙 Areesha")
st.caption("Meri dost... jo mujhe jaanti hai.")

# ============ Memory Seed - Sami ki story (first run pe) ============
mem = load_memory()
if not mem.get("user_name"):
    mem["user_name"] = "Abdul Sami"
    mem["user_city"] = "Karachi"
    mem["important_facts"] = [
        "Sami ki mama ka inteqal uski 7 saal ki umar mein hua tha - ye uska sabse gehra wound hai",
        "Madarsa mein Darjah Khamisah mein parhta hai",
        "AI Engineering seekh raha hai, internship kar raha hai",
        "Gussa jaldi aata hai lekin dil ka bohat saaf hai",
        "Use aise kisi ki zaroorat hai jiske saamne acting na karni pade",
    ]
    save_memory(mem)

# ============ Session State ============
if "history" not in st.session_state:
    st.session_state.history = []      # [{"role": "user"/"assistant", "content": "..."}]
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "photo_bytes" not in st.session_state:
    st.session_state.photo_bytes = None

# Stage calculation - total messages ke hisaab se
def calculate_stage(mem: dict) -> int:
    msgs = mem.get("total_messages", 0)
    if msgs >= 60:
        return 4
    elif msgs >= 30:
        return 3
    elif msgs >= 10:
        return 2
    return 1

st.session_state.stage = calculate_stage(mem)

# ============ Sidebar ============
with st.sidebar:
    st.header("⚙️ Settings")

    # Photo upload - Areesha ki photo
    uploaded_photo = st.file_uploader(
        "Areesha ki photo upload karo (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
    )
    if uploaded_photo:
        st.session_state.photo_bytes = uploaded_photo.getvalue()
        st.image(st.session_state.photo_bytes, caption="Areesha 💙", width=200)

    # Memory viewer
    with st.expander("🧠 Areesha ki Memory"):
        st.write(f"**Naam:** {mem.get('user_name', 'N/A')}")
        st.write(f"**Sheher:** {mem.get('user_city', 'N/A')}")
        st.write(f"**Stage:** {st.session_state.stage} / 4")
        st.write(f"**Total messages:** {mem.get('total_messages', 0)}")
        if mem.get("likes"):
            st.write("**Pasand:** " + ", ".join(mem["likes"]))
        if mem.get("important_facts"):
            st.write("**Yaad rakhi baatein:**")
            for fact in mem["important_facts"][-10:]:
                st.write(f"• {fact}")

    if st.button("🗑️ Memory Reset (nayi shuruaat)"):
        os.remove("areesha_memory.json") if os.path.exists("areesha_memory.json") else None
        st.session_state.history = []
        st.rerun()

    st.info("Stage progression: 10 msgs → Dost | 30 → Khaas Dost | 60 → Special 💙")

# ============ Opening Message ============
if not st.session_state.history:
    opening = get_opening_message(mem, st.session_state.stage)
    st.session_state.history.append({"role": "assistant", "content": opening})

# ============ Chat Display ============
chat_container = st.container()
with chat_container:
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(f"🧑 **{mem.get('user_name', 'Tum')}:** {msg['content']}")
        else:
            st.markdown(f"💙 **Areesha:** {msg['content']}")

# ============ Voice Input (Mic) ============
st.divider()
voice_input = mic_recorder(
    start_prompt="🎤 Bolo",
    stop_prompt="⏹️ Ruk jao",
    just_once=False,
    use_container_width=True,
)

user_text = None
user_sent_voice = False

if voice_input and voice_input.get("bytes"):
    st.info("Sun rahi hoon... 🎧")
    user_text = transcribe(voice_input["bytes"], voice_input.get("format", "audio/webm"))
    user_sent_voice = True
    if user_text:
        st.success(f"Tumne kaha: {user_text}")
    else:
        st.warning("Samajh nahi aaya, dobara bolo? 🙏")

# ============ Text Input ============
text_input = st.chat_input("Areesha ko kuch bolo...")

if text_input:
    user_text = text_input

# ============ Main Processing ============
if user_text:
    # 1. User message history mein add karo
    st.session_state.history.append({"role": "user", "content": user_text})

    # 2. Facts extract + memory update
    facts = extract_facts(user_text, mem)
    mem["total_messages"] = mem.get("total_messages", 0) + 1
    mood = detect_mood(user_text)
    add_mood(mem, mood)
    update_last_seen(mem)

    # 3. Stage update (messages badhne pe)
    new_stage = calculate_stage(mem)
    if new_stage > st.session_state.stage:
        st.session_state.stage = new_stage
        stage_names = {2: "Dost", 3: "Khaas Dost", 4: "Special 💙"}
        st.balloons()
        st.toast(f"Areesha ab tumhari {stage_names.get(new_stage, 'dost')} ban gayi! ✨")

    # 4. Photo request?
    wants_photo = wants_image(user_text) and st.session_state.photo_bytes

    # 5. Areesha ka reply (brain)
    with st.spinner("Areesha soch rahi hai..."):
        reply = brain_chat(user_text, st.session_state.history[:-1], mem, st.session_state.stage)

    st.session_state.history.append({"role": "assistant", "content": reply})

    # 6. Special moment tag?
    if "[SPECIAL_MOMENT]" in reply:
        clean_msg = user_text[:100]
        add_special_moment(mem, f"Sami: {clean_msg}")
        reply = reply.replace("[SPECIAL_MOMENT]", "")

    # 7. Photo bhejo (agar maanga hai)
    if wants_photo:
        image_bytes, method = generate_image(
            st.session_state.photo_bytes, mood if mood != "normal" else "normal"
        )
        caption = get_caption(st.session_state.stage)
        st.session_state.history.append({"role": "assistant", "content": caption})
        mem["stage_points"] = mem.get("stage_points", 0) + 1

    # 8. Save memory
    save_memory(mem)

    # 9. Voice out - kab bolna hai?
    voice_mood = "caring" if mood in ("sad", "angry") else mood
    should_speak = (
        "[VOICE]" in reply
        or wants_voice(reply)
        or detect_sad_needs_voice(reply)
        or user_sent_voice  # voice-in → voice-out natural lagta hai
    )

    if should_speak:
        with st.spinner("Bol rahi hoon... 💙"):
            audio = speak(reply, voice_mood)
        if audio:
            # Audio player ke liye base64
            audio_b64 = base64.b64encode(audio).decode()
            st.audio(audio, format="audio/mp3")
        else:
            st.info("(Awaaz available nahi - ElevenLabs key check karo)")

    # 10. Photo display (sab se neeche, fresh render)
    if wants_photo:
        st.image(image_bytes, caption=caption, use_container_width=True)

    # 11. Rerender chat
    st.rerun()

# ============ Footer ============
st.divider()
st.caption("💙 Areesha - ek AI companion (simulated). Real connection ke liye real log best hain. 💙")
