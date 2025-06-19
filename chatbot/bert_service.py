from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BertRAGService:
    def __init__(self):
        # Modèle BERT multilingue optimisé pour la recherche sémantique
        try:
            print("Chargement du modèle BERT...")
            self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
            self.index = None
            self.documents = []
            self.embeddings = None
            print("✅ Modèle BERT chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle BERT: {e}")
            raise
        
    def load_fitness_data(self, documents: List[Dict]):
        """
        Charge les documents fitness et crée l'index BERT
        """
        if not documents:
            logger.warning("Aucun document fourni")
            return
            
        try:
            self.documents = documents
            
            # Prépare les textes pour l'encodage
            texts = []
            for doc in documents:
                # Combine titre + contenu pour une meilleure recherche
                title = doc.get('title', '')
                content = doc.get('content', '')
                text = f"{title} {content}".strip()
                texts.append(text)
            
            if not texts:
                logger.warning("Aucun texte valide trouvé dans les documents")
                return
            
            # Encode avec BERT
            print("Encodage des documents avec BERT...")
            self.embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # Crée l'index FAISS pour la recherche rapide
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner Product pour similarité
            
            # Normalise les embeddings pour la similarité cosinus
            faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings)
            
            print(f"✅ Index BERT créé avec {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            raise
    
    def search_relevant_docs(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Recherche les documents les plus pertinents pour une question
        """
        if self.index is None:
            logger.warning("Index BERT non initialisé")
            return []
            
        if not query.strip():
            logger.warning("Query vide")
            return []
        
        try:
            # Encode la question avec BERT
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Recherche dans l'index
            scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
            
            # Retourne les documents avec scores
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if 0 <= idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['relevance_score'] = float(score)
                    doc['rank'] = i + 1
                    results.append(doc)
            
            logger.info(f"Trouvé {len(results)} documents pertinents pour: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def format_context_for_llama(self, relevant_docs: List[Dict]) -> str:
        """
        Formate les documents trouvés pour le prompt Llama
        """
        if not relevant_docs:
            return "Aucun contexte spécifique trouvé."
        
        context = "Informations pertinentes :\n\n"
        for doc in relevant_docs:
            title = doc.get('title', 'Document')
            content = doc.get('content', '')
            score = doc.get('relevance_score', 0)
            
            context += f"📋 {title}\n"
            context += f"{content}\n"
            context += f"(Pertinence: {score:.2f})\n\n"
        
        return context