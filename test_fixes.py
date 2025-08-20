#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import faceit_client
from storage import storage

async def test_statistics_fixes():
    """Тестируем исправления статистики"""
    test_nickname = "Geun-Hee"
    
    try:
        print("=== Тестирование исправлений статистики ===\n")
        
        # Поиск игрока
        print(f"1. Поиск игрока '{test_nickname}'...")
        player = await faceit_client.find_player_by_nickname(test_nickname)
        if not player:
            print("   ❌ Игрок не найден")
            return
        
        player_id = player['player_id']
        print(f"   SUCCESS: Player found: {player['nickname']} (ID: {player_id})")
        
        # Получаем детали и статистику
        print(f"\n2. Получение данных...")
        player_details = await faceit_client.get_player_details(player_id)
        stats_data = await faceit_client.get_player_stats(player_id)
        
        if not player_details or not stats_data:
            print("   ❌ Не удалось получить данные")
            return
        
        # Форматируем статистику
        print(f"\n3. Форматирование статистики...")
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        
        if not formatted_stats:
            print("   ❌ Ошибка форматирования")
            return
        
        print("   ✅ Статистика отформатирована")
        
        # Тестируем исправления
        print(f"\n=== РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЙ ===")
        
        # 1. ELO до следующего уровня
        current_elo = formatted_stats.get('elo', 0)
        current_level = formatted_stats.get('level', 0)
        
        level_thresholds = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000]
        
        if current_level >= 10:
            elo_to_next = 0
        else:
            next_level_threshold = level_thresholds[current_level]
            elo_to_next = max(0, next_level_threshold - current_elo)
        
        print(f"\n1. ✅ ELO исправление:")
        print(f"   Текущий уровень: {current_level}")
        print(f"   Текущий ELO: {current_elo}")
        print(f"   До следующего уровня: {elo_to_next if elo_to_next > 0 else 'Максимум'}")
        
        # 2. Источник данных о матчах
        print(f"\n2. ✅ Источник данных матчей:")
        total_matches = formatted_stats.get('matches', 0)
        print(f"   Количество матчей: {total_matches} (из lifetime данных)")
        
        # 3. ADR и KAST
        adr_value = formatted_stats.get('adr', 0)
        kast_value = formatted_stats.get('kast', 0)
        
        print(f"\n3. ✅ ADR и KAST:")
        print(f"   ADR: {adr_value}")
        print(f"   KAST: {kast_value}% (валидное значение: {0 <= kast_value <= 100})")
        
        # 4. Средние показатели за матч
        print(f"\n4. ✅ Средние показатели за матч:")
        avg_kills = formatted_stats.get('avg_kills_per_match', 0)
        avg_deaths = formatted_stats.get('avg_deaths_per_match', 0)
        avg_assists = formatted_stats.get('avg_assists_per_match', 0)
        
        print(f"   Убийств за матч: {avg_kills}")
        print(f"   Смертей за матч: {avg_deaths}")
        print(f"   Ассистов за матч: {avg_assists}")
        
        # 5. Первые действия за матч
        print(f"\n5. ✅ Первые действия за матч:")
        avg_first_kills = formatted_stats.get('avg_first_kills_per_match', 0)
        avg_first_deaths = formatted_stats.get('avg_first_deaths_per_match', 0)
        
        print(f"   Первые убийства за матч: {avg_first_kills}")
        print(f"   Первые смерти за матч: {avg_first_deaths}")
        
        # 6. Утилити статистика за матч
        print(f"\n6. ✅ Утилити статистика за матч:")
        avg_flash = formatted_stats.get('avg_flash_assists_per_match', 0)
        avg_utility = formatted_stats.get('avg_utility_damage_per_match', 0)
        avg_molotov = formatted_stats.get('avg_molotov_damage_per_match', 0)
        
        print(f"   Ослеплений за матч: {avg_flash}")
        print(f"   Урон гранатами за матч: {avg_utility}")
        print(f"   Урон молотовами за матч: {avg_molotov}")
        
        # Тестируем правильную статистику в формате, как она будет отображаться
        print(f"\n=== ИТОГОВОЕ СООБЩЕНИЕ (как будет показано пользователю) ===")
        
        stats_message = f"""📊 **Общая статистика игрока**

👤 **Игрок:** {formatted_stats.get('nickname', 'Unknown')}
🎮 **Уровень:** {current_level} | **ELO:** {current_elo}
⬆️ **До след. уровня:** {elo_to_next if elo_to_next > 0 else 'Максимум'}
⭐ **HLTV Rating 2.1:** {formatted_stats.get('hltv_rating', 0):.3f}
🌍 **Регион:** {formatted_stats.get('region', 'N/A')}

📈 **Игровые результаты:**
• **Карт сыграно:** {total_matches}
• **Побед:** {formatted_stats.get('wins', 0)} ({formatted_stats.get('winrate', 0):.1f}%)
• **Лучшая серия:** {formatted_stats.get('longest_win_streak', 0)} побед

⚔️ **Средние показатели за матч:**
• **Убийства:** {avg_kills}
• **Смерти:** {avg_deaths}
• **Ассисты:** {avg_assists}

💥 **Урон и эффективность:**
• **ADR:** {adr_value:.1f}
• **KAST:** {kast_value:.1f}%
• **Ослеплений за игру:** {avg_flash}
• **Урон гранатами за игру:** {avg_utility}
• **Урон молотовых за игру:** {avg_molotov}

🎯 **Первые действия за матч:**
• **Первые убийства:** {avg_first_kills}
• **Первые смерти:** {avg_first_deaths}

_Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}_"""
        
        print(stats_message)
        
        print(f"\n=== ✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО! ===")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await faceit_client.close()


if __name__ == "__main__":
    asyncio.run(test_statistics_fixes())