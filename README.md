# 🏋️ Fitness Coach IA - Streamlit + API

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
- `scripts/` - Scripts de démarrage 

## 🎯 Fonctionnalités

- Chat intelligent avec coach fitness
- Recherche d'exercices avec RAG
- Profils utilisateurs personnalisés
- Dashboard fitness interactif
- Réponses en français optimisées
- Recommandations de tutos vidéo
