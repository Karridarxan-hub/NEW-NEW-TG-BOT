import asyncio
from faceit_client import FaceitAPIClient
from datetime import datetime

async def test_sessions():
    """Тестируем новую логику сессий"""
    print("=== ТЕСТ ЛОГИКИ СЕССИЙ ===\n")
    
    client = FaceitAPIClient()
    player_id = '0cf595d2-b9a1-4316-9df9-a627c7a8c664'
    
    try:
        # Получаем последние 20 матчей для тестирования
        history_data = await client.get_player_history(player_id, limit=20)
        
        if not history_data or 'items' not in history_data:
            print("Нет данных о матчах")
            return
        
        matches = history_data['items']
        print(f"Получено матчей: {len(matches)}")
        
        # Группируем матчи в сессии (логика из main_handler.py)
        sessions = []
        current_session = []
        
        for match in matches:
            finished_at = match.get('finished_at', 0)
            if not finished_at:
                continue
                
            # Нормализуем время
            if finished_at > 10**12:
                match_time = datetime.fromtimestamp(finished_at / 1000)
            else:
                match_time = datetime.fromtimestamp(finished_at)
            
            match['parsed_time'] = match_time
            
            # Если текущая сессия пуста, начинаем новую
            if not current_session:
                current_session = [match]
            else:
                # Проверяем разрыв между матчами
                last_match_time = current_session[-1]['parsed_time']
                time_diff = (last_match_time - match_time).total_seconds() / 3600  # в часах
                
                if time_diff <= 10:  # Матчи в рамках 10 часов - одна сессия
                    current_session.append(match)
                else:  # Больше 10 часов - новая сессия
                    sessions.append(current_session)
                    current_session = [match]
        
        # Добавляем последнюю сессию
        if current_session:
            sessions.append(current_session)
        
        print(f"Найдено сессий: {len(sessions)}\n")
        
        # Показываем информацию о каждой сессии
        for i, session in enumerate(sessions, 1):
            print(f"=== СЕССИЯ {i} ===")
            print(f"Матчей в сессии: {len(session)}")
            
            # Время сессии
            session_start = session[-1]['parsed_time']
            session_end = session[0]['parsed_time']
            duration_hours = (session_end - session_start).total_seconds() / 3600
            
            print(f"Начало: {session_start.strftime('%d.%m.%Y %H:%M')}")
            print(f"Конец: {session_end.strftime('%d.%m.%Y %H:%M')}")
            print(f"Длительность: {duration_hours:.1f} часов")
            
            # Показываем матчи сессии
            print("Матчи:")
            for j, match in enumerate(session, 1):
                map_name = match.get('map', 'Unknown')
                match_time = match['parsed_time'].strftime('%H:%M')
                print(f"  {j}. {map_name} - {match_time}")
                
                # Проверяем разрыв между матчами
                if j > 1:
                    prev_match = session[j-2]
                    time_diff = (prev_match['parsed_time'] - match['parsed_time']).total_seconds() / 3600
                    print(f"     (разрыв: {time_diff:.1f}ч)")
            
            print()
            
        # Тестируем новую функцию анализа (без вызова API)
        if sessions:
            latest_session = sessions[0]
            print("=== ТЕСТ АНАЛИЗА ПОСЛЕДНЕЙ СЕССИИ ===")
            
            # Упрощенный анализ без API вызовов
            total_matches = len(latest_session)
            wins = 0
            match_results = []
            
            for match in latest_session:
                # Пытаемся определить результат из результатов матча
                if 'results' in match and 'score' in match['results']:
                    score = match['results']['score']
                    # Упрощенная логика определения победы
                    if score.get('faction1', 0) > score.get('faction2', 0):
                        wins += 1
                        match_results.append("🏆")
                    else:
                        match_results.append("💔")
                else:
                    match_results.append("❓")
            
            winrate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            print(f"Матчей: {total_matches}")
            print(f"Побед: {wins}")
            print(f"Winrate: {winrate:.1f}%")
            print(f"Результаты: {' '.join(match_results)}")
        
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sessions())