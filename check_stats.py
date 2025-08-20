import asyncio
from faceit_client import FaceitAPIClient
import json

async def check_stats():
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    stats = await client.get_player_stats(player_id)
    
    print("=== Lifetime stats keys ===")
    lifetime = stats.get('lifetime', {})
    for key in sorted(lifetime.keys()):
        if any(word in key.lower() for word in ['triple', 'quadro', 'penta', 'ace', 'double', 'multi', 'clutch', '1v', '2k', '3k', '4k', '5k', 'mvp', 'rounds']):
            print(f"  {key}: {lifetime[key]}")
    
    print("\n=== Segment stats keys ===")
    segments = stats.get('segments', [])
    if segments:
        map_segment = [s for s in segments if s.get('type') == 'Map'][0]
        map_stats = map_segment.get('stats', {})
        for key in sorted(map_stats.keys()):
            if any(word in key.lower() for word in ['triple', 'quadro', 'penta', 'ace', 'double', 'multi', 'clutch', '1v', '2k', '3k', '4k', '5k', 'mvp', 'rounds']):
                print(f"  {key}: {map_stats[key]}")

asyncio.run(check_stats())