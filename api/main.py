from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime

# Création de l'application FastAPI
app = FastAPI(
    title="🏋️ Coach Fitness IA API",
    description="API pour coach fitness intelligent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "🏋️ API Coach Fitness IA",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check simple"""
    return {
        "status": "healthy",
        "message": "API fonctionnelle",
        "model_loaded": False,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat_simple(request: dict):
    """Chat simple pour tester"""
    message = request.get("message", "")
    
    return {
        "response": f"🏋️ Test réussi ! Vous avez dit: '{message}'. L'intégration du modèle DistilGPT-2 arrive bientôt !",
        "sources": ["API Test"],
        "model_used": "test_mode",
        "response_time": 0.1
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)