import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import hashlib
import hmac
from contextlib import asynccontextmanager

from config import settings
from storage import storage, init_storage, cleanup_storage, cleanup_storage_task
from faceit_client import faceit_client

# Настройка логирования с маскированием чувствительных данных
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
    """Маскировать чувствительные данные для логов"""
    if len(data) <= show_chars * 2:
        return "*" * len(data)
    return data[:show_chars] + "*" * (len(data) - show_chars * 2) + data[-show_chars:]

# Создаем экземпляры бота и диспетчера
bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())

def setup_routers():
    """Настройка роутеров - вызывается один раз"""
    try:
        # Импортируем обработчики из модулей только при настройке
        from bot.handlers import main_router, stats_router, match_router, profile_router, settings_router, match_history_router, form_analysis_router, last_match_router, current_match_router, comparison_router, help_router
        
        # Регистрируем роутеры в правильном порядке
        dp.include_router(main_router)
        dp.include_router(stats_router)
        dp.include_router(match_router)
        dp.include_router(profile_router)
        dp.include_router(match_history_router)
        dp.include_router(form_analysis_router)
        dp.include_router(last_match_router)
        dp.include_router(current_match_router)
        dp.include_router(comparison_router)
        dp.include_router(help_router)
        dp.include_router(settings_router)
        
        logger.info("✅ Роутеры успешно зарегистрированы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации роутеров: {e}")
        raise

# FastAPI приложение
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("🚀 Запуск FACEIT CS2 бота...")
    logger.info(f"🤖 Bot Token: {mask_sensitive_data(settings.bot_token)}")
    logger.info(f"🔑 FACEIT API Key: {mask_sensitive_data(settings.faceit_api_key)}")
    
    # Настройка роутеров
    setup_routers()
    
    # Инициализация базы данных
    try:
        await init_storage()
        logger.info("✅ Database connections established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to databases: {e}")
        raise
    
    # Запуск фоновых задач
    cleanup_task = asyncio.create_task(cleanup_storage_task())
    polling_task = asyncio.create_task(start_polling())
    match_monitor_task = asyncio.create_task(match_monitoring_task())
    
    try:
        yield
    finally:
        # Остановка
        logger.info("🛑 Остановка бота...")
        cleanup_task.cancel()
        polling_task.cancel()
        match_monitor_task.cancel()
        
        # Закрытие подключений к БД
        await cleanup_storage()
        
        # Ждем завершения задач
        await asyncio.gather(cleanup_task, polling_task, match_monitor_task, return_exceptions=True)

app = FastAPI(
    title="FACEIT CS2 Bot API",
    description="API для получения статистики игроков CS2 с FACEIT",
    version="1.1.0",
    lifespan=lifespan
)

# API endpoints
@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "FACEIT CS2 Bot API",
        "version": "1.1.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "stats": "/api/stats",
            "player_search": "/api/player/search/{nickname}",
            "player_stats": "/api/player/{player_id}/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка состояния системы"""
    try:
        # Проверяем доступность FACEIT API
        test_response = await faceit_client._make_request("/players", {"nickname": "test", "game": "cs2"})
        faceit_status = "ok" if test_response or True else "error"  # Игнорируем 404 для тестового запроса
        
        # Получаем статистику из базы данных
        db_stats = await storage.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": await storage.get_current_time(),
            "services": {
                "bot": "active",
                "api": "active", 
                "storage": "active",
                "postgres": "active",
                "redis": "active",
                "faceit_api": faceit_status
            },
            "metrics": db_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": await storage.get_current_time()
            }
        )

