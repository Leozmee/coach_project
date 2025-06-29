# 🏋️ Coach fitness IA 

Coach fitness intelligent basé sur DistilGPT-2 fine-tuné avec interface Streamlit.


# Option 1 : Déploiement Docker 

#### 1. Prérequis
- Docker et Docker Compose installés
- Votre modèle dans `models/coach-sportif-french/`

#### 2. Déploiement automatique
```bash
# Déploiement simple (API + Streamlit)
./scripts/docker-deploy.sh deploy

# Déploiement production avec Nginx
./scripts/docker-deploy.sh production
```

#### 3. Accéder à l'application
- Interface Streamlit: http://localhost:8501
- API Documentation: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

#### 4. Gestion des containers
```bash

./scripts/docker-deploy.sh status

./scripts/docker-deploy.sh logs

./scripts/docker-deploy.sh stop

./scripts/docker-deploy.sh rebuild
```


# Option 2 : Installation classique

#### 1. Installation
```bash
pip install -r requirements.txt
```

#### 2. Déployer votre modèle
```bash
python scripts/deploy_model.py /path/to/your/coach-sportif-french
```

#### 3. Lancer l'API
```bash
python scripts/start_api.py
```

#### 4. Lancer Streamlit (dans un autre terminal)
```bash
python scripts/start_streamlit.py
```

#### 5. Ouvrir l'application
- Streamlit: http://localhost:8501
- API Docs: http://localhost:8001/docs



## 📁 Structure

- `api/` - Backend FastAPI avec votre modèle
- `streamlit_app/` - Interface utilisateur Streamlit  
- `models/` - Votre modèle DistilGPT-2 fine-tuné
- `scripts/` - Scripts de démarrage 
- `nginx/` - Configuration reverse proxy (Docker)
- `Dockerfile.api` - Container API FastAPI
- `Dockerfile.streamlit` - Container interface Streamlit
- `docker-compose.yml` - Orchestration des services

## 🎯 Fonctionnalités

- Chat intelligent avec coach fitness
- Recherche d'exercices avec RAG
- Profils utilisateurs personnalisés
- Dashboard fitness interactif
- Réponses en français optimisées
- Recommandations de tutos vidéo
- Reconnaissance vocale avec Whisper
- Architecture multi-modèles (DistilGPT-2 + PlayPart AI)

