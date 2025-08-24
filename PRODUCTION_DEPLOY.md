# 🚀 FACEIT CS2 Bot - Production Deploy Guide

## 📋 Инструкции по развертыванию на ВПС

### ✅ Готово к деплою:
- **Версия**: v2.1.3 с системой воркеров
- **Репозиторий**: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT.git
- **Боевой токен**: Настроен ✓
- **Производительность**: 8 воркеров, 3-5x ускорение

---

## 🖥️ ШАГИ РАЗВЕРТЫВАНИЯ НА ВПС

### 1. Подготовка ВПС

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose -y

# Проверка установки
docker --version
docker-compose --version
```

### 2. Клонирование репозитория

```bash
# Переход в рабочую директорию
cd /opt

# Клонирование продакшн репозитория
sudo git clone https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT.git faceit-bot
cd faceit-bot

# Установка прав
sudo chown -R $USER:$USER /opt/faceit-bot
```

### 3. Настройка окружения

```bash
# Копирование production конфига
cp .env.production .env

# Проверка настроек (токен уже настроен)
cat .env

# При необходимости редактирование
nano .env
```

### 4. Развертывание в продакшене

```bash
# Сделать скрипт исполняемым
chmod +x scripts/deploy.sh

# Запуск продакшн деплоя с пересборкой
./scripts/deploy.sh prod --rebuild
```

### 5. Проверка работоспособности

```bash
# Проверка статуса контейнеров
docker-compose ps

# Проверка логов бота
docker-compose logs -f faceit-bot

# Проверка API
curl http://localhost:8000/health

# Проверка воркеров в логах
docker-compose logs faceit-bot | grep "воркер"
```

---

## ⚙️ CONFIGURATION

### Настройки производительности (уже настроены в .env):

```bash
# Количество воркеров для разных задач
STATS_WORKERS=3          # Анализ статистики
HISTORY_WORKERS=2        # История матчей  
COMPARISON_WORKERS=2     # Сравнения игроков
NOTIFICATION_WORKERS=1   # Уведомления

# Производительность API
CONCURRENT_REQUESTS=5    # Одновременных запросов к FACEIT
BATCH_SIZE=10           # Размер batch обработки
MAX_QUEUE_SIZE=1000     # Максимальный размер очередей
WORKER_TIMEOUT=30       # Таймаут воркеров (секунды)
```

### Мониторинг ресурсов:

```bash
# Использование ресурсов контейнерами
docker stats

# Логи воркеров в реальном времени
docker-compose logs -f faceit-bot | grep -E "(worker|воркер|Worker)"

# Проверка очередей (в логах бота)
docker-compose logs faceit-bot | grep -E "(queue|очеред)"
```

---

## 🔄 УПРАВЛЕНИЕ

### Команды управления:

```bash
# Перезапуск бота
docker-compose restart faceit-bot

# Полная остановка
docker-compose down

# Запуск после остановки  
docker-compose up -d

# Обновление кода (pull из Git)
git pull origin master
./scripts/deploy.sh prod --rebuild
```

### Резервное копирование:

```bash
# Создание backup
sudo tar -czf /opt/backups/faceit-bot-$(date +%Y%m%d).tar.gz \
  --exclude='logs' --exclude='.git' /opt/faceit-bot

# Backup базы данных
docker-compose exec postgres pg_dump -U faceit_user faceit_bot > backup.sql
```

---

## 🚨 TROUBLESHOOTING

### Общие проблемы:

1. **Бот не отвечает**:
   ```bash
   # Проверить логи
   docker-compose logs faceit-bot
   
   # Перезапустить
   docker-compose restart faceit-bot
   ```

2. **Ошибки воркеров**:
   ```bash
   # Проверить статус воркеров в логах
   docker-compose logs faceit-bot | grep -i error
   
   # Уменьшить нагрузку (в .env):
   CONCURRENT_REQUESTS=3
   STATS_WORKERS=2
   ```

3. **Проблемы с FACEIT API**:
   ```bash
   # Проверить API ключ
   grep FACEIT_API_KEY .env
   
   # Тестировать подключение
   curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://open.faceit.com/data/v4/players/me
   ```

---

## 📊 ПРОИЗВОДИТЕЛЬНОСТЬ

### Ожидаемые улучшения v2.1.3:

- ⚡ **3-5x ускорение** анализа матчей и статистики
- 🔄 **Параллельная обработка** множественных запросов  
- 📈 **Лучшая отзывчивость** при пиковых нагрузках
- 🎯 **Оптимизированные** API запросы к FACEIT

### Мониторинг производительности:

```bash
# CPU и память контейнеров
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Количество обработанных задач (в логах)
docker-compose logs faceit-bot | grep -c "processed"

# Время ответа API
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

---

## ✅ ГОТОВО К РАБОТЕ!

Бот развернут в продакшене с полной системой воркеров.

**Контакты для поддержки:**
- Telegram: @karriDD
- GitHub Issues: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/issues

**Версия:** v2.1.3 Production Release 🚀