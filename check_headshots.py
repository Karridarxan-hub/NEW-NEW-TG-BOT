import asyncio
from faceit_client import FaceitAPIClient
import json

async def check_headshots():
    """Проверяем статистику хедшотов для игрока Geun-Hee"""
    client = FaceitAPIClient()
    
    # Сначала найдем игрока по нику
    player_data = await client.find_player_by_nickname("Geun-Hee")
    
    if not player_data:
        print("Игрок Geun-Hee не найден")
        return
    
    player_id = player_data['player_id']
    print(f"Найден игрок: {player_data['nickname']} (ID: {player_id})")
    
    # Получаем статистику
    stats = await client.get_player_stats(player_id)
    
    if not stats:
        print("Не удалось получить статистику")
        return
    
    print("\n=== LIFETIME СТАТИСТИКА ===")
    lifetime = stats.get('lifetime', {})
    
    # Ищем все поля связанные с хедшотами
    headshot_fields = {}
    for key, value in lifetime.items():
        if 'headshot' in key.lower() or 'hs' in key.lower():
            headshot_fields[key] = value
            print(f"{key}: {value}")
    
    print("\n=== SEGMENTS СТАТИСТИКА ===")
    segments = stats.get('segments', [])
    
    # Проверяем segments
    for segment in segments:
        if segment.get('type') == 'Map':
            segment_stats = segment.get('stats', {})
            segment_label = segment.get('label', 'Unknown')
            
            # Ищем хедшоты в этом сегменте
            for key, value in segment_stats.items():
                if 'headshot' in key.lower() or 'hs' in key.lower():
                    print(f"[{segment_label}] {key}: {value}")
    
    print("\n=== SUMMARY ===")
    print(f"Всего полей с хедшотами в lifetime: {len(headshot_fields)}")
    
    # Выводим самые вероятные поля
    likely_fields = [
        'Average Headshots %',
        'Headshots %', 
        'Total Headshots %',
        'Headshot %'
    ]
    
    print("\nВероятные поля для среднего % хедшотов:")
    for field in likely_fields:
        if field in lifetime:
            print(f"  {field}: {lifetime[field]}")
        else:
            print(f"  {field}: НЕ НАЙДЕНО")

if __name__ == "__main__":
    asyncio.run(check_headshots())