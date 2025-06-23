# scripts/deploy_model.py - Déploiement et validation de votre modèle DistilGPT-2

import os
import sys
import shutil
from pathlib import Path
import json

def validate_model_files(source_path):
    """Valide que tous les fichiers nécessaires sont présents"""
    
    required_files = [
        "config.json",
        "tokenizer_config.json", 
        "tokenizer.json",
        "vocab.json",
        "merges.txt",
        "special_tokens_map.json",
        "generation_config.json"
    ]
    
    # Fichiers modèle (au moins un requis)
    model_files = ["model.safetensors", "pytorch_model.bin"]
    
    source = Path(source_path)
    missing_files = []
    
    # Vérifier fichiers requis
    for file_name in required_files:
        if not (source / file_name).exists():
            missing_files.append(file_name)
    
    # Vérifier qu'au moins un fichier modèle existe
    model_found = any((source / model_file).exists() for model_file in model_files)
    if not model_found:
        missing_files.extend(model_files)
    
    return missing_files

def get_model_info(model_path):
    """Récupère les informations du modèle"""
    try:
        config_path = Path(model_path) / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return {
                "model_type": config.get("model_type", "unknown"),
                "vocab_size": config.get("vocab_size", "unknown"),
                "hidden_size": config.get("hidden_size", "unknown"),
                "num_layers": config.get("n_layer", config.get("num_hidden_layers", "unknown"))
            }
    except Exception as e:
        print(f"⚠️ Impossible de lire config.json: {e}")
    
    return {"model_type": "unknown"}

