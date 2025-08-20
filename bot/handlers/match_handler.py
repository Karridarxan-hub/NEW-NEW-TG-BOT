from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import re

from keyboards import get_match_history_keyboard, get_main_menu_keyboard
from storage import storage
from faceit_client import faceit_client

# Создаем роутер для обработчиков матчей
router = Router(name="match_handler")

# FSM состояния для матчей
class MatchStates(StatesGroup):
    waiting_for_custom_count = State()
    waiting_for_match_url = State()

# Меню истории матчей
@router.callback_query(F.data == "match_history")
async def show_match_history_menu(callback: CallbackQuery):
    """Показать меню истории матчей"""
    await callback.message.edit_text(
        "📝 Выберите количество матчей для просмотра:",
        reply_markup=get_match_history_keyboard()
    )
    await callback.answer()

# Показать последние N матчей
@router.callback_query(F.data.startswith("history_"))
async def show_match_history(callback: CallbackQuery, state: FSMContext):
    """Показать историю матчей"""
    data = callback.data.split("_")
    
    if len(data) != 2:
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return
    
    if data[1] == "custom":
        # Запрашиваем пользовательское количество
        await callback.message.edit_text(
            "✏️ Введите количество матчей для просмотра (1-100):"
        )
        await state.set_state(MatchStates.waiting_for_custom_count)
        await callback.answer()
        return
    
    try:
        count = int(data[1])
    except ValueError:
        await callback.answer("❌ Неверное количество матчей", show_alert=True)
        return
    
    await show_matches_list(callback.message, callback.from_user.id, count)
    await callback.answer()

# Обработка пользовательского количества матчей
@router.message(MatchStates.waiting_for_custom_count)
async def process_custom_count(message: Message, state: FSMContext):
    """Обработка пользовательского количества матчей"""
    try:
        count = int(message.text.strip())
        if count < 1 or count > 100:
            await message.answer("❌ Количество должно быть от 1 до 100")
            return
    except ValueError:
        await message.answer("❌ Введите число от 1 до 100")
        return
    
    await state.clear()
    await show_matches_list(message, message.from_user.id, count)

