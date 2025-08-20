import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisClient:
    """Клиент для работы с Redis"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
        # Настройки TTL для разных типов данных
        self.ttl_settings = {
            'user_sessions': 1800,      # 30 минут
            'api_cache': 300,           # 5 минут  
            'match_cache': 3600,        # 1 час
            'temp_data': 600,           # 10 минут
            'rate_limits': 60,          # 1 минута
        }
    
    async def connect(self, redis_url: str):
        """Подключение к Redis"""
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Закрытие подключения"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    # === КЭШИРОВАНИЕ ДАННЫХ ===
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
            
            # Пробуем распарсить JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установить значение по ключу"""
        try:
            # Сериализуем в JSON если это не строка
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить ключ"""
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking key existence {key}: {e}")
            return False
    
    # === ПОЛЬЗОВАТЕЛЬСКИЕ СЕССИИ ===
    
    async def start_user_session(self, user_id: int) -> str:
        """Начать пользовательскую сессию"""
        session_id = f"session:{user_id}:{datetime.now().timestamp()}"
        session_data = {
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'matches': [],
            'stats': {}
        }
        
        await self.set(session_id, session_data, self.ttl_settings['user_sessions'])
        await self.set(f"current_session:{user_id}", session_id, self.ttl_settings['user_sessions'])
        
        return session_id
    
    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить текущую сессию пользователя"""
        session_key = await self.get(f"current_session:{user_id}")
        if session_key:
            return await self.get(session_key)
        return None
    
    async def update_session_stats(self, user_id: int, stats: Dict[str, Any]) -> bool:
        """Обновить статистику сессии"""
        session = await self.get_user_session(user_id)
        if session:
            session['stats'].update(stats)
            session_key = await self.get(f"current_session:{user_id}")
            return await self.set(session_key, session, self.ttl_settings['user_sessions'])
        return False
    
    # === КЭШИРОВАНИЕ API ЗАПРОСОВ ===
    
    async def cache_api_response(self, endpoint: str, params: str, response: Any) -> bool:
        """Кэшировать ответ API"""
        cache_key = f"api_cache:{endpoint}:{hash(params)}"
        cache_data = {
            'response': response,
            'cached_at': datetime.now().isoformat(),
            'endpoint': endpoint,
            'params': params
        }
        
        return await self.set(cache_key, cache_data, self.ttl_settings['api_cache'])
    
    async def get_cached_api_response(self, endpoint: str, params: str) -> Optional[Any]:
        """Получить кэшированный ответ API"""
        cache_key = f"api_cache:{endpoint}:{hash(params)}"
        cached_data = await self.get(cache_key)
        
        if cached_data:
            return cached_data.get('response')
        return None
    
    # === RATE LIMITING ===
    
    async def check_rate_limit(self, user_id: int, action: str, limit: int = 10) -> bool:
        """Проверить лимит запросов"""
        key = f"rate_limit:{user_id}:{action}"
        
        try:
            current = await self.redis.get(key)
            
            if current is None:
                # Первый запрос
                await self.redis.setex(key, self.ttl_settings['rate_limits'], 1)
                return True
            
            current_count = int(current)
            if current_count >= limit:
                return False
            
            # Увеличиваем счетчик
            await self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {user_id}:{action}: {e}")
            return True  # В случае ошибки разрешаем запрос
    
    async def reset_rate_limit(self, user_id: int, action: str) -> bool:
        """Сбросить лимит запросов"""
        key = f"rate_limit:{user_id}:{action}"
        return await self.delete(key)
    
    # === ВРЕМЕННЫЕ ДАННЫЕ ===
    
    async def store_temp_data(self, key: str, data: Any, ttl: int = None) -> bool:
        """Сохранить временные данные"""
        if ttl is None:
            ttl = self.ttl_settings['temp_data']
        
        return await self.set(f"temp:{key}", data, ttl)
    
    async def get_temp_data(self, key: str) -> Optional[Any]:
        """Получить временные данные"""
        return await self.get(f"temp:{key}")
    
    async def delete_temp_data(self, key: str) -> bool:
        """Удалить временные данные"""
        return await self.delete(f"temp:{key}")
    
    # === СПИСКИ И МНОЖЕСТВА ===
    
    async def add_to_list(self, list_key: str, value: Any, max_size: int = 100) -> bool:
        """Добавить элемент в список"""
        try:
            # Добавляем в начало списка
            await self.redis.lpush(list_key, json.dumps(value))
            
            # Обрезаем список до максимального размера
            await self.redis.ltrim(list_key, 0, max_size - 1)
            
            # Устанавливаем TTL если его нет
            ttl = await self.redis.ttl(list_key)
            if ttl == -1:  # Нет TTL
                await self.redis.expire(list_key, self.ttl_settings['temp_data'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to list {list_key}: {e}")
            return False
    
    async def get_list(self, list_key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Получить элементы списка"""
        try:
            items = await self.redis.lrange(list_key, start, end)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Error getting list {list_key}: {e}")
            return []
    
    async def add_to_set(self, set_key: str, value: str) -> bool:
        """Добавить элемент в множество"""
        try:
            await self.redis.sadd(set_key, value)
            
            # Устанавливаем TTL если его нет
            ttl = await self.redis.ttl(set_key)
            if ttl == -1:
                await self.redis.expire(set_key, self.ttl_settings['temp_data'])
            
            return True
        except Exception as e:
            logger.error(f"Error adding to set {set_key}: {e}")
            return False
    
    async def is_in_set(self, set_key: str, value: str) -> bool:
        """Проверить наличие элемента в множестве"""
        try:
            return bool(await self.redis.sismember(set_key, value))
        except Exception as e:
            logger.error(f"Error checking set membership {set_key}: {e}")
            return False
    
    # === СТАТИСТИКА И МОНИТОРИНГ ===
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Получить информацию о Redis"""
        try:
            info = await self.redis.info()
            return {
                'used_memory': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        try:
            # Считаем ключи по типам
            pattern_counts = {}
            for pattern in ['api_cache:*', 'session:*', 'temp:*', 'rate_limit:*']:
                keys = await self.redis.keys(pattern)
                pattern_counts[pattern.replace('*', 'count')] = len(keys)
            
            return pattern_counts
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    # === УТИЛИТЫ ===
    
    async def clear_cache(self, pattern: str = None) -> int:
        """Очистить кэш по паттерну"""
        try:
            if pattern:
                keys = await self.redis.keys(pattern)
                if keys:
                    return await self.redis.delete(*keys)
            else:
                return await self.redis.flushdb()
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    async def set_expiry(self, key: str, seconds: int) -> bool:
        """Установить время жизни ключа"""
        try:
            return bool(await self.redis.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiry for {key}: {e}")
            return False