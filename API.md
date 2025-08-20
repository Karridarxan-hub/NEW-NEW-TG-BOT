# 📡 API Документация FACEIT CS2 Бота

## 📋 Обзор API

FACEIT CS2 Бот предоставляет RESTful API для интеграции с внешними системами и мониторинга. API построен на FastAPI с автоматической генерацией OpenAPI документации.

## 🔗 Базовый URL

```
http://localhost:8000  # Разработка
https://yourdomain.com # Продакшен
```

## 📊 Интерактивная документация

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## 🔐 Аутентификация

В текущей версии API endpoints не требуют аутентификации, но рекомендуется настроить rate limiting в продакшене.

## 📍 Endpoints

### 1. Health Check

#### GET `/`
Проверка статуса API.

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/"
```

**Ответ:**
```json
{
  "message": "FACEIT CS2 Bot API is running",
  "status": "ok"
}
```

#### GET `/health`
Детальная проверка здоровья системы.

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Ответ:**
```json
{
  "status": "healthy",
  "bot_status": "running",
  "storage": {
    "users_count": 150,
    "sessions_count": 45,
    "cache_size": 892
  }
}
```

### 2. Player Search

#### GET `/api/player/search/{nickname}`
Поиск игрока по никнейму FACEIT.

**Параметры:**
- `nickname` (path) - Никнейм игрока на FACEIT

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/api/player/search/s1mple"
```

**Успешный ответ (200):**
```json
{
  "player_id": "c2f2c5a8-1234-4567-8901-123456789abc",
  "nickname": "s1mple",
  "level": 10,
  "elo": 3241,
  "country": "UA",
  "avatar": "https://avatars.faceit.com/..."
}
```

**Ошибка - игрок не найден (404):**
```json
{
  "error": "Player not found"
}
```

**Ошибка сервера (500):**
```json
{
  "error": "Internal server error"
}
```

### 3. Player Statistics

#### GET `/api/player/{player_id}/stats`
Получение полной статистики игрока.

**Параметры:**
- `player_id` (path) - Уникальный ID игрока FACEIT

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/api/player/c2f2c5a8-1234-4567-8901-123456789abc/stats"
```

**Успешный ответ (200):**
```json
{
  "nickname": "s1mple",
  "level": 10,
  "elo": 3241,
  "matches": 2847,
  "wins": 1823,
  "winrate": 64.0,
  "kills": 62394,
  "deaths": 48729,
  "assists": 12847,
  "kd_ratio": 1.28,
  "adr": 84.7,
  "hltv_rating": 1.24,
  "kast": 75.3,
  "headshots": 47.8,
  "first_kills": 8394,
  "first_deaths": 6728,
  "flash_assists": 4729,
  "utility_damage": 47382,
  "he_damage": 28394,
  "molotov_damage": 18988,
  "enemies_flashed": 15847,
  "maps": {
    "de_mirage": {
      "matches": 387,
      "wins": 251,
      "winrate": 64.9,
      "kills": 8472,
      "deaths": 6684,
      "assists": 1749,
      "kd_ratio": 1.27,
      "adr": 85.2,
      "hltv_rating": 1.26
    },
    "de_inferno": {
      "matches": 341,
      "wins": 218,
      "winrate": 63.9,
      "kills": 7583,
      "deaths": 5927,
      "assists": 1564,
      "kd_ratio": 1.28,
      "adr": 83.9,
      "hltv_rating": 1.23
    }
  }
}
```

### 4. Bot Statistics

#### GET `/api/stats`
Получение статистики работы бота.

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/api/stats"
```

**Ответ:**
```json
{
  "total_users": 1547,
  "active_sessions": 89,
  "cache_entries": 2847,
  "tracked_matches": 34,
  "comparison_data": 127
}
```

### 5. FACEIT Webhook

#### POST `/webhook/faceit`
Webhook endpoint для получения уведомлений от FACEIT.

**Headers:**
```
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "event": "match_finished",
  "payload": {
    "id": "match-id-12345",
    "status": "finished",
    "teams": [...],
    "players": [...]
  }
}
```

**Ответ:**
```json
{
  "status": "ok"
}
```

## 📊 Коды ответов HTTP

| Код | Описание | Когда возникает |
|-----|----------|-----------------|
| 200 | OK | Успешный запрос |
| 400 | Bad Request | Неверные параметры запроса |
| 404 | Not Found | Ресурс не найден |
| 429 | Too Many Requests | Превышен лимит запросов |
| 500 | Internal Server Error | Внутренняя ошибка сервера |
| 502 | Bad Gateway | Проблемы с внешним API |
| 503 | Service Unavailable | Сервис временно недоступен |

## 🔄 Rate Limiting

