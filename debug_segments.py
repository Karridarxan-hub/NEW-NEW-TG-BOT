#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import json

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient


async def debug_segments():
    """Отладка структуры segments данных"""
    client = FaceitAPIClient()
    test_nickname = "Geun-Hee"
    
    try:
        print("=== Debug Segments Data ===\n")
        
        # Поиск игрока
        player = await client.find_player_by_nickname(test_nickname)
        if not player:
            print("Player not found")
            return
        
        player_id = player['player_id']
        print(f"Player: {player['nickname']} (ID: {player_id})")
        
        # Получение RAW статистики
        print(f"\nGetting raw player stats...")
        stats = await client.get_player_stats(player_id)
        if not stats:
            print("Failed to get stats")
            return
        
        # Показываем структуру данных
        print(f"\n=== Raw Data Structure ===")
        
        # Lifetime данные
        if 'lifetime' in stats:
            print(f"\nLifetime data available:")
            lifetime = stats['lifetime']
            for key, value in lifetime.items():
                print(f"  {key}: {value}")
        
        # Segments данные
        if 'segments' in stats:
            segments = stats['segments']
            print(f"\nSegments data ({len(segments)} segments):")
            
            for i, segment in enumerate(segments):
                print(f"\n  Segment {i+1}:")
                print(f"    Label: {segment.get('label', 'N/A')}")
                print(f"    Type: {segment.get('type', 'N/A')}")
                
                if 'stats' in segment:
                    segment_stats = segment['stats']
                    print(f"    Stats ({len(segment_stats)} metrics):")
                    for key, value in segment_stats.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"    No stats in this segment")
        else:
            print("\nNo segments data available")
        
        # Тестируем другого игрока, который может иметь более полные данные
        print(f"\n=== Testing with another player ===")
        test_nicknames = ["s1mple", "ZywOo", "sh1ro", "electronic"]
        
        for nickname in test_nicknames:
            print(f"\nTrying player: {nickname}")
            player2 = await client.find_player_by_nickname(nickname)
            if not player2:
                print(f"  Player {nickname} not found")
                continue
            
            player2_id = player2['player_id']
            stats2 = await client.get_player_stats(player2_id)
            
            if stats2 and 'segments' in stats2:
                segments2 = stats2['segments']
                overall_segment = next((s for s in segments2 if s.get('label') == 'Overall'), None)
                
                if overall_segment:
                    print(f"  SUCCESS: {nickname} has Overall segment!")
                    overall_stats = overall_segment.get('stats', {})
                    print(f"  Overall segment metrics:")
                    for key, value in overall_stats.items():
                        print(f"    {key}: {value}")
                    
                    # Тестируем расчет рейтинга
                    rating = client.calculate_hltv_rating(overall_stats)
                    print(f"  HLTV 2.1 Rating: {rating}")
                    break
                else:
                    print(f"  {nickname} has segments but no Overall segment")
                    segment_labels = [s.get('label', 'N/A') for s in segments2]
                    print(f"  Available segments: {segment_labels}")
            else:
                print(f"  {nickname} has no segments data")
    
    except Exception as e:
        print(f"\nError during debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(debug_segments())