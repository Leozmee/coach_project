# api/fitness_service.py - Version complète corrigée

import os
import logging
import torch
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pathlib import Path
from enum import Enum
import re

# Imports IA
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    GPT2Tokenizer, GPT2LMHeadModel
)
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Types de modèles disponibles"""
    LOCAL_DISTILGPT2 = "local_distilgpt2"
    PLAYPART_TRAINER = "playpart_trainer"

class FitnessCoachService:
    """Service principal avec support multi-modèles"""
    
    def __init__(self, local_model_path: str = "./models/coach-sportif-french"):
        self.local_model_path = Path(local_model_path)
        self.device = self._get_device()
        
        # État global
        self.initialization_time = None
        self.initialization_error = None
        
        # Modèles disponibles
        self.models = {}
        self.tokenizers = {}
        self.model_configs = {
            ModelType.LOCAL_DISTILGPT2: {
                "name": "DistilGPT-2 Fine-tuné Local",
                "description": "Votre modèle DistilGPT-2 fine-tuné français",
                "path": str(self.local_model_path),
                "is_local": True,
                "loaded": False
            },
            ModelType.PLAYPART_TRAINER: {
                "name": "PlayPart AI Personal Trainer",
                "description": "Modèle GPT-2 spécialisé fitness de HuggingFace",
                "path": "Lukamac/PlayPart-AI-Personal-Trainer",
                "is_local": False,
                "loaded": False
            }
        }
        
        # Modèle actuel
        self.current_model = ModelType.LOCAL_DISTILGPT2
        
        # Composants RAG
        self.embedding_model = None
        self.faiss_index = None
        self.rag_enabled = False
        self.exercise_database = []
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'fallback_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': None,
            'model_usage': {model.value: 0 for model in ModelType}
        }
        
        # Configuration génération par modèle
        self.generation_configs = {
            ModelType.LOCAL_DISTILGPT2: {
                'max_new_tokens': 150,
                'temperature': 0.7,
                'do_sample': True,
                'top_p': 0.9,
                'top_k': 50,
                'repetition_penalty': 1.1,
                'no_repeat_ngram_size': 3
            },
            ModelType.PLAYPART_TRAINER: {
                'max_new_tokens': 60,
                'temperature': 0.5,
                'do_sample': True,
                'top_p': 0.7,
                'top_k': 25,
                'repetition_penalty': 1.4,
                'no_repeat_ngram_size': 2,
                'pad_token_id': 50256,
                'eos_token_id': 50256,
                'early_stopping': True,
                'length_penalty': 1.2
            }
        }
        
        # Initialiser
        self._load_exercise_database()
        self._initialize_service()
    
    def _get_device(self):
        """Détermine le device optimal"""
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"🚀 GPU détecté: {torch.cuda.get_device_name()}")
        else:
            device = torch.device("cpu")
            logger.info("💻 Utilisation CPU")
        return device
    
    def _initialize_service(self):
        """Initialise le service avec TOUS les modèles"""
        start_time = datetime.now()
        
        try:
            logger.info("🏋️ Initialisation Service Multi-Modèles...")
            
            # Charger RAG
            if RAG_AVAILABLE:
                logger.info("📊 Chargement du système RAG...")
                self._load_rag()
            
            # Charger tous les modèles disponibles
            logger.info("🤖 Chargement de tous les modèles...")
            
            # 1. Charger le modèle local (DistilGPT-2)
            self._load_model(ModelType.LOCAL_DISTILGPT2)
            
            # 2. Charger PlayPart AI (même si erreur, on continue)
            try:
                self._load_model(ModelType.PLAYPART_TRAINER)
            except Exception as e:
                logger.warning(f"⚠️ PlayPart AI non chargé: {e}")
            
            # Vérifier qu'au moins un modèle est chargé
            loaded_models = [name for name, config in self.model_configs.items() if config["loaded"]]
            
            if not loaded_models:
                raise Exception("Aucun modèle n'a pu être chargé")
            
            logger.info(f"✅ Modèles chargés: {[self.model_configs[m]['name'] for m in loaded_models]}")
            
            self.initialization_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Service multi-modèles initialisé en {self.initialization_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.initialization_error = error_msg
    
    def _load_model(self, model_type: ModelType) -> bool:
        """Charge un modèle spécifique avec gestion d'erreurs améliorée"""
        try:
            config = self.model_configs[model_type]
            logger.info(f"🤖 Chargement {config['name']}...")
            
            if model_type == ModelType.LOCAL_DISTILGPT2:
                success = self._load_local_distilgpt2()
            elif model_type == ModelType.PLAYPART_TRAINER:
                success = self._load_playpart_trainer()
            else:
                logger.error(f"❌ Type de modèle inconnu: {model_type}")
                return False
            
            if success:
                logger.info(f"✅ {config['name']} chargé avec succès")
            else:
                logger.error(f"❌ Échec du chargement de {config['name']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement {model_type}: {e}")
            self.model_configs[model_type]["loaded"] = False
            return False
    
    def _load_local_distilgpt2(self) -> bool:
        """Charge votre modèle DistilGPT-2 local"""
        try:
            if not self.local_model_path.exists():
                logger.warning(f"⚠️ Modèle local non trouvé: {self.local_model_path}")
                return False
            
            # Tokenizer
            tokenizer = AutoTokenizer.from_pretrained(str(self.local_model_path))
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.pad_token_id = tokenizer.eos_token_id
            
            # Modèle
            model = AutoModelForCausalLM.from_pretrained(
                str(self.local_model_path),
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            )
            model.to(self.device)
            model.eval()
            
            # Sauvegarder
            self.models[ModelType.LOCAL_DISTILGPT2] = model
            self.tokenizers[ModelType.LOCAL_DISTILGPT2] = tokenizer
            self.model_configs[ModelType.LOCAL_DISTILGPT2]["loaded"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur DistilGPT-2 local: {e}")
            self.model_configs[ModelType.LOCAL_DISTILGPT2]["loaded"] = False
            return False
    
    def _load_playpart_trainer(self) -> bool:
        """Charge le modèle PlayPart AI Personal Trainer avec gestion d'erreurs renforcée"""
        try:
            logger.info("📥 Téléchargement PlayPart AI Personal Trainer...")
            
            # Test de connectivité d'abord
            import requests
            try:
                response = requests.get("https://huggingface.co", timeout=10)
                if response.status_code != 200:
                    logger.error("❌ Pas de connexion à HuggingFace")
                    return False
            except:
                logger.error("❌ Problème de connexion réseau")
                return False
            
            # Tokenizer GPT-2 standard
            tokenizer = GPT2Tokenizer.from_pretrained(
                "Lukamac/PlayPart-AI-Personal-Trainer",
                resume_download=True,
                force_download=False,
                local_files_only=False
            )
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
            
            # Modèle GPT-2 standard
            model = GPT2LMHeadModel.from_pretrained(
                "Lukamac/PlayPart-AI-Personal-Trainer",
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                pad_token_id=tokenizer.eos_token_id,
                resume_download=True,
                force_download=False,
                local_files_only=False
            )
            
            model.to(self.device)
            model.eval()
            
            # Sauvegarder
            self.models[ModelType.PLAYPART_TRAINER] = model
            self.tokenizers[ModelType.PLAYPART_TRAINER] = tokenizer
            self.model_configs[ModelType.PLAYPART_TRAINER]["loaded"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur PlayPart Trainer: {e}")
            self.model_configs[ModelType.PLAYPART_TRAINER]["loaded"] = False
            return False
    
    def switch_model(self, model_type: ModelType) -> Dict[str, Any]:
        """Change le modèle actuel"""
        try:
            logger.info(f"🔄 Changement vers {model_type}")
            
            # Vérifier si le modèle est déjà chargé
            if not self.model_configs[model_type]["loaded"]:
                logger.info(f"⏳ Modèle {model_type} non chargé, tentative de chargement...")
                success = self._load_model(model_type)
                if not success:
                    return {
                        "success": False,
                        "message": f"Impossible de charger {model_type}",
                        "current_model": self.current_model
                    }
            
            # Changer le modèle actuel
            old_model = self.current_model
            self.current_model = model_type
            
            config = self.model_configs[model_type]
            
            logger.info(f"✅ Modèle changé: {old_model} → {model_type}")
            
            return {
                "success": True,
                "message": f"Modèle changé vers {config['name']}",
                "old_model": old_model,
                "current_model": model_type,
                "model_info": config
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur changement modèle: {e}")
            return {
                "success": False,
                "message": str(e),
                "current_model": self.current_model
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Retourne la liste des modèles disponibles"""
        return {
            "models": self.model_configs,
            "current_model": self.current_model,
            "device": str(self.device)
        }
    
    def _load_rag(self):
        """Charge le système RAG (optionnel)"""
        try:
            logger.info("📊 Chargement RAG...")
            
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            self._build_faiss_index()
            
            self.rag_enabled = True
            logger.info("✅ RAG activé")
            
        except Exception as e:
            logger.error(f"⚠️ RAG non disponible: {e}")
            self.rag_enabled = False
    
    def _load_exercise_database(self):
        """Base d'exercices pour RAG - Adaptée pour les deux modèles"""
        self.exercise_database = [
            {
                "id": 1,
                "title": "Push-ups technique",
                "content": "Perfect push-ups require proper form: hands shoulder-width apart, body straight, controlled movement down and up. Start with 3 sets of 8-12 reps for beginners. Focus on quality over quantity.",
                "muscle_groups": ["chest", "triceps", "shoulders"],
                "difficulty": "beginner",
                "equipment": "none"
            },
            {
                "id": 2,
                "title": "Squat fundamentals", 
                "content": "Squats target quads and glutes effectively. Feet shoulder-width apart, sit back like sitting in chair, keep back straight. 3 sets of 12-20 reps. Great compound exercise.",
                "muscle_groups": ["quadriceps", "glutes", "calves"],
                "difficulty": "beginner",
                "equipment": "none"
            },
            {
                "id": 3,
                "title": "Upper body strength",
                "content": "Build upper body with compound movements: push-ups, pull-ups, dips. Progressive overload principle applies. Focus on form first, then increase intensity.",
                "muscle_groups": ["chest", "back", "arms", "shoulders"],
                "difficulty": "intermediate", 
                "equipment": "pull-up bar"
            },
            {
                "id": 4,
                "title": "Nutrition basics",
                "content": "Post-workout nutrition: consume 20-25g protein within 30 minutes. Stay hydrated with 2-3L daily. Balanced diet with complex carbohydrates and healthy fats.",
                "category": "nutrition",
                "importance": "high"
            },
            {
                "id": 5,
                "title": "Recovery essentials",
                "content": "Recovery is crucial for progress: 7-9 hours sleep nightly, post-workout stretching, active rest between intense sessions. Listen to your body signals.",
                "category": "recovery",
                "importance": "critical"
            }
        ]
    
    def _build_faiss_index(self):
        """Construit index FAISS pour recherche sémantique"""
        if not self.embedding_model:
            return
        
        try:
            texts = [f"{item['title']} {item['content']}" for item in self.exercise_database]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            faiss.normalize_L2(embeddings)
            self.faiss_index.add(embeddings.astype('float32'))
            
            logger.info(f"✅ Index FAISS: {self.faiss_index.ntotal} documents")
            
        except Exception as e:
            logger.error(f"❌ Erreur FAISS: {e}")
            self.faiss_index = None
    
    def search_relevant_context(self, query: str, top_k: int = 3) -> List[Dict]:
        """Recherche contexte via RAG"""
        if not self.rag_enabled or not self.faiss_index:
            return self.exercise_database[:top_k]
        
        try:
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
            faiss.normalize_L2(query_embedding)
            
            scores, indices = self.faiss_index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.exercise_database))
            )
            
            relevant_docs = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.exercise_database):
                    doc = self.exercise_database[idx].copy()
                    doc['relevance_score'] = float(scores[0][i])
                    relevant_docs.append(doc)
            
            return [doc for doc in relevant_docs if doc['relevance_score'] > 0.2]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return self.exercise_database[:top_k]
    
    def _create_prompt(self, question: str, context_docs: List[Dict], model_type: ModelType) -> str:
        """Crée prompt optimisé selon le modèle"""
        # Contexte RAG simplifié
        context_text = ""
        if context_docs:
            # Pour PlayPart, utiliser seulement le meilleur document et le raccourcir
            if model_type == ModelType.PLAYPART_TRAINER:
                best_doc = context_docs[0]
                context_text = f"{best_doc['title']}: {best_doc['content'][:60]}..."
            else:
                context_parts = []
                for doc in context_docs[:2]:
                    context_parts.append(f"- {doc['title']}: {doc['content'][:80]}...")
                context_text = "\n".join(context_parts)
        
        # Prompts spécifiques par modèle
        if model_type == ModelType.LOCAL_DISTILGPT2:
            # Format français pour votre modèle
            prompt = f"""[COACH] En tant que coach sportif français certifié, voici les informations pertinentes :

{context_text}

Question: {question}

Réponse: """
            
        elif model_type == ModelType.PLAYPART_TRAINER:
            # Format ultra-simple pour PlayPart
            if context_text:
                prompt = f"""{context_text}

{question}
Answer:"""
            else:
                prompt = f"""{question}
Answer:"""
        
        return prompt
    
    def _clean_playpart_response(self, text: str) -> str:
        """Nettoyage spécialisé pour PlayPart AI"""
        if not text:
            return ""
        
        # Supprimer caractères non-ASCII problématiques
        cleaned = ''.join(char for char in text if ord(char) < 128 or char.isspace())
        
        # Supprimer patterns suspects avec regex
        cleaned = re.sub(r'[^\w\s\.,!?()-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Supprimer répétitions de mots
        words = cleaned.split()
        result_words = []
        prev_word = ""
        
        for word in words:
            if word.lower() != prev_word.lower():
                result_words.append(word)
            prev_word = word
        
        cleaned = ' '.join(result_words)
        
        # Arrêter à la première phrase cohérente
        sentences = cleaned.split('.')
        if len(sentences) > 1 and len(sentences[0]) > 15:
            cleaned = sentences[0] + '.'
        
        return cleaned.strip()
    
    def _post_process_response(self, response: str, model_type: ModelType) -> str:
        """Post-traitement selon le modèle"""
        if not response:
            return "Sorry, I couldn't generate an appropriate response." if model_type == ModelType.PLAYPART_TRAINER else "Désolé, je n'ai pas pu générer une réponse appropriée."
        
        cleaned = response.strip()
        
        # Supprimer artefacts prompt
        artifacts = ["[COACH]", "Question:", "Réponse:", "Answer:", "Context:", "Q:", "A:"]
        for artifact in artifacts:
            if artifact in cleaned:
                parts = cleaned.split(artifact)
                if len(parts) > 1:
                    cleaned = parts[-1].strip()
        
        # Nettoyage spécialisé pour PlayPart
        if model_type == ModelType.PLAYPART_TRAINER:
            cleaned = self._clean_playpart_response(cleaned)
            
            # Vérification de cohérence
            if len(cleaned) < 10 or not any(char.isalpha() for char in cleaned):
                return self._get_playpart_fallback(response)
        
        # Nettoyage général
        cleaned = cleaned.replace("\\n", " ").replace("  ", " ")
        
        # Limiter longueur selon le modèle
        max_length = 200 if model_type == ModelType.PLAYPART_TRAINER else 400
        if len(cleaned) > max_length:
            sentences = cleaned.split('.')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < max_length:
                    result += sentence + "."
                else:
                    break
            cleaned = result if result else cleaned[:max_length]
        
        # Assurer fin propre
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def _get_playpart_fallback(self, original_question: str) -> str:
        """Fallback spécialisé pour PlayPart en cas de génération incohérente"""
        fallback_responses = {
            "upper body": "Focus on compound exercises like push-ups, pull-ups, and dips. Start with bodyweight movements and progress gradually.",
            "strength": "Build strength through progressive overload. Start with basic exercises, focus on proper form, then gradually increase intensity.",
            "muscle": "Muscle building requires proper exercise form, adequate protein intake, and sufficient recovery time.",
            "workout": "An effective workout includes warm-up, compound exercises, and cool-down. Aim for 45-60 minutes per session.",
            "exercise": "Choose exercises that match your fitness level. Start with bodyweight movements before adding weights.",
            "squat": "Proper squat form: feet shoulder-width apart, sit back like sitting in chair, keep back straight.",
            "push": "Perfect push-ups: hands shoulder-width apart, body straight, controlled movement down and up.",
            "cardio": "Effective cardio includes walking, jogging, cycling, or swimming. Start with 20-30 minutes, 3-4 times per week.",
            "nutrition": "Post-workout nutrition: consume protein within 30 minutes, stay hydrated, eat balanced meals.",
            "recovery": "Recovery is crucial: get 7-9 hours sleep, stretch post-workout, allow rest days between intense sessions."
        }
        
        question_lower = original_question.lower()
        for keyword, response in fallback_responses.items():
            if keyword in question_lower:
                return response
        
        return "Focus on progressive training with proper form. Start with basic exercises and gradually increase intensity."
    
    def generate_advice(self, question: str, user_profile: Optional[Dict] = None, model_type: Optional[ModelType] = None) -> Dict[str, Any]:
        """Génère conseil avec le modèle sélectionné"""
        start_time = datetime.now()
        self.stats['total_requests'] += 1
        
        # Utiliser le modèle spécifié ou le modèle actuel
        target_model = model_type or self.current_model
        
        try:
            # Recherche contexte RAG (moins pour PlayPart)
            context_count = 1 if target_model == ModelType.PLAYPART_TRAINER else 2
            relevant_docs = self.search_relevant_context(question, top_k=context_count)
            
            # Vérifier modèle
            if not self.model_configs[target_model]["loaded"]:
                return self._fallback_response(question, relevant_docs, target_model)
            
            # Statistiques modèle
            self.stats['model_usage'][target_model.value] += 1
            
            # Récupérer modèle et tokenizer
            model = self.models[target_model]
            tokenizer = self.tokenizers[target_model]
            config = self.generation_configs[target_model]
            
            # Créer prompt
            prompt = self._create_prompt(question, relevant_docs, target_model)
            
            # Tokeniser avec gestion d'erreurs
            try:
                max_prompt_length = 200 if target_model == ModelType.PLAYPART_TRAINER else 400
                inputs = tokenizer.encode(
                    prompt, 
                    return_tensors='pt', 
                    truncation=True, 
                    max_length=max_prompt_length
                ).to(self.device)
            except Exception as e:
                logger.error(f"❌ Erreur tokenisation: {e}")
                return self._fallback_response(question, relevant_docs, target_model)
            
            # Créer attention_mask
            attention_mask = torch.ones_like(inputs)
            
            # Générer avec paramètres optimisés
            with torch.no_grad():
                try:
                    outputs = model.generate(
                        inputs,
                        attention_mask=attention_mask,
                        max_length=inputs.shape[1] + config['max_new_tokens'],
                        temperature=config['temperature'],
                        do_sample=config['do_sample'],
                        top_p=config['top_p'],
                        top_k=config['top_k'],
                        repetition_penalty=config['repetition_penalty'],
                        no_repeat_ngram_size=config['no_repeat_ngram_size'],
                        pad_token_id=config.get('pad_token_id', tokenizer.pad_token_id),
                        eos_token_id=config.get('eos_token_id', tokenizer.eos_token_id),
                        early_stopping=config.get('early_stopping', False),
                        length_penalty=config.get('length_penalty', 1.0)
                    )
                except Exception as e:
                    logger.error(f"❌ Erreur génération: {e}")
                    return self._fallback_response(question, relevant_docs, target_model)
            
            # Décoder et post-traiter
            try:
                raw_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                generated_text = raw_response[len(prompt):].strip()
                final_response = self._post_process_response(generated_text, target_model)
            except Exception as e:
                logger.error(f"❌ Erreur décodage: {e}")
                return self._fallback_response(question, relevant_docs, target_model)
            
            # Vérification finale pour PlayPart
            if target_model == ModelType.PLAYPART_TRAINER and len(final_response) < 20:
                final_response = self._get_playpart_fallback(question)
            
            # Statistiques
            response_time = (datetime.now() - start_time).total_seconds()
            self.stats['successful_requests'] += 1
            self.stats['last_request_time'] = datetime.now()
            
            # Moyenne mobile
            self.stats['average_response_time'] = (
                (self.stats['average_response_time'] * (self.stats['successful_requests'] - 1) + response_time) 
                / self.stats['successful_requests']
            )
            
            return {
                'response': final_response,
                'sources': [doc.get('title', 'Document') for doc in relevant_docs],
                'context_used': len(relevant_docs) > 0,
                'model_used': target_model.value,
                'model_name': self.model_configs[target_model]["name"],
                'response_time': response_time,
                'confidence': 'high' if len(relevant_docs) > 0 else 'medium',
                'rag_enabled': self.rag_enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            self.stats['fallback_requests'] += 1
            return self._fallback_response(question, relevant_docs if 'relevant_docs' in locals() else [], target_model)
    
    def _fallback_response(self, question: str, relevant_docs: List[Dict], model_type: ModelType) -> Dict[str, Any]:
        """Réponse de fallback selon le modèle"""
        # Réponses adaptées au modèle
        if model_type == ModelType.PLAYPART_TRAINER:
            fallback_map = {
                'push': "Perfect push-ups: Keep body straight, hands shoulder-width apart, lower controlled until chest nearly touches ground. Start with 3 sets of 8-12 reps.",
                'squat': "Proper squats: Feet shoulder-width apart, sit back like sitting in chair, keep back straight. 3 sets of 12-20 reps for beginners.",
                'upper body': "Upper body strength: Focus on push-ups, pull-ups, dips. Progressive overload is key. Compound movements work best.",
                'strength': "Build strength: Start with bodyweight exercises, focus on proper form, then gradually add resistance. Consistency beats intensity.",
                'workout': "Effective workouts: Warm-up 5-10min, compound exercises, 3 sets per exercise, finish with stretching.",
                'muscle': "Muscle building: Progressive overload, adequate protein, sufficient recovery. Train each muscle group 2-3 times per week."
            }
            default_response = "Focus on bodyweight exercises like push-ups, squats, planks. Prioritize form over quantity. Progressive improvement and consistency are essential."
        else:
            fallback_map = {
                'pompes': "🏋️ **Pompes parfaites** : Position planche, mains largeur d'épaules, corps aligné. Descendre contrôlée jusqu'à frôler le sol. 3 séries de 8-12 répétitions.",
                'squat': "🏋️ **Squats efficaces** : Pieds largeur d'épaules, descendre comme pour s'asseoir, genoux alignés. 3 séries de 12-20 répétitions.",
                'cardio': "❤️ **Cardio débutant** : Marche rapide 30-45min, 3-4x/semaine. Progression graduelle vers alternance marche/course.",
                'nutrition': "🥗 **Nutrition sportive** : Hydratation 2-3L/jour, protéines 20-25g post-effort, alimentation équilibrée."
            }
            default_response = "🏋️ **Conseils fitness** : Échauffement 5-10min, exercices au poids du corps, 3 séries selon niveau, récupération avec étirements. Progression graduelle essentielle ! 💪"
        
        # Chercher réponse appropriée
        question_lower = question.lower()
        response_text = None
        
        for keyword, response in fallback_map.items():
            if keyword in question_lower:
                response_text = response
                break
        
        # Utiliser contexte RAG si disponible
        if not response_text and relevant_docs:
            best_doc = relevant_docs[0]
            response_text = f"**{best_doc['title']}** : {best_doc['content'][:150]}..."
        
        # Réponse par défaut
        if not response_text:
            response_text = default_response
        
        return {
            'response': response_text,
            'sources': [doc.get('title', 'Document') for doc in relevant_docs] if relevant_docs else ['Conseils de base'],
            'context_used': len(relevant_docs) > 0,
            'model_used': f'fallback_{model_type.value}',
            'model_name': f"Fallback {self.model_configs[model_type]['name']}",
            'response_time': 0.1,
            'confidence': 'medium',
            'rag_enabled': self.rag_enabled
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Statistiques du service - MÉTHODE MANQUANTE AJOUTÉE"""
        return {
            'status': 'healthy' if any(config["loaded"] for config in self.model_configs.values()) else 'degraded',
            'models': self.model_configs,
            'current_model': self.current_model,
            'rag_enabled': self.rag_enabled,
            'device': str(self.device),
            'initialization_time': self.initialization_time,
            'initialization_error': self.initialization_error,
            'stats': self.stats.copy(),
            'exercise_database_size': len(self.exercise_database),
            'timestamp': datetime.now().isoformat()
        }

# Instance globale
_fitness_service = None

def get_fitness_service(local_model_path: str = "./models/coach-sportif-french"):
    """Singleton du service"""
    global _fitness_service
    
    if _fitness_service is None:
        logger.info("🚀 Initialisation service fitness multi-modèles...")
        _fitness_service = FitnessCoachService(local_model_path)
    
    return _fitness_service