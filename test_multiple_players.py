#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient


async def test_multiple_players():
    """Тест HLTV 2.1 рейтинга для нескольких игроков"""
    client = FaceitAPIClient()
    test_nicknames = ["Geun-Hee", "s1mple", "ZywOo"]
    
    try:
        print("=== Multiple Players HLTV 2.1 Test ===\n")
        
        for nickname in test_nicknames:
            print(f"Testing player: {nickname}")
            print("-" * 40)
            
            # Поиск игрока
            player = await client.find_player_by_nickname(nickname)
            if not player:
                print(f"   Player {nickname} not found\n")
                continue
            
            player_id = player['player_id']
            
            # Получение полного профиля
            full_profile = await client.get_player_full_profile(nickname)
            if not full_profile:
                print(f"   Failed to get full profile for {nickname}\n")
                continue
            
            stats = full_profile.get('stats', {})
            data_quality = full_profile.get('data_quality', {})
            data_source = stats.get('data_source', {})
            
            # Отображаем результаты
            print(f"   Player Info:")
            print(f"     Nickname: {stats.get('nickname', 'N/A')}")
            print(f"     Level: {stats.get('level', 'N/A')}")
            print(f"     ELO: {stats.get('elo', 'N/A')}")
            
            print(f"   HLTV 2.1 Metrics:")
            print(f"     ADR: {stats.get('adr', 'N/A')}")
            print(f"     KAST: {stats.get('kast', 'N/A')}%")
            print(f"     K/D Ratio: {stats.get('kd_ratio', 'N/A')}")
            print(f"     HLTV Rating 2.1: {stats.get('hltv_rating', 'N/A')}")
            
            print(f"   Data Quality:")
            print(f"     Source: {data_quality.get('recommended_source', 'N/A')}")
            print(f"     Completeness: {data_quality.get('data_completeness_score', 0)}%")
            print(f"     Map segments: {data_quality.get('map_segments_count', 0)}")
            print(f"     Can aggregate: {data_quality.get('can_aggregate_maps', False)}")
            
            print(f"   Extended Metrics:")
            print(f"     First Kills: {stats.get('first_kills', 'N/A')}")
            print(f"     Flash Assists: {stats.get('flash_assists', 'N/A')}")
            print(f"     Utility Damage: {stats.get('utility_damage', 'N/A')}")
            
            # Топ карты по HLTV рейтингу
            maps = stats.get('maps', {})
            if maps:
                print(f"   Top Maps by HLTV Rating:")
                sorted_maps = sorted(maps.items(), key=lambda x: x[1].get('hltv_rating', 0), reverse=True)
                for i, (map_name, map_data) in enumerate(sorted_maps[:3]):
                    print(f"     {i+1}. {map_name}: {map_data.get('hltv_rating', 'N/A')} (ADR: {map_data.get('adr', 'N/A')}, KAST: {map_data.get('kast', 'N/A')}%)")
            
            print()
        
        print("=== Test Completed ===")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_multiple_players())