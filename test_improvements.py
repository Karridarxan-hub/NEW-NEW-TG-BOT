"""
Тестирование улучшений бота
"""

import asyncio
import logging
from faceit_client import FaceitAPIClient
from bot.services.cache_service import CacheService
from bot.handlers.enhanced_comparison import format_enhanced_comparison, get_indicator
from storage import init_storage, cleanup_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_cache_service():
    """Тестирование сервиса кеширования"""
    print("\n=== Тестирование Redis кеширования ===")
    
    # Инициализируем storage
    await init_storage()
    
    # Тестовые данные
    test_nickname = "s1mple"
    test_profile = {
        "nickname": test_nickname,
        "level": 10,
        "elo": 3000,
        "stats": {
            "kd_ratio": 1.5,
            "winrate": 65
        }
    }
    
    # Тест сохранения в кеш
    print(f"1. Сохранение профиля {test_nickname} в кеш...")
    await CacheService.set_player_profile(test_nickname, test_profile)
    print("   ✅ Профиль сохранен")
    
    # Тест получения из кеша
    print(f"2. Получение профиля {test_nickname} из кеша...")
    cached = await CacheService.get_player_profile(test_nickname)
    if cached and cached.get("nickname") == test_nickname:
        print(f"   ✅ Профиль получен из кеша: ELO={cached.get('elo')}")
    else:
        print("   ❌ Профиль не найден в кеше")
    
    # Тест статистики кеша
    print("3. Получение статистики кеша...")
    stats = await CacheService.get_cache_stats()
    print(f"   ✅ Статистика: {stats}")
    
    return True


async def test_visual_indicators():
    """Тестирование визуальных индикаторов"""
    print("\n=== Тестирование визуальных индикаторов ===")
    
    # Тест индикаторов для разных значений
    test_cases = [
        (100, 50, True, "Больше лучше: 100 vs 50"),
        (50, 100, True, "Больше лучше: 50 vs 100"),
        (100, 100, True, "Равные значения: 100 vs 100"),
        (2.0, 3.0, False, "Меньше лучше: 2.0 vs 3.0"),
    ]
    
    for val1, val2, higher_is_better, description in test_cases:
        ind1, ind2 = get_indicator(val1, val2, higher_is_better)
        print(f"{description}: {ind1} {val1} | {val2} {ind2}")
    
    return True


async def test_enhanced_comparison():
    """Тестирование улучшенного сравнения"""
    print("\n=== Тестирование улучшенного сравнения ===")
    
    # Создаем тестовые профили
    player1 = {
        "nickname": "Player1",
        "stats": {
            "level": 10,
            "elo": 2500,
            "matches": 1000,
            "wins": 600,
            "winrate": 60.0,
            "kd_ratio": 1.3,
            "avg_headshot_percentage": 52.0,
            "adr": 85.5,
            "kast": 72.0,
            "hltv_rating": 1.15,
            "map_statistics": {
                "de_mirage": {
                    "matches": 250,
                    "winrate": 65.0,
                    "kd_ratio": 1.4,
                    "hltv_rating": 1.2
                },
                "de_dust2": {
                    "matches": 200,
                    "winrate": 58.0,
                    "kd_ratio": 1.25,
                    "hltv_rating": 1.1
                },
                "de_inferno": {
                    "matches": 180,
                    "winrate": 62.0,
                    "kd_ratio": 1.35,
                    "hltv_rating": 1.18
                }
            }
        },
        "performance": {
            "recent_form": ["W", "W", "L", "W", "W", "W", "L", "W", "W", "L"],
            "wins": 7,
            "losses": 3
        }
    }
    
    player2 = {
        "nickname": "Player2",
        "stats": {
            "level": 9,
            "elo": 2200,
            "matches": 800,
            "wins": 400,
            "winrate": 50.0,
            "kd_ratio": 1.1,
            "avg_headshot_percentage": 48.0,
            "adr": 78.2,
            "kast": 68.5,
            "hltv_rating": 1.05,
            "map_statistics": {
                "de_ancient": {
                    "matches": 150,
                    "winrate": 52.0,
                    "kd_ratio": 1.15,
                    "hltv_rating": 1.08
                },
                "de_nuke": {
                    "matches": 120,
                    "winrate": 48.0,
                    "kd_ratio": 1.05,
                    "hltv_rating": 1.02
                },
                "de_vertigo": {
                    "matches": 100,
                    "winrate": 45.0,
                    "kd_ratio": 1.0,
                    "hltv_rating": 0.98
                }
            }
        },
        "performance": {
            "recent_form": ["L", "W", "L", "L", "W", "W", "L", "L", "W", "L"],
            "wins": 4,
            "losses": 6
        }
    }
    
    # Генерируем сравнение
    print("Генерация сравнения двух игроков...")
    comparison_text = format_enhanced_comparison(player1, player2)
    
    # Проверяем основные элементы
    checks = [
        ("📈" in comparison_text, "Визуальные индикаторы роста"),
        ("📉" in comparison_text, "Визуальные индикаторы падения"),
        ("🗺️" in comparison_text, "Секция карт"),
        ("HLTV" in comparison_text, "HLTV рейтинг"),
        ("Mirage" in comparison_text or "mirage" in comparison_text, "Статистика по картам"),
        ("W" in comparison_text and "L" in comparison_text, "Последняя форма"),
        ("🏆" in comparison_text, "Итоговое сравнение")
    ]
    
    for check, description in checks:
        if check:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
    
    # Выводим часть результата
    print("\nПервые 500 символов сравнения:")
    print(comparison_text[:500].replace("<b>", "").replace("</b>", ""))
    
    return True


