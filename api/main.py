# api/main.py - Version complète avec votre modèle DistilGPT-2

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import des modèles et services
from .models import (
    ChatRequest, FitnessRequest, FitnessResponse, HealthResponse,
    ExerciseSearchRequest, ExerciseSearchResponse, CategoriesResponse,
    StatsResponse, FeedbackRequest
)
from .config import get_settings
from .fitness_service import get_fitness_service

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instance globale du service
fitness_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    global fitness_service
    logger.info("🚀 Démarrage API Coach Fitness avec DistilGPT-2...")
    
    try:
        settings = get_settings()
        fitness_service = get_fitness_service(settings.model_path)
        logger.info("✅ Service fitness avec modèle DistilGPT-2 initialisé")
        yield
    except Exception as e:
        logger.error(f"❌ Erreur initialisation: {e}")
        yield
    finally:
        # Shutdown
        logger.info("🛑 Arrêt API Coach Fitness")

# Création de l'application FastAPI
app = FastAPI(
    title="🏋️ Coach Fitness IA API",
    description="API intelligente pour coaching fitness basée sur DistilGPT-2 fine-tuné + RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuration CORS pour Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ENDPOINTS PRINCIPAUX ===

@app.get("/", summary="Page d'accueil")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "🏋️ API Coach Fitness IA",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "model": "DistilGPT-2 fine-tuné",
        "streamlit_compatible": True
    }

