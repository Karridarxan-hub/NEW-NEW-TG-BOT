from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio


class InMemoryStorage:
    """Временное хранилище данных в памяти для бота"""
    
    def __init__(self):
        # Данные пользователей: {user_id: user_data}
        self.users: Dict[int, Dict[str, Any]] = {}
        
        # Сессии игроков: {user_id: session_data}
        self.sessions: Dict[int, Dict[str, Any]] = {}
        
        # Кэш FACEIT данных: {cache_key: (data, timestamp)}
        self.faceit_cache: Dict[str, tuple] = {}
        
        # Настройки пользователей: {user_id: settings}
        self.user_settings: Dict[int, Dict[str, Any]] = {}
        
        # Данные для сравнения игроков: {user_id: [player_data]}
        self.comparison_data: Dict[int, List[Dict[str, Any]]] = {}
        
        # Отслеживание последних матчей для уведомлений: {user_id: last_match_id}
        self.tracked_matches: Dict[int, str] = {}
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        return self.users.get(user_id)
    
    def set_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Сохранить данные пользователя"""
        self.users[user_id] = data
    
    def get_user_faceit_id(self, user_id: int) -> Optional[str]:
        """Получить FACEIT ID пользователя"""
        user_data = self.get_user(user_id)
        return user_data.get('faceit_id') if user_data else None
    
    def set_user_faceit_data(self, user_id: int, faceit_id: str, nickname: str) -> None:
        """Привязать FACEIT профиль к пользователю"""
        if user_id not in self.users:
            self.users[user_id] = {}
        
        self.users[user_id].update({
            'faceit_id': faceit_id,
            'nickname': nickname,
            'linked_at': datetime.now()
        })
    
    def get_session(self, user_id: int) -> Dict[str, Any]:
        """Получить сессию пользователя"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'start_time': datetime.now(),
                'matches': [],
                'stats': {}
            }
        return self.sessions[user_id]
    
    def add_session_match(self, user_id: int, match_data: Dict[str, Any]) -> None:
        """Добавить матч в сессию"""
        session = self.get_session(user_id)
        session['matches'].append(match_data)
        
        # Очистка старых матчей (старше 12 часов)
        cutoff_time = datetime.now() - timedelta(hours=12)
        session['matches'] = [
            match for match in session['matches']
            if match.get('finished_at', datetime.now()) > cutoff_time
        ]
    
    def get_cached_data(self, cache_key: str, max_age_minutes: int = 5) -> Optional[Any]:
        """Получить кэшированные данные"""
        if cache_key in self.faceit_cache:
            data, timestamp = self.faceit_cache[cache_key]
            if datetime.now() - timestamp < timedelta(minutes=max_age_minutes):
                return data
            else:
                del self.faceit_cache[cache_key]
        return None
    
    def set_cached_data(self, cache_key: str, data: Any) -> None:
        """Сохранить данные в кэш"""
        self.faceit_cache[cache_key] = (data, datetime.now())
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получить настройки пользователя"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                'match_notifications': True,
                'subscription_type': 'standard',
                'language': 'ru'
            }
        return self.user_settings[user_id]
    
    def save_user(self, user_id: int, faceit_id: str, nickname: str) -> None:
        """Сохранить пользователя"""
        self.users[user_id] = {
            'faceit_id': faceit_id,
            'nickname': nickname,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_current_time(self) -> str:
        """Получить текущее время"""
        return datetime.now().isoformat()
    
    def get_comparison_list(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить список игроков для сравнения"""
        return self.comparison_data.get(user_id, [])
    
    def add_to_comparison(self, user_id: int, player_data: Dict[str, Any]) -> None:
        """Добавить игрока в список сравнения"""
        if user_id not in self.comparison_data:
            self.comparison_data[user_id] = []
        
        # Проверяем, нет ли уже такого игрока
        existing = any(p['faceit_id'] == player_data['faceit_id'] for p in self.comparison_data[user_id])
        if not existing and len(self.comparison_data[user_id]) < 5:  # Максимум 5 игроков
            self.comparison_data[user_id].append(player_data)
    
    def clear_comparison_list(self, user_id: int) -> None:
        """Очистить список сравнения"""
        if user_id in self.comparison_data:
            self.comparison_data[user_id] = []

    def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> None:
        """Обновить настройки пользователя"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id].update(settings)
    
    def get_comparison_players(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить список игроков для сравнения"""
        return self.comparison_data.get(user_id, [])
    
    def add_comparison_player(self, user_id: int, player_data: Dict[str, Any]) -> None:
        """Добавить игрока для сравнения"""
        if user_id not in self.comparison_data:
            self.comparison_data[user_id] = []
        self.comparison_data[user_id].append(player_data)
    
    def clear_comparison_data(self, user_id: int) -> None:
        """Очистить данные сравнения"""
        self.comparison_data[user_id] = []
    
    def set_tracked_match(self, user_id: int, match_id: str) -> None:
        """Установить отслеживаемый матч для уведомлений"""
        self.tracked_matches[user_id] = match_id
    
    def get_tracked_match(self, user_id: int) -> Optional[str]:
        """Получить отслеживаемый матч"""
        return self.tracked_matches.get(user_id)
    
    def cleanup_old_cache(self) -> None:
        """Очистка устаревшего кэша"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        keys_to_delete = [
            key for key, (_, timestamp) in self.faceit_cache.items()
            if timestamp < cutoff_time
        ]
        for key in keys_to_delete:
            del self.faceit_cache[key]


# Глобальный экземпляр хранилища
storage = InMemoryStorage()


async def cleanup_storage_task():
    """Периодическая очистка хранилища"""
    while True:
        await asyncio.sleep(3600)  # Каждый час
        storage.cleanup_old_cache()