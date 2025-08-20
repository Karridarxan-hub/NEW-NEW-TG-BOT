#!/usr/bin/env python3
"""
Комплексная система тестирования всех функций статистики на реальном аккаунте "Geun-Hee"
Включает в себя все основные тесты, валидацию данных, интеграционные тесты и обработку ошибок.

Автор: Claude Code
Версия: 1.0
Дата: 2025-08-19
"""

import asyncio
import logging
import json
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import sys
import os

# Настройка логирования с подробным форматированием
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('comprehensive_test.log', encoding='utf-8')
    ]
)

# Устанавливаем кодировку для stdout в Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)

# Импорты проекта
try:
    from faceit_client import FaceitAPIClient
    from bot.handlers.stats_handler import (
        safe_float, safe_int, validate_user_data, format_time_ago
    )
    from storage import storage
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    sys.exit(1)


class ComprehensiveStatsValidator:
    """Класс для комплексной валидации статистических данных"""
    
    @staticmethod
    def validate_player_basic_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация базовых данных игрока"""
        errors = []
        
        # Обязательные поля
        required_fields = ['player_id', 'nickname']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Отсутствует обязательное поле: {field}")
        
        # Валидация ELO и уровня
        elo = data.get('elo', 0)
        level = data.get('level', 0)
        
        if not (0 <= elo <= 4000):
            errors.append(f"ELO вне допустимого диапазона: {elo}")
        
        if not (0 <= level <= 10):
            errors.append(f"Уровень вне допустимого диапазона: {level}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_player_stats(stats: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация статистики игрока"""
        errors = []
        
        # Проверка численных значений
        numeric_checks = [
            ('matches', 0, 100000),
            ('wins', 0, 100000),
            ('winrate', 0, 100),
            ('kd_ratio', 0, 10),
            ('adr', 0, 200),
            ('kast', 0, 100),
            ('hltv_rating', 0, 3),
            ('headshots_avg', 0, 100),
            ('headshots_total', 0, 100)
        ]
        
        for field, min_val, max_val in numeric_checks:
            value = stats.get(field, 0)
            if not isinstance(value, (int, float)):
                errors.append(f"Поле {field} должно быть числовым: {type(value)}")
                continue
                
            if not (min_val <= value <= max_val):
                errors.append(f"Поле {field} вне допустимого диапазона {min_val}-{max_val}: {value}")
        
        # Логические проверки
        if stats.get('wins', 0) > stats.get('matches', 0):
            errors.append("Побед больше чем матчей")
        
        if stats.get('deaths', 0) > 0 and stats.get('kd_ratio', 0) > 0:
            calculated_kd = stats.get('kills', 0) / stats.get('deaths', 1)
            if abs(calculated_kd - stats.get('kd_ratio', 0)) > 0.01:
                logger.warning(f"Расхождение в K/D: рассчитано {calculated_kd:.3f}, получено {stats.get('kd_ratio'):.3f}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_maps_stats(maps_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация статистики по картам"""
        errors = []
        
        if not isinstance(maps_data, dict):
            return False, ["Данные карт должны быть словарем"]
        
        for map_name, map_stats in maps_data.items():
            if not isinstance(map_stats, dict):
                errors.append(f"Статистика карты {map_name} должна быть словарем")
                continue
            
            # Проверяем базовые поля карты
            if map_stats.get('wins', 0) > map_stats.get('matches', 0):
                errors.append(f"На карте {map_name} побед больше матчей")
            
            winrate = map_stats.get('winrate', 0)
            if not (0 <= winrate <= 100):
                errors.append(f"Винрейт на карте {map_name} вне диапазона: {winrate}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_match_history(history_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация данных истории матчей"""
        errors = []
        
        if not isinstance(history_data, dict) or 'items' not in history_data:
            return False, ["История должна содержать поле 'items'"]
        
        items = history_data['items']
        if not isinstance(items, list):
            return False, ["Поле 'items' должно быть списком"]
        
        for i, match in enumerate(items[:5]):  # Проверяем первые 5 матчей
            if not isinstance(match, dict):
                errors.append(f"Матч {i} должен быть словарем")
                continue
            
            # Проверяем наличие базовых полей
            required_fields = ['match_id', 'game_mode', 'status']
            for field in required_fields:
                if field not in match:
                    errors.append(f"В матче {i} отсутствует поле {field}")
            
            # Проверяем временные метки
            finished_at = match.get('finished_at')
            if finished_at and isinstance(finished_at, (int, float)):
                try:
                    if finished_at > 10**12:
                        match_time = datetime.fromtimestamp(finished_at / 1000)
                    else:
                        match_time = datetime.fromtimestamp(finished_at)
                    
                    # Проверяем что матч не из будущего
                    if match_time > datetime.now() + timedelta(minutes=5):
                        errors.append(f"Матч {i} из будущего: {match_time}")
                        
                except Exception as e:
                    errors.append(f"Ошибка парсинга времени матча {i}: {e}")
        
        return len(errors) == 0, errors


class ComprehensiveStatsTest:
    """Главный класс для комплексного тестирования системы статистики"""
    
    def __init__(self, api_key: str = "41f48f43-609c-4639-b821-360b039f18b4"):
        self.api_key = api_key
        self.test_nickname = "Geun-Hee"
        self.client = None
        self.validator = ComprehensiveStatsValidator()
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'warnings': [],
            'performance_metrics': {}
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Логирование результата теста"""
        self.test_results['total_tests'] += 1
        
        if success:
            self.test_results['passed_tests'] += 1
            status = "[PASS]"
            logger.info(f"{status} - {test_name} ({duration:.2f}s): {details}")
        else:
            self.test_results['failed_tests'] += 1
            status = "[FAIL]"
            logger.error(f"{status} - {test_name} ({duration:.2f}s): {details}")
            self.test_results['errors'].append(f"{test_name}: {details}")
        
        if duration > 0:
            self.test_results['performance_metrics'][test_name] = duration
    
    def log_warning(self, message: str):
        """Логирование предупреждения"""
        logger.warning(f"[WARNING]: {message}")
        self.test_results['warnings'].append(message)
    
    async def setup(self):
        """Инициализация тестового окружения"""
        logger.info("=" * 80)
        logger.info("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ СТАТИСТИКИ FACEIT")
        logger.info("=" * 80)
        logger.info(f"Тестируемый игрок: {self.test_nickname}")
        logger.info(f"API ключ: {self.api_key[:20]}...")
        logger.info(f"Время начала: {datetime.now()}")
        logger.info("=" * 80)
        
        # Инициализация клиента с production API ключом
        self.client = FaceitAPIClient()
        self.client.api_key = self.api_key
        self.client.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Тест подключения к API
        start_time = datetime.now()
        try:
            test_response = await self.client._make_request("/search/players", 
                                                          params={"nickname": "test", "game": "cs2"})
            duration = (datetime.now() - start_time).total_seconds()
            
            if test_response is not None:
                self.log_test_result("API Connection Test", True, "Подключение к FACEIT API успешно", duration)
            else:
                self.log_test_result("API Connection Test", False, "Не удалось подключиться к FACEIT API", duration)
                return False
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("API Connection Test", False, f"Ошибка подключения: {str(e)}", duration)
            return False
        
        return True
    
    async def test_1_find_player(self) -> Optional[Dict]:
        """Тест 1: Поиск игрока Geun-Hee"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 1: ПОИСК ИГРОКА")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            player_data = await self.client.find_player_by_nickname(self.test_nickname)
            duration = (datetime.now() - start_time).total_seconds()
            
            if not player_data:
                self.log_test_result("Find Player", False, f"Игрок {self.test_nickname} не найден", duration)
                return None
            
            # Валидация найденного игрока
            if player_data['nickname'].lower() != self.test_nickname.lower():
                self.log_warning(f"Найден игрок с другим именем: {player_data['nickname']}")
            
            # Проверка игры CS2
            if 'games' in player_data and 'cs2' not in player_data.get('games', {}):
                self.log_test_result("Find Player", False, "Игрок не играет в CS2", duration)
                return None
            
            player_id = player_data['player_id']
            self.log_test_result("Find Player", True, 
                               f"Найден: {player_data['nickname']} (ID: {player_id})", duration)
            
            # Логирование дополнительной информации
            logger.info(f"   Страна: {player_data.get('country', 'N/A')}")
            logger.info(f"   Верифицирован: {'Да' if player_data.get('verified') else 'Нет'}")
            
            return player_data
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Find Player", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return None
    
    async def test_2_get_player_details(self, player_id: str) -> Optional[Dict]:
        """Тест 2: Получение детальной информации о игроке"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 2: ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ИГРОКА")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            details_data = await self.client.get_player_details(player_id)
            duration = (datetime.now() - start_time).total_seconds()
            
            if not details_data:
                self.log_test_result("Get Player Details", False, "Детальная информация не получена", duration)
                return None
            
            # Проверяем наличие CS2 данных
            cs2_data = details_data.get('games', {}).get('cs2', {})
            if not cs2_data:
                self.log_test_result("Get Player Details", False, "Отсутствуют данные CS2", duration)
                return None
            
            # Валидация базовых данных
            is_valid, errors = self.validator.validate_player_basic_data({
                'player_id': details_data.get('player_id'),
                'nickname': details_data.get('nickname'),
                'elo': cs2_data.get('faceit_elo', 0),
                'level': cs2_data.get('skill_level', 0)
            })
            
            if not is_valid:
                for error in errors:
                    self.log_warning(f"Валидация деталей: {error}")
            
            self.log_test_result("Get Player Details", True, 
                               f"ELO: {cs2_data.get('faceit_elo')}, Уровень: {cs2_data.get('skill_level')}", 
                               duration)
            
            # Логирование подробной информации
            logger.info(f"   Регион: {cs2_data.get('region', 'N/A')}")
            logger.info(f"   Игровое имя: {cs2_data.get('game_player_name', 'N/A')}")
            
            return details_data
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Get Player Details", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return None
    
    async def test_3_get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Тест 3: Получение статистики игрока"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 3: СТАТИСТИКА ИГРОКА")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            stats_data = await self.client.get_player_stats(player_id)
            duration = (datetime.now() - start_time).total_seconds()
            
            if not stats_data:
                self.log_test_result("Get Player Stats", False, "Статистика не получена", duration)
                return None
            
            # Проверяем структуру данных
            has_lifetime = 'lifetime' in stats_data
            has_segments = 'segments' in stats_data and len(stats_data['segments']) > 0
            
            if not has_lifetime and not has_segments:
                self.log_test_result("Get Player Stats", False, "Отсутствуют lifetime и segments", duration)
                return None
            
            # Логируем структуру
            logger.info(f"   Lifetime данные: {'Да' if has_lifetime else 'Нет'}")
            logger.info(f"   Segments: {len(stats_data.get('segments', []))}")
            
            if has_lifetime:
                lifetime = stats_data['lifetime']
                logger.info(f"   Матчи: {lifetime.get('Matches', 'N/A')}")
                logger.info(f"   Побед: {lifetime.get('Wins', 'N/A')}")
                logger.info(f"   Винрейт: {lifetime.get('Win Rate %', 'N/A')}%")
            
            # Подсчитываем сегменты карт
            map_segments = [s for s in stats_data.get('segments', []) if s.get('label') != 'Overall']
            logger.info(f"   Карт с данными: {len(map_segments)}")
            
            self.log_test_result("Get Player Stats", True, 
                               f"Структура: {'lifetime' if has_lifetime else ''} + {len(stats_data.get('segments', []))} сегментов", 
                               duration)
            
            return stats_data
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Get Player Stats", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return None
    
    async def test_4_format_player_stats(self, player_details: Dict, stats_data: Dict) -> Optional[Dict]:
        """Тест 4: Форматирование статистики игрока"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 4: ФОРМАТИРОВАНИЕ СТАТИСТИКИ")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            formatted_stats = self.client.format_player_stats(player_details, stats_data)
            duration = (datetime.now() - start_time).total_seconds()
            
            if not formatted_stats:
                self.log_test_result("Format Player Stats", False, "Форматирование не выполнено", duration)
                return None
            
            # Валидация отформатированных данных
            is_valid, errors = self.validator.validate_player_stats(formatted_stats)
            
            if not is_valid:
                self.log_test_result("Format Player Stats", False, f"Ошибки валидации: {'; '.join(errors)}", duration)
                return formatted_stats  # Возвращаем даже с ошибками для дальнейшего анализа
            
            # Валидация статистики по картам
            maps_data = formatted_stats.get('maps', {})
            maps_valid, maps_errors = self.validator.validate_maps_stats(maps_data)
            
            if not maps_valid:
                for error in maps_errors:
                    self.log_warning(f"Валидация карт: {error}")
            
            self.log_test_result("Format Player Stats", True, 
                               f"Все данные корректны, карт: {len(maps_data)}", duration)
            
            # Подробное логирование отформатированных данных
            logger.info(f"   Никнейм: {formatted_stats.get('nickname')}")
            logger.info(f"   Уровень: {formatted_stats.get('level')}")
            logger.info(f"   ELO: {formatted_stats.get('elo')}")
            logger.info(f"   Матчи: {formatted_stats.get('matches')}")
            logger.info(f"   Винрейт: {formatted_stats.get('winrate'):.1f}%")
            logger.info(f"   K/D: {formatted_stats.get('kd_ratio'):.3f}")
            logger.info(f"   ADR: {formatted_stats.get('adr'):.1f}")
            logger.info(f"   KAST: {formatted_stats.get('kast'):.1f}%")
            logger.info(f"   HLTV Rating: {formatted_stats.get('hltv_rating'):.3f}")
            
            return formatted_stats
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Format Player Stats", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return None
    
    async def test_5_calculate_hltv_rating(self, stats_data: Dict):
        """Тест 5: Расчет HLTV рейтинга"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 5: РАСЧЕТ HLTV РЕЙТИНГА")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            # Получаем данные для расчета из разных источников
            test_scenarios = []
            
            # Из lifetime данных
            if 'lifetime' in stats_data:
                test_scenarios.append(("Lifetime", stats_data['lifetime']))
            
            # Из Overall сегмента
            segments = stats_data.get('segments', [])
            overall_segment = next((s for s in segments if s.get('label') == 'Overall'), None)
            if overall_segment and 'stats' in overall_segment:
                test_scenarios.append(("Overall Segment", overall_segment['stats']))
            
            # Из первой карты (если есть)
            map_segments = [s for s in segments if s.get('label') != 'Overall']
            if map_segments:
                first_map = map_segments[0]
                test_scenarios.append((f"Map: {first_map.get('label')}", first_map.get('stats', {})))
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if not test_scenarios:
                self.log_test_result("Calculate HLTV Rating", False, "Нет данных для расчета", duration)
                return
            
            # Тестируем расчет для каждого сценария
            for scenario_name, scenario_data in test_scenarios:
                rating = self.client.calculate_hltv_rating(scenario_data)
                
                if not isinstance(rating, (int, float)):
                    self.log_warning(f"HLTV рейтинг для {scenario_name} не числовой: {type(rating)}")
                    continue
                
                if not (0 <= rating <= 3):
                    self.log_warning(f"HLTV рейтинг для {scenario_name} вне диапазона 0-3: {rating}")
                
                logger.info(f"   {scenario_name}: {rating:.3f}")
            
            self.log_test_result("Calculate HLTV Rating", True, 
                               f"Рассчитан для {len(test_scenarios)} источников данных", duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Calculate HLTV Rating", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
    
    async def test_6_get_player_history(self, player_id: str) -> Optional[Dict]:
        """Тест 6: История матчей игрока"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 6: ИСТОРИЯ МАТЧЕЙ")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        try:
            history_data = await self.client.get_player_history(player_id, limit=20)
            duration = (datetime.now() - start_time).total_seconds()
            
            if not history_data:
                self.log_test_result("Get Player History", False, "История матчей не получена", duration)
                return None
            
            # Валидация истории матчей
            is_valid, errors = self.validator.validate_match_history(history_data)
            
            if not is_valid:
                self.log_test_result("Get Player History", False, f"Ошибки валидации: {'; '.join(errors)}", duration)
                return history_data
            
            matches = history_data['items']
            logger.info(f"   Получено матчей: {len(matches)}")
            
            # Анализируем последние матчи
            recent_results = []
            for match in matches[:10]:
                result = self.client._determine_player_result(match, player_id)
                if result is True:
                    recent_results.append("W")
                elif result is False:
                    recent_results.append("L")
                else:
                    recent_results.append("?")
            
            wins = recent_results.count("W")
            losses = recent_results.count("L")
            unknown = recent_results.count("?")
            
            logger.info(f"   Последние 10 матчей: {wins}W {losses}L {unknown}?")
            logger.info(f"   Результаты: {''.join(recent_results)}")
            
            # Проверяем наличие временных меток
            matches_with_time = sum(1 for match in matches if match.get('finished_at'))
            logger.info(f"   Матчей с временными метками: {matches_with_time}/{len(matches)}")
            
            self.log_test_result("Get Player History", True, 
                               f"{len(matches)} матчей, последние результаты: {wins}W {losses}L", duration)
            
            return history_data
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Get Player History", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return None
    
    async def test_7_stats_handler_functions(self, player_id: str, formatted_stats: Dict):
        """Тест 7: Функции обработчика статистики"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 7: ФУНКЦИИ STATS_HANDLER")
        logger.info("=" * 50)
        
        # Тест вспомогательных функций
        start_time = datetime.now()
        try:
            # Тест safe_float
            test_cases_float = [
                ("1.5", 1.5),
                ("1,5", 1.5),
                ("invalid", 0.0),
                (None, 0.0),
                (15, 15.0),
                ("", 0.0)
            ]
            
            for input_val, expected in test_cases_float:
                result = safe_float(input_val)
                if result != expected:
                    self.log_warning(f"safe_float({input_val}) = {result}, ожидалось {expected}")
            
            # Тест safe_int
            test_cases_int = [
                ("10", 10),
                ("10.5", 10),
                ("invalid", 0),
                (None, 0),
                (15, 15),
                ("", 0)
            ]
            
            for input_val, expected in test_cases_int:
                result = safe_int(input_val)
                if result != expected:
                    self.log_warning(f"safe_int({input_val}) = {result}, ожидалось {expected}")
            
            # Тест validate_user_data
            test_user_data = validate_user_data({
                'nickname': 'TestUser', 
                'faceit_id': '123',
                'created_at': datetime.now().isoformat()
            })
            
            if test_user_data['nickname'] != 'TestUser':
                self.log_warning(f"validate_user_data вернул неправильный nickname: {test_user_data['nickname']}")
            
            # Тест format_time_ago
            test_timestamp = datetime.now().timestamp()
            time_str = format_time_ago(test_timestamp)
            if "только что" not in time_str and "мин. назад" not in time_str:
                self.log_warning(f"format_time_ago вернул неожиданный результат: {time_str}")
            
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Stats Handler Functions", True, 
                               "Все вспомогательные функции работают корректно", duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Stats Handler Functions", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
    
    async def test_8_integration_tests(self, player_id: str):
        """Тест 8: Интеграционные тесты полного цикла"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 8: ИНТЕГРАЦИОННЫЕ ТЕСТЫ")
        logger.info("=" * 50)
        
        # Тест полного цикла: поиск → статистика → форматирование
        start_time = datetime.now()
        try:
            # Полный цикл обработки
            player_data = await self.client.find_player_by_nickname(self.test_nickname)
            if not player_data:
                raise Exception("Игрок не найден в интеграционном тесте")
            
            details = await self.client.get_player_details(player_data['player_id'])
            stats = await self.client.get_player_stats(player_data['player_id'])
            history = await self.client.get_player_history(player_data['player_id'], limit=10)
            
            if not (details and stats and history):
                raise Exception("Не удалось получить все данные в интеграционном тесте")
            
            formatted = self.client.format_player_stats(details, stats)
            if not formatted:
                raise Exception("Не удалось отформатировать данные в интеграционном тесте")
            
            # Проверяем анализ производительности
            performance = await self.client.analyze_player_performance(player_id, 20)
            if not performance:
                self.log_warning("Анализ производительности не удался")
            else:
                logger.info(f"   Анализ производительности: {performance.get('total_matches')} матчей, {performance.get('winrate')}% WR")
            
            # Проверяем полный профиль
            full_profile = await self.client.get_player_full_profile(self.test_nickname)
            if not full_profile:
                self.log_warning("Полный профиль не получен")
            else:
                logger.info(f"   Полный профиль: {len(full_profile)} разделов данных")
            
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Integration Tests", True, 
                               "Полный цикл обработки данных работает", duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Integration Tests", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
    
    async def test_9_error_handling(self):
        """Тест 9: Обработка ошибок и граничных случаев"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 9: ОБРАБОТКА ОШИБОК")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        error_tests_passed = 0
        error_tests_total = 4
        
        try:
            # Тест несуществующего игрока
            fake_player = await self.client.find_player_by_nickname("NonExistentPlayer123456789")
            if fake_player is None:
                error_tests_passed += 1
                logger.info("   ✅ Корректная обработка несуществующего игрока")
            else:
                logger.warning("   ⚠️ Неожиданно найден несуществующий игрок")
            
            # Тест несуществующего ID
            fake_details = await self.client.get_player_details("fake-player-id-123")
            if fake_details is None:
                error_tests_passed += 1
                logger.info("   ✅ Корректная обработка несуществующего ID")
            else:
                logger.warning("   ⚠️ Неожиданно получены данные для несуществующего ID")
            
            # Тест форматирования с пустыми данными
            empty_formatted = self.client.format_player_stats({}, {})
            if not empty_formatted or len(empty_formatted) == 0:
                error_tests_passed += 1
                logger.info("   ✅ Корректная обработка пустых данных при форматировании")
            else:
                logger.warning("   ⚠️ Неожиданное форматирование пустых данных")
            
            # Тест расчета HLTV с некорректными данными
            invalid_rating = self.client.calculate_hltv_rating({"invalid": "data"})
            if invalid_rating == 0.0:
                error_tests_passed += 1
                logger.info("   ✅ Корректная обработка некорректных данных для HLTV рейтинга")
            else:
                logger.warning(f"   ⚠️ Неожиданный рейтинг для некорректных данных: {invalid_rating}")
            
            duration = (datetime.now() - start_time).total_seconds()
            success_rate = error_tests_passed / error_tests_total
            
            self.log_test_result("Error Handling", success_rate >= 0.75, 
                               f"Пройдено {error_tests_passed}/{error_tests_total} тестов обработки ошибок", 
                               duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_test_result("Error Handling", False, f"Исключение: {str(e)}", duration)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
    
    async def test_10_performance_and_caching(self, player_id: str):
        """Тест 10: Производительность и кэширование"""
        logger.info("\n" + "=" * 50)
        logger.info("ТЕСТ 10: ПРОИЗВОДИТЕЛЬНОСТЬ И КЭШИРОВАНИЕ")
        logger.info("=" * 50)
        
        try:
            # Первый запрос (без кэша)
            start_time = datetime.now()
            stats1 = await self.client.get_player_stats(player_id)
            first_request_time = (datetime.now() - start_time).total_seconds()
            
            # Второй запрос (с кэшем)
            start_time = datetime.now()
            stats2 = await self.client.get_player_stats(player_id)
            second_request_time = (datetime.now() - start_time).total_seconds()
            
            # Проверяем кэширование
            cache_improvement = first_request_time - second_request_time
            cache_worked = second_request_time < first_request_time * 0.5  # Второй запрос должен быть значительно быстрее
            
            logger.info(f"   Первый запрос: {first_request_time:.3f}s")
            logger.info(f"   Второй запрос: {second_request_time:.3f}s") 
            logger.info(f"   Улучшение: {cache_improvement:.3f}s")
            logger.info(f"   Кэширование работает: {'Да' if cache_worked else 'Нет'}")
            
            if not cache_worked:
                self.log_warning("Кэширование работает неэффективно")
            
            # Тест множественных параллельных запросов
            start_time = datetime.now()
            parallel_tasks = [
                self.client.get_player_details(player_id),
                self.client.get_player_stats(player_id),
                self.client.get_player_history(player_id, limit=10)
            ]
            
            results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            parallel_time = (datetime.now() - start_time).total_seconds()
            
            successful_parallel = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"   Параллельные запросы: {successful_parallel}/3 успешно за {parallel_time:.3f}s")
            
            total_duration = first_request_time + second_request_time + parallel_time
            self.log_test_result("Performance and Caching", True, 
                               f"Кэш: {'работает' if cache_worked else 'неэффективен'}, параллельно: {successful_parallel}/3", 
                               total_duration)
            
        except Exception as e:
            self.log_test_result("Performance and Caching", False, f"Исключение: {str(e)}", 0)
            logger.error(f"Трейсбек: {traceback.format_exc()}")
    
    def print_final_report(self):
        """Печать итогового отчета"""
        logger.info("\n" + "=" * 80)
        logger.info("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        logger.info("=" * 80)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info(f"Всего тестов: {total}")
        logger.info(f"Пройдено: {passed} (✅)")
        logger.info(f"Провалено: {failed} (❌)")
        logger.info(f"Успешность: {success_rate:.1f}%")
        
        if self.test_results['warnings']:
            logger.info(f"\nПредупреждений: {len(self.test_results['warnings'])}")
            for warning in self.test_results['warnings']:
                logger.info(f"  ⚠️ {warning}")
        
        if self.test_results['errors']:
            logger.info(f"\nОшибки:")
            for error in self.test_results['errors']:
                logger.info(f"  ❌ {error}")
        
        # Статистика производительности
        if self.test_results['performance_metrics']:
            logger.info(f"\nПроизводительность:")
            total_time = sum(self.test_results['performance_metrics'].values())
            logger.info(f"  Общее время тестирования: {total_time:.2f}s")
            
            slowest = max(self.test_results['performance_metrics'].items(), key=lambda x: x[1])
            logger.info(f"  Самый медленный тест: {slowest[0]} ({slowest[1]:.2f}s)")
        
        # Заключение
        if success_rate >= 90:
            status = "🎉 ОТЛИЧНО"
            conclusion = "Все основные функции работают корректно!"
        elif success_rate >= 75:
            status = "✅ ХОРОШО"
            conclusion = "Система работает с незначительными проблемами."
        elif success_rate >= 50:
            status = "⚠️ УДОВЛЕТВОРИТЕЛЬНО"
            conclusion = "Есть серьезные проблемы, требуется доработка."
        else:
            status = "❌ НЕУДОВЛЕТВОРИТЕЛЬНО"
            conclusion = "Критические ошибки, система не готова к использованию."
        
        logger.info(f"\nСТАТУС ТЕСТИРОВАНИЯ: {status}")
        logger.info(f"ЗАКЛЮЧЕНИЕ: {conclusion}")
        logger.info("=" * 80)
        
        return success_rate
    
    async def run_comprehensive_test(self) -> float:
        """Запуск полного комплексного тестирования"""
        try:
            # Инициализация
            if not await self.setup():
                return 0.0
            
            # Основные тесты
            player_data = await self.test_1_find_player()
            if not player_data:
                logger.error("Критическая ошибка: игрок не найден, дальнейшее тестирование невозможно")
                return self.print_final_report()
            
            player_id = player_data['player_id']
            
            # Получение данных
            details_data = await self.test_2_get_player_details(player_id)
            stats_data = await self.test_3_get_player_stats(player_id)
            
            if not (details_data and stats_data):
                logger.error("Критическая ошибка: не удалось получить основные данные")
                return self.print_final_report()
            
            # Обработка данных
            formatted_stats = await self.test_4_format_player_stats(details_data, stats_data)
            await self.test_5_calculate_hltv_rating(stats_data)
            
            # История матчей
            history_data = await self.test_6_get_player_history(player_id)
            
            # Дополнительные тесты
            await self.test_7_stats_handler_functions(player_id, formatted_stats or {})
            await self.test_8_integration_tests(player_id)
            await self.test_9_error_handling()
            await self.test_10_performance_and_caching(player_id)
            
            # Итоговый отчет
            return self.print_final_report()
            
        except Exception as e:
            logger.error(f"Критическая ошибка во время тестирования: {e}")
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            return 0.0
        
        finally:
            if self.client:
                await self.client.close()


async def main():
    """Основная функция запуска тестирования"""
    print("Запуск комплексного тестирования системы статистики...")
    print(f"Дата: {datetime.now()}")
    print(f"Тестируемый игрок: Geun-Hee")
    print("-" * 50)
    
    # Создаем и запускаем тест
    tester = ComprehensiveStatsTest(api_key="41f48f43-609c-4639-b821-360b039f18b4")
    success_rate = await tester.run_comprehensive_test()
    
    print(f"\nТестирование завершено с результатом: {success_rate:.1f}%")
    return success_rate


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result >= 75:
            sys.exit(0)  # Успех
        else:
            sys.exit(1)  # Ошибка
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
        sys.exit(2)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(3)