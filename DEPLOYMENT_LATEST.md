# 🐳 Развертывание FACEIT CS2 Бота (v2.1.0)

## 📋 Предварительные Требования

### 🔑 Токены и Ключи
```bash
# В файле .env
BOT_TOKEN=ваш_telegram_bot_token
FACEIT_API_KEY=ваш_faceit_api_key
```

### 🗄️ Базы Данных
- **PostgreSQL** для основных данных
- **Redis** для кэширования

## 🚀 Быстрый Запуск

### 1. Клонирование и Настройка
```bash
git clone <repository>
cd "NEW project bot"
cp .env.example .env
# Отредактируйте .env с вашими токенами
```

### 2. Docker Развертывание
```bash
# Разработка
docker-compose -f docker-compose.dev.yml up -d

# Производство
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Инициализация БД
```bash
# Выполните миграции
docker-compose exec bot python -c "
from storage import storage
import asyncio
asyncio.run(storage.init_storage())
"
```

## 🛠️ Локальная Разработка

### Требования
- Python 3.11+
- PostgreSQL 13+
- Redis 6+

### Установка
```bash
pip install -r requirements.txt
python main.py
```

**Порт:** 8001 (изменен с 8000 в v2.1.0)

## 📊 Новые Функции v2.1.0

### 🗺️ Динамические Карты
```python
# Теперь автоматически загружает все карты из FACEIT API
# Больше не нужно обновлять хардкодный список
```

### ⏰ Улучшенные Сессии
```python
# Новый интервал группировки
SESSION_INTERVAL_HOURS = 10  # вместо 12

# Новый формат отображения с цветовыми индикаторами
📅 11.08.2025 - 6 матчей • Длительность: 3.5ч
🟢 HLTV: 1.02 | 🟢 K/D: 1.1 | 🔴 WR: 33.3%
```

### 🎯 Исправленная Точность
```python
# Хедшоты теперь рассчитываются из segments
# Точность: 46% → 50.1% (+4.1%)
```

## 🔧 Конфигурация Контейнеров

### Docker Compose Конфигурация
```yaml
# docker-compose.yml (основной)
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8001:8001"  # Обновленный порт
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - FACEIT_API_KEY=${FACEIT_API_KEY}
    depends_on:
      - postgres
      - redis
```

### Переменные Окружения
```bash
# Основные
BOT_TOKEN=8282...  # Telegram Bot Token
FACEIT_API_KEY=41f4...  # FACEIT API Key

# База данных
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=faceit_bot
POSTGRES_USER=faceit_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Приложение
DEBUG=false
PORT=8001  # Новый порт в v2.1.0
```

## 📋 Проверка Статуса

### Здоровье Системы
```bash
# Проверка статуса контейнеров
docker-compose ps

# Логи бота
docker-compose logs bot

# Проверка базы данных
docker-compose exec postgres psql -U faceit_user -d faceit_bot -c "SELECT COUNT(*) FROM users;"
```

### API Endpoints
```bash
# Проверка здоровья
curl http://localhost:8001/health

# Метрики
curl http://localhost:8001/metrics
```

## 🚨 Устранение Неполадок

### Конфликт Портов
```bash
# Если порт 8001 занят
netstat -tulpn | grep :8001
# Измените PORT в .env или остановите конфликтующий процесс
```

### Проблемы с БД
```bash
# Пересоздание БД
docker-compose down -v
docker-compose up -d postgres redis
# Подождите 30 секунд
docker-compose up -d bot
```

### Проблемы с API
```bash
# Проверка FACEIT API ключа
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://open.faceit.com/data/v4/players/me"
```

## 📈 Мониторинг

### Логи и Метрики
- **Логи:** `docker-compose logs -f bot`
- **Метрики:** Доступны через `/metrics` endpoint
- **Здоровье:** Проверка через `/health`

### Основные Метрики
- Количество активных пользователей
- Запросы к FACEIT API
- Время отклика статистических запросов
- Использование кэша Redis

## 🔄 Обновление

### Обновление до v2.1.0
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Проверка Версии
```bash
# В логах должно быть указано v2.1.0
docker-compose logs bot | grep "version"
```

---

**Версия:** 2.1.0  
**Дата:** 20.08.2025  
**Статус:** Стабильная  
**Поддержка:** Активная