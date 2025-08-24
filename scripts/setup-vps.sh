#!/bin/bash

# 🖥️ FACEIT CS2 Bot - VPS Setup Script
# Автоматическая подготовка ВПС для GitHub Actions деплоя

set -e

# Конфигурация
PROJECT_NAME="faceit-cs2-bot"
DEPLOY_PATH="/opt/faceit-bot"
BACKUP_DIR="/opt/backups"
USER_NAME="faceit"
REPO_URL="https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT.git"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Проверка прав администратора
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Скрипт должен быть запущен с правами root (sudo)"
    fi
    log "✅ Права администратора подтверждены"
}

# Обновление системы
update_system() {
    log "🔄 Обновление системы..."
    apt update && apt upgrade -y
    apt install -y curl git wget unzip software-properties-common
    log "✅ Система обновлена"
}

# Установка Docker
install_docker() {
    log "🐳 Установка Docker..."
    
    if command -v docker &> /dev/null; then
        log "✅ Docker уже установлен"
        return
    fi
    
    # Удаление старых версий
    apt remove -y docker docker-engine docker.io containerd runc || true
    
    # Установка Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Добавление пользователя в группу docker
    if [[ -n "$SUDO_USER" ]]; then
        usermod -aG docker "$SUDO_USER"
        log "✅ Пользователь $SUDO_USER добавлен в группу docker"
    fi
    
    # Запуск Docker
    systemctl enable docker
    systemctl start docker
    
    log "✅ Docker установлен и запущен"
}

# Установка Docker Compose
install_docker_compose() {
    log "📦 Установка Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log "✅ Docker Compose уже установлен"
        return
    fi
    
    # Установка через pip для совместимости
    apt install -y python3-pip
    pip3 install docker-compose
    
    # Альтернативная установка если pip не работает
    if ! command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
        curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log "✅ Docker Compose установлен"
}

# Создание пользователя для деплоя
create_deploy_user() {
    log "👤 Создание пользователя для деплоя..."
    
    if id "$USER_NAME" &>/dev/null; then
        log "✅ Пользователь $USER_NAME уже существует"
        return
    fi
    
    # Создание пользователя
    useradd -m -s /bin/bash -G docker "$USER_NAME"
    
    # Настройка sudo без пароля для деплоя
    echo "$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose, /bin/systemctl" > "/etc/sudoers.d/$USER_NAME"
    
    log "✅ Пользователь $USER_NAME создан"
}

# Настройка директорий
setup_directories() {
    log "📁 Настройка директорий..."
    
    # Создание основной директории
    mkdir -p "$DEPLOY_PATH"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/var/log/$PROJECT_NAME"
    
    # Установка прав
    chown -R "$USER_NAME:$USER_NAME" "$DEPLOY_PATH"
    chown -R "$USER_NAME:$USER_NAME" "$BACKUP_DIR"
    chmod 755 "$DEPLOY_PATH"
    chmod 755 "$BACKUP_DIR"
    
    log "✅ Директории настроены"
}

# Клонирование репозитория
clone_repository() {
    log "📥 Клонирование репозитория..."
    
    if [[ -d "$DEPLOY_PATH/.git" ]]; then
        log "✅ Репозиторий уже существует"
        return
    fi
    
    # Клонирование от имени пользователя деплоя
    sudo -u "$USER_NAME" git clone "$REPO_URL" "$DEPLOY_PATH"
    
    # Переход в рабочую директорию
    cd "$DEPLOY_PATH"
    
    # Настройка Git
    sudo -u "$USER_NAME" git config user.name "VPS Deploy"
    sudo -u "$USER_NAME" git config user.email "deploy@vps"
    
    log "✅ Репозиторий склонирован"
}

# Настройка SSH для GitHub Actions
setup_ssh() {
    log "🔑 Настройка SSH..."
    
    SSH_DIR="/home/$USER_NAME/.ssh"
    sudo -u "$USER_NAME" mkdir -p "$SSH_DIR"
    sudo -u "$USER_NAME" chmod 700 "$SSH_DIR"
    
    # Создание authorized_keys если не существует
    AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
    if [[ ! -f "$AUTHORIZED_KEYS" ]]; then
        sudo -u "$USER_NAME" touch "$AUTHORIZED_KEYS"
        sudo -u "$USER_NAME" chmod 600 "$AUTHORIZED_KEYS"
    fi
    
    info "📋 SSH настроен. Для GitHub Actions нужно:"
    info "   1. Добавить публичный ключ в $AUTHORIZED_KEYS"
    info "   2. Настроить GitHub Secrets (см. инструкцию)"
    
    log "✅ SSH настроен"
}

