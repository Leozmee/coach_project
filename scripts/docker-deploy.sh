#!/bin/bash
# scripts/docker-deploy.sh - Script de déploiement Docker complet

set -e  # Arrêter en cas d'erreur

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

print_banner() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "🏋️  DÉPLOIEMENT DOCKER FITNESS COACH IA"
    echo "=============================================="
    echo -e "${NC}"
}

check_requirements() {
    echo_info "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        echo_error "Docker n'est pas installé!"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo_error "Docker Compose n'est pas installé!"
        exit 1
    fi
    
    # Vérifier l'espace disque (au moins 5GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    required_space=5242880  # 5GB en KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        echo_warning "Espace disque faible: $(($available_space/1024/1024))GB disponible, 5GB recommandé"
    fi
    
    echo_success "Prérequis vérifiés"
}

check_model() {
    echo_info "Vérification du modèle..."
    
    if [ ! -d "models/coach-sportif-french" ]; then
        echo_error "Modèle non trouvé dans models/coach-sportif-french/"
        echo_info "Déployez votre modèle avec: python scripts/deploy_model.py /path/to/your/model"
        exit 1
    fi
    
    # Vérifier les fichiers essentiels
    required_files=("config.json" "tokenizer_config.json" "vocab.json")
    for file in "${required_files[@]}"; do
        if [ ! -f "models/coach-sportif-french/$file" ]; then
            echo_error "Fichier manquant: models/coach-sportif-french/$file"
            exit 1
        fi
    done
    
    echo_success "Modèle validé"
}

create_directories() {
    echo_info "Création des répertoires..."
    
    mkdir -p logs nginx/ssl
    
    # Créer un fichier .env par défaut si il n'existe pas
    if [ ! -f ".env" ]; then
        echo_info "Création du fichier .env par défaut..."
        cat > .env << EOF
# Configuration Docker
PROJECT_NAME=Fitness Coach IA
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_TIMEOUT=30

# Streamlit Configuration
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# Modèle Configuration
MODEL_PATH=/app/models/coach-sportif-french
MODEL_DEVICE=auto
ENABLE_RAG=true

# YouTube API (optionnel)
YOUTUBE_API_KEY=

# Cache Configuration
ENABLE_CACHE=true
CACHE_TTL=3600
EOF
        echo_warning "Fichier .env créé. Ajoutez votre YOUTUBE_API_KEY si nécessaire."
    fi
    
    echo_success "Répertoires créés"
}

build_images() {
    echo_info "Construction des images Docker..."
    
    # Construire l'image API
    echo_info "🔨 Construction de l'image API..."
    docker build -f Dockerfile.api -t fitness-coach-api:latest .
    
    # Construire l'image Streamlit
    echo_info "🔨 Construction de l'image Streamlit..."
    docker build -f Dockerfile.streamlit -t fitness-coach-streamlit:latest .
    
    echo_success "Images construites avec succès"
}

deploy_stack() {
    echo_info "Déploiement de la stack Docker..."
    
    # Mode de déploiement
    if [ "$1" = "production" ]; then
        echo_info "🚀 Déploiement en mode PRODUCTION avec Nginx"
        docker-compose --profile production up -d
    else
        echo_info "🚀 Déploiement en mode DÉVELOPPEMENT"
        docker-compose up -d api streamlit
    fi
    
    echo_success "Stack déployée"
}

wait_for_services() {
    echo_info "Attente du démarrage des services..."
    
    # Attendre l'API
    echo_info "⏳ Attente de l'API..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/health &> /dev/null; then
            echo_success "API prête"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    # Attendre Streamlit
    echo_info "⏳ Attente de Streamlit..."
    for i in {1..30}; do
        if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
            echo_success "Streamlit prêt"
            break
        fi
        sleep 2
        echo -n "."
    done
}

show_status() {
    echo_info "État des services:"
    docker-compose ps
    
    echo ""
    echo_success "🎉 DÉPLOIEMENT TERMINÉ!"
    echo ""
    echo -e "${GREEN}📱 Interface Streamlit: ${BLUE}http://localhost:8501${NC}"
    echo -e "${GREEN}🔧 API Documentation: ${BLUE}http://localhost:8001/docs${NC}"
    echo -e "${GREEN}💚 Health Check API: ${BLUE}http://localhost:8001/health${NC}"
    
    if docker-compose ps | grep nginx &> /dev/null; then
        echo -e "${GREEN}🌐 Nginx Proxy: ${BLUE}http://localhost${NC}"
    fi
    
    echo ""
    echo_info "Commandes utiles:"
    echo "  • Voir les logs: docker-compose logs -f"
    echo "  • Arrêter: docker-compose down"
    echo "  • Redémarrer: docker-compose restart"
    echo "  • Mise à jour: $0 --rebuild"
}

cleanup() {
    echo_info "Nettoyage..."
    docker-compose down
    echo_success "Services arrêtés"
}

main() {
    print_banner
    
    case "${1:-deploy}" in
        "deploy")
            check_requirements
            check_model
            create_directories
            build_images
            deploy_stack "${2:-development}"
            wait_for_services
            show_status
            ;;
        "production")
            check_requirements
            check_model
            create_directories
            build_images
            deploy_stack "production"
            wait_for_services
            show_status
            ;;
        "rebuild")
            echo_info "Reconstruction et redéploiement..."
            cleanup
            build_images
            deploy_stack "${2:-development}"
            wait_for_services
            show_status
            ;;
        "stop")
            cleanup
            ;;
        "status")
            docker-compose ps
            ;;
        "logs")
            docker-compose logs -f "${2:-}"
            ;;
        *)
            echo "Usage: $0 [deploy|production|rebuild|stop|status|logs]"
            echo ""
            echo "Commandes:"
            echo "  deploy      - Déploiement standard (développement)"
            echo "  production  - Déploiement avec Nginx"
            echo "  rebuild     - Reconstruction des images et redéploiement"
            echo "  stop        - Arrêt des services"
            echo "  status      - État des containers"
            echo "  logs        - Affichage des logs"
            exit 1
            ;;
    esac
}

# Gestion des signaux pour cleanup
trap cleanup EXIT

# Exécution
main "$@"