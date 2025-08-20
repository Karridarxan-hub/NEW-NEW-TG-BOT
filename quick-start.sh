#!/bin/bash

# Quick Start Script для FACEIT CS2 Bot
# Использование: ./quick-start.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 FACEIT CS2 Bot - Quick Start${NC}"
echo "=================================="

# Проверка .env файла
if [[ ! -f ".env" ]]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создайте .env файл на основе .env.example и заполните API ключи${NC}"
    exit 1
fi

# Проверка обязательных переменных
source .env

if [[ "$BOT_TOKEN" == "your_telegram_bot_token_here" ]]; then
    echo -e "${RED}❌ BOT_TOKEN не настроен!${NC}"
    echo -e "${YELLOW}Получите токен у @BotFather и добавьте в .env${NC}"
    exit 1
fi

if [[ "$FACEIT_API_KEY" == "your_faceit_api_key_here" ]]; then
    echo -e "${RED}❌ FACEIT_API_KEY не настроен!${NC}"
    echo -e "${YELLOW}Получите ключ на https://developers.faceit.com и добавьте в .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Конфигурация проверена${NC}"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker готов к работе${NC}"

# Создание необходимых директорий
mkdir -p logs data

# Остановка старых контейнеров (если есть)
echo -e "${BLUE}🛑 Остановка старых контейнеров...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true

# Запуск бота
echo -e "${BLUE}▶️ Запуск FACEIT CS2 Bot...${NC}"
docker-compose up --build -d

# Ожидание запуска
echo -e "${BLUE}⏳ Ожидание запуска сервисов...${NC}"
sleep 10

# Проверка состояния
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}🎉 Бот успешно запущен!${NC}"
    echo ""
    echo "📊 Полезные команды:"
    echo "  docker-compose logs -f          # Просмотр логов"
    echo "  docker-compose ps               # Статус контейнеров"
    echo "  docker-compose down             # Остановка бота"
    echo "  curl http://localhost:8000/health # Проверка здоровья"
    echo ""
    echo "🌐 Доступные endpoints:"
    echo "  http://localhost:8000/health    # Health check"
    echo "  http://localhost:8000/docs      # API документация"
    echo "  http://localhost:8000/api/stats # Статистика бота"
    echo ""
    echo -e "${YELLOW}💡 Найдите вашего бота в Telegram и отправьте /start${NC}"
else
    echo -e "${RED}❌ Бот не отвечает на health check${NC}"
    echo "Проверьте логи: docker-compose logs -f"
    exit 1
fi