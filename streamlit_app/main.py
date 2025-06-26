# streamlit_app/main.py - Coach Fitness IA avec voix & YouTube
import os
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import requests
from dotenv import load_dotenv

from avatar_component import (
    display_zen_avatar,
    get_contextual_avatar,
    load_svg_as_base64,
)
from audiorecorder import audiorecorder  # pip install streamlit-audiorecorder
import whisper

# ───────────────────────────────────────────────────
# 1) Chargement Whisper (cache pour les reruns)
# ───────────────────────────────────────────────────
@st.cache_resource
def get_whisper_model():
    return whisper.load_model("base")  # tu peux mettre "small" si GPU limité

WHISPER_MODEL = get_whisper_model()

# ───────────────────────────────────────────────────
# 2) ENV & KEYS
# ───────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ───────────────────────────────────────────────────
# 3) YouTube Helper
# ───────────────────────────────────────────────────
def search_youtube(query: str, max_results: int = 1):
    """Renvoie [(title, url)] pour une requête YouTube."""
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
        "videoDuration": "medium",
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url) as resp:
            items = json.loads(resp.read().decode()).get("items", [])
    except Exception as e:
        st.error(f"❌ Erreur YouTube: {e}")
        return []
    results = []
    for it in items:
        vid = it["id"]["videoId"]
        title = it["snippet"]["title"]
        results.append((title, f"https://www.youtube.com/watch?v={vid}"))
    return results

