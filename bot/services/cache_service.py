"""
Сервис кеширования для FACEIT данных
Оптимизирует запросы к API через Redis кеш
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from storage import storage

logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для кеширования данных FACEIT"""
    
    # TTL для разных типов данных (в секундах)
    TTL_SETTINGS = {
        'player_profile': 300,      # 5 минут для профилей игроков
        'player_stats': 300,        # 5 минут для статистики
        'match_details': 1800,      # 30 минут для деталей матчей
        'match_stats': 1800,        # 30 минут для статистики матчей
        'player_matches': 180,      # 3 минуты для списка матчей
        'map_stats': 600,          # 10 минут для статистики по картам
    }
    
    @classmethod
    async def get_player_profile(cls, nickname: str) -> Optional[Dict[str, Any]]:
        """Получить профиль игрока из кеша"""
        cache_key = f"player_profile:{nickname.lower()}"
        
        try:
            # Пробуем получить из Redis
            cached_data = await storage.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for player profile: {nickname}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached player profile {nickname}: {e}")
            return None
    
    @classmethod
    async def set_player_profile(cls, nickname: str, profile_data: Dict[str, Any]) -> None:
        """Сохранить профиль игрока в кеш"""
        cache_key = f"player_profile:{nickname.lower()}"
        
        try:
            await storage.redis.setex(
                cache_key,
                cls.TTL_SETTINGS['player_profile'],
                json.dumps(profile_data, ensure_ascii=False)
            )
            logger.debug(f"Cached player profile: {nickname}")
            
        except Exception as e:
            logger.error(f"Error caching player profile {nickname}: {e}")
    
    @classmethod
    async def get_player_stats(cls, player_id: str) -> Optional[Dict[str, Any]]:
        """Получить статистику игрока из кеша"""
        cache_key = f"player_stats:{player_id}"
        
        try:
            cached_data = await storage.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for player stats: {player_id}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached player stats {player_id}: {e}")
            return None
    
    @classmethod
    async def set_player_stats(cls, player_id: str, stats_data: Dict[str, Any]) -> None:
        """Сохранить статистику игрока в кеш"""
        cache_key = f"player_stats:{player_id}"
        
        try:
            await storage.redis.setex(
                cache_key,
                cls.TTL_SETTINGS['player_stats'],
                json.dumps(stats_data, ensure_ascii=False)
            )
            logger.debug(f"Cached player stats: {player_id}")
            
        except Exception as e:
            logger.error(f"Error caching player stats {player_id}: {e}")
    
    @classmethod
    async def get_match_details(cls, match_id: str) -> Optional[Dict[str, Any]]:
        """Получить детали матча из кеша"""
        cache_key = f"match_details:{match_id}"
        
        try:
            cached_data = await storage.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for match details: {match_id}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached match details {match_id}: {e}")
            return None
    
    @classmethod
    async def set_match_details(cls, match_id: str, match_data: Dict[str, Any]) -> None:
        """Сохранить детали матча в кеш"""
        cache_key = f"match_details:{match_id}"
        
        try:
            await storage.redis.setex(
                cache_key,
                cls.TTL_SETTINGS['match_details'],
                json.dumps(match_data, ensure_ascii=False)
            )
            logger.debug(f"Cached match details: {match_id}")
            
        except Exception as e:
            logger.error(f"Error caching match details {match_id}: {e}")
    
    @classmethod
    async def get_player_matches(cls, player_id: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Получить список матчей игрока из кеша"""
        cache_key = f"player_matches:{player_id}:{limit}"
        
        try:
            cached_data = await storage.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for player matches: {player_id}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached player matches {player_id}: {e}")
            return None
    
    @classmethod
    async def set_player_matches(cls, player_id: str, matches_data: Dict[str, Any], limit: int = 20) -> None:
        """Сохранить список матчей игрока в кеш"""
        cache_key = f"player_matches:{player_id}:{limit}"
        
        try:
            await storage.redis.setex(
                cache_key,
                cls.TTL_SETTINGS['player_matches'],
                json.dumps(matches_data, ensure_ascii=False)
            )
            logger.debug(f"Cached player matches: {player_id}")
            
        except Exception as e:
            logger.error(f"Error caching player matches {player_id}: {e}")
    
    @classmethod
    async def invalidate_player_cache(cls, nickname: str, player_id: str = None) -> None:
        """Инвалидировать весь кеш игрока"""
        try:
            # Удаляем профиль
            await storage.redis.delete(f"player_profile:{nickname.lower()}")
            
            # Если есть player_id, удаляем и статистику
            if player_id:
                await storage.redis.delete(f"player_stats:{player_id}")
                # Удаляем разные варианты кеша матчей
                for limit in [10, 20, 50]:
                    await storage.redis.delete(f"player_matches:{player_id}:{limit}")
            
            logger.info(f"Invalidated cache for player: {nickname}")
            
        except Exception as e:
            logger.error(f"Error invalidating player cache {nickname}: {e}")
    
    @classmethod
    async def get_cache_stats(cls) -> Dict[str, int]:
        """Получить статистику использования кеша"""
        try:
            # Получаем все ключи кеша
            keys = await storage.redis.keys("player_*")
            
            stats = {
                'total_keys': len(keys),
                'profiles': len([k for k in keys if k.startswith(b'player_profile:')]),
                'stats': len([k for k in keys if k.startswith(b'player_stats:')]),
                'matches': len([k for k in keys if k.startswith(b'player_matches:')]),
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'total_keys': 0, 'profiles': 0, 'stats': 0, 'matches': 0}