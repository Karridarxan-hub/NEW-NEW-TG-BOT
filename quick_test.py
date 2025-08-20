#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient

async def quick_test():
    """Быстрое тестирование исправлений"""
    client = FaceitAPIClient()
    test_nickname = "Geun-Hee"
    
    try:
        print("=== БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ ===")
        
        # 1. Поиск игрока
        print(f"\n1. Поиск игрока {test_nickname}...")
        player = await client.find_player_by_nickname(test_nickname)
        if not player:
            print("❌ Игрок не найден")
            return
        
        player_id = player['player_id']
        print(f"✅ Найден: {player['nickname']} (ID: {player_id})")
        
        # 2. Получение статистики
        print(f"\n2. Получение статистики...")
        formatted_stats = await client.format_player_stats(player_id, player['nickname'])
        if not formatted_stats:
            print("❌ Статистика не получена")
            return
        
        print("✅ Статистика получена")
        
        # 3. Проверяем ключевые исправления
        print(f"\n=== ПРОВЕРКА ИСПРАВЛЕНИЙ ===")
        
        # Подсчет матчей
        if "Матчи:" in formatted_stats:
            matches_line = [line for line in formatted_stats.split('\n') if 'Матчи:' in line][0]
            matches_count = matches_line.split(':')[1].strip()
            print(f"📊 Количество матчей: {matches_count}")
            if "1104" in matches_count:
                print("✅ ИСПРАВЛЕНО: Матчи показывают 1104")
            else:
                print(f"⚠️ Матчи: {matches_count} (ожидали 1104)")
        
        # K/D Ratio
        if "K/D:" in formatted_stats:
            kd_line = [line for line in formatted_stats.split('\n') if 'K/D:' in line][0]
            kd_value = kd_line.split(':')[1].strip()
            print(f"⚔️ K/D Ratio: {kd_value}")
            try:
                kd_float = float(kd_value)
                if 0.5 <= kd_float <= 5.0:
                    print("✅ ИСПРАВЛЕНО: K/D в разумных пределах")
                else:
                    print(f"⚠️ K/D выглядит странно: {kd_float}")
            except ValueError:
                print(f"⚠️ K/D не является числом: {kd_value}")
        
        # Молотов урон
        if "Молотовы:" in formatted_stats:
            molotov_line = [line for line in formatted_stats.split('\n') if 'Молотовы:' in line][0]
            molotov_damage = molotov_line.split(':')[1].strip()
            print(f"🔥 Урон молотовами: {molotov_damage}")
            try:
                dmg_float = float(molotov_damage.split()[0])  # Берем только число
                if dmg_float > 0:
                    print("✅ ИСПРАВЛЕНО: Урон молотовами > 0")
                else:
                    print("⚠️ Урон молотовами всё еще 0.0")
            except (ValueError, IndexError):
                print(f"⚠️ Не удалось парсить урон молотовами: {molotov_damage}")
        
        print(f"\n=== ПОЛНАЯ СТАТИСТИКА ===")
        print(formatted_stats[:1000] + "..." if len(formatted_stats) > 1000 else formatted_stats)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(quick_test())