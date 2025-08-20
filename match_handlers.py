from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime
import asyncio

from keyboards import get_back_to_main_keyboard, get_back_keyboard
from faceit_client import faceit_client
from storage import storage


router = Router()


def format_match_status(status: str) -> str:
    """Форматировать статус матча с эмодзи"""
    status_emojis = {
        'finished': '✅',
        'ongoing': '🔴',
        'ready': '🟡',
        'cancelled': '❌',
        'unknown': '❓'
    }
    return status_emojis.get(status.lower(), '❓')


def format_team_scores(team1: dict, team2: dict) -> str:
    """Форматировать счет команд"""
    team1_name = team1.get('name', 'Team 1')[:15]
    team2_name = team2.get('name', 'Team 2')[:15]
    score1 = team1.get('stats', {}).get('Final Score', '0')
    score2 = team2.get('stats', {}).get('Final Score', '0')
    
    return f"{team1_name} {score1}:{score2} {team2_name}"


def calculate_player_stats_from_match(player_stats: dict) -> dict:
    """Рассчитать статистику игрока из матча"""
    stats = player_stats.get('stats', {})
    
    kills = int(stats.get('Kills', 0))
    deaths = int(stats.get('Deaths', 1))
    assists = int(stats.get('Assists', 0))
    rounds = int(stats.get('Rounds', 1))
    
    # Основные метрики
    kd_ratio = round(kills / max(deaths, 1), 2)
    adr = round(float(stats.get('ADR', 0)), 1)
    kast = round(float(stats.get('KAST %', 0)), 1)
    
    # Упрощенный расчет HLTV рейтинга для матча
    kpr = kills / max(rounds, 1)
    dpr = deaths / max(rounds, 1)
    impact = 2.13 * kpr + 0.42 * (assists / max(rounds, 1)) - 0.41
    hltv_rating = 0.0073 * kast + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * impact + 0.0032 * adr + 0.1587
    hltv_rating = max(0, round(hltv_rating, 2))
    
    return {
        'kills': kills,
        'deaths': deaths,
        'assists': assists,
        'kd_ratio': kd_ratio,
        'adr': adr,
        'kast': kast,
        'hltv_rating': hltv_rating,
        'headshots': round(float(stats.get('Headshots %', 0)), 1),
        'first_kills': int(stats.get('First Kills', 0)),
        'first_deaths': int(stats.get('First Deaths', 0))
    }


