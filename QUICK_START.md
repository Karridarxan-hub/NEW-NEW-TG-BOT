# 🚀 Quick Start - FACEIT CS2 Bot

## 📋 Что нужно перед запуском

### 1. API ключи
Получите следующие ключи:

#### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Сохраните полученный токен

#### FACEIT API Key  
1. Перейдите на [FACEIT Developer Portal](https://developers.faceit.com)
2. Зарегистрируйтесь или войдите
3. Создайте новое приложение
4. Получите **Server-side API ключ**
5. Сохраните ключ

### 2. Настройка .env
```bash
# Откройте файл .env и замените значения:
BOT_TOKEN=ваш_реальный_токен_бота
FACEIT_API_KEY=ваш_реальный_faceit_ключ
```

## ⚡ Быстрый запуск

### Windows:
```cmd
quick-start.bat
```

### Linux/Mac:
```bash
chmod +x quick-start.sh
./quick-start.sh
```

### Альтернативный способ:
```bash
docker-compose up --build
```

## 🔍 Проверка работы

### Health Check:
```bash
curl http://localhost:8000/health
```

### Просмотр логов:
```bash
docker-compose logs -f
```

### API документация:
Откройте в браузере: http://localhost:8000/docs

## 📱 Тестирование в Telegram

1. Найдите вашего бота в Telegram по имени (которое указали в BotFather)
2. Отправьте `/start`
3. Введите ваш никнейм FACEIT
4. Тестируйте функции через меню

## 🛠️ Управление

### Остановка:
```bash
docker-compose down
```

### Перезапуск:
```bash
docker-compose restart
```

### Полная пересборка:
```bash
docker-compose down
docker-compose up --build
```

## ❓ Проблемы

### Бот не отвечает
- Проверьте правильность BOT_TOKEN
- Убедитесь что порт 8000 свободен
- Посмотрите логи: `docker-compose logs -f`

### Ошибки FACEIT API
- Проверьте правильность FACEIT_API_KEY
- Убедитесь что ключ активен на developers.faceit.com

### Конфликты портов
- Измените порт в docker-compose.yml (8000 на другой)
- Или остановите другие сервисы на порту 8000

## 📞 Поддержка

Если возникли проблемы, проверьте:
1. [DEPLOYMENT.md](DEPLOYMENT.md) - полная инструкция
2. [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - техническая документация
3. Логи приложения: `docker-compose logs -f`