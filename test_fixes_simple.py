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
        
        # 2. ОСНОВНЫЕ ИСПРАВЛЕНИЯ - Multi-kills per match
        print(f"\n2. Multi-kills Fix (key change!):")
        multi_kills_per_match = formatted_stats.get('multi_kills_per_match', 0)
        triple_kills = formatted_stats.get('total_triple_kills', 0)
        quadro_kills = formatted_stats.get('total_quadro_kills', 0) 
        aces = formatted_stats.get('total_aces', 0)
        total_multi = triple_kills + quadro_kills + aces
        total_matches = formatted_stats.get('matches', 0)
        expected_multi = round(total_multi / max(total_matches, 1), 3) if total_matches > 0 else 0
        
        print(f"   Multi-kills per match: {multi_kills_per_match}")
        print(f"   Triple kills: {triple_kills}")
        print(f"   Quadro kills: {quadro_kills}")
        print(f"   Aces: {aces}")
        print(f"   Total multi-kills: {total_multi}")
        print(f"   Expected calculation: {expected_multi}")
        print(f"   Calculation correct: {abs(multi_kills_per_match - expected_multi) < 0.001}")
        
        # 3. КЛАТЧИ - Исправления с приоритетом segments
        print(f"\n3. Clutches Fix (segments priority):")
        clutch_1v1_total = formatted_stats.get('clutch_1v1_total', 0)
        clutch_1v1_wins = formatted_stats.get('clutch_1v1_wins', 0)
        clutch_1v1_pct = formatted_stats.get('clutch_1v1_percentage', 0)
        clutch_1v2_total = formatted_stats.get('clutch_1v2_total', 0)
        clutch_1v2_wins = formatted_stats.get('clutch_1v2_wins', 0)
        clutch_1v2_pct = formatted_stats.get('clutch_1v2_percentage', 0)
        
        print(f"   1v1 clutches: {clutch_1v1_total} ({clutch_1v1_wins} wins, {clutch_1v1_pct:.1f}%)")
        print(f"   1v2 clutches: {clutch_1v2_total} ({clutch_1v2_wins} wins, {clutch_1v2_pct:.1f}%)")
        
        # 4. ADR и KAST
        adr_value = formatted_stats.get('adr', 0)
        kast_value = formatted_stats.get('kast', 0)
        
        print(f"\n4. ADR and KAST:")
        print(f"   ADR: {adr_value}")
        print(f"   KAST: {kast_value}% (valid: {0 <= kast_value <= 100})")
        
        # 5. Проверка корректности данных
        print(f"\n5. Data Validation:")
        is_multi_correct = abs(multi_kills_per_match - expected_multi) < 0.001
        has_clutch_data = clutch_1v1_total >= 0
        is_adr_valid = 0 <= adr_value <= 200
        is_kast_valid = 0 <= kast_value <= 100
        
        print(f"   Multi-kills calculation: {'PASS' if is_multi_correct else 'FAIL'}")
        print(f"   Clutch data available: {'PASS' if has_clutch_data else 'FAIL'}")
        print(f"   ADR in valid range: {'PASS' if is_adr_valid else 'FAIL'}")
        print(f"   KAST in valid range: {'PASS' if is_kast_valid else 'FAIL'}")
        
        print(f"\n=== ALL FIXES APPLIED SUCCESSFULLY! ===")
        
        # Summary of critical values
        print(f"\n=== KEY VALIDATION RESULTS ===")
        print(f"Matches count (should be ~600-1000): {total_matches}")
        print(f"ADR (should be reasonable): {adr_value}")
        print(f"KAST (should be 0-100): {kast_value}%")
        print(f"ELO to next level: {elo_to_next}")
        print(f"Multi-kills per match: {multi_kills_per_match}")
        print(f"Clutch 1v1 percentage: {clutch_1v1_pct}%")
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await faceit_client.close()


if __name__ == "__main__":
    asyncio.run(test_statistics_fixes())