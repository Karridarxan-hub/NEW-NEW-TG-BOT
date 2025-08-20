#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient


async def test_hltv_rating_calculation():
    """Тест расчета HLTV 2.1 рейтинга с приоритетом segments/Overall"""
    client = FaceitAPIClient()
    test_nickname = "Geun-Hee"
    
    try:
        print("=== HLTV 2.1 Rating Test ===\n")
        
        # Поиск игрока
        print(f"1. Searching for player '{test_nickname}'...")
        player = await client.find_player_by_nickname(test_nickname)
        if not player:
            print("   Player not found")
            return
        
        player_id = player['player_id']
        print(f"   Player found: {player['nickname']} (ID: {player_id})")
        
        # Получение расширенной статистики
        print(f"\n2. Getting enhanced player stats...")
        enhanced_stats = await client.get_enhanced_player_stats(player_id)
        if not enhanced_stats:
            print("   Failed to get enhanced stats")
            return
        
        print("   Enhanced stats retrieved successfully")
        
        # Анализ качества данных
        if 'data_quality' in enhanced_stats:
            quality = enhanced_stats['data_quality']
            print(f"\n3. Data Quality Analysis:")
            print(f"   - Has segments: {quality.get('has_segments', False)}")
            print(f"   - Has overall segment: {quality.get('has_overall_segment', False)}")  
            print(f"   - Has lifetime: {quality.get('has_lifetime', False)}")
            print(f"   - Recommended source: {quality.get('recommended_source', 'none')}")
            print(f"   - Data completeness: {quality.get('data_completeness_score', 0)}%")
            print(f"   - Available metrics: {len(quality.get('critical_metrics_available', []))}")
            print(f"   - Missing metrics: {quality.get('missing_metrics', [])}")
        
        # Получение деталей игрока
        print(f"\n4. Getting player details...")
        player_details = await client.get_player_details(player_id)
        if not player_details:
            print("   Failed to get player details")
            return
        
        # Форматирование статистики
        print(f"\n5. Formatting player stats...")
        formatted_stats = client.format_player_stats(player_details, enhanced_stats)
        if not formatted_stats:
            print("   Failed to format stats")
            return
        
        print("   Stats formatted successfully")
        
        # Отображение ключевых метрик
        print(f"\n6. Key Metrics for HLTV 2.1 Rating:")
        print(f"   - Nickname: {formatted_stats.get('nickname', 'N/A')}")
        print(f"   - Level: {formatted_stats.get('level', 'N/A')}")
        print(f"   - ELO: {formatted_stats.get('elo', 'N/A')}")
        print(f"   - ADR: {formatted_stats.get('adr', 'N/A')}")
        print(f"   - KAST: {formatted_stats.get('kast', 'N/A')}%")
        print(f"   - K/D Ratio: {formatted_stats.get('kd_ratio', 'N/A')}")
        print(f"   - HLTV Rating 2.1: {formatted_stats.get('hltv_rating', 'N/A')}")
        
        # Дополнительные метрики
        print(f"\n7. Additional Metrics:")
        print(f"   - First Kills: {formatted_stats.get('first_kills', 'N/A')}")
        print(f"   - First Deaths: {formatted_stats.get('first_deaths', 'N/A')}")
        print(f"   - Flash Assists: {formatted_stats.get('flash_assists', 'N/A')}")
        print(f"   - Utility Damage: {formatted_stats.get('utility_damage', 'N/A')}")
        
        # Информация об источнике данных
        if 'data_source' in formatted_stats:
            data_source = formatted_stats['data_source']
            print(f"\n8. Data Source Information:")
            print(f"   - HLTV rating calculated from: {data_source.get('hltv_rating_from', 'unknown')}")
            print(f"   - Has segments: {data_source.get('has_segments', False)}")
            print(f"   - Has overall segment: {data_source.get('has_overall_segment', False)}")
            print(f"   - Has lifetime: {data_source.get('has_lifetime', False)}")
        
        # Тестирование расчета рейтинга напрямую
        print(f"\n9. Direct Rating Calculation Test:")
        
        # Из segments/Overall если доступно
        segments = enhanced_stats.get('segments', [])
        overall_segment = next((s for s in segments if s.get('label') == 'Overall'), None)
        
        if overall_segment and 'stats' in overall_segment:
            segment_stats = overall_segment['stats']
            segment_rating = client.calculate_hltv_rating(segment_stats)
            print(f"   - Rating from segments/Overall: {segment_rating}")
            
            # Показываем ключевые данные из segments
            print(f"   - Segments data:")
            print(f"     * ADR: {segment_stats.get('ADR', 'N/A')}")
            print(f"     * KAST: {segment_stats.get('KAST %', 'N/A')}%")
            print(f"     * K/D Ratio: {segment_stats.get('K/D Ratio', 'N/A')}")
            print(f"     * Kills: {segment_stats.get('Kills', 'N/A')}")
            print(f"     * Deaths: {segment_stats.get('Deaths', 'N/A')}")
            print(f"     * Rounds: {segment_stats.get('Rounds', 'N/A')}")
        
        # Из lifetime для сравнения
        lifetime_stats = enhanced_stats.get('lifetime', {})
        if lifetime_stats:
            lifetime_rating = client.calculate_hltv_rating(lifetime_stats)
            print(f"   - Rating from lifetime: {lifetime_rating}")
            
            print(f"   - Lifetime data:")
            print(f"     * K/D Ratio: {lifetime_stats.get('K/D Ratio', 'N/A')}")
            print(f"     * Kills: {lifetime_stats.get('Kills', 'N/A')}")
            print(f"     * Deaths: {lifetime_stats.get('Deaths', 'N/A')}")
        
        print(f"\n=== Test Completed Successfully ===")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_hltv_rating_calculation())