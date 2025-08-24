import asyncpg
import redis.asyncio as redis
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseStorage:
    """Система хранения данных с PostgreSQL и Redis"""
    
    def __init__(self):
        self.postgres: Optional[asyncpg.Connection] = None
        self.redis: Optional[redis.Redis] = None
        
        # Настройки подключения (будут загружаться из config)
        self.postgres_url = None
        self.redis_url = None
        
        # Кэш TTL настройки
        self.cache_ttl = {
            'user_cache': 300,      # 5 минут
            'match_cache': 3600,    # 1 час
            'session_cache': 1800,  # 30 минут
            'faceit_cache': 300     # 5 минут
        }
    
    async def connect(self, postgres_url: str, redis_url: str):
        """Подключение к PostgreSQL и Redis"""
        try:
            # Подключение к PostgreSQL
            self.postgres = await asyncpg.connect(postgres_url)
            logger.info("✅ Подключение к PostgreSQL установлено")
            
            # Подключение к Redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Подключение к Redis установлено")
            
            # Создание необходимых таблиц
            await self._create_tables()
            logger.info("✅ Таблицы базы данных проверены/созданы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базам данных: {e}")
            raise
    
    async def _create_tables(self):
        """Создание необходимых таблиц при первом запуске"""
        try:
            # Таблица для кэша FACEIT API
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS faceit_cache (
                    cache_key TEXT PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_faceit_cache_expires_at ON faceit_cache(expires_at);
            """)
            
            # Таблица для пользователей
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    faceit_id TEXT UNIQUE NOT NULL,
                    nickname TEXT NOT NULL,
                    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_users_faceit_id ON users(faceit_id);
            """)
            
            # Таблица для сессий пользователей
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
            """)
            
            # Таблица для уведомлений  
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    notification_type TEXT NOT NULL,
                    data JSONB NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
                CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent);
            """)
            
            logger.info("✅ Схема базы данных готова (4 таблицы)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise

    async def disconnect(self):
        """Закрытие подключений"""
        if self.postgres:
            await self.postgres.close()
            logger.info("PostgreSQL connection closed")
        
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    # === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===
    
    async def save_user(self, user_id: int, faceit_id: str, nickname: str) -> None:
        """Сохранить пользователя в базе данных"""
        query = """
            INSERT INTO users (user_id, faceit_id, nickname, created_at, last_activity)
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                faceit_id = EXCLUDED.faceit_id,
                nickname = EXCLUDED.nickname,
                last_activity = NOW()
        """
        
        try:
            await self.postgres.execute(query, user_id, faceit_id, nickname)
            
            # Также кэшируем в Redis
            user_data = {
                'faceit_id': faceit_id,
                'nickname': nickname,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            await self.redis.hset(f"user:{user_id}", mapping=user_data)
            await self.redis.expire(f"user:{user_id}", self.cache_ttl['user_cache'])
            
            logger.info(f"User {user_id} ({nickname}) saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        # Сначала пробуем Redis
        try:
            cached_data = await self.redis.hgetall(f"user:{user_id}")
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Redis cache miss for user {user_id}: {e}")
        
        # Если нет в кэше, обращаемся к PostgreSQL
        query = """
            SELECT user_id, faceit_id, nickname, created_at, last_activity 
            FROM users WHERE user_id = $1
        """
        
        try:
            row = await self.postgres.fetchrow(query, user_id)
            if row:
                user_data = dict(row)
                # Преобразуем datetime в строки для JSON
                user_data['created_at'] = user_data['created_at'].isoformat()
                user_data['last_activity'] = user_data['last_activity'].isoformat()
                
                # Кэшируем результат
                await self.redis.hset(f"user:{user_id}", mapping=user_data)
                await self.redis.expire(f"user:{user_id}", self.cache_ttl['user_cache'])
                
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_user_faceit_id(self, user_id: int) -> Optional[str]:
        """Получить FACEIT ID пользователя"""
        user_data = await self.get_user(user_id)
        return user_data.get('faceit_id') if user_data else None
    
    # === НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ ===
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получить настройки пользователя"""
        query = """
            SELECT notifications, language, subscription_type, updated_at
            FROM user_settings WHERE user_id = $1
        """
        
        try:
            row = await self.postgres.fetchrow(query, user_id)
            if row:
                return dict(row)
            else:
                # Создаем настройки по умолчанию
                await self.update_user_settings(user_id, {
                    'notifications': True,
                    'language': 'ru',
                    'subscription_type': 'standard'
                })
                return {
                    'notifications': True,
                    'language': 'ru',
                    'subscription_type': 'standard'
                }
        except Exception as e:
            logger.error(f"Error getting user settings {user_id}: {e}")
            return {'notifications': True, 'language': 'ru', 'subscription_type': 'standard'}
    
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> None:
        """Обновить настройки пользователя"""
        query = """
            INSERT INTO user_settings (user_id, notifications, language, subscription_type, updated_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                notifications = COALESCE($2, user_settings.notifications),
                language = COALESCE($3, user_settings.language),
                subscription_type = COALESCE($4, user_settings.subscription_type),
                updated_at = NOW()
        """
        
        try:
            await self.postgres.execute(
                query,
                user_id,
                settings.get('notifications'),
                settings.get('language'),
                settings.get('subscription_type')
            )
            
            # Инвалидируем кэш настроек
            await self.redis.delete(f"settings:{user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user settings {user_id}: {e}")
            raise
    
    # === СРАВНЕНИЕ ИГРОКОВ ===
    
    async def get_comparison_list(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить список игроков для сравнения"""
        query = """
            SELECT player_faceit_id, player_nickname, added_at
            FROM comparison_lists 
            WHERE user_id = $1
            ORDER BY added_at DESC
            LIMIT 5
        """
        
        try:
            rows = await self.postgres.fetch(query, user_id)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting comparison list {user_id}: {e}")
            return []
    
    async def add_to_comparison(self, user_id: int, player_data: Dict[str, Any]) -> None:
        """Добавить игрока в список сравнения"""
        query = """
            INSERT INTO comparison_lists (user_id, player_faceit_id, player_nickname, added_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, player_faceit_id) DO NOTHING
        """
        
        try:
            await self.postgres.execute(
                query,
                user_id,
                player_data['faceit_id'],
                player_data['nickname']
            )
        except Exception as e:
            logger.error(f"Error adding to comparison {user_id}: {e}")
            raise
    
    async def clear_comparison_list(self, user_id: int) -> None:
        """Очистить список сравнения"""
        query = "DELETE FROM comparison_lists WHERE user_id = $1"
        
        try:
            await self.postgres.execute(query, user_id)
        except Exception as e:
            logger.error(f"Error clearing comparison list {user_id}: {e}")
            raise
    
    # === КЭШИРОВАНИЕ FACEIT API ===
    
    async def get_cached_data(self, cache_key: str, max_age_minutes: int = 5) -> Optional[Any]:
        """Получить кэшированные данные FACEIT API"""
        try:
            # Сначала пробуем Redis
            cached_json = await self.redis.get(f"faceit:{cache_key}")
            if cached_json:
                return json.loads(cached_json)
            
            # Если нет в Redis, проверяем PostgreSQL
            query = """
                SELECT data FROM faceit_cache 
                WHERE cache_key = $1 AND expires_at > NOW()
            """
            
            row = await self.postgres.fetchrow(query, cache_key)
            if row:
                # Если данные в виде строки, парсим их, если dict - используем как есть
                data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
                # Сохраняем в Redis для быстрого доступа
                await self.redis.setex(
                    f"faceit:{cache_key}",
                    self.cache_ttl['faceit_cache'],
                    json.dumps(data)
                )
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data {cache_key}: {e}")
            return None
    
    async def set_cached_data(self, cache_key: str, data: Any, ttl_minutes: int = 5) -> None:
        """Сохранить данные в кэш"""
        try:
            # Сохраняем в Redis
            await self.redis.setex(
                f"faceit:{cache_key}",
                ttl_minutes * 60,
                json.dumps(data)
            )
            
            # Сохраняем в PostgreSQL для долгосрочного хранения
            query = """
                INSERT INTO faceit_cache (cache_key, data, created_at, expires_at)
                VALUES ($1, $2::jsonb, NOW(), NOW() + INTERVAL '%s minutes')
                ON CONFLICT (cache_key)
                DO UPDATE SET
                    data = EXCLUDED.data,
                    created_at = NOW(),
                    expires_at = NOW() + INTERVAL '%s minutes'
            """ % (ttl_minutes, ttl_minutes)
            
            await self.postgres.execute(query, cache_key, json.dumps(data, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"Error setting cached data {cache_key}: {e}")
    
    # === ИСТОРИЯ МАТЧЕЙ ===
    
    async def save_match(self, match_data: Dict[str, Any]) -> None:
        """Сохранить матч в историю"""
        query = """
            INSERT INTO match_history (
                match_id, user_id, finished_at, result,
                kills, deaths, assists, adr, hltv_rating,
                headshots, headshot_percentage, map_name,
                score_team1, score_team2, rounds_played
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (match_id) DO UPDATE SET
                result = EXCLUDED.result,
                kills = EXCLUDED.kills,
                deaths = EXCLUDED.deaths,
                assists = EXCLUDED.assists,
                adr = EXCLUDED.adr,
                hltv_rating = EXCLUDED.hltv_rating
        """
        
        try:
            await self.postgres.execute(
                query,
                match_data.get('match_id'),
                match_data.get('user_id'),
                match_data.get('finished_at'),
                match_data.get('result'),
                match_data.get('kills', 0),
                match_data.get('deaths', 0),
                match_data.get('assists', 0),
                match_data.get('adr', 0.0),
                match_data.get('hltv_rating', 0.0),
                match_data.get('headshots', 0),
                match_data.get('headshot_percentage', 0.0),
                match_data.get('map_name'),
                match_data.get('score_team1', 0),
                match_data.get('score_team2', 0),
                match_data.get('rounds_played', 0)
            )
        except Exception as e:
            logger.error(f"Error saving match {match_data.get('match_id')}: {e}")
            raise
    
    async def get_match_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить историю матчей пользователя"""
        query = """
            SELECT * FROM match_history 
            WHERE user_id = $1 
            ORDER BY finished_at DESC 
            LIMIT $2
        """
        
        try:
            rows = await self.postgres.fetch(query, user_id, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting match history {user_id}: {e}")
            return []
    
    # === УТИЛИТЫ ===
    
    async def get_current_time(self) -> str:
        """Получить текущее время"""
        return datetime.now().isoformat()
    
    async def cleanup_expired_cache(self) -> None:
        """Очистка просроченного кэша"""
        try:
            # Очистка PostgreSQL кэша
            await self.postgres.execute("SELECT clean_expired_cache()")
            
            # Redis кэш очищается автоматически через TTL
            logger.info("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    # === УВЕДОМЛЕНИЯ ===
    
    async def get_users_with_notifications(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей с включенными уведомлениями"""
        query = """
            SELECT u.user_id, u.faceit_id, u.nickname, us.notifications
            FROM users u
            LEFT JOIN user_settings us ON u.user_id = us.user_id
            WHERE us.notifications = true OR us.notifications IS NULL
        """
        
        try:
            rows = await self.postgres.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting users with notifications: {e}")
            return []
    
    async def get_user_by_faceit_id(self, faceit_id: str) -> Optional[Dict[str, Any]]:
        """Найти пользователя по FACEIT ID"""
        query = """
            SELECT u.user_id, u.faceit_id, u.nickname, us.notifications
            FROM users u
            LEFT JOIN user_settings us ON u.user_id = us.user_id
            WHERE u.faceit_id = $1
        """
        
        try:
            row = await self.postgres.fetchrow(query, faceit_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user by faceit_id {faceit_id}: {e}")
            return None
    
    async def is_match_notification_sent(self, match_id: str, user_id: int) -> bool:
        """Проверить, было ли уже отправлено уведомление о матче"""
        query = """
            SELECT 1 FROM match_notifications 
            WHERE match_id = $1 AND user_id = $2
        """
        
        try:
            result = await self.postgres.fetchrow(query, match_id, user_id)
            return result is not None
        except Exception as e:
            logger.error(f"Error checking match notification {match_id} for user {user_id}: {e}")
            return True  # В случае ошибки считаем что уведомление уже было отправлено
    
    async def mark_match_notification_sent(self, match_id: str, user_id: int, match_data: Dict[str, Any] = None) -> None:
        """Отметить что уведомление о матче было отправлено"""
        query = """
            INSERT INTO match_notifications (match_id, user_id, sent_at, match_data)
            VALUES ($1, $2, NOW(), $3)
            ON CONFLICT (match_id, user_id) DO NOTHING
        """
        
        try:
            match_json = json.dumps(match_data) if match_data else None
            await self.postgres.execute(query, match_id, user_id, match_json)
        except Exception as e:
            logger.error(f"Error marking match notification {match_id} for user {user_id}: {e}")
            raise
    
    async def get_last_processed_match_time(self, faceit_id: str) -> Optional[datetime]:
        """Получить время последнего обработанного матча для игрока"""
        query = """
            SELECT MAX(finished_at) as last_match_time
            FROM match_history mh
            JOIN users u ON mh.user_id = u.user_id
            WHERE u.faceit_id = $1
        """
        
        try:
            result = await self.postgres.fetchval(query, faceit_id)
            return result
        except Exception as e:
            logger.error(f"Error getting last processed match time for {faceit_id}: {e}")
            return None
    
    async def save_notification_log(self, user_id: int, match_id: str, status: str, error_message: str = None) -> None:
        """Сохранить лог уведомления"""
        query = """
            INSERT INTO notification_logs (user_id, match_id, status, error_message, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """
        
        try:
            await self.postgres.execute(query, user_id, match_id, status, error_message)
        except Exception as e:
            logger.error(f"Error saving notification log: {e}")
    
    async def cleanup_old_notifications(self, days: int = 30) -> None:
        """Очистить старые записи уведомлений"""
        try:
            # Удаляем старые записи о отправленных уведомлениях
            await self.postgres.execute(
                "DELETE FROM match_notifications WHERE sent_at < NOW() - INTERVAL '%s days'", 
                days
            )
            
            # Удаляем старые логи уведомлений
            await self.postgres.execute(
                "DELETE FROM notification_logs WHERE created_at < NOW() - INTERVAL '%s days'", 
                days
            )
            
            logger.info(f"Cleaned up notifications older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику базы данных"""
        try:
            stats = {}
            
            # Статистика пользователей
            users_count = await self.postgres.fetchval("SELECT COUNT(*) FROM users")
            stats['total_users'] = users_count
            
            # Статистика матчей (если таблица существует)
            try:
                matches_count = await self.postgres.fetchval("SELECT COUNT(*) FROM match_history")
                stats['total_matches'] = matches_count
            except:
                stats['total_matches'] = 0
            
            # Статистика уведомлений
            try:
                notifications_count = await self.postgres.fetchval("SELECT COUNT(*) FROM match_notifications")
                stats['total_notifications'] = notifications_count
            except:
                stats['total_notifications'] = 0
            
            # Подробная статистика кэша
            cache_count = await self.postgres.fetchval("SELECT COUNT(*) FROM faceit_cache WHERE expires_at > NOW()")
            expired_cache_count = await self.postgres.fetchval("SELECT COUNT(*) FROM faceit_cache WHERE expires_at <= NOW()")
            total_cache_size = await self.postgres.fetchval("SELECT pg_size_pretty(pg_total_relation_size('faceit_cache'))")
            
            stats['cache_entries'] = cache_count
            stats['expired_cache_entries'] = expired_cache_count  
            stats['cache_table_size'] = total_cache_size
            
            # Redis статистика
            try:
                redis_info = await self.redis.info('memory')
                stats['redis_used_memory'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_keys_count'] = await self.redis.dbsize()
            except:
                stats['redis_used_memory'] = 'N/A'
                stats['redis_keys_count'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'total_users': 0, 'total_matches': 0, 'cache_entries': 0}