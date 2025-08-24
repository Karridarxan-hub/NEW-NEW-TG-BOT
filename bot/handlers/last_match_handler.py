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
        team1_name = teams.get('faction1', {}).get('name', 'Неизвестная команда')
        team2_name = teams.get('faction2', {}).get('name', 'Неизвестная команда')
        
        # Попробуем получить имена команд из match_stats если они не найдены
        if team1_name == 'Неизвестная команда' or team2_name == 'Неизвестная команда':
            try:
                rounds = match_stats.get('rounds', [])
                if rounds:
                    teams_data = rounds[0].get('teams', [])
                    if len(teams_data) >= 2:
                        team1_stats_name = teams_data[0].get('team_stats', {}).get('Team', '')
                        team2_stats_name = teams_data[1].get('team_stats', {}).get('Team', '')
                        if team1_stats_name and team1_name == 'Неизвестная команда':
                            team1_name = team1_stats_name
                        if team2_stats_name and team2_name == 'Неизвестная команда':
                            team2_name = team2_stats_name
            except Exception as e:
                logger.error(f"Error getting team names from match_stats: {e}")
        
        # Получаем правильный счёт раундов из match_stats
        team1_score, team2_score = _get_round_scores(match_stats)
        if team1_score is None or team2_score is None:
            # Fallback к счёту матчей если нет данных о раундах
            team1_score = match_result.get('score', {}).get('faction1', 0)
            team2_score = match_result.get('score', {}).get('faction2', 0)
        
        # Определяем статус для пользователя (победа/поражение)
        user_team_index = _get_user_team(match_stats, user_faceit_id)
        status_emoji = "🎮"  # По умолчанию
        
        logger.error(f"VERSION 2.1: user_team_index={user_team_index}, team1_score={team1_score}, team2_score={team2_score}")
        logger.error(f"VERSION 2.1: team1_name={team1_name}, team2_name={team2_name}")
        
        # Определяем по счету
        if user_team_index is not None and team1_score is not None and team2_score is not None:
            if user_team_index == 0:
                # Игрок в первой команде
                status_emoji = "🏆" if team1_score > team2_score else "❌"
                user_team = 'faction1'
                logger.error(f"VERSION 2.1: Игрок в команде 1, статус: {status_emoji}")
            elif user_team_index == 1:
                # Игрок во второй команде
                status_emoji = "🏆" if team2_score > team1_score else "❌"
                user_team = 'faction2'
                logger.error(f"VERSION 2.1: Игрок в команде 2, статус: {status_emoji}")
            else:
                user_team = None
        else:
            user_team = None
            logger.error(f"VERSION 2.1: Не удалось определить команду игрока")

        # Карта - попробуем получить из разных источников
        map_name = "Неизвестная карта"
        
        # Сначала из voting
        voting = match_data.get('voting', {})
        if voting and 'map' in voting:
            if 'pick' in voting['map'] and voting['map']['pick']:
                map_name = voting['map']['pick'][0]
            elif 'name' in voting['map'] and voting['map']['name']:
                map_name = voting['map']['name']
        
        # Если не нашли, попробуем из match_stats
        if map_name == "Неизвестная карта":
            try:
                rounds = match_stats.get('rounds', [])
                if rounds:
                    round_stats = rounds[0].get('round_stats', {})
                    if 'Map' in round_stats and round_stats['Map']:
                        map_name = round_stats['Map']
                        # Добавляем префикс de_ если его нет
                        if not map_name.startswith('de_') and map_name.lower() != 'unknown':
                            map_name = f"de_{map_name.lower()}"
            except Exception as e:
                logger.error(f"Error getting map name from match_stats: {e}")

        # Статистика пользователя
        user_stats = _get_user_stats(match_stats, user_faceit_id)
        
        # Определяем какая команда игрока и показываем её первой
        if user_team_index == 0:
            # Команда игрока - первая
            user_team_name = team1_name
            user_team_score = team1_score
            enemy_team_name = team2_name
            enemy_team_score = team2_score
        elif user_team_index == 1:
            # Команда игрока - вторая
            user_team_name = team2_name
            user_team_score = team2_score
            enemy_team_name = team1_name
            enemy_team_score = team1_score
        else:
            # Не удалось определить - показываем как есть
            user_team_name = team1_name
            user_team_score = team1_score
            enemy_team_name = team2_name
            enemy_team_score = team2_score
        
        # Формируем первые строки сообщения
        message_lines = [
            f"{status_emoji} <b>{user_team_name}</b> {user_team_score} - {enemy_team_score} {enemy_team_name}",
            f"🗺️ <b>Карта:</b> {map_name}",
            "",
            f"📊 <b>Ваша статистика:</b>",
        ]

        if user_stats:
            kills = user_stats.get('Kills', '0')
            deaths = user_stats.get('Deaths', '0')
            assists = user_stats.get('Assists', '0')
            kd_ratio = user_stats.get('K/D Ratio', '0.00')
            kr_ratio = user_stats.get('K/R Ratio', '0.00')
            headshots = user_stats.get('Headshots', '0')
            
            # Рассчитываем процент хедшотов
            try:
                kills_int = int(kills)
                hs_int = int(headshots)
                if kills_int > 0:
                    hs_percent = round((hs_int / kills_int) * 100, 1)
                    logger.error(f"VERSION 2.1: HS% рассчитан: {hs_int}/{kills_int} = {hs_percent}%")
                else:
                    hs_percent = 0
            except Exception as e:
                logger.error(f"VERSION 2.1: Ошибка расчета HS%: {e}")
                hs_percent = user_stats.get('HS %', '0')
                
            mvps = user_stats.get('MVPs', '0')
            triple_kills = user_stats.get('Triple Kills', '0')
            quadro_kills = user_stats.get('Quadro Kills', '0')
            penta_kills = user_stats.get('Penta Kills', '0')
            adr = user_stats.get('ADR', '0')
            
            # Основная статистика
            message_lines.append(
                f"🔥 <b>K-D-A:</b> {kills}-{deaths}-{assists} | <b>K/D:</b> {kd_ratio} | <b>ADR:</b> {adr}"
            )
            
            # Дополнительная статистика
            message_lines.append(
                f"🎯 <b>Хедшоты:</b> {headshots} ({hs_percent}%) | <b>K/R:</b> {kr_ratio} | <b>MVP:</b> {mvps}"
            )
            
            # Мультикиллы (показываем только если есть)
            multikills = []
            if int(triple_kills) > 0:
                multikills.append(f"3K: {triple_kills}")
            if int(quadro_kills) > 0:
                multikills.append(f"4K: {quadro_kills}")  
            if int(penta_kills) > 0:
                multikills.append(f"5K: {penta_kills}")
                
            if multikills:
                message_lines.append(f"⚡ <b>Мультикиллы:</b> {' | '.join(multikills)}")
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
        logger.error(f"VERSION 2.1: Ищем игрока {user_faceit_id}")
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return None
            
        round_stats = rounds[0]  # Берем первый раунд
        teams = round_stats.get('teams', [])
        
        for i, team in enumerate(teams):
            team_name = team.get('team_stats', {}).get('Team', 'Unknown')
            players = team.get('players', [])
            logger.error(f"VERSION 2.1: Проверяем команду {i} ({team_name}) с {len(players)} игроками")
            
            for player in players:
                player_id = player.get('player_id')
                player_nick = player.get('nickname', 'Unknown')
                logger.error(f"VERSION 2.1: Проверяем игрока {player_nick} (ID: {player_id})")
                
                if player_id == user_faceit_id:
                    logger.error(f"VERSION 2.1: НАШЛИ игрока {player_nick} в команде {team_name} (индекс {i})")
                    # Возвращаем индекс команды (0 или 1) вместо team_id
                    return i
        
        logger.error(f"VERSION 2.1: Игрок {user_faceit_id} НЕ НАЙДЕН ни в одной команде")
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
                # Выделяем пользователя жирным текстом
                if player_id == user_faceit_id:
                    player_line = f"<b>• {nickname}</b> ({kills}-{deaths}-{assists}, ADR: {adr})"
                else:
                    player_line = f"• {nickname} ({kills}-{deaths}-{assists}, ADR: {adr})"
                
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
    
    builder.adjust(1)  # Каждая кнопка на отдельной строке
    return builder.as_markup()


def _get_back_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура без кнопок навигации"""
    return None


def _get_round_scores(match_stats: Dict) -> tuple:
    """Получает счёт раундов из статистики матча"""
    try:
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return None, None
            
        round_stats = rounds[0]
        teams = round_stats.get('teams', [])
        
        if len(teams) >= 2:
            team1_score = teams[0].get('team_stats', {}).get('Final Score', 0)
            team2_score = teams[1].get('team_stats', {}).get('Final Score', 0)
            
            # Проверяем что счёт валидный
            if isinstance(team1_score, (int, str)) and isinstance(team2_score, (int, str)):
                try:
                    return int(team1_score), int(team2_score)
                except ValueError:
                    pass
        
        return None, None
    except Exception as e:
        logger.error(f"Error getting round scores: {e}")
        return None, None


def _get_team_display_order(user_team, team1_name, team2_name, team1_score, team2_score):
    """Определяет порядок отображения команд - команда игрока первой"""
    if user_team == 'faction1':
        return team1_name, team1_score, team2_name, team2_score
    elif user_team == 'faction2':
        return team2_name, team2_score, team1_name, team1_score
    else:
        # Если не удалось определить команду игрока
        return team1_name, team1_score, team2_name, team2_score