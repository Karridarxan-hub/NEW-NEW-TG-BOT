"""
Простое тестирование извлечения данных без подключения к БД
"""

import asyncio
import logging
from faceit_client import FaceitAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_profile_structure():
    """Тестирование структуры профиля без БД"""
    print("\n=== Тестирование структуры профиля FACEIT ===\n")
    
    client = FaceitAPIClient()
    
    test_nickname = "s1mple"
    
    try:
        # Получаем базовые данные игрока
        print(f"1. Поиск игрока {test_nickname}...")
        player = await client.find_player_by_nickname(test_nickname)
        
        if player:
            print(f"   НАЙДЕН: {player.get('nickname')} (ID: {player.get('player_id')})")
            player_id = player['player_id']
            
            # Получаем детали
            print(f"\n2. Получение деталей игрока...")
            details = await client.get_player_details(player_id)
            
            if details:
                # Проверяем CS2 данные
                cs2_data = details.get('games', {}).get('cs2', {})
                print(f"   CS2 данные:")
                print(f"      - skill_level: {cs2_data.get('skill_level', 'НЕТ')}")
                print(f"      - faceit_elo: {cs2_data.get('faceit_elo', 'НЕТ')}")
                
                # Получаем статистику
                print(f"\n3. Получение статистики...")
                stats = await client.get_player_stats(player_id)
                
                if stats:
                    print(f"   Статистика получена")
                    
                    # Проверяем lifetime
                    lifetime = stats.get('lifetime', {})
                    print(f"      - Lifetime данные: {len(lifetime)} полей")
                    
                    # Проверяем segments
                    segments = stats.get('segments', [])
                    print(f"      - Segments: {len(segments)} сегментов")
                    
                    # Форматируем статистику
                    print(f"\n4. Форматирование статистики...")
                    formatted_stats = client.format_player_stats(details, stats)
                    
                    print(f"   Результат форматирования:")
                    print(f"      - nickname: {formatted_stats.get('nickname')}")
                    print(f"      - level: {formatted_stats.get('level')}")
                    print(f"      - elo: {formatted_stats.get('elo')}")
                    print(f"      - winrate: {formatted_stats.get('winrate')}")
                    print(f"      - kd_ratio: {formatted_stats.get('kd_ratio')}")
                    
                    # Симулируем извлечение для сравнения
                    print(f"\n5. Симуляция добавления в сравнение (НОВЫЙ способ):")
                    comparison_player = {
                        'nickname': formatted_stats.get('nickname', test_nickname),
                        'skill_level': formatted_stats.get('level', 0),
                        'faceit_elo': formatted_stats.get('elo', 0),
                        'profile_data': {
                            'stats': formatted_stats
                        }
                    }
                    
                    print(f"   Результат:")
                    print(f"      - nickname: {comparison_player['nickname']}")
                    print(f"      - skill_level: {comparison_player['skill_level']}")
                    print(f"      - faceit_elo: {comparison_player['faceit_elo']}")
                    
                    if comparison_player['skill_level'] > 0 and comparison_player['faceit_elo'] > 0:
                        print("   УСПЕХ: Данные извлечены корректно!")
                    else:
                        print("   ПРОБЛЕМА: Данные все еще нулевые!")
                
                else:
                    print("   Статистика не получена")
            else:
                print("   Детали не получены")
        else:
            print(f"   Игрок {test_nickname} не найден")
            
    except Exception as e:
        print(f"   ОШИБКА: {e}")
    
    await client.close()


async def main():
    """Основная функция"""
    print("Запуск простого теста извлечения данных\n")
    await test_profile_structure()
    print("\n=== Тест завершен ===")


if __name__ == "__main__":
    asyncio.run(main())