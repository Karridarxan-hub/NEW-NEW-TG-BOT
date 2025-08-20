@echo off
rem Quick Start Script для FACEIT CS2 Bot (Windows)
rem Использование: quick-start.bat

echo 🚀 FACEIT CS2 Bot - Quick Start
echo ==================================

rem Проверка .env файла
if not exist ".env" (
    echo ❌ Файл .env не найден!
    echo 💡 Создайте .env файл на основе .env.example и заполните API ключи
    pause
    exit /b 1
)

echo ✅ Файл .env найден

rem Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose не установлен
    pause
    exit /b 1
)

echo ✅ Docker готов к работе

rem Создание директорий
if not exist "logs" mkdir logs
if not exist "data" mkdir data

rem Остановка старых контейнеров
echo 🛑 Остановка старых контейнеров...
docker-compose down --remove-orphans >nul 2>&1

rem Запуск бота
echo ▶️ Запуск FACEIT CS2 Bot...
docker-compose up --build -d

rem Ожидание запуска
echo ⏳ Ожидание запуска сервисов...
timeout /t 10 >nul

rem Проверка состояния
curl -f -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Бот не отвечает на health check
    echo Проверьте логи: docker-compose logs -f
    pause
    exit /b 1
)

echo 🎉 Бот успешно запущен!
echo.
echo 📊 Полезные команды:
echo   docker-compose logs -f          # Просмотр логов
echo   docker-compose ps               # Статус контейнеров
echo   docker-compose down             # Остановка бота
echo   curl http://localhost:8000/health # Проверка здоровья
echo.
echo 🌐 Доступные endpoints:
echo   http://localhost:8000/health    # Health check
echo   http://localhost:8000/docs      # API документация
echo   http://localhost:8000/api/stats # Статистика бота
echo.
echo 💡 Найдите вашего бота в Telegram и отправьте /start

pause