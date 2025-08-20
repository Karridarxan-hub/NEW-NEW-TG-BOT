#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
from typing import Dict, List, Any

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient
from keyboards import (
    get_main_menu_keyboard, get_player_stats_keyboard, get_match_history_keyboard,
    get_form_analysis_keyboard, get_player_comparison_keyboard, get_settings_keyboard,
    get_help_keyboard, get_profile_keyboard, get_current_match_analysis_keyboard,
    get_last_match_keyboard
)

async def test_faceit_client():
    """Тестируем клиент FACEIT API"""
    print("=== Тест FACEIT Client ===")
    
    try:
        client = FaceitAPIClient()
        
        # Тест поиска игрока
        print("1. Тестируем поиск игрока 'test'...")
        player_data = await client.get_player_full_profile("test")
        
        if player_data:
            print(f"✅ Игрок найден: {player_data.get('nickname', 'N/A')}")
            print(f"   FACEIT ID: {player_data.get('player_id', 'N/A')}")
            print(f"   Уровень: {player_data.get('games', {}).get('cs2', {}).get('skill_level', 'N/A')}")
            
            # Тест получения статистики
            print("2. Тестируем получение статистики...")
            stats = await client.get_player_stats(player_data['player_id'])
            if stats:
                print("✅ Статистика получена")
                # Проверяем наличие новых метрик
                segments = stats.get('segments', [])
                if segments:
                    overall = next((s for s in segments if s.get('type') == 'Overall'), None)
                    if overall and 'stats' in overall:
                        stats_data = overall['stats']
                        print(f"   K/D: {stats_data.get('Average K/D Ratio', {}).get('value', 'N/A')}")
                        print(f"   HLTV 2.1: {stats_data.get('Average HLTV 2.1 Rating', {}).get('value', 'N/A')}")
                        print(f"   KAST: {stats_data.get('Average KAST', {}).get('value', 'N/A')}")
                        print(f"   Урон с гранат: {stats_data.get('Average Grenade Damage', {}).get('value', 'N/A')}")
            
            # Тест получения матчей
            print("3. Тестируем получение истории матчей...")
            matches = await client.get_player_matches(player_data['player_id'], limit=5)
            if matches:
                print(f"✅ Найдено {len(matches)} матчей")
                for i, match in enumerate(matches[:3], 1):
                    print(f"   Матч {i}: {match.get('competition_name', 'N/A')} на {match.get('map', {}).get('name', 'N/A')}")
            
        else:
            print("❌ Игрок не найден")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_keyboards():
    """Тестируем все клавиатуры"""
    print("\n=== Тест клавиатур ===")
    
    keyboards = [
        ("Главное меню", get_main_menu_keyboard),
        ("Статистика игрока", get_player_stats_keyboard),
        ("История матчей", get_match_history_keyboard),
        ("Анализ формы", get_form_analysis_keyboard),
        ("Сравнение игроков", lambda: get_player_comparison_keyboard(False)),
        ("Настройки", get_settings_keyboard),
        ("Помощь", get_help_keyboard),
        ("Профиль", get_profile_keyboard),
        ("Анализ текущего матча", get_current_match_analysis_keyboard),
        ("Последний матч", get_last_match_keyboard),
    ]
    
    for name, keyboard_func in keyboards:
        try:
            keyboard = keyboard_func()
            buttons_count = len([btn for row in keyboard.inline_keyboard for btn in row])
            print(f"✅ {name}: {buttons_count} кнопок")
        except Exception as e:
            print(f"❌ {name}: Ошибка - {e}")

async def test_database_connection():
    """Тестируем подключение к базе данных"""
    print("\n=== Тест базы данных ===")
    
    try:
        import asyncpg
        from config import settings
        
        # Подключаемся к базе
        conn = await asyncpg.connect(settings.database_url)
        
        # Проверяем таблицы
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        print(f"✅ Подключение к БД успешно. Найдено {len(tables)} таблиц:")
        for table in tables:
            print(f"   - {table['tablename']}")
        
        # Тестируем функции БД
        cache_cleaned = await conn.fetchval("SELECT clean_expired_cache();")
        print(f"✅ Функция очистки кэша работает: удалено {cache_cleaned} записей")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")

async def test_redis_connection():
    """Тестируем подключение к Redis"""
    print("\n=== Тест Redis ===")
    
    try:
        import redis.asyncio as redis
        from config import settings
        
        # Подключаемся к Redis
        r = await redis.from_url(settings.redis_url)
        
        # Тестовые операции
        await r.set("test_key", "test_value", ex=10)
        value = await r.get("test_key")
        
        if value == b"test_value":
            print("✅ Redis подключение работает")
            
            # Проверяем информацию
            info = await r.info("server")
            print(f"   Redis версия: {info.get('redis_version', 'N/A')}")
        else:
            print("❌ Redis тест не прошел")
            
        await r.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")

def test_imports():
    """Тестируем импорты всех обработчиков"""
    print("\n=== Тест импортов обработчиков ===")
    
    handlers = [
        "bot.handlers.main_handler",
        "bot.handlers.stats_handler", 
        "bot.handlers.match_history_handler",
        "bot.handlers.form_analysis_handler",
        "bot.handlers.last_match_handler",
        "bot.handlers.comparison_handler",
        "bot.handlers.current_match_handler",
        "bot.handlers.profile_handler",
        "bot.handlers.settings_handler",
        "bot.handlers.help_handler",
        "bot.handlers.notifications_handler"
    ]
    
    for handler_name in handlers:
        try:
            __import__(handler_name)
            print(f"✅ {handler_name}")
        except Exception as e:
            print(f"❌ {handler_name}: {e}")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск полного тестирования FACEIT CS2 Bot")
    print("=" * 50)
    
    # Тестируем импорты
    test_imports()
    
    # Тестируем клавиатуры
    test_keyboards()
    
    # Тестируем подключения
    await test_redis_connection()
    await test_database_connection()
    
    # Тестируем FACEIT API
    await test_faceit_client()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("\n💡 Для запуска бота выполните: python main.py")

if __name__ == "__main__":
    # Настройка кодировки для Windows
    if sys.platform == "win32":
        import locale
        try:
            # Пытаемся установить UTF-8 кодировку
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            else:
                # Для старых версий Python
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
        except:
            # Если не получилось, заменяем проблемные символы
            import functools
            print = functools.partial(print, errors='replace')
    
    # Запускаем тестирование
    asyncio.run(main())