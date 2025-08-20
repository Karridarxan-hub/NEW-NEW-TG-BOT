#!/bin/bash

# Скрипт резервного копирования FACEIT CS2 Бота
# Использование: ./backup.sh [--full] [--config-only] [--retention-days N]

set -e

# Конфигурация
PROJECT_NAME="faceit-cs2-bot"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_BASE_DIR="${BACKUP_DIR:-/opt/backups/$PROJECT_NAME}"
DEFAULT_RETENTION_DAYS=30

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Параметры
BACKUP_TYPE="standard"
RETENTION_DAYS=$DEFAULT_RETENTION_DAYS

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --full|-f)
            BACKUP_TYPE="full"
            shift
            ;;
        --config-only|-c)
            BACKUP_TYPE="config"
            shift
            ;;
        --retention-days|-r)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --help|-h)
            cat << EOF
Использование: $0 [OPTIONS]

OPTIONS:
  --full, -f                Полное резервное копирование (включая логи и данные)
  --config-only, -c         Копирование только конфигурационных файлов
  --retention-days N, -r N  Количество дней хранения backup'ов (по умолчанию: $DEFAULT_RETENTION_DAYS)
  --help, -h                Показать справку

Типы backup'ов:
  standard     Стандартное копирование (код, конфигурация, без логов)
  full         Полное копирование (все файлы включая логи и данные)
  config       Только конфигурационные файлы

Примеры:
  $0                        # Стандартное копирование
  $0 --full                 # Полное копирование
  $0 --config-only          # Только конфигурация
  $0 --retention-days 7     # Хранить backup'ы 7 дней
EOF
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

# Функции для логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Создание директорий для backup
setup_backup_dir() {
    log "📁 Настройка директорий для backup..."
    
    mkdir -p "$BACKUP_BASE_DIR"
    
    if [[ ! -w "$BACKUP_BASE_DIR" ]]; then
        error "Нет прав записи в директорию backup: $BACKUP_BASE_DIR"
    fi
    
    log "✅ Директория backup готова: $BACKUP_BASE_DIR"
}

# Получение информации о проекте
get_project_info() {
    log "📊 Сбор информации о проекте..."
    
    # Текущий коммит Git (если доступен)
    if [[ -d "$PROJECT_DIR/.git" ]] && command -v git &> /dev/null; then
        GIT_COMMIT=$(cd "$PROJECT_DIR" && git rev-parse HEAD 2>/dev/null || echo "unknown")
        GIT_BRANCH=$(cd "$PROJECT_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        info "Git commit: $GIT_COMMIT"
        info "Git branch: $GIT_BRANCH"
    else
        GIT_COMMIT="unknown"
        GIT_BRANCH="unknown"
    fi
    
    # Статус Docker контейнеров
    if command -v docker &> /dev/null; then
        CONTAINER_STATUS=$(docker ps --filter "name=faceit.*bot" --format "{{.Names}}: {{.Status}}" 2>/dev/null || echo "not running")
        info "Container status: $CONTAINER_STATUS"
    else
        CONTAINER_STATUS="docker not available"
    fi
}

# Создание метаданных backup
create_backup_metadata() {
    local backup_dir="$1"
    local metadata_file="$backup_dir/backup_metadata.json"
    
    log "📝 Создание метаданных backup..."
    
    cat > "$metadata_file" << EOF
{
  "backup_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "type": "$BACKUP_TYPE",
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "project_dir": "$PROJECT_DIR"
  },
  "git_info": {
    "commit": "$GIT_COMMIT",
    "branch": "$GIT_BRANCH"
  },
  "system_info": {
    "os": "$(uname -s)",
    "arch": "$(uname -m)",
    "container_status": "$CONTAINER_STATUS"
  },
  "backup_contents": {
    "config_files": true,
    "source_code": $([ "$BACKUP_TYPE" != "config" ] && echo "true" || echo "false"),
    "logs": $([ "$BACKUP_TYPE" == "full" ] && echo "true" || echo "false"),
    "data": $([ "$BACKUP_TYPE" == "full" ] && echo "true" || echo "false")
  }
}
EOF
    
    log "✅ Метаданные созданы: $metadata_file"
}

