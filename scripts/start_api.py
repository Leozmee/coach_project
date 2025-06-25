# scripts/start_api.py - Script de démarrage de l'API (CORRIGÉ)

import os
import sys
import subprocess
import time
from pathlib import Path

# scripts/start_api.py (en haut du fichier)
from dotenv import load_dotenv
load_dotenv()


def check_requirements():
    """Vérifie que les dépendances sont installées"""
    
    # Dictionnaire package_name -> nom_import_reel
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'torch': 'torch',
        'transformers': 'transformers',
        'sentence-transformers': 'sentence_transformers',  # Correction ici
        'faiss-cpu': 'faiss',  # Correction ici - faiss-cpu s'importe comme 'faiss'
        'pydantic': 'pydantic'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} ({import_name})")
        except ImportError as e:
            print(f"❌ {package_name} ({import_name}) - {e}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ PACKAGES MANQUANTS:")
        for package in missing_packages:
            print(f"   - {package}")
        print(f"\n💡 Installez avec: pip install {' '.join(missing_packages)}")
        return False
    
    print(f"\n✅ Toutes les dépendances sont installées")
    return True

def check_model():
    """Vérifie que le modèle est présent"""
    model_path = Path("./models/coach-sportif-french")
    
    if not model_path.exists():
        print("❌ MODÈLE NON TROUVÉ")
        print(f"   Chemin: {model_path}")
        print("\n💡 Déployez votre modèle avec:")
        print("   python scripts/deploy_model.py /path/to/your/model")
        return False
    
    # Vérifier fichiers essentiels
    required_files = ['config.json', 'tokenizer_config.json', 'vocab.json']
    missing_files = []
    
    for file_name in required_files:
        if not (model_path / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print("❌ FICHIERS MODÈLE MANQUANTS:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        return False
    
    print(f"✅ Modèle trouvé: {model_path}")
    return True

def start_api():
    """Démarre l'API FastAPI"""
    print("🚀 DÉMARRAGE API COACH FITNESS")
    print("=" * 50)
    
    # Vérifications préalables
    print("🔍 Vérification des dépendances...")
    if not check_requirements():
        sys.exit(1)
    
    print("\n🔍 Vérification du modèle...")
    if not check_model():
        sys.exit(1)
    
    # Configuration depuis variables d'environnement
    api_host = os.getenv('API_HOST', '127.0.0.1')
    api_port = int(os.getenv('API_PORT', 8001))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"\n📡 Configuration:")
    print(f"   Host: {api_host}:{api_port}")
    print(f"   Debug: {'✅ On' if debug else '❌ Off'}")
    print("=" * 50)
    
    # Ajouter le répertoire parent au PYTHONPATH
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Démarrer avec uvicorn
        import uvicorn
        
        print("🚀 Lancement de l'API...")
        print(f"📡 Documentation: http://{api_host}:{api_port}/docs")
        print(f"🔍 Health check: http://{api_host}:{api_port}/health")
        print("\n💡 Appuyez sur Ctrl+C pour arrêter")
        
        uvicorn.run(
            "api.main:app",
            host=api_host,
            port=api_port,
            reload=debug,
            log_level="info" if debug else "warning",
            access_log=debug
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'API par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur démarrage API: {e}")
        print(f"💡 Vérifiez que le dossier 'api' existe et contient main.py")
        sys.exit(1)

if __name__ == "__main__":
    start_api()