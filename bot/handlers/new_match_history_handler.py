from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List, Dict, Any, Optional
import logging

from keyboards import get_match_history_keyboard, get_back_to_main_keyboard
from storage import storage
from faceit_client import faceit_client

# Создаем роутер для нового обработчика истории матчей
router = Router(name="new_match_history_handler")

# Настройка логирования
logger = logging.getLogger(__name__)

# FSM состояния для истории матчей
class NewMatchHistoryStates(StatesGroup):
    waiting_for_custom_count = State()

# Обработчик главного меню истории матчей
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

# Обработчики для фиксированного количества матчей (5, 10, 30)
@router.callback_query(F.data.in_(["history_5", "history_10", "history_30"]))
async def show_match_history(callback: CallbackQuery, state: FSMContext):
    """Показать историю матчей для фиксированного количества"""
    await state.clear()
    
    # Извлекаем количество матчей из callback_data
    match_count = int(callback.data.split("_")[1])
    
    await process_match_history_request(callback, match_count)

# Обработчик для ввода пользовательского количества матчей
@router.callback_query(F.data == "history_custom")
async def ask_custom_match_count(callback: CallbackQuery, state: FSMContext):
    """Запросить пользовательское количество матчей"""
    await state.set_state(NewMatchHistoryStates.waiting_for_custom_count)
    
    await callback.message.edit_text(
        "✏️ <b>Ввод количества матчей</b>\n\n"
        "Введите количество матчей для просмотра (от 1 до 100):",
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик ввода пользовательского количества
@router.message(NewMatchHistoryStates.waiting_for_custom_count)
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
        
        # Создаем псевдо-callback для обработки
        await process_match_history_request_from_message(message, match_count)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число от 1 до 100.\n"
            "Попробуйте еще раз:"
        )

async def process_match_history_request(callback: CallbackQuery, match_count: int):
    """Обработать запрос истории матчей через callback"""
    user_id = callback.from_user.id
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль FACEIT не привязан!\n"
            "Используйте /start для привязки профиля.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🔄 Загружаю последние {match_count} матчей...",
        reply_markup=None
    )

    try:
        # Получаем историю матчей
        logger.info(f"Запрашиваем историю для игрока {faceit_id}, лимит: {match_count}")
        history_data = await faceit_client.get_player_history(faceit_id, limit=match_count)
        
        logger.info(f"Получены данные от API: {bool(history_data)}")
        if history_data:
            logger.info(f"Количество матчей в ответе: {len(history_data.get('items', []))}")
        
        if not history_data or not history_data.get("items"):
            logger.warning(f"История матчей пуста для игрока {faceit_id}")
            await callback.message.edit_text(
                "📭 История матчей пуста.\n"
                "Возможно, у игрока нет матчей в CS2 или данные еще не обновились.",
                reply_markup=get_match_history_keyboard()
            )
            await callback.answer()
            return

        matches = history_data["items"]
        logger.info(f"Обрабатываем {len(matches)} матчей")
        
        # Формируем сообщение с историей в новом формате
        message_text = await format_new_match_history(matches, faceit_id, match_count)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=None,
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

