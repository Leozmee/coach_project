# scripts/start_streamlit.py - Lancement Streamlit

import os
import sys
import subprocess
from pathlib import Path
import requests
import time

def check_api_status():
    """Vérifie que l'API est accessible"""
    print("🔍 Vérification de l'API...")
    
    api_url = "http://127.0.0.1:8001"
    
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            model_loaded = data.get("model_loaded", False)
            
            print(f"✅ API accessible sur {api_url}")
            print(f"🤖 Modèle chargé: {'✅' if model_loaded else '❌'}")
            
            if not model_loaded:
                print("⚠️  Le modèle n'est pas chargé. L'interface fonctionnera en mode dégradé.")
            
            return True
        else:
            print(f"⚠️  API répond mais avec erreur: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API non accessible !")
        print("💡 Solution:")
        print("   1. Lancez l'API: python scripts/start_api.py")
        print("   2. Attendez que le modèle se charge")
        print("   3. Relancez Streamlit")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def start_streamlit():
    """Lance l'application Streamlit"""
    print("🚀 LANCEMENT STREAMLIT COACH FITNESS")
    print("=" * 45)
    
    # Vérifier la structure du projet
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    streamlit_app = project_root / "streamlit_app" / "main.py"
    
    print(f"📁 Projet: {project_root}")
    print(f"📄 App Streamlit: {streamlit_app}")
    
    # Créer le dossier streamlit_app si nécessaire
    streamlit_dir = project_root / "streamlit_app"
    streamlit_dir.mkdir(exist_ok=True)
    
    # Vérifier que le fichier main.py existe
    if not streamlit_app.exists():
        print("❌ Fichier streamlit_app/main.py non trouvé !")
        print("💡 Créez le fichier avec le code de l'application Streamlit")
        return False
    
    # Vérifier l'API
    api_ok = check_api_status()
    if not api_ok:
        response = input("\n❓ Continuer malgré les problèmes d'API ? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Changer vers la racine du projet
    os.chdir(project_root)
    
    # Configuration Streamlit
    streamlit_config = {
        "server.port": 8501,
        "server.address": "localhost",
        "server.headless": False,
        "browser.serverAddress": "localhost",
        "browser.gatherUsageStats": False,
        "theme.primaryColor": "#FF6B6B",
        "theme.backgroundColor": "#0E1117",
        "theme.secondaryBackgroundColor": "#262730",
        "theme.textColor": "#FAFAFA"
    }
    
    # Construire la commande
    cmd = ["streamlit", "run", str(streamlit_app)]
    
    # Ajouter les options de configuration
    for key, value in streamlit_config.items():
        cmd.extend(["--server.port" if key == "server.port" else f"--{key}", str(value)])
    
    print("\n🎨 Configuration Streamlit:")
    print(f"   Port: {streamlit_config['server.port']}")
    print(f"   Adresse: {streamlit_config['server.address']}")
    print(f"   Thème: Fitness (orange/dark)")
    
    print(f"\n🌐 Interface accessible sur:")
    print(f"   http://localhost:{streamlit_config['server.port']}")
    
    print(f"\n🔗 API Backend:")
    print(f"   http://127.0.0.1:8001")
    print(f"   Documentation: http://127.0.0.1:8001/docs")
    
    print("\n💡 Appuyez sur Ctrl+C pour arrêter")
    print("=" * 45)
    
    try:
        # Lancer Streamlit
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de Streamlit par l'utilisateur")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement de Streamlit: {e}")
        return False
    except FileNotFoundError:
        print("❌ Streamlit n'est pas installé !")
        print("💡 Installer avec: pip install streamlit")
        return False

def main():
    """Point d'entrée principal"""
    
    # Vérifier l'environnement virtuel
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  Vous n'êtes pas dans un environnement virtuel")
        print("💡 Activez votre environnement: conda activate fitness_env")
        response = input("❓ Continuer quand même ? (y/N): ")
        if response.lower() != 'y':
            return
    
    success = start_streamlit()
    
    if success:
        print("✅ Streamlit lancé avec succès !")
    else:
        print("❌ Échec du lancement de Streamlit")

if __name__ == "__main__":
    main()