# api/models.py - Modèles Pydantic corrigés

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# === MODÈLES DE REQUÊTE ===

class UserProfile(BaseModel):
    """Profil utilisateur simplifié"""
    age: Optional[int] = Field(None, ge=15, le=100)
    gender: Optional[str] = Field(None)
    fitness_level: Optional[str] = Field("débutant")
    goal: Optional[str] = Field(None)
    available_time: Optional[int] = Field(None, ge=10, le=240)
    equipment: Optional[List[str]] = Field(default_factory=list)  # CORRIGÉ

class ChatRequest(BaseModel):
    """Requête de chat"""
    message: str = Field(..., min_length=1, max_length=500)
    profile: Optional[UserProfile] = Field(None)

class FitnessRequest(BaseModel):
    """Requête fitness détaillée"""
    question: str = Field(..., min_length=1, max_length=500)
    profile: Optional[UserProfile] = Field(None)
    context: Optional[str] = Field(None)

# === MODÈLES DE RÉPONSE ===

class FitnessResponse(BaseModel):
    """Réponse du coach fitness"""
    response: str = Field(...)
    sources: List[str] = Field(default_factory=list)  # CORRIGÉ
    context_used: bool = Field(False)
    model_used: str = Field(...)
    response_time: float = Field(...)
    confidence: str = Field(...)
    rag_enabled: bool = Field(False)

class HealthResponse(BaseModel):
    """Réponse health check"""
    status: str = Field(...)
    model_loaded: bool = Field(...)
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
    muscle_groups: Optional[List[str]] = Field(default_factory=list)  # CORRIGÉ
    difficulty: Optional[str] = Field(None)
    max_results: Optional[int] = Field(5, ge=1, le=20)

class ExerciseSearchResponse(BaseModel):
    """Résultats de recherche"""
    exercises: List[Dict[str, Any]] = Field(default_factory=list)  # CORRIGÉ
    total_found: int = Field(...)
    query_time: float = Field(...)

class CategoriesResponse(BaseModel):
    """Catégories disponibles"""
    muscle_groups: List[str] = Field(default_factory=list)  # CORRIGÉ
    difficulties: List[str] = Field(default_factory=list)  # CORRIGÉ
    equipment: List[str] = Field(default_factory=list)  # CORRIGÉ
    categories: List[str] = Field(default_factory=list)  # CORRIGÉ
    total_exercises: int = Field(...)

class StatsResponse(BaseModel):
    """Statistiques du service"""
    model_loaded: bool = Field(...)
    rag_enabled: bool = Field(...)
    device: str = Field(...)
    initialization_time: Optional[float] = Field(None)
    total_requests: int = Field(...)
    successful_requests: int = Field(...)
    fallback_requests: int = Field(...)
    average_response_time: float = Field(...)
    exercise_database_size: int = Field(...)
    last_request_time: Optional[str] = Field(None)
    timestamp: str = Field(...)

class FeedbackRequest(BaseModel):
    """Feedback utilisateur"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    question: Optional[str] = Field(None)
    response_helpful: Optional[bool] = Field(None)