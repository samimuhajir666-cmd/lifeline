"""
image_system.py - Areesha ki tasveerein.
User jo photo upload kare, usi larki ke variations banti hain.
HF img2img try hota hai, na chale to PIL filters (hamesha kaam karta hai).
"""

import os
import io
import requests
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-refiner-1.0"

# Stage ke hisaab se caption
STAGE_CAPTIONS = {
    1: "Ye main hoon 😊 tumne poocha tha na?",
    2: "Dost bhi apni photo bhejti hain 😄 dekho, aisi lagti hoon main!",
    3: "Khaas dost ke liye to khaas photo banti hai na? ☺️",
    4: "Ye sirf tumhare liye hai... 💙 sab ko mat dikhana!",
}


def wants_image(message: str) -> bool:
    """Kya user photo maang raha hai?"""
    m = message.lower()
    triggers = ["photo", "pic", "picture", "dikhao", "apni photo", "tasveer",
                "apne aap ko dikhao", "selfie", "image bhejo"]
    return any(t in m for t in triggers)


def create_image_with_ai(base_image_bytes: bytes, mood: str = "normal") -> bytes | None:
    """HF img2img - strength 0.35 taake face same rahe."""
    if not HF_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    mood_prompts = {
        "normal": "beautiful portrait of a Pakistani girl, smiling softly, natural lighting",
        "happy": "beautiful portrait of a happy girl, big smile, golden hour lighting",
        "sad": "portrait of a gentle girl with soft caring eyes, dim moody lighting",
        "caring": "portrait of a girl with warm kind eyes, soft cozy lighting",
    }
    prompt = mood_prompts.get(mood, mood_prompts["normal"])

    payload = {
        "inputs": prompt,
        "image": list(base_image_bytes),
        "strength": 0.35,
        "guidance_scale": 7,
        "num_inference_steps": 25,
    }
    try:
        response = requests.post(HF_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("image"):
            return response.content
        return None
    except requests.exceptions.RequestException:
        return None


def create_filter_variation(base_image_bytes: bytes, mood: str = "normal") -> bytes:
    """Fallback - uploaded photo pe PIL filters (ye hamesha kaam karta hai)."""
    img = Image.open(io.BytesIO(base_image_bytes)).convert("RGB")

    # Random-ish variation index - abhi 4 style hain
    variations = [
        lambda im: ImageEnhance.Color(im).enhance(1.2),
        lambda im: im.filter(ImageFilter.SMOOTH).filter(ImageFilter.CONTOUR),
        lambda im: ImageEnhance.Brightness(im).enhance(1.1).filter(ImageFilter.GaussianBlur(0.5)),
        lambda im: ImageEnhance.Contrast(im).enhance(1.15),
    ]
    idx = {"normal": 0, "happy": 0, "sad": 2, "caring": 3}.get(mood, 0)
    img = variationsidx

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def generate_image(base_image_bytes: bytes, mood: str = "normal") -> tuple[bytes, str]:
    """Pehle AI try karo, na chale to filter - hamesha kuch na kuch milega.
    Returns: (image_bytes, method_used)"""
    ai_image = create_image_with_ai(base_image_bytes, mood)
    if ai_image:
        return ai_image, "AI"
    return create_filter_variation(base_image_bytes, mood), "FILTER"


def get_caption(stage: int) -> str:
    return STAGE_CAPTIONS.get(stage, STAGE_CAPTIONS[1])