# Копирование конфигурационных файлов
backup_config() {
    local backup_dir="$1"
    
    log "⚙️ Копирование конфигурационных файлов..."
    
    # Основные конфигурационные файлы
    local config_files=(
        ".env"
        ".env.example"
        "docker-compose.yml"
        "docker-compose.dev.yml"
        "docker-compose.prod.yml"
        "Dockerfile"
        "Dockerfile.dev"
        "requirements.txt"
        "config.py"
    )
    
    mkdir -p "$backup_dir/config"
    
    for file in "${config_files[@]}"; do
        if [[ -f "$PROJECT_DIR/$file" ]]; then
            cp "$PROJECT_DIR/$file" "$backup_dir/config/"
            info "Скопирован: $file"
        else
            warn "Файл не найден: $file"
        fi
    done
    
    # Nginx конфигурация (если есть)
    if [[ -d "$PROJECT_DIR/nginx" ]]; then
        cp -r "$PROJECT_DIR/nginx" "$backup_dir/config/"
        info "Скопирована директория nginx"
    fi
    
    # Скрипты
    if [[ -d "$PROJECT_DIR/scripts" ]]; then
        cp -r "$PROJECT_DIR/scripts" "$backup_dir/"
        info "Скопирована директория scripts"
    fi
    
    log "✅ Конфигурационные файлы скопированы"
}

# Копирование исходного кода
backup_source() {
    local backup_dir="$1"
    
    if [[ "$BACKUP_TYPE" == "config" ]]; then
        return 0
    fi
    
    log "📦 Копирование исходного кода..."
    
    # Исходные файлы Python
    local source_files=(
        "main.py"
        "storage.py"
        "faceit_client.py"
        "keyboards.py"
        "bot_handlers.py"
        "match_handlers.py"
        "history_handlers.py"
        "additional_handlers.py"
        "test_bot.py"
    )
    
    mkdir -p "$backup_dir/src"
    
    for file in "${source_files[@]}"; do
        if [[ -f "$PROJECT_DIR/$file" ]]; then
            cp "$PROJECT_DIR/$file" "$backup_dir/src/"
            info "Скопирован: $file"
        else
            warn "Исходный файл не найден: $file"
        fi
    done
    
    # Документация
    local doc_files=(
        "README.md"
        "ARCHITECTURE.md"
        "DEPLOYMENT.md"
        "API.md"
        "TECHNICAL_GUIDE.md"
    )
    
    mkdir -p "$backup_dir/docs"
    
    for file in "${doc_files[@]}"; do
        if [[ -f "$PROJECT_DIR/$file" ]]; then
            cp "$PROJECT_DIR/$file" "$backup_dir/docs/"
            info "Скопирован: $file"
        fi
    done
    
    log "✅ Исходный код скопирован"
}

# Копирование данных и логов
backup_data() {
    local backup_dir="$1"
    
    if [[ "$BACKUP_TYPE" != "full" ]]; then
        return 0
    fi
    
    log "🗄️ Копирование данных и логов..."
    
    # Логи
    if [[ -d "$PROJECT_DIR/logs" ]]; then
        cp -r "$PROJECT_DIR/logs" "$backup_dir/"
        local log_size
        log_size=$(du -sh "$backup_dir/logs" 2>/dev/null | cut -f1 || echo "unknown")
        info "Скопированы логи (размер: $log_size)"
    else
        warn "Директория логов не найдена"
    fi
    
    # Пользовательские данные
    if [[ -d "$PROJECT_DIR/data" ]]; then
        cp -r "$PROJECT_DIR/data" "$backup_dir/"
        info "Скопированы пользовательские данные"
    fi
    
    # Экспорт данных Docker volumes (если возможно)
    if command -v docker &> /dev/null && docker volume ls | grep -q "$PROJECT_NAME"; then
        log "📦 Экспорт Docker volumes..."
        mkdir -p "$backup_dir/volumes"
        
        # Попытка экспорта volumes
        docker run --rm -v "${PROJECT_NAME}_redis_data:/data" -v "$backup_dir/volumes:/backup" alpine tar czf /backup/redis_data.tar.gz -C /data . 2>/dev/null || warn "Не удалось экспортировать Redis volume"
    fi
    
    log "✅ Данные и логи скопированы"
}

