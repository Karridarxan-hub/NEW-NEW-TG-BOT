import asyncio
from faceit_client import FaceitAPIClient

async def check_clutches():
    """Проверяем данные клатчей в lifetime vs segments"""
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    
    stats = await client.get_player_stats(player_id)
    
    print("=== LIFETIME CLUTCH DATA ===")
    lifetime = stats.get('lifetime', {})
    
    clutch_fields_lifetime = {}
    for key, value in lifetime.items():
        if '1v1' in key.lower() or '1v2' in key.lower() or 'clutch' in key.lower():
            clutch_fields_lifetime[key] = value
            print(f"{key}: {value}")
    
    print("\n=== SEGMENTS CLUTCH DATA ===")
    segments = stats.get('segments', [])
    
    clutch_fields_segments = {}
    total_1v1_count = 0
    total_1v1_wins = 0
    total_1v2_count = 0  
    total_1v2_wins = 0
    
    for segment in segments:
        if segment.get('type') == 'Map':
            segment_stats = segment.get('stats', {})
            segment_label = segment.get('label', 'Unknown')
            
            for key, value in segment_stats.items():
                if '1v1' in key.lower() or '1v2' in key.lower() or 'clutch' in key.lower():
                    print(f"[{segment_label}] {key}: {value}")
                    
                    # Суммируем для общего расчета
                    if key == 'Total 1v1 Count':
                        total_1v1_count += int(value)
                    elif key == 'Total 1v1 Wins':
                        total_1v1_wins += int(value)
                    elif key == 'Total 1v2 Count':
                        total_1v2_count += int(value)
                    elif key == 'Total 1v2 Wins':
                        total_1v2_wins += int(value)
    
    print(f"\n=== СРАВНЕНИЕ ===")
    print(f"LIFETIME:")
    print(f"  1v1 Count: {lifetime.get('Total 1v1 Count', 0)}")
    print(f"  1v1 Wins: {lifetime.get('Total 1v1 Wins', 0)}")
    print(f"  1v2 Count: {lifetime.get('Total 1v2 Count', 0)}")
    print(f"  1v2 Wins: {lifetime.get('Total 1v2 Wins', 0)}")
    
    print(f"\nSEGMENTS (суммированно):")
    print(f"  1v1 Count: {total_1v1_count}")
    print(f"  1v1 Wins: {total_1v1_wins}")
    print(f"  1v2 Count: {total_1v2_count}")
    print(f"  1v2 Wins: {total_1v2_wins}")
    
    # Рассчитываем проценты
    if total_1v1_count > 0:
        segments_1v1_percent = (total_1v1_wins / total_1v1_count) * 100
        print(f"  1v1 Win Rate (segments): {segments_1v1_percent:.1f}%")
    
    if total_1v2_count > 0:
        segments_1v2_percent = (total_1v2_wins / total_1v2_count) * 100
        print(f"  1v2 Win Rate (segments): {segments_1v2_percent:.1f}%")
    
    lifetime_1v1_percent = float(lifetime.get('1v1 Win Rate', 0)) * 100
    lifetime_1v2_percent = float(lifetime.get('1v2 Win Rate', 0)) * 100
    print(f"  1v1 Win Rate (lifetime): {lifetime_1v1_percent:.1f}%")
    print(f"  1v2 Win Rate (lifetime): {lifetime_1v2_percent:.1f}%")

if __name__ == "__main__":
    asyncio.run(check_clutches())