# scripts/setup_project.py - Script de création de la structure complète

import os
import sys
from pathlib import Path

def create_project_structure():
    """Crée la structure complète du projet Streamlit + API"""
    
    print("🏗️ CRÉATION STRUCTURE PROJET STREAMLIT FITNESS COACH")
    print("=" * 60)
    
    # Structure des dossiers
    directories = [
        "models/coach-sportif-french",
        "api",
        "streamlit_app/components",
        "streamlit_app/services", 
        "streamlit_app/utils",
        "scripts",
        "assets/images/fitness_icons",
        "assets/css",
        "assets/data",
        "config",
        "tests",
        "logs",
        "notebooks"
    ]
    
    # Créer tous les dossiers
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Créé: {directory}")
    
    # Fichiers __init__.py à créer
    init_files = [
        "api/__init__.py",
        "streamlit_app/__init__.py",
        "streamlit_app/components/__init__.py",
        "streamlit_app/services/__init__.py",
        "streamlit_app/utils/__init__.py",
        "config/__init__.py",
        "tests/__init__.py"
    ]
    
    # Créer les fichiers __init__.py
    for init_file in init_files:
        Path(init_file).touch()
        print(f"📄 Créé: {init_file}")
    
    # Créer .env
    env_content = """# Configuration générale
PROJECT_NAME=Fitness Coach IA
DEBUG=True
LOG_LEVEL=INFO

# API Configuration
API_HOST=127.0.0.1
API_PORT=8001
API_TIMEOUT=30

# Streamlit Configuration  
STREAMLIT_HOST=127.0.0.1
STREAMLIT_PORT=8501

# Modèle Configuration
MODEL_PATH=./models/coach-sportif-french
MODEL_DEVICE=auto

# Cache Configuration
ENABLE_CACHE=True
CACHE_TTL=3600
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    print("📄 Créé: .env")
    
    # Créer .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/*.log
*.log

# Models (trop lourds pour git)
models/*/
!models/.gitkeep

# Environment
.env
.env.local
.env.production

# Cache
.streamlit/
.cache/

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/

# Tests
.pytest_cache/
.coverage
htmlcov/
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("📄 Créé: .gitignore")
    
    # Créer requirements.txt principal
    main_requirements = """# Dépendances principales
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0

# IA et ML
torch>=2.0.0
transformers>=4.35.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0

# Data processing
numpy>=1.24.0
pandas>=2.0.0

# Utils
pydantic>=2.4.0
python-multipart>=0.0.6
aiofiles>=23.0.0

# Development
pytest>=7.4.0
black>=23.0.0
isort>=5.12.0
"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(main_requirements)
    print("📄 Créé: requirements.txt")
    
    # Créer README.md
    readme_content = """# 🏋️ Fitness Coach IA - Streamlit + API

Coach fitness intelligent basé sur DistilGPT-2 fine-tuné avec interface Streamlit.

## 🚀 Démarrage rapide

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Déployer votre modèle
```bash
python scripts/deploy_model.py /path/to/your/coach-sportif-french
```

### 3. Lancer l'API
```bash
python scripts/start_api.py
```

### 4. Lancer Streamlit (dans un autre terminal)
```bash
python scripts/start_streamlit.py
```

### 5. Ouvrir l'application
- Streamlit: http://localhost:8501
- API Docs: http://localhost:8001/docs

## 📁 Structure

- `api/` - Backend FastAPI avec votre modèle
- `streamlit_app/` - Interface utilisateur Streamlit  
- `models/` - Votre modèle DistilGPT-2 fine-tuné
- `scripts/` - Scripts de démarrage et utilitaires

## 🎯 Fonctionnalités

- Chat intelligent avec coach fitness
- Recherche d'exercices avec RAG
- Profils utilisateurs personnalisés
- Dashboard fitness interactif
- Réponses en français optimisées
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("📄 Créé: README.md")
    
    # Fichier de garde pour models/
    Path("models/.gitkeep").touch()
    
    print("\n🎉 STRUCTURE CRÉÉE AVEC SUCCÈS !")
    print("\n📋 PROCHAINES ÉTAPES:")
    print("1. Copier votre modèle: python scripts/deploy_model.py /path/to/your/model")
    print("2. Installer dépendances: pip install -r requirements.txt")
    print("3. Créer les fichiers de code (étapes suivantes)")

if __name__ == "__main__":
    create_project_structure()