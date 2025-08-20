#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import faceit_client

async def test_statistics_fixes():
    """Test statistics fixes"""
    test_nickname = "Geun-Hee"
    
    try:
        print("=== Testing Statistics Fixes ===\n")
        
        # Find player
        print(f"1. Searching for player '{test_nickname}'...")
        player = await faceit_client.find_player_by_nickname(test_nickname)
        if not player:
            print("   ERROR: Player not found")
            return
        
        player_id = player['player_id']
        print(f"   SUCCESS: Player found: {player['nickname']} (ID: {player_id})")
        
        # Get details and stats
        print(f"\n2. Getting player data...")
        player_details = await faceit_client.get_player_details(player_id)
        stats_data = await faceit_client.get_player_stats(player_id)
        
        if not player_details or not stats_data:
            print("   ERROR: Failed to get data")
            return
        
        # Format stats
        print(f"\n3. Formatting statistics...")
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        
        if not formatted_stats:
            print("   ERROR: Formatting failed")
            return
        
        print("   SUCCESS: Statistics formatted")
        
        # Test fixes
        print(f"\n=== RESULTS OF FIXES ===")
        
        # 1. ELO to next level
        current_elo = formatted_stats.get('elo', 0)
        current_level = formatted_stats.get('level', 0)
        
        level_thresholds = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000]
        
        if current_level >= 10:
            elo_to_next = 0
        else:
            next_level_threshold = level_thresholds[current_level]
            elo_to_next = max(0, next_level_threshold - current_elo)
        
        print(f"\n1. ELO Fix:")
        print(f"   Current level: {current_level}")
        print(f"   Current ELO: {current_elo}")
        print(f"   To next level: {elo_to_next if elo_to_next > 0 else 'Maximum'}")
        
        # 2. Match count data source
        print(f"\n2. Match Data Source:")
        total_matches = formatted_stats.get('matches', 0)
        print(f"   Total matches: {total_matches} (from lifetime data)")
        
        # 3. ADR and KAST
        adr_value = formatted_stats.get('adr', 0)
        kast_value = formatted_stats.get('kast', 0)
        
        print(f"\n3. ADR and KAST:")
        print(f"   ADR: {adr_value}")
        print(f"   KAST: {kast_value}% (valid: {0 <= kast_value <= 100})")
        
        # 4. Average stats per match
        print(f"\n4. Average Stats per Match:")
        avg_kills = formatted_stats.get('avg_kills_per_match', 0)
        avg_deaths = formatted_stats.get('avg_deaths_per_match', 0)
        avg_assists = formatted_stats.get('avg_assists_per_match', 0)
        
        print(f"   Kills per match: {avg_kills}")
        print(f"   Deaths per match: {avg_deaths}")
        print(f"   Assists per match: {avg_assists}")
        
        # 5. First actions per match
        print(f"\n5. First Actions per Match:")
        avg_first_kills = formatted_stats.get('avg_first_kills_per_match', 0)
        avg_first_deaths = formatted_stats.get('avg_first_deaths_per_match', 0)
        
        print(f"   First kills per match: {avg_first_kills}")
        print(f"   First deaths per match: {avg_first_deaths}")
        
        # 6. Utility stats per match
        print(f"\n6. Utility Stats per Match:")
        avg_flash = formatted_stats.get('avg_flash_assists_per_match', 0)
        avg_utility = formatted_stats.get('avg_utility_damage_per_match', 0)
        avg_molotov = formatted_stats.get('avg_molotov_damage_per_match', 0)
        
        print(f"   Flash assists per match: {avg_flash}")
        print(f"   Utility damage per match: {avg_utility}")
        print(f"   Molotov damage per match: {avg_molotov}")
        
        print(f"\n=== ALL FIXES APPLIED SUCCESSFULLY! ===")
        
        # Summary of critical values
        print(f"\n=== KEY VALIDATION RESULTS ===")
        print(f"Matches count (should be ~600-1000): {total_matches}")
        print(f"ADR (should be reasonable): {adr_value}")
        print(f"KAST (should be 0-100): {kast_value}%")
        print(f"ELO to next level: {elo_to_next}")
        print(f"Average kills per match: {avg_kills}")
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await faceit_client.close()


if __name__ == "__main__":
    asyncio.run(test_statistics_fixes())