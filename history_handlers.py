from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import *
from faceit_client import faceit_client
from storage import storage
from match_handlers import format_match_status, calculate_player_stats_from_match


class HistoryStates(StatesGroup):
    waiting_for_custom_count = State()


router = Router()


@router.callback_query(F.data == "match_history")
async def match_history_menu(callback: CallbackQuery):
    """Меню истории матчей"""
    await callback.message.edit_text(
        "📝 История матчей\n\nВыберите количество матчей для просмотра:",
        reply_markup=get_match_history_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("history_"))
async def show_match_history(callback: CallbackQuery, state: FSMContext):
    """Показать историю матчей"""
    user_id = callback.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль не привязан. Используйте /start для привязки профиля.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    action = callback.data.split("_")[1]
    
    if action == "custom":
        await callback.message.edit_text(
            "✏️ Введите количество матчей (от 1 до 100):",
            reply_markup=get_back_keyboard("match_history")
        )
        await state.set_state(HistoryStates.waiting_for_custom_count)
        await callback.answer()
        return
    
    # Определяем количество матчей
    match_counts = {"5": 5, "10": 10, "30": 30}
    match_count = match_counts.get(action, 10)
    
    await process_match_history_request(callback, faceit_id, match_count)


@router.message(HistoryStates.waiting_for_custom_count)
async def process_custom_match_count(message: Message, state: FSMContext):
    """Обработка пользовательского количества матчей"""
    try:
        count = int(message.text.strip())
        if count < 1 or count > 100:
            await message.answer("❌ Количество должно быть от 1 до 100. Попробуйте еще раз:")
            return
        
        user_id = message.from_user.id
        faceit_id = storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль не привязан. Используйте /start для привязки профиля.",
                reply_markup=get_back_to_main_keyboard()
            )
            await state.clear()
            return
        
        # Создаем фиктивный callback для совместимости
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
            
            async def answer(self):
                """Фиктивный ответ для совместимости"""
                return None
        
        fake_callback = FakeCallback(message)
        await process_match_history_request(fake_callback, faceit_id, count)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректное число от 1 до 100:")