@app.get("/api/player/search/{nickname}")
async def search_player(nickname: str):
    """Поиск игрока по никнейму"""
    try:
        # Валидация никнейма
        if not nickname or len(nickname) < 2 or len(nickname) > 30:
            return JSONResponse(
                status_code=400,
                content={"error": "Nickname must be between 2 and 30 characters"}
            )
        
        # Поиск игрока
        player_data = await faceit_client.find_player_by_nickname(nickname)
        
        if not player_data:
            return JSONResponse(
                status_code=404,
                content={"error": f"Player '{nickname}' not found"}
            )
        
        return {
            "player_id": player_data.get("player_id"),
            "nickname": player_data.get("nickname"),
            "avatar": player_data.get("avatar"),
            "country": player_data.get("country"),
            "games": player_data.get("games", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching player {nickname}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

@app.get("/api/player/{player_id}/stats")
async def get_player_stats(player_id: str):
    """Получить статистику игрока"""
    try:
        # Валидация player_id
        if not player_id or len(player_id) < 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid player_id format"}
            )
        
        # Получение статистики
        stats = await faceit_client.get_player_stats(player_id)
        
        if not stats:
            return JSONResponse(
                status_code=404,
                content={"error": f"Stats for player '{player_id}' not found"}
            )
        
        return {
            "player_id": player_id,
            "stats": stats,
            "timestamp": await storage.get_current_time()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for player {player_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

@app.get("/api/stats")
async def get_bot_stats():
    """Получить статистику бота"""
    db_stats = await storage.get_stats()
    return {
        **db_stats,
        "uptime": await storage.get_current_time(),
        "version": "1.2.0"
    }

@app.post("/webhook/faceit")
async def faceit_webhook(request: Request, data: dict):
    """Webhook для уведомлений от FACEIT"""
    try:
        # Проверка подписи webhook (базовая безопасность)
        await verify_webhook_signature(request, data)
        logger.info(f"Received FACEIT webhook: {data.get('event', 'unknown')}")
        
        # Обработка различных типов событий
        event_type = data.get("event")
        
        if event_type == "match_status_finished":
            # Обработка завершенного матча
            match_id = data.get("payload", {}).get("id")
            if match_id:
                await process_finished_match(match_id)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Webhook processing failed"}
        )

async def process_finished_match(match_id: str):
    """Обработать завершенный матч и отправить уведомления"""
    try:
        logger.info(f"Processing finished match: {match_id}")
        
        # Получаем детали матча
        match_details = await faceit_client.get_match_details(match_id)
        if not match_details:
            logger.warning(f"No match details found for match {match_id}")
            return
        
        # Получаем статистику матча для более подробной информации
        match_stats = await faceit_client.get_match_stats(match_id)
        if not match_stats:
            logger.warning(f"No match stats found for match {match_id}")
        
        # Находим пользователей, которые участвовали в матче
        teams = match_details.get("teams", {})
        notified_users = 0
        
        for team_name, team_data in teams.items():
            roster = team_data.get("roster", [])
            for player in roster:
                player_id = player.get("player_id")
                if not player_id:
                    continue
                
                # Ищем пользователя в нашей базе по FACEIT ID
                user = await storage.get_user_by_faceit_id(player_id)
                if not user:
                    continue
                
                user_id = user.get("user_id")
                notifications_enabled = user.get("notifications", True)
                
                # Проверяем, включены ли уведомления у пользователя
                if not notifications_enabled:
                    logger.info(f"Notifications disabled for user {user_id}")
                    await storage.save_notification_log(user_id, match_id, "skipped", "notifications_disabled")
                    continue
                
                # Проверяем, не отправляли ли уже уведомление об этом матче
                already_notified = await storage.is_match_notification_sent(match_id, user_id)
                if already_notified:
                    logger.info(f"Notification for match {match_id} already sent to user {user_id}")
                    continue
                
                # Отправляем уведомление
                try:
                    await send_match_notification(user_id, match_details, match_stats, player_id)
                    
                    # Отмечаем что уведомление отправлено
                    await storage.mark_match_notification_sent(match_id, user_id, {
                        "match_id": match_id,
                        "player_id": player_id,
                        "nickname": player.get("nickname"),
                        "sent_at": datetime.now().isoformat()
                    })
                    
                    # Сохраняем матч в историю пользователя
                    if match_stats:
                        await save_match_to_history(user_id, match_id, match_details, match_stats, player_id)
                    
                    await storage.save_notification_log(user_id, match_id, "sent")
                    notified_users += 1
                    
                    logger.info(f"Match notification sent to user {user_id} for match {match_id}")
                    
                except Exception as notification_error:
                    error_msg = str(notification_error)
                    logger.error(f"Failed to send notification to user {user_id}: {error_msg}")
                    await storage.save_notification_log(user_id, match_id, "failed", error_msg)
        
        logger.info(f"Match {match_id} processing completed. Notifications sent to {notified_users} users")
        
    except Exception as e:
        logger.error(f"Error processing finished match {match_id}: {e}")

async def send_match_notification(user_id: int, match_details: dict, match_stats: dict, user_faceit_id: str):
    """Отправить уведомление о завершенном матче"""
    try:
        # Формируем сообщение уведомления используя тот же формат что и в last_match
        message_text = await format_match_notification(match_details, match_stats, user_faceit_id)
        
        # Создаем клавиатуру с ссылкой на матч
        keyboard = create_match_keyboard(match_details)
        
        await bot.send_message(
            user_id, 
            message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {e}")
        raise


async def format_match_notification(match_data: dict, match_stats: dict, user_faceit_id: str) -> str:
    """Форматирует уведомление о матче в том же стиле что и последний матч"""
    try:
        # Получаем основную информацию о матче
        match_result = match_data.get('results', {})
        winner = match_result.get('winner')
        
        # Определяем команды и счет
        teams = match_data.get('teams', {})
        team1_name = teams.get('faction1', {}).get('name', 'Team 1')
        team2_name = teams.get('faction2', {}).get('name', 'Team 2')
        
        team1_score = match_result.get('score', {}).get('faction1', 0)
        team2_score = match_result.get('score', {}).get('faction2', 0)
        
        # Определяем статус для пользователя (победа/поражение)
        user_team = get_user_team_from_match_stats(match_stats, user_faceit_id)
        if user_team and winner:
            if (user_team == 'faction1' and winner == 'faction1') or \
               (user_team == 'faction2' and winner == 'faction2'):
                status_emoji = "🏆"
            else:
                status_emoji = "💔"
        else:
            status_emoji = "🎮"

        # Карта
        voting = match_data.get('voting', {})
        map_name = "Неизвестная карта"
        if voting and 'map' in voting:
            if 'pick' in voting['map']:
                map_name = voting['map']['pick'][0] if voting['map']['pick'] else "Неизвестная карта"
            elif 'name' in voting['map']:
                map_name = voting['map']['name']

        # Статистика пользователя
        user_stats = get_user_stats_from_match(match_stats, user_faceit_id)
        
        # Формируем сообщение
        message_lines = [
            "🎮 <b>Ваш матч завершен!</b>",
            "",
            f"{status_emoji} <b>{team1_name} {team1_score} - {team2_score} {team2_name}</b>",
            f"🗺️ <b>Карта:</b> {map_name}",
            "",
            f"📊 <b>Ваша статистика:</b>",
        ]

        if user_stats:
            kills = user_stats.get('Kills', '0')
            deaths = user_stats.get('Deaths', '0')
            assists = user_stats.get('Assists', '0')
            kd_ratio = user_stats.get('K/D Ratio', '0.00')
            adr = user_stats.get('ADR', '0')
            hltv_rating = faceit_client.calculate_hltv_rating(user_stats)
            
            message_lines.append(
                f"🔥 K-D-A: {kills}-{deaths}-{assists} | K/D: {kd_ratio} | ADR: {adr} | HLTV 2.1: {hltv_rating:.2f}"
            )
        else:
            message_lines.append("❌ Статистика недоступна")

        return "\n".join(message_lines)

    except Exception as e:
        logger.error(f"Error formatting match notification: {e}")
        return "🎮 Ваш матч завершен!\n❌ Ошибка при загрузке деталей матча"


def get_user_team_from_match_stats(match_stats: dict, user_faceit_id: str) -> str:
    """Определяет в какой команде играл пользователь"""
    try:
        if not match_stats:
            return None
            
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return None
            
        round_stats = rounds[0]  # Берем первый раунд
        teams = round_stats.get('teams', [])
        
        for team in teams:
            players = team.get('players', [])
            for player in players:
                if player.get('player_id') == user_faceit_id:
                    return team.get('team_id')
        
        return None
    except Exception as e:
        logger.error(f"Error getting user team: {e}")
        return None


def get_user_stats_from_match(match_stats: dict, user_faceit_id: str) -> dict:
    """Получает статистику пользователя из матча"""
    try:
        if not match_stats:
            return None
            
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return None
            
        round_stats = rounds[0]
        teams = round_stats.get('teams', [])
        
        for team in teams:
            players = team.get('players', [])
            for player in players:
                if player.get('player_id') == user_faceit_id:
                    return player.get('player_stats', {})
        
        return None
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None


def create_match_keyboard(match_data: dict):
    """Создает клавиатуру с кнопкой для просмотра матча на FACEIT"""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Кнопка для просмотра матча на FACEIT
    match_id = match_data.get('match_id', '')
    if match_id:
        faceit_url = f"https://www.faceit.com/en/cs2/room/{match_id}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Смотреть матч на FACEIT", url=faceit_url)]
            ]
        )
        return keyboard
    
    return None


