"""
Отладка функциональности сравнения игроков
"""

import asyncio
import json
from faceit_client import FaceitAPIClient


async def debug_player_profile(nickname: str):
    """Отладка получения профиля игрока"""
    print(f"\n=== Отладка профиля игрока: {nickname} ===")
    
    client = FaceitAPIClient()
    
    try:
        # Получаем полный профиль
        print("1. Вызов get_player_full_profile...")
        profile = await client.get_player_full_profile(nickname)
        
        if profile:
            print("2. Профиль получен успешно!")
            
            # Выводим структуру
            print("3. Ключи верхнего уровня:")
            for key in profile.keys():
                print(f"   - {key}: {type(profile[key])}")
            
            # Проверяем stats
            if 'stats' in profile:
                stats = profile['stats']
                print("\n4. Содержимое profile['stats']:")
                print(f"   - nickname: {stats.get('nickname')}")
                print(f"   - level: {stats.get('level')}")
                print(f"   - elo: {stats.get('elo')}")
                print(f"   - winrate: {stats.get('winrate')}")
                print(f"   - kd_ratio: {stats.get('kd_ratio')}")
                print(f"   - matches: {stats.get('matches')}")
            else:
                print("\n4. ПРОБЛЕМА: Нет поля 'stats' в профиле!")
                
                # Проверяем альтернативные места
                print("\n   Проверка альтернативных мест:")
                for key, value in profile.items():
                    if isinstance(value, dict) and ('level' in value or 'elo' in value):
                        print(f"   Найдены данные в '{key}': {value}")
            
            # Симулируем добавление в сравнение
            print("\n5. Симуляция добавления в сравнение:")
            player_stats = profile.get('stats', {})
            comparison_data = {
                'nickname': player_stats.get('nickname', nickname),
                'skill_level': player_stats.get('level', 0),
                'faceit_elo': player_stats.get('elo', 0)
            }
            
            print(f"   Результат:")
            for key, value in comparison_data.items():
                print(f"      {key}: {value}")
            
            # Проверка на нулевые значения
            if comparison_data['skill_level'] == 0 and comparison_data['faceit_elo'] == 0:
                print("\n   ❌ ПРОБЛЕМА: Данные остаются нулевыми!")
                
                # Дополнительная диагностика
                print("\n   Дополнительная диагностика:")
                if 'details' in profile:
                    details = profile['details']
                    cs2_data = details.get('games', {}).get('cs2', {})
                    print(f"      details.games.cs2.skill_level: {cs2_data.get('skill_level')}")
                    print(f"      details.games.cs2.faceit_elo: {cs2_data.get('faceit_elo')}")
            else:
                print("\n   ✅ УСПЕХ: Данные извлечены корректно!")
                
        else:
            print("2. ❌ Профиль не получен!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    await client.close()


async def main():
    """Тестирование нескольких игроков"""
    test_players = ["s1mple", "Geun-Hee", "Raoni4", "NiKo"]
    
    for player in test_players:
        await debug_player_profile(player)
        print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())