async def process_match_history_request(callback, faceit_id: str, match_count: int):
    """Обработать запрос истории матчей"""
    await callback.message.edit_text("🔄 Загружаем историю матчей...")
    
    # Получаем историю матчей
    matches_data = await faceit_client.get_player_matches(faceit_id, limit=match_count)
    
    if not matches_data or not matches_data.get('items'):
        await callback.message.edit_text(
            "❌ Не удалось загрузить историю матчей. Попробуйте позже.",
            reply_markup=get_back_keyboard("match_history")
        )
        return
    
    matches = matches_data['items']
    
    if not matches:
        await callback.message.edit_text(
            "❌ Матчи не найдены.",
            reply_markup=get_back_keyboard("match_history")
        )
        return
    
    # Обрабатываем каждый матч
    processed_matches = []
    
    for i, match in enumerate(matches):
        if i >= match_count:  # Дополнительная защита
            break
            
        try:
            match_id = match['match_id']
            
            # Получаем детали и статистику матча
            match_details = await faceit_client.get_match_details(match_id)
            match_stats = await faceit_client.get_match_stats(match_id)
            
            if not match_details or not match_stats:
                continue
            
            # Обрабатываем данные матча
            processed_match = await process_single_match(match_details, match_stats, faceit_id)
            
            if processed_match:
                processed_matches.append(processed_match)
                
        except Exception as e:
            print(f"Error processing match {match.get('match_id', 'unknown')}: {e}")
            continue
    
    if not processed_matches:
        await callback.message.edit_text(
            "❌ Не удалось обработать матчи. Попробуйте позже.",
            reply_markup=get_back_keyboard("match_history")
        )
        return
    
    # Формируем текст с историей
    history_text = f"📝 **История матчей** (последние {len(processed_matches)})\n\n"
    
    for i, match in enumerate(processed_matches, 1):
        status_emoji = format_match_status(match['status'])
        result_emoji = "🏆" if match['won'] else "💀"
        
        history_text += f"**{i}.** {status_emoji} {result_emoji} {match['team_scores']}\n"
        history_text += f"🗺️ {match['map']} | [FACEIT]({match['faceit_url']})\n"
        history_text += f"💀 {match['stats']['kills']}/{match['stats']['deaths']}/{match['stats']['assists']} | "
        history_text += f"K/D: {match['stats']['kd_ratio']} | ADR: {match['stats']['adr']} | "
        history_text += f"HLTV: {match['stats']['hltv_rating']}\n\n"
    
    # Добавляем общую статистику
    total_matches = len(processed_matches)
    wins = sum(1 for match in processed_matches if match['won'])
    winrate = round((wins / total_matches) * 100, 1) if total_matches > 0 else 0
    
    avg_kills = round(sum(match['stats']['kills'] for match in processed_matches) / total_matches, 1)
    avg_deaths = round(sum(match['stats']['deaths'] for match in processed_matches) / total_matches, 1)
    avg_assists = round(sum(match['stats']['assists'] for match in processed_matches) / total_matches, 1)
    avg_kd = round(sum(match['stats']['kd_ratio'] for match in processed_matches) / total_matches, 2)
    avg_adr = round(sum(match['stats']['adr'] for match in processed_matches) / total_matches, 1)
    avg_hltv = round(sum(match['stats']['hltv_rating'] for match in processed_matches) / total_matches, 2)
    
    summary_text = f"""📊 **Общая статистика:**
🎮 **Матчи:** {total_matches}
🏆 **Победы:** {wins} ({winrate}%)
💀 **Средние K/D/A:** {avg_kills}/{avg_deaths}/{avg_assists}
⚔️ **Средний K/D:** {avg_kd}
💥 **Средний ADR:** {avg_adr}
🎯 **Средний HLTV:** {avg_hltv}"""
    
    # Отправляем в два сообщения, если слишком длинное
    if len(history_text) > 3500:
        await callback.message.edit_text(
            history_text[:3500] + "...",
            reply_markup=get_back_keyboard("match_history"),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        await callback.message.answer(
            summary_text,
            reply_markup=get_back_keyboard("match_history"),
            parse_mode="Markdown"
        )
    else:
        full_text = history_text + summary_text
        await callback.message.edit_text(
            full_text,
            reply_markup=get_back_keyboard("match_history"),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    
    await callback.answer()


async def process_single_match(match_details: dict, match_stats: dict, player_faceit_id: str) -> dict:
    """Обработать один матч"""
    try:
        # Основная информация о матче
        match_id = match_details['match_id']
        status = match_details.get('status', 'unknown')
        map_name = match_details.get('voting', {}).get('map', {}).get('pick', ['Unknown'])[0]
        
        # Команды и счет
        teams = match_details.get('teams', {})
        team1 = teams.get('faction1', {})
        team2 = teams.get('faction2', {})
        
        # Ссылка на FACEIT
        faceit_url = f"https://www.faceit.com/en/csgo/room/{match_id}"
        
        # Получаем статистику игрока
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return None
        
        round_stats = rounds[0]
        teams_stats = round_stats.get('teams', [])
        
        player_stats = None
        player_team_stats = None
        enemy_team_stats = None
        
        # Находим нашего игрока
        for team_stats in teams_stats:
            for player in team_stats.get('players', []):
                if player.get('player_id') == player_faceit_id:
                    player_stats = player
                    player_team_stats = team_stats
                    enemy_team_stats = next(
                        (team for team in teams_stats if team != team_stats), 
                        None
                    )
                    break
            if player_stats:
                break
        
        if not player_stats:
            return None
        
        # Рассчитываем статистику
        calculated_stats = calculate_player_stats_from_match(player_stats)
        
        # Определяем результат
        player_team_score = player_team_stats.get('stats', {}).get('Final Score', '0')
        enemy_team_score = enemy_team_stats.get('stats', {}).get('Final Score', '0') if enemy_team_stats else '0'
        
        try:
            won = int(player_team_score) > int(enemy_team_score)
        except:
            won = False
        
        # Формируем счет команд
        team1_name = team1.get('name', 'Team 1')[:10]  # Короткие названия
        team2_name = team2.get('name', 'Team 2')[:10]
        team_scores = f"{team1_name} {player_team_score}:{enemy_team_score} {team2_name}"
        
        return {
            'match_id': match_id,
            'status': status,
            'map': map_name,
            'won': won,
            'team_scores': team_scores,
            'faceit_url': faceit_url,
            'stats': calculated_stats
        }
        
    except Exception as e:
        print(f"Error processing single match: {e}")
        return None