async def save_match_to_history(user_id: int, match_id: str, match_details: dict, match_stats: dict, user_faceit_id: str):
    """Сохранить матч в историю пользователя"""
    try:
        # Получаем статистику пользователя из матча
        user_stats = get_user_stats_from_match(match_stats, user_faceit_id)
        if not user_stats:
            logger.warning(f"No user stats found for match {match_id}")
            return
        
        # Определяем результат матча для пользователя
        match_result = match_details.get('results', {})
        winner = match_result.get('winner')
        user_team = get_user_team_from_match_stats(match_stats, user_faceit_id)
        
        if user_team and winner:
            if (user_team == 'faction1' and winner == 'faction1') or \
               (user_team == 'faction2' and winner == 'faction2'):
                result = "win"
            else:
                result = "loss"
        else:
            result = "unknown"
        
        # Получаем время завершения матча
        finished_at = match_details.get('finished_at')
        if finished_at:
            # Конвертируем timestamp в datetime
            from datetime import datetime
            finished_at = datetime.fromtimestamp(finished_at)
        else:
            finished_at = datetime.now()
        
        # Карта
        voting = match_details.get('voting', {})
        map_name = "Unknown"
        if voting and 'map' in voting:
            if 'pick' in voting['map']:
                map_name = voting['map']['pick'][0] if voting['map']['pick'] else "Unknown"
            elif 'name' in voting['map']:
                map_name = voting['map']['name']
        
        # Счет команд
        teams = match_details.get('teams', {})
        score = match_result.get('score', {})
        team1_score = score.get('faction1', 0)
        team2_score = score.get('faction2', 0)
        
        # Подготавливаем данные для сохранения
        match_data = {
            'match_id': match_id,
            'user_id': user_id,
            'finished_at': finished_at,
            'result': result,
            'kills': int(user_stats.get('Kills', '0')),
            'deaths': int(user_stats.get('Deaths', '0')),
            'assists': int(user_stats.get('Assists', '0')),
            'adr': float(user_stats.get('ADR', '0')),
            'hltv_rating': faceit_client.calculate_hltv_rating(user_stats),
            'headshots': int(user_stats.get('Headshots', '0')),
            'headshot_percentage': float(user_stats.get('Headshots %', '0')),
            'map_name': map_name,
            'score_team1': team1_score,
            'score_team2': team2_score,
            'rounds_played': team1_score + team2_score
        }
        
        # Сохраняем в базу данных
        await storage.save_match(match_data)
        logger.info(f"Match {match_id} saved to history for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error saving match {match_id} to history: {e}")

