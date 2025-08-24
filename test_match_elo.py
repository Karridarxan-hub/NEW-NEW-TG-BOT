#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient

async def test_match_elo():
    """Проверяем наличие ELO в деталях матча"""
    client = FaceitAPIClient()
    
    test_player = "test"
    
    print(f"🔍 Проверка ELO в деталях матча для игрока: {test_player}")
    print("=" * 60)
    
    try:
        # 1. Находим игрока
        player_data = await client.find_player_by_nickname(test_player)
        if not player_data:
            print(f"❌ Игрок {test_player} не найден")
            return
        
        player_id = player_data['player_id']
        print(f"✅ Игрок найден: {player_data.get('nickname')} (ID: {player_id})")
        
        # 2. Получаем историю матчей
        history_data = await client.get_player_history(player_id, limit=3)
        
        if not history_data or 'items' not in history_data:
            print("❌ Не удалось получить историю матчей")
            return
        
        matches = history_data['items']
        print(f"📋 Найдено {len(matches)} матчей\n")
        
        # 3. Для каждого матча получаем детали через /matches/{match_id}
        for i, match in enumerate(matches, 1):
            match_id = match.get('match_id')
            if not match_id:
                continue
                
            print(f"🎮 МАТЧ {i}: {match_id}")
            
            # Получаем ДЕТАЛИ матча (не stats!)
            match_details = await client.get_match_details(match_id)
            
            if match_details:
                print(f"   ✅ Детали матча получены")
                
                # Ищем ELO в структуре
                if 'teams' in match_details:
                    teams = match_details['teams']
                    
                    for team_name, team_data in teams.items():
                        if isinstance(team_data, dict) and 'players' in team_data:
                            players = team_data['players']
                            
                            for player in players:
                                if player.get('player_id') == player_id:
                                    print(f"   📊 Игрок найден в команде {team_name}:")
                                    
                                    # Проверяем разные варианты ELO
                                    if 'game_player_id' in player:
                                        print(f"      game_player_id: {player['game_player_id']}")
                                    if 'game_skill_level' in player:
                                        print(f"      game_skill_level: {player['game_skill_level']}")
                                    if 'elo' in player:
                                        print(f"      ✨ ELO: {player['elo']}")
                                    if 'faceit_elo' in player:
                                        print(f"      ✨ FACEIT_ELO: {player['faceit_elo']}")
                                    
                                    print(f"      📝 Все поля игрока: {list(player.keys())}")
                                    break
                
                # Проверяем есть ли другие места с ELO
                if 'elo' in match_details:
                    print(f"   🎯 ELO в корне: {match_details['elo']}")
                    
                # Проверяем результаты
                if 'results' in match_details:
                    print(f"   📈 Результаты: {match_details['results']}")
                    
                print(f"   📝 Корневые ключи: {list(match_details.keys())[:10]}...")
            else:
                print(f"   ❌ Не удалось получить детали матча")
            
            print()
        
        print("=" * 60)
        print("💡 ВЫВОД:")
        print("Если ELO есть в деталях матча, можно отслеживать изменения")
        print("между матчами для расчета динамики за сессию.")
        
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
    
    asyncio.run(test_match_elo())