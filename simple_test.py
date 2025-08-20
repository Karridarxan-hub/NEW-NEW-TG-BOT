#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient

async def simple_test():
    """Простое тестирование без эмодзи"""
    client = FaceitAPIClient()
    test_nickname = "Geun-Hee"
    
    try:
        print("=== ТЕСТ ИСПРАВЛЕНИЙ ===")
        
        # 1. Поиск игрока
        print(f"\n1. Поиск игрока {test_nickname}...")
        player = await client.find_player_by_nickname(test_nickname)
        if not player:
            print("FAIL: Игрок не найден")
            return
        
        player_id = player['player_id']
        print(f"OK: Найден {player['nickname']} (ID: {player_id})")
        
        # 2. Получение raw статистики для проверки
        print(f"\n2. Получение raw данных...")
        stats = await client.get_player_stats(player_id)
        if not stats:
            print("FAIL: Статистика не получена")
            return
        
        # Проверяем segments данные
        segments = stats.get('segments', [])
        print(f"OK: Получено {len(segments)} сегментов")
        
        # Считаем матчи из segments
        total_matches = 0
        for segment in segments:
            if 'stats' in segment:
                matches = segment['stats'].get('Matches', 0)
                total_matches += int(matches) if matches else 0
        
        print(f"ПОДСЧЕТ: Всего матчей из segments: {total_matches}")
        
        # 3. Получение детальных данных игрока
        print(f"\n3. Получение детальных данных...")
        player_details = await client.get_player_details(player_id)
        if not player_details:
            print("FAIL: Детальные данные не получены")
            return
            
        # 4. Форматирование статистики
        print(f"\n4. Форматирование статистики...")
        formatted_stats = client.format_player_stats(player_details, stats)
        if not formatted_stats:
            print("FAIL: Форматированная статистика не получена")
            return
        
        print("OK: Статистика отформатирована")
        
        # Проверяем ключевые исправления
        print(f"\n=== РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЙ ===")
        
        # Проверяем ключевые метрики
        if 'matches' in formatted_stats:
            print(f"МАТЧИ: {formatted_stats['matches']}")
            if formatted_stats['matches'] == 1104:
                print("✅ ИСПРАВЛЕНО: Матчи показывают корректное значение 1104")
            else:
                print(f"⚠️ Матчи: {formatted_stats['matches']} (ожидали 1104)")
        
        if 'kd_ratio' in formatted_stats:
            kd_value = formatted_stats['kd_ratio']
            print(f"K/D: {kd_value}")
            if 0.5 <= kd_value <= 5.0:
                print("✅ ИСПРАВЛЕНО: K/D в разумных пределах")
            else:
                print(f"⚠️ K/D выглядит странно: {kd_value}")
        
        if 'molotov_damage' in formatted_stats:
            molotov_damage = formatted_stats['molotov_damage']
            print(f"МОЛОТОВЫ: {molotov_damage}")
            if molotov_damage > 0:
                print("✅ ИСПРАВЛЕНО: Урон молотовами > 0")
            else:
                print("⚠️ Урон молотовами всё еще 0.0")
        
        print(f"\nВСЕ КЛЮЧИ В СТАТИСТИКЕ:")
        print(list(formatted_stats.keys()))
        
        print(f"\nПЕРВЫЕ ЗНАЧЕНИЯ:")
        for key, value in list(formatted_stats.items())[:10]:
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    # Настройка кодировки для Windows
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    
    asyncio.run(simple_test())