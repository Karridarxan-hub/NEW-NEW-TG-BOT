#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient

async def debug_elo_in_matches():
    """Проверяем структуру данных матчей для поиска ELO"""
    client = FaceitAPIClient()
    
    # Тестируем с игроком test
    test_player = "test"
    
    print(f"🔍 Исследование ELO в матчах для игрока: {test_player}")
    print("=" * 60)
    
    try:
        # 1. Находим игрока
        player_data = await client.find_player_by_nickname(test_player)
        if not player_data:
            print(f"❌ Игрок {test_player} не найден")
            return
        
        player_id = player_data['player_id']
        print(f"✅ Игрок найден: {player_data.get('nickname')} (ID: {player_id})")
        
        # 2. Получаем профиль для сравнения ELO
        profile = await client.get_player_details(player_id)
        if profile and 'games' in profile and 'cs2' in profile['games']:
            current_elo = profile['games']['cs2'].get('faceit_elo', 'N/A')
            print(f"📊 Текущий ELO в профиле: {current_elo}")
        
        # 3. Получаем историю матчей
        print("\n🏆 Получаем историю матчей...")
        history_data = await client.get_player_history(player_id, limit=5)
        
        if not history_data or 'items' not in history_data:
            print("❌ Не удалось получить историю матчей")
            return
        
        matches = history_data['items']
        print(f"📋 Найдено {len(matches)} матчей")
        
        # 4. Анализируем структуру каждого матча
        for i, match in enumerate(matches[:3], 1):  # Анализируем первые 3 матча
            print(f"\n🎮 МАТЧ {i}:")
            print(f"   Match ID: {match.get('match_id', 'N/A')}")
            print(f"   Дата: {match.get('started_at', 'N/A')}")
            print(f"   Карта: {match.get('map', {}).get('name', 'N/A')}")
            
            # Ищем ELO в разных местах
            print("\n   🔍 Поиск ELO полей:")
            
            # Прямое поле elo
            if 'elo' in match:
                print(f"      ✅ match['elo']: {match['elo']}")
            else:
                print("      ❌ match['elo']: НЕТ")
            
            # faceit_elo
            if 'faceit_elo' in match:
                print(f"      ✅ match['faceit_elo']: {match['faceit_elo']}")
            else:
                print("      ❌ match['faceit_elo']: НЕТ")
            
            # В teams или players
            if 'teams' in match:
                print("      🏃 Ищем в teams...")
                teams = match['teams']
                for team_name, team_data in teams.items():
                    if isinstance(team_data, dict) and 'players' in team_data:
                        players = team_data['players']
                        for player in players:
                            if player.get('player_id') == player_id:
                                print(f"         Игрок найден в команде {team_name}")
                                if 'elo' in player:
                                    print(f"         ✅ player['elo']: {player['elo']}")
                                if 'faceit_elo' in player:
                                    print(f"         ✅ player['faceit_elo']: {player['faceit_elo']}")
                                if 'player_elo' in player:
                                    print(f"         ✅ player['player_elo']: {player['player_elo']}")
                                print(f"         📋 Все ключи игрока: {list(player.keys())}")
                                break
            
            # Выводим все ключи матча для полной картины
            print(f"      📝 Все ключи матча: {list(match.keys())}")
        
        print("\n" + "=" * 60)
        print("🎯 ВЫВОДЫ:")
        print("Если ELO нет в данных истории матчей, нужно получать его")
        print("из профиля игрока до и после сессии или использовать другой подход.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    # Настройка кодировки для Windows
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    asyncio.run(debug_elo_in_matches())