# streamlit_app/main.py - Version avec CSS externe

import streamlit as st
import requests
import json
import time
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv
from avatar_component import display_zen_avatar, get_contextual_avatar, load_svg_as_base64

# Configuration de la page
st.set_page_config(
    page_title="🏋️ Coach Fitness IA - Multi-Modèles",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ───────────────────────────────────────────────────
# CHARGEMENT DES STYLES CSS EXTERNES
# ───────────────────────────────────────────────────
def load_external_css():
    """Charge les styles CSS depuis le fichier externe avec gestion d'erreurs"""
    current_dir = Path(__file__).parent
    css_file = current_dir / "styles.css"
    
    try:
        if css_file.exists():
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Ajouter le CSS avec la même méthode que l'original
            st.markdown(f"""
<style>
{css_content}
</style>
""", unsafe_allow_html=True)
            return True
        else:
            st.error(f"❌ Fichier CSS non trouvé: {css_file}")
            return False
    except Exception as e:
        st.error(f"❌ Erreur chargement CSS: {e}")
        return False

# ───────────────────────────────────────────────────
# ENV & KEYS
# ───────────────────────────────────────────────────
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ───────────────────────────────────────────────────
# YouTube Helper
# ───────────────────────────────────────────────────
def search_youtube(query: str, max_results: int = 1):
    """Renvoie liste de (title, url) YouTube."""
    if not YOUTUBE_API_KEY:
        return []
    endpoint = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query + " fitness exercise workout tutorial",
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "safeSearch": "strict",
        "relevanceLanguage": "fr",
        "videoDuration": "medium"  # Eviter les vidéos trop courtes
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

# Configuration API
API_BASE_URL = "http://127.0.0.1:8001"
MAX_RETRIES = 3
TIMEOUT = 30

class FitnessAPI:
    """Client pour l'API Coach Fitness avec support multi-modèles"""
    
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
    
    def get_available_models(self) -> Dict[str, Any]:
        """Récupère la liste des modèles disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Erreur récupération modèles: {e}")
            return {}
    
    def switch_model(self, model_type: str) -> Dict[str, Any]:
        """Change le modèle actuel"""
        try:
            payload = {"model_type": model_type}
            response = self.session.post(
                f"{self.base_url}/models/switch",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Erreur changement modèle: {e}")
            return {"success": False, "message": str(e)}
    
    def chat(self, message: str, profile: Optional[Dict] = None, model_type: Optional[str] = None) -> Dict[str, Any]:
        """Envoie un message au chatbot"""
        try:
            payload = {"message": message}
            if profile:
                payload["profile"] = profile
            if model_type:
                payload["model_type"] = model_type
            
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
                "model_name": "Erreur",
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
    
    if "current_model" not in st.session_state:
        st.session_state.current_model = "local_distilgpt2"
    
    if "available_models" not in st.session_state:
        st.session_state.available_models = {}

def add_dynamic_button_styles(svg_base64):
    """Ajoute les styles dynamiques pour le bouton (qui ne peuvent pas être dans le CSS externe)"""
    if svg_base64:
        st.markdown(f"""
        <style>
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
        <p>Votre accompagnateur bien-être personnalisé avec IA multi-modèles + Vidéos YouTube</p>
    </div>
    """, unsafe_allow_html=True)

def get_model_display_name(model_used: str) -> str:
    """Retourne le nom d'affichage du modèle"""
    model_names = {
        "local_distilgpt2": "DistilGPT-2 🇫🇷",
        "playpart_trainer": "PlayPart AI 🇺🇸",
        "fallback_local_distilgpt2": "Fallback DistilGPT-2 🇫🇷",
        "fallback_playpart_trainer": "Fallback PlayPart AI 🇺🇸"
    }
    return model_names.get(model_used, model_used)

def get_model_chat_class(model_used: str) -> str:
    """Retourne la classe CSS selon le modèle utilisé"""
    if "playpart" in model_used.lower():
        return "playpart"
    return ""

def display_sidebar():
    """Affiche la sidebar avec l'image push-to-talk comme bouton cliquable uniquement"""
    with st.sidebar:
        
        # === IMAGE DU ROBOT COACH + BOUTON PUSH-TO-TALK IMAGE ===
        current_dir = Path(__file__).parent
        robot_image_path = current_dir / "assets" / "robot_coach.png"
        push_to_talk_path = current_dir / "assets" / "push_to_talk.png"
        
        if robot_image_path.exists():
            # Affichage de l'image robot
            col1, col2, col3 = st.columns([0.5, 3, 0.5])
            with col2:
                st.image(
                    str(robot_image_path), 
                    width=200,
                    caption="🤖 Coach IA Personnel"
                )
            
            # === BOUTON PUSH-TO-TALK AVEC IMAGE SEULEMENT ===
            if push_to_talk_path.exists():
                # Convertir l'image en base64
                import base64
                with open(push_to_talk_path, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode()
                
                # Image comme bouton cliquable
                st.markdown(f"""
                <div style="text-align: center; margin: 1rem 0;">
                    <div 
                        onclick="alert(' Fonctionnalité vocale en développement !\\n\\nBientôt disponible :\\n• Reconnaissance vocale\\n• Conversion speech-to-text\\n• Envoi automatique')"
                        style="
                            cursor: pointer;
                            padding: 15px;
                            border-radius: 20px;
                            transition: all 0.3s ease;
                            background: linear-gradient(135deg, rgba(147,112,219,0.1), rgba(0,206,209,0.1));
                            border: 2px solid transparent;
                            display: inline-block;
                            box-shadow: 0 4px 15px rgba(147,112,219,0.2);
                        "
                        onmouseover="
                            this.style.transform='scale(1.1)'; 
                            this.style.borderColor='#9370DB'; 
                            this.style.boxShadow='0 8px 30px rgba(147,112,219,0.4)';
                        "
                        onmouseout="
                            this.style.transform='scale(1)'; 
                            this.style.borderColor='transparent'; 
                            this.style.boxShadow='0 4px 15px rgba(147,112,219,0.2)';
                        "
                        onmousedown="this.style.transform='scale(0.95)';"
                        onmouseup="this.style.transform='scale(1.1)';"
                        title="🎤 Cliquez pour la reconnaissance vocale"
                    >
                        <img src="data:image/png;base64,{img_base64}" 
                             style="
                                width: 100px; 
                                height: auto; 
                                display: block; 
                                margin: 0 auto;
                                filter: drop-shadow(0 2px 8px rgba(147,112,219,0.3));
                             " 
                             alt="Push to Talk" />
                        <p style="
                            color: #9370DB; 
                            font-size: 0.9rem; 
                            margin: 0.8rem 0 0 0; 
                            font-weight: 600;
                            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                        "> Push to Talk</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                        
            else:
                # Fallback si l'image n'existe pas
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="
                        padding: 15px;
                        border: 2px dashed #9370DB;
                        border-radius: 20px;
                        background: rgba(147,112,219,0.1);
                    ">
                        <p style="color: #9370DB; margin: 0;">
                            📁 Ajoutez push_to_talk.png dans assets/
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        else:
            # Fallback simple si pas d'image robot
            display_zen_avatar(mood="zen", size=60, position="center")
        
        # === SÉLECTEUR DE MODÈLE SIMPLE ===
        st.markdown("---")
        st.markdown("#### 🤖 Sélection du Modèle IA")
        
        # Récupérer les modèles disponibles
        models_data = st.session_state.api_client.get_available_models()
        
        if models_data and "models" in models_data:
            st.session_state.available_models = models_data["models"]
            st.session_state.current_model = models_data["current_model"]
            
            # Options pour le selectbox
            model_options = []
            model_mapping = {}
            
            for model_key, model_info in models_data["models"].items():
                if model_info.get("loaded", False):
                    display_name = f"{model_info['name']}"
                    if "distilgpt2" in model_key.lower():
                        display_name += " 🇫🇷"
                    elif "playpart" in model_key.lower():
                        display_name += " 🇺🇸"
                    
                    model_options.append(display_name)
                    model_mapping[display_name] = model_key
            
            # Trouver l'index actuel
            current_display = None
            for display_name, key in model_mapping.items():
                if key == models_data["current_model"]:
                    current_display = display_name
                    break
            
            current_index = model_options.index(current_display) if current_display in model_options else 0
            
            # Selectbox simple
            selected_model = st.selectbox(
                "Choisir le modèle :",
                model_options,
                index=current_index,
                key="model_selector"
            )
            
            # Changer le modèle si différent
            if selected_model in model_mapping:
                selected_key = model_mapping[selected_model]
                if selected_key != st.session_state.current_model:
                    with st.spinner(f"🔄 Changement vers {selected_model}..."):
                        result = st.session_state.api_client.switch_model(selected_key)
                        
                        if result.get("success", False):
                            st.session_state.current_model = selected_key
                            st.success(f"✅ Modèle changé !")
                            time.sleep(1)  # Petite pause pour voir le message
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message', 'Erreur changement modèle')}")
            
            # Info modèle actuel
            current_info = models_data["models"].get(models_data["current_model"], {})
            st.info(f"🎯 **Actuel** : {current_info.get('name', 'Unknown')}")
            
        else:
            st.error("❌ Modèles non disponibles")
        
        # === OPTION YOUTUBE ===
        st.markdown("---")
        st.markdown("#### 📺 Vidéos YouTube")
        
        enable_youtube = st.checkbox("Recherche automatique de vidéos", value=True)
        
        if YOUTUBE_API_KEY:
            st.success("🔑 API YouTube configurée")
        else:
            st.warning("⚠️ Clé API YouTube manquante")
            st.caption("Ajoutez YOUTUBE_API_KEY dans votre .env")
        
        # Profil utilisateur
        st.markdown("---")
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
            "equipment": equipment,
            "enable_youtube": enable_youtube
        }
        
        # État de l'API
        st.markdown("---")
        st.markdown("### 🌸 État du Système")
        
        health = st.session_state.api_client.health_check()
        if health:
            status = health.get("status", "unknown")
            current_model_info = health.get("models", {}).get(health.get("current_model", ""), {})
            
            if status == "healthy":
                st.success("🌟 Système harmonieux")
                st.info(f"🤖 IA: {current_model_info.get('name', 'Unknown')}")
                st.info(f"📱 Device: {health.get('device', 'unknown')}")
                
                # Statut des modèles
                for model_key, model_info in health.get("models", {}).items():
                    icon = "✅" if model_info.get("loaded", False) else "⏳"
                    name = model_info.get("name", model_key)[:15] + "..."
                    st.caption(f"{icon} {name}")
            else:
                st.warning("🌤️ Système en transition")
        else:
            st.error("🌧️ Système en repos")
        
        # Actions
        st.markdown("---")
        if st.button("Nouveau Départ"):
            st.session_state.messages = []
            st.rerun()

def display_youtube_video(title: str, url: str):
    """Affiche une vidéo YouTube dans un container stylisé"""
    st.markdown(f"""
    <div class="youtube-container">
        <div class="youtube-header">
            <span class="youtube-icon">📺</span>
            <span>Vidéo recommandée : {title[:60]}{'...' if len(title) > 60 else ''}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Afficher la vidéo YouTube
    st.video(url)

def display_chat():
    """Affiche l'interface de chat avec style zen et avatars SVG + YouTube"""
    
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
                <div style="margin-top: 2.5rem;">
                    <p style="color: #9370DB; font-size: 1.1rem; font-weight: 500;">
                         Questions adaptées aux modèles :
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
                            🇫🇷 "Exercices de relaxation" 
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #50C878, rgba(80,200,120,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🇺🇸 "Upper body strength training" 
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #9370DB, rgba(147,112,219,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🇫🇷 "Comment adopter une nutrition équilibrée"
                        </div>
                        <div style="
                            background: linear-gradient(135deg, #FFA07A, rgba(255,160,122,0.8)); 
                            padding: 1.3rem; 
                            border-radius: 20px; 
                            color: white; 
                            font-weight: 500;
                        ">
                            🇺🇸 "How to perform burpees correctly" 
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Afficher l'historique des messages avec avatars SVG et indicateurs de modèle
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
                
                # Classes CSS selon le modèle utilisé
                model_class = get_model_chat_class(message.get("model_used", ""))
                model_display = get_model_display_name(message.get("model_used", "unknown"))
                
                st.markdown(f"""
                <div class="bot-message {model_class}">
                    <div class="bot-avatar-bubble {model_class}">
                        {avatar_html}
                    </div>
                    <div class="model-indicator">{model_display}</div>
                    <strong>Coach Bien-être :</strong> {message["content"]}
                    <div style="
                        opacity: 0.8; 
                        margin-top: 1.2rem; 
                        font-size: 0.9rem; 
                        border-top: 1px solid rgba(255,255,255,0.3); 
                        padding-top: 0.8rem;
                    ">
                        ⚡ {message.get("response_time", 0):.2f}s | 
                        🌸 {message.get("model_name", "unknown")} | 
                        🎯 {message.get("confidence", "serein")} | 
                        💫 Harmonieux
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Afficher la vidéo YouTube si présente
                if "youtube_url" in message and message["youtube_url"]:
                    display_youtube_video(
                        message.get("youtube_title", "Vidéo d'exercice"),
                        message["youtube_url"]
                    )
    
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
            
            # Ajouter l'avatar au bouton via CSS dynamique
            current_dir = Path(__file__).parent
            svg_path = current_dir / "assets" / "avatar.svg"
            svg_base64 = load_svg_as_base64(str(svg_path))
            
            # Appliquer les styles dynamiques pour le bouton
            add_dynamic_button_styles(svg_base64)
        
        with col2:
            # Afficher le modèle qui sera utilisé
            current_model_info = st.session_state.available_models.get(st.session_state.current_model, {})
            model_name = current_model_info.get('name', 'Unknown')
            if "distilgpt2" in st.session_state.current_model.lower():
                st.info(f"🇫🇷 Utilise : {model_name}")
            elif "playpart" in st.session_state.current_model.lower():
                st.info(f"🇺🇸 Utilise : {model_name}")
            else:
                st.info(f"🤖 Utilise : {model_name}")
    
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
            current_model_name = st.session_state.available_models.get(st.session_state.current_model, {}).get('name', 'IA')
            with st.spinner(f"🌸 Réflexion bienveillante avec {current_model_name}..."):
                start_time = time.time()
                
                # Appel API avec le modèle actuellement sélectionné
                response = st.session_state.api_client.chat(
                    user_input, 
                    st.session_state.user_profile,
                    None  # Utilise le modèle actuel défini côté API
                )
                
                response_time = time.time() - start_time
        
        # Préparer la réponse du bot
        bot_message = {
            "role": "assistant",
            "content": response.get("response", "Erreur de réponse"),
            "model_used": response.get("model_used", "unknown"),
            "model_name": response.get("model_name", "Unknown AI"),
            "response_time": response.get("response_time", response_time),
            "confidence": response.get("confidence", "serein"),
            "timestamp": datetime.now()
        }
        
        # Recherche YouTube si activée
        if st.session_state.user_profile.get("enable_youtube", False) and YOUTUBE_API_KEY:
            with st.spinner("📺 Recherche de vidéos YouTube..."):
                try:
                    # Créer une requête de recherche adaptée
                    search_query = user_input
                    
                    # Ajouter des mots-clés selon le contenu
                    fitness_keywords = []
                    if any(word in user_input.lower() for word in ["push", "pompes", "pushup"]):
                        fitness_keywords.append("push-ups tutorial")
                    elif any(word in user_input.lower() for word in ["squat", "squats"]):
                        fitness_keywords.append("squat technique")
                    elif any(word in user_input.lower() for word in ["cardio", "running", "course"]):
                        fitness_keywords.append("cardio workout")
                    elif any(word in user_input.lower() for word in ["yoga", "stretching", "étirement"]):
                        fitness_keywords.append("yoga stretching")
                    elif any(word in user_input.lower() for word in ["abs", "abdos", "core"]):
                        fitness_keywords.append("abs workout")
                    elif any(word in user_input.lower() for word in ["upper body", "haut du corps"]):
                        fitness_keywords.append("upper body workout")
                    else:
                        fitness_keywords.append("fitness exercise")
                    
                    # Rechercher sur YouTube
                    search_term = f"{search_query} {' '.join(fitness_keywords)}"
                    videos = search_youtube(search_term, max_results=1)
                    
                    if videos:
                        video_title, video_url = videos[0]
                        bot_message["youtube_url"] = video_url
                        bot_message["youtube_title"] = video_title
                        
                        # Mentionner la vidéo dans la réponse
                        bot_message["content"] += f"\n\n📺 J'ai trouvé une vidéo qui pourrait vous aider !"
                        
                except Exception as e:
                    st.warning(f"⚠️ Erreur recherche YouTube : {e}")
        
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
            st.markdown("### 📊 Métriques de Bien-être Multi-Modèles")
            
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
                current_model_name = stats.get('models', {}).get(stats.get('current_model', ''), {}).get('name', 'Unknown')[:15]
                st.markdown(f"""
                <div class="metric-container">
                    <h4>🤖 IA Actuelle</h4>
                    <h2 style="font-size: 1.5rem;">{current_model_name}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Statistiques d'usage par modèle si disponible
            if stats.get('model_usage', {}):
                st.markdown("#### 📈 Usage par Modèle")
                usage_data = stats['model_usage']
                
                col1, col2 = st.columns(2)
                
                for i, (model_key, usage_count) in enumerate(usage_data.items()):
                    model_name = stats.get('models', {}).get(model_key, {}).get('name', model_key)
                    
                    with col1 if i % 2 == 0 else col2:
                        st.markdown(f"""
                        <div class="metric-container" style="padding: 1rem;">
                            <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">{model_name}</h4>
                            <h2 style="font-size: 1.8rem;">{usage_count}</h2>
                        </div>
                        """, unsafe_allow_html=True)
    except:
        pass

def main():
    """Fonction principale de l'application Zen Multi-Modèles + YouTube"""
    
    # CHARGER LES STYLES CSS EN PREMIER
    load_external_css()
    
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
             Coach Fitness IA • Édition Multi-Modèles + YouTube
        </h3>
        <p style="font-size: 1rem; margin: 0.5rem 0; color: #00999C;">
            🇫🇷 DistilGPT-2 Fine-Tuné + 🇺🇸 PlayPart AI Personal Trainer + RAG + 📺 YouTube • IA Bienveillante
        </p>
        <p style="font-size: 0.9rem; opacity: 0.8; color: ##006669;">
            By Maxime & Léo © 
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()