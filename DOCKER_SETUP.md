# 🐳 Настройка PostgreSQL и Redis в контейнерах

## 📋 Обзор изменений v1.2.0

В версии 1.2.0 добавлены PostgreSQL и Redis контейнеры для персистентного хранения данных и кэширования.

### 🔄 Что изменилось:
- ✅ **PostgreSQL контейнер** для хранения пользователей, истории матчей и настроек
- ✅ **Redis контейнер** для быстрого кэширования FACEIT API ответов
- ✅ **Автоматическая инициализация БД** через migrations/init.sql
- ✅ **Новая архитектура хранения** с DatabaseStorage

## 🚀 Быстрый запуск

### 1. Убедитесь, что Docker запущен
```bash
docker --version
docker-compose --version
```

### 2. Настройте переменные окружения
Файл `.env` уже содержит необходимые переменные:
```env
# Базы данных (автоматически настроены)
DATABASE_URL=postgresql://faceit_user:faceit_password@postgres:5432/faceit_bot
REDIS_URL=redis://redis:6379/0
```

### 3. Запустите все контейнеры
```bash
# Полный запуск (бот + PostgreSQL + Redis)
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build
```

### 4. Проверьте состояние
```bash
# Проверка всех контейнеров
docker-compose ps

# Проверка здоровья через API
curl http://localhost:8000/health
```

## 🏗️ Архитектура контейнеров

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FACEIT BOT    │    │   PostgreSQL     │    │     Redis       │
│                 │────▶│                  │    │                 │
│ • Telegram Bot  │    │ • Users          │◀───│ • API Cache     │
│ • FastAPI       │    │ • Match History  │    │ • Sessions      │
│ • Bot Handlers  │    │ • Settings       │    │ • Temp Data     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Структура базы данных

### PostgreSQL таблицы:
- `users` - пользователи бота
- `user_settings` - настройки пользователей  
- `match_history` - история матчей
- `comparison_lists` - списки сравнения игроков
- `user_sessions` - сессии пользователей
- `faceit_cache` - долгосрочный кэш FACEIT данных
- `tracked_matches` - отслеживание матчей для уведомлений

### Redis структуры:
- `api_cache:*` - кэш FACEIT API ответов (TTL: 5 мин)
- `session:*` - пользовательские сессии (TTL: 30 мин)
- `rate_limit:*` - ограничения частоты запросов (TTL: 1 мин)
- `temp:*` - временные данные (TTL: 10 мин)

## 🔧 Управление контейнерами

### Запуск отдельных сервисов
```bash
# Только базы данных
docker-compose up postgres redis -d

# Только бот (если БД уже запущены)  
docker-compose up faceit-bot

# С пересборкой
docker-compose up --build faceit-bot
```

### Мониторинг и логи
```bash
# Просмотр логов всех контейнеров
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f faceit-bot
docker-compose logs -f postgres
docker-compose logs -f redis

# Статистика ресурсов
docker stats
```

### Подключение к базам данных
```bash
# PostgreSQL
docker-compose exec postgres psql -U faceit_user -d faceit_bot

# Redis CLI
docker-compose exec redis redis-cli
```

### Полезные команды
```bash
# Перезапуск всех сервисов
docker-compose restart

# Остановка
docker-compose down

# Остановка с удалением volumes (ВНИМАНИЕ: потеря данных!)
docker-compose down -v

# Просмотр состояния health checks
docker-compose ps
```

## 🔍 Проверка работоспособности

### 1. API Health Check
```bash
curl http://localhost:8000/health
```
Ответ должен содержать:
```json
{
  "status": "healthy",
  "services": {
    "postgres": "active",
    "redis": "active",
    "faceit_api": "ok"
  },
  "metrics": {
    "total_users": 0,
    "total_matches": 0,
    "cache_entries": 0
  }
}
```

### 2. Проверка PostgreSQL
```bash
docker-compose exec postgres pg_isready -U faceit_user
```

### 3. Проверка Redis
```bash
docker-compose exec redis redis-cli ping
```

## 🐛 Устранение неполадок

### PostgreSQL не запускается
```bash
# Проверка логов
docker-compose logs postgres

# Пересборка с чистыми volumes
docker-compose down -v
docker-compose up postgres --build
```

### Redis недоступен
```bash
# Проверка подключения
docker-compose exec redis redis-cli ping

# Очистка Redis
docker-compose exec redis redis-cli FLUSHALL
```

### Бот не подключается к БД
```bash
# Проверка переменных окружения
docker-compose config

# Проверка сетей
docker network ls
docker network inspect newprojectbot_faceit-network
```

## 📈 Мониторинг производительности

### PostgreSQL
```sql
-- Размер базы данных
SELECT pg_size_pretty(pg_database_size('faceit_bot'));

-- Количество подключений
SELECT count(*) FROM pg_stat_activity;

-- Самые медленные запросы
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 5;
```

### Redis
```bash
# Использование памяти
docker-compose exec redis redis-cli INFO memory

# Статистика ключей
docker-compose exec redis redis-cli INFO keyspace

# Мониторинг команд
docker-compose exec redis redis-cli MONITOR
```

## 🔒 Безопасность

### Production настройки:
1. Измените пароли в `.env`:
   ```env
   DATABASE_URL=postgresql://faceit_user:STRONG_PASSWORD@postgres:5432/faceit_bot
   ```

2. Отключите внешние порты в docker-compose.yml:
   ```yaml
   # Удалите эти строки для production:
   ports:
     - "5432:5432"  # PostgreSQL
     - "6379:6379"  # Redis
   ```

3. Используйте SSL для PostgreSQL в production

## 📚 Дополнительная информация

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

🎮 **Готово!** Теперь у вас есть полноценная инфраструктура с персистентным хранилищем в контейнерах.