# Настройка firewall
setup_firewall() {
    log "🔥 Настройка firewall..."
    
    # Установка ufw если не установлен
    apt install -y ufw
    
    # Базовые правила
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH
    ufw allow ssh
    
    # HTTP/HTTPS (если планируется)
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Docker API (внутренний)
    ufw allow 8000/tcp
    
    # Активация (с подтверждением)
    echo "y" | ufw enable
    
    log "✅ Firewall настроен"
}

# Настройка логирования
setup_logging() {
    log "📝 Настройка логирования..."
    
    # Logrotate для логов проекта
    cat > "/etc/logrotate.d/$PROJECT_NAME" << EOF
/var/log/$PROJECT_NAME/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        docker-compose -f $DEPLOY_PATH/docker-compose.yml restart faceit-bot || true
    endscript
}
EOF
    
    # Настройка журналирования Docker
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    }
}
EOF
    
    systemctl restart docker
    
    log "✅ Логирование настроено"
}

# Создание systemd сервиса
create_systemd_service() {
    log "⚙️ Создание systemd сервиса..."
    
    cat > "/etc/systemd/system/$PROJECT_NAME.service" << EOF
[Unit]
Description=FACEIT CS2 Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_PATH
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$USER_NAME
Group=$USER_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$PROJECT_NAME.service"
    
    log "✅ Systemd сервис создан"
}

# Проверка установки
verify_installation() {
    log "🔍 Проверка установки..."
    
    # Проверка Docker
    if ! docker --version; then
        error "Docker не установлен корректно"
    fi
    
    # Проверка Docker Compose
    if ! docker-compose --version; then
        error "Docker Compose не установлен корректно"
    fi
    
    # Проверка пользователя
    if ! id "$USER_NAME" &>/dev/null; then
        error "Пользователь $USER_NAME не создан"
    fi
    
    # Проверка директорий
    if [[ ! -d "$DEPLOY_PATH" ]]; then
        error "Директория деплоя не создана"
    fi
    
    # Проверка репозитория
    if [[ ! -d "$DEPLOY_PATH/.git" ]]; then
        error "Репозиторий не склонирован"
    fi
    
    log "✅ Все проверки пройдены"
}

# Показ итоговой информации
show_summary() {
    log "📋 Настройка завершена!"
    echo
    echo -e "${BLUE}=== ИНФОРМАЦИЯ О НАСТРОЙКЕ ===${NC}"
    echo -e "${GREEN}Пользователь деплоя:${NC} $USER_NAME"
    echo -e "${GREEN}Путь деплоя:${NC} $DEPLOY_PATH"
    echo -e "${GREEN}Бэкапы:${NC} $BACKUP_DIR"
    echo -e "${GREEN}Логи:${NC} /var/log/$PROJECT_NAME"
    echo
    echo -e "${YELLOW}=== СЛЕДУЮЩИЕ ШАГИ ===${NC}"
    echo "1. Настройте GitHub Secrets в репозитории:"
    echo "   - VPS_HOST: IP адрес или домен ВПС"
    echo "   - VPS_USER: $USER_NAME"
    echo "   - VPS_PORT: 22 (или ваш SSH порт)"
    echo "   - VPS_SSH_KEY: приватный SSH ключ"
    echo
    echo "2. Добавьте публичный SSH ключ в authorized_keys:"
    echo "   sudo -u $USER_NAME nano /home/$USER_NAME/.ssh/authorized_keys"
    echo
    echo "3. Протестируйте деплой:"
    echo "   git push origin master"
    echo
    echo -e "${GREEN}🎉 ВПС готов для автоматического деплоя через GitHub Actions!${NC}"
}

# Основная функция
main() {
    log "🚀 Начало настройки ВПС для GitHub Actions деплоя"
    
    check_root
    update_system
    install_docker
    install_docker_compose
    create_deploy_user
    setup_directories
    clone_repository
    setup_ssh
    setup_firewall
    setup_logging
    create_systemd_service
    verify_installation
    show_summary
    
    log "🎉 Настройка ВПС завершена успешно!"
}

# Запуск скрипта
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi