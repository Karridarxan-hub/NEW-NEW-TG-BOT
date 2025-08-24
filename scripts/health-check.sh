#!/bin/bash

# Скрипт проверки состояния FACEIT CS2 Бота
# Использование: ./health-check.sh [--detailed] [--json]

set -e

# Конфигурация
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TIMEOUT=10
PROJECT_NAME="faceit-cs2-bot"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Параметры
DETAILED=false
JSON_OUTPUT=false

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --detailed|-d)
            DETAILED=true
            shift
            ;;
        --json|-j)
            JSON_OUTPUT=true
            shift
            ;;
        --help|-h)
            echo "Использование: $0 [OPTIONS]"
            echo "OPTIONS:"
            echo "  --detailed, -d    Детальная проверка"
            echo "  --json, -j        Вывод в формате JSON"
            echo "  --help, -h        Показать справку"
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

# Функции для вывода
log_info() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${BLUE}ℹ️  $1${NC}"
    fi
}

log_success() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    fi
}

log_warning() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    fi
}

log_error() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Результаты проверок
declare -A results
overall_status="healthy"

# Проверка HTTP endpoint
check_http_endpoint() {
    log_info "Проверка HTTP endpoints..."
    
    # Основной endpoint
    if curl -f -s --max-time $TIMEOUT "$API_BASE_URL/" > /dev/null; then
        results["http_root"]="ok"
        log_success "Корневой endpoint доступен"
    else
        results["http_root"]="error"
        log_error "Корневой endpoint недоступен"
        overall_status="unhealthy"
    fi
    
    # Health check endpoint
    local health_response
    health_response=$(curl -f -s --max-time $TIMEOUT "$API_BASE_URL/health" 2>/dev/null || echo "error")
    
    if [[ "$health_response" != "error" ]]; then
        results["http_health"]="ok"
        log_success "Health check endpoint отвечает"
        
        # Парсинг ответа health check
        if command -v jq &> /dev/null; then
            local status
            status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
            results["health_status"]="$status"
            
            if [[ "$status" == "healthy" ]]; then
                log_success "Статус здоровья: healthy"
            else
                log_warning "Статус здоровья: $status"
                overall_status="degraded"
            fi
        fi
    else
        results["http_health"]="error"
        log_error "Health check endpoint недоступен"
        overall_status="unhealthy"
    fi
    
    # API endpoints (если детальная проверка)
    if [[ "$DETAILED" == "true" ]]; then
        # Проверка документации API
        if curl -f -s --max-time $TIMEOUT "$API_BASE_URL/docs" > /dev/null; then
            results["http_docs"]="ok"
            log_success "API документация доступна"
        else
            results["http_docs"]="error"
            log_warning "API документация недоступна"
        fi
        
        # Проверка статистики бота
        local stats_response
        stats_response=$(curl -f -s --max-time $TIMEOUT "$API_BASE_URL/api/stats" 2>/dev/null || echo "error")
        
        if [[ "$stats_response" != "error" ]]; then
            results["api_stats"]="ok"
            log_success "API статистики отвечает"
            
            if command -v jq &> /dev/null; then
                local total_users
                total_users=$(echo "$stats_response" | jq -r '.total_users' 2>/dev/null || echo "unknown")
                results["total_users"]="$total_users"
                log_info "Всего пользователей: $total_users"
            fi
        else
            results["api_stats"]="error"
            log_warning "API статистики недоступно"
        fi
    fi
}

