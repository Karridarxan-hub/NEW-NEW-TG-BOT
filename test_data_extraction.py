"""
Тестирование извлечения данных из профиля FACEIT
"""

import asyncio
import logging
from faceit_client import FaceitAPIClient
from storage import init_storage, cleanup_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_profile_data_extraction():
    """Тестирование извлечения данных из профиля"""
    print("\n=== Тестирование извлечения данных профиля ===\n")
    
    # Инициализируем storage
    await init_storage()
    
    client = FaceitAPIClient()
    
    # Тестовые никнеймы
    test_nicknames = ["s1mple", "Geun-Hee", "Raoni4"]
    
    for nickname in test_nicknames:
        print(f"\n--- Тестирование игрока: {nickname} ---")
        
        try:
            # Получаем полный профиль
            profile = await client.get_player_full_profile(nickname)
            
            if profile:
                # Проверяем структуру данных
                print(f"1. Структура профиля:")
                print(f"   - Корневые ключи: {list(profile.keys())}")
                
                # Проверяем наличие stats
                if 'stats' in profile:
                    stats = profile['stats']
                    print(f"\n2. Данные в profile['stats']:")
                    print(f"   - nickname: {stats.get('nickname', 'NOT FOUND')}")
                    print(f"   - level: {stats.get('level', 'NOT FOUND')}")
                    print(f"   - elo: {stats.get('elo', 'NOT FOUND')}")
                    print(f"   - winrate: {stats.get('winrate', 'NOT FOUND')}")
                    print(f"   - kd_ratio: {stats.get('kd_ratio', 'NOT FOUND')}")
                    print(f"   - matches: {stats.get('matches', 'NOT FOUND')}")
                else:
                    print("   ОШИБКА: Нет поля 'stats' в профиле!")
                
                # Проверяем старые поля (должны отсутствовать в корне)
                print(f"\n3. Проверка старых полей в корне:")
                print(f"   - skill_level в корне: {profile.get('skill_level', 'NOT FOUND (правильно)')}")
                print(f"   - faceit_elo в корне: {profile.get('faceit_elo', 'NOT FOUND (правильно)')}")
                
                # Симулируем добавление в список сравнения
                print(f"\n4. Симуляция добавления в сравнение:")
                player_stats = profile.get('stats', {})
                comparison_player = {
                    'nickname': player_stats.get('nickname', nickname),
                    'skill_level': player_stats.get('level', 0),
                    'faceit_elo': player_stats.get('elo', 0),
                    'profile_data': profile
                }
                
                print(f"   Результат:")
                print(f"   - nickname: {comparison_player['nickname']}")
                print(f"   - skill_level: {comparison_player['skill_level']}")
                print(f"   - faceit_elo: {comparison_player['faceit_elo']}")
                
                if comparison_player['skill_level'] == 0 and comparison_player['faceit_elo'] == 0:
                    print("   ⚠️ ВНИМАНИЕ: Данные все еще нулевые!")
                else:
                    print("   ✅ Данные извлечены корректно!")
                    
            else:
                print(f"   ❌ Не удалось получить профиль игрока {nickname}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    await client.close()
    await cleanup_storage()
    
    print("\n=== Тестирование завершено ===\n")


async def test_comparison_flow():
    """Тестирование полного процесса сравнения"""
    print("\n=== Тестирование процесса сравнения ===\n")
    
    await init_storage()
    client = FaceitAPIClient()
    
    # Симулируем добавление двух игроков
    players = ["s1mple", "Niko"]
    comparison_players = []
    
    for nickname in players:
        print(f"Добавление игрока {nickname}...")
        profile = await client.get_player_full_profile(nickname)
        
        if profile:
            player_stats = profile.get('stats', {})
            comparison_players.append({
                'nickname': player_stats.get('nickname', nickname),
                'skill_level': player_stats.get('level', 0),
                'faceit_elo': player_stats.get('elo', 0),
                'profile_data': profile
            })
            print(f"  ✅ Добавлен: Level {player_stats.get('level', 0)}, ELO {player_stats.get('elo', 0)}")
        else:
            print(f"  ❌ Не удалось добавить")
    
    # Проверяем данные для сравнения
    print("\n--- Данные для сравнения ---")
    for i, player in enumerate(comparison_players, 1):
        print(f"{i}. {player['nickname']}")
        print(f"   Level: {player['skill_level']}")
        print(f"   ELO: {player['faceit_elo']}")
    
    await client.close()
    await cleanup_storage()
    
    print("\n=== Тестирование завершено ===\n")


async def main():
    """Основная функция"""
    print("Запуск тестов извлечения данных\n")
    
    # Тест 1: Извлечение данных профиля
    await test_profile_data_extraction()
    
    # Тест 2: Процесс сравнения
    await test_comparison_flow()


if __name__ == "__main__":
    asyncio.run(main())