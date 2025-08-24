@echo off
REM Скрипт для быстрой сборки Docker контейнеров (Windows)

setlocal enabledelayedexpansion

echo.
echo 🚀 Быстрая сборка FACEIT Bot
echo.

REM Засекаем время начала
set start_time=%time%

REM Проверяем аргументы
set FORCE_REBUILD=false
if "%1"=="--force" set FORCE_REBUILD=true
if "%1"=="-f" set FORCE_REBUILD=true

if "%FORCE_REBUILD%"=="true" (
    echo ⚠️  Принудительная пересборка (без кеша^)
    echo.
)

echo 📊 Проверяем статус контейнеров...
docker-compose ps

echo.
echo 🛑 Останавливаем существующие контейнеры...
docker-compose down

if "%FORCE_REBUILD%"=="true" (
    echo.
    echo 🧹 Очищаем Docker кеш...
    docker system prune -f
    echo.
    echo 🔄 Сборка без кеша...
    docker-compose build --no-cache
) else (
    echo.
    echo ⚡ Быстрая сборка с кешем...
    docker-compose build
)

echo.
echo 🚀 Запускаем контейнеры...
docker-compose up -d

echo.
echo 📊 Статус сервисов:
docker-compose ps

echo.
echo 📋 Логи запуска:
docker-compose logs --tail=20

REM Вычисляем время выполнения
set end_time=%time%
echo.
echo ✅ Сборка завершена
echo   Время начала: %start_time%
echo   Время окончания: %end_time%

echo.
echo 🔗 Полезные команды:
echo   Логи бота:     docker-compose logs -f faceit-bot
echo   Перезапуск:    docker-compose restart faceit-bot  
echo   Остановка:     docker-compose down
echo   Статус:        docker-compose ps
echo.

pause