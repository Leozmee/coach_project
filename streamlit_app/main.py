# streamlit_app/main.py
# --------------------------------------------------
# Coach Fitness IA – Streamlit + Avatar + Whisper-API + YouTube
# --------------------------------------------------

import os
import io
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import requests
import soundfile as sf
import openai
from dotenv import load_dotenv
from avatar_component import display_zen_avatar, get_contextual_avatar, load_svg_as_base64
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# ───────────────────────────────────────────────────
# ENV & KEYS
# ───────────────────────────────────────────────────
load_dotenv()
openai.api_key  = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
API_BASE_URL    = "http://127.0.0.1:8001"
TIMEOUT         = 30

# ───────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────
def transcribe_via_openai(pcm_bytes: bytes) -> str:
    """Transcrit du PWM en ligne via Whisper API."""
    # Convertir bytes PCM en WAV en mémoire
    data, sr = sf.read(io.BytesIO(pcm_bytes), dtype="int16")
    wav_buf = io.BytesIO()
    sf.write(wav_buf, data, sr, format="WAV")
    wav_buf.seek(0)

    resp = openai.Audio.transcribe(
        model="whisper-1",
        file=wav_buf,
        response_format="json",
        language="fr",
    )
    return resp.get("text", "").strip()

def search_youtube(query: str, max_results: int = 1):
    """Renvoie liste de (title, url) YouTube."""
    if not YOUTUBE_API_KEY:
        return []
    endpoint = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "safeSearch": "strict",
        "relevanceLanguage": "fr",
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url) as resp:
            items = json.loads(resp.read().decode()).get("items", [])
    except Exception as e:
        st.error(f"YouTube error: {e}")
        return []
    return [
        (it["snippet"]["title"], f"https://www.youtube.com/watch?v={it['id']['videoId']}")
        for it in items
    ]

def get_avatar_html(size=30, mood="zen") -> str:
    """SVG avatar inline."""
    svg_b64 = load_svg_as_base64(Path(__file__).parent/"assets"/"avatar.svg")
    if svg_b64:
        return (f'<img src="data:image/svg+xml;base64,{svg_b64}" '
                f'style="width:{size}px;height:{size}px;border-radius:50%;" />')
    return "🧘"

