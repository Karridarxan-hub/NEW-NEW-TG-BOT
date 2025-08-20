#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faceit_client import FaceitAPIClient

async def investigate_faceit_api_structure():
    """Детальное исследование структуры FACEIT API для поиска правильных данных"""
    client = FaceitAPIClient()
    
    # Тестируем с несколькими игроками для полноты картины
    test_players = ["test", "shroud", "s1mple"]  # Игроки с разным количеством матчей
    
    for nickname in test_players:
        print(f"\n{'='*80}")
        print(f"🔍 ИССЛЕДОВАНИЕ ИГРОКА: {nickname}")
        print(f"{'='*80}")
        
        try:
            # 1. Поиск игрока
            print("1️⃣ Поиск игрока...")
            player = await client.find_player_by_nickname(nickname)
            if not player:
                print(f"❌ Игрок {nickname} не найден")
                continue
                
            player_id = player.get('player_id')
            print(f"✅ Найден: {player.get('nickname')} (ID: {player_id})")
            
            # 2. Детали игрока
            print("\n2️⃣ Детали игрока...")
            details = await client.get_player_details(player_id)
            if details and 'games' in details and 'cs2' in details['games']:
                cs2_info = details['games']['cs2']
                print(f"📊 CS2 данные:")
                print(f"   - Уровень: {cs2_info.get('skill_level', 'N/A')}")
                print(f"   - ELO: {cs2_info.get('faceit_elo', 'N/A')}")
                print(f"   - Регион: {cs2_info.get('region', 'N/A')}")
            
            # 3. Статистика - САМОЕ ВАЖНОЕ
            print("\n3️⃣ СТАТИСТИКА - ДЕТАЛЬНЫЙ АНАЛИЗ:")
            stats = await client.get_player_stats(player_id)
            if not stats:
                print("❌ Статистика недоступна")
                continue
                
            # Анализируем LIFETIME данные
            print("\n📈 LIFETIME ДАННЫЕ:")
            lifetime = stats.get('lifetime', {})
            if lifetime:
                matches_lifetime = lifetime.get('Matches', 'НЕТ ДАННЫХ')
                wins_lifetime = lifetime.get('Wins', 'НЕТ ДАННЫХ') 
                winrate_lifetime = lifetime.get('Win Rate %', 'НЕТ ДАННЫХ')
                print(f"   🎯 Матчи (lifetime): {matches_lifetime}")
                print(f"   🏆 Победы (lifetime): {wins_lifetime}")
                print(f"   📊 Винрейт (lifetime): {winrate_lifetime}%")
                print(f"   🔑 Ключи в lifetime: {list(lifetime.keys())}")
            else:
                print("   ❌ Lifetime данных нет")
            
            # Анализируем SEGMENTS
            print("\n📊 SEGMENTS ДАННЫЕ:")
            segments = stats.get('segments', [])
            print(f"   📋 Всего сегментов: {len(segments)}")
            
            for i, segment in enumerate(segments):
                segment_type = segment.get('type', 'Unknown')
                segment_label = segment.get('label', 'No label')
                print(f"\n   📂 Сегмент {i+1}: {segment_type} - {segment_label}")
                
                # Ищем данные о матчах в каждом сегменте
                if 'stats' in segment:
                    seg_stats = segment['stats']
                    
                    # Проверяем есть ли информация о матчах
                    matches_keys = [k for k in seg_stats.keys() if 'match' in k.lower()]
                    game_keys = [k for k in seg_stats.keys() if any(word in k.lower() for word in ['game', 'round', 'total'])]
                    
                    print(f"      🎮 Ключи связанные с матчами: {matches_keys}")
                    print(f"      🎯 Ключи игровых данных: {game_keys[:10]}...")  # Показываем первые 10
                    
                    # Ищем конкретные метрики
                    important_keys = ['Matches', 'Games', 'Rounds', 'Wins', 'Win Rate %', 'Kills', 'Deaths', 'K/D Ratio']
                    for key in important_keys:
                        if key in seg_stats:
                            value = seg_stats[key]
                            print(f"      ✅ {key}: {value}")
            
            # Анализируем Enhanced stats
            print("\n4️⃣ ENHANCED СТАТИСТИКА:")
            enhanced = await client.get_enhanced_player_stats(player_id)
            if enhanced:
                print("   ✅ Enhanced статистика доступна")
                if 'segments' in enhanced:
                    print(f"   📊 Enhanced сегментов: {len(enhanced['segments'])}")
                if 'lifetime' in enhanced:
                    enhanced_lifetime = enhanced['lifetime']
                    enhanced_matches = enhanced_lifetime.get('Matches', 'НЕТ')
                    print(f"   🎯 Enhanced Матчи: {enhanced_matches}")
            
            # 5. История матчей для проверки
            print("\n5️⃣ ПРОВЕРКА ЧЕРЕЗ ИСТОРИЮ МАТЧЕЙ:")
            # Запрашиваем большое количество для подсчета реального числа
            history = await client.get_player_history(player_id, limit=100)
            if history and 'items' in history:
                actual_matches_in_history = len(history['items'])
                print(f"   📝 Матчей в истории (лимит 100): {actual_matches_in_history}")
                
                # Если получили 100, значит их больше - попробуем получить еще
                if actual_matches_in_history == 100:
                    print("   ⚠️  Вероятно матчей больше 100, проверяем дальше...")
                    
                    # Проверим разные offset'ы чтобы понять реальное количество
                    total_found = 100
                    offset = 100
                    
                    while offset < 3000:  # Максимум проверим до 3000
                        batch = await client.get_player_history(player_id, limit=100, offset=offset)
                        if batch and 'items' in batch and len(batch['items']) > 0:
                            batch_size = len(batch['items'])
                            total_found += batch_size
                            print(f"   📝 Offset {offset}: найдено еще {batch_size} матчей")
                            if batch_size < 100:  # Последняя порция
                                break
                            offset += 100
                        else:
                            break
                    
                    print(f"   🎯 РЕАЛЬНОЕ КОЛИЧЕСТВО МАТЧЕЙ: ~{total_found}")
            
            print(f"\n{'='*40} ВЫВОДЫ {'='*40}")
            print(f"Игрок: {nickname}")
            print(f"Lifetime Матчи: {lifetime.get('Matches', 'НЕТ') if lifetime else 'НЕТ LIFETIME'}")
            print(f"Реальные матчи из истории: {total_found if 'total_found' in locals() else 'Неизвестно'}")
            print("="*80)
            
        except Exception as e:
            print(f"❌ Ошибка при обработке игрока {nickname}: {e}")
    
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
    
    asyncio.run(investigate_faceit_api_structure())