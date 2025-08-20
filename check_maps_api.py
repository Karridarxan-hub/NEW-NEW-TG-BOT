import asyncio
from faceit_client import FaceitAPIClient
import json

async def check_maps_from_api():
    """Проверяем, какие карты возвращает FACEIT API"""
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    
    print("=== АНАЛИЗ КАРТ ИЗ FACEIT API ===\n")
    
    try:
        # Получаем статистику игрока
        stats = await client.get_player_stats(player_id)
        
        if not stats:
            print("❌ Не удалось получить данные из API")
            return
        
        # Получаем segments
        segments = stats.get('segments', [])
        print(f"Всего segments получено: {len(segments)}")
        
        # Фильтруем только карты
        map_segments = [s for s in segments if s.get('type') == 'Map']
        print(f"Segments типа 'Map': {len(map_segments)}")
        
        if not map_segments:
            print("Нет данных по картам")
            return
        
        print("\n=== СПИСОК КАРТ ИЗ API ===")
        maps_data = {}
        
        for i, map_segment in enumerate(map_segments, 1):
            map_name = map_segment.get('label', 'Unknown')
            map_stats = map_segment.get('stats', {})
            
            print(f"\n{i}. {map_name}")
            
            # Основные показатели
            matches = map_stats.get('Matches', 0)
            wins = map_stats.get('Wins', 0)
            winrate = map_stats.get('Win Rate %', 0)
            
            print(f"   Матчей: {matches}")
            print(f"   Побед: {wins}")
            print(f"   Winrate: {winrate}%")
            
            # Сохраняем данные для дальнейшего анализа
            maps_data[map_name] = {
                'matches': matches,
                'wins': wins,
                'winrate': winrate,
                'available_stats': list(map_stats.keys())
            }
        
        print(f"\n=== ИТОГО ===")
        print(f"🎯 Всего карт в API: {len(maps_data)}")
        print(f"📋 Список карт:")
        
        # Сортируем карты по количеству матчей
        sorted_maps = sorted(maps_data.items(), key=lambda x: x[1]['matches'], reverse=True)
        
        for map_name, data in sorted_maps:
            print(f"   • {map_name} ({data['matches']} матчей)")
        
        # Проверяем, есть ли карты без данных
        maps_with_data = [name for name, data in maps_data.items() if data['matches'] > 0]
        maps_without_data = [name for name, data in maps_data.items() if data['matches'] == 0]
        
        print(f"\n📊 Карты с данными: {len(maps_with_data)}")
        print(f"❌ Карты без данных: {len(maps_without_data)}")
        
        if maps_without_data:
            print("Карты без данных:")
            for map_name in maps_without_data:
                print(f"   • {map_name}")
        
        # Проверяем известные карты CS2
        known_cs2_maps = [
            'Mirage', 'Inferno', 'Dust2', 'Nuke', 'Vertigo', 
            'Ancient', 'Anubis', 'Train', 'Overpass', 'Cache'
        ]
        
        api_map_names = list(maps_data.keys())
        
        print(f"\n🔍 СРАВНЕНИЕ С ИЗВЕСТНЫМИ КАРТАМИ CS2:")
        for known_map in known_cs2_maps:
            found = any(known_map.lower() in api_map.lower() for api_map in api_map_names)
            status = "✅ Найдена" if found else "❌ Не найдена"
            print(f"   {known_map}: {status}")
        
        # Выводим дополнительные карты из API
        additional_maps = []
        for api_map in api_map_names:
            if not any(known_map.lower() in api_map.lower() for known_map in known_cs2_maps):
                additional_maps.append(api_map)
        
        if additional_maps:
            print(f"\n➕ ДОПОЛНИТЕЛЬНЫЕ КАРТЫ В API:")
            for map_name in additional_maps:
                print(f"   • {map_name}")
        
        # Выводим детальную информацию о доступных статистиках
        print(f"\n📋 ДОСТУПНЫЕ СТАТИСТИКИ (пример с первой карты):")
        if map_segments:
            first_map = map_segments[0]
            first_map_stats = first_map.get('stats', {})
            print(f"Карта: {first_map.get('label', 'Unknown')}")
            for stat_key in sorted(first_map_stats.keys()):
                print(f"   • {stat_key}: {first_map_stats[stat_key]}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_maps_from_api())