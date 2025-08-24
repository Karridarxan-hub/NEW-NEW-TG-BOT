from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any

from keyboards import get_stats_keyboard, get_main_menu_keyboard, get_stats_reply_keyboard, get_main_reply_keyboard
from storage import storage
from faceit_client import faceit_client

# Создаем логгер для обработчика
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков статистики
router = Router(name="stats_handler")

# Меню статистики игрока
@router.callback_query(F.data == "player_stats")
async def show_stats_menu(callback: CallbackQuery):
    """Показать меню статистики"""
    await callback.message.edit_text(
        "📊 Выберите тип статистики:",
        reply_markup=get_stats_keyboard()
    )
    await callback.answer()

# Общая статистика
@router.callback_query(F.data == "stats_overall")
async def show_overall_stats(callback: CallbackQuery):
    """Показать общую статистику игрока с исправленной обработкой данных"""
    user_id = callback.from_user.id
    
    try:
        # ИСПРАВЛЕНО: Используем await для async метода storage
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await callback.answer("❌ Профиль не привязан!", show_alert=True)
            return
        
        # Отправляем сообщение о загрузке
        await callback.message.edit_text("📊 Загружаем статистику...")
        
        # Получаем детали игрока и статистику параллельно
        player_details = await faceit_client.get_player_details(faceit_id)
        stats_data = await faceit_client.get_player_stats(faceit_id)
        
        if not stats_data or not player_details:
            await callback.message.edit_text(
                "❌ Не удалось загрузить статистику.\n"
                "Проверьте подключение или попробуйте позже.",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        # ИСПРАВЛЕНО: Используем улучшенный метод форматирования из faceit_client
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        
        if not formatted_stats:
            await callback.message.edit_text(
                "❌ Ошибка обработки статистики.",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        # ИСПРАВЛЕНО: Используем await для получения пользователя
        user_data = await storage.get_user(user_id)
        nickname = user_data.get('nickname', 'Unknown') if user_data else 'Unknown'
        
        # ИСПРАВЛЕНО: Убираем await - calculate_player_rating это sync метод
        # Данные уже рассчитаны в format_player_stats
        hltv_rating = formatted_stats.get('hltv_rating', 0.0)
        
        # Получаем ELO до следующего уровня
        current_elo = formatted_stats.get('elo', 0)
        current_level = formatted_stats.get('level', 0)
        elo_to_next_level = max(0, (current_level + 1) * 100 - current_elo) if current_level < 10 else 0
        
        # Формируем улучшенное сообщение с валидацией данных
        stats_message = f"""
📊 **Общая статистика игрока**

👤 **Игрок:** {nickname}
🎮 **Уровень:** {current_level} | **ELO:** {current_elo}
⬆️ **До след. уровня:** {elo_to_next_level if elo_to_next_level > 0 else 'Максимум'}
⭐ **Рейтинг игрока:** {hltv_rating:.3f}
🌍 **Регион:** {formatted_stats.get('region', 'N/A')}
✅ **Верифицирован:** {'Да' if formatted_stats.get('verified', False) else 'Нет'}

📈 **Игровые результаты:**
• **Карт сыграно:** {formatted_stats.get('matches', 0)}
• **Побед:** {formatted_stats.get('wins', 0)} ({formatted_stats.get('winrate', 0):.1f}%)
• **Лучшая серия:** {formatted_stats.get('longest_win_streak', 0)} побед

⚔️ **Убийства и смерти:**
• **Средний K/D:** {formatted_stats.get('average_kd', 0):.3f}
• **Общий K/D:** {formatted_stats.get('kd_ratio', 0):.3f} 
• **Килов за раунд:** {formatted_stats.get('kpr', 0):.3f}
• **Хедшотов:** {formatted_stats.get('headshots_avg', 0):.1f}%

💥 **Урон:**
• **ADR:** {formatted_stats.get('adr', 0):.1f}

_Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}_
"""
        
        # Отправляем статистику
        await callback.message.edit_text(
            stats_message,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in show_overall_stats for user {user_id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке статистики.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()

# Статистика по картам
@router.callback_query(F.data == "stats_maps")
async def show_maps_stats(callback: CallbackQuery):
    """Показать статистику по картам с исправленным парсингом данных"""
    user_id = callback.from_user.id
    
    try:
        # ИСПРАВЛЕНО: Используем await для async метода
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await callback.answer("❌ Профиль не привязан!", show_alert=True)
            return
        
        await callback.message.edit_text("🗺️ Загружаем статистику по картам...")
        
        # Получаем детали игрока и статистику
        player_details = await faceit_client.get_player_details(faceit_id)
        stats_data = await faceit_client.get_player_stats(faceit_id)
        
        if not stats_data or not player_details:
            await callback.message.edit_text(
                "❌ Статистика по картам недоступна",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        # ИСПРАВЛЕНО: Используем улучшенное форматирование
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        maps_stats = formatted_stats.get('maps', {})
        
        if not maps_stats:
            await callback.message.edit_text(
                "❌ Данные по картам отсутствуют.\n"
                "Возможно, игрок не играл достаточно матчей.",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        # Сортируем карты по количеству матчей
        sorted_maps = sorted(
            maps_stats.items(), 
            key=lambda x: x[1].get('matches', 0), 
            reverse=True
        )
        
        # Формируем сообщение с улучшенным форматированием
        message = "🗺️ **Статистика по картам**\n\n"
        
        for i, (map_name, map_data) in enumerate(sorted_maps[:7], 1):  # Топ-7 карт
            # Валидация данных карты
            matches = map_data.get('matches', 0)
            wins = map_data.get('wins', 0)
            winrate = map_data.get('winrate', 0)
            kd_ratio = map_data.get('kd_ratio', 0)
            adr = map_data.get('adr', 0)
            kast = map_data.get('kast', 0)
            hltv_rating = map_data.get('hltv_rating', 0)
            headshots = map_data.get('headshots', 0)
            
            # Пропускаем карты без данных
            if matches == 0:
                continue
                
            # Добавляем эмодзи для карт
            map_emojis = {
                'de_mirage': '🌋', 'de_inferno': '🏭', 'de_dust2': '🌪️',
                'de_train': '🚂', 'de_cache': '🏰', 'de_overpass': '🌊',
                'de_nuke': '🌌', 'de_vertigo': '🏔️', 'de_ancient': '🌿'
            }
            
            map_emoji = ""
            for key, emoji in map_emojis.items():
                if key.lower() in map_name.lower() or map_name.lower() in key.lower():
                    map_emoji = emoji
                    break
            
            message += f"**{map_emoji} {i}. {map_name}**\n"
            message += f"📊 Матчей: **{matches}** (🏆{wins})\n"
            message += f"📈 Winrate: **{winrate:.1f}%**\n"
            message += f"⚔️ K/D: **{kd_ratio:.3f}**\n"
            message += f"💥 ADR: **{adr:.1f}**\n"
            message += f"🎯 KAST: **{kast:.1f}%**\n"
            message += f"🎧 HS%: **{headshots:.1f}%**\n"
            message += f"⭐ Рейтинг: **{hltv_rating:.2f}**\n\n"
        
        if len(message.split('\n')) <= 3:  # Если нет данных
            message += "_Недостаточно данных для отображения статистики по картам._"
        else:
            message += f"_Показано карт: {min(len(sorted_maps), 7)} из {len(sorted_maps)}_"
        
        await callback.message.edit_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in show_maps_stats for user {user_id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке статистики по картам.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()

# Статистика за сессию
@router.callback_query(F.data == "stats_session")
async def show_session_stats(callback: CallbackQuery):
    """Показать статистику за текущую сессию с правильной логикой группировки"""
    user_id = callback.from_user.id
    
    try:
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await callback.answer("❌ Профиль не привязан!", show_alert=True)
            return
        
        await callback.message.edit_text("⏰ Загружаем статистику сессии...")
        
        # Получаем последние 100 матчей для анализа сессий
        history_data = await faceit_client.get_player_history(faceit_id, limit=100)
        
        if not history_data or 'items' not in history_data:
            await callback.message.edit_text(
                "❌ Нет данных о последних матчах",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        matches = history_data['items']
        
        # Группируем матчи в сессии (промежуток более 12 часов = новая сессия)
        sessions = []
        current_session = []
        
        for match in matches:
            finished_at = match.get('finished_at', 0)
            if not finished_at:
                continue
                
            # Нормализуем время
            if finished_at > 10**12:
                match_time = datetime.fromtimestamp(finished_at / 1000)
            else:
                match_time = datetime.fromtimestamp(finished_at)
            
            match['parsed_time'] = match_time
            
            # Если текущая сессия пуста, начинаем новую
            if not current_session:
                current_session = [match]
            else:
                # Проверяем разрыв между матчами
                last_match_time = current_session[-1]['parsed_time']
                time_diff = (last_match_time - match_time).total_seconds() / 3600  # в часах
                
                if time_diff <= 12:  # Матчи в рамках 12 часов - одна сессия
                    current_session.append(match)
                else:  # Больше 12 часов - новая сессия
                    sessions.append(current_session)
                    current_session = [match]
        
        # Добавляем последнюю сессию
        if current_session:
            sessions.append(current_session)
        
        if not sessions:
            await callback.message.edit_text(
                "⏰ **Статистика сессии**\n\n"
                "Сессии не найдены.",
                parse_mode="Markdown",
                reply_markup=get_stats_keyboard()
            )
            await callback.answer()
            return
        
        # Берем последнюю сессию (самую свежую)
        latest_session = sessions[0]
        
        # Анализируем статистику последней сессии
        session_stats = await analyze_session_stats(latest_session, faceit_id)
        
        # Формируем сообщение
        session_start = latest_session[-1]['parsed_time'].strftime('%d.%m %H:%M')
        session_end = latest_session[0]['parsed_time'].strftime('%d.%m %H:%M')
        
        message = f"""
⏰ **Статистика по сессиям**

🕒 **Период:** {session_start} - {session_end}
📊 **Результаты:**
• Матчей: {session_stats['total_matches']}
• Побед: {session_stats['wins']} ({session_stats['winrate']:.1f}%)
• Поражений: {session_stats['losses']}

📈 **Игровые показатели:**
• K/D: {session_stats['kd_ratio']:.3f}
• Рейтинг игрока: {session_stats['hltv_rating']:.3f}
• ADR: {session_stats['adr']:.1f}

📋 **Матчи сессии:**
"""
        
        # Показываем детали матчей сессии
        for i, match in enumerate(latest_session[:5], 1):
            result_emoji = session_stats['match_results'][i-1] if i-1 < len(session_stats['match_results']) else "❓"
            map_name = match.get('map', 'Unknown')
            
            # Получаем счет
            score_info = ""
            if 'results' in match and 'score' in match['results']:
                score = match['results']['score']
                score_info = f" ({score.get('faction1', 0)}:{score.get('faction2', 0)})"
            
            time_str = match['parsed_time'].strftime('%H:%M')
            message += f"\n{i}. {result_emoji} {map_name}{score_info} - {time_str}"
        
        if len(latest_session) > 5:
            message += f"\n\n_Показано 5 из {len(latest_session)} матчей сессии_"
        
        message += f"\n\n_Всего найдено сессий: {len(sessions)}_"
        
        await callback.message.edit_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in show_session_stats for user {user_id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке статистики сессии.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=get_stats_keyboard()
        )
        await callback.answer()


async def analyze_session_stats(session_matches: List[Dict], faceit_id: str) -> Dict[str, Any]:
    """Анализ статистики сессии"""
    total_matches = len(session_matches)
    wins = 0
    losses = 0
    match_results = []
    
    total_kills = 0
    total_deaths = 0
    total_damage = 0
    total_rounds = 0
    
    for match in session_matches:
        # Определяем результат матча
        player_won = faceit_client._determine_player_result(match, faceit_id)
        
        if player_won is True:
            wins += 1
            match_results.append("🏆")
        elif player_won is False:
            losses += 1
            match_results.append("❌")
        else:
            match_results.append("❓")
        
        # Получаем детальную статистику матча (если доступна)
        match_id = match.get('match_id')
        if match_id:
            try:
                match_stats = await faceit_client.get_match_stats(match_id)
                if match_stats and 'rounds' in match_stats:
                    # Ищем статистику игрока в матче
                    for round_data in match_stats['rounds']:
                        for team in round_data.get('teams', []):
                            for player in team.get('players', []):
                                if player.get('player_id') == faceit_id:
                                    stats = player.get('player_stats', {})
                                    total_kills += int(stats.get('Kills', 0))
                                    total_deaths += int(stats.get('Deaths', 0))
                                    total_damage += int(stats.get('Damage', 0))
                                    total_rounds += int(round_data.get('round_stats', {}).get('Rounds', 0))
                                    break
            except Exception as e:
                logger.debug(f"Could not get detailed stats for match {match_id}: {e}")
                continue
    
    # Рассчитываем показатели
    kd_ratio = (total_kills / total_deaths) if total_deaths > 0 else 0
    adr = (total_damage / total_rounds) if total_rounds > 0 else 0
    winrate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    # Приближенный рейтинг игрока для сессии
    if total_rounds > 0:
        kpr = total_kills / total_rounds
        dpr = total_deaths / total_rounds
        hltv_rating = max(0.0, 0.0073 * 70 + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * kpr + 0.0032 * adr + 0.1587)
    else:
        hltv_rating = 0.0
    
    return {
        'total_matches': total_matches,
        'wins': wins,
        'losses': losses,
        'winrate': winrate,
        'kd_ratio': kd_ratio,
        'adr': adr,
        'hltv_rating': hltv_rating,
        'match_results': match_results
    }

# УДАЛЕНО: Функция calculate_average_adr больше не нужна,
# так как ADR рассчитывается в faceit_client.format_player_stats()

# Вспомогательные функции для безопасной работы с данными
def safe_float(value: Any, default: float = 0.0) -> float:
    """Безопасное преобразование значения в float"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))
        except (ValueError, TypeError):
            return default
    return default

def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование значения в int"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(float(value.replace(',', '.')))
        except (ValueError, TypeError):
            return default
    return default

def validate_user_data(user_data: Optional[Dict]) -> Dict[str, Any]:
    """Валидация данных пользователя"""
    if not user_data:
        return {'nickname': 'Unknown', 'faceit_id': None}
    
    return {
        'nickname': user_data.get('nickname', 'Unknown'),
        'faceit_id': user_data.get('faceit_id'),
        'created_at': user_data.get('created_at'),
        'last_activity': user_data.get('last_activity')
    }

def format_time_ago(timestamp: Optional[Any]) -> str:
    """Форматирование времени 'назад'"""
    if not timestamp:
        return "неизвестно"
    
    try:
        if isinstance(timestamp, str):
            time_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (int, float)):
            if timestamp > 10**12:  # миллисекунды
                time_obj = datetime.fromtimestamp(timestamp / 1000)
            else:  # секунды
                time_obj = datetime.fromtimestamp(timestamp)
        else:
            return "неизвестно"
        
        delta = datetime.now() - time_obj
        
        if delta.days > 0:
            return f"{delta.days} дн. назад"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} ч. назад"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "только что"
            
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return "неизвестно"


# УДАЛЕНЫ: Reply-обработчики перенесены в main_handler.py для правильного роутинга