@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Vérification de l'état du service"""
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non initialisé")
        
        stats = fitness_service.get_service_stats()
        
        return HealthResponse(
            status=stats['status'],
            model_loaded=stats['model_loaded'],
            rag_enabled=stats['rag_enabled'],
            device=stats['device'],
            exercise_database_size=stats['exercise_database_size'],
            total_requests=stats['stats']['total_requests'],
            successful_requests=stats['stats']['successful_requests'],
            average_response_time=stats['stats']['average_response_time'],
            timestamp=stats['timestamp']
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/advice", response_model=FitnessResponse, summary="Conseil fitness personnalisé")
async def get_fitness_advice(request: FitnessRequest):
    """
    Génère un conseil fitness personnalisé avec votre modèle DistilGPT-2
    """
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non disponible")
        
        logger.info(f"📝 Question reçue: {request.question[:50]}...")
        
        # Convertir le profil
        profile_dict = request.profile.dict() if request.profile else None
        
        # Générer la réponse avec votre modèle DistilGPT-2
        result = fitness_service.generate_advice(
            question=request.question,
            user_profile=profile_dict
        )
        
        logger.info(f"✅ Réponse DistilGPT-2 générée en {result['response_time']:.2f}s")
        
        return FitnessResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur génération conseil: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/chat", response_model=FitnessResponse, summary="Chat avec DistilGPT-2")
async def chat_endpoint(request: ChatRequest):
    """
    Chat simple utilisant votre modèle DistilGPT-2 fine-tuné
    """
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non disponible")
        
        logger.info(f"💬 Chat: {request.message[:50]}...")
        
        # Convertir vers format standard
        profile_dict = request.profile.dict() if request.profile else None
        
        # Générer réponse avec votre modèle DistilGPT-2
        result = fitness_service.generate_advice(
            question=request.message,
            user_profile=profile_dict
        )
        
        return FitnessResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur chat: {e}")
        raise HTTPException(status_code=500, detail="Erreur chat")

@app.post("/exercises/search", response_model=ExerciseSearchResponse, summary="Recherche d'exercices")
async def search_exercises(request: ExerciseSearchRequest):
    """
    Recherche d'exercices dans la base de données avec filtres
    """
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non disponible")
        
        start_time = datetime.now()
        
        # Recherche sémantique via RAG
        relevant_docs = fitness_service.search_relevant_context(
            request.query, 
            top_k=request.max_results
        )
        
        # Application des filtres
        filtered_exercises = []
        for doc in relevant_docs:
            # Filtre difficulté
            if request.difficulty and doc.get('difficulty') != request.difficulty:
                continue
                
            # Filtre groupes musculaires
            if request.muscle_groups:
                doc_muscles = doc.get('muscle_groups', [])
                if not any(muscle in doc_muscles for muscle in request.muscle_groups):
                    continue
            
            filtered_exercises.append(doc)
        
        query_time = (datetime.now() - start_time).total_seconds()
        
        return ExerciseSearchResponse(
            exercises=filtered_exercises,
            total_found=len(filtered_exercises),
            query_time=query_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur recherche exercices: {e}")
        raise HTTPException(status_code=500, detail="Erreur recherche exercices")

@app.get("/exercises/categories", response_model=CategoriesResponse, summary="Catégories disponibles")
async def get_exercise_categories():
    """Retourne les catégories et filtres disponibles"""
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non disponible")
        
        # Analyser la base d'exercices
        all_muscle_groups = set()
        all_difficulties = set()
        all_equipment = set()
        all_categories = set()
        
        for exercise in fitness_service.exercise_database:
            if 'muscle_groups' in exercise:
                all_muscle_groups.update(exercise['muscle_groups'])
            if 'difficulty' in exercise:
                all_difficulties.add(exercise['difficulty'])
            if 'equipment' in exercise:
                all_equipment.add(exercise['equipment'])
            if 'category' in exercise:
                all_categories.add(exercise['category'])
        
        return CategoriesResponse(
            muscle_groups=sorted(list(all_muscle_groups)),
            difficulties=sorted(list(all_difficulties)),
            equipment=sorted(list(all_equipment)),
            categories=sorted(list(all_categories)),
            total_exercises=len(fitness_service.exercise_database)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur catégories: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération catégories")

@app.get("/stats", response_model=StatsResponse, summary="Statistiques du service")
async def get_service_stats():
    """Statistiques détaillées du service DistilGPT-2"""
    try:
        if fitness_service is None:
            raise HTTPException(status_code=503, detail="Service non disponible")
        
        stats = fitness_service.get_service_stats()
        
        return StatsResponse(
            model_loaded=stats['model_loaded'],
            rag_enabled=stats['rag_enabled'],
            device=stats['device'],
            initialization_time=stats['initialization_time'],
            total_requests=stats['stats']['total_requests'],
            successful_requests=stats['stats']['successful_requests'],
            fallback_requests=stats['stats']['fallback_requests'],
            average_response_time=stats['stats']['average_response_time'],
            exercise_database_size=stats['exercise_database_size'],
            last_request_time=stats['stats']['last_request_time'].isoformat() if stats['stats']['last_request_time'] else None,
            timestamp=stats['timestamp']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur statistiques")

@app.get("/test", summary="Test du modèle DistilGPT-2")
async def test_service():
    """Test rapide pour vérifier votre modèle DistilGPT-2"""
    try:
        if fitness_service is None:
            return {"status": "error", "message": "Service non initialisé"}
        
        # Test avec votre modèle
        test_question = "Comment faire des pompes correctement ?"
        result = fitness_service.generate_advice(test_question)
        
        return {
            "status": "success",
            "test_question": test_question,
            "response_preview": result['response'][:100] + "...",
            "model_used": result['model_used'],
            "response_time": result['response_time'],
            "rag_enabled": result['rag_enabled'],
            "model_loaded": fitness_service.model_loaded
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/feedback", summary="Feedback utilisateur")
async def submit_feedback(feedback: FeedbackRequest):
    """Collecte du feedback utilisateur"""
    try:
        logger.info(f"📝 Feedback reçu: {feedback.rating}/5 - {feedback.comment[:50] if feedback.comment else 'Pas de commentaire'}...")
        
        return {
            "message": "Merci pour votre feedback !",
            "feedback_id": f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "received"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur feedback: {e}")
        raise HTTPException(status_code=500, detail="Erreur enregistrement feedback")

# === GESTION D'ERREURS ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Gestionnaire d'erreurs HTTP personnalisé"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Gestionnaire d'erreurs générales"""
    logger.error(f"❌ Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# === MIDDLEWARE PERSONNALISÉS ===

@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware pour logger les requêtes"""
    start_time = datetime.now()
    
    # Traiter la requête
    response = await call_next(request)
    
    # Log des métriques
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"🌐 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# === LANCEMENT DE L'API ===

def main():
    """Point d'entrée principal pour lancement direct"""
    settings = get_settings()
    
    logger.info(f"🚀 Lancement API Fitness Coach avec DistilGPT-2")
    logger.info(f"📡 Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"🤖 Modèle: {settings.model_path}")
    logger.info(f"🔧 Device: auto-détection")
    
    # Configuration Uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug
    )

if __name__ == "__main__":
    main()