# Сжатие backup
compress_backup() {
    local backup_dir="$1"
    local timestamp="$2"
    
    log "🗜️ Сжатие backup..."
    
    local backup_archive="$BACKUP_BASE_DIR/${PROJECT_NAME}_${BACKUP_TYPE}_${timestamp}.tar.gz"
    
    cd "$BACKUP_BASE_DIR"
    tar -czf "$backup_archive" -C "$(dirname "$backup_dir")" "$(basename "$backup_dir")"
    
    # Удаление временной директории
    rm -rf "$backup_dir"
    
    # Проверка целостности архива
    if tar -tzf "$backup_archive" > /dev/null 2>&1; then
        local archive_size
        archive_size=$(du -sh "$backup_archive" | cut -f1)
        log "✅ Backup сжат: $backup_archive (размер: $archive_size)"
        echo "$backup_archive"
    else
        error "Ошибка при создании архива backup"
    fi
}

# Очистка старых backup'ов
cleanup_old_backups() {
    log "🧹 Очистка старых backup'ов (старше $RETENTION_DAYS дней)..."
    
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        return 0
    fi
    
    local deleted_count=0
    
    # Поиск и удаление старых файлов
    while IFS= read -r -d '' file; do
        rm "$file"
        info "Удален старый backup: $(basename "$file")"
        ((deleted_count++))
    done < <(find "$BACKUP_BASE_DIR" -name "${PROJECT_NAME}_*.tar.gz" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $deleted_count -gt 0 ]]; then
        log "✅ Удалено старых backup'ов: $deleted_count"
    else
        info "Старые backup'ы не найдены"
    fi
}

# Отправка уведомления
send_notification() {
    local backup_file="$1"
    local backup_size
    backup_size=$(du -sh "$backup_file" | cut -f1)
    
    # Webhook уведомление (если настроено)
    if [[ -n "${BACKUP_WEBHOOK_URL:-}" ]] && command -v curl &> /dev/null; then
        local notification_data
        notification_data=$(cat << EOF
{
  "text": "✅ Backup завершен",
  "attachments": [
    {
      "color": "good",
      "fields": [
        {
          "title": "Проект",
          "value": "$PROJECT_NAME",
          "short": true
        },
        {
          "title": "Тип",
          "value": "$BACKUP_TYPE",
          "short": true
        },
        {
          "title": "Размер",
          "value": "$backup_size",
          "short": true
        },
        {
          "title": "Файл",
          "value": "$(basename "$backup_file")",
          "short": false
        }
      ]
    }
  ]
}
EOF
        )
        
        if curl -X POST "$BACKUP_WEBHOOK_URL" \
               -H "Content-Type: application/json" \
               -d "$notification_data" \
               --silent --show-error > /dev/null; then
            info "Уведомление отправлено"
        else
            warn "Не удалось отправить уведомление"
        fi
    fi
}

# Основная функция
main() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    
    log "🚀 Начало резервного копирования ($BACKUP_TYPE)"
    log "📅 Timestamp: $timestamp"
    log "📂 Проект: $PROJECT_DIR"
    log "💾 Backup директория: $BACKUP_BASE_DIR"
    
    # Проверка директории проекта
    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Директория проекта не найдена: $PROJECT_DIR"
    fi
    
    setup_backup_dir
    get_project_info
    
    # Создание временной директории для backup
    local temp_backup_dir
    temp_backup_dir=$(mktemp -d "$BACKUP_BASE_DIR/tmp_backup_XXXXXX")
    
    create_backup_metadata "$temp_backup_dir"
    backup_config "$temp_backup_dir"
    backup_source "$temp_backup_dir"
    backup_data "$temp_backup_dir"
    
    local backup_archive
    backup_archive=$(compress_backup "$temp_backup_dir" "$timestamp")
    
    cleanup_old_backups
    send_notification "$backup_archive"
    
    log "🎉 Резервное копирование завершено успешно!"
    log "📦 Архив: $backup_archive"
    
    # Вывод информации о backup'е
    if command -v tar &> /dev/null; then
        echo
        info "Содержимое backup'а:"
        tar -tzf "$backup_archive" | head -20
        if [[ $(tar -tzf "$backup_archive" | wc -l) -gt 20 ]]; then
            info "... и еще $(( $(tar -tzf "$backup_archive" | wc -l) - 20 )) файлов"
        fi
    fi
}

# Обработка прерывания
cleanup_on_interrupt() {
    warn "Backup прерван пользователем"
    # Очистка временных файлов
    if [[ -n "${temp_backup_dir:-}" && -d "$temp_backup_dir" ]]; then
        rm -rf "$temp_backup_dir"
    fi
    exit 130
}

trap cleanup_on_interrupt INT TERM

# Запуск
main "$@"