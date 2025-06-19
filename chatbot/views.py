from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from .bert_service import BertRAGService
from .llm_service import LlamaService

logger = logging.getLogger(__name__)

# Instance globale des services (pour éviter de les recharger à chaque requête)
bert_service = None
llama_service = None

def initialize_services():
    """Initialise les services IA au démarrage"""
    global bert_service, llama_service
    
    if bert_service is None:
        logger.info("🚀 Initialisation des services IA...")
        
        # Données de base pour commencer
        test_documents = [
            {
                "title": "Pompes classiques",
                "content": "Les pompes sont un exercice de base pour développer les pectoraux, triceps et deltoïdes. Position: mains écartées largeur d'épaules, corps droit, descendre jusqu'à frôler le sol. Commencez par 3 séries de 8-12 répétitions."
            },
            {
                "title": "Squats pour débutants", 
                "content": "Le squat renforce quadriceps, fessiers et mollets. Pieds écartés largeur d'épaules, descendre comme pour s'asseoir, genoux alignés avec les pieds. 3 séries de 10-15 répétitions."
            },
            {
                "title": "Cardio pour perte de poids",
                "content": "Pour perdre du poids efficacement: alternez marche rapide et course. 30-45min, 3-4 fois par semaine. Privilégiez la régularité à l'intensité. Fréquence cardiaque cible: 60-70% de votre FC max."
            },
            {
                "title": "Étirements post-entraînement",
                "content": "Toujours s'étirer après l'effort. Maintenez chaque étirement 30 secondes. Concentrez-vous sur les muscles travaillés. Respirez profondément et ne forcez jamais."
            },
            {
                "title": "Nutrition pré-entraînement",
                "content": "Mangez 1-2h avant l'entraînement. Privilégiez les glucides complexes (avoine, banane) et évitez les graisses. Hydratez-vous bien avant, pendant et après l'effort."
            }
        ]
        
        try:
            bert_service = BertRAGService()
            bert_service.load_fitness_data(test_documents)
            llama_service = LlamaService()
            logger.info("✅ Services IA initialisés avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation services: {e}")
            raise

class ChatbotView(View):
    """Vue principale du chatbot"""
    
    def get(self, request):
        """Affiche la page du chatbot"""
        return render(request, 'chatbot/index.html')

@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    """API pour les conversations avec le chatbot"""
    
    def post(self, request):
        try:
            # Initialiser les services si nécessaire
            if bert_service is None or llama_service is None:
                initialize_services()
            
            # Parser la requête JSON
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({
                    'error': 'Message vide',
                    'response': 'Veuillez poser une question.'
                }, status=400)
            
            logger.info(f"Question reçue: {user_message}")
            
            # 1. Recherche BERT pour trouver le contexte pertinent
            relevant_docs = bert_service.search_relevant_docs(user_message, top_k=3)
            context = bert_service.format_context_for_llama(relevant_docs)
            
            # 2. Génération de la réponse avec Llama
            response = llama_service.get_response(user_message, context_docs=context)
            
            # 3. Retourner la réponse
            return JsonResponse({
                'response': response,
                'context_used': len(relevant_docs) > 0,
                'sources': [doc.get('title', 'Document') for doc in relevant_docs]
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Format JSON invalide'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Erreur API chatbot: {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur',
                'response': 'Désolé, une erreur est survenue. Veuillez réessayer.'
            }, status=500)

def health_check(request):
    """Endpoint pour vérifier le statut des services"""
    try:
        if bert_service is None or llama_service is None:
            initialize_services()
        
        return JsonResponse({
            'status': 'OK',
            'bert_ready': bert_service is not None,
            'llama_ready': llama_service is not None,
            'documents_loaded': len(bert_service.documents) if bert_service else 0
        })
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'error': str(e)
        }, status=500)