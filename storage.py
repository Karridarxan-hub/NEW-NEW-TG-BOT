from bot.services.database_storage import DatabaseStorage
from config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# Глобальный экземпляр хранилища
storage = DatabaseStorage()

async def init_storage():
    """Инициализация подключения к базам данных"""
    try:
        # Проверяем наличие URL для подключения
        if not settings.database_url or not settings.redis_url:
            logger.error("❌ Database URLs not configured in .env file")
            raise ValueError("Database URLs not configured")
        
        # Подключаемся к базам данных
        await storage.connect(settings.database_url, settings.redis_url)
        
        logger.info("✅ Storage initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize storage: {e}")
        raise

async def cleanup_storage():
    """Закрытие подключений к базам данных"""
    try:
        await storage.disconnect()
        logger.info("Storage connections closed")
    except Exception as e:
        logger.error(f"Error closing storage connections: {e}")

async def cleanup_storage_task():
    """Фоновая задача для очистки кэша и уведомлений"""
    while True:
        try:
            await asyncio.sleep(1800)  # Каждые 30 минут
            await storage.cleanup_expired_cache()
            await storage.cleanup_old_notifications(30)  # Очищаем уведомления старше 30 дней
            logger.info("Cache and notifications cleanup task completed")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(300)  # При ошибке ждем 5 минут


# Для обратной совместимости со старыми обработчиками
# Создаем wrapper класс с теми же методами, что были в InMemoryStorage

class LegacyStorageWrapper:
    """Wrapper для обратной совместимости со старыми методами"""
    
    def __init__(self, db_storage: DatabaseStorage):
        self.db = db_storage
    
    # Пользователи
    def get_user(self, user_id: int):
        """Синхронная обертка для получения пользователя"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_user(user_id))
        except:
            return None
    
    def save_user(self, user_id: int, faceit_id: str, nickname: str):
        """Синхронная обертка для сохранения пользователя"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.db.save_user(user_id, faceit_id, nickname))
        except Exception as e:
            logger.error(f"Error saving user: {e}")
    
    def get_user_faceit_id(self, user_id: int):
        """Синхронная обертка для получения FACEIT ID"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_user_faceit_id(user_id))
        except:
            return None
    
    # Настройки
    def get_user_settings(self, user_id: int):
        """Синхронная обертка для получения настроек"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_user_settings(user_id))
        except:
            return {'notifications': True, 'language': 'ru'}
    
    def update_user_settings(self, user_id: int, settings: dict):
        """Синхронная обертка для обновления настроек"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.db.update_user_settings(user_id, settings))
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
    
    # Сравнение игроков
    def get_comparison_list(self, user_id: int):
        """Синхронная обертка для получения списка сравнения"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_comparison_list(user_id))
        except:
            return []
    
    def add_to_comparison(self, user_id: int, player_data: dict):
        """Синхронная обертка для добавления в сравнение"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.db.add_to_comparison(user_id, player_data))
        except Exception as e:
            logger.error(f"Error adding to comparison: {e}")
    
    def clear_comparison_list(self, user_id: int):
        """Синхронная обертка для очистки списка сравнения"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.db.clear_comparison_list(user_id))
        except Exception as e:
            logger.error(f"Error clearing comparison: {e}")
    
    # Кэширование
    def get_cached_data(self, cache_key: str, max_age_minutes: int = 5):
        """Синхронная обертка для получения кэша"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_cached_data(cache_key, max_age_minutes))
        except:
            return None
    
    def set_cached_data(self, cache_key: str, data):
        """Синхронная обертка для установки кэша"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.db.set_cached_data(cache_key, data))
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
    
    # Утилиты
    def get_current_time(self):
        """Получить текущее время"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.db.get_current_time())
        except:
            return None

    # Совместимость со старыми свойствами
    @property
    def users(self):
        """Эмуляция старого интерфейса users"""
        return {}
    
    @property 
    def sessions(self):
        """Эмуляция старого интерфейса sessions"""
        return {}
        
    @property
    def faceit_cache(self):
        """Эмуляция старого интерфейса faceit_cache"""
        return {}

# Создаем wrapper для обратной совместимости
legacy_storage = LegacyStorageWrapper(storage)

# Экспортируем для использования в старых обработчиках
# Можно постепенно мигрировать на прямое использование storage
__all__ = ['storage', 'legacy_storage', 'init_storage', 'cleanup_storage', 'cleanup_storage_task']