# ───────────────────────────────────────────────────
# 4) Streamlit config + CSS
# ───────────────────────────────────────────────────
st.set_page_config(
    page_title="🏋️ Coach Fitness IA",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Styles CSS originaux avec juste un ajout pour le sélecteur + YouTube
st.markdown("""
<style>
/* ==================== PALETTE LAVANDE & AIGUE-MARINE ==================== */
:root {
    --lavande-principal: #9370DB;
    --aigue-marine: #00CED1;
    --saumon-orange: #FFA07A;
    --emeraude: #50C878;
    --fond-clair: #F8F8F8;
    --texte-fonce: #333333;
    --lavande-clair: rgba(147, 112, 219, 0.1);
    --aigue-marine-clair: rgba(0, 206, 209, 0.1);
}

/* Style général avec douceur */
.stApp {
    background: linear-gradient(135deg, var(--lavande-principal) 0%, #B19CD9 50%, #E6E6FA 100%);
    color: var(--texte-fonce);
}

/* Header avec douceur moderne */
.main-header {
    background: linear-gradient(135deg, var(--lavande-principal), var(--aigue-marine), var(--saumon-orange));
    background-size: 400% 400%;
    animation: gentle-flow 12s ease infinite;
    padding: 2.5rem;
    border-radius: 30px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 
        0 20px 60px rgba(147, 112, 219, 0.3),
        inset 0 1px 3px rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.3);
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
    color: rgba(255, 255, 255, 0.95);
    font-size: 1.3rem;
    margin: 0.8rem 0 0 0;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
    font-weight: 400;
    font-style: italic;
}

/* Messages avec design doux et moderne */
.user-message {
    background: linear-gradient(135deg, var(--aigue-marine) 0%, #40E0D0 100%);
    color: white;
    padding: 1.8rem;
    border-radius: 25px 25px 8px 25px;
    margin: 1.2rem 0;
    box-shadow: 
        0 10px 30px rgba(0, 206, 209, 0.3),
        inset 0 1px 3px rgba(255, 255, 255, 0.3);
    animation: slideInRight 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.4);
    position: relative;
    backdrop-filter: blur(5px);
}

.user-message::before {
    content: "💭";
    position: absolute;
    top: -12px;
    right: -12px;
    background: linear-gradient(45deg, var(--saumon-orange), #FFB89A);
    border-radius: 50%;
    width: 35px;
    height: 35px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    border: 2px solid white;
    font-size: 1.1rem;
}

.bot-message {
    background: linear-gradient(135deg, var(--lavande-principal) 0%, #B19CD9 100%);
    color: white;
    padding: 1.8rem 1.8rem 1.8rem 3rem;
    border-radius: 25px 25px 25px 8px;
    margin: 1.2rem 0 1.2rem 2rem;
    box-shadow: 
        0 10px 30px rgba(147, 112, 219, 0.3),
        inset 0 1px 3px rgba(255, 255, 255, 0.3);
    animation: slideInLeft 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.4);
    position: relative;
    backdrop-filter: blur(5px);
}

/* Style spécial pour PlayPart AI */
.bot-message.playpart {
    background: linear-gradient(135deg, var(--emeraude) 0%, #66D98C 100%);
}

.bot-avatar-bubble {
    position: absolute;
    top: 15px;
    left: -20px;
    background: linear-gradient(45deg, var(--aigue-marine), #40E0D0);
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    border: 2px solid white;
    animation: gentle-glow 3s ease-in-out infinite;
    z-index: 10;
    overflow: hidden;
}

.bot-avatar-bubble.playpart {
    background: linear-gradient(45deg, var(--emeraude), #66D98C);
}

.bot-avatar-bubble img {
    width: 24px !important;
    height: 24px !important;
    border-radius: 50%;
    object-fit: cover;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
    vertical-align: middle !important;
}

/* Indicateur de modèle utilisé */
.model-indicator {
    position: absolute;
    top: -8px;
    right: 15px;
    background: rgba(255, 255, 255, 0.9);
    color: var(--texte-fonce);
    padding: 0.2rem 0.8rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* Style pour les vidéos YouTube */
.youtube-container {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
    border-radius: 20px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 2px solid var(--saumon-orange);
    box-shadow: 
        0 10px 25px rgba(255, 160, 122, 0.3),
        inset 0 1px 3px rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
}

.youtube-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
    color: var(--texte-fonce);
    font-weight: 600;
}

.youtube-icon {
    color: #FF0000;
    font-size: 1.5rem;
}

@keyframes gentle-glow {
    0%, 100% { 
        box-shadow: 0 4px 12px rgba(0,0,0,0.2), 0 0 8px var(--aigue-marine); 
        transform: scale(1);
    }
    50% { 
        box-shadow: 0 4px 12px rgba(0,0,0,0.2), 0 0 16px var(--aigue-marine); 
        transform: scale(1.05);
    }
}

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(30px) scale(0.95); }
    to { opacity: 1; transform: translateX(0) scale(1); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-30px) scale(0.95); }
    to { opacity: 1; transform: translateX(0) scale(1); }
}

/* Sidebar douce */
.css-1d391kg {
    background: linear-gradient(135deg, var(--fond-clair), rgba(147, 112, 219, 0.05));
    backdrop-filter: blur(15px);
    border-radius: 25px;
    border: 1px solid rgba(147, 112, 219, 0.2);
    box-shadow: 0 10px 25px rgba(147, 112, 219, 0.15);
}

/* Form avec style doux */
.stForm {
    background: linear-gradient(135deg, var(--lavande-clair), var(--aigue-marine-clair));
    backdrop-filter: blur(15px);
    border-radius: 25px;
    padding: 2rem;
    border: 2px solid var(--aigue-marine);
    box-shadow: 
        0 15px 35px rgba(0, 206, 209, 0.2),
        inset 0 1px 3px rgba(255, 255, 255, 0.3);
    position: relative;
    overflow: hidden;
}

.stForm::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, var(--aigue-marine), var(--lavande-principal), var(--saumon-orange), var(--aigue-marine));
    border-radius: 25px;
    z-index: -1;
    animation: gentle-border 6s linear infinite;
    opacity: 0.6;
}

@keyframes gentle-border {
    0% { background-position: 0% 50%; }
    100% { background-position: 400% 50%; }
}

/* Input avec style apaisant - FOND BLANC SIMPLE */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    border: 2px solid var(--aigue-marine);
    border-radius: 20px;
    color: var(--texte-fonce);
    font-size: 1.1rem;
    padding: 1rem 1.2rem;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    font-weight: 400;
}

.stTextInput > div > div > input:focus {
    border-color: var(--lavande-principal);
    background: rgba(255, 255, 255, 0.98) !important;
    box-shadow: 
        0 0 20px rgba(0, 206, 209, 0.3),
        0 0 40px rgba(147, 112, 219, 0.2);
    transform: scale(1.02);
}

.stTextInput > div > div > input::placeholder {
    color: rgba(147, 112, 219, 0.6);
    font-style: italic;
}

/* Selectbox avec style harmonieux */
.stSelectbox > div > div > div {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid var(--emeraude);
    border-radius: 20px;
    color: var(--texte-fonce);
}

.stSelectbox > div > div > div:focus-within {
    border-color: var(--lavande-principal);
    box-shadow: 
        0 0 20px rgba(80, 200, 120, 0.3),
        0 0 40px rgba(147, 112, 219, 0.2);
}

/* Boutons avec douceur */
.stButton > button {
    background: linear-gradient(45deg, var(--aigue-marine), var(--saumon-orange));
    color: white;
    border: none;
    border-radius: 20px;
    padding: 0.9rem 2.5rem;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    box-shadow: 
        0 6px 20px rgba(0, 206, 209, 0.3),
        inset 0 1px 3px rgba(255, 255, 255, 0.3);
    text-transform: capitalize;
    letter-spacing: 0.5px;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 
        0 12px 30px rgba(0, 206, 209, 0.4),
        inset 0 2px 6px rgba(255, 255, 255, 0.4);
    background: linear-gradient(45deg, #20B2AA, var(--aigue-marine));
}

/* Métriques avec style zen - SANS BARRE EN HAUT */
.metric-container {
    background: linear-gradient(135deg, var(--fond-clair), rgba(0, 206, 209, 0.08));
    backdrop-filter: blur(15px);
    padding: 1.8rem;
    border-radius: 25px;
    margin: 1.2rem 0;
    border: 2px solid var(--aigue-marine);
    box-shadow: 
        0 10px 25px rgba(0, 206, 209, 0.2),
        inset 0 1px 3px rgba(255, 255, 255, 0.5);
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    position: relative;
}

.metric-container:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 
        0 15px 35px rgba(0, 206, 209, 0.3),
        0 0 20px rgba(147, 112, 219, 0.2);
    border-color: var(--lavande-principal);
}

.metric-container h4 {
    margin: 0 0 1rem 0;
    color: var(--lavande-principal);
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-container h2 {
    margin: 0;
    color: var(--aigue-marine);
    font-size: 2.2rem;
    font-weight: 700;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}

/* Alertes avec style apaisant */
.stSuccess {
    background: linear-gradient(135deg, var(--aigue-marine-clair), rgba(0, 206, 209, 0.15));
    border: 2px solid var(--aigue-marine);
    border-radius: 18px;
    color: var(--texte-fonce);
    backdrop-filter: blur(10px);
}

.stError {
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 107, 107, 0.2));
    border: 2px solid #FF6B6B;
    border-radius: 18px;
    backdrop-filter: blur(10px);
}

.stInfo {
    background: linear-gradient(135deg, var(--lavande-clair), rgba(147, 112, 219, 0.15));
    border: 2px solid var(--lavande-principal);
    border-radius: 18px;
    color: var(--texte-fonce);
    backdrop-filter: blur(10px);
}

/* Animation du spinner zen */
.stSpinner > div {
    border-top-color: var(--aigue-marine) !important;
    border-right-color: var(--lavande-principal) !important;
    border-bottom-color: var(--saumon-orange) !important;
    border-width: 3px !important;
}

/* Style pour l'avatar dans le header */
.header-avatar {
    animation: gentle-float 4s ease-in-out infinite;
}

@keyframes gentle-float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-5px) rotate(2deg); }
}

/* Responsive design doux */
@media (max-width: 768px) {
    .main-header h1 { 
        font-size: 2.5rem; 
        flex-direction: column;
        gap: 10px;
    }
    .main-header p { 
        font-size: 1.1rem; 
    }
    .user-message, .bot-message { 
        padding: 1.5rem; 
        font-size: 1rem; 
        border-radius: 20px; 
    }
    .metric-container h2 { 
        font-size: 1.8rem; 
    }
}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────
# 5) API client
# ───────────────────────────────────────────────────
API_BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 30

class FitnessAPI:
    def __init__(self, base_url: str = API_BASE_URL):
        self.session = requests.Session()
        self.base_url = base_url

    def health_check(self) -> Dict[str, Any]:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except:
            return {}

    def get_available_models(self) -> Dict[str, Any]:
        try:
            r = self.session.get(f"{self.base_url}/models", timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except:
            return {}

    def switch_model(self, model_type: str) -> Dict[str, Any]:
        try:
            r = self.session.post(
                f"{self.base_url}/models/switch",
                json={"model_type": model_type},
                timeout=TIMEOUT
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def chat(self, message: str, profile: Optional[Dict] = None, model_type: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload = {"message": message}
            if profile:
                payload["profile"] = profile
            if model_type:
                payload["model_type"] = model_type
            r = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type":"application/json"},
                timeout=TIMEOUT
            )
            r.raise_for_status()
            return r.json()
        except:
            return {
                "response": "Désolé, je ne peux pas répondre pour le moment.",
                "model_used": "error",
                "model_name": "Erreur",
                "response_time": 0.0,
                "confidence": "—"
            }

# ───────────────────────────────────────────────────
# 6) Session State init
# ───────────────────────────────────────────────────
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_client" not in st.session_state:
        st.session_state.api_client = FitnessAPI()
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}
    if "available_models" not in st.session_state:
        st.session_state.available_models = {}
    if "current_model" not in st.session_state:
        st.session_state.current_model = None

init_session_state()

# ───────────────────────────────────────────────────
# 7) Header & Sidebar
# ───────────────────────────────────────────────────
def get_avatar_html(size=30, mood="zen"):
    """SVG embarqué pour avatar."""
    svg_b64 = load_svg_as_base64(Path(__file__).parent/"assets"/"avatar.svg")
    if svg_b64:
        return f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width:{size}px;height:{size}px;border-radius:50%;" />'
    return "🧘"

def display_header():
    avatar = get_avatar_html(120, "happy")
    st.markdown(f"""
    <div class="main-header">
      <h1>{avatar} Coach Fitness IA</h1>
      <p>Votre accompagnateur bien-être personnalisé</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    with st.sidebar:
        display_zen_avatar(mood="zen", size=60, position="center")
        st.markdown("#### 🤖 Sélection du modèle IA")
        models_data = st.session_state.api_client.get_available_models()
        if models_data.get("models"):
            st.session_state.available_models = models_data["models"]
            st.session_state.current_model = models_data["current_model"]
            # construit la liste de labels
            mapping = {}
            labels = []
            for k,v in models_data["models"].items():
                if v.get("loaded"):
                    label = v["name"] + (" 🇫🇷" if "distilgpt2" in k else " 🇺🇸")
                    labels.append(label)
                    mapping[label] = k
            idx = labels.index(next(l for l,m in mapping.items() if m==st.session_state.current_model))
            sel = st.selectbox("Choisir :", labels, index=idx)
            if mapping[sel]!=st.session_state.current_model:
                res = st.session_state.api_client.switch_model(mapping[sel])
                if res.get("success"):
                    st.success("✅ Modèle changé")
                    st.session_state.current_model = mapping[sel]
                    time.sleep(1); st.rerun()
                else:
                    st.error(f"❌ {res.get('message')}")
            st.info(f"🎯 Actuel : {models_data['models'][st.session_state.current_model]['name']}")
        else:
            st.error("❌ Pas de modèles dispo")

        st.markdown("---\n#### 🧘 Votre Profil")
        age = st.slider("Âge", 15, 80, 25)
        gender = st.selectbox("Genre", ["","Homme","Femme","Autre"])
        level = st.selectbox("Niveau", ["débutant","intermédiaire","avancé"])
        goal = st.selectbox("Objectif", ["","Bien-être","Perte de poids","Tonification","Endurance"])
        tps = st.slider("Temps (min/jour)", 10,240,30)
        equip=[]
        if st.checkbox("Corps nu"): equip.append("aucun")
        if st.checkbox("Haltères"): equip.append("haltères")
        if st.checkbox("Élastiques"): equip.append("élastiques")
        if st.checkbox("Tapis"): equip.append("tapis")
        st.session_state.user_profile = {
            "age":age,"gender":gender or None,
            "fitness_level":level,"goal":goal or None,
            "available_time":tps,"equipment":equip,
            "enable_youtube": st.checkbox("🔎 YouTube auto", value=True)
        }
        st.markdown("---\n### 🌸 État du Système")
        health = st.session_state.api_client.health_check()
        if health.get("status")=="healthy":
            st.success("🌟 Système OK")
            cm = health.get("current_model")
            name = health["models"][cm]["name"] if cm else "-"
            st.info(f"🤖 IA: {name}")
        else:
            st.warning("⚠️ Système pas prêt")

# ───────────────────────────────────────────────────
# 8) Traitement factorisé
# ───────────────────────────────────────────────────
def handle_user_query(user_input: str):
    """Ajoute user, appelle l’API, recherche YouTube, stocke bot et relance."""
    # 1️⃣ user
    st.session_state.messages.append({
        "role":"user","content":user_input,"timestamp":datetime.now()
    })
    # 2️⃣ API
    with st.spinner("Réflexion…"):
        t0 = time.time()
        resp = st.session_state.api_client.chat(
            user_input,
            st.session_state.user_profile,
            st.session_state.current_model
        )
        rt = time.time() - t0
    # 3️⃣ bot message
    bot_msg = {
        "role":"assistant",
        "content": resp.get("response","Désolé…"),
        "model_used": resp.get("model_used","—"),
        "model_name": resp.get("model_name","—"),
        "response_time": resp.get("response_time", rt),
        "confidence": resp.get("confidence","—"),
        "timestamp": datetime.now()
    }
    # 4️⃣ YouTube
    if st.session_state.user_profile.get("enable_youtube",True) and YOUTUBE_API_KEY:
        with st.spinner("Recherche YouTube…"):
            vids = search_youtube(f"{user_input} entraînement tutoriel",1)
        if vids:
            title, url = vids[0]
            bot_msg["youtube_title"] = title
            bot_msg["youtube_url"]   = url
            bot_msg["content"] += "\n\n📺 J’ai trouvé une vidéo pour vous !"
    # 5️⃣ clear audio & push & rerun
    if "voice" in st.session_state:
        del st.session_state["voice"]   # **important** pour stopper la boucle
    st.session_state.messages.append(bot_msg)
    st.rerun()

# ───────────────────────────────────────────────────
# 9) Zone Chat
# ───────────────────────────────────────────────────
def display_chat():
    # messages existants
    for msg in st.session_state.messages:
        if msg["role"]=="user":
            st.markdown(f'<div class="user-message"><strong>Vous :</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            ava = get_avatar_html(24, get_contextual_avatar(msg["content"])["mood"])
            st.markdown(f'''
                <div class="bot-message">
                  <div class="bot-avatar-bubble">{ava}</div>
                  <strong>Coach :</strong> {msg["content"]}
                  <div style="opacity:.8;margin-top:1rem;font-size:.85rem;">
                    ⚡ {msg["response_time"]:.2f}s | 🎯 {msg["confidence"]}
                  </div>
                </div>
            ''', unsafe_allow_html=True)
            if msg.get("youtube_url"):
                st.video(msg["youtube_url"])

    st.markdown("---")

    # 1️⃣ voix
    audio_seg = audiorecorder("🎤 Appuyez pour parler","Relâchez pour stopper", key="voice")
    if audio_seg:
        with st.spinner("Transcription…"):
            audio_seg.export("tmp.wav",format="wav")
            txt = WHISPER_MODEL.transcribe("tmp.wav", language="fr", fp16=False)["text"].strip()
        if txt:
            handle_user_query(txt)
        return  # on sort, le rerun se fait dans handle_user_query

    # 2️⃣ formulaire texte
    with st.form("form_text", clear_on_submit=True):
        user_input = st.text_input("🌸 Votre question :", key="inp")
        send = st.form_submit_button("Envoyer")
    if send and user_input.strip():
        handle_user_query(user_input)

# ───────────────────────────────────────────────────
# 10) Statistiques (placeholder)
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

if __name__=="__main__":
    main()