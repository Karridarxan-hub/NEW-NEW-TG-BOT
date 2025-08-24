"""
Специализированные воркеры для обработки задач анализа FACEIT данных
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import settings
from storage import storage
from faceit_client import FaceitAPIClient


logger = logging.getLogger(__name__)


class WorkerQueue:
    """Система очередей для распределения задач между воркерами"""
    
    def __init__(self, max_size: int = 1000):
        self.stats_queue = asyncio.Queue(maxsize=max_size)
        self.history_queue = asyncio.Queue(maxsize=max_size)
        self.comparison_queue = asyncio.Queue(maxsize=max_size)
        self.notification_queue = asyncio.Queue(maxsize=max_size)
        
    async def add_stats_task(self, task: Dict[str, Any]):
        """Добавить задачу анализа статистики"""
        try:
            await self.stats_queue.put(task)
            logger.debug(f"Added stats task: {task.get('type', 'unknown')}")
        except asyncio.QueueFull:
            logger.warning("Stats queue is full, dropping task")
    
    async def add_history_task(self, task: Dict[str, Any]):
        """Добавить задачу анализа истории матчей"""
        try:
            await self.history_queue.put(task)
            logger.debug(f"Added history task: {task.get('type', 'unknown')}")
        except asyncio.QueueFull:
            logger.warning("History queue is full, dropping task")
    
    async def add_comparison_task(self, task: Dict[str, Any]):
        """Добавить задачу сравнения игроков"""
        try:
            await self.comparison_queue.put(task)
            logger.debug(f"Added comparison task: {task.get('type', 'unknown')}")
        except asyncio.QueueFull:
            logger.warning("Comparison queue is full, dropping task")
    
    async def add_notification_task(self, task: Dict[str, Any]):
        """Добавить задачу уведомления"""
        try:
            await self.notification_queue.put(task)
            logger.debug(f"Added notification task: {task.get('type', 'unknown')}")
        except asyncio.QueueFull:
            logger.warning("Notification queue is full, dropping task")


# Глобальная очередь задач
worker_queue = WorkerQueue(max_size=settings.max_queue_size)


async def stats_analysis_worker(worker_id: int):
    """Воркер для анализа статистики игроков"""
    logger.info(f"🔍 Stats analysis worker {worker_id} started")
    client = FaceitAPIClient()
    
    while True:
        try:
            # Ждем задачу из очереди
            task = await asyncio.wait_for(
                worker_queue.stats_queue.get(),
                timeout=settings.worker_timeout
            )
            
            logger.debug(f"Worker {worker_id} processing stats task: {task.get('type')}")
            
            # Обработка разных типов задач
            task_type = task.get('type')
            if task_type == 'player_stats':
                await process_player_stats(client, task)
            elif task_type == 'current_match':
                await process_current_match(client, task)
            elif task_type == 'form_analysis':
                await process_form_analysis(client, task)
            else:
                logger.warning(f"Unknown stats task type: {task_type}")
            
            # Отмечаем задачу как выполненную
            worker_queue.stats_queue.task_done()
            
        except asyncio.TimeoutError:
            # Нет задач, продолжаем ожидание
            continue
        except Exception as e:
            logger.error(f"Error in stats worker {worker_id}: {e}")
            await asyncio.sleep(1)
    
    await client.close()


async def match_history_worker(worker_id: int):
    """Воркер для анализа истории матчей"""
    logger.info(f"📊 Match history worker {worker_id} started")
    client = FaceitAPIClient()
    
    while True:
        try:
            task = await asyncio.wait_for(
                worker_queue.history_queue.get(),
                timeout=settings.worker_timeout
            )
            
            logger.debug(f"Worker {worker_id} processing history task: {task.get('type')}")
            
            task_type = task.get('type')
            if task_type == 'match_history':
                await process_match_history(client, task)
            elif task_type == 'last_matches':
                await process_last_matches(client, task)
            elif task_type == 'session_stats':
                await process_session_stats(client, task)
            else:
                logger.warning(f"Unknown history task type: {task_type}")
            
            worker_queue.history_queue.task_done()
            
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Error in history worker {worker_id}: {e}")
            await asyncio.sleep(1)
    
    await client.close()


async def comparison_worker(worker_id: int):
    """Воркер для сравнения игроков"""
    logger.info(f"⚖️ Comparison worker {worker_id} started")
    client = FaceitAPIClient()
    
    while True:
        try:
            task = await asyncio.wait_for(
                worker_queue.comparison_queue.get(),
                timeout=settings.worker_timeout
            )
            
            logger.debug(f"Worker {worker_id} processing comparison task: {task.get('type')}")
            
            task_type = task.get('type')
            if task_type == 'player_comparison':
                await process_player_comparison(client, task)
            elif task_type == 'enhanced_comparison':
                await process_enhanced_comparison(client, task)
            else:
                logger.warning(f"Unknown comparison task type: {task_type}")
            
            worker_queue.comparison_queue.task_done()
            
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Error in comparison worker {worker_id}: {e}")
            await asyncio.sleep(1)
    
    await client.close()


async def notification_worker(worker_id: int):
    """Воркер для отправки уведомлений"""
    logger.info(f"📢 Notification worker {worker_id} started")
    
    while True:
        try:
            task = await asyncio.wait_for(
                worker_queue.notification_queue.get(),
                timeout=settings.worker_timeout
            )
            
            logger.debug(f"Processing notification task: {task.get('type')}")
            
            task_type = task.get('type')
            if task_type == 'match_notification':
                await process_match_notification(task)
            elif task_type == 'stats_notification':
                await process_stats_notification(task)
            else:
                logger.warning(f"Unknown notification task type: {task_type}")
            
            worker_queue.notification_queue.task_done()
            
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Error in notification worker {worker_id}: {e}")
            await asyncio.sleep(1)


# Функции обработки задач

async def process_player_stats(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи получения статистики игрока"""
    try:
        player_id = task['player_id']
        user_id = task['user_id']
        
        # Получаем статистику игрока
        player_details = await client.get_player_details(player_id)
        if not player_details:
            logger.warning(f"No details found for player {player_id}")
            return
        
        player_stats = await client.get_player_stats(player_id)
        if not player_stats:
            logger.warning(f"No stats found for player {player_id}")
            return
        
        # Форматируем статистику
        formatted_stats = client.format_player_stats(player_details, player_stats)
        
        # Сохраняем в кэш
        cache_key = f"player_stats_{player_id}"
        await storage.cache_data(cache_key, formatted_stats, ttl_minutes=15)
        
        logger.info(f"Processed stats for player {player_id}")
        
    except Exception as e:
        logger.error(f"Error processing player stats: {e}")