async def test_faceit_client_cache():
    """Тестирование кеширования в FACEIT клиенте"""
    print("\n=== Тестирование FACEIT клиента с кешем ===")
    
    client = FaceitAPIClient()
    test_nickname = "s1mple"
    
    # Первый запрос (без кеша)
    print(f"1. Первый запрос профиля {test_nickname} (без кеша)...")
    import time
    start = time.time()
    profile1 = await client.get_player_full_profile(test_nickname)
    time1 = time.time() - start
    
    if profile1:
        print(f"   ✅ Профиль получен за {time1:.2f} сек")
    else:
        print(f"   ❌ Профиль не получен")
        return False
    
    # Второй запрос (из кеша)
    print(f"2. Второй запрос профиля {test_nickname} (из кеша)...")
    start = time.time()
    profile2 = await client.get_player_full_profile(test_nickname)
    time2 = time.time() - start
    
    if profile2:
        print(f"   ✅ Профиль получен за {time2:.2f} сек")
        if time2 < time1:
            print(f"   ✅ Кеш работает! Ускорение в {time1/time2:.1f} раз")
        else:
            print(f"   ⚠️ Кеш не дал ускорения")
    else:
        print(f"   ❌ Профиль не получен")
    
    await client.close()
    return True


async def main():
    """Основная функция тестирования"""
    print("Запуск тестов улучшений бота\n")
    
    results = []
    
    # Тест 1: Кеширование
    try:
        result = await test_cache_service()
        results.append(("Redis кеширование", result))
    except Exception as e:
        logger.error(f"Ошибка теста кеширования: {e}")
        results.append(("Redis кеширование", False))
    
    # Тест 2: Визуальные индикаторы
    try:
        result = await test_visual_indicators()
        results.append(("Визуальные индикаторы", result))
    except Exception as e:
        logger.error(f"Ошибка теста индикаторов: {e}")
        results.append(("Визуальные индикаторы", False))
    
    # Тест 3: Улучшенное сравнение
    try:
        result = await test_enhanced_comparison()
        results.append(("Улучшенное сравнение", result))
    except Exception as e:
        logger.error(f"Ошибка теста сравнения: {e}")
        results.append(("Улучшенное сравнение", False))
    
    # Тест 4: FACEIT клиент с кешем
    try:
        result = await test_faceit_client_cache()
        results.append(("FACEIT клиент с кешем", result))
    except Exception as e:
        logger.error(f"Ошибка теста FACEIT клиента: {e}")
        results.append(("FACEIT клиент с кешем", False))
    
    # Результаты
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nПройдено: {passed_count}/{total_count}")
    
    # Очистка
    await cleanup_storage()
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)