# ───────────────────────────────────────────────────
# API client
# ───────────────────────────────────────────────────
class FitnessAPI:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session  = requests.Session()

    def chat(self, message: str, profile: Dict[str,Any]):
        try:
            r = self.session.post(
                f"{self.base_url}/chat",
                json={"message": message, "profile": profile},
                timeout=TIMEOUT
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.error(f"API error: {e}")
            return {"response": "Erreur API", "response_time": 0, "confidence": "—"}

# ───────────────────────────────────────────────────
# Session state init
# ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_client" not in st.session_state:
    st.session_state.api_client = FitnessAPI()
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

# ───────────────────────────────────────────────────
# Streamlit config + CSS
# ───────────────────────────────────────────────────
st.set_page_config(
    page_title="🏋️ Coach Fitness IA",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ==================== PALETTE LAVANDE & AIGUE-MARINE ==================== */
:root {
    --lavande-principal: #9370DB;
    --aigue-marine: #00CED1;
    --saumon-orange: #FFA07A;
    --fond-clair: #F8F8F8;
    --texte-fonce: #333333;
    --lavande-clair: rgba(147, 112, 219, 0.1);
    --aigue-marine-clair: rgba(0, 206, 209, 0.1);
}
/* Style général */
.stApp {
    background: linear-gradient(135deg, var(--lavande-principal) 0%, #B19CD9 50%, #E6E6FA 100%);
    color: var(--texte-fonce);
}
/* Header */
.main-header {
    background: linear-gradient(135deg, var(--lavande-principal), var(--aigue-marine), var(--saumon-orange));
    background-size: 400% 400%;
    animation: gentle-flow 12s ease infinite;
    padding: 2.5rem;
    border-radius: 30px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow:
        0 20px 60px rgba(147,112,219,0.3),
        inset 0 1px 3px rgba(255,255,255,0.5);
    border: 1px solid rgba(255,255,255,0.3);
    backdrop-filter: blur(10px);
}
@keyframes gentle-flow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.main-header h1 {
    color: white;
    font-size: 3.2rem;
    margin: 0;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    font-weight: 600;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
}
.main-header p {
    color: rgba(255,255,255,0.95);
    font-size: 1.3rem;
    margin: 0.8rem 0 0 0;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
    font-style: italic;
}
/* Messages */
.user-message {
    background: linear-gradient(135deg, var(--aigue-marine) 0%, #40E0D0 100%);
    color: white;
    padding: 1.8rem;
    border-radius: 25px 25px 8px 25px;
    margin: 1.2rem 0;
    box-shadow:
        0 10px 30px rgba(0,206,209,0.3),
        inset 0 1px 3px rgba(255,255,255,0.3);
    animation: slideInRight 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
    border: 1px solid rgba(255,255,255,0.4);
    position: relative;
    backdrop-filter: blur(5px);
}
.user-message::before {
    content: "💭";
    position: absolute;
    top: -12px; right: -12px;
    background: linear-gradient(45deg, var(--saumon-orange),#FFB89A);
    width: 35px; height: 35px;
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.2);
    border:2px solid white;
    font-size:1.1rem;
}
.bot-message {
    background: linear-gradient(135deg, var(--lavande-principal) 0%, #B19CD9 100%);
    color: white;
    padding: 1.8rem 1.8rem 1.8rem 3rem;
    border-radius: 25px 25px 25px 8px;
    margin: 1.2rem 0 1.2rem 2rem;
    box-shadow:
        0 10px 30px rgba(147,112,219,0.3),
        inset 0 1px 3px rgba(255,255,255,0.3);
    animation: slideInLeft 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
    border: 1px solid rgba(255,255,255,0.4);
    position: relative; backdrop-filter: blur(5px);
}
.bot-avatar-bubble {
    position:absolute; top:15px; left:-20px;
    background: linear-gradient(45deg,var(--aigue-marine),#40E0D0);
    width:40px;height:40px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.2);
    border:2px solid white;animation:gentle-glow 3s ease-in-out infinite;
    overflow:hidden; z-index:10;
}
.bot-avatar-bubble img {
    width:24px!important;height:24px!important;
    border-radius:50%;object-fit:cover;
}
@keyframes gentle-glow {
    0%,100%{box-shadow:0 4px 12px rgba(0,0,0,0.2),0 0 8px var(--aigue-marine);transform:scale(1);}
    50%{box-shadow:0 4px 12px rgba(0,0,0,0.2),0 0 16px var(--aigue-marine);transform:scale(1.05);}
}
@keyframes slideInRight {from{opacity:0;transform:translateX(30px) scale(0.95);}to{opacity:1;transform:translateX(0) scale(1);}}
@keyframes slideInLeft  {from{opacity:0;transform:translateX(-30px) scale(0.95);}to{opacity:1;transform:translateX(0) scale(1);}}
/* Sidebar */
.css-1d391kg {
    background: linear-gradient(135deg, var(--fond-clair), rgba(147,112,219,0.05));
    backdrop-filter: blur(15px);
    border-radius:25px; border:1px solid rgba(147,112,219,0.2);
    box-shadow:0 10px 25px rgba(147,112,219,0.15);
}
/* Form */
.stForm {
    background: linear-gradient(135deg, var(--lavande-clair), var(--aigue-marine-clair));
    backdrop-filter: blur(15px); border-radius:25px; padding:2rem;
    border:2px solid var(--aigue-marine); box-shadow:0 15px 35px rgba(0,206,209,0.2),inset 0 1px 3px rgba(255,255,255,0.3);
    position:relative; overflow:hidden;
}
.stForm::before {
    content:'';position:absolute;top:-2px;left:-2px;right:-2px;bottom:-2px;
    background:linear-gradient(45deg,var(--aigue-marine),var(--lavande-principal),var(--saumon-orange),var(--aigue-marine));
    border-radius:25px;z-index:-1;animation:gentle-border 6s linear infinite;opacity:0.6;
}
@keyframes gentle-border {0%{background-position:0% 50%;}100%{background-position:400% 50%;}}
.stTextInput > div > div > input {background:rgba(255,255,255,0.95)!important;backdrop-filter:blur(10px);border:2px solid var(--aigue-marine);border-radius:20px;color:var(--texte-fonce);font-size:1.1rem;padding:1rem 1.2rem;transition:all .3s cubic-bezier(.25,.46,.45,.94);font-weight:400;}
.stTextInput > div > div > input:focus {border-color:var(--lavande-principal);background:rgba(255,255,255,0.98)!important;box-shadow:0 0 20px rgba(0,206,209,0.3),0 0 40px rgba(147,112,219,0.2);transform:scale(1.02);}
.stTextInput > div > div > input::placeholder {color:rgba(147,112,219,0.6);font-style:italic;}
.stButton > button {background:linear-gradient(45deg,var(--aigue-marine),var(--saumon-orange));color:white;border:none;border-radius:20px;padding:.9rem 2.5rem;font-weight:600;font-size:1.1rem;transition:all .3s cubic-bezier(.25,.46,.45,.94);box-shadow:0 6px 20px rgba(0,206,209,0.3),inset 0 1px 3px rgba(255,255,255,0.3);text-transform:capitalize;letter-spacing:.5px;}
.stButton > button:hover {transform:translateY(-3px) scale(1.05);box-shadow:0 12px 30px rgba(0,206,209,0.4),inset 0 2px 6px rgba(255,255,255,0.4);background:linear-gradient(45deg,#20B2AA,var(--aigue-marine));}
.metric-container {background:linear-gradient(135deg,var(--fond-clair),rgba(0,206,209,0.08));backdrop-filter:blur(15px);padding:1.8rem;border-radius:25px;margin:1.2rem 0;border:2px solid var(--aigue-marine);box-shadow:0 10px 25px rgba(0,206,209,0.2),inset 0 1px 3px rgba(255,255,255,0.5);transition:all .3s cubic-bezier(.25,.46,.45,.94);position:relative;}
.metric-container:hover {transform:translateY(-5px) scale(1.02);box-shadow:0 15px 35px rgba(0,206,209,0.3),0 0 20px rgba(147,112,219,0.2);border-color:var(--lavande-principal);}
.metric-container h4 {margin:0 0 1rem 0;color:var(--lavande-principal);font-size:1rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;}
.metric-container h2 {margin:0;color:var(--aigue-marine);font-size:2.2rem;font-weight:700;text-shadow:1px 1px 3px rgba(0,0,0,0.1);}
.stSuccess {background:linear-gradient(135deg,var(--aigue-marine-clair),rgba(0,206,209,0.15));border:2px solid var(--aigue-marine);border-radius:18px;color:var(--texte-fonce);backdrop-filter:blur(10px);}
.stError   {background:linear-gradient(135deg,rgba(255,107,107,0.1),rgba(255,107,107,0.2));border:2px solid #FF6B6B;border-radius:18px;backdrop-filter:blur(10px);}
.stInfo    {background:linear-gradient(135deg,var(--lavande-clair),rgba(147,112,219,0.15));border:2px solid var(--lavande-principal);border-radius:18px;color:var(--texte-fonce);backdrop-filter:blur(10px);}
.stSpinner > div {border-top-color:var(--aigue-marine)!important;border-right-color:var(--lavande-principal)!important;border-bottom-color:var(--saumon-orange)!important;border-width:3px!important;}
.header-avatar {animation:gentle-float 4s ease-in-out infinite;}
@keyframes gentle-float {0%,100%{transform:translateY(0) rotate(0);}50%{transform:translateY(-5px) rotate(2deg);}}
@media (max-width:768px){.main-header h1{font-size:2.5rem;flex-direction:column;gap:10px;}.main-header p{font-size:1.1rem;}.user-message,.bot-message{padding:1.5rem;font-size:1rem;border-radius:20px;}.metric-container h2{font-size:1.8rem;}}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────
# Header & Sidebar
# ───────────────────────────────────────────────────
def display_header():
    st.markdown(f"""
        <div class="main-header">
            <h1>{get_avatar_html(120,'happy')} Coach Fitness IA</h1>
            <p>Votre accompagnateur bien-être personnalisé</p>
        </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    with st.sidebar:
        display_zen_avatar(mood="zen", size=60, position="center")
        st.markdown("#### 🧘 Votre Profil")
        # Sliders & selectboxes
        age = st.slider("Âge", 15, 80, 25)
        gender = st.selectbox("Genre", ["", "Homme", "Femme", "Autre"])
        fitness_level = st.selectbox("Niveau de fitness", ["débutant", "intermédiaire", "avancé"])
        goal = st.selectbox("Objectif principal", ["", "Bien-être général", "Perte de poids douce", "Tonification", "Endurance", "Flexibilité"])
        available_time = st.slider("Temps disponible (min/jour)", 10, 240, 30)
        st.markdown("#### 🏃 Équipement Disponible")
        equipment = []
        if st.checkbox("Exercices au poids du corps"):
            equipment.append("aucun")
        if st.checkbox("Haltères légers"):
            equipment.append("haltères")
        if st.checkbox("Élastiques/bandes"):
            equipment.append("élastiques")
        if st.checkbox("Tapis de yoga"):
            equipment.append("tapis")
        if st.checkbox("Ballon de fitness"):
            equipment.append("ballon")
        # Update profile
        st.session_state.user_profile = {
            "age": age,
            "gender": gender or None,
            "fitness_level": fitness_level,
            "goal": goal or None,
            "available_time": available_time,
            "equipment": equipment
        }
        st.markdown("---")
        if st.button("🔄 Nouveau départ"):
            st.session_state.messages = []
            st.rerun()

# ───────────────────────────────────────────────────
# Chat + Whisper-API + YouTube
# ───────────────────────────────────────────────────
def display_chat():
    voice_text = ""
    # 1) Capture audio
    webrtc_ctx = webrtc_streamer(
        key="speech", mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True
    )
    if webrtc_ctx.audio_receiver:
        frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        if frames:
            pcm = b"".join(f.to_ndarray().tobytes() for f in frames)
            try:
                voice_text = transcribe_via_openai(pcm)
                if voice_text:
                    st.info(f"🎤 Transcrit : **{voice_text}**")
            except Exception as e:
                st.warning(f"Transcription failed: {e}")

    # 2) Affichage historique
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-message"><strong>Vous :</strong> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            avatar = get_avatar_html(24, get_contextual_avatar(msg["content"])["mood"])
            st.markdown(f"""
                <div class="bot-message">
                  <div class="bot-avatar-bubble">{avatar}</div>
                  <strong>Coach :</strong> {msg["content"]}
                  <div style="opacity:.7;font-size:.85rem;margin-top:.5rem;">
                    ⚡ {msg["response_time"]:.2f}s | 🎯 {msg["confidence"]}
                  </div>
                </div>""", unsafe_allow_html=True)
            if yt := msg.get("youtube_url"):
                st.video(yt)

    st.markdown("---")
    # 3) Formulaire
    with st.form("q_form", clear_on_submit=True):
        txt = st.text_input("🌸 Votre question :", value=voice_text, placeholder="…")
        ok  = st.form_submit_button("Envoyer")
    # 4) Traitement
    if ok and txt.strip():
        st.session_state.messages.append(
            {"role": "user", "content": txt, "timestamp": datetime.now()}
        )
        with st.spinner("🤖 Réflexion…"):
            t0 = time.time()
            resp = st.session_state.api_client.chat(txt, st.session_state.user_profile)
            rt = time.time() - t0
        bot = {
            "role": "assistant",
            "content": resp.get("response", "Désolé…"),
            "response_time": resp.get("response_time", rt),
            "confidence": resp.get("confidence", "—"),
            "timestamp": datetime.now()
        }
        vids = search_youtube(f"{txt} entraînement tutoriel", 1)
        if vids:
            bot["youtube_url"] = vids[0][1]
        st.session_state.messages.append(bot)
        st.rerun()

# ───────────────────────────────────────────────────
# Stats
# ───────────────────────────────────────────────────
def display_stats():
    st.sidebar.markdown("---")
    st.sidebar.info(f"💬 Échanges : {len(st.session_state.messages)}")

# ───────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────
def main():
    display_header()
    display_sidebar()
    display_chat()
    display_stats()

if __name__ == "__main__":
    main()