@router.callback_query(F.data == "last_match")
async def show_last_match(callback: CallbackQuery):
    """Показать последний матч"""
    user_id = callback.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль не привязан. Используйте /start для привязки профиля.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    await callback.message.edit_text("🔄 Загружаем последний матч...")
    
    # Получаем историю матчей
    matches_data = await faceit_client.get_player_matches(faceit_id, limit=1)
    
    if not matches_data or not matches_data.get('items'):
        await callback.message.edit_text(
            "❌ Не удалось найти матчи. Попробуйте позже.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    last_match = matches_data['items'][0]
    match_id = last_match['match_id']
    
    # Получаем детали матча
    match_details = await faceit_client.get_match_details(match_id)
    match_stats = await faceit_client.get_match_stats(match_id)
    
    if not match_details or not match_stats:
        await callback.message.edit_text(
            "❌ Не удалось загрузить детали матча.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    # Сохраняем последний матч для отслеживания
    storage.set_tracked_match(user_id, match_id)
    
    await format_and_send_match_details(callback, match_details, match_stats, faceit_id)


async def format_and_send_match_details(callback: CallbackQuery, match_details: dict, 
                                      match_stats: dict, player_faceit_id: str):
    """Форматировать и отправить детали матча"""
    # Основная информация о матче
    status = format_match_status(match_details.get('status', 'unknown'))
    map_name = match_details.get('voting', {}).get('map', {}).get('pick', ['Unknown'])[0]
    
    teams = match_details.get('teams', {})
    team1 = teams.get('faction1', {})
    team2 = teams.get('faction2', {})
    
    # Ссылка на FACEIT
    faceit_url = f"https://www.faceit.com/en/csgo/room/{match_details['match_id']}"
    
    # Поиск нашего игрока в статистике
    rounds = match_stats.get('rounds', [])
    if not rounds:
        await callback.message.edit_text(
            "❌ Нет доступной статистики матча.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    round_stats = rounds[0]  # Берем первый раунд для общей статистики
    teams_stats = round_stats.get('teams', [])
    
    player_stats = None
    player_team_stats = None
    enemy_team_stats = None
    
    # Находим статистику нашего игрока
    for team_stats in teams_stats:
        for player in team_stats.get('players', []):
            if player.get('player_id') == player_faceit_id:
                player_stats = player
                player_team_stats = team_stats
                # Находим команду противника
                enemy_team_stats = next(
                    (team for team in teams_stats if team != team_stats), 
                    None
                )
                break
        if player_stats:
            break
    
    if not player_stats:
        await callback.message.edit_text(
            "❌ Не удалось найти статистику игрока в матче.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    # Рассчитываем статистику игрока
    calculated_stats = calculate_player_stats_from_match(player_stats)
    
    # Формируем текст с основной информацией
    score_text = format_team_scores(team1, team2)
    
    # Определяем результат матча для игрока
    player_team_score = player_team_stats.get('stats', {}).get('Final Score', '0')
    enemy_team_score = enemy_team_stats.get('stats', {}).get('Final Score', '0') if enemy_team_stats else '0'
    
    try:
        won = int(player_team_score) > int(enemy_team_score)
        result_emoji = "🏆" if won else "💀"
        result_text = "Победа" if won else "Поражение"
    except:
        result_emoji = "❓"
        result_text = "Неизвестно"
    
    match_text = f"""🎮 **Последний матч** {status}

{result_emoji} **{result_text}**
🗺️ **Карта:** {map_name}
📊 **Счет:** {score_text}
🔗 [Открыть на FACEIT]({faceit_url})

👤 **Ваша статистика:**
💀 **K/D/A:** {calculated_stats['kills']}/{calculated_stats['deaths']}/{calculated_stats['assists']}
⚔️ **K/D:** {calculated_stats['kd_ratio']}
💥 **ADR:** {calculated_stats['adr']}
🎯 **HLTV 2.1:** {calculated_stats['hltv_rating']}
📍 **KAST:** {calculated_stats['kast']}%
🎯 **Хедшоты:** {calculated_stats['headshots']}%
⚡ **Первые убийства:** {calculated_stats['first_kills']}
💀 **Первые смерти:** {calculated_stats['first_deaths']}"""
    
    # Добавляем статистику команд
    if player_team_stats and enemy_team_stats:
        match_text += "\n\n📋 **Составы команд:**"
        
        # Команда игрока
        player_team_name = player_team_stats.get('team_stats', {}).get('Team', 'Наша команда')
        match_text += f"\n\n🟢 **{player_team_name}** ({player_team_score})"
        
        team_players = sorted(
            player_team_stats.get('players', []), 
            key=lambda x: int(x.get('stats', {}).get('Kills', 0)), 
            reverse=True
        )
        
        for player in team_players:
            nickname = player.get('nickname', 'Unknown')
            p_stats = calculate_player_stats_from_match(player)
            
            # Выделяем нашего игрока
            if player.get('player_id') == player_faceit_id:
                nickname = f"**{nickname}**"
            
            match_text += f"\n{nickname}: {p_stats['kills']}/{p_stats['deaths']}/{p_stats['assists']} (ADR: {p_stats['adr']}, HLTV: {p_stats['hltv_rating']})"
        
        # Команда противника
        enemy_team_name = enemy_team_stats.get('team_stats', {}).get('Team', 'Команда противника')
        match_text += f"\n\n🔴 **{enemy_team_name}** ({enemy_team_score})"
        
        enemy_players = sorted(
            enemy_team_stats.get('players', []), 
            key=lambda x: int(x.get('stats', {}).get('Kills', 0)), 
            reverse=True
        )
        
        for player in enemy_players:
            nickname = player.get('nickname', 'Unknown')
            p_stats = calculate_player_stats_from_match(player)
            
            match_text += f"\n{nickname}: {p_stats['kills']}/{p_stats['deaths']}/{p_stats['assists']} (ADR: {p_stats['adr']}, HLTV: {p_stats['hltv_rating']})"
    
    await callback.message.edit_text(
        match_text,
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer()


async def check_for_finished_matches():
    """Проверка завершенных матчей для уведомлений"""
    while True:
        try:
            # Проверяем каждые 2 минуты
            await asyncio.sleep(120)
            
            for user_id, tracked_match_id in storage.tracked_matches.items():
                # Проверяем настройки уведомлений
                user_settings = storage.get_user_settings(user_id)
                if not user_settings.get('match_notifications', True):
                    continue
                
                # Получаем детали матча
                match_details = await faceit_client.get_match_details(tracked_match_id)
                
                if not match_details:
                    continue
                
                # Проверяем, завершился ли матч
                if match_details.get('status') == 'finished':
                    # Получаем статистику
                    match_stats = await faceit_client.get_match_stats(tracked_match_id)
                    
                    if match_stats:
                        # Отправляем уведомление
                        faceit_id = storage.get_user_faceit_id(user_id)
                        if faceit_id:
                            # Отправляем уведомление о завершении матча
                            from main import bot
                            await send_match_notification(bot, user_id, match_details, match_stats)
                    
                    # Удаляем из отслеживания
                    del storage.tracked_matches[user_id]
        
        except Exception as e:
            print(f"Error checking finished matches: {e}")
            continue


# Функция для отправки уведомления (будет вызываться из main.py)
async def send_match_notification(bot, user_id: int, match_details: dict, match_stats: dict):
    """Отправить уведомление о завершенном матче"""
    try:
        faceit_id = storage.get_user_faceit_id(user_id)
        if not faceit_id:
            return
        
        # Получаем статистику игрока из матча
        rounds = match_stats.get('rounds', [])
        if not rounds:
            return
        
        round_stats = rounds[0]
        teams_stats = round_stats.get('teams', [])
        
        player_stats = None
        player_team_stats = None
        enemy_team_stats = None
        
        # Находим статистику игрока
        for team_stats in teams_stats:
            for player in team_stats.get('players', []):
                if player.get('player_id') == faceit_id:
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
            return
        
        calculated_stats = calculate_player_stats_from_match(player_stats)
        
        # Определяем результат
        player_team_score = player_team_stats.get('stats', {}).get('Final Score', '0')
        enemy_team_score = enemy_team_stats.get('stats', {}).get('Final Score', '0') if enemy_team_stats else '0'
        
        try:
            won = int(player_team_score) > int(enemy_team_score)
            result_emoji = "🏆" if won else "💀"
            result_text = "Победа" if won else "Поражение"
        except:
            result_emoji = "❓"
            result_text = "Неизвестно"
        
        # Основная информация
        map_name = match_details.get('voting', {}).get('map', {}).get('pick', ['Unknown'])[0]
        teams = match_details.get('teams', {})
        team1 = teams.get('faction1', {})
        team2 = teams.get('faction2', {})
        score_text = format_team_scores(team1, team2)
        
        notification_text = f"""🔔 **Матч завершен!**

{result_emoji} **{result_text}**
🗺️ **Карта:** {map_name}
📊 **Счет:** {score_text}

👤 **Ваша статистика:**
💀 **K/D/A:** {calculated_stats['kills']}/{calculated_stats['deaths']}/{calculated_stats['assists']}
⚔️ **K/D:** {calculated_stats['kd_ratio']}
💥 **ADR:** {calculated_stats['adr']}
🎯 **HLTV 2.1:** {calculated_stats['hltv_rating']}"""
        
        await bot.send_message(
            user_id,
            notification_text,
            parse_mode="Markdown",
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Добавляем матч в сессию
        match_data = {
            'match_id': match_details['match_id'],
            'finished_at': datetime.now(),
            'won': won,
            'kills': calculated_stats['kills'],
            'deaths': calculated_stats['deaths'],
            'assists': calculated_stats['assists'],
            'adr': calculated_stats['adr'],
            'hltv_rating': calculated_stats['hltv_rating']
        }
        storage.add_session_match(user_id, match_data)
        
    except Exception as e:
        print(f"Error sending match notification: {e}")