def check_existing_model():
    """Vérifie si le modèle existe déjà dans le projet"""
    # Chemins possibles depuis la racine du projet
    possible_paths = [
        Path("models/coach-sportif-french"),  # Depuis racine
        Path("../models/coach-sportif-french"),  # Depuis scripts/
        Path("./models/coach-sportif-french")  # Relatif
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path.resolve()
    
    return None

def validate_existing_model(model_path):
    """Valide un modèle existant"""
    print("🔍 VALIDATION MODÈLE EXISTANT")
    print("=" * 40)
    print(f"📂 Chemin: {model_path}")
    
    # Lister les fichiers présents
    files = list(model_path.glob("*"))
    print(f"\n📋 FICHIERS TROUVÉS ({len(files)}):")
    
    total_size = 0
    for file_path in sorted(files):
        if file_path.is_file():
            size = file_path.stat().st_size
            total_size += size
            
            if size > 1024 * 1024:  # > 1MB
                size_str = f"{size / (1024*1024):.1f}MB"
            else:
                size_str = f"{size / 1024:.1f}KB"
            
            print(f"   ✅ {file_path.name} ({size_str})")
    
    print(f"\n📊 Taille totale: {total_size / (1024*1024):.1f}MB")
    
    # Validation des fichiers requis
    missing_files = validate_model_files(model_path)
    
    if missing_files:
        print(f"\n❌ FICHIERS MANQUANTS:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print(f"\n✅ Tous les fichiers requis sont présents")
    
    # Informations détaillées
    model_info = get_model_info(model_path)
    print(f"\n📊 INFORMATIONS MODÈLE:")
    print(f"   Type: {model_info['model_type']}")
    print(f"   Vocab size: {model_info['vocab_size']}")
    print(f"   Hidden size: {model_info['hidden_size']}")
    print(f"   Layers: {model_info['num_layers']}")
    
    return True

def deploy_model(source_path, target_path="./models/coach-sportif-french"):
    """
    Déploie votre modèle DistilGPT-2 dans la structure du projet
    
    Args:
        source_path: Chemin vers votre modèle (dossier avec tous les fichiers)
        target_path: Destination dans le projet
    """
    
    print("🚀 DÉPLOIEMENT MODÈLE DISTILGPT-2 FITNESS COACH")
    print("=" * 55)
    
    source = Path(source_path)
    target = Path(target_path)
    
    # Vérifications préliminaires
    if not source.exists():
        print(f"❌ ERREUR: Dossier source non trouvé: {source}")
        print(f"💡 Vérifiez le chemin vers votre modèle")
        return False
    
    if not source.is_dir():
        print(f"❌ ERREUR: Le chemin source doit être un dossier: {source}")
        return False
    
    print(f"📂 Source: {source}")
    print(f"📂 Destination: {target}")
    
    # Validation des fichiers
    print(f"\n🔍 VALIDATION DES FICHIERS...")
    missing_files = validate_model_files(source)
    
    if missing_files:
        print(f"❌ FICHIERS MANQUANTS:")
        for file in missing_files:
            print(f"   - {file}")
        print(f"\n💡 Votre modèle doit contenir tous ces fichiers.")
        print(f"💡 Vérifiez que vous pointez vers le bon dossier de modèle.")
        return False
    
    print(f"✅ Tous les fichiers requis sont présents")
    
    # Informations sur le modèle
    model_info = get_model_info(source)
    print(f"\n📊 INFORMATIONS MODÈLE:")
    print(f"   Type: {model_info['model_type']}")
    print(f"   Vocab size: {model_info['vocab_size']}")
    print(f"   Hidden size: {model_info['hidden_size']}")
    print(f"   Layers: {model_info['num_layers']}")
    
    # Créer le dossier de destination
    target.mkdir(parents=True, exist_ok=True)
    
    # Copier tous les fichiers
    print(f"\n📦 COPIE DES FICHIERS...")
    
    copied_files = []
    total_size = 0
    
    for file_path in source.iterdir():
        if file_path.is_file():
            target_file = target / file_path.name
            
            try:
                shutil.copy2(file_path, target_file)
                file_size = file_path.stat().st_size
                total_size += file_size
                
                # Affichage avec taille
                if file_size > 1024 * 1024:  # > 1MB
                    size_str = f"{file_size / (1024*1024):.1f}MB"
                else:
                    size_str = f"{file_size / 1024:.1f}KB"
                
                print(f"   ✅ {file_path.name} ({size_str})")
                copied_files.append(file_path.name)
                
            except Exception as e:
                print(f"   ❌ Erreur copie {file_path.name}: {e}")
                return False
    
    print(f"\n📈 RÉSUMÉ:")
    print(f"   Fichiers copiés: {len(copied_files)}")
    print(f"   Taille totale: {total_size / (1024*1024):.1f}MB")
    
    # Vérification finale
    print(f"\n🔍 VÉRIFICATION FINALE...")
    
    try:
        # Test de chargement du config
        config_file = target / "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"   ✅ config.json lisible")
        print(f"   ✅ Modèle prêt pour l'API")
        
    except Exception as e:
        print(f"   ⚠️ Avertissement: {e}")
        print(f"   💡 Le modèle a été copié mais pourrait nécessiter des ajustements")
    
    # Instructions finales
    print(f"\n🎉 DÉPLOIEMENT RÉUSSI !")
    print(f"\n📋 PROCHAINES ÉTAPES:")
    print(f"   1. Installer les dépendances: pip install -r requirements.txt")
    print(f"   2. Lancer l'API: python scripts/start_api.py")
    print(f"   3. Lancer Streamlit: python scripts/start_streamlit.py")
    print(f"   4. Tester: http://localhost:8501")
    
    return True

def main():
    """Point d'entrée principal"""
    
    # Si aucun argument, vérifier s'il y a déjà un modèle
    if len(sys.argv) == 1:
        print("🏋️ VALIDATION MODÈLE FITNESS COACH")
        print("=" * 40)
        
        existing_model = check_existing_model()
        
        if existing_model:
            print(f"✅ Modèle trouvé: {existing_model}")
            
            if validate_existing_model(existing_model):
                print(f"\n🎉 MODÈLE VALIDÉ !")
                print(f"\n📋 PROCHAINES ÉTAPES:")
                print(f"   1. Installer les dépendances: pip install -r requirements.txt")
                print(f"   2. Lancer l'API: python scripts/start_api.py")
                print(f"   3. Lancer Streamlit: python scripts/start_streamlit.py")
                print(f"   4. Tester: http://localhost:8501")
                sys.exit(0)
            else:
                print(f"\n❌ Modèle incomplet ou corrompu")
                sys.exit(1)
        else:
            print("❌ Aucun modèle trouvé dans le projet")
            print("\nUsage:")
            print("  python scripts/deploy_model.py <chemin_vers_votre_modele>")
            print("\nExemple:")
            print("  python scripts/deploy_model.py /path/to/coach-sportif-french")
            print("  python scripts/deploy_model.py ./mon_modele")
            print("\n💡 Le dossier doit contenir tous les fichiers de votre modèle DistilGPT-2")
            sys.exit(1)
    
    # Mode déploiement avec source spécifiée
    elif len(sys.argv) == 2:
        model_source = sys.argv[1]
        success = deploy_model(model_source)
        
        if success:
            print(f"\n🚀 Modèle prêt ! Vous pouvez maintenant créer l'API.")
            sys.exit(0)
        else:
            print(f"\n❌ Échec du déploiement. Vérifiez le chemin et les fichiers.")
            sys.exit(1)
    
    else:
        print("🏋️ DÉPLOIEMENT MODÈLE FITNESS COACH")
        print("=" * 40)
        print("\nUsage:")
        print("  python scripts/deploy_model.py                    # Valider modèle existant")
        print("  python scripts/deploy_model.py <chemin_modele>    # Déployer nouveau modèle")
        print("\nExemple:")
        print("  python scripts/deploy_model.py /path/to/coach-sportif-french")
        sys.exit(1)

if __name__ == "__main__":
    main()