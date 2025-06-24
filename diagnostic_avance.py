# diagnostic_model_fixed.py - Version corrigée sans erreur de syntaxe

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
    """Vérifie le chemin du modèle avec support SafeTensors"""
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
            
            # Vérifier les fichiers requis (formats multiples)
            required_files = ["config.json"]
            model_files = [
                "pytorch_model.bin",      # Format PyTorch classique
                "model.safetensors",      # Format SafeTensors
                "pytorch_model-00001-of-00001.bin"  # Modèles divisés
            ]
            
            # Vérifier fichiers de base
            missing_base = []
            for file in required_files:
                if not (model_path / file).exists():
                    missing_base.append(file)
            
            # Vérifier au moins un fichier de modèle
            model_file_found = None
            for model_file in model_files:
                if (model_path / model_file).exists():
                    model_file_found = model_file
                    break
            
            if missing_base:
                logger.warning(f"   ⚠️  Fichiers de base manquants: {missing_base}")
                continue
            elif not model_file_found:
                logger.warning(f"   ⚠️  Aucun fichier de modèle trouvé")
                continue
            else:
                logger.info(f"   ✅ Modèle trouvé: {model_file_found}")
                logger.info(f"   ✅ Tous les fichiers requis présents")
                return model_path.absolute()
        else:
            logger.info(f"   ❌ Non trouvé: {path}")
    
    return None

def test_model_loading(model_path):
    """Test de chargement du modèle avec support SafeTensors"""
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
        
        # Test modèle avec support SafeTensors
        logger.info("🤖 Chargement du modèle...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"   📱 Device: {device}")
        
        # Détection automatique du format
        model_path_obj = Path(model_path)
        if (model_path_obj / "model.safetensors").exists():
            logger.info("   🔒 Format détecté: SafeTensors")
        elif (model_path_obj / "pytorch_model.bin").exists():
            logger.info("   ⚡ Format détecté: PyTorch")
        
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            low_cpu_mem_usage=True,
            # SafeTensors est supporté automatiquement par transformers
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
        
        logger.info(f"   ✅ Test de génération réussi!")
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

def main():
    """Diagnostic principal avec support SafeTensors"""
    logger = setup_logging()
    
    print("🔍 DIAGNOSTIC MODÈLE DISTILGPT-2 (SafeTensors Support)")
    print("=" * 55)
    
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
    
    # 3. Trouver le modèle (avec support SafeTensors)
    model_path = check_model_path()
    if not model_path:
        print(f"\n❌ MODÈLE NON TROUVÉ")
        print("   Vérifier que votre modèle DistilGPT-2 est bien présent")
        return False
    
    # 4. Tester le chargement avec SafeTensors
    success, error = test_model_loading(model_path)
    
    if success:
        print(f"\n🎉 MODÈLE SAFETENSORS FONCTIONNEL!")
        print(f"   Chemin: {model_path}")
        print(f"   Format: SafeTensors (sécurisé)")
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"   1. Redémarrer l'API: python scripts/start_api.py")
        print(f"   2. Tester: curl -s http://127.0.0.1:8001/health | jq '.model_loaded'")
        print("   3. Chat test: curl -X POST http://127.0.0.1:8001/chat \\")
        print("      -H 'Content-Type: application/json' \\")
        print("      -d '{\"message\": \"Salut!\"}' | jq '.model_used'")
        
        return True
    else:
        print(f"\n❌ ERREUR DE CHARGEMENT:")
        print(f"   {error}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)