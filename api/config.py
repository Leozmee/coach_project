# api/config.py - Version simple sans pydantic_settings

import os
from pathlib import Path
from functools import lru_cache

class Settings:
    """Configuration simple de l'API Fitness Coach"""
    
    def __init__(self):
        # API
        self.api_host = os.getenv("API_HOST", "127.0.0.1")
        self.api_port = int(os.getenv("API_PORT", "8001"))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Modèle - Chemin vers votre modèle DistilGPT-2
        self.model_path = os.getenv("MODEL_PATH", "./models/coach-sportif-french")
        self.model_device = os.getenv("MODEL_DEVICE", "auto")
        
        # RAG
        self.enable_rag = os.getenv("ENABLE_RAG", "true").lower() == "true"
        self.rag_top_k = int(os.getenv("RAG_TOP_K", "3"))
        
        # Génération
        self.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "150"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("TOP_P", "0.9"))
        
        # Logs
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

@lru_cache()
def get_settings() -> Settings:
    """Récupère la configuration avec cache"""
    return Settings()

# Pour compatibilité
def get_config():
    """Alias pour get_settings"""
    return get_settings()