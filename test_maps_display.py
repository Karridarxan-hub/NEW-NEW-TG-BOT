import asyncio
from faceit_client import FaceitAPIClient

async def test_maps_display():
    """Тестируем новую логику отображения карт"""
    print("=== ТЕСТ ОТОБРАЖЕНИЯ КАРТ ===\n")
    
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    
    try:
        # Получаем данные игрока и статистику
        player_details = await client.get_player_details(player_id)
        stats_data = await client.get_player_stats(player_id)
        
        if not stats_data or not player_details:
            print("Не удалось загрузить данные")
            return
        
        # Форматируем статистику  
        formatted_stats = client.format_player_stats(player_details, stats_data)
        maps_stats = formatted_stats.get('maps', {})
        
        print(f"Получено карт из API: {len(maps_stats)}")
        
        # Воспроизводим логику из main_handler.py
        map_emojis = {
            'mirage': '🌋',
            'inferno': '🏭', 
            'dust2': '🌪️',
            'nuke': '🌌',
            'vertigo': '🏔️',
            'ancient': '🌿',
            'anubis': '🏺',
            'train': '🚂',
            'overpass': '🌉'
        }
        
        message_text = "Статистика по картам\n\n"
        
        if maps_stats:
            # Сортируем карты по количеству матчей (убывание)
            sorted_maps = sorted(
                maps_stats.items(), 
                key=lambda x: x[1].get('matches', 0), 
                reverse=True
            )
            
            for i, (map_name, map_data) in enumerate(sorted_maps, 1):
                # Определяем эмоджи для карты
                map_key = map_name.lower().replace(' ', '').replace('de_', '')
                map_emoji = map_emojis.get(map_key, '🗺️')
                
                message_text += f"{i}. {map_name}\n"
                
                matches = map_data.get('matches', 0)
                if matches > 0:
                    # Есть данные - показываем статистику
                    wins = map_data.get('wins', 0)
                    winrate = map_data.get('winrate', 0)
                    kd_ratio = map_data.get('kd_ratio', 0)
                    adr = map_data.get('adr', 0)
                    
                    message_text += f"   Матчей: {matches} (Побед: {wins})\n"
                    message_text += f"   Winrate: {winrate:.1f}%\n"
                    message_text += f"   K/D: {kd_ratio:.3f}\n"
                    message_text += f"   ADR: {adr:.1f}\n\n"
                else:
                    # Нет данных - показываем сообщение
                    message_text += f"   Нет данных по карте\n\n"
        else:
            message_text += "Данные по картам недоступны\n"
        
        print("=== РЕЗУЛЬТАТ ОТОБРАЖЕНИЯ ===")
        print(message_text)
        
        print(f"\n=== ДЕТАЛИ ===")
        print(f"Всего карт: {len(sorted_maps)}")
        print("Порядок карт (по матчам):")
        for i, (map_name, map_data) in enumerate(sorted_maps, 1):
            matches = map_data.get('matches', 0)
            print(f"  {i}. {map_name}: {matches} матчей")
        
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_maps_display())