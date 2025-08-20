# 🚀 Руководство по развертыванию FACEIT CS2 Бота

## 📋 Обзор

Данное руководство содержит подробные инструкции по развертыванию FACEIT CS2 бота в различных окружениях с использованием Docker и docker-compose.

## 🛠️ Системные требования

### Минимальные требования
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+  
- **RAM**: 512 MB
- **CPU**: 1 ядро
- **Disk**: 1 GB свободного места
- **Network**: Стабильное интернет-соединение

### Рекомендуемые требования
- **OS**: Linux (Ubuntu 22.04 LTS)
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **RAM**: 2 GB
- **CPU**: 2+ ядра
- **Disk**: 5 GB SSD
- **Network**: Высокоскоростное соединение

## 🔑 Предварительная настройка

### 1. Получение API ключей

#### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

#### FACEIT API Key
1. Зарегистрируйтесь на [FACEIT Developer Portal](https://developers.faceit.com)
2. Создайте новое приложение
3. Получите Server-side API ключ
4. Сохраните ключ

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Обязательные параметры
BOT_TOKEN=your_telegram_bot_token_here
FACEIT_API_KEY=your_faceit_api_key_here

# Опциональные параметры
DEBUG=false
LOG_LEVEL=INFO
WEBHOOK_URL=https://yourdomain.com/webhook/faceit

# Кэширование и производительность
CACHE_TTL=300
MAX_SESSIONS=1000
CLEANUP_INTERVAL=3600

# Мониторинг
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
```

## 🔧 Режимы развертывания

### 1. Локальная разработка

#### Быстрый старт
```bash
# Клонирование проекта
git clone <repository-url>
cd faceit-cs2-bot

# Создание .env файла
cp .env.example .env
# Отредактируйте .env файл с вашими ключами

# Запуск в режиме разработки
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

#### Детальная настройка разработки
```bash
# Сборка development образа
docker build -f Dockerfile.dev -t faceit-bot:dev .

# Запуск с hot-reload
docker-compose -f docker-compose.dev.yml up -d

# Просмотр логов
docker-compose logs -f faceit-bot

# Остановка
docker-compose -f docker-compose.dev.yml down
```

### 2. Тестовое окружение

#### Настройка тестинга
```bash
# Запуск тестов в контейнере
docker run --rm -v $(pwd):/app faceit-bot:dev pytest /app/test_bot.py -v

# Запуск с coverage
docker run --rm -v $(pwd):/app faceit-bot:dev pytest /app/test_bot.py --cov=. --cov-report=html

# Линтинг кода
docker run --rm -v $(pwd):/app faceit-bot:dev flake8 /app --max-line-length=88
docker run --rm -v $(pwd):/app faceit-bot:dev black /app --check
```

### 3. Продакшен развертывание

#### Подготовка сервера
```bash
# Обновление системы (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Развертывание приложения
```bash
# Клонирование в продакшен директорию
sudo mkdir -p /opt/faceit-bot
sudo chown $USER:$USER /opt/faceit-bot
cd /opt/faceit-bot

git clone <repository-url> .

# Настройка production .env
cp .env.example .env
nano .env  # Отредактируйте с production настройками

# Создание необходимых директорий
mkdir -p logs data nginx/ssl

# Запуск в продакшене
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Проверка статуса
docker-compose ps
docker-compose logs -f
```

## 🌐 Настройка Nginx (опционально)

### 1. Конфигурация Nginx

Создайте файл `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream faceit_bot {
        server faceit-bot:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API endpoints
        location /api/ {
            limit_req zone=api burst=5 nodelay;
            proxy_pass http://faceit_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://faceit_bot;
            access_log off;
        }

        # Webhook endpoint
        location /webhook/ {
            proxy_pass http://faceit_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### 2. SSL сертификаты

```bash
# Используя Certbot (Let's Encrypt)
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d yourdomain.com

# Копирование в nginx директорию
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*.pem

# Включение nginx в compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile proxy up -d
```

## 📊 Мониторинг и логирование

### 1. Проверка состояния сервисов

```bash
# Статус всех сервисов
docker-compose ps

# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f faceit-bot

# Health check
curl http://localhost:8000/health
```

### 2. Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Мониторинг дискового пространства
df -h

# Мониторинг логов
tail -f logs/app.log
```

### 3. Настройка логирования

```bash
# Ротация логов (логrotate)
sudo nano /etc/logrotate.d/faceit-bot
```

```
/opt/faceit-bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 1000 1000
}
```

## 🔧 Обслуживание и обновления

### 1. Обновление приложения

```bash
# Backup текущей версии
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
cp -r /opt/faceit-bot /opt/faceit-bot-backup-$(date +%Y%m%d)

# Получение обновлений
git pull origin main

# Пересборка и перезапуск
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Проверка работоспособности
sleep 30
curl http://localhost:8000/health
```

### 2. Резервное копирование

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/faceit-bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup конфигурации
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose*.yml nginx/

# Backup логов
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Удаление старых backups (старше 30 дней)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 3. Восстановление после сбоя

```bash
# Остановка сервисов
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Восстановление из backup
tar -xzf /opt/backups/faceit-bot/config_YYYYMMDD_HHMMSS.tar.gz

# Перезапуск с force recreate
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
```

## 🚨 Устранение неполадок

### 1. Частые проблемы

#### Контейнер не запускается
```bash
# Проверка логов
docker-compose logs faceit-bot

# Проверка переменных окружения
docker-compose config

# Проверка портов
netstat -tulpn | grep :8000
```

#### FACEIT API ошибки
```bash
# Проверка API ключа
curl -H "Authorization: Bearer $FACEIT_API_KEY" \
     "https://open.faceit.com/data/v4/players?nickname=test"

# Проверка лимитов
grep "429" logs/app.log
```

#### Проблемы с памятью
```bash
# Мониторинг памяти
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Очистка кэша
docker exec faceit-bot-container python -c "from storage import storage; storage.cleanup_old_cache()"
```

### 2. Диагностические команды

```bash
# Полная диагностика
./scripts/health-check.sh

# Проверка сетевого соединения
docker exec faceit-bot-container ping -c 3 open.faceit.com

# Проверка API endpoints
curl -f http://localhost:8000/api/stats
```

## 🔄 CI/CD Pipeline (опционально)

### GitHub Actions example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.DEPLOY_KEY }}
        script: |
          cd /opt/faceit-bot
          git pull origin main
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
          sleep 30
          curl -f http://localhost:8000/health
```

## 📞 Поддержка

При возникновении проблем с развертыванием:

1. Проверьте [раздел устранения неполадок](#-устранение-неполадок)
2. Изучите логи: `docker-compose logs -f`
3. Проверьте статус сервисов: `docker-compose ps`
4. Создайте Issue на GitHub с подробным описанием проблемы

---

*Руководство обновлено: 2024-01-01*  
*Версия: 1.0.0*