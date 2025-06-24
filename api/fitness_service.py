# api/fitness_service.py - Version corrigée pour SafeTensors

import os
import logging
import torch
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

# Imports IA
from transformers import AutoModelForCausalLM, AutoTokenizer
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class FitnessCoachService:
    """Service principal avec votre modèle DistilGPT-2 fine-tuné"""
    
    def __init__(self, model_path: str = "./models/coach-sportif-french"):
        self.model_path = Path(model_path)
        self.device = self._get_device()
        
        # État
        self.model_loaded = False
        self.rag_enabled = False
        self.initialization_time = None
        self.initialization_error = None
        
        # Composants
        self.tokenizer = None
        self.model = None
        self.embedding_model = None
        self.faiss_index = None
        self.exercise_database = []
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'fallback_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': None
        }
        
        # Configuration génération
        self.generation_config = {
            'max_new_tokens': 150,
            'temperature': 0.7,
            'do_sample': True,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'no_repeat_ngram_size': 3
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
        """Initialise le service complet avec gestion d'erreurs améliorée"""
        start_time = datetime.now()
        
        try:
            logger.info("🏋️ Initialisation Coach Fitness...")
            logger.info(f"📁 Chemin modèle: {self.model_path.absolute()}")
            
            # Vérifier existence du modèle
            if not self.model_path.exists():
                error_msg = f"Dossier modèle non trouvé: {self.model_path.absolute()}"
                logger.error(f"❌ {error_msg}")
                self.initialization_error = error_msg
                self._suggest_model_fix()
                return
            
            # Vérifier fichiers requis avec support SafeTensors
            required_files = ["config.json"]
            model_files = ["pytorch_model.bin", "model.safetensors"]
            
            missing_base = []
            for file in required_files:
                if not (self.model_path / file).exists():
                    missing_base.append(file)
            
            # Vérifier au moins un fichier de modèle
            model_file_found = None
            for model_file in model_files:
                if (self.model_path / model_file).exists():
                    model_file_found = model_file
                    break
            
            if missing_base:
                error_msg = f"Fichiers de base manquants dans {self.model_path}: {missing_base}"
                logger.error(f"❌ {error_msg}")
                self.initialization_error = error_msg
                return
            
            if not model_file_found:
                error_msg = f"Aucun fichier de modèle trouvé dans {self.model_path}"
                logger.error(f"❌ {error_msg}")
                self.initialization_error = error_msg
                return
            
            logger.info(f"✅ Fichiers modèle détectés: {model_file_found}")
            
            # 1. Charger DistilGPT-2
            logger.info("🤖 Chargement du modèle DistilGPT-2...")
            self._load_model()
            
            # 2. Charger RAG (optionnel)
            if RAG_AVAILABLE:
                logger.info("📊 Chargement du système RAG...")
                self._load_rag()
            else:
                logger.warning("⚠️ RAG non disponible (dépendances manquantes)")
            
            self.model_loaded = True
            self.initialization_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Service initialisé avec succès en {self.initialization_time:.2f}s")
            logger.info(f"📱 Device: {self.device}")
            logger.info(f"🤖 Modèle: DistilGPT-2 fine-tuné")
            logger.info(f"📊 RAG: {'Activé' if self.rag_enabled else 'Désactivé'}")
            
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.initialization_error = error_msg
            self.model_loaded = False
            self._suggest_model_fix()
    
    def _suggest_model_fix(self):
        """Suggestions pour corriger les problèmes de modèle"""
        logger.info("\n🔧 SUGGESTIONS DE CORRECTION:")
        logger.info("1. Vérifier le chemin du modèle:")
        logger.info(f"   ls -la {self.model_path}")
        logger.info("2. Diagnostic complet:")
        logger.info("   python diagnostic_model_fixed.py")
        logger.info("3. Installer accelerate si nécessaire:")
        logger.info("   pip install accelerate")
    
    def _load_model(self):
        """Charge votre modèle DistilGPT-2 fine-tuné avec support SafeTensors"""
        try:
            logger.info(f"📚 Chargement tokenizer depuis: {self.model_path}")
            
            # Tokenizer avec gestion d'erreurs
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            
            # Configurer pad token si nécessaire
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                logger.info("🔧 Pad token configuré")
            
            # Mettre à jour config génération
            self.generation_config['pad_token_id'] = self.tokenizer.pad_token_id
            self.generation_config['eos_token_id'] = self.tokenizer.eos_token_id
            
            logger.info(f"✅ Tokenizer chargé. Vocabulaire: {len(self.tokenizer.vocab)}")
            
            # Détection du format de modèle
            if (self.model_path / "model.safetensors").exists():
                logger.info("🔒 Format SafeTensors détecté")
            elif (self.model_path / "pytorch_model.bin").exists():
                logger.info("⚡ Format PyTorch détecté")
            
            # Modèle avec options adaptées (SANS low_cpu_mem_usage pour éviter accelerate)
            logger.info(f"⚡ Chargement modèle sur {self.device}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                # Retirer low_cpu_mem_usage pour éviter accelerate
            )
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("✅ Modèle DistilGPT-2 chargé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            raise
    
    def _load_rag(self):
        """Charge le système RAG (optionnel)"""
        try:
            logger.info("📊 Chargement RAG...")
            
            # Modèle embeddings
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            # Construire index FAISS
            self._build_faiss_index()
            
            self.rag_enabled = True
            logger.info("✅ RAG activé")
            
        except Exception as e:
            logger.error(f"⚠️ RAG non disponible: {e}")
            self.rag_enabled = False
    
    def _load_exercise_database(self):
        """Base d'exercices pour RAG"""
        self.exercise_database = [
            {
                "id": 1,
                "title": "Pompes classiques",
                "content": "Exercice fondamental pour pectoraux, triceps et deltoïdes. Position planche, mains largeur d'épaules, descendre contrôlée jusqu'à frôler le sol. 3 séries de 8-12 répétitions pour débutants.",
                "muscle_groups": ["pectoraux", "triceps", "deltoïdes"],
                "difficulty": "débutant",
                "equipment": "aucun"
            },
            {
                "id": 2,
                "title": "Squats parfaits",
                "content": "Mouvement roi pour quadriceps et fessiers. Pieds largeur d'épaules, descendre comme pour s'asseoir, garder dos droit. 3 séries de 12-20 répétitions.",
                "muscle_groups": ["quadriceps", "fessiers", "mollets"],
                "difficulty": "débutant",
                "equipment": "aucun"
            },
            {
                "id": 3,
                "title": "Planche abdominale",
                "content": "Gainage statique pour core et stabilité. Position sur avant-bras, corps aligné, contracter abdos et fessiers. Tenir 30 secondes à 2 minutes.",
                "muscle_groups": ["abdominaux", "core", "épaules"],
                "difficulty": "débutant",
                "equipment": "aucun"
            },
            {
                "id": 4,
                "title": "Nutrition sportive",
                "content": "Hydratation 2-3L/jour, protéines 20-25g post-effort dans les 30min. Privilégier sources complètes: œufs, poisson, viande maigre.",
                "category": "nutrition",
                "importance": "haute"
            },
            {
                "id": 5,
                "title": "Récupération optimale",
                "content": "Sommeil 7-9h/nuit priorité absolue. Étirements post-effort 30s par muscle. Repos actif entre séances intenses.",
                "category": "récupération",
                "importance": "critique"
            }
        ]
    
    def _build_faiss_index(self):
        """Construit index FAISS pour recherche sémantique"""
        if not self.embedding_model:
            return
        
        try:
            # Créer embeddings
            texts = [f"{item['title']} {item['content']}" for item in self.exercise_database]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # Index FAISS
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # Normaliser et ajouter
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
            # Encoder query
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
            faiss.normalize_L2(query_embedding)
            
            # Rechercher
            scores, indices = self.faiss_index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.exercise_database))
            )
            
            # Retourner documents
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
    
    def _create_prompt(self, question: str, context_docs: List[Dict]) -> str:
        """Crée prompt optimisé pour votre modèle fine-tuné"""
        # Contexte RAG
        context_text = ""
        if context_docs:
            context_parts = []
            for doc in context_docs[:2]:
                context_parts.append(f"- {doc['title']}: {doc['content'][:150]}...")
            context_text = "\n".join(context_parts)
        
        # Format optimisé pour votre modèle
        prompt = f"""[COACH] En tant que coach sportif français certifié, voici les informations pertinentes :

{context_text}

Question: {question}

Réponse: """
        
        return prompt
    
    def _post_process_response(self, response: str) -> str:
        """Post-traitement français"""
        if not response:
            return "Désolé, je n'ai pas pu générer une réponse appropriée."
        
        # Nettoyer
        cleaned = response.strip()
        
        # Supprimer artefacts prompt
        for artifact in ["[COACH]", "Question:", "Réponse:"]:
            if artifact in cleaned:
                cleaned = cleaned.split(artifact)[-1].strip()
        
        # Nettoyer caractères
        cleaned = cleaned.replace("\\n", " ").replace("  ", " ")
        
        # Limiter longueur
        if len(cleaned) > 400:
            sentences = cleaned.split('.')
            cleaned = '. '.join(sentences[:3])
            if not cleaned.endswith('.'):
                cleaned += '.'
        
        # Assurer fin propre
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def generate_advice(self, question: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """Génère conseil avec votre modèle DistilGPT-2"""
        start_time = datetime.now()
        self.stats['total_requests'] += 1
        
        try:
            # 1. Recherche contexte RAG
            relevant_docs = self.search_relevant_context(question, top_k=3)
            
            # 2. Vérifier modèle
            if not self.model_loaded:
                return self._fallback_response(question, relevant_docs)
            
            # 3. Créer prompt
            prompt = self._create_prompt(question, relevant_docs)
            
            # 4. Tokeniser avec attention_mask
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors='pt', 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            # Créer attention_mask pour éviter le warning
            attention_mask = torch.ones_like(inputs)
            
            # 5. Générer avec votre modèle DistilGPT-2
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    attention_mask=attention_mask,  # Ajouter attention_mask
                    max_length=inputs.shape[1] + self.generation_config['max_new_tokens'],
                    temperature=self.generation_config['temperature'],
                    do_sample=self.generation_config['do_sample'],
                    top_p=self.generation_config['top_p'],
                    top_k=self.generation_config['top_k'],
                    repetition_penalty=self.generation_config['repetition_penalty'],
                    no_repeat_ngram_size=self.generation_config['no_repeat_ngram_size'],
                    pad_token_id=self.generation_config['pad_token_id'],
                    eos_token_id=self.generation_config['eos_token_id']
                )
            
            # 6. Décoder et post-traiter
            raw_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = raw_response[len(prompt):].strip()
            final_response = self._post_process_response(generated_text)
            
            # 7. Statistiques
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
                'model_used': 'distilgpt2_finetuned',
                'response_time': response_time,
                'confidence': 'high' if len(relevant_docs) > 0 else 'medium',
                'rag_enabled': self.rag_enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            self.stats['fallback_requests'] += 1
            return self._fallback_response(question, relevant_docs if 'relevant_docs' in locals() else [])
    
    def _fallback_response(self, question: str, relevant_docs: List[Dict]) -> Dict[str, Any]:
        """Réponse de fallback"""
        # Réponses basées sur mots-clés
        fallback_map = {
            'pompes': "🏋️ **Pompes parfaites** : Position planche, mains largeur d'épaules, corps aligné. Descendre contrôlée jusqu'à frôler le sol, remonter en poussant. 3 séries de 8-12 répétitions pour débuter. Focus sur la technique avant la quantité !",
            'squat': "🏋️ **Squats efficaces** : Pieds largeur d'épaules, descendre comme pour s'asseoir, genoux alignés avec pieds. 3 séries de 12-20 répétitions. Excellent pour quadriceps et fessiers !",
            'cardio': "❤️ **Cardio débutant** : Marche rapide 30-45min, 3-4x/semaine. Progression graduelle vers alternance marche/course. L'important c'est la régularité !",
            'nutrition': "🥗 **Nutrition sportive** : Hydratation 2-3L/jour, protéines 20-25g post-effort, alimentation équilibrée. Les bases font la différence !",
            'récupération': "😴 **Récupération optimale** : Sommeil 7-9h/nuit, étirements post-effort, repos actif. La récupération fait partie de l'entraînement !"
        }
        
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
            response_text = f"**{best_doc['title']}** : {best_doc['content'][:200]}... 💪"
        
        # Réponse générale
        if not response_text:
            response_text = "🏋️ **Conseils fitness généraux** : Commencez par échauffement 5-10min, exercices au poids du corps (pompes, squats, planche), 3 séries selon votre niveau, récupération avec étirements. Progression graduelle et écoute du corps essentielles ! 💪"
        
        return {
            'response': response_text,
            'sources': [doc.get('title', 'Document') for doc in relevant_docs] if relevant_docs else ['Conseils de base'],
            'context_used': len(relevant_docs) > 0,
            'model_used': 'fallback_rag',
            'response_time': 0.1,
            'confidence': 'medium',
            'rag_enabled': self.rag_enabled
        }
    
    def get_exercise_recommendations(self, muscle_groups=None, difficulty=None, equipment=None):
        """Recommandations d'exercices"""
        filtered = []
        for exercise in self.exercise_database:
            if muscle_groups and 'muscle_groups' in exercise:
                if not any(muscle in exercise['muscle_groups'] for muscle in muscle_groups):
                    continue
            if difficulty and exercise.get('difficulty') != difficulty:
                continue
            if equipment and exercise.get('equipment') != equipment:
                continue
            filtered.append(exercise)
        return filtered
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Statistiques du service"""
        return {
            'status': 'healthy' if self.model_loaded else 'degraded',
            'model_loaded': self.model_loaded,
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

def get_fitness_service(model_path: str = "./models/coach-sportif-french"):
    """Singleton du service"""
    global _fitness_service
    
    if _fitness_service is None:
        logger.info("🚀 Initialisation service fitness...")
        _fitness_service = FitnessCoachService(model_path)
    
    return _fitness_service