# api/models.py - Modèles Pydantic avec support multi-modèles

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# === ÉNUMÉRATIONS ===

class ModelType(str, Enum):
    """Types de modèles disponibles"""
    LOCAL_DISTILGPT2 = "local_distilgpt2"
    PLAYPART_TRAINER = "playpart_trainer"

# === MODÈLES DE REQUÊTE ===

class UserProfile(BaseModel):
    """Profil utilisateur simplifié"""
    age: Optional[int] = Field(None, ge=15, le=100)
    gender: Optional[str] = Field(None)
    fitness_level: Optional[str] = Field("débutant")
    goal: Optional[str] = Field(None)
    available_time: Optional[int] = Field(None, ge=10, le=240)
    equipment: Optional[List[str]] = Field(default_factory=list)

class ChatRequest(BaseModel):
    """Requête de chat avec sélection de modèle"""
    message: str = Field(..., min_length=1, max_length=500)
    profile: Optional[UserProfile] = Field(None)
    model_type: Optional[ModelType] = Field(None, description="Modèle à utiliser (optionnel)")

class FitnessRequest(BaseModel):
    """Requête fitness détaillée avec sélection de modèle"""
    question: str = Field(..., min_length=1, max_length=500)
    profile: Optional[UserProfile] = Field(None)
    context: Optional[str] = Field(None)
    model_type: Optional[ModelType] = Field(None, description="Modèle à utiliser (optionnel)")

class ModelSwitchRequest(BaseModel):
    """Requête de changement de modèle"""
    model_type: ModelType = Field(..., description="Modèle à activer")

# === MODÈLES DE RÉPONSE ===

class FitnessResponse(BaseModel):
    """Réponse du coach fitness"""
    response: str = Field(...)
    sources: List[str] = Field(default_factory=list)
    context_used: bool = Field(False)
    model_used: str = Field(...)
    model_name: str = Field(...)
    response_time: float = Field(...)
    confidence: str = Field(...)
    rag_enabled: bool = Field(False)

class ModelInfo(BaseModel):
    """Informations sur un modèle"""
    name: str = Field(...)
    description: str = Field(...)
    path: str = Field(...)
    is_local: bool = Field(...)
    loaded: bool = Field(...)

class AvailableModelsResponse(BaseModel):
    """Réponse avec modèles disponibles"""
    models: Dict[str, ModelInfo] = Field(...)
    current_model: ModelType = Field(...)
    device: str = Field(...)

class ModelSwitchResponse(BaseModel):
    """Réponse de changement de modèle"""
    success: bool = Field(...)
    message: str = Field(...)
    old_model: Optional[ModelType] = Field(None)
    current_model: ModelType = Field(...)
    model_info: Optional[ModelInfo] = Field(None)

class HealthResponse(BaseModel):
    """Réponse health check"""
    status: str = Field(...)
    models: Dict[str, ModelInfo] = Field(...)
    current_model: ModelType = Field(...)
    rag_enabled: bool = Field(False)
    device: str = Field(...)
    exercise_database_size: int = Field(...)
    total_requests: int = Field(0)
    successful_requests: int = Field(0)
    average_response_time: float = Field(0.0)
    timestamp: str = Field(...)

class ExerciseSearchRequest(BaseModel):
    """Recherche d'exercices"""
    query: str = Field(..., min_length=2)
    muscle_groups: Optional[List[str]] = Field(default_factory=list)
    difficulty: Optional[str] = Field(None)
    max_results: Optional[int] = Field(5, ge=1, le=20)

class ExerciseSearchResponse(BaseModel):
    """Résultats de recherche"""
    exercises: List[Dict[str, Any]] = Field(default_factory=list)
    total_found: int = Field(...)
    query_time: float = Field(...)

class CategoriesResponse(BaseModel):
    """Catégories disponibles"""
    muscle_groups: List[str] = Field(default_factory=list)
    difficulties: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    total_exercises: int = Field(...)

class StatsResponse(BaseModel):
    """Statistiques du service"""
    models: Dict[str, ModelInfo] = Field(...)
    current_model: ModelType = Field(...)
    rag_enabled: bool = Field(...)
    device: str = Field(...)
    initialization_time: Optional[float] = Field(None)
    total_requests: int = Field(...)
    successful_requests: int = Field(...)
    fallback_requests: int = Field(...)
    average_response_time: float = Field(...)
    model_usage: Dict[str, int] = Field(default_factory=dict)
    exercise_database_size: int = Field(...)
    last_request_time: Optional[str] = Field(None)
    timestamp: str = Field(...)

class FeedbackRequest(BaseModel):
    """Feedback utilisateur"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    question: Optional[str] = Field(None)
    response_helpful: Optional[bool] = Field(None)
    model_used: Optional[str] = Field(None)