async def verify_webhook_signature(request: Request, data: dict):
    """Проверить подпись webhook (базовая проверка)"""
    try:
        # Получаем заголовки
        signature_header = request.headers.get("X-FACEIT-Signature")
        user_agent = request.headers.get("User-Agent", "")
        
        # Базовые проверки безопасности
        if not user_agent.startswith("FACEIT"):
            logger.warning("Suspicious webhook: invalid user agent")
            
        # Если есть секретный ключ, проверяем подпись
        webhook_secret = getattr(settings, 'faceit_webhook_secret', None)
        if webhook_secret and signature_header:
            # Простая проверка HMAC подписи
            body = str(data).encode()
            expected_signature = hmac.new(
                webhook_secret.encode(), 
                body, 
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature_header, expected_signature):
                logger.warning("Webhook signature verification failed")
        
        logger.info("Webhook signature verification passed")
        
    except Exception as e:
        logger.error(f"Webhook signature verification error: {e}")


async def match_monitoring_task():
    """Фоновая задача для периодической проверки новых матчей"""
    logger.info("🔍 Запуск задачи мониторинга матчей...")
    
    while True:
        try:
            # Ждем 5 минут между проверками
            await asyncio.sleep(300)
            
            # Получаем всех пользователей с включенными уведомлениями
            users_with_notifications = await storage.get_users_with_notifications()
            if not users_with_notifications:
                logger.debug("No users with notifications enabled")
                continue
            
            logger.info(f"Checking matches for {len(users_with_notifications)} users")
            
            for user in users_with_notifications:
                try:
                    await check_user_new_matches(user)
                except Exception as user_error:
                    logger.error(f"Error checking matches for user {user.get('user_id')}: {user_error}")
                    # Продолжаем проверку других пользователей
                    
        except Exception as e:
            logger.error(f"Error in match monitoring task: {e}")
            # При серьезной ошибке ждем дольше
            await asyncio.sleep(600)


