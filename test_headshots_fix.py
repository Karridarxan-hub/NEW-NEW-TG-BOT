import asyncio
from faceit_client import FaceitAPIClient

async def test_headshots_fix():
    """Тестируем исправление расчета хедшотов"""
    print("=== ТЕСТ ИСПРАВЛЕНИЯ ХЕДШОТОВ ===\n")
    
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    
    try:
        # Получаем данные игрока и статистику
        player_details = await client.get_player_details(player_id)
        stats_data = await client.get_player_stats(player_id)
        
        if not stats_data or not player_details:
            print("Не удалось загрузить данные")
            return
        
        # Форматируем статистику с новой логикой
        formatted_stats = client.format_player_stats(player_details, stats_data)
        
        print("=== РЕЗУЛЬТАТ НОВОГО РАСЧЕТА ===")
        print(f"Средний % хедшотов: {formatted_stats.get('avg_headshot_percentage', 0)}%")
        
        # Показываем детальный расчет
        print("\n=== ДЕТАЛЬНЫЙ РАСЧЕТ ===")
        segments = stats_data.get('segments', [])
        map_stats = [s for s in segments if s.get('type') == 'Map']
        
        total_headshot_percentage = 0.0
        maps_with_data = 0
        
        print("Данные по картам:")
        for map_stat in map_stats:
            map_name = map_stat.get('label', 'Unknown')
            map_data = map_stat.get('stats', {})
            
            if map_data and 'Average Headshots %' in map_data:
                headshot_pct = float(map_data.get('Average Headshots %', 0))
                if headshot_pct > 0:
                    print(f"  {map_name}: {headshot_pct}%")
                    total_headshot_percentage += headshot_pct
                    maps_with_data += 1
        
        if maps_with_data > 0:
            calculated_avg = round(total_headshot_percentage / maps_with_data, 1)
            print(f"\nРасчет: {total_headshot_percentage:.1f} / {maps_with_data} = {calculated_avg}%")
        
        # Сравнение с lifetime
        lifetime = stats_data.get('lifetime', {})
        lifetime_headshots = lifetime.get('Average Headshots %', 0)
        
        print(f"\n=== СРАВНЕНИЕ ===")
        print(f"Lifetime данные:  {lifetime_headshots}%")
        print(f"Segments данные:  {formatted_stats.get('avg_headshot_percentage', 0)}%")
        print(f"Разница: {abs(float(formatted_stats.get('avg_headshot_percentage', 0)) - float(lifetime_headshots)):.1f}%")
        
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_headshots_fix())