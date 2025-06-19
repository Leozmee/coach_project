import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger explicitement le .env
load_dotenv()

class LlamaService:
    def __init__(self):
        print("🔧 Initialisation LlamaService avec token HF...")
        
        # Récupérer le token
        token = os.environ.get("HF_TOKEN")
        if token:
            print(f"✅ Token trouvé: {token[:10]}...")
        else:
            print("❌ Token HF non trouvé!")
            raise ValueError("Token Hugging Face non trouvé")
        
        try:
            self.client = InferenceClient(
                model="meta-llama/Llama-3.2-3B-Instruct",
                token=token,
            )
            print("✅ Client InferenceClient créé")
        except Exception as e:
            print(f"❌ Erreur création client: {e}")
            raise
    
    def get_response(self, user_message, context_docs="", few_shot_examples=""):
        try:
            # Préparer les messages pour le mode conversational
            messages = []
            
            # Message système avec le contexte
            system_message = f"""Tu es un coach sportif professionnel. Réponds en français de manière concise et pratique.

Utilise ces informations pour répondre à la question :
{context_docs}

Donne des conseils précis et pratiques."""

            messages.append({
                "role": "system", 
                "content": system_message
            })
            
            # Message utilisateur
            messages.append({
                "role": "user", 
                "content": user_message
            })

            print("🚀 Envoi requête à Llama en mode conversational...")
            
            # Utiliser chat_completion au lieu de text_generation
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.7,
            )
            
            # Extraire le contenu de la réponse
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                return "Aucune réponse générée"
                
        except Exception as e:
            logger.error(f"Erreur détaillée: {e}")
            
            # Si l'erreur indique un problème de modèle, essayer un autre modèle
            if "not supported" in str(e).lower():
                return self._try_alternative_model(user_message, context_docs)
            else:
                return f"Erreur : {str(e)}"
    
    def _try_alternative_model(self, user_message, context_docs):
        """Essaie un modèle alternatif si le premier ne fonctionne pas"""
        try:
            print("🔄 Tentative avec un modèle alternatif...")
            
            # Essayer avec un modèle qui supporte text_generation
            alt_client = InferenceClient(
                model="microsoft/DialoGPT-medium",
                token=os.environ.get("HF_TOKEN"),
            )
            
            prompt = f"""Coach sportif: {context_docs}

Question: {user_message}
Réponse:"""

            response = alt_client.text_generation(
                prompt=prompt,
                max_new_tokens=200,
                temperature=0.7,
                return_full_text=False
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur avec modèle alternatif: {e}")
            return f"""❌ Erreur technique avec l'IA

Mais voici une réponse basée sur le contexte trouvé :

{context_docs}

Pour une réponse plus personnalisée, essayez de vous connecter avec huggingface-cli login ou vérifiez votre configuration."""