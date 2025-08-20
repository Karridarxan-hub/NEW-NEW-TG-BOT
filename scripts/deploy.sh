#!/bin/bash

# Скрипт развертывания FACEIT CS2 Бота
# Использование: ./deploy.sh [dev|prod] [--rebuild]

set -e

# Конфигурация
PROJECT_NAME="faceit-cs2-bot"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME-deploy.log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Проверка аргументов
ENVIRONMENT=${1:-"dev"}
REBUILD=${2:-""}

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    error "Неверная среда развертывания. Используйте: dev или prod"
fi

log "🚀 Начало развертывания в среде: $ENVIRONMENT"

# Проверка требований
check_requirements() {
    log "🔍 Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен"
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен"
    fi
    
    # Проверка прав
    if ! docker info &> /dev/null; then
        error "Нет прав для работы с Docker"
    fi
    
    log "✅ Системные требования выполнены"
}

# Создание резервной копии
create_backup() {
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        log "💾 Создание резервной копии..."
        
        mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        
        tar -czf "$BACKUP_FILE" \
            --exclude='logs' \
            --exclude='data' \
            --exclude='.git' \
            . || warn "Не удалось создать полную резервную копию"
        
        log "✅ Резервная копия создана: $BACKUP_FILE"
    fi
}

# Проверка конфигурации
check_config() {
    log "⚙️ Проверка конфигурации..."
    
    if [[ ! -f ".env" ]]; then
        error "Файл .env не найден. Создайте его на основе .env.example"
    fi
    
    # Проверка обязательных переменных
    source .env
    
    if [[ -z "$BOT_TOKEN" ]]; then
        error "BOT_TOKEN не установлен в .env"
    fi
    
    if [[ -z "$FACEIT_API_KEY" ]]; then
        error "FACEIT_API_KEY не установлен в .env"
    fi
    
    # Проверка валидности токена (базовая)
    if [[ ${#BOT_TOKEN} -lt 40 ]]; then
        warn "BOT_TOKEN может быть невалидным (слишком короткий)"
    fi
    
    if [[ ${#FACEIT_API_KEY} -lt 30 ]]; then
        warn "FACEIT_API_KEY может быть невалидным (слишком короткий)"
    fi
    
    log "✅ Конфигурация проверена"
}

# Остановка старых контейнеров
stop_services() {
    log "🛑 Остановка существующих сервисов..."
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans || true
    else
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans || true
    fi
    
    log "✅ Сервисы остановлены"
}

# Сборка образов
build_images() {
    log "🔨 Сборка Docker образов..."
    
    BUILD_ARGS=""
    if [[ "$REBUILD" == "--rebuild" ]]; then
        BUILD_ARGS="--no-cache"
        log "🔄 Принудительная пересборка образов"
    fi
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build $BUILD_ARGS
    else
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build $BUILD_ARGS
    fi
    
    log "✅ Образы собраны"
}

# Запуск сервисов
start_services() {
    log "▶️ Запуск сервисов..."
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    fi
    
    log "✅ Сервисы запущены"
}

# Проверка здоровья
health_check() {
    log "🏥 Проверка состояния сервисов..."
    
    # Ждем запуска
    sleep 30
    
    # Проверка Docker контейнеров
    if ! docker-compose ps | grep -q "Up"; then
        error "Контейнеры не запустились"
    fi
    
    # Проверка HTTP endpoint
    MAX_ATTEMPTS=12  # 2 минуты
    ATTEMPT=1
    
    while [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; do
        info "Попытка $ATTEMPT/$MAX_ATTEMPTS: проверка /health endpoint..."
        
        if curl -f -s http://localhost:8000/health > /dev/null; then
            log "✅ Сервис готов к работе"
            return 0
        fi
        
        sleep 10
        ((ATTEMPT++))
    done
    
    error "Сервис не отвечает на health check"
}

# Показ статуса
show_status() {
    log "📊 Статус развертывания:"
    echo
    
    # Статус контейнеров
    echo "Docker контейнеры:"
    docker-compose ps
    echo
    
    # Использование ресурсов
    echo "Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo
    
    # Логи (последние 10 строк)
    echo "Последние логи:"
    docker-compose logs --tail=10 faceit-bot
    echo
    
    # Endpoints
    echo "Доступные endpoints:"
    echo "- Health check: http://localhost:8000/health"
    echo "- API docs: http://localhost:8000/docs"
    echo "- Metrics: http://localhost:8000/metrics (если включены)"
    echo
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        echo "🌐 Продакшен развертывание завершено!"
        echo "Не забудьте:"
        echo "- Настроить SSL сертификаты"
        echo "- Настроить мониторинг"
        echo "- Настроить резервное копирование"
    else
        echo "🛠️ Development развертывание завершено!"
        echo "- Логи: docker-compose logs -f"
        echo "- Перезапуск: docker-compose restart"
    fi
}

# Очистка при ошибке
cleanup_on_error() {
    error "❌ Развертывание не удалось"
    warn "Выполнение отката..."
    
    # Остановка проблемных контейнеров
    docker-compose down --remove-orphans || true
    
    # Восстановление из бэкапа (для продакшена)
    if [[ "$ENVIRONMENT" == "prod" && -n "$BACKUP_FILE" ]]; then
        warn "Восстановление из резервной копии: $BACKUP_FILE"
        # Здесь можно добавить логику восстановления
    fi
    
    exit 1
}

# Обработчик сигналов
trap cleanup_on_error ERR

# Основная логика развертывания
main() {
    log "🎯 Развертывание $PROJECT_NAME в среде $ENVIRONMENT"
    
    check_requirements
    check_config
    create_backup
    stop_services
    build_images
    start_services
    health_check
    show_status
    
    log "🎉 Развертывание успешно завершено!"
    
    # Отправка уведомления (опционально)
    if command -v curl &> /dev/null && [[ -n "${WEBHOOK_DEPLOY_URL:-}" ]]; then
        curl -X POST "$WEBHOOK_DEPLOY_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"✅ $PROJECT_NAME развернут в $ENVIRONMENT\"}" \
            || warn "Не удалось отправить уведомление о развертывании"
    fi
}

# Функция помощи
show_help() {
    echo "Использование: $0 [ENVIRONMENT] [OPTIONS]"
    echo
    echo "ENVIRONMENT:"
    echo "  dev     Развертывание в среде разработки (по умолчанию)"
    echo "  prod    Развертывание в продакшене"
    echo
    echo "OPTIONS:"
    echo "  --rebuild  Принудительная пересборка Docker образов"
    echo "  --help     Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 dev                # Развертывание в dev"
    echo "  $0 prod --rebuild     # Продакшен с пересборкой"
    echo
}

# Проверка аргументов
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Запуск основной функции
main "$@"