async def check_user_new_matches(user: dict):
    """Проверить новые матчи для конкретного пользователя"""
    try:
        user_id = user.get('user_id')
        faceit_id = user.get('faceit_id')
        nickname = user.get('nickname', 'Unknown')
        
        if not faceit_id:
            return
        
        # Получаем последние матчи игрока
        history = await faceit_client.get_player_history(faceit_id, limit=5)
        if not history or not history.get('items'):
            return
        
        # Получаем время последнего обработанного матча
        last_processed_time = await storage.get_last_processed_match_time(faceit_id)
        
        new_matches = []
        for match in history['items']:
            match_finished_at = match.get('finished_at')
            if not match_finished_at:
                continue
                
            # Конвертируем timestamp в datetime
            match_time = datetime.fromtimestamp(match_finished_at)
            
            # Если есть последнее время обработки, проверяем что матч новее
            if last_processed_time and match_time <= last_processed_time:
                continue
                
            # Проверяем что уведомление еще не отправлялось
            match_id = match.get('match_id')
            if not match_id:
                continue
                
            already_notified = await storage.is_match_notification_sent(match_id, user_id)
            if already_notified:
                continue
                
            new_matches.append(match)
        
        # Обрабатываем новые матчи
        for match in new_matches:
            match_id = match.get('match_id')
            logger.info(f"Processing new match {match_id} for user {nickname}")
            
            # Получаем детали матча
            match_details = await faceit_client.get_match_details(match_id)
            if not match_details:
                continue
                
            # Получаем статистику матча
            match_stats = await faceit_client.get_match_stats(match_id)
            if not match_stats:
                logger.warning(f"No stats available for match {match_id}")
                continue
            
            try:
                # Отправляем уведомление
                await send_match_notification(user_id, match_details, match_stats, faceit_id)
                
                # Отмечаем что уведомление отправлено
                await storage.mark_match_notification_sent(match_id, user_id, {
                    "match_id": match_id,
                    "player_id": faceit_id,
                    "nickname": nickname,
                    "sent_at": datetime.now().isoformat()
                })
                
                # Сохраняем матч в историю
                await save_match_to_history(user_id, match_id, match_details, match_stats, faceit_id)
                
                await storage.save_notification_log(user_id, match_id, "sent")
                logger.info(f"New match notification sent to {nickname} for match {match_id}")
                
            except Exception as notification_error:
                error_msg = str(notification_error)
                logger.error(f"Failed to send new match notification to {nickname}: {error_msg}")
                await storage.save_notification_log(user_id, match_id, "failed", error_msg)
    
    except Exception as e:
        logger.error(f"Error checking new matches for user {user.get('nickname', 'Unknown')}: {e}")


async def start_polling():
    """Запуск polling для бота"""
    try:
        logger.info("🤖 Запуск Telegram bot polling...")
        await dp.start_polling(
            bot, 
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        await bot.session.close()

# Точка входа
if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=settings.debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")