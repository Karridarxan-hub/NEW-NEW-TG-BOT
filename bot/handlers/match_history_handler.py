from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List, Dict, Any, Optional
import logging

from keyboards import get_match_history_keyboard, get_back_to_main_keyboard, get_back_to_history_keyboard
from storage import storage
from faceit_client import faceit_client

# Создаем роутер для обработчиков истории матчей
router = Router(name="match_history_handler")

# Настройка логирования
logger = logging.getLogger(__name__)

# FSM состояния для истории матчей
class MatchHistoryStates(StatesGroup):
    waiting_for_custom_count = State()

# Обработчик открытия меню истории матчей
@router.callback_query(F.data == "match_history")
async def show_match_history_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню истории матчей"""
    await state.clear()
    
    await callback.message.edit_text(
        "📝 <b>История матчей</b>\n\n"
        "Выберите количество матчей для просмотра:",
        reply_markup=get_match_history_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики для фиксированного количества матчей
@router.callback_query(F.data.in_(["history_5", "history_10", "history_30"]))
async def show_match_history(callback: CallbackQuery, state: FSMContext):
    """Показать историю матчей для фиксированного количества"""
    await state.clear()
    
    # Извлекаем количество матчей из callback_data
    match_count = int(callback.data.split("_")[1])
    
    user_id = callback.from_user.id
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль FACEIT не привязан!\n"
            "Используйте /start для привязки профиля.",
            reply_markup=get_back_to_history_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"🔄 Загружаю последние {match_count} матчей...",
        reply_markup=None
    )
    
    try:
        # Получаем историю матчей
        history_data = await faceit_client.get_player_history(faceit_id, limit=match_count)
        
        if not history_data:
            await callback.message.edit_text(
                "❌ Не удалось загрузить историю матчей.\n"
                "FACEIT API временно недоступен, попробуйте позже.",
                reply_markup=get_match_history_keyboard()
            )
            await callback.answer()
            return
        
        if not history_data.get("items"):
            await callback.message.edit_text(
                "📭 История матчей пуста.\n"
                "Возможно, у игрока нет матчей в CS2 или данные еще не обновились.",
                reply_markup=get_match_history_keyboard()
            )
            await callback.answer()
            return
        
        matches = history_data["items"]
        
        # Формируем сообщение с историей
        message_text = await format_match_history(matches, faceit_id, match_count)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=get_match_history_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории матчей: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке истории матчей.",
            reply_markup=get_match_history_keyboard()
        )
    
    await callback.answer()

# Обработчик для ввода пользовательского количества матчей
@router.callback_query(F.data == "history_custom")
async def ask_custom_match_count(callback: CallbackQuery, state: FSMContext):
    """Запросить пользовательское количество матчей"""
    await state.set_state(MatchHistoryStates.waiting_for_custom_count)
    
    await callback.message.edit_text(
        "✏️ <b>Ввод количества матчей</b>\n\n"
        "Введите количество матчей для просмотра (от 1 до 100):",
        reply_markup=get_back_to_history_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик ввода пользовательского количества
@router.message(MatchHistoryStates.waiting_for_custom_count)
async def process_custom_match_count(message: Message, state: FSMContext):
    """Обработать введенное количество матчей"""
    try:
        match_count = int(message.text.strip())
        
        if not 1 <= match_count <= 100:
            await message.answer(
                "❌ Количество матчей должно быть от 1 до 100.\n"
                "Попробуйте еще раз:"
            )
            return
        
        await state.clear()
        
        user_id = message.from_user.id
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_back_to_history_keyboard()
            )
            return
        
        loading_msg = await message.answer(
            f"🔄 Загружаю последние {match_count} матчей..."
        )
        
        try:
            # Получаем историю матчей
            history_data = await faceit_client.get_player_history(faceit_id, limit=match_count)
            
            if not history_data:
                await loading_msg.edit_text(
                    "❌ Не удалось загрузить историю матчей.\n"
                    "FACEIT API временно недоступен, попробуйте позже.",
                    reply_markup=get_match_history_keyboard()
                )
                return
            
            if not history_data.get("items"):
                await loading_msg.edit_text(
                    "📭 История матчей пуста.\n"
                    "Возможно, у игрока нет матчей в CS2 или данные еще не обновились.",
                    reply_markup=get_match_history_keyboard()
                )
                return
            
            matches = history_data["items"]
            
            # Формируем сообщение с историей
            message_text = await format_match_history(matches, faceit_id, match_count)
            
            await loading_msg.edit_text(
                message_text,
                reply_markup=get_match_history_keyboard(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории матчей: {e}")
            await loading_msg.edit_text(
                "❌ Произошла ошибка при загрузке истории матчей.",
                reply_markup=get_match_history_keyboard()
            )
    
    except ValueError:
        await message.answer(
            "❌ Введите корректное число от 1 до 100.\n"
            "Попробуйте еще раз:"
        )

async def format_match_history(matches: List[Dict[str, Any]], player_faceit_id: str, match_count: int) -> str:
    """Форматировать историю матчей"""
    message_text = f"📝 <b>Последние {match_count} матчей</b>\n\n"
    
    for i, match in enumerate(matches, 1):
        try:
            match_id = match["match_id"]
            
            # Получаем детальную статистику матча
            match_stats = await faceit_client.get_match_stats(match_id)
            
            if not match_stats:
                continue
            
            # Определяем результат матча для игрока
            player_result = determine_player_result(match_stats, player_faceit_id)
            
            if not player_result:
                continue
            
            # Форматируем информацию о матче
            match_info = format_single_match(match, match_stats, player_result, i)
            message_text += match_info + "\n"
            
        except Exception as e:
            logger.error(f"Ошибка при обработке матча {match.get('match_id', 'unknown')}: {e}")
            continue
    
    if len(matches) == 0:
        message_text += "❌ Матчи не найдены."
    
    return message_text

def determine_player_result(match_stats: Dict[str, Any], player_faceit_id: str) -> Optional[Dict[str, Any]]:
    """Определить результат матча для конкретного игрока"""
    try:
        rounds = match_stats.get("rounds", [])
        if not rounds:
            return None
        
        # Берем данные из первого раунда (общая статистика матча)
        round_stats = rounds[0]
        teams = round_stats.get("teams", [])
        
        player_team = None
        enemy_team = None
        player_stats = None
        
        # Находим команду игрока и его статистику
        for team in teams:
            players = team.get("players", [])
            for player in players:
                if player.get("player_id") == player_faceit_id:
                    player_team = team
                    player_stats = player.get("player_stats", {})
                    break
            
            if player_team:
                # Находим вражескую команду
                enemy_team = next((t for t in teams if t != player_team), None)
                break
        
        if not player_team or not enemy_team or not player_stats:
            return None
        
        # Определяем победу/поражение
        player_score = int(player_team.get("team_stats", {}).get("Final Score", "0"))
        enemy_score = int(enemy_team.get("team_stats", {}).get("Final Score", "0"))
        
        won = player_score > enemy_score
        
        return {
            "won": won,
            "player_team": player_team,
            "enemy_team": enemy_team,
            "player_stats": player_stats,
            "player_score": player_score,
            "enemy_score": enemy_score
        }
        
    except Exception as e:
        logger.error(f"Ошибка при определении результата игрока: {e}")
        return None

def format_single_match(match: Dict[str, Any], match_stats: Dict[str, Any], player_result: Dict[str, Any], match_number: int) -> str:
    """Форматировать информацию об одном матче"""
    try:
        # Основная информация о матче
        match_id = match["match_id"]
        
        # Получаем названия команд
        team1_name = player_result["player_team"].get("team_stats", {}).get("Team", "Team 1")
        team2_name = player_result["enemy_team"].get("team_stats", {}).get("Team", "Team 2")
        
        # Счет
        team1_score = player_result["player_score"]
        team2_score = player_result["enemy_score"]
        
        # Статус (победа/поражение)
        status_emoji = "🏆" if player_result["won"] else "💔"
        
        # Карта
        map_name = match_stats.get("rounds", [{}])[0].get("round_stats", {}).get("Map", "Unknown")
        
        # Статистика игрока
        player_stats = player_result["player_stats"]
        kills = player_stats.get("Kills", "0")
        deaths = player_stats.get("Deaths", "0")
        assists = player_stats.get("Assists", "0")
        
        # K/D ratio
        try:
            kd_ratio = round(float(kills) / max(float(deaths), 1), 2)
        except:
            kd_ratio = "0.00"
        
        # ADR (Average Damage per Round)
        adr = player_stats.get("ADR", "0")
        
        # HLTV Rating 2.1 (если доступен)
        hltv_rating = player_stats.get("K/D Ratio", kd_ratio)  # Используем K/D как fallback
        
        # Формируем текст матча
        match_text = (
            f"{match_number}. {status_emoji} <b>{team1_name}</b> {team1_score} - {team2_score} <b>{team2_name}</b>\n"
            f"🗺️ <i>{map_name}</i>\n"
            f"🔗 <a href=\"https://www.faceit.com/en/cs2/room/{match_id}\">Смотреть матч на FACEIT</a>\n"
            f"📊 {kills}-{deaths}-{assists} | K/D: {kd_ratio} | ADR: {adr} | HLTV: {hltv_rating}"
        )
        
        return match_text
        
    except Exception as e:
        logger.error(f"Ошибка при форматировании матча: {e}")
        return f"{match_number}. ❌ Ошибка обработки матча"

# Обработчик возврата назад в меню истории
@router.callback_query(F.data == "back_to_history")
async def back_to_history_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню истории матчей"""
    await state.clear()
    await show_match_history_menu(callback, state)