# Проверка Docker контейнеров
check_docker_containers() {
    if command -v docker &> /dev/null; then
        log_info "Проверка Docker контейнеров..."
        
        # Проверка основного контейнера бота
        local bot_status
        bot_status=$(docker ps --filter "name=faceit.*bot" --format "{{.Status}}" 2>/dev/null | head -1)
        
        if [[ -n "$bot_status" && "$bot_status" =~ ^Up ]]; then
            results["docker_bot"]="ok"
            log_success "Docker контейнер бота запущен"
            
            # Получение времени работы
            local uptime
            uptime=$(echo "$bot_status" | sed 's/Up //' | sed 's/ (.*//')
            results["bot_uptime"]="$uptime"
            log_info "Время работы: $uptime"
        else
            results["docker_bot"]="error"
            log_error "Docker контейнер бота не запущен"
            overall_status="unhealthy"
        fi
        
        # Проверка Redis контейнера (если есть)
        local redis_status
        redis_status=$(docker ps --filter "name=.*redis" --format "{{.Status}}" 2>/dev/null | head -1)
        
        if [[ -n "$redis_status" && "$redis_status" =~ ^Up ]]; then
            results["docker_redis"]="ok"
            log_success "Redis контейнер запущен"
        elif [[ "$DETAILED" == "true" ]]; then
            results["docker_redis"]="not_found"
            log_info "Redis контейнер не найден (может не использоваться)"
        fi
        
        # Статистика использования ресурсов
        if [[ "$DETAILED" == "true" ]]; then
            local stats_output
            stats_output=$(docker stats --no-stream --format "{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "(faceit|bot)" | head -1)
            
            if [[ -n "$stats_output" ]]; then
                local cpu_usage
                local mem_usage
                cpu_usage=$(echo "$stats_output" | cut -f2)
                mem_usage=$(echo "$stats_output" | cut -f3)
                
                results["cpu_usage"]="$cpu_usage"
                results["memory_usage"]="$mem_usage"
                log_info "Использование CPU: $cpu_usage"
                log_info "Использование памяти: $mem_usage"
                
                # Проверка на высокое использование ресурсов
                local cpu_num
                cpu_num=$(echo "$cpu_usage" | sed 's/%//')
                if (( $(echo "$cpu_num > 80" | bc -l) 2>/dev/null )); then
                    log_warning "Высокое использование CPU: $cpu_usage"
                    if [[ "$overall_status" == "healthy" ]]; then
                        overall_status="degraded"
                    fi
                fi
            fi
        fi
    else
        results["docker"]="not_available"
        log_info "Docker не доступен для проверки"
    fi
}

# Проверка подключения к внешним API
check_external_apis() {
    if [[ "$DETAILED" == "true" ]]; then
        log_info "Проверка внешних API..."
        
        # Проверка FACEIT API (проверяем базовую доступность)
        faceit_response=$(curl -s --max-time $TIMEOUT "https://open.faceit.com/data/v4/players?nickname=test" 2>/dev/null | grep -o "You are not authorized" || echo "error")
        if [[ "$faceit_response" == "You are not authorized" ]]; then
            results["faceit_api"]="ok"
            log_success "FACEIT API доступно (требует авторизации)"
        else
            results["faceit_api"]="error"
            log_warning "FACEIT API недоступно"
            if [[ "$overall_status" == "healthy" ]]; then
                overall_status="degraded"
            fi
        fi
        
        # Проверка Telegram API
        if curl -f -s --max-time $TIMEOUT "https://api.telegram.org" > /dev/null; then
            results["telegram_api"]="ok"
            log_success "Telegram API доступно"
        else
            results["telegram_api"]="error"
            log_warning "Telegram API недоступно"
            if [[ "$overall_status" == "healthy" ]]; then
                overall_status="degraded"
            fi
        fi
    fi
}

# Проверка файловой системы
check_filesystem() {
    if [[ "$DETAILED" == "true" ]]; then
        log_info "Проверка файловой системы..."
        
        # Проверка места на диске
        local disk_usage
        disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
        results["disk_usage"]="${disk_usage}%"
        
        if (( disk_usage > 90 )); then
            log_warning "Мало места на диске: ${disk_usage}%"
            if [[ "$overall_status" == "healthy" ]]; then
                overall_status="degraded"
            fi
        else
            log_success "Место на диске: ${disk_usage}%"
        fi
        
        # Проверка директорий логов
        if [[ -d "logs" ]]; then
            local log_size
            log_size=$(du -sh logs 2>/dev/null | cut -f1 || echo "unknown")
            results["log_directory_size"]="$log_size"
            log_info "Размер директории логов: $log_size"
        fi
    fi
}

# Проверка портов
check_ports() {
    if [[ "$DETAILED" == "true" ]] && command -v netstat &> /dev/null; then
        log_info "Проверка портов..."
        
        # Проверка порта 8000 (FastAPI - внешний порт)
        if netstat -tlpn 2>/dev/null | grep -q ":8000 "; then
            results["port_8000"]="open"
            log_success "Порт 8000 открыт (FastAPI)"
        else
            results["port_8000"]="closed"
            log_warning "Порт 8000 закрыт"
        fi
        
        # Проверка порта 6380 (Redis внешний порт)
        if netstat -tlpn 2>/dev/null | grep -q ":6380 "; then
            results["port_6380"]="open"
            log_info "Порт 6380 открыт (Redis)"
        fi
        
        # Проверка порта 5432 (PostgreSQL)
        if netstat -tlpn 2>/dev/null | grep -q ":5432 "; then
            results["port_5432"]="open"
            log_info "Порт 5432 открыт (PostgreSQL)"
        fi
    fi
}

# Вывод результатов в JSON
output_json() {
    cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "overall_status": "$overall_status",
  "checks": {
EOF

    local first=true
    for key in "${!results[@]}"; do
        if [[ "$first" != "true" ]]; then
            echo ","
        fi
        echo -n "    \"$key\": \"${results[$key]}\""
        first=false
    done

    cat << EOF

  }
}
EOF
}

# Основная функция
main() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${BLUE}🏥 Health Check для $PROJECT_NAME${NC}"
        echo "=================================="
    fi
    
    # Выполнение проверок
    check_http_endpoint
    check_docker_containers
    check_external_apis
    check_filesystem
    check_ports
    
    # Вывод результатов
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        output_json
    else
        echo
        echo "=================================="
        case "$overall_status" in
            "healthy")
                echo -e "${GREEN}🎉 Общий статус: ЗДОРОВ${NC}"
                exit 0
                ;;
            "degraded")
                echo -e "${YELLOW}⚠️  Общий статус: УХУДШЕН${NC}"
                exit 1
                ;;
            "unhealthy")
                echo -e "${RED}💀 Общий статус: НЕЗДОРОВ${NC}"
                exit 2
                ;;
        esac
    fi
}

# Запуск
main "$@"