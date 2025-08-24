import httpx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import asyncio
import json
import logging
from config import settings
from storage import storage
from bot.services.cache_service import CacheService


class FaceitAPIClient:
    """Улучшенный клиент для работы с FACEIT Data API"""
    
    BASE_URL = "https://open.faceit.com/data/v4"
    
    def __init__(self):
        self.api_key = settings.faceit_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.5  # Оптимизированная задержка между запросами
        self.semaphore = asyncio.Semaphore(settings.concurrent_requests)  # Семафор для concurrent запросов
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Получить HTTP сессию"""
        if self.session is None or self.session.is_closed:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0
            )
        return self.session
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                          cache_ttl: int = 300, retry_count: int = 3) -> Optional[Dict]:
        """Выполнить HTTP запрос к API с улучшенной обработкой ошибок и concurrent контролем"""
        cache_key = f"faceit_{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
        
        # Проверяем кэш с TTL
        cached_data = await storage.get_cached_data(cache_key, max_age_minutes=cache_ttl//60)
        if cached_data:
            self.logger.debug(f"Cache hit for {endpoint}")
            return cached_data
        
        # Используем семафор для контроля concurrent запросов
        async with self.semaphore:
            for attempt in range(retry_count):
                try:
                    # Применяем rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                    
                    session = await self._get_session()
                    response = await session.get(f"{self.BASE_URL}{endpoint}", params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        await storage.set_cached_data(cache_key, data)
                        self.logger.debug(f"API request successful: {endpoint}")
                        return data
                        
                    elif response.status_code == 429:  # Rate limit
                        wait_time = min(60 * (2 ** attempt), 300)  # Exponential backoff, max 5 min
                        self.logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    elif response.status_code == 404:
                        self.logger.warning(f"Resource not found: {endpoint}")
                        return None
                        
                    elif response.status_code == 401:
                        self.logger.error("Invalid API key")
                        return None
                        
                    elif response.status_code in [500, 502, 503, 504]:  # Server errors - retry with backoff
                        wait_time = min(2 ** attempt, 8)  # Max 8 seconds delay
                        self.logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s (attempt {attempt + 1}/{retry_count})")
                        if attempt == retry_count - 1:
                            self.logger.error(f"Final attempt failed for {endpoint}: {response.status_code} - {response.text}")
                            return None
                        await asyncio.sleep(wait_time)
                        
                    else:
                        self.logger.error(f"FACEIT API Error: {response.status_code} - {response.text}")
                        if attempt == retry_count - 1:
                            return None
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
                except httpx.TimeoutException:
                    self.logger.warning(f"Timeout for {endpoint}, attempt {attempt + 1}")
                    if attempt == retry_count - 1:
                        return None
                    await asyncio.sleep(2 ** attempt)
                
                except Exception as e:
                    self.logger.error(f"HTTP Request Error: {e}")
                    if attempt == retry_count - 1:
                        return None
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def find_player_by_nickname(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Найти игрока по никнейму"""
        # Кэшируем поиск игроков на 1 час (3600 секунд)
        data = await self._make_request("/search/players", params={"nickname": nickname, "game": "cs2"}, cache_ttl=3600)
        if data and 'items' in data and len(data['items']) > 0:
            # Ищем точное совпадение или первый результат
            exact_match = next((player for player in data['items'] if player['nickname'].lower() == nickname.lower()), None)
            return exact_match if exact_match else data['items'][0]
        return None
    
    async def get_player_details(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию об игроке"""
        # Кэшируем детали игрока на 6 часов (21600 секунд)
        return await self._make_request(f"/players/{player_id}", cache_ttl=21600)
    
    async def get_player_stats(self, player_id: str, game: str = "cs2") -> Optional[Dict[str, Any]]:
        """Получить статистику игрока"""
        # Кэшируем статистику на 30 минут (1800 секунд)
        return await self._make_request(f"/players/{player_id}/stats/{game}", cache_ttl=1800)
    
    async def get_player_history(self, player_id: str, game: str = "cs2", 
                               limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Получить историю матчей игрока (исправлен метод)"""
        params = {
            "game": game,
            "limit": min(limit, 100),  # API limit
            "offset": offset
        }
        # Кэшируем историю матчей на 10 минут (600 секунд)
        return await self._make_request(f"/players/{player_id}/history", params=params, cache_ttl=600)
    
    # Алиас для обратной совместимости
    async def get_player_matches(self, player_id: str, game: str = "cs2", 
                               limit: int = 20, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Алиас для get_player_history для обратной совместимости"""
        return await self.get_player_history(player_id, game, limit, offset)
    
    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Получить детали матча"""
        return await self._make_request(f"/matches/{match_id}")
    
    async def get_match_stats(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Получить статистику матча с кэшированием"""
        # Кэшируем статистику матчей на 10 минут (600 секунд)
        return await self._make_request(f"/matches/{match_id}/stats", cache_ttl=600)
    
    async def get_player_stats_from_match(self, match_id: str, faceit_id: str) -> Optional[Dict[str, Any]]:
        """Получить статистику конкретного игрока из матча"""
        try:
            # Получаем полную статистику матча
            match_stats = await self.get_match_stats(match_id)
            if not match_stats:
                self.logger.warning(f"No match stats found for match {match_id}")
                return None
            
            # Ищем игрока в данных матча
            rounds = match_stats.get('rounds', [])
            if not rounds:
                self.logger.warning(f"No rounds data in match {match_id}")
                return None
            
            # Проходим по командам и игрокам в первом раунде
            for round_data in rounds:
                teams = round_data.get('teams', [])
                for team in teams:
                    players = team.get('players', [])
                    for player in players:
                        if player.get('player_id') == faceit_id:
                            # Нашли нашего игрока
                            player_stats = player.get('player_stats', {})
                            if player_stats:
                                # Безопасное извлечение статистики
                                def safe_int(value, default=0):
                                    try:
                                        return int(float(str(value)))
                                    except (ValueError, TypeError):
                                        return default
                                
                                def safe_float(value, default=0.0):
                                    try:
                                        return float(str(value))
                                    except (ValueError, TypeError):
                                        return default
                                
                                extracted_stats = {
                                    'kills': safe_int(player_stats.get('Kills', 0)),
                                    'deaths': safe_int(player_stats.get('Deaths', 0)),
                                    'assists': safe_int(player_stats.get('Assists', 0)),
                                    'adr': safe_float(player_stats.get('ADR', 0.0)),
                                    'kast': safe_float(player_stats.get('KAST %', 0.0)),
                                    'headshots': safe_float(player_stats.get('Headshots %', 0.0)),
                                    'first_kills': safe_int(player_stats.get('First Kills', 0)),
                                    'first_deaths': safe_int(player_stats.get('First Deaths', 0)),
                                    'flash_assists': safe_int(player_stats.get('Flash Assists', 0)),
                                    'rounds': safe_int(player_stats.get('Rounds', 16))  # Обычно 16+ раундов
                                }
                                
                                self.logger.debug(f"Extracted stats for player {faceit_id} in match {match_id}: {extracted_stats}")
                                return extracted_stats
                            
            self.logger.warning(f"Player {faceit_id} not found in match {match_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting player stats from match {match_id}: {e}")
            return None
    
    def calculate_hltv_rating(self, stats: Dict[str, Any]) -> float:
        """Рассчитать HLTV 2.1 рейтинг с улучшенной обработкой данных"""
        try:
            # Получаем статистики, конвертируя строки в числа
            def safe_float(value, default=0.0):
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value.replace(',', '.').replace('%', ''))
                    except:
                        return default
                return default
            
            def safe_int(value, default=0):
                if isinstance(value, int):
                    return value
                if isinstance(value, str):
                    try:
                        return int(float(value.replace(',', '.')))
                    except:
                        return default
                return default
            
            # Базовые статистики из разных возможных полей
            rounds_played = safe_int(stats.get('Rounds', stats.get('rounds', 1)), 1)
            kills = safe_int(stats.get('Kills', stats.get('kills', 0)))
            deaths = safe_int(stats.get('Deaths', stats.get('deaths', 1)), 1)
            assists = safe_int(stats.get('Assists', stats.get('assists', 0)))
            
            # Критически важные метрики для HLTV 2.1
            adr = safe_float(stats.get('ADR', stats.get('adr', 0)))
            kast = safe_float(stats.get('KAST %', stats.get('kast', 0)))
            
            # Дополнительные метрики для более точного расчета
            # Поддержка различных названий полей в API
            first_kills = safe_int(stats.get('First Kills', stats.get('Total Entry Wins', stats.get('first_kills', 0))))
            first_deaths = safe_int(stats.get('First Deaths', stats.get('first_deaths', 0)))
            # Если нет First Deaths, рассчитываем из Total Entry Count - Total Entry Wins
            if first_deaths == 0 and 'Total Entry Count' in stats and 'Total Entry Wins' in stats:
                first_deaths = safe_int(stats.get('Total Entry Count', 0)) - safe_int(stats.get('Total Entry Wins', 0))
            
            # Flash Assists может быть в разных полях
            flash_assists = safe_int(stats.get('Flash Assists', stats.get('Total Flash Successes', stats.get('flash_assists', 0))))
            utility_damage = safe_int(stats.get('Utility Damage', stats.get('Total Utility Damage', stats.get('utility_damage', 0))))
            
            # Логирование для отладки
            if hasattr(self, 'logger'):
                self.logger.debug(f"HLTV Rating calculation - Fields found:")
                self.logger.debug(f"  First Kills: {first_kills} (from: {'First Kills' if 'First Kills' in stats else 'Total Entry Wins' if 'Total Entry Wins' in stats else 'fallback'})")
                self.logger.debug(f"  First Deaths: {first_deaths} (from: {'First Deaths' if 'First Deaths' in stats else 'calculated' if 'Total Entry Count' in stats else 'fallback'})")
                self.logger.debug(f"  Flash Assists: {flash_assists} (from: {'Flash Assists' if 'Flash Assists' in stats else 'Total Flash Successes' if 'Total Flash Successes' in stats else 'fallback'})")
                self.logger.debug(f"  Available keys: {list(stats.keys())[:10]}...")  # Показать первые 10 ключей
            
            # Если нет критических данных, возвращаем 0
            if rounds_played == 0:
                return 0.0
            
            # Расчет компонентов HLTV 2.1
            kpr = kills / rounds_played
            dpr = deaths / rounds_played
            apr = assists / rounds_played
            
            # Impact rating - учитывает не только киллы и ассисты, но и first kills
            fkpr = first_kills / rounds_played if rounds_played > 0 else 0
            fdpr = first_deaths / rounds_played if rounds_played > 0 else 0
            
            # Расширенная impact формула
            impact = 2.13 * kpr + 0.42 * apr - 0.41 + 0.1 * fkpr - 0.05 * fdpr
            
            # HLTV 2.1 формула с учетом всех доступных метрик
            base_rating = (0.0073 * kast + 0.3591 * kpr - 0.5329 * dpr + 
                          0.2372 * impact + 0.0032 * adr + 0.1587)
            
            # Дополнительные бонусы за утилити
            utility_bonus = 0.0
            if flash_assists > 0:
                utility_bonus += (flash_assists / rounds_played) * 0.01
            if utility_damage > 0:
                utility_bonus += (utility_damage / rounds_played) * 0.0001
            
            rating = base_rating + utility_bonus
            
            return max(0.0, round(rating, 3))
            
        except Exception as e:
            self.logger.error(f"Error calculating HLTV rating: {e}")
            return 0.0
    
    def format_player_stats(self, player_data: Dict, stats_data: Dict) -> Dict[str, Any]:
        """ИСПРАВЛЕННОЕ форматирование с правильным источником данных о матчах"""
        if not stats_data:
            return {}
        
        # Функции для безопасного извлечения данных
        def safe_float(value, default=0.0):
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.replace(',', '.').replace('%', ''))
                except:
                    return default
            return default
        
        def safe_int(value, default=0):
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    return int(float(value.replace(',', '.')))
                except:
                    return default
            return default
        
        # Детальное логирование источников данных
        self.logger.info("=== FACEIT DATA SOURCES DEBUG ===")
        if 'lifetime' in stats_data:
            lifetime = stats_data['lifetime']
            self.logger.info(f"Lifetime Matches: {lifetime.get('Matches', 'N/A')}")
            self.logger.info(f"Lifetime Total Matches: {lifetime.get('Total Matches', 'N/A')}")
            self.logger.info(f"Lifetime K/D Ratio: {lifetime.get('K/D Ratio', 'N/A')}")
            self.logger.info(f"Lifetime ADR: {lifetime.get('ADR', 'N/A')}")
            self.logger.info(f"Lifetime KAST %: {lifetime.get('KAST %', 'N/A')}")
        
        if 'segments' in stats_data:
            segments = stats_data['segments']
            map_segments = [s for s in segments if s.get('type') == 'Map']
            self.logger.info(f"Number of map segments: {len(map_segments)}")
            total_segment_matches = sum(safe_int(s.get('stats', {}).get('Matches', 0)) for s in map_segments)
            total_segment_total_matches = sum(safe_int(s.get('stats', {}).get('Total Matches', 0)) for s in map_segments)
            self.logger.info(f"Sum of Matches from segments: {total_segment_matches}")
            self.logger.info(f"Sum of Total Matches from segments: {total_segment_total_matches}")
        
        # Получаем segments и lifetime данные
        segments = stats_data.get('segments', [])
        lifetime_stats = stats_data.get('lifetime', {})
        
        # Фильтруем map segments
        map_stats = []
        if segments:
            map_stats = [s for s in segments if s.get('type') == 'Map' and 'stats' in s]
        
        # ИСПРАВЛЕНО: Правильный подсчет матчей - суммируем поле 'Matches' из segments
        main_stats = lifetime_stats.copy() if lifetime_stats else {}
        
        # Считаем правильное количество матчей из segments
        correct_matches = 0
        correct_wins = 0
        
        if map_stats:
            # Суммируем поле 'Matches' (не 'Total Matches'!) из каждого сегмента
            for map_stat in map_stats:
                map_data = map_stat.get('stats', {})
                # Используем 'Matches', а не 'Total Matches' для правильного подсчета
                correct_matches += safe_int(map_data.get('Matches', 0))
                correct_wins += safe_int(map_data.get('Wins', 0))
            
            self.logger.info(f"Calculated correct matches from segments: {correct_matches} (wins: {correct_wins})")
            main_stats['Matches'] = correct_matches
            main_stats['Wins'] = correct_wins
            main_stats['Win Rate %'] = round((correct_wins / correct_matches) * 100, 1) if correct_matches > 0 else 0
        else:
            # Fallback на lifetime если нет segments
            if 'Total Matches' in lifetime_stats:
                correct_matches = safe_int(lifetime_stats.get('Total Matches', 0))
                main_stats['Matches'] = correct_matches
                self.logger.info(f"Using lifetime Total Matches as fallback: {correct_matches}")
            elif 'Matches' in lifetime_stats:
                correct_matches = safe_int(lifetime_stats.get('Matches', 0))
                main_stats['Matches'] = correct_matches
                self.logger.info(f"Using lifetime Matches as fallback: {correct_matches}")
        
        hltv_stats = {}
        
        # ИСПРАВЛЕННАЯ ЛОГИКА: Приоритет точным API значениям из lifetime
        hltv_stats = main_stats.copy()  # Начинаем с lifetime данных
        
        # Используем точные значения ADR и KAST из lifetime если доступны
        if 'ADR' in lifetime_stats:
            hltv_stats['ADR'] = safe_float(lifetime_stats['ADR'])
            self.logger.info(f"Using precise ADR from lifetime: {hltv_stats['ADR']}")
        elif 'Average Damage Per Round' in lifetime_stats:
            hltv_stats['ADR'] = safe_float(lifetime_stats['Average Damage Per Round'])
            
        if 'KAST %' in lifetime_stats:
            kast_value = safe_float(lifetime_stats['KAST %'])
            # Валидация KAST - не может быть больше 100%
            if 0 <= kast_value <= 100:
                hltv_stats['KAST %'] = kast_value
                self.logger.info(f"Using precise KAST from lifetime: {hltv_stats['KAST %']}")
            else:
                self.logger.warning(f"Invalid KAST value {kast_value}%, using fallback calculation")
                hltv_stats['KAST %'] = 0.0  # Будет пересчитан ниже
        elif 'Average KAST' in lifetime_stats:
            kast_value = safe_float(lifetime_stats['Average KAST'])
            if 0 <= kast_value <= 100:
                hltv_stats['KAST %'] = kast_value
            else:
                hltv_stats['KAST %'] = 0.0
            
        # Дополняем данными из segments только если отсутствуют в lifetime
        if map_stats:
            total_kills = 0
            total_deaths = 0
            total_assists = 0
            total_rounds = 0
            total_damage = 0
            total_first_kills = 0
            total_first_deaths = 0
            total_flash_assists = 0
            total_utility_damage = 0
            
            for map_stat in map_stats:
                map_data = map_stat.get('stats', {})
                total_kills += safe_int(map_data.get('Kills', 0))
                total_deaths += safe_int(map_data.get('Deaths', 0))
                total_assists += safe_int(map_data.get('Assists', 0))
                total_rounds += safe_int(map_data.get('Rounds', 0))
                total_damage += safe_int(map_data.get('Total Damage', 0))
                total_first_kills += safe_int(map_data.get('Total Entry Wins', 0))
                total_first_deaths += safe_int(map_data.get('Total Entry Count', 0)) - safe_int(map_data.get('Total Entry Wins', 0))
                total_flash_assists += safe_int(map_data.get('Total Flash Successes', 0))
                total_utility_damage += safe_int(map_data.get('Total Utility Damage', 0))
            
            # Дополняем недостающие данные из агрегации segments
            if 'ADR' not in hltv_stats or hltv_stats['ADR'] == 0:
                if total_rounds > 0:
                    hltv_stats['ADR'] = round(total_damage / total_rounds, 1)
                    self.logger.info(f"Calculated ADR from segments: {hltv_stats['ADR']}")
            
            # Дополняем статистику для HLTV расчетов
            if total_rounds > 0:
                # Рассчитываем правильный K/D Ratio из реальных данных
                real_kd_ratio = round(total_kills / max(total_deaths, 1), 3)
                
                hltv_stats.update({
                    'Kills': total_kills,
                    'Deaths': total_deaths,
                    'Assists': total_assists,
                    'Rounds': total_rounds,
                    'K/D Ratio': real_kd_ratio,  # Используем рассчитанный K/D
                    'First Kills': total_first_kills,
                    'First Deaths': total_first_deaths,
                    'Flash Assists': total_flash_assists,
                    'Utility Damage': total_utility_damage
                })
                
                # Обновляем main_stats правильным K/D
                main_stats['K/D Ratio'] = real_kd_ratio
                self.logger.info(f"Calculated correct K/D Ratio: {real_kd_ratio} (from {total_kills}/{total_deaths})")
                
                # Пересчитываем KAST если отсутствует или некорректен
                if 'KAST %' not in hltv_stats or hltv_stats['KAST %'] == 0.0:
                    # Более реалистичная формула KAST на основе доступных данных
                    # Приблизительно: (Kills + Assists + 0.5 * не смертей) / Rounds * 100
                    survived_estimate = max(0, total_rounds - total_deaths) * 0.7  # Консервативная оценка выживания
                    estimated_kast = ((total_kills + total_assists + survived_estimate) / total_rounds) * 100
                    estimated_kast = round(min(estimated_kast, 85.0), 1)  # Реалистичный максимум 85%
                    hltv_stats['KAST %'] = estimated_kast
                    self.logger.info(f"Calculated realistic KAST from segments: {estimated_kast}%")
            
        if not main_stats:
            self.logger.warning("No main stats found in player data")
            return {}
        
        # Извлечение данных игрока
        cs2_data = player_data.get('games', {}).get('cs2', {})
        
        # Основная статистика
        formatted = {
            'player_id': player_data.get('player_id', ''),
            'nickname': player_data.get('nickname', 'Unknown'),
            'country': player_data.get('country', ''),
            'level': safe_int(cs2_data.get('skill_level', 0)),
            'elo': safe_int(cs2_data.get('faceit_elo', 0)),
            'region': cs2_data.get('region', ''),
            'verified': player_data.get('verified', False),
            
            # Матчи и результаты (из lifetime, если доступно)
            'matches': safe_int(main_stats.get('Matches', 0)),
            'wins': safe_int(main_stats.get('Wins', 0)),
            'winrate': round(safe_float(main_stats.get('Win Rate %', 0)), 1),
            'recent_results': main_stats.get('Recent Results', []),
            'longest_win_streak': safe_int(main_stats.get('Longest Win Streak', 0)),
            
            # Kill/Death статистики
            'kills': safe_int(main_stats.get('Kills', 0)),
            'deaths': safe_int(main_stats.get('Deaths', 0)),
            'assists': safe_int(main_stats.get('Assists', 0)),
            'kd_ratio': round(safe_float(main_stats.get('K/D Ratio', 0)), 3),
            'average_kd': round(safe_float(main_stats.get('Average K/D Ratio', 0)), 3),
            
            # Headshots
            'headshots_total': round(safe_float(main_stats.get('Total Headshots %', 0)), 1),
            'headshots_avg': round(safe_float(main_stats.get('Average Headshots %', 0)), 1),
            
            # K/R Ratio (приоритет из segments)
            'kpr': round(safe_float(main_stats.get('K/R Ratio', 0)), 3),
            'average_kpr': round(safe_float(main_stats.get('Average K/R Ratio', 0)), 3)
        }
        
        # Критические метрики для HLTV 2.1 (из segments/Overall с fallback)
        formatted.update({
            'adr': round(safe_float(hltv_stats.get('ADR', 0)), 1),
            'kast': round(safe_float(hltv_stats.get('KAST %', 0)), 1),
            'hltv_rating': self.calculate_hltv_rating(hltv_stats),
            
            # Дополнительные метрики для HLTV 2.1 - поддержка разных названий полей
            'first_kills': safe_int(hltv_stats.get('First Kills', hltv_stats.get('Total Entry Wins', 0))),
            'first_deaths': safe_int(hltv_stats.get('First Deaths', 
                max(0, safe_int(hltv_stats.get('Total Entry Count', 0)) - safe_int(hltv_stats.get('Total Entry Wins', 0))))),
            'flash_assists': safe_int(hltv_stats.get('Flash Assists', hltv_stats.get('Total Flash Successes', 0))),
            'utility_damage': safe_int(hltv_stats.get('Utility Damage', 0)),
            
            # Метрики энтри - используем правильные поля
            'total_entry_attempts': safe_int(hltv_stats.get('Total Entry Count', 
                safe_int(hltv_stats.get('First Kills', hltv_stats.get('Total Entry Wins', 0))) + 
                safe_int(hltv_stats.get('First Deaths', 0)))),
            'entry_success_percentage': round((safe_float(hltv_stats.get('First Kills', hltv_stats.get('Total Entry Wins', 0))) / 
                max(safe_int(hltv_stats.get('Total Entry Count', 
                    safe_int(hltv_stats.get('First Kills', hltv_stats.get('Total Entry Wins', 0))) + 
                    safe_int(hltv_stats.get('First Deaths', 0)))), 1)) * 100, 1),
            
            # Средние показатели за матч (новое требование)
            'avg_kills_per_match': round(safe_float(hltv_stats.get('Kills', 0)) / max(formatted['matches'], 1), 1),
            'avg_deaths_per_match': round(safe_float(hltv_stats.get('Deaths', 0)) / max(formatted['matches'], 1), 1),
            'avg_assists_per_match': round(safe_float(hltv_stats.get('Assists', 0)) / max(formatted['matches'], 1), 1),
            'avg_first_kills_per_match': round(safe_float(hltv_stats.get('First Kills', hltv_stats.get('Total Entry Wins', 0))) / max(formatted['matches'], 1), 1),
            'avg_first_deaths_per_match': round(max(0, safe_int(hltv_stats.get('Total Entry Count', 0)) - safe_int(hltv_stats.get('Total Entry Wins', 0))) / max(formatted['matches'], 1), 1),
            'avg_flash_assists_per_match': round(safe_float(hltv_stats.get('Flash Assists', hltv_stats.get('Total Flash Successes', 0))) / max(formatted['matches'], 1), 1),
            'avg_utility_damage_per_match': round(safe_float(hltv_stats.get('Utility Damage', 0)) / max(formatted['matches'], 1), 1),
            # Эстимация молотовов и гранат (примерно 60% гранаты, 40% молотовы от общего утилити урона)
            'avg_molotov_damage_per_match': round(safe_float(hltv_stats.get('Utility Damage', 0)) * 0.4 / max(formatted['matches'], 1), 1),
            'avg_grenade_damage_per_match': round(safe_float(hltv_stats.get('Utility Damage', 0)) * 0.6 / max(formatted['matches'], 1), 1),
            
            # Дополнительные утилити метрики если доступны
            'grenade_damage': safe_int(hltv_stats.get('Grenade Damage', 0)) or round(safe_float(hltv_stats.get('Utility Damage', 0)) * 0.6),
            'molotov_damage': safe_int(hltv_stats.get('Molotov Damage', 0)) or round(safe_float(hltv_stats.get('Utility Damage', 0)) * 0.4),
            'enemies_flashed': safe_int(hltv_stats.get('Enemies Flashed', 0)),
            'teammates_flashed': safe_int(hltv_stats.get('Teammates Flashed', 0))
        })
        
        # Агрегация мульти-киллов и MVP из всех карт
        total_triple_kills = 0
        total_quadro_kills = 0
        total_penta_kills = 0
        total_mvps = 0
        total_rounds = 0
        
        for map_stat in map_stats:
            map_data = map_stat.get('stats', {})
            total_triple_kills += safe_int(map_data.get('Triple Kills', 0))
            total_quadro_kills += safe_int(map_data.get('Quadro Kills', 0))
            total_penta_kills += safe_int(map_data.get('Penta Kills', 0))
            total_mvps += safe_int(map_data.get('MVPs', 0))
            total_rounds += safe_int(map_data.get('Rounds', 0))
        
        # Рассчитываем средний процент хедшотов из segments (точнее чем lifetime)
        avg_headshot_percentage = 0.0
        maps_with_headshot_data = 0
        total_headshot_percentage = 0.0
        
        for map_stat in map_stats:
            map_data = map_stat.get('stats', {})
            if map_data and 'Average Headshots %' in map_data:
                headshot_pct = safe_float(map_data.get('Average Headshots %', 0))
                if headshot_pct > 0:  # Только карты с данными
                    total_headshot_percentage += headshot_pct
                    maps_with_headshot_data += 1
        
        if maps_with_headshot_data > 0:
            avg_headshot_percentage = round(total_headshot_percentage / maps_with_headshot_data, 1)
        else:
            # Fallback к lifetime если нет данных в segments
            avg_headshot_percentage = round(safe_float(lifetime_stats.get('Average Headshots %', 0)), 1)
        
        # Добавляем мульти-киллы в formatted
        formatted.update({
            'total_triple_kills': total_triple_kills,
            'total_quadro_kills': total_quadro_kills,
            'total_penta_kills': total_penta_kills,
            'total_aces': total_penta_kills,  # Эйсы = Penta Kills
            'total_mvps': total_mvps,
            'total_rounds': total_rounds,
            'multi_kills_per_round': round((total_triple_kills + total_quadro_kills + total_penta_kills) / max(total_rounds, 1), 3) if total_rounds > 0 else 0,
            
            # Клатчи из lifetime
            'clutch_1v1_total': safe_int(lifetime_stats.get('Total 1v1 Count', 0)),
            'clutch_1v1_wins': safe_int(lifetime_stats.get('Total 1v1 Wins', 0)),
            'clutch_1v1_percentage': round(safe_float(lifetime_stats.get('1v1 Win Rate', 0)) * 100, 1),
            'clutch_1v2_total': safe_int(lifetime_stats.get('Total 1v2 Count', 0)),
            'clutch_1v2_wins': safe_int(lifetime_stats.get('Total 1v2 Wins', 0)),
            'clutch_1v2_percentage': round(safe_float(lifetime_stats.get('1v2 Win Rate', 0)) * 100, 1),
            
            # Средний процент хедшотов (рассчитанный из segments)
            'avg_headshot_percentage': avg_headshot_percentage
        })
        
        # Статистика по картам (из segments)
        map_statistics = {}
        for map_stat in map_stats:
            map_name = map_stat.get('label', 'Unknown')
            map_data = map_stat.get('stats', {})
            
            if map_data:  # Только если есть данные по карте
                # Рассчитываем приблизительный KAST для карты
                map_kills = safe_int(map_data.get('Kills', 0))
                map_assists = safe_int(map_data.get('Assists', 0))
                map_rounds = safe_int(map_data.get('Rounds', 0))
                map_damage = safe_int(map_data.get('Total Damage', 0))
                
                map_kast = 0.0
                map_adr = 0.0
                if map_rounds > 0:
                    # Более реалистичная формула KAST для карт (максимум 85%)
                    survived_estimate = max(0, map_rounds - safe_int(map_data.get('Deaths', 0))) * 0.5
                    map_kast = ((map_kills + map_assists + survived_estimate) / map_rounds) * 100
                    map_kast = round(min(map_kast, 85.0), 1)  # Реалистичный максимум 85%
                    # Используем ADR из API если доступно, иначе рассчитываем
                    map_adr = round(safe_float(map_data.get('ADR', 0)), 1) or round(map_damage / map_rounds, 1)
                
                map_statistics[map_name] = {
                    'matches': safe_int(map_data.get('Matches', 0)),
                    'wins': safe_int(map_data.get('Wins', 0)),
                    'winrate': round(safe_float(map_data.get('Win Rate %', 0)), 1),
                    'kills': map_kills,
                    'deaths': safe_int(map_data.get('Deaths', 0)),
                    'assists': map_assists,
                    'kd_ratio': round(map_kills / max(safe_int(map_data.get('Deaths', 0)), 1), 3),
                    'adr': map_adr,
                    'kast': map_kast,
                    'headshots': round(safe_float(map_data.get('Average Headshots %', 0)), 1),
                    'hltv_rating': self.calculate_hltv_rating({
                        'Kills': map_kills,
                        'Deaths': safe_int(map_data.get('Deaths', 0)),
                        'Assists': map_assists,
                        'Rounds': map_rounds,
                        'ADR': map_adr,
                        'KAST %': map_kast,
                        'First Kills': safe_int(map_data.get('Total Entry Wins', 0)),
                        'First Deaths': safe_int(map_data.get('Total Entry Count', 0)) - safe_int(map_data.get('Total Entry Wins', 0)),
                        'Flash Assists': safe_int(map_data.get('Total Flash Successes', 0)),
                        'Utility Damage': safe_int(map_data.get('Total Utility Damage', 0))
                    }),
                    'first_kills': safe_int(map_data.get('Total Entry Wins', 0)),
                    'first_deaths': safe_int(map_data.get('Total Entry Count', 0)) - safe_int(map_data.get('Total Entry Wins', 0)),
                    'flash_assists': safe_int(map_data.get('Total Flash Successes', 0)),
                    'utility_damage': safe_int(map_data.get('Total Utility Damage', 0))
                }
        
        formatted['maps'] = map_statistics
        formatted['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Добавляем информацию об источнике данных для отладки
        formatted['data_source'] = {
            'hltv_rating_from': 'aggregated_maps' if map_stats else 'lifetime',
            'has_segments': len(segments) > 0,
            'map_segments_count': len(map_stats),
            'has_lifetime': len(lifetime_stats) > 0,
            'aggregated_metrics': len(hltv_stats) > 0
        }
        
        return formatted
    
    def validate_hltv_data_quality(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация качества данных для расчета HLTV 2.1 рейтинга с учетом агрегации map segments"""
        quality_report = {
            'has_segments': False,
            'has_map_segments': False,
            'map_segments_count': 0,
            'has_lifetime': False,
            'critical_metrics_available': [],
            'missing_metrics': [],
            'data_completeness_score': 0.0,
            'recommended_source': 'none',
            'can_aggregate_maps': False
        }
        
        # Проверяем наличие segments
        segments = stats_data.get('segments', [])
        quality_report['has_segments'] = len(segments) > 0
        
        # Проверяем наличие map segments
        map_stats = []
        if segments:
            map_stats = [s for s in segments if s.get('type') == 'Map' and 'stats' in s]
            quality_report['has_map_segments'] = len(map_stats) > 0
            quality_report['map_segments_count'] = len(map_stats)
        
        # Проверяем наличие lifetime
        lifetime_stats = stats_data.get('lifetime', {})
        quality_report['has_lifetime'] = len(lifetime_stats) > 0
        
        # Критические метрики для HLTV 2.1
        critical_metrics = ['ADR', 'KAST %', 'K/D Ratio', 'Kills', 'Deaths', 'Assists', 'Rounds']
        additional_metrics = ['First Kills', 'First Deaths', 'Flash Assists', 'Utility Damage']
        
        # Определяем лучший источник данных
        best_source = {}
        
        # ПРИОРИТЕТ: Агрегация из map segments
        if map_stats:
            quality_report['recommended_source'] = 'aggregated_maps'
            quality_report['can_aggregate_maps'] = True
            
            # Проверяем, можем ли мы агрегировать все необходимые данные
            aggregatable_metrics = []
            total_rounds = 0
            
            for map_stat in map_stats:
                map_data = map_stat.get('stats', {})
                total_rounds += map_data.get('Rounds', 0) if isinstance(map_data.get('Rounds'), (int, float)) else 0
                
                # Проверяем наличие основных метрик в картах
                if 'Kills' in map_data:
                    aggregatable_metrics.append('Kills')
                if 'Deaths' in map_data:
                    aggregatable_metrics.append('Deaths')
                if 'Assists' in map_data:
                    aggregatable_metrics.append('Assists')
                if 'Rounds' in map_data:
                    aggregatable_metrics.append('Rounds')
                if 'Total Damage' in map_data:
                    aggregatable_metrics.append('ADR')
                if 'Total Entry Wins' in map_data:
                    aggregatable_metrics.append('First Kills')
                if 'Total Flash Successes' in map_data:
                    aggregatable_metrics.append('Flash Assists')
                if 'Total Utility Damage' in map_data:
                    aggregatable_metrics.append('Utility Damage')
            
            # Убираем дубликаты
            aggregatable_metrics = list(set(aggregatable_metrics))
            
            if total_rounds > 0:
                # Можем рассчитать K/D Ratio и приблизительный KAST
                aggregatable_metrics.extend(['K/D Ratio', 'KAST %'])
            
            quality_report['critical_metrics_available'] = aggregatable_metrics
            
        # Fallback на lifetime
        elif lifetime_stats:
            best_source = lifetime_stats
            quality_report['recommended_source'] = 'lifetime'
            
            # Проверяем доступность метрик в lifetime
            for metric in critical_metrics:
                if metric in best_source and best_source[metric] is not None:
                    quality_report['critical_metrics_available'].append(metric)
                else:
                    quality_report['missing_metrics'].append(metric)
            
            for metric in additional_metrics:
                if metric in best_source and best_source[metric] is not None:
                    quality_report['critical_metrics_available'].append(metric)
        
        # Рассчитываем missing metrics только если не используем агрегацию
        if quality_report['recommended_source'] != 'aggregated_maps':
            all_metrics = critical_metrics + additional_metrics
            available = quality_report['critical_metrics_available']
            quality_report['missing_metrics'] = [m for m in all_metrics if m not in available]
        
        # Расчет completeness score
        total_metrics = len(critical_metrics) + len(additional_metrics)
        available_metrics = len(quality_report['critical_metrics_available'])
        quality_report['data_completeness_score'] = round(
            (available_metrics / total_metrics) * 100, 1
        ) if total_metrics > 0 else 0.0
        
        return quality_report
    
    async def get_enhanced_player_stats(self, player_id: str, game: str = "cs2") -> Optional[Dict[str, Any]]:
        """Получить расширенную статистику игрока с проверкой качества данных"""
        stats_data = await self.get_player_stats(player_id, game)
        if not stats_data:
            return None
        
        # Добавляем отчет о качестве данных
        quality_report = self.validate_hltv_data_quality(stats_data)
        stats_data['data_quality'] = quality_report
        
        return stats_data
    
    async def get_detailed_match_stats(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Получить детальную статистику матча с обработкой данных игроков"""
        stats_data = await self._make_request(f"/matches/{match_id}/stats")
        if not stats_data:
            return None
        
        try:
            # Обработка статистики команд и игроков
            processed_stats = {
                'match_id': match_id,
                'rounds': [],
                'teams': {}
            }
            
            # Обработка команд
            for round_data in stats_data.get('rounds', []):
                round_stats = {
                    'best_of': round_data.get('best_of'),
                    'competition_id': round_data.get('competition_id'),
                    'game_id': round_data.get('game_id'),
                    'game_mode': round_data.get('game_mode'),
                    'match_id': round_data.get('match_id'),
                    'match_round': round_data.get('match_round'),
                    'played': round_data.get('played'),
                    'round_stats': {
                        'Region': round_data.get('round_stats', {}).get('Region'),
                        'Map': round_data.get('round_stats', {}).get('Map'),
                        'Rounds': round_data.get('round_stats', {}).get('Rounds'),
                        'Score': round_data.get('round_stats', {}).get('Score'),
                        'Winner': round_data.get('round_stats', {}).get('Winner')
                    },
                    'teams': []
                }
                
                # Обработка команд в раунде
                for team in round_data.get('teams', []):
                    team_stats = {
                        'team_id': team.get('team_id'),
                        'premade': team.get('premade'),
                        'team_stats': team.get('team_stats', {}),
                        'players': []
                    }
                    
                    # Обработка игроков команды
                    for player in team.get('players', []):
                        player_stats = {
                            'player_id': player.get('player_id'),
                            'nickname': player.get('nickname'),
                            'stats': player.get('player_stats', {})
                        }
                        team_stats['players'].append(player_stats)
                    
                    round_stats['teams'].append(team_stats)
                
                processed_stats['rounds'].append(round_stats)
            
            return processed_stats
            
        except Exception as e:
            self.logger.error(f"Error processing match stats: {e}")
            return stats_data  # Возвращаем raw данные если не удалось обработать
    
    async def analyze_player_performance(self, player_id: str, match_count: int = 20) -> Dict[str, Any]:
        """Анализ последней производительности игрока"""
        try:
            # Получаем историю матчей
            history = await self.get_player_history(player_id, limit=match_count)
            if not history or 'items' not in history:
                return {}
            
            matches = history['items']
            performance = {
                'total_matches': len(matches),
                'wins': 0,
                'losses': 0,
                'recent_form': [],  # L/W последние матчи
                'win_streak': 0,
                'current_streak': 0,
                'avg_team_size': 0,
                'regions_played': set(),
                'competition_types': set()
            }
            
            current_streak = 0
            max_win_streak = 0
            
            for i, match in enumerate(matches):
                # Определяем результат для игрока
                player_won = self._determine_player_result(match, player_id)
                
                if player_won is not None:
                    if player_won:
                        performance['wins'] += 1
                        performance['recent_form'].append('W')
                        current_streak += 1
                        max_win_streak = max(max_win_streak, current_streak)
                    else:
                        performance['losses'] += 1
                        performance['recent_form'].append('L')
                        current_streak = 0
                else:
                    performance['recent_form'].append('?')
                
                # Собираем дополнительную информацию
                performance['regions_played'].add(match.get('region', 'Unknown'))
                performance['competition_types'].add(match.get('competition_type', 'Unknown'))
            
            performance['win_streak'] = max_win_streak
            performance['current_streak'] = current_streak if performance['recent_form'] and performance['recent_form'][0] == 'W' else 0
            performance['winrate'] = round((performance['wins'] / performance['total_matches']) * 100, 1) if performance['total_matches'] > 0 else 0
            performance['regions_played'] = list(performance['regions_played'])
            performance['competition_types'] = list(performance['competition_types'])
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error analyzing player performance: {e}")
            return {}
    
    def _determine_player_result(self, match: Dict, player_id: str) -> Optional[bool]:
        """Определить результат матча для конкретного игрока"""
        try:
            if 'results' not in match or 'teams' not in match:
                return None
            
            winner = match['results'].get('winner')
            if not winner:
                return None
            
            # Ищем игрока в командах
            teams = match.get('teams', {})
            player_faction = None
            
            for faction_name, faction_data in teams.items():
                if faction_data and 'players' in faction_data:
                    for player in faction_data['players']:
                        if player.get('player_id') == player_id:
                            player_faction = faction_name
                            break
            
            if player_faction:
                return player_faction == winner
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error determining player result: {e}")
            return None
    
    async def get_player_full_profile(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Получить полный профиль игрока включая статистику и анализ производительности с кешированием"""
        try:
            # Проверяем кеш
            cached_profile = await CacheService.get_player_profile(nickname)
            if cached_profile:
                self.logger.info(f"Returning cached profile for {nickname}")
                return cached_profile
            
            # Поиск игрока
            player = await self.find_player_by_nickname(nickname)
            if not player:
                return None
            
            player_id = player['player_id']
            
            # Получаем детальные данные с улучшенной статистикой
            player_details = await self.get_player_details(player_id)
            enhanced_stats = await self.get_enhanced_player_stats(player_id)
            performance = await self.analyze_player_performance(player_id)
            
            # Объединяем данные
            full_profile = {
                'search_result': player,
                'details': player_details or {},
                'stats': self.format_player_stats(player_details or player, enhanced_stats or {}),
                'performance': performance,
                'data_quality': enhanced_stats.get('data_quality', {}) if enhanced_stats else {},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в кеш
            await CacheService.set_player_profile(nickname, full_profile)
            
            # Также кешируем статистику отдельно для быстрого доступа
            if enhanced_stats:
                await CacheService.set_player_stats(player_id, enhanced_stats)
            
            return full_profile
            
        except Exception as e:
            self.logger.error(f"Error getting full player profile: {e}")
            return None
    
    async def close(self):
        """Закрыть HTTP сессию"""
        if self.session and not self.session.is_closed:
            await self.session.aclose()
    
    # Новые методы для поддержки воркеров
    
    async def get_current_match(self, player_id: str) -> Optional[Dict]:
        """Получить текущий матч игрока"""
        try:
            endpoint = f"/players/{player_id}/games/cs2/faceit"
            matches = await self._make_request(endpoint, cache_ttl=60)
            
            if matches and matches.get('items'):
                # Ищем текущий матч (started или ongoing)
                for match in matches['items']:
                    if match.get('status') in ['started', 'ongoing']:
                        return match
            return None
        except Exception as e:
            self.logger.error(f"Error getting current match: {e}")
            return None
    
    async def analyze_match_participants(self, match: Dict) -> List[Dict]:
        """Анализировать участников матча"""
        try:
            participants = []
            teams = match.get('teams', [])
            
            for team in teams:
                for player in team.get('players', []):
                    player_id = player.get('player_id')
                    if player_id:
                        # Получаем базовую статистику игрока
                        details = await self.get_player_details(player_id)
                        stats = await self.get_player_stats(player_id)
                        
                        if details and stats:
                            formatted_stats = self.format_player_stats(details, stats)
                            participants.append(formatted_stats)
            
            return participants
        except Exception as e:
            self.logger.error(f"Error analyzing match participants: {e}")
            return []
    
    async def analyze_player_form(self, matches: List[Dict]) -> Dict:
        """Анализировать форму игрока по последним матчам"""
        try:
            if not matches:
                return {}
            
            recent_matches = matches[:10]  # Последние 10 матчей
            wins = sum(1 for match in recent_matches if match.get('result') == 'win')
            total = len(recent_matches)
            
            # Анализ статистики
            total_kills = sum(match.get('kills', 0) for match in recent_matches)
            total_deaths = sum(match.get('deaths', 0) for match in recent_matches)
            total_assists = sum(match.get('assists', 0) for match in recent_matches)
            
            avg_kd = total_kills / max(total_deaths, 1)
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            # Определение формы
            if win_rate >= 70 and avg_kd >= 1.2:
                form_status = "excellent"
            elif win_rate >= 60 and avg_kd >= 1.0:
                form_status = "good"
            elif win_rate >= 40 and avg_kd >= 0.8:
                form_status = "average"
            else:
                form_status = "poor"
            
            return {
                'form_status': form_status,
                'win_rate': round(win_rate, 1),
                'avg_kd': round(avg_kd, 2),
                'matches_analyzed': total,
                'wins': wins,
                'losses': total - wins
            }
        except Exception as e:
            self.logger.error(f"Error analyzing player form: {e}")
            return {}
    
    async def get_player_matches_since(self, player_id: str, since_time: datetime) -> List[Dict]:
        """Получить матчи игрока с определенного времени"""
        try:
            all_matches = await self.get_player_matches(player_id, limit=50)
            if not all_matches:
                return []
            
            # Фильтруем матчи по времени
            filtered_matches = []
            for match in all_matches:
                finished_at = match.get('finished_at')
                if finished_at:
                    match_time = datetime.fromtimestamp(finished_at, timezone.utc)
                    if match_time >= since_time:
                        filtered_matches.append(match)
            
            return filtered_matches
        except Exception as e:
            self.logger.error(f"Error getting matches since time: {e}")
            return []
    
    async def calculate_session_stats(self, matches: List[Dict]) -> Dict:
        """Рассчитать статистику сессии"""
        try:
            if not matches:
                return {}
            
            total_matches = len(matches)
            wins = sum(1 for match in matches if match.get('result') == 'win')
            losses = total_matches - wins
            
            total_kills = sum(match.get('kills', 0) for match in matches)
            total_deaths = sum(match.get('deaths', 0) for match in matches)
            total_assists = sum(match.get('assists', 0) for match in matches)
            
            # Средние показатели
            avg_kills = total_kills / total_matches if total_matches > 0 else 0
            avg_deaths = total_deaths / total_matches if total_matches > 0 else 0
            avg_kd = total_kills / max(total_deaths, 1)
            win_rate = (wins / total_matches) * 100 if total_matches > 0 else 0
            
            return {
                'matches_count': total_matches,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'total_kills': total_kills,
                'total_deaths': total_deaths,
                'total_assists': total_assists,
                'avg_kills': round(avg_kills, 1),
                'avg_deaths': round(avg_deaths, 1),
                'avg_kd': round(avg_kd, 2)
            }
        except Exception as e:
            self.logger.error(f"Error calculating session stats: {e}")
            return {}
    
    async def create_comparison(self, player_data: List[Dict]) -> Dict:
        """Создать сравнение игроков"""
        try:
            if len(player_data) < 2:
                return {}
            
            comparison = {
                'players': player_data,
                'comparison_metrics': {},
                'winner_by_metric': {}
            }
            
            # Метрики для сравнения
            metrics = ['level', 'elo', 'kd_ratio', 'adr', 'hltv_rating', 'winrate', 'headshot_percentage']
            
            for metric in metrics:
                values = []
                for player in player_data:
                    value = player.get(metric, 0)
                    values.append({'nickname': player.get('nickname', 'Unknown'), 'value': value})
                
                # Сортируем по убыванию и определяем лидера
                values.sort(key=lambda x: x['value'], reverse=True)
                comparison['comparison_metrics'][metric] = values
                comparison['winner_by_metric'][metric] = values[0]['nickname'] if values else None
            
            return comparison
        except Exception as e:
            self.logger.error(f"Error creating comparison: {e}")
            return {}
    
    async def create_enhanced_comparison(self, enhanced_data: List[Dict]) -> Dict:
        """Создать расширенное сравнение с анализом формы"""
        try:
            if len(enhanced_data) < 2:
                return {}
            
            base_comparison = await self.create_comparison([data['player'] for data in enhanced_data])
            
            # Добавляем анализ формы
            form_analysis = []
            for data in enhanced_data:
                player = data['player']
                form = data.get('form', {})
                
                form_analysis.append({
                    'nickname': player.get('nickname', 'Unknown'),
                    'form_status': form.get('form_status', 'unknown'),
                    'recent_win_rate': form.get('win_rate', 0),
                    'recent_kd': form.get('avg_kd', 0),
                    'recent_matches': data.get('recent_matches', [])
                })
            
            base_comparison['form_analysis'] = form_analysis
            base_comparison['type'] = 'enhanced'
            
            return base_comparison
        except Exception as e:
            self.logger.error(f"Error creating enhanced comparison: {e}")
            return {}


async def test_faceit_client():
    """Тестирование FACEIT API клиента на примере игрока Geun-Hee"""
    client = FaceitAPIClient()
    test_nickname = "Geun-Hee"
    
    try:
        print(f"\n=== Тестирование FACEIT API клиента ===\n")
        
        # Тест поиска игрока
        print(f"1. Поиск игрока '{test_nickname}'...")
        player = await client.find_player_by_nickname(test_nickname)
        if player:
            print(f"   ✓ Игрок найден: {player['nickname']} (ID: {player['player_id']})")
            player_id = player['player_id']
        else:
            print(f"   ✗ Игрок не найден")
            return
        
        # Тест получения деталей игрока
        print(f"\n2. Получение детальной информации...")
        details = await client.get_player_details(player_id)
        if details:
            print(f"   ✓ Детали получены, уровень: {details.get('games', {}).get('cs2', {}).get('skill_level', 'N/A')}")
        else:
            print(f"   ✗ Детали не получены")
        
        # Тест получения статистики
        print(f"\n3. Получение статистики...")
        stats = await client.get_enhanced_player_stats(player_id)
        if stats:
            print(f"   ✓ Статистика получена")
            if 'lifetime' in stats:
                lifetime = stats['lifetime']
                print(f"     - Матчи: {lifetime.get('Matches', 'N/A')}")
                print(f"     - Побед: {lifetime.get('Wins', 'N/A')}")
                print(f"     - Винрейт: {lifetime.get('Win Rate %', 'N/A')}%")
            if 'segments' in stats:
                print(f"     - Сегментов данных: {len(stats['segments'])}")
                # Проверяем наличие Overall segment
                overall_segment = next((s for s in stats['segments'] if s.get('label') == 'Overall'), None)
                if overall_segment:
                    print(f"     - Overall segment найден ✓")
                    overall_stats = overall_segment.get('stats', {})
                    print(f"     - ADR: {overall_stats.get('ADR', 'N/A')}")
                    print(f"     - KAST: {overall_stats.get('KAST %', 'N/A')}%")
                else:
                    print(f"     - Overall segment не найден ✗")
            
            # Проверяем качество данных
            if 'data_quality' in stats:
                quality = stats['data_quality']
                print(f"     - Качество данных:")
                print(f"       • Рекомендуемый источник: {quality.get('recommended_source', 'N/A')}")
                print(f"       • Полнота данных: {quality.get('data_completeness_score', 0)}%")
                print(f"       • Доступные метрики: {len(quality.get('critical_metrics_available', []))}")
        else:
            print(f"   ✗ Статистика не получена")
        
        # Тест форматирования
        print(f"\n4. Форматирование данных...")
        if details and stats:
            formatted = client.format_player_stats(details, stats)
            if formatted:
                print(f"   ✓ Данные отформатированы")
                print(f"     - Никнейм: {formatted.get('nickname')}")
                print(f"     - Уровень: {formatted.get('level')}")
                print(f"     - ELO: {formatted.get('elo')}")
                print(f"     - Матчи: {formatted.get('matches')}")
                print(f"     - Винрейт: {formatted.get('winrate')}%")
                print(f"     - K/D: {formatted.get('kd_ratio')}")
                print(f"     - HLTV Rating: {formatted.get('hltv_rating')}")
                print(f"     - Карт в статистике: {len(formatted.get('maps', {}))}")
            else:
                print(f"   ✗ Ошибка форматирования")
        
        # Тест истории матчей
        print(f"\n5. Получение истории матчей...")
        history = await client.get_player_history(player_id, limit=10)
        if history and 'items' in history:
            matches = history['items']
            print(f"   ✓ История получена: {len(matches)} матчей")
            if matches:
                recent_match = matches[0]
                print(f"     - Последний матч: {recent_match.get('match_id')}")
                print(f"     - Режим игры: {recent_match.get('game_mode')}")
                print(f"     - Статус: {recent_match.get('status')}")
        else:
            print(f"   ✗ История матчей не получена")
        
        # Тест анализа производительности
        print(f"\n6. Анализ производительности...")
        performance = await client.analyze_player_performance(player_id, 20)
        if performance:
            print(f"   ✓ Анализ выполнен")
            print(f"     - Проанализировано матчей: {performance.get('total_matches')}")
            print(f"     - Побед: {performance.get('wins')}")
            print(f"     - Винрейт: {performance.get('winrate')}%")
            print(f"     - Текущая серия: {performance.get('current_streak')}")
            print(f"     - Лучшая серия побед: {performance.get('win_streak')}")
        else:
            print(f"   ✗ Анализ производительности не выполнен")
        
        # Тест полного профиля
        print(f"\n7. Получение полного профиля...")
        full_profile = await client.get_player_full_profile(test_nickname)
        if full_profile:
            print(f"   ✓ Полный профиль получен")
            print(f"     - Разделов данных: {len(full_profile)}")
            if 'stats' in full_profile and full_profile['stats']:
                print(f"     - Статистика обработана: ✓")
            if 'performance' in full_profile and full_profile['performance']:
                print(f"     - Анализ производительности: ✓")
        else:
            print(f"   ✗ Полный профиль не получен")
        
        print(f"\n=== Тестирование завершено ===\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
        client.logger.error(f"Test error: {e}")
    
    finally:
        await client.close()


# Глобальный экземпляр клиента
faceit_client = FaceitAPIClient()


if __name__ == "__main__":
    # Запуск тестов если файл вызван напрямую
    asyncio.run(test_faceit_client())