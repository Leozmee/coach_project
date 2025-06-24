# scripts/diagnostic_model.py - Diagnostic complet pour identifier le problème

import os
import sys
import logging
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

def setup_logging():
    """Configure le logging pour le diagnostic"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_model_path():
    """Vérifie le chemin du modèle"""
    logger = logging.getLogger(__name__)
    
    # Chemins à vérifier
    possible_paths = [
        "./models/coach-sportif-french",
        "models/coach-sportif-french",
        "./coach-sportif-french",
        "coach-sportif-french"
    ]
    
    logger.info("🔍 Vérification des chemins du modèle...")
    
    for path in possible_paths:
        model_path = Path(path)
        logger.info(f"   Vérification: {path}")
        
        if model_path.exists():
            logger.info(f"   ✅ Trouvé: {model_path.absolute()}")
            
            # Vérifier les fichiers requis
            required_files = [
                "config.json",
                "pytorch_model.bin",
                "tokenizer.json",
                "tokenizer_config.json"
            ]
            
            missing_files = []
            for file in required_files:
                if not (model_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                logger.warning(f"   ⚠️  Fichiers manquants: {missing_files}")
            else:
                logger.info(f"   ✅ Tous les fichiers requis présents")
                return model_path.absolute()
        else:
            logger.info(f"   ❌ Non trouvé: {path}")
    
    return None

def test_model_loading(model_path):
    """Test de chargement du modèle"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🚀 Test de chargement du modèle: {model_path}")
        
        # Test tokenizer
        logger.info("📝 Chargement du tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        logger.info(f"   ✅ Tokenizer chargé. Vocabulaire: {len(tokenizer.vocab)}")
        
        # Configuration du pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("   🔧 Pad token configuré")
        
        # Test modèle
        logger.info("🤖 Chargement du modèle...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"   📱 Device: {device}")
        
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        model.to(device)
        model.eval()
        logger.info(f"   ✅ Modèle chargé sur {device}")
        
        # Test de génération
        logger.info("🧪 Test de génération...")
        test_prompt = "Comment faire des pompes ?"
        inputs = tokenizer.encode(test_prompt, return_tensors='pt').to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=inputs.shape[1] + 50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_text = response[len(test_prompt):].strip()
        
        logger.info(f"   ✅ Test réussi!")
        logger.info(f"   📝 Prompt: {test_prompt}")
        logger.info(f"   🤖 Réponse: {generated_text[:100]}...")
        
        return True, None
        
    except Exception as e:
        logger.error(f"   ❌ Erreur: {e}")
        return False, str(e)

def check_dependencies():
    """Vérifie les dépendances"""
    logger = logging.getLogger(__name__)
    logger.info("📦 Vérification des dépendances...")
    
    required_packages = {
        'torch': 'torch',
        'transformers': 'transformers',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'streamlit': 'streamlit'
    }
    
    missing = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"   ✅ {package}")
        except ImportError:
            logger.error(f"   ❌ {package} - MANQUANT")
            missing.append(package)
    
    return missing

def check_api_imports():
    """Vérifie les imports de l'API"""
    logger = logging.getLogger(__name__)
    logger.info("🔌 Vérification des imports API...")
    
    try:
        from api.fitness_service import FitnessCoachService
        logger.info("   ✅ FitnessCoachService importé")
        
        from api.config import get_settings
        logger.info("   ✅ Configuration importée")
        
        from api.models import FitnessRequest, FitnessResponse
        logger.info("   ✅ Modèles Pydantic importés")
        
        return True
    except Exception as e:
        logger.error(f"   ❌ Erreur import: {e}")
        return False

def generate_fix_script(model_path, error_info=None):
    """Génère un script de correction"""
    logger = logging.getLogger(__name__)
    logger.info("🔧 Génération du script de correction...")
    
    fix_script = f"""# scripts/fix_model.py - Script de correction automatique

import os
import sys
import shutil
from pathlib import Path

def fix_model_path():
    \"\"\"Corrige le chemin du modèle\"\"\"
    source_path = Path("{model_path}")
    target_path = Path("models/coach-sportif-french")
    
    print(f"🔧 Correction du chemin du modèle...")
    print(f"   Source: {{source_path}}")
    print(f"   Cible: {{target_path}}")
    
    # Créer le dossier models si nécessaire
    target_path.parent.mkdir(exist_ok=True)
    
    # Copier ou créer un lien symbolique
    if source_path != target_path:
        if target_path.exists():
            print(f"   ⚠️  Suppression de l'ancien modèle...")
            shutil.rmtree(target_path)
        
        print(f"   📁 Copie du modèle...")
        shutil.copytree(source_path, target_path)
        print(f"   ✅ Modèle copié!")
    
    return target_path

def update_api_config():
    \"\"\"Met à jour la configuration de l'API\"\"\"
    config_content = '''# api/config.py - Configuration corrigée

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    \"\"\"Configuration de l'API Fitness Coach\"\"\"
    
    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8001
    debug: bool = True
    
    # Modèle - CHEMIN CORRIGÉ
    model_path: str = "./models/coach-sportif-french"
    model_device: str = "auto"
    
    # RAG
    enable_rag: bool = True
    rag_top_k: int = 3
    
    # Génération
    max_new_tokens: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Logs
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    \"\"\"Récupère la configuration avec cache\"\"\"
    return Settings()
'''
    
    with open("api/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print("✅ Configuration API mise à jour")

if __name__ == "__main__":
    print("🔧 CORRECTION AUTOMATIQUE DU MODÈLE")
    print("=" * 40)
    
    # Corriger le chemin
    model_path = fix_model_path()
    
    # Mettre à jour la config
    update_api_config()
    
    print(f"\\n🎉 CORRECTION TERMINÉE!")
    print(f"   Modèle: {{model_path}}")
    print(f"\\n📋 PROCHAINES ÉTAPES:")
    print(f"   1. Redémarrer l'API: python scripts/start_api.py")
    print(f"   2. Tester: curl -s http://127.0.0.1:8001/health | jq '.model_loaded'")
"""
    
    with open("scripts/fix_model.py", "w", encoding="utf-8") as f:
        f.write(fix_script)
    
    logger.info("   ✅ Script de correction créé: scripts/fix_model.py")

def main():
    """Diagnostic principal"""
    logger = setup_logging()
    
    print("🔍 DIAGNOSTIC MODÈLE DISTILGPT-2")
    print("=" * 40)
    
    # 1. Vérifier les dépendances
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n❌ DÉPENDANCES MANQUANTES: {missing_deps}")
        print("   Installer avec: pip install " + " ".join(missing_deps))
        return False
    
    # 2. Vérifier les imports API
    if not check_api_imports():
        print(f"\n❌ PROBLÈME D'IMPORTS API")
        print("   Vérifier la structure du projet")
        return False
    
    # 3. Trouver le modèle
    model_path = check_model_path()
    if not model_path:
        print(f"\n❌ MODÈLE NON TROUVÉ")
        print("   Vérifier que votre modèle DistilGPT-2 est bien présent")
        print("   Utiliser: python scripts/deploy_model.py /path/to/your/model")
        return False
    
    # 4. Tester le chargement
    success, error = test_model_loading(model_path)
    
    if success:
        print(f"\n✅ MODÈLE FONCTIONNEL!")
        print(f"   Chemin: {model_path}")
        print(f"\n📋 SI L'API NE FONCTIONNE TOUJOURS PAS:")
        print(f"   1. Redémarrer l'API: python scripts/start_api.py")
        print(f"   2. Vérifier: curl -s http://127.0.0.1:8001/health | jq '.model_loaded'")
        return True
    else:
        print(f"\n❌ ERREUR DE CHARGEMENT:")
        print(f"   {error}")
        
        # Générer script de correction
        generate_fix_script(model_path, error)
        print(f"\n🔧 SCRIPT DE CORRECTION GÉNÉRÉ:")
        print(f"   Exécuter: python scripts/fix_model.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)