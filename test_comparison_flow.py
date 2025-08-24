"""
Тестирование полного потока сравнения игроков
"""

import asyncio
from bot.handlers.comparison_handler import format_comparison_menu_text
from faceit_client import FaceitAPIClient


async def simulate_comparison_flow():
    """Симулируем полный поток добавления игроков в сравнение"""
    print("=== Симуляция потока сравнения ===\n")
    
    client = FaceitAPIClient()
    
    # Симулируем список для сравнения
    comparison_players = []
    
    # Добавляем первого игрока
    print("1. Добавление первого игрока...")
    nickname1 = "s1mple"
    
    try:
        profile1 = await client.get_player_full_profile(nickname1)
        if profile1:
            player_stats1 = profile1.get('stats', {})
            
            print(f"   Профиль {nickname1} получен:")
            print(f"   - nickname: {player_stats1.get('nickname')}")
            print(f"   - level: {player_stats1.get('level')}")
            print(f"   - elo: {player_stats1.get('elo')}")
            
            comparison_players.append({
                'nickname': player_stats1.get('nickname', nickname1),
                'skill_level': player_stats1.get('level', 0),
                'faceit_elo': player_stats1.get('elo', 0),
                'profile_data': profile1
            })
            
            print(f"   Добавлен в список сравнения:")
            print(f"   - nickname: {comparison_players[0]['nickname']}")
            print(f"   - skill_level: {comparison_players[0]['skill_level']}")
            print(f"   - faceit_elo: {comparison_players[0]['faceit_elo']}")
        else:
            print(f"   Не удалось получить профиль {nickname1}")
    
    except Exception as e:
        print(f"   Ошибка с {nickname1}: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Добавляем второго игрока
    print("2. Добавление второго игрока...")
    nickname2 = "NiKo"
    
    try:
        profile2 = await client.get_player_full_profile(nickname2)
        if profile2:
            player_stats2 = profile2.get('stats', {})
            
            print(f"   Профиль {nickname2} получен:")
            print(f"   - nickname: {player_stats2.get('nickname')}")
            print(f"   - level: {player_stats2.get('level')}")
            print(f"   - elo: {player_stats2.get('elo')}")
            
            comparison_players.append({
                'nickname': player_stats2.get('nickname', nickname2),
                'skill_level': player_stats2.get('level', 0),
                'faceit_elo': player_stats2.get('elo', 0),
                'profile_data': profile2
            })
            
            print(f"   Добавлен в список сравнения:")
            print(f"   - nickname: {comparison_players[1]['nickname']}")
            print(f"   - skill_level: {comparison_players[1]['skill_level']}")
            print(f"   - faceit_elo: {comparison_players[1]['faceit_elo']}")
        else:
            print(f"   Не удалось получить профиль {nickname2}")
    
    except Exception as e:
        print(f"   Ошибка с {nickname2}: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Тестируем отображение меню
    print("3. Тестирование отображения меню сравнения...")
    
    user_data = {'comparison_players': comparison_players}
    menu_text = await format_comparison_menu_text(user_data)
    
    print("   Результат format_comparison_menu_text:")
    print(menu_text.replace('<b>', '').replace('</b>', ''))
    
    print("\n" + "-"*50 + "\n")
    
    # Тестируем сравнение
    if len(comparison_players) == 2:
        print("4. Тестирование улучшенного сравнения...")
        
        from bot.handlers.enhanced_comparison import format_enhanced_comparison
        
        try:
            comparison_text = format_enhanced_comparison(
                comparison_players[0]['profile_data'],
                comparison_players[1]['profile_data']
            )
            
            print("   Первые 800 символов сравнения:")
            clean_text = comparison_text.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            print(clean_text[:800])
            
        except Exception as e:
            print(f"   Ошибка сравнения: {e}")
            import traceback
            traceback.print_exc()
    
    await client.close()
    print("\n=== Тестирование завершено ===")


if __name__ == "__main__":
    asyncio.run(simulate_comparison_flow())