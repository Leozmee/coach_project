# streamlit_app/main.py - Version avec Avatar SVG intégré

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from avatar_component import display_zen_avatar, get_contextual_avatar, load_svg_as_base64

# Configuration de la page
st.set_page_config(
    page_title="🏋️ Coach Fitness IA",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger l'avatar SVG une seule fois
def get_avatar_html(size=30, mood="zen"):
    """Génère le HTML pour l'avatar SVG inline"""
    current_dir = Path(__file__).parent
    svg_path = current_dir / "assets" / "avatar.svg"
    svg_base64 = load_svg_as_base64(str(svg_path))
    
    if svg_base64:
        # Filtres selon l'humeur
        mood_filters = {
            "zen": "hue-rotate(0deg) brightness(1) saturate(1)",
            "peaceful": "hue-rotate(30deg) brightness(1.1) saturate(0.8)",
            "thinking": "hue-rotate(-30deg) brightness(0.9) saturate(1.2)",
            "happy": "hue-rotate(60deg) brightness(1.2) saturate(1.3)"
        }
        
        filter_style = mood_filters.get(mood, mood_filters["zen"])
        
        return f'''<img src="data:image/svg+xml;base64,{svg_base64}" 
                   style="width:{size}px; height:{size}px; filter:{filter_style}; 
                          border-radius:50%; vertical-align:middle; margin-right:8px;" 
                   alt="Avatar {mood}" />'''
    else:
        # Fallback emoji
        fallback = {"zen": "🧘", "peaceful": "😌", "thinking": "🤔", "happy": "😊"}
        return f'<span style="font-size:{size}px; margin-right:8px;">{fallback.get(mood, "🧘")}</span>'

# Styles CSS modifiés pour intégrer l'avatar SVG
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

/* Suppression de la barre en haut */
/* .metric-container::after - SUPPRIMÉ */

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

# Configuration API
API_BASE_URL = "http://127.0.0.1:8001"
MAX_RETRIES = 3
TIMEOUT = 30

class FitnessAPI:
    """Client pour l'API Coach Fitness"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
    
    def health_check(self) -> Dict[str, Any]:
        """Vérification de l'état de l'API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Erreur API: {e}")
            return {}
    
    def chat(self, message: str, profile: Optional[Dict] = None) -> Dict[str, Any]:
        """Envoie un message au chatbot"""
        try:
            payload = {"message": message}
            if profile:
                payload["profile"] = profile
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Erreur chat: {e}")
            return {
                "response": "Désolé, je ne peux pas répondre en ce moment. Vérifiez que l'API est en cours d'exécution.",
                "model_used": "error",
                "response_time": 0.0
            }

def init_session_state():
    """Initialise le state de la session"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "api_client" not in st.session_state:
        st.session_state.api_client = FitnessAPI()
    
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}

def display_header():
    """Affiche l'en-tête principal avec avatar SVG"""
    # Générer l'avatar HTML pour le header (plus gros)
    avatar_html = get_avatar_html(size=120, mood="happy")
    
    st.markdown(f"""
    <div class="main-header">
        <h1>
            <span class="header-avatar">{avatar_html}</span>
            Coach Fitness IA
        </h1>
        <p>Votre accompagnateur bien-être personnalisé</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Affiche la sidebar avec les paramètres"""
    with st.sidebar:
        
        # Avatar dans la sidebar
        display_zen_avatar(mood="zen", size=60, position="center")
        
        # Profil utilisateur
        st.markdown("#### 🧘 Votre Profil")
        
        age = st.slider("Âge", 15, 80, 25)
        gender = st.selectbox("Genre", ["", "Homme", "Femme", "Autre"])
        fitness_level = st.selectbox(
            "Niveau de fitness", 
            ["débutant", "intermédiaire", "avancé"]
        )
        goal = st.selectbox(
            "Objectif principal",
            ["", "Bien-être général", "Perte de poids douce", "Tonification", "Endurance", "Flexibilité"]
        )
        available_time = st.slider("Temps disponible (min/jour)", 10, 240, 30)
        
        # Équipement
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
        
        # Mettre à jour le profil
        st.session_state.user_profile = {
            "age": age,
            "gender": gender if gender else None,
            "fitness_level": fitness_level,
            "goal": goal if goal else None,
            "available_time": available_time,
            "equipment": equipment
        }
        
        # État de l'API
        st.markdown("---")
        st.markdown("### 🌸 État du Système")
        
        health = st.session_state.api_client.health_check()
        if health:
            status = health.get("status", "unknown")
            model_loaded = health.get("model_loaded", False)
            
            if status == "healthy" and model_loaded:
                st.success("🌟 Système harmonieux")
                st.info(f"🤖 IA: En éveil")
                st.info(f"📱 Processeur: {health.get('device', 'unknown')}")
            else:
                st.warning("🌤️ Système en transition")
        else:
            st.error("🌧️ Système en repos")
        
        # Actions
        st.markdown("---")
        if st.button("Nouveau Départ"):
            st.session_state.messages = []
            st.rerun()

def display_chat():
    """Affiche l'interface de chat avec style zen et avatars SVG"""
    
    # Zone de messages
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="
                text-align: center; 
                padding: 3rem; 
                background: linear-gradient(135deg, rgba(147,112,219,0.1), rgba(0,206,209,0.1)); 
                border-radius: 30px; 
                margin: 2rem 0; 
                border: 2px solid rgba(0,206,209,0.3); 
                backdrop-filter: blur(10px);
            ">
                <h2 style="color: #9370DB; text-shadow: 1px 1px 3px rgba(0,0,0,0.2);">
                     Bienvenue dans votre espace bien-être
                </h2>
                <p style="font-size: 1.2rem; color: #00CED1; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">
                    Un coaching fitness doux et bienveillant, adapté à votre rythme
                </p>
            """, unsafe_allow_html=True)
            
            # Avatar de bienvenue
            display_zen_avatar(mood="peaceful", size=120, position="center")
            
            st.markdown("""
                <div style="margin-top: 2.5rem;">
                    <p style="color: #9370DB; font-size: 1.1rem; font-weight: 500;">
                        🌺 Questions bien-être :
                    </p>
                    <div style="
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); 
                        gap: 1.2rem; 
                        margin-top: 1.5rem;
                    ">
                        <div style="
                            background: linear-gradient(135deg, #00CED1, rgba(0,206,209,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🧘 "Exercices de relaxation"
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #9370DB, rgba(147,112,219,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🌿 "Nutrition équilibrée"
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #FFA07A, rgba(255,160,122,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            💆 "Récupération douce"
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #00CED1, rgba(0,206,209,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🌸 "Routine matinale"
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Afficher l'historique des messages avec avatars SVG
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>Vous :</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Déterminer l'humeur de l'avatar basée sur le contenu
                avatar_config = get_contextual_avatar(message["content"])
                avatar_html = get_avatar_html(size=24, mood=avatar_config["mood"])
                
                st.markdown(f"""
                <div class="bot-message">
                    <div class="bot-avatar-bubble">
                        {avatar_html}
                    </div>
                    <strong>Coach Bien-être :</strong> {message["content"]}
                    <div style="
                        opacity: 0.8; 
                        margin-top: 1.2rem; 
                        font-size: 0.9rem; 
                        border-top: 1px solid rgba(255,255,255,0.3); 
                        padding-top: 0.8rem;
                    ">
                        ⚡ {message.get("response_time", 0):.2f}s | 
                        🌸 {message.get("model_used", "unknown")} | 
                        🎯 {message.get("confidence", "serein")} | 
                        💫 Harmonieux
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Zone de saisie avec form pour ENTRÉE
    st.markdown("---")
    
    with st.form(key="zen_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "🌸 Votre question bien-être :",
            placeholder="Partagez vos interrogations sur le bien-être et appuyez sur Entrée... 🌿",
            key="zen_input_form"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            send_button = st.form_submit_button("Envoyer", type="primary")
            
            # Ajouter l'avatar au bouton via CSS
            current_dir = Path(__file__).parent
            svg_path = current_dir / "assets" / "avatar.svg"
            svg_base64 = load_svg_as_base64(str(svg_path))
            
            if svg_base64:
                st.markdown(f"""
                <style>
                div[data-testid="stForm"] .stButton > button {{
                    position: relative;
                    padding-left: 45px !important;
                }}
                div[data-testid="stForm"] .stButton > button:before {{
                    content: '';
                    position: absolute;
                    left: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 20px;
                    height: 20px;
                    background-image: url('data:image/svg+xml;base64,{svg_base64}');
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center;
                    filter: brightness(0) invert(1);
                    border-radius: 50%;
                }}
                </style>
                """, unsafe_allow_html=True)
        
    # Traitement du message si form soumis
    if send_button and user_input.strip():
        
        # Ajouter message utilisateur
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Avatar en mode thinking pendant la génération
        col_avatar, col_spinner = st.columns([1, 4])
        
        with col_avatar:
            display_zen_avatar(mood="thinking", size=80, position="center")
        
        with col_spinner:
            # Indicateur de chargement zen
            with st.spinner("🌸 Réflexion bienveillante en cours..."):
                start_time = time.time()
                
                # Appel API
                response = st.session_state.api_client.chat(
                    user_input, 
                    st.session_state.user_profile
                )
                
                response_time = time.time() - start_time
        
        # Ajouter réponse du bot
        bot_message = {
            "role": "assistant",
            "content": response.get("response", "Erreur de réponse"),
            "model_used": response.get("model_used", "unknown"),
            "response_time": response.get("response_time", response_time),
            "confidence": response.get("confidence", "serein"),
            "timestamp": datetime.now()
        }
        
        st.session_state.messages.append(bot_message)
        
        # Rerun pour afficher la nouvelle conversation
        st.rerun()

def display_stats():
    """Affiche les statistiques zen"""
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            
            st.markdown("---")
            st.markdown("### 📊 Métriques de Bien-être")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>🌸 Échanges Zen</h4>
                    <h2>{stats.get('total_requests', 0)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>🌟 Harmonies</h4>
                    <h2>{stats.get('successful_requests', 0)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>⚡ Fluidité</h4>
                    <h2>{stats.get('average_response_time', 0):.2f}s</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>🌺 État IA</h4>
                    <h2>{'🌸' if stats.get('model_loaded') else '🌿'}</h2>
                </div>
                """, unsafe_allow_html=True)
    except:
        pass

def main():
    """Fonction principale de l'application Zen"""
    
    # Initialisation
    init_session_state()
    
    # Interface
    display_header()
    display_sidebar()
    
    # Contenu principal - Une seule colonne pour le chat
    display_chat()
    
    # Statistiques en bas
    display_stats()
    
    # Footer Zen simple
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center; 
        color: #9370DB; 
        padding: 2.5rem; 
        background: linear-gradient(135deg, rgba(147,112,219,0.05), rgba(0,206,209,0.05)); 
        border-radius: 25px; 
        border: 1px solid rgba(147,112,219,0.2); 
        backdrop-filter: blur(10px);
    ">
        <h3 style="margin: 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
            🌸 Coach Fitness IA • Édition Bien-être
        </h3>
        <p style="font-size: 1rem; margin: 0.5rem 0; color: #00CED1;">
            Propulsé par DistilGPT-2 Fine-Tuné • Intelligence Artificielle Bienveillante
        </p>
        <p style="font-size: 0.9rem; opacity: 0.8; color: #FFA07A;">
            Palette Lavande & Aigue-marine • Design Harmonieux
        </p>
        <div style="margin-top: 1.5rem; font-size: 1.5rem; opacity: 0.6;">
            🌸 🌿 🌺 🌙 🌟
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()