### Лимиты по умолчанию
- **Global**: 1000 запросов/час на IP
- **Player Search**: 60 запросов/минуту на IP  
- **Player Stats**: 30 запросов/минуту на IP
- **Health Check**: Без ограничений

### Headers при лимитах
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Ответ при превышении лимита
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

## 🔍 Фильтрация и пагинация

Для endpoints, возвращающих массивы данных:

### Query параметры
- `limit` (int) - Количество записей (max: 100, default: 20)
- `offset` (int) - Смещение для пагинации (default: 0)
- `sort` (string) - Поле для сортировки
- `order` (string) - Направление сортировки (asc/desc)

### Пример с пагинацией
```bash
curl "http://localhost:8000/api/matches?limit=10&offset=20&sort=date&order=desc"
```

## 🚨 Обработка ошибок

### Структура ошибки
```json
{
  "error": "Error description",
  "error_code": "PLAYER_NOT_FOUND",
  "details": {
    "player_id": "invalid-id",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Коды ошибок
- `PLAYER_NOT_FOUND` - Игрок не найден
- `INVALID_PARAMETERS` - Неверные параметры
- `FACEIT_API_ERROR` - Ошибка FACEIT API
- `RATE_LIMIT_EXCEEDED` - Превышен лимит запросов
- `INTERNAL_ERROR` - Внутренняя ошибка

## 📈 Мониторинг и метрики

### Health Check Endpoints

#### GET `/health/live`
Liveness probe - проверка, что приложение запущено.

```json
{
  "status": "alive",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/health/ready`
Readiness probe - готовность обслуживать запросы.

```json
{
  "status": "ready",
  "dependencies": {
    "faceit_api": "ok",
    "telegram_api": "ok"
  }
}
```

### Метрики Prometheus

#### GET `/metrics`
Экспорт метрик в формате Prometheus.

```
# HELP faceit_bot_requests_total Total API requests
# TYPE faceit_bot_requests_total counter
faceit_bot_requests_total{method="GET",endpoint="/api/player/stats",status="200"} 1547

# HELP faceit_bot_response_time_seconds Response time in seconds
# TYPE faceit_bot_response_time_seconds histogram
faceit_bot_response_time_seconds_bucket{le="0.1"} 892
```

## 🧪 Примеры использования

### Python Client
```python
import requests

class FaceitBotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def search_player(self, nickname):
        response = requests.get(f"{self.base_url}/api/player/search/{nickname}")
        return response.json()
    
    def get_player_stats(self, player_id):
        response = requests.get(f"{self.base_url}/api/player/{player_id}/stats")
        return response.json()

# Использование
client = FaceitBotClient()
player = client.search_player("s1mple")
stats = client.get_player_stats(player["player_id"])
```

### JavaScript/Node.js Client
```javascript
class FaceitBotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async searchPlayer(nickname) {
        const response = await fetch(`${this.baseUrl}/api/player/search/${nickname}`);
        return response.json();
    }
    
    async getPlayerStats(playerId) {
        const response = await fetch(`${this.baseUrl}/api/player/${playerId}/stats`);
        return response.json();
    }
}

// Использование
const client = new FaceitBotClient();
const player = await client.searchPlayer('s1mple');
const stats = await client.getPlayerStats(player.player_id);
```

### cURL примеры

```bash
#!/bin/bash

# Поиск игрока
PLAYER=$(curl -s "http://localhost:8000/api/player/search/s1mple")
PLAYER_ID=$(echo $PLAYER | jq -r '.player_id')

# Получение статистики
STATS=$(curl -s "http://localhost:8000/api/player/$PLAYER_ID/stats")

# Вывод основной статистики  
echo "Игрок: $(echo $STATS | jq -r '.nickname')"
echo "Уровень: $(echo $STATS | jq -r '.level')"
echo "ELO: $(echo $STATS | jq -r '.elo')"
echo "K/D: $(echo $STATS | jq -r '.kd_ratio')"
```

## 🔧 SDK и библиотеки

### Официальные SDK
- **Python SDK**: `pip install faceit-cs2-bot-sdk`
- **JavaScript SDK**: `npm install faceit-cs2-bot-sdk`

### Community Libraries
- **Go Client**: github.com/community/faceit-cs2-go
- **PHP Client**: packagist.org/community/faceit-cs2-php

## 📝 OpenAPI Specification

Полная OpenAPI 3.0 спецификация доступна по адресу `/openapi.json`:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "FACEIT CS2 Bot API",
    "description": "API для Telegram бота статистики FACEIT CS2",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "http://localhost:8000",
      "description": "Development server"
    }
  ],
  "paths": {
    "/api/player/search/{nickname}": {
      "get": {
        "summary": "Search player by nickname",
        "parameters": [
          {
            "name": "nickname",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Player found",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Player"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

*API документация обновлена: 2024-01-01*  
*Версия API: 1.0.0*