async def process_match_history_request_from_message(message: Message, match_count: int):
    """Обработать запрос истории матчей через message (для пользовательского ввода)"""
    user_id = message.from_user.id
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await message.answer(
            "❌ Профиль FACEIT не привязан!\n"
            "Используйте /start для привязки профиля.",
            reply_markup=get_back_to_main_keyboard()
        )
        return

    loading_msg = await message.answer(
        f"🔄 Загружаю последние {match_count} матчей..."
    )

    try:
        # Получаем историю матчей
        history_data = await faceit_client.get_player_history(faceit_id, limit=match_count)
        
        if not history_data or not history_data.get("items"):
            await loading_msg.edit_text(
                "📭 История матчей пуста.\n"
                "Возможно, у игрока нет матчей в CS2 или данные еще не обновились.",
                reply_markup=get_match_history_keyboard()
            )
            return

        matches = history_data["items"]
        
        # Формируем сообщение с историей в новом формате
        message_text = await format_new_match_history(matches, faceit_id, match_count)
        
        await loading_msg.edit_text(
            message_text,
            reply_markup=None,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории матчей: {e}")
        await loading_msg.edit_text(
            "❌ Произошла ошибка при загрузке истории матчей.",
            reply_markup=get_match_history_keyboard()
        )

async def format_new_match_history(matches: List[Dict[str, Any]], player_faceit_id: str, match_count: int) -> str:
    """Форматировать историю матчей в новом формате"""
    logger.info(f"Форматируем {len(matches)} матчей для игрока {player_faceit_id}")
    message_text = ""
    processed_matches = 0
    
    for i, match in enumerate(matches, 1):
        try:
            match_id = match["match_id"]
            logger.info(f"Обрабатываем матч {i}/{len(matches)}: {match_id}")
            
            # Получаем детальную статистику матча
            match_stats = await faceit_client.get_match_stats(match_id)
            
            if not match_stats:
                logger.warning(f"Не удалось получить статистику для матча {match_id}")
                continue

            # Определяем результат матча для игрока
            player_result = determine_player_result(match_stats, player_faceit_id)
            
            if not player_result:
                logger.warning(f"Не удалось определить результат игрока для матча {match_id}")
                continue

            # Форматируем информацию о матче в новом формате
            match_info = format_single_match_new(match, match_stats, player_result, i)
            message_text += match_info + "\n\n"
            processed_matches += 1
            logger.info(f"Матч {match_id} успешно обработан")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке матча {match.get('match_id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Обработано {processed_matches} из {len(matches)} матчей")
    
    if processed_matches == 0:
        message_text = "❌ Не удалось обработать ни одного матча. Попробуйте позже."
    
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
        player_nickname = None
        
        # Находим команду игрока и его статистику
        for team in teams:
            players = team.get("players", [])
            for player in players:
                if player.get("player_id") == player_faceit_id:
                    player_team = team
                    player_stats = player.get("player_stats", {})
                    player_nickname = player.get("nickname", "Unknown")
                    logger.info(f"Игрок {player_nickname} найден в команде {team.get('team_stats', {}).get('Team', 'Unknown')}")
                    break
            
            if player_team:
                # Находим вражескую команду
                enemy_team = next((t for t in teams if t != player_team), None)
                break
        
        if not player_team or not enemy_team or not player_stats:
            logger.warning(f"Не удалось найти игрока {player_faceit_id} в матче")
            return None
        
        # Определяем победу/поражение
        player_score = int(player_team.get("team_stats", {}).get("Final Score", "0"))
        enemy_score = int(enemy_team.get("team_stats", {}).get("Final Score", "0"))
        
        won = player_score > enemy_score
        
        player_team_name = player_team.get("team_stats", {}).get("Team", "Unknown")
        enemy_team_name = enemy_team.get("team_stats", {}).get("Team", "Unknown")
        logger.info(f"Матч: {player_team_name} {player_score} - {enemy_score} {enemy_team_name}. Игрок {'выиграл' if won else 'проиграл'}")
        
        return {
            "won": won,
            "player_team": player_team,
            "enemy_team": enemy_team,
            "player_stats": player_stats,
            "player_score": player_score,
            "enemy_score": enemy_score,
            "player_nickname": player_nickname
        }
        
    except Exception as e:
        logger.error(f"Ошибка при определении результата игрока: {e}")
        return None

def format_single_match_new(match: Dict[str, Any], match_stats: Dict[str, Any], player_result: Dict[str, Any], match_number: int) -> str:
    """Форматировать информацию об одном матче в новом формате"""
    try:
        # Получаем названия команд
        player_team_name = player_result["player_team"].get("team_stats", {}).get("Team", "team_Unknown")
        enemy_team_name = player_result["enemy_team"].get("team_stats", {}).get("Team", "team_Unknown")
        
        # Счет
        player_score = player_result["player_score"]
        enemy_score = player_result["enemy_score"]
        
        # Статус (победа/поражение)
        status_emoji = "🏆" if player_result["won"] else "❌"
        
        # Получаем никнейм игрока для отображения
        player_nickname = player_result.get("player_nickname", "Unknown")
        
        # Карта
        map_name = match_stats.get("rounds", [{}])[0].get("round_stats", {}).get("Map", "Unknown")
        if map_name != "Unknown":
            map_name = f"de_{map_name.lower()}" if not map_name.startswith("de_") else map_name
        
        # Статистика игрока
        player_stats = player_result["player_stats"]
        kills = int(player_stats.get("Kills", "0"))
        deaths = int(player_stats.get("Deaths", "0"))
        assists = int(player_stats.get("Assists", "0"))
        
        # K/D ratio с 2 знаками после запятой
        try:
            kd_ratio = round(float(kills) / max(float(deaths), 1), 2)
        except:
            kd_ratio = 0.00
        
        # ADR (Average Damage per Round)
        try:
            adr = float(player_stats.get("ADR", "0"))
        except:
            adr = 0.0
        
        # Рейтинг игрока (правильный расчет)
        try:
            hltv_rating = faceit_client.calculate_hltv_rating(player_stats)  # Рейтинг игрока
        except:
            hltv_rating = 0.00
        
        # Формируем текст в новом формате
        # 1. 🏆 team_Geun-Hee 13 - 4 team_kuv1ch
        # 🗺️ de_nuke  
        # 📊 16-15-5 | K/D: 1.07 | ADR: 97.3
        # 🔗 [Смотреть матч на FACEIT](https://www.faceit.com/ru/cs2/room/MATCH_ID)
        
        # Получаем match_id для ссылки
        match_id = match.get("match_id", "")
        faceit_url = f"https://www.faceit.com/ru/cs2/room/{match_id}"
        
        match_text = (
            f"{match_number}. <b>{player_team_name}</b> {status_emoji} {player_score} - {enemy_score} {enemy_team_name}\n"
            f"🗺️ {map_name}\n"
            f"📊 {kills}-{deaths}-{assists} | K/D: {kd_ratio:.2f} | ADR: {adr:.1f}\n"
            f"🔗 <a href='{faceit_url}'>Смотреть матч на FACEIT</a>"
        )
        
        return match_text
        
    except Exception as e:
        logger.error(f"Ошибка при форматировании матча: {e}")
        return f"{match_number}. ❌ Ошибка обработки матча"

# Reply-обработчики для кнопок внизу экрана
@router.message(F.text == "5 матчей")
async def handle_history_5_reply(message: Message, state: FSMContext):
    """Reply-обработчик для 5 матчей"""
    logger.warning(f"✅ SUCCESS: NEW ROUTER обрабатывает '5 матчей' от пользователя {message.from_user.id}")
    await process_match_history_request_from_message(message, 5)

@router.message(F.text == "10 матчей")
async def handle_history_10_reply(message: Message, state: FSMContext):
    """Reply-обработчик для 10 матчей"""
    logger.info(f"Обрабатываем reply '10 матчей' от пользователя {message.from_user.id}")
    await process_match_history_request_from_message(message, 10)

@router.message(F.text == "30 матчей")
async def handle_history_30_reply(message: Message, state: FSMContext):
    """Reply-обработчик для 30 матчей"""
    logger.info(f"Обрабатываем reply '30 матчей' от пользователя {message.from_user.id}")
    await process_match_history_request_from_message(message, 30)

# Обработчик возврата назад в главное меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    from keyboards import get_main_menu_keyboard
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()