# Показать последний матч
@router.callback_query(F.data == "last_match")
async def show_last_match(callback: CallbackQuery):
    """Показать детальную информацию о последнем матче"""
    user_id = callback.from_user.id
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.answer("❌ Профиль не привязан!", show_alert=True)
        return
    
    await callback.message.edit_text("🎮 Загружаем последний матч...")
    
    # Получаем последний матч
    matches = await faceit_client.get_player_matches(faceit_id, limit=1)
    
    if not matches or not matches.get('items'):
        await callback.message.edit_text(
            "❌ Не удалось загрузить последний матч",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    match = matches['items'][0]
    match_id = match.get('match_id')
    
    # Получаем детальную статистику матча
    match_stats = await faceit_client.get_match_stats(match_id)
    
    if not match_stats:
        await callback.message.edit_text(
            "❌ Не удалось загрузить статистику матча",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Формируем сообщение с деталями матча
    message = format_match_details(match, match_stats, faceit_id)
    
    await callback.message.edit_text(
        message,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True
    )
    await callback.answer()

# Анализ текущего матча по ссылке
@router.callback_query(F.data == "current_match_analysis")
async def request_match_url(callback: CallbackQuery, state: FSMContext):
    """Запросить ссылку на матч для анализа"""
    await callback.message.edit_text(
        "🔍 Отправьте ссылку на матч FACEIT для анализа:\n\n"
        "Пример: https://www.faceit.com/en/cs2/room/..."
    )
    await state.set_state(MatchStates.waiting_for_match_url)
    await callback.answer()

# Обработка ссылки на матч
@router.message(MatchStates.waiting_for_match_url)
async def analyze_match_url(message: Message, state: FSMContext):
    """Анализ матча по ссылке"""
    url = message.text.strip()
    
    # Извлекаем match_id из URL
    match_pattern = r'room/([a-f0-9\-]+)'
    match_result = re.search(match_pattern, url)
    
    if not match_result:
        await message.answer(
            "❌ Неверный формат ссылки.\n"
            "Отправьте ссылку вида: https://www.faceit.com/en/cs2/room/..."
        )
        return
    
    match_id = match_result.group(1)
    await state.clear()
    
    await message.answer("🔍 Анализируем матч...")
    
    # Получаем детали матча
    match_details = await faceit_client.get_match_details(match_id)
    
    if not match_details:
        await message.answer(
            "❌ Не удалось загрузить информацию о матче",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Анализируем команды
    teams = match_details.get('teams', {})
    
    message_text = "🔍 **Анализ матча**\n\n"
    
    for team_key, team_data in teams.items():
        message_text += f"**Команда {team_key}:**\n"
        
        # Получаем статистику каждого игрока
        for player in team_data.get('roster', []):
            player_id = player.get('player_id')
            player_stats = await faceit_client.get_player_stats(player_id)
            
            if player_stats:
                lifetime = player_stats.get('lifetime', {})
                kd = lifetime.get('K/D Ratio', '?')
                winrate = lifetime.get('Win Rate %', '?')
                matches = lifetime.get('Matches', '?')
                
                message_text += f"• {player.get('nickname')}: "
                message_text += f"K/D {kd}, WR {winrate}%, {matches} матчей\n"
            else:
                message_text += f"• {player.get('nickname')}: данные недоступны\n"
        
        message_text += "\n"
    
    message_text += f"[Открыть на FACEIT]({url})"
    
    await message.answer(
        message_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True
    )

# Вспомогательные функции
async def show_matches_list(message, user_id: int, count: int):
    """Показать список матчей"""
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await message.answer("❌ Профиль не привязан!")
        return
    
    # Получаем матчи
    matches = await faceit_client.get_player_matches(faceit_id, limit=count)
    
    if not matches or not matches.get('items'):
        await message.edit_text(
            "📝 История матчей пуста",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Формируем сообщение
    text = f"📝 **История последних {count} матчей:**\n\n"
    
    for i, match in enumerate(matches['items'][:count], 1):
        # Определяем результат
        teams = match.get('teams', {})
        results = match.get('results', {})
        winner = results.get('winner')
        
        # Находим команду игрока
        player_team = None
        for team_id, team_data in teams.items():
            if any(p['player_id'] == faceit_id for p in team_data.get('players', [])):
                player_team = team_id
                break
        
        # Определяем исход
        if player_team == winner:
            result_emoji = "✅"
        else:
            result_emoji = "❌"
        
        # Получаем счет
        score = results.get('score', {})
        faction1_score = score.get('faction1', 0)
        faction2_score = score.get('faction2', 0)
        
        # Получаем карту
        voting = match.get('voting', {})
        map_pick = voting.get('map', {}).get('pick', ['Unknown'])[0]
        
        # Время матча
        finished_at = match.get('finished_at', 0) / 1000
        time_str = datetime.fromtimestamp(finished_at).strftime('%d.%m %H:%M')
        
        text += f"{i}. {result_emoji} **{faction1_score}:{faction2_score}** "
        text += f"на {map_pick} | {time_str}\n"
    
    # Добавляем ссылку на FACEIT
    user_data = await storage.get_user(user_id)
    nickname = user_data.get('nickname', '')
    text += f"\n[Все матчи на FACEIT](https://www.faceit.com/en/players/{nickname}/stats/cs2)"
    
    await message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_match_history_keyboard(),
        disable_web_page_preview=True
    )

def format_match_details(match, match_stats, player_id):
    """Форматировать детальную информацию о матче"""
    # Базовая информация
    teams = match.get('teams', {})
    results = match.get('results', {})
    
    # Находим команду игрока
    player_team = None
    for team_id, team_data in teams.items():
        if any(p['player_id'] == player_id for p in team_data.get('players', [])):
            player_team = team_id
            break
    
    # Результат матча
    winner = results.get('winner')
    is_win = player_team == winner
    result_text = "Победа ✅" if is_win else "Поражение ❌"
    
    # Счет
    score = results.get('score', {})
    
    # Карта
    voting = match.get('voting', {})
    map_name = voting.get('map', {}).get('pick', ['Unknown'])[0]
    
    # Время
    finished_at = match.get('finished_at', 0) / 1000
    time_str = datetime.fromtimestamp(finished_at).strftime('%H:%M %d.%m.%Y')
    
    # Формируем сообщение
    message = f"""
🎮 **Последний матч**

📊 **Результат:** {result_text}
🗺️ **Карта:** {map_name}
⚔️ **Счет:** {score.get('faction1', 0)}:{score.get('faction2', 0)}
🕐 **Время:** {time_str}

**Статистика игроков:**
"""
    
    # Добавляем статистику игроков
    if match_stats and 'rounds' in match_stats:
        rounds = match_stats['rounds']
        
        # Группируем по командам
        for team_key in ['faction1', 'faction2']:
            message += f"\n**Команда {team_key}:**\n"
            
            team_players = rounds[0].get('teams', [])[0 if team_key == 'faction1' else 1].get('players', [])
            
            for player in team_players:
                nickname = player.get('nickname', 'Unknown')
                kills = player.get('player_stats', {}).get('Kills', 0)
                deaths = player.get('player_stats', {}).get('Deaths', 0)
                assists = player.get('player_stats', {}).get('Assists', 0)
                kd = kills / deaths if deaths > 0 else kills
                
                message += f"• {nickname}: {kills}/{deaths}/{assists} (K/D: {kd:.2f})\n"
    
    # Ссылка на матч
    match_id = match.get('match_id')
    message += f"\n[Подробнее на FACEIT](https://www.faceit.com/en/cs2/room/{match_id})"
    
    return message