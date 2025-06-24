# streamlit_app/components/avatar_component.py - Intégration de ton avatar SVG

import streamlit as st
from pathlib import Path
import base64

class ChatbotAvatar:
    """Composant pour gérer l'avatar SVG du chatbot"""
    
    def __init__(self, svg_path: str = "streamlit_app/assets/chatbot.svg"):
        self.svg_path = Path(svg_path)
        self.current_mood = "neutral"
    
    def load_svg(self) -> str:
        """Charge le fichier SVG et retourne son contenu"""
        try:
            if self.svg_path.exists():
                with open(self.svg_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return self._get_fallback_svg()
        except Exception as e:
            st.error(f"Erreur chargement avatar: {e}")
            return self._get_fallback_svg()
    
    def _get_fallback_svg(self) -> str:
        """Avatar de secours si fichier non trouvé"""
        return """
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="80" fill="#667eea"/>
            <circle cx="85" cy="85" r="8" fill="white"/>
            <circle cx="115" cy="85" r="8" fill="white"/>
            <path d="M 75 125 Q 100 140 125 125" stroke="white" stroke-width="3" fill="none"/>
            <text x="100" y="180" text-anchor="middle" fill="#667eea" font-size="12">Coach IA</text>
        </svg>
        """
    
    def modify_svg_mood(self, svg_content: str, mood: str = "neutral") -> str:
        """Modifie l'avatar selon l'humeur/contexte"""
        
        # Définir les transformations selon le mood
        mood_modifications = {
            "thinking": {
                "animation": "transform: scale(1.05); transition: all 0.3s ease;",
                "filter": "filter: brightness(1.1);",
                "extra": """
                    <style>
                        .thinking { animation: pulse 2s infinite; }
                        @keyframes pulse {
                            0% { opacity: 1; }
                            50% { opacity: 0.7; }
                            100% { opacity: 1; }
                        }
                    </style>
                """
            },
            "happy": {
                "animation": "transform: scale(1.1) rotate(2deg); transition: all 0.5s ease;",
                "filter": "filter: brightness(1.2) saturate(1.3);",
                "extra": ""
            },
            "motivated": {
                "animation": "transform: scale(1.15); transition: all 0.3s ease;",
                "filter": "filter: contrast(1.2) saturate(1.2);",
                "extra": """
                    <style>
                        .motivated { animation: bounce 1s infinite; }
                        @keyframes bounce {
                            0%, 100% { transform: translateY(0); }
                            50% { transform: translateY(-10px); }
                        }
                    </style>
                """
            },
            "neutral": {
                "animation": "transition: all 0.3s ease;",
                "filter": "",
                "extra": ""
            }
        }
        
        modifications = mood_modifications.get(mood, mood_modifications["neutral"])
        
        # Injecter les styles dans le SVG
        if "<svg" in svg_content:
            # Ajouter classe CSS selon le mood
            svg_content = svg_content.replace(
                "<svg", 
                f'<svg class="{mood}" style="{modifications["animation"]} {modifications["filter"]}"'
            )
            
            # Ajouter animations CSS si nécessaire
            if modifications["extra"]:
                svg_content = modifications["extra"] + svg_content
        
        return svg_content
    
    def display_avatar(self, 
                      mood: str = "neutral", 
                      size: int = 200, 
                      container_style: str = ""):
        """Affiche l'avatar avec animations et mood"""
        
        svg_content = self.load_svg()
        modified_svg = self.modify_svg_mood(svg_content, mood)
        
        # Container avec style personnalisé
        avatar_html = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
            {container_style}
        ">
            <div style="
                width: {size}px;
                height: {size}px;
                display: flex;
                justify-content: center;
                align-items: center;
            ">
                {modified_svg}
            </div>
        </div>
        """
        
        st.markdown(avatar_html, unsafe_allow_html=True)
        self.current_mood = mood
    
    def get_mood_from_context(self, message_type: str = "response") -> str:
        """Détermine le mood selon le contexte"""
        
        mood_mapping = {
            "user_typing": "thinking",
            "generating": "thinking", 
            "success": "happy",
            "motivation": "motivated",
            "exercise": "motivated",
            "nutrition": "happy",
            "recovery": "neutral",
            "error": "neutral",
            "default": "neutral"
        }
        
        return mood_mapping.get(message_type, "neutral")

# Fonction utilitaire pour l'intégration facile
def display_coach_avatar(mood: str = "neutral", size: int = 200, key: str = None):
    """
    Fonction simple pour afficher l'avatar n'importe où dans l'app
    
    Args:
        mood: État de l'avatar (thinking, happy, motivated, neutral)
        size: Taille en pixels
        key: Clé unique si utilisé plusieurs fois
    """
    
    if f"avatar_{key}" not in st.session_state:
        st.session_state[f"avatar_{key}"] = ChatbotAvatar()
    
    avatar = st.session_state[f"avatar_{key}"]
    avatar.display_avatar(mood=mood, size=size)
    
    return avatar

# Styles CSS additionnels pour les animations
def load_avatar_styles():
    """Charge les styles CSS pour les animations d'avatar"""
    st.markdown("""
    <style>
    /* Animations pour l'avatar */
    .avatar-container {
        transition: all 0.3s ease;
    }
    
    .avatar-container:hover {
        transform: scale(1.05);
    }
    
    /* Animation de réflexion */
    .thinking-animation {
        animation: thinking-pulse 2s infinite ease-in-out;
    }
    
    @keyframes thinking-pulse {
        0%, 100% { 
            opacity: 1;
            transform: scale(1);
        }
        50% { 
            opacity: 0.8;
            transform: scale(1.02);
        }
    }
    
    /* Animation de motivation */
    .motivation-animation {
        animation: motivation-bounce 1s infinite ease-in-out;
    }
    
    @keyframes motivation-bounce {
        0%, 100% { 
            transform: translateY(0) scale(1);
        }
        50% { 
            transform: translateY(-5px) scale(1.05);
        }
    }
    
    /* Animation de bonheur */
    .happy-animation {
        animation: happy-wiggle 0.8s ease-in-out;
    }
    
    @keyframes happy-wiggle {
        0%, 100% { transform: rotate(0deg) scale(1); }
        25% { transform: rotate(2deg) scale(1.05); }
        75% { transform: rotate(-2deg) scale(1.05); }
    }
    </style>
    """, unsafe_allow_html=True)