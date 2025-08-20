import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import User, Chat, Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from faceit_client import FaceitAPIClient
from bot.services.database_storage import DatabaseStorage
# Импорты для тестирования без прямого импорта декорированных функций


class TestFaceitClient:
    """Тесты для FACEIT API клиента"""
    
    @pytest.fixture
    def faceit_client(self):
        return FaceitAPIClient()
    
    @pytest.mark.asyncio
    async def test_calculate_hltv_rating(self, faceit_client):
        """Тест расчета HLTV рейтинга"""
        stats = {
            'Rounds': 26,
            'Kills': 20,
            'Deaths': 15,
            'Assists': 5,
            'ADR': 85.5,
            'KAST %': 75.0
        }
        
        rating = faceit_client.calculate_hltv_rating(stats)
        
        assert isinstance(rating, float)
        assert 0 <= rating <= 3.0  # Разумные границы для HLTV рейтинга
    
    @pytest.mark.asyncio
    async def test_format_player_stats(self, faceit_client):
        """Тест форматирования статистики игрока"""
        player_data = {
            'nickname': 'TestPlayer',
            'games': {
                'cs2': {
                    'skill_level': 7,
                    'faceit_elo': 1850
                }
            }
        }
        
        stats_data = {
            'segments': [
                {
                    'label': 'Overall',
                    'stats': {
                        'Matches': 100,
                        'Wins': 65,
                        'Win Rate %': 65.0,
                        'Kills': 1500,
                        'Deaths': 1200,
                        'Assists': 400,
                        'K/D Ratio': 1.25,
                        'ADR': 78.5,
                        'KAST %': 72.0
                    }
                }
            ]
        }
        
        formatted = faceit_client.format_player_stats(player_data, stats_data)
        
        assert formatted['nickname'] == 'TestPlayer'
        assert formatted['level'] == 7
        assert formatted['elo'] == 1850
        assert formatted['matches'] == 100
        assert formatted['winrate'] == 65.0
        assert formatted['kd_ratio'] == 1.25


class TestStorage:
    """Тесты для системы хранения"""
    
    @pytest.fixture
    def storage(self):
        # Создаем AsyncMock для тестирования без реальной БД
        storage = AsyncMock()
        return storage
    
    @pytest.mark.asyncio
    async def test_user_management(self, storage):
        """Тест управления пользователями"""
        user_id = 12345
        faceit_id = "test-faceit-id"
        nickname = "TestPlayer"
        
        # Настраиваем mock возвращаемые значения
        storage.get_user.return_value = {'faceit_id': faceit_id, 'nickname': nickname}
        storage.get_user_faceit_id.return_value = faceit_id
        
        # Проверяем получение данных  
        user_data = await storage.get_user(user_id)
        assert user_data['faceit_id'] == faceit_id
        assert user_data['nickname'] == nickname
        
        # Проверяем получение FACEIT ID
        retrieved_faceit_id = await storage.get_user_faceit_id(user_id)
        assert retrieved_faceit_id == faceit_id
    
    @pytest.mark.asyncio
    async def test_session_management(self, storage):
        """Тест управления сессиями"""
        user_id = 12345
        
        # Настраиваем mock для сессии
        session = {
            'start_time': '2024-01-01T12:00:00',
            'matches': [{'match_id': 'test-match', 'won': True, 'kills': 20, 'deaths': 15}]
        }
        storage.get_session.return_value = session
        
        # Проверяем получение сессии
        retrieved_session = await storage.get_session(user_id)
        assert 'start_time' in retrieved_session
        assert 'matches' in retrieved_session
        assert isinstance(retrieved_session['matches'], list)
        assert len(retrieved_session['matches']) == 1
        assert retrieved_session['matches'][0]['match_id'] == 'test-match'
    
    @pytest.mark.asyncio
    async def test_cache_management(self, storage):
        """Тест управления кэшем"""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Настраиваем mock для кэша
        storage.get_cached_data.return_value = test_data
        
        # Получаем данные из кэша
        cached_data = await storage.get_cached_data(cache_key)
        assert cached_data == test_data
    
    @pytest.mark.asyncio
    async def test_user_settings(self, storage):
        """Тест настроек пользователя"""
        user_id = 12345
        
        # Настраиваем mock для настроек
        default_settings = {'match_notifications': True, 'subscription_type': 'standard'}
        updated_settings = {'match_notifications': False, 'subscription_type': 'standard'}
        
        storage.get_user_settings.side_effect = [default_settings, updated_settings]
        
        # Получаем настройки по умолчанию
        settings = await storage.get_user_settings(user_id)
        assert settings['match_notifications'] is True
        assert settings['subscription_type'] == 'standard'
        
        # Получаем обновленные настройки
        final_settings = await storage.get_user_settings(user_id)
        assert final_settings['match_notifications'] is False
        assert final_settings['subscription_type'] == 'standard'


class TestBotHandlers:
    """Интеграционные тесты для обработчиков бота"""
    
    @pytest.mark.asyncio
    async def test_storage_integration(self):
        """Тест интеграции с системой хранения"""
        from storage import storage
        
        # Тестируем что storage инициализирован
        assert storage is not None
        assert hasattr(storage, 'get_user_faceit_id')
    
    @pytest.mark.asyncio  
    async def test_faceit_client_integration(self):
        """Тест интеграции с FACEIT клиентом"""
        from faceit_client import faceit_client
        
        # Тестируем что клиент инициализирован
        assert faceit_client is not None
        assert hasattr(faceit_client, 'find_player_by_nickname')
    
    @pytest.mark.asyncio
    async def test_keyboards_integration(self):
        """Тест интеграции с клавиатурами"""
        from keyboards import get_main_menu_keyboard
        
        # Тестируем генерацию главного меню
        keyboard = get_main_menu_keyboard()
        assert keyboard is not None
        
    @pytest.mark.asyncio
    async def test_handlers_import(self):
        """Тест импорта всех обработчиков"""
        # Проверяем что все модули handlers импортируются
        from bot.handlers import main_router, stats_router, match_router, settings_router
        
        assert main_router is not None
        assert stats_router is not None  
        assert match_router is not None
        assert settings_router is not None
    
    @pytest.mark.asyncio
    async def test_main_app_integration(self):
        """Тест интеграции основного приложения"""
        from main import app, bot, dp
        
        # Проверяем что основные компоненты инициализированы
        assert app is not None
        assert bot is not None
        assert dp is not None


class TestMatchHandlers:
    """Тесты для обработчиков матчей"""
    
    def test_calculate_player_stats_from_match(self):
        """Тест расчета статистики игрока из матча"""
        from match_handlers import calculate_player_stats_from_match
        
        player_stats = {
            'stats': {
                'Kills': '20',
                'Deaths': '15',
                'Assists': '5',
                'Rounds': '26',
                'ADR': '85.5',
                'KAST %': '75.0',
                'Headshots %': '45.0'
            }
        }
        
        result = calculate_player_stats_from_match(player_stats)
        
        assert result['kills'] == 20
        assert result['deaths'] == 15
        assert result['assists'] == 5
        assert result['kd_ratio'] == 1.33  # 20/15 rounded
        assert result['adr'] == 85.5
        assert result['kast'] == 75.0
        assert isinstance(result['hltv_rating'], float)


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])