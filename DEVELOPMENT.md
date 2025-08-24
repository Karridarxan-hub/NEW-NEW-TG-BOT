# 🚀 Руководство по разработке FACEIT CS2 Bot

## 🎯 Быстрый старт

### 📋 Окружения

| Окружение | Бот токен | Использование |
|-----------|-----------|---------------|
| **Development** | `8282817400:AAGmpBXkc4oYYOjZJx9l6WvAES9uAg5xy_g` | @test_faceit_darkhan_bot - Тестирование |
| **Production** | `8200317917:AAE3wSxtG6N7wKeLJezgNaQsCd5uHMcXjVk` | @faceitstatsme_bot - Продакшен |

---

## 🔄 Workflow разработки

### 1️⃣ **Локальная разработка**

```bash
# Запуск локального окружения с тестовым ботом
./start-dev.bat     # Windows
./start-dev.sh      # Linux/Mac

# Проверка что все работает:
# 🌐 http://localhost:8000/health - FastAPI API
# 🤖 Тестируйте бота в Telegram
# 📋 docker-compose logs -f faceit-bot - логи
```

**Что запускается:**
- 🤖 **Тестовый Telegram бот** (токен из `.env`)
- 🌐 **FastAPI сервер** на http://localhost:8000
- 🗄️ **PostgreSQL** база данных со всеми таблицами
- ⚡ **Redis** для кэширования FACEIT API
- 👥 **Workers система** для фоновой обработки

### 2️⃣ **Тестирование изменений**

- 📱 **Тестируйте все функции** в Telegram с тестовым ботом
- 🔍 **Проверяйте логи** на наличие ошибок
- 🌐 **Тестируйте API endpoints** через браузер/Postman
- 📊 **Мониторьте health check** - http://localhost:8000/health

### 3️⃣ **Деплой в продакшен**

```bash
# Автоматический деплой через GitHub Actions
./deploy-to-production.bat  # Windows

# Или вручную:
git add .
git commit -m "🆕 Описание изменений" 
git push production master
```

**Что происходит при деплое:**
1. 🚀 **GitHub Actions** автоматически запускается
2. 🔐 **SSH подключение** к ВПС
3. 📥 **Git pull** новых изменений  
4. 🐳 **Docker rebuild** и перезапуск сервисов
5. 🏥 **Health check** проверка работоспособности
6. ✅ **Продовый бот обновлен!**

---

## 📁 Структура файлов

```
├── .env                    # 🧪 Локальные настройки (тестовый бот)
├── .env.production        # 🚀 Продовые настройки (на ВПС)
├── docker-compose.yml     # 🐳 Docker конфигурация
├── start-dev.bat/sh       # 🎯 Быстрый старт разработки
├── deploy-to-production.bat # 🚀 Деплой в продакшен
├── main.py               # 🤖 Главный файл приложения
└── bot/                  # 📁 Код бота
```

---

## 🔧 Настройки окружений

### 🧪 **Локальная разработка (.env)**
- `DEBUG=true` - отладочные логи
- `LOG_LEVEL=DEBUG` - подробное логирование  
- Меньше воркеров для экономии ресурсов
- Метрики включены для отладки

### 🚀 **Продакшен (.env.production)**  
- `DEBUG=false` - только важные логи
- `LOG_LEVEL=INFO` - стандартное логирование
- Больше воркеров для производительности
- Оптимизированные настройки кэша

---

## 🛠️ Полезные команды

### Docker управление
```bash
# Перезапуск только бота (при изменениях кода)
docker-compose restart faceit-bot

# Пересборка после изменения Dockerfile
docker-compose build --no-cache faceit-bot

# Остановка всех сервисов
docker-compose down

# Логи всех сервисов  
docker-compose logs -f

# Логи только бота
docker-compose logs -f faceit-bot
```

### Отладка
```bash
# Подключение к контейнеру бота
docker-compose exec faceit-bot bash

# Проверка состояния баз данных
docker-compose exec postgres psql -U faceit_user -d faceit_bot
docker-compose exec redis redis-cli

# Мониторинг ресурсов
docker stats
```

---

## 🚨 Важные замечания

### ⚠️ **НЕ изменяйте токены в коде!**
- Токены настраиваются через `.env` файлы
- Локально автоматически используется тестовый токен
- В продакшене автоматически используется продовый токен

### 🔐 **Безопасность**
- Никогда не коммитьте `.env.production` файл
- `.env` файл с тестовым токеном можно коммитить
- API ключи и пароли только через переменные окружения

### 📊 **Мониторинг**
- Health check: http://localhost:8000/health (локально)
- GitHub Actions: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/actions
- ВПС логи: `docker-compose logs -f faceit-bot`

---

## 🎉 Готово!

**Теперь у вас есть полностью настроенная среда разработки!**

🧪 **Разрабатывайте** → 🧪 **Тестируйте** → 🚀 **Деплойте** → 🎯 **Профит!**

Вопросы? Проблемы? Проверьте логи или создайте issue! 🚀