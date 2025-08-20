#!/usr/bin/env python3
"""
Тестовый файл для проверки исправленного stats_handler.py
"""

import asyncio
import logging
from faceit_client import faceit_client
from storage import storage, init_storage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_stats_handler():
    """Тест основных функций stats_handler с игроком Geun-Hee"""
    test_nickname = "Geun-Hee"
    
    try:
        print(f"\n=== Тест stats_handler с игроком {test_nickname} ===\n")
        
        # Инициализируем storage (если нужно)
        try:
            await init_storage()
            print("✓ Storage инициализирован")
        except Exception as e:
            print(f"⚠ Storage не инициализирован (это нормально для тестов): {e}")
        
        # 1. Поиск игрока
        print(f"1. Поиск игрока '{test_nickname}'...")
        player = await faceit_client.find_player_by_nickname(test_nickname)
        if player:
            print(f"   ✓ Игрок найден: {player['nickname']} (ID: {player['player_id']})")
            player_id = player['player_id']
        else:
            print(f"   ✗ Игрок не найден")
            return
        
        # 2. Получение детальной статистики
        print(f"\n2. Получение детальной статистики...")
        player_details = await faceit_client.get_player_details(player_id)
        stats_data = await faceit_client.get_player_stats(player_id)
        
        if player_details and stats_data:
            print(f"   ✓ Данные получены")
        else:
            print(f"   ✗ Ошибка получения данных")
            return
        
        # 3. Форматирование статистики (как в исправленном stats_handler)
        print(f"\n3. Форматирование статистики...")
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        
        if formatted_stats:
            print(f"   ✓ Статистика отформатирована")
            print(f"     - Никнейм: {formatted_stats.get('nickname')}")
            print(f"     - Уровень: {formatted_stats.get('level')}")
            print(f"     - ELO: {formatted_stats.get('elo')}")
            print(f"     - Матчи: {formatted_stats.get('matches')}")
            print(f"     - Винрейт: {formatted_stats.get('winrate'):.1f}%")
            print(f"     - K/D: {formatted_stats.get('kd_ratio'):.3f}")
            print(f"     - ADR: {formatted_stats.get('adr'):.1f}")
            print(f"     - HLTV Rating: {formatted_stats.get('hltv_rating'):.2f}")
            
            # Проверка статистики по картам
            maps_stats = formatted_stats.get('maps', {})
            print(f"     - Карт в статистике: {len(maps_stats)}")
            
            if maps_stats:
                print("     - Топ-3 карты по матчам:")
                sorted_maps = sorted(maps_stats.items(), key=lambda x: x[1].get('matches', 0), reverse=True)
                for i, (map_name, map_data) in enumerate(sorted_maps[:3], 1):
                    matches = map_data.get('matches', 0)
                    winrate = map_data.get('winrate', 0)
                    print(f"       {i}. {map_name}: {matches} матчей, {winrate:.1f}% WR")
        else:
            print(f"   ✗ Ошибка форматирования статистики")
            return
        
        # 4. Получение истории матчей
        print(f"\n4. Получение истории матчей...")
        history_data = await faceit_client.get_player_history(player_id, limit=10)
        
        if history_data and 'items' in history_data:
            matches = history_data['items']
            print(f"   ✓ История получена: {len(matches)} матчей")
            
            # Тест определения результатов матчей
            print("   Результаты последних 5 матчей:")
            for i, match in enumerate(matches[:5], 1):
                player_won = faceit_client._determine_player_result(match, player_id)
                result_emoji = "✅" if player_won is True else "❌" if player_won is False else "❓"
                map_name = match.get('map', 'Unknown')
                print(f"     {i}. {result_emoji} {map_name}")
        else:
            print(f"   ✗ История матчей не получена")
        
        # 5. Тест функций безопасного парсинга
        print(f"\n5. Тест вспомогательных функций...")
        from bot.handlers.stats_handler import safe_float, safe_int, validate_user_data
        
        # Тест safe_float
        assert safe_float("1.5") == 1.5
        assert safe_float("1,5") == 1.5
        assert safe_float("invalid") == 0.0
        assert safe_float(None) == 0.0
        print("   ✓ safe_float работает корректно")
        
        # Тест safe_int
        assert safe_int("10") == 10
        assert safe_int("10.5") == 10
        assert safe_int("invalid") == 0
        print("   ✓ safe_int работает корректно")
        
        # Тест validate_user_data
        test_user_data = validate_user_data({'nickname': 'TestUser', 'faceit_id': '123'})
        assert test_user_data['nickname'] == 'TestUser'
        print("   ✓ validate_user_data работает корректно")
        
        print(f"\n=== Все тесты пройдены успешно! ===\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
        logger.error(f"Test error: {e}")
    
    finally:
        await faceit_client.close()

if __name__ == "__main__":
    asyncio.run(test_stats_handler())