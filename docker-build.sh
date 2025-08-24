#!/bin/bash
# Скрипт для быстрой сборки Docker контейнеров

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Быстрая сборка FACEIT Bot${NC}"

# Функция для отображения времени выполнения
timer() {
    if [[ $# -eq 0 ]]; then
        echo $(date '+%s')
    else
        local  stime=$1
        etime=$(date '+%s')
        if [[ -z "$stime" ]]; then stime=$etime; fi
        dt=$((etime - stime))
        ds=$((dt % 60))
        dm=$(((dt / 60) % 60))
        dh=$((dt / 3600))
        printf '%d:%02d:%02d' $dh $dm $ds
    fi
}

# Проверяем аргументы
FORCE_REBUILD=false
if [[ "$1" == "--force" || "$1" == "-f" ]]; then
    FORCE_REBUILD=true
    echo -e "${YELLOW}⚠️  Принудительная пересборка (без кеша)${NC}"
fi

# Засекаем время
start_time=$(timer)

echo -e "${GREEN}📊 Проверяем статус контейнеров...${NC}"
docker-compose ps

echo -e "${GREEN}🛑 Останавливаем существующие контейнеры...${NC}"
docker-compose down

if [[ "$FORCE_REBUILD" == true ]]; then
    echo -e "${YELLOW}🧹 Очищаем Docker кеш...${NC}"
    docker system prune -f
    docker-compose build --no-cache
else
    echo -e "${GREEN}⚡ Быстрая сборка с кешем...${NC}"
    docker-compose build
fi

echo -e "${GREEN}🚀 Запускаем контейнеры...${NC}"
docker-compose up -d

echo -e "${GREEN}📊 Статус сервисов:${NC}"
docker-compose ps

echo -e "${GREEN}📋 Логи запуска:${NC}"
docker-compose logs --tail=20

# Показываем время выполнения
end_time=$(timer $start_time)
echo -e "${GREEN}✅ Сборка завершена за: ${end_time}${NC}"

echo -e "${GREEN}🔗 Полезные команды:${NC}"
echo -e "  Логи бота:     ${YELLOW}docker-compose logs -f faceit-bot${NC}"
echo -e "  Перезапуск:    ${YELLOW}docker-compose restart faceit-bot${NC}"
echo -e "  Остановка:     ${YELLOW}docker-compose down${NC}"
echo -e "  Статус:        ${YELLOW}docker-compose ps${NC}"