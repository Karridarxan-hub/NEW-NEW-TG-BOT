#!/bin/bash

# 🚀 Запуск локальной разработки FACEIT CS2 Bot
# Тестовый бот: 8282817400:AAGmpBXkc4oYYOjZJx9l6WvAES9uAg5xy_g

echo ""
echo "🚀 Запуск локальной среды разработки..."
echo "🤖 Тестовый бот: @test_faceit_darkhan_bot"
echo "🌐 FastAPI: http://localhost:8000"  
echo "🗄️ PostgreSQL: localhost:5432"
echo "⚡ Redis: localhost:6380"
echo ""

# Остановка старых контейнеров
echo "🔄 Остановка старых контейнеров..."
docker-compose down

# Запуск сервисов
echo "🐳 Запуск Docker Compose..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Проверка статуса
echo "📊 Статус сервисов:"
docker-compose ps

# Health check
echo ""
echo "🏥 Проверка Health Check..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Сервисы готовы к работе!"
    echo ""
    echo "📱 Протестируйте бота в Telegram"
    echo "🌐 Откройте http://localhost:8000/health для проверки"
    echo "📋 Логи: docker-compose logs -f faceit-bot"
else
    echo "❌ Сервисы еще запускаются, подождите..."
    echo "📋 Проверьте логи: docker-compose logs faceit-bot"
fi

echo ""
echo "🎯 Готово к разработке! Удачи! 🚀"