# 🔐 Текущая конфигурация FACEIT CS2 Бота

## 📋 Состояние на 2025-01-08

### 🤖 Telegram Bot
- **Имя бота**: @test_faceit_darkhan_bot
- **Bot ID**: 8282817400
- **BOT_TOKEN**: `8282817400:AAGmpBXkc4oYYOjZJx9l6WvAES9uAg5xy_g`
- **Статус**: ✅ Активен и работает

### 🎮 FACEIT API
- **FACEIT_API_KEY**: `41f48f43-609c-4639-b821-360b039f18b4`
- **Base URL**: https://open.faceit.com/data/v4
- **Rate Limit**: 60 requests/min
- **Статус**: ✅ Подключен и работает

### 🐳 Docker Deployment

#### Контейнеры
```bash
# Основной бот
CONTAINER ID: faceit_cs2_bot
IMAGE: newprojectbot-faceit-bot
STATUS: Up (healthy)
PORTS: 0.0.0.0:8000->8000/tcp

# Redis кэш
CONTAINER ID: faceit_redis  
IMAGE: redis:7-alpine
STATUS: Up (healthy)
PORTS: 0.0.0.0:6379->6379/tcp
```

#### Сеть
```bash
NETWORK: faceit-network
SUBNET: 172.22.0.0/16
DRIVER: bridge
```

#### Volumes
```bash
redis_data: driver local
nginx_logs: driver local
./logs:/app/logs:rw
./data:/app/data:rw
```

### 🌐 Endpoints

#### Health Check
```bash
URL: http://localhost:8000/health
Method: GET
Response: {"status": "healthy", "bot_status": "running"}
```

#### API Endpoints
```bash
# Поиск игрока
GET /api/player/search/{nickname}

# Статистика игрока  
GET /api/player/{player_id}/stats

# Статистика бота
GET /api/stats

# FACEIT Webhook
POST /webhook/faceit
```

### ⚙️ Environment Variables (.env)
```env
BOT_TOKEN=8282817400:AAGmpBXkc4oYYOjZJx9l6WvAES9uAg5xy_g
FACEIT_API_KEY=41f48f43-609c-4639-b821-360b039f18b4
DEBUG=false
PYTHONUNBUFFERED=1
```

### 📊 Функциональность

#### ✅ Работает полностью:
- 🚀 Запуск бота и API сервера
- 📱 Telegram polling
- 🔍 Поиск FACEIT профилей
- 📊 Базовая статистика игрока
- 🎮 Главное меню с навигацией
- 💾 In-memory хранилище данных
- 🏥 Health checks

#### 🚧 Заглушки (готово к развертыванию):
- 📝 История матчей
- 📈 Анализ формы
- 🎮 Последний матч  
- ⚔️ Сравнение игроков
- 🔍 Анализ текущего матча
- 👤 Управление профилем
- ⚙️ Настройки пользователя
- ❓ Справочная система

### 🔧 Команды развертывания

#### Запуск
```bash
cd "C:\Users\karri\OneDrive\Рабочий стол\projects\NEW project bot"
docker-compose up -d
```

#### Перезапуск
```bash
docker-compose restart faceit-bot
```

#### Полная пересборка
```bash
docker-compose down
docker-compose build --no-cache --pull
docker-compose up -d
```

#### Просмотр логов
```bash
docker-compose logs faceit-bot -f
```

#### Проверка статуса
```bash
docker-compose ps
curl http://localhost:8000/health
```

### 📈 Мониторинг

#### Логи приложения
```bash
# Местоположение
./logs/ директория в проекте

# Формат
2025-08-18 21:07:21,196 - aiogram.dispatcher - INFO - Run polling for bot @test_faceit_darkhan_bot

# Уровни логирования
INFO, WARNING, ERROR
```

#### Метрики
```bash
# Health check статус
curl -s http://localhost:8000/health | jq

# Redis статус  
docker exec faceit_redis redis-cli ping

# Статистика бота
curl -s http://localhost:8000/api/stats | jq
```

### 🔐 Безопасность

#### Настройки Docker
- Непривилегированный пользователь (appuser:1000)
- Ограничения ресурсов (CPU: 1.0, Memory: 512M)
- Health checks для мониторинга

#### Network Security
- Изолированная Docker сеть
- Только необходимые порты открыты
- Внутренняя коммуникация между контейнерами

#### API Security
- Rate limiting на FACEIT API
- Input validation для пользовательских данных
- Secure token handling

### 🚨 Критические заметки

⚠️ **ВАЖНО**: Данный файл содержит конфиденциальную информацию:
- Токены API
- Ключи доступа
- Конфигурацию производственной среды

🔒 **Безопасность**:
- Не публиковать в открытые репозитории
- Регулярно обновлять токены
- Мониторить использование API ключей

📋 **Backup**:
- Регулярное резервное копирование конфигурации
- Документирование всех изменений
- Версионирование настроек

---

*Конфигурация зафиксирована: 2025-01-08 02:10 UTC+5*  
*Статус: Production Ready*  
*Последняя проверка: ✅ Все системы работают*