async def process_current_match(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи анализа текущего матча"""
    try:
        player_id = task['player_id']
        
        # Получаем текущий матч
        current_match = await client.get_current_match(player_id)
        if not current_match:
            return
        
        # Анализируем участников матча
        participants = await client.analyze_match_participants(current_match)
        
        # Сохраняем результат
        cache_key = f"current_match_{player_id}"
        await storage.cache_data(cache_key, {
            'match': current_match,
            'participants': participants
        }, ttl_minutes=5)
        
        logger.info(f"Processed current match for player {player_id}")
        
    except Exception as e:
        logger.error(f"Error processing current match: {e}")


async def process_form_analysis(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи анализа формы игрока"""
    try:
        player_id = task['player_id']
        
        # Получаем последние матчи
        matches = await client.get_player_matches(player_id, limit=20)
        if not matches:
            return
        
        # Анализируем форму
        form_analysis = await client.analyze_player_form(matches)
        
        # Сохраняем результат
        cache_key = f"form_analysis_{player_id}"
        await storage.cache_data(cache_key, form_analysis, ttl_minutes=30)
        
        logger.info(f"Processed form analysis for player {player_id}")
        
    except Exception as e:
        logger.error(f"Error processing form analysis: {e}")


async def process_match_history(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи анализа истории матчей"""
    try:
        player_id = task['player_id']
        limit = task.get('limit', 20)
        
        # Получаем историю матчей
        matches = await client.get_player_matches(player_id, limit=limit)
        if not matches:
            return
        
        # Обрабатываем каждый матч
        processed_matches = []
        for match in matches:
            match_details = await client.get_match_details(match['match_id'])
            if match_details:
                processed_matches.append(match_details)
        
        # Сохраняем результат
        cache_key = f"match_history_{player_id}_{limit}"
        await storage.cache_data(cache_key, processed_matches, ttl_minutes=20)
        
        logger.info(f"Processed {len(processed_matches)} matches for player {player_id}")
        
    except Exception as e:
        logger.error(f"Error processing match history: {e}")


async def process_last_matches(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи получения последних матчей"""
    try:
        player_id = task['player_id']
        
        # Получаем последние матчи с деталями
        matches = await client.get_player_matches(player_id, limit=5)
        detailed_matches = []
        
        # Batch обработка матчей
        semaphore = asyncio.Semaphore(settings.concurrent_requests)
        
        async def get_match_detail(match):
            async with semaphore:
                return await client.get_match_details(match['match_id'])
        
        tasks = [get_match_detail(match) for match in matches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if not isinstance(result, Exception) and result:
                detailed_matches.append(result)
        
        # Сохраняем результат
        cache_key = f"last_matches_{player_id}"
        await storage.cache_data(cache_key, detailed_matches, ttl_minutes=10)
        
        logger.info(f"Processed last matches for player {player_id}")
        
    except Exception as e:
        logger.error(f"Error processing last matches: {e}")


async def process_session_stats(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи анализа статистики сессии"""
    try:
        user_id = task['user_id']
        player_id = task['player_id']
        
        # Получаем данные сессии из БД
        session = await storage.get_user_active_session(user_id)
        if not session:
            return
        
        # Получаем матчи за период сессии
        matches = await client.get_player_matches_since(player_id, session['start_time'])
        
        # Анализируем статистику сессии
        session_stats = await client.calculate_session_stats(matches)
        
        # Обновляем сессию в БД
        await storage.update_session_stats(session['id'], session_stats)
        
        logger.info(f"Updated session stats for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing session stats: {e}")


async def process_player_comparison(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи сравнения игроков"""
    try:
        players = task['players']  # Список player_id
        
        # Получаем статистику всех игроков параллельно
        semaphore = asyncio.Semaphore(settings.concurrent_requests)
        
        async def get_player_data(player_id):
            async with semaphore:
                details = await client.get_player_details(player_id)
                stats = await client.get_player_stats(player_id)
                return client.format_player_stats(details, stats) if details and stats else None
        
        tasks = [get_player_data(pid) for pid in players]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        player_data = []
        for result in results:
            if not isinstance(result, Exception) and result:
                player_data.append(result)
        
        # Создаем сравнение
        comparison_result = await client.create_comparison(player_data)
        
        # Сохраняем результат
        cache_key = f"comparison_{'_'.join(players)}"
        await storage.cache_data(cache_key, comparison_result, ttl_minutes=20)
        
        logger.info(f"Created comparison for {len(player_data)} players")
        
    except Exception as e:
        logger.error(f"Error processing player comparison: {e}")


async def process_enhanced_comparison(client: FaceitAPIClient, task: Dict[str, Any]):
    """Обработка задачи расширенного сравнения"""
    try:
        players = task['players']
        
        # Получаем расширенные данные для каждого игрока
        enhanced_data = []
        
        for player_id in players:
            # Базовая статистика
            details = await client.get_player_details(player_id)
            stats = await client.get_player_stats(player_id)
            
            if details and stats:
                # Последние матчи для анализа формы
                matches = await client.get_player_matches(player_id, limit=10)
                form = await client.analyze_player_form(matches) if matches else None
                
                enhanced_data.append({
                    'player': client.format_player_stats(details, stats),
                    'form': form,
                    'recent_matches': matches[:5] if matches else []
                })
        
        # Создаем расширенное сравнение
        enhanced_comparison = await client.create_enhanced_comparison(enhanced_data)
        
        # Сохраняем результат
        cache_key = f"enhanced_comparison_{'_'.join(players)}"
        await storage.cache_data(cache_key, enhanced_comparison, ttl_minutes=30)
        
        logger.info(f"Created enhanced comparison for {len(enhanced_data)} players")
        
    except Exception as e:
        logger.error(f"Error processing enhanced comparison: {e}")


async def process_match_notification(task: Dict[str, Any]):
    """Обработка уведомления о матче"""
    try:
        user_id = task['user_id']
        match_data = task['match_data']
        
        # Здесь будет логика отправки уведомления через Telegram
        # Пока заглушка
        logger.info(f"Sent match notification to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing match notification: {e}")


async def process_stats_notification(task: Dict[str, Any]):
    """Обработка уведомления о статистике"""
    try:
        user_id = task['user_id']
        stats_data = task['stats_data']
        
        # Здесь будет логика отправки уведомления через Telegram
        # Пока заглушка
        logger.info(f"Sent stats notification to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing stats notification: {e}")


def get_worker_queue() -> WorkerQueue:
    """Получить глобальную очередь воркеров"""
    return worker_queue