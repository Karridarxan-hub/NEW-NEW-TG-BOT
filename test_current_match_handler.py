#!/usr/bin/env python3
"""
Тест для обработчика анализа текущего матча
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.current_match_handler import extract_match_id, calculate_team_strength, analyze_map_performance


def test_extract_match_id():
    """Тест извлечения match_id из разных форматов ссылок"""
    print("Тестирование извлечения match_id из ссылок...")
    
    test_urls = [
        "https://www.faceit.com/en/cs2/room/1-abc123-def456-ghi789",
        "https://faceit.com/ru/cs2/room/1-abc123-def456-ghi789",
        "https://www.faceit.com/en/csgo/room/1-abc123-def456-ghi789",
        "https://faceit.com/de/cs2/room/1-123abc-456def-789ghi",
        "invalid-url",
        "https://faceit.com/room/abc123-def456-ghi789-123456",
    ]
    
    for url in test_urls:
        match_id = extract_match_id(url)
        print(f"URL: {url}")
        print(f"Match ID: {match_id}")
        print("---")


def test_calculate_team_strength():
    """Тест расчета силы команды"""
    print("\nТестирование расчета силы команды...")
    
    # Тестовые данные игроков
    test_players = [
        {
            'nickname': 'Player1',
            'hltv_rating': 1.15,
            'elo': 2100,
            'level': 8,
            'winrate': 65.5,
            'matches': 150
        },
        {
            'nickname': 'Player2', 
            'hltv_rating': 0.85,
            'elo': 1800,
            'level': 6,
            'winrate': 45.2,
            'matches': 80
        },
        {
            'nickname': 'Player3',
            'hltv_rating': 1.05,
            'elo': 1950,
            'level': 7,
            'winrate': 58.3,
            'matches': 200
        },
        {
            'nickname': 'Player4',
            'hltv_rating': 0.78,
            'elo': 1650,
            'level': 5,
            'winrate': 42.1,
            'matches': 120
        },
        {
            'nickname': 'Player5',
            'hltv_rating': 1.22,
            'elo': 2300,
            'level': 9,
            'winrate': 72.8,
            'matches': 300
        }
    ]
    
    strength = calculate_team_strength(test_players)
    
    print(f"Средний HLTV: {strength['avg_hltv']}")
    print(f"Средний ELO: {strength['avg_elo']}")
    print(f"Средний уровень: {strength['avg_level']}")
    print(f"Средний винрейт: {strength['avg_winrate']}%")
    print(f"Всего матчей: {strength['total_matches']}")
    print(f"Количество игроков: {strength['player_count']}")
    
    print(f"\nСильные игроки ({len(strength['strong_players'])}):")
    for player in strength['strong_players']:
        print(f"  • {player['nickname']}: HLTV {player['hltv']}")
    
    print(f"\nСлабые игроки ({len(strength['weak_players'])}):")
    for player in strength['weak_players']:
        print(f"  • {player['nickname']}: HLTV {player['hltv']}")


def test_analyze_map_performance():
    """Тест анализа производительности на карте"""
    print("\nТестирование анализа производительности на карте...")
    
    # Тестовые данные игроков с картами
    test_players = [
        {
            'nickname': 'Player1',
            'maps': {
                'Mirage': {
                    'matches': 25,
                    'winrate': 68.0,
                    'hltv_rating': 1.12
                },
                'Inferno': {
                    'matches': 15,
                    'winrate': 53.3,
                    'hltv_rating': 0.95
                }
            }
        },
        {
            'nickname': 'Player2',
            'maps': {
                'Mirage': {
                    'matches': 18,
                    'winrate': 44.4,
                    'hltv_rating': 0.88
                }
            }
        },
        {
            'nickname': 'Player3',
            'maps': {
                'Mirage': {
                    'matches': 32,
                    'winrate': 62.5,
                    'hltv_rating': 1.08
                }
            }
        },
        {
            'nickname': 'Player4',
            'maps': {}  # Нет данных по картам
        }
    ]
    
    # Анализ карты Mirage
    map_perf = analyze_map_performance(test_players, 'Mirage')
    
    print(f"Карта: Mirage")
    print(f"Средний винрейт: {map_perf['avg_winrate']}%")
    print(f"Всего матчей: {map_perf['total_matches']}")
    print(f"Игроков с данными: {map_perf['players_with_data']}/4")
    print(f"Уровень достоверности: {map_perf['confidence_level']}")
    
    if map_perf['best_player']:
        best = map_perf['best_player']
        print(f"\nЛучший игрок: {best['nickname']}")
        print(f"  Винрейт: {best['winrate']}% ({best['matches']} матчей)")
        print(f"  HLTV: {best['hltv']}")
    
    if map_perf['worst_player']:
        worst = map_perf['worst_player']
        print(f"\nХудший игрок: {worst['nickname']}")
        print(f"  Винрейт: {worst['winrate']}% ({worst['matches']} матчей)")
        print(f"  HLTV: {worst['hltv']}")
    
    # Тест для несуществующей карты
    print(f"\n--- Тест для Dust2 (нет данных) ---")
    dust2_perf = analyze_map_performance(test_players, 'Dust2')
    print(f"Уровень достоверности: {dust2_perf['confidence_level']}")
    print(f"Игроков с данными: {dust2_perf['players_with_data']}")


def main():
    """Запуск всех тестов"""
    print("ТЕСТИРОВАНИЕ ОБРАБОТЧИКА АНАЛИЗА ТЕКУЩЕГО МАТЧА\n")
    print("=" * 60)
    
    try:
        # Тест извлечения match_id
        test_extract_match_id()
        
        # Тест расчета силы команды
        test_calculate_team_strength()
        
        # Тест анализа карты
        test_analyze_map_performance()
        
        print("\n" + "=" * 60)
        print("Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"\nОшибка в тестах: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()