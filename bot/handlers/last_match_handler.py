from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Dict, List, Optional, Any
import logging

from storage import storage
from faceit_client import faceit_client


# Создаем роутер для обработчика последнего матча
router = Router(name="last_match_handler")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "last_match")
async def show_last_match(callback: CallbackQuery):
    """Показать информацию о последнем матче игрока"""
    user_id = callback.from_user.id
    
    try:
        # Получаем FACEIT ID пользователя
        faceit_id = await storage.get_user_faceit_id(user_id)
        if not faceit_id:
            await callback.message.edit_text(
                "❌ Профиль FACEIT не найден.\nИспользуйте /start для привязки профиля.",
                reply_markup=_get_back_keyboard()
            )
            await callback.answer()
            return

        await callback.message.edit_text("🔄 Загрузка информации о последнем матче...")

        # Получаем последний матч из истории
        history = await faceit_client.get_player_history(faceit_id, limit=1)
        if not history or not history.get('items'):
            await callback.message.edit_text(
                "❌ История матчей не найдена.",
                reply_markup=_get_back_keyboard()
            )
            await callback.answer()
            return

        last_match = history['items'][0]
        match_id = last_match['match_id']

        # Получаем детальную статистику матча
        match_stats = await faceit_client.get_match_stats(match_id)
        if not match_stats:
            await callback.message.edit_text(
                "❌ Не удалось получить статистику матча.",
                reply_markup=_get_back_keyboard()
            )
            await callback.answer()
            return

        # Формируем сообщение с информацией о матче
        message_text = await _format_match_message(last_match, match_stats, faceit_id)
        
        # Создаем клавиатуру с ссылкой на матч
        keyboard = _create_match_keyboard(last_match)

        await callback.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in show_last_match: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении информации о матче.",
            reply_markup=_get_back_keyboard()
        )
    
    await callback.answer()


async def _format_match_message(match_data: Dict, match_stats: Dict, user_faceit_id: str) -> str:
    """Форматирует сообщение с информацией о матче"""
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
        user_team = _get_user_team(match_stats, user_faceit_id)
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
        user_stats = _get_user_stats(match_stats, user_faceit_id)
        
        # Формируем первые строки сообщения
        message_lines = [
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

        message_lines.append("")

        # Добавляем информацию о командах
        teams_info = _format_teams_info(match_stats, user_faceit_id)
        message_lines.extend(teams_info)

        return "\n".join(message_lines)

    except Exception as e:
        logger.error(f"Error formatting match message: {e}")
        return "❌ Ошибка при формировании сообщения о матче"


def _get_user_team(match_stats: Dict, user_faceit_id: str) -> Optional[str]:
    """Определяет в какой команде играл пользователь"""
    try:
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


def _get_user_stats(match_stats: Dict, user_faceit_id: str) -> Optional[Dict]:
    """Получает статистику пользователя из матча"""
    try:
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


def _format_teams_info(match_stats: Dict, user_faceit_id: str) -> List[str]:
    """Форматирует информацию о командах с игроками"""
    try:
        lines = []
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return ["❌ Информация о командах недоступна"]
            
        round_stats = rounds[0]
        teams = round_stats.get('teams', [])
        
        for i, team in enumerate(teams):
            team_name = team.get('team_stats', {}).get('Team', f'Команда {i+1}')
            lines.append(f"👥 <b>{team_name}:</b>")
            
            # Получаем и сортируем игроков по количеству киллов
            players = team.get('players', [])
            sorted_players = sorted(
                players, 
                key=lambda p: int(p.get('player_stats', {}).get('Kills', '0')), 
                reverse=True
            )
            
            for player in sorted_players:
                nickname = player.get('nickname', 'Unknown')
                stats = player.get('player_stats', {})
                player_id = player.get('player_id', '')
                
                kills = stats.get('Kills', '0')
                deaths = stats.get('Deaths', '0')
                assists = stats.get('Assists', '0')
                adr = stats.get('ADR', '0')
                kast = stats.get('KAST', '0')
                hltv_rating = faceit_client.calculate_hltv_rating(stats)
                
                # Выделяем пользователя жирным текстом
                if player_id == user_faceit_id:
                    player_line = f"<b>• {nickname}</b> ({kills}-{deaths}-{assists}, ADR: {adr}, KAST: {kast}%, HLTV 2.1: {hltv_rating:.2f})"
                else:
                    player_line = f"• {nickname} ({kills}-{deaths}-{assists}, ADR: {adr}, KAST: {kast}%, HLTV 2.1: {hltv_rating:.2f})"
                
                lines.append(player_line)
            
            lines.append("")  # Пустая строка между командами
        
        return lines

    except Exception as e:
        logger.error(f"Error formatting teams info: {e}")
        return ["❌ Ошибка при получении информации о командах"]


def _create_match_keyboard(match_data: Dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками для матча"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка для просмотра матча на FACEIT
    match_id = match_data.get('match_id', '')
    if match_id:
        faceit_url = f"https://www.faceit.com/en/cs2/room/{match_id}"
        builder.button(text="🔗 Смотреть матч на FACEIT", url=faceit_url)
    
    # Кнопка назад в главное меню
    builder.button(text="◀️ Назад в главное меню", callback_data="back_to_main")
    
    builder.adjust(1, 1)  # Каждая кнопка на отдельной строке
    return builder.as_markup()


def _get_back_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой возврата"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_main")]
        ]
    )