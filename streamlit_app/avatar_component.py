# streamlit_app/avatar_component.py
import streamlit as st
import base64
from pathlib import Path
from typing import Literal, Optional
import os

def load_svg_as_base64(svg_path: str) -> Optional[str]:
    """Charge un fichier SVG et le convertit en base64 pour l'affichage"""
    try:
        if os.path.exists(svg_path):
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Encoder en base64
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            return svg_base64
        else:
            st.warning(f"⚠️ Fichier SVG non trouvé: {svg_path}")
            return None
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du SVG: {e}")
        return None

def display_zen_avatar(
    mood: Literal["zen", "peaceful", "thinking", "happy"] = "zen",
    size: int = 80,
    position: Literal["left", "center", "right"] = "center",
    custom_style: str = ""
) -> None:
    """
    Affiche l'avatar SVG avec différentes humeurs et styles
    
    Args:
        mood: L'humeur de l'avatar (zen, peaceful, thinking, happy)
        size: Taille de l'avatar en pixels
        position: Position de l'avatar (left, center, right)
        custom_style: Styles CSS personnalisés
    """
    
    # Chemin vers le fichier SVG
    current_dir = Path(__file__).parent
    svg_path = current_dir / "assets" / "avatar.svg"
    
    # Charger le SVG en base64
    svg_base64 = load_svg_as_base64(str(svg_path))
    
    if not svg_base64:
        # Avatar de fallback en emoji si le SVG n'est pas trouvé
        fallback_avatars = {
            "zen": "🧘",
            "peaceful": "😌",
            "thinking": "🤔",
            "happy": "😊"
        }
        
        avatar_emoji = fallback_avatars.get(mood, "🧘")
        
        st.markdown(f"""
        <div style="
            text-align: {position};
            font-size: {size * 0.8}px;
            margin: 10px 0;
            {custom_style}
        ">
            {avatar_emoji}
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Styles CSS pour les différentes humeurs
    mood_styles = {
        "zen": {
            "filter": "hue-rotate(0deg) brightness(1) saturate(1)",
            "animation": "gentle-float 4s ease-in-out infinite"
        },
        "peaceful": {
            "filter": "hue-rotate(30deg) brightness(1.1) saturate(0.8)",
            "animation": "peaceful-glow 3s ease-in-out infinite"
        },
        "thinking": {
            "filter": "hue-rotate(-30deg) brightness(0.9) saturate(1.2)",
            "animation": "thinking-pulse 2s ease-in-out infinite"
        },
        "happy": {
            "filter": "hue-rotate(60deg) brightness(1.2) saturate(1.3)",
            "animation": "happy-bounce 1.5s ease-in-out infinite"
        }
    }
    
    current_mood = mood_styles.get(mood, mood_styles["zen"])
    
    # Position styles
    position_styles = {
        "left": "text-align: left; margin-right: auto;",
        "center": "text-align: center; margin: 0 auto;",
        "right": "text-align: right; margin-left: auto;"
    }
    
    position_style = position_styles.get(position, position_styles["center"])
    
    # Générer le HTML avec le SVG
    st.markdown(f"""
    <style>
    @keyframes gentle-float {{
        0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
        50% {{ transform: translateY(-10px) rotate(2deg); }}
    }}
    
    @keyframes peaceful-glow {{
        0%, 100% {{ 
            filter: hue-rotate(30deg) brightness(1.1) saturate(0.8) drop-shadow(0 0 10px rgba(147, 112, 219, 0.3));
        }}
        50% {{ 
            filter: hue-rotate(30deg) brightness(1.2) saturate(0.9) drop-shadow(0 0 20px rgba(147, 112, 219, 0.5));
        }}
    }}
    
    @keyframes thinking-pulse {{
        0%, 100% {{ 
            transform: scale(1);
            filter: hue-rotate(-30deg) brightness(0.9) saturate(1.2);
        }}
        50% {{ 
            transform: scale(1.05);
            filter: hue-rotate(-30deg) brightness(1) saturate(1.3);
        }}
    }}
    
    @keyframes happy-bounce {{
        0%, 100% {{ 
            transform: translateY(0px) scale(1);
            filter: hue-rotate(60deg) brightness(1.2) saturate(1.3);
        }}
        50% {{ 
            transform: translateY(-8px) scale(1.1);
            filter: hue-rotate(60deg) brightness(1.3) saturate(1.4);
        }}
    }}
    
    .zen-avatar-container {{
        {position_style}
        display: inline-block;
        margin: 10px;
        transition: all 0.3s ease;
    }}
    
    .zen-avatar-container:hover {{
        transform: scale(1.1);
        filter: drop-shadow(0 0 15px rgba(0, 206, 209, 0.4));
    }}
    
    .zen-avatar {{
        width: {size}px;
        height: {size}px;
        {current_mood["filter"]};
        animation: {current_mood["animation"]};
        border-radius: 50%;
        padding: 5px;
        background: linear-gradient(135deg, rgba(147,112,219,0.1), rgba(0,206,209,0.1));
        {custom_style}
    }}
    </style>
    
    <div class="zen-avatar-container">
        <img class="zen-avatar" src="data:image/svg+xml;base64,{svg_base64}" alt="Avatar Zen {mood}" />
    </div>
    """, unsafe_allow_html=True)

def display_animated_avatar_sequence(avatars_config: list, duration: float = 3.0):
    """
    Affiche une séquence d'avatars animés
    
    Args:
        avatars_config: Liste de configurations d'avatars [{"mood": "zen", "size": 80}, ...]
        duration: Durée entre chaque changement d'avatar
    """
    
    if not avatars_config:
        return
    
    # Utiliser session state pour gérer l'index de l'avatar actuel
    if "avatar_index" not in st.session_state:
        st.session_state.avatar_index = 0
    
    current_config = avatars_config[st.session_state.avatar_index]
    
    # Afficher l'avatar actuel
    display_zen_avatar(
        mood=current_config.get("mood", "zen"),
        size=current_config.get("size", 80),
        position=current_config.get("position", "center")
    )
    
    # Auto-refresh pour changer d'avatar
    import time
    time.sleep(duration)
    st.session_state.avatar_index = (st.session_state.avatar_index + 1) % len(avatars_config)
    st.rerun()

# Fonction helper pour créer des avatars contextuels
def get_contextual_avatar(message_content: str) -> dict:
    """
    Retourne la configuration d'avatar basée sur le contenu du message
    
    Args:
        message_content: Le contenu du message à analyser
        
    Returns:
        Dict avec la configuration de l'avatar approprié
    """
    
    message_lower = message_content.lower()
    
    # Mapping des mots-clés vers les humeurs
    keyword_mapping = {
        "zen": ["relaxation", "méditation", "calme", "sérénité", "paix"],
        "thinking": ["question", "comment", "pourquoi", "expliquer", "comprendre"],
        "happy": ["bravo", "excellent", "super", "génial", "parfait", "réussi"],
        "peaceful": ["bien-être", "douceur", "tranquille", "repos", "sommeil"]
    }
    
    # Analyser le contenu pour déterminer l'humeur
    for mood, keywords in keyword_mapping.items():
        if any(keyword in message_lower for keyword in keywords):
            return {"mood": mood, "size": 80, "position": "center"}
    
    # Humeur par défaut
    return {"mood": "zen", "size": 80, "position": "center"}

# Exemple d'utilisation pour tester le composant
if __name__ == "__main__":
    st.set_page_config(page_title="Test Avatar Component", layout="wide")
    
    st.title("🧘 Test du Composant Avatar")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Zen")
        display_zen_avatar("zen", 100)
    
    with col2:
        st.subheader("Peaceful")
        display_zen_avatar("peaceful", 100)
    
    with col3:
        st.subheader("Thinking")
        display_zen_avatar("thinking", 100)
    
    with col4:
        st.subheader("Happy")
        display_zen_avatar("happy", 100)
    
    st.markdown("---")
    
    # Test avec différentes tailles
    st.subheader("Différentes tailles")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_zen_avatar("zen", 60, "center")
    with col2:
        display_zen_avatar("zen", 80, "center")
    with col3:
        display_zen_avatar("zen", 120, "center")