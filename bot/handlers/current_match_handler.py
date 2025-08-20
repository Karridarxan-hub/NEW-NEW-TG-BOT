from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Dict, List, Any, Optional, Tuple
import re
import asyncio
from datetime import datetime

from keyboards import get_main_menu_keyboard, get_back_to_main_keyboard
from storage import storage
from faceit_client import faceit_client


# Создаем роутер для анализа текущего матча
router = Router(name="current_match_handler")


class CurrentMatchStates(StatesGroup):
    """FSM состояния для анализа текущего матча"""
    waiting_for_match_link = State()


def get_current_match_keyboard() -> Dict:
    """Клавиатура для анализа текущего матча"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔗 Ввести ссылку на матч", callback_data="enter_match_link")
    builder.button(text="📊 Обновить анализ", callback_data="refresh_current_match")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 1, 2)
    return builder.as_markup()


def get_match_analysis_keyboard() -> Dict:
    """Клавиатура с результатами анализа"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Детальный анализ команд", callback_data="detailed_team_analysis")
    builder.button(text="🗺️ Анализ карты", callback_data="detailed_map_analysis")
    builder.button(text="🔄 Новый анализ", callback_data="enter_match_link")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def extract_match_id(url: str) -> Optional[str]:
    """
    Извлечь match_id из ссылки FACEIT
    Поддерживаемые форматы:
    - https://www.faceit.com/en/cs2/room/1-abc123-def456-ghi789
    - https://faceit.com/en/cs2/room/1-abc123-def456-ghi789
    - https://www.faceit.com/ru/cs2/room/1-abc123-def456-ghi789
    """
    patterns = [
        r'faceit\.com/[a-z]{2}/cs2/room/(1-[a-f0-9-]+)',
        r'faceit\.com/[a-z]{2}/csgo/room/(1-[a-f0-9-]+)',
        r'faceit\.com/.*room/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
        r'faceit\.com.*/(1-[a-f0-9-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def calculate_team_strength(players_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Рассчитать силу команды на основе статистики игроков
    """
    if not players_stats:
        return {
            'avg_hltv': 0.0,
            'avg_elo': 0,
            'avg_level': 0,
            'strong_players': [],
            'weak_players': [],
            'total_matches': 0,
            'avg_winrate': 0.0
        }
    
    hltv_ratings = []
    elos = []
    levels = []
    winrates = []
    total_matches = 0
    
    strong_players = []  # HLTV > 1.1
    weak_players = []    # HLTV < 0.9
    
    for player_stats in players_stats:
        hltv = player_stats.get('hltv_rating', 0.0)
        elo = player_stats.get('elo', 0)
        level = player_stats.get('level', 0)
        winrate = player_stats.get('winrate', 0.0)
        matches = player_stats.get('matches', 0)
        nickname = player_stats.get('nickname', 'Unknown')
        
        if hltv > 0:
            hltv_ratings.append(hltv)
            
            if hltv >= 1.1:
                strong_players.append({
                    'nickname': nickname,
                    'hltv': hltv,
                    'elo': elo,
                    'level': level
                })
            elif hltv < 0.9:
                weak_players.append({
                    'nickname': nickname,
                    'hltv': hltv,
                    'elo': elo,
                    'level': level
                })
        
        if elo > 0:
            elos.append(elo)
        if level > 0:
            levels.append(level)
        if winrate > 0:
            winrates.append(winrate)
        if matches > 0:
            total_matches += matches
    
    return {
        'avg_hltv': round(sum(hltv_ratings) / len(hltv_ratings), 3) if hltv_ratings else 0.0,
        'avg_elo': round(sum(elos) / len(elos)) if elos else 0,
        'avg_level': round(sum(levels) / len(levels), 1) if levels else 0,
        'avg_winrate': round(sum(winrates) / len(winrates), 1) if winrates else 0.0,
        'strong_players': sorted(strong_players, key=lambda x: x['hltv'], reverse=True),
        'weak_players': sorted(weak_players, key=lambda x: x['hltv']),
        'total_matches': total_matches,
        'player_count': len(players_stats)
    }


def analyze_map_performance(players_stats: List[Dict[str, Any]], map_name: str) -> Dict[str, Any]:
    """
    Проанализировать производительность игроков на конкретной карте
    """
    if not players_stats or not map_name:
        return {
            'avg_winrate': 0.0,
            'total_matches': 0,
            'players_with_data': 0,
            'best_player': None,
            'worst_player': None,
            'confidence_level': 'low'
        }
    
    map_performances = []
    total_matches = 0
    players_with_data = 0
    
    for player_stats in players_stats:
        maps_data = player_stats.get('maps', {})
        
        # Пытаемся найти карту (с учетом возможных вариантов названий)
        map_data = None
        for map_key, data in maps_data.items():
            if map_key.lower() == map_name.lower() or map_name.lower() in map_key.lower():
                map_data = data
                break
        
        if map_data and isinstance(map_data, dict):
            matches = map_data.get('matches', 0)
            winrate = map_data.get('winrate', 0.0)
            hltv = map_data.get('hltv_rating', 0.0)
            
            if matches > 0:  # Учитываем только игроков с опытом на карте
                map_performances.append({
                    'nickname': player_stats.get('nickname', 'Unknown'),
                    'winrate': winrate,
                    'matches': matches,
                    'hltv': hltv
                })
                total_matches += matches
                players_with_data += 1
    
    if not map_performances:
        return {
            'avg_winrate': 0.0,
            'total_matches': 0,
            'players_with_data': 0,
            'best_player': None,
            'worst_player': None,
            'confidence_level': 'none'
        }
    
    # Рассчитываем средний винрейт (взвешенный по количеству матчей)
    weighted_winrate = 0.0
    if total_matches > 0:
        for perf in map_performances:
            weight = perf['matches'] / total_matches
            weighted_winrate += perf['winrate'] * weight
    
    # Определяем лучшего и худшего игрока на карте
    best_player = max(map_performances, key=lambda x: (x['winrate'], x['hltv']))
    worst_player = min(map_performances, key=lambda x: (x['winrate'], x['hltv']))
    
    # Определяем уровень достоверности анализа
    confidence_level = 'low'
    if players_with_data >= 4 and total_matches >= 50:
        confidence_level = 'high'
    elif players_with_data >= 3 and total_matches >= 25:
        confidence_level = 'medium'
    elif players_with_data >= 2 and total_matches >= 10:
        confidence_level = 'low'
    else:
        confidence_level = 'very_low'
    
    return {
        'avg_winrate': round(weighted_winrate, 1),
        'total_matches': total_matches,
        'players_with_data': players_with_data,
        'best_player': best_player,
        'worst_player': worst_player,
        'confidence_level': confidence_level,
        'all_performances': map_performances
    }


async def get_team_players_stats(team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Получить статистику всех игроков команды
    """
    players_stats = []
    
    if not team_data or 'players' not in team_data:
        return players_stats
    
    for player in team_data['players']:
        player_id = player.get('player_id')
        nickname = player.get('nickname', 'Unknown')
        
        if not player_id:
            continue
        
        try:
            # Получаем полную статистику игрока
            player_details = await faceit_client.get_player_details(player_id)
            player_stats_data = await faceit_client.get_player_stats(player_id)
            
            if player_details and player_stats_data:
                formatted_stats = faceit_client.format_player_stats(player_details, player_stats_data)
                if formatted_stats:
                    players_stats.append(formatted_stats)
            
            # Задержка между запросами для соблюдения лимитов API
            await asyncio.sleep(0.2)
            
        except Exception as e:
            print(f"Ошибка получения статистики игрока {nickname}: {e}")
            continue
    
    return players_stats


async def analyze_current_match(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Провести полный анализ текущего матча
    """
    try:
        # Получаем детали матча
        match_details = await faceit_client.get_match_details(match_id)
        if not match_details:
            return None
        
        # Извлекаем основную информацию о матче
        match_info = {
            'match_id': match_id,
            'status': match_details.get('status', 'unknown'),
            'game': match_details.get('game', 'cs2'),
            'region': match_details.get('region', 'unknown'),
            'competition_name': match_details.get('competition_name', 'Unknown'),
            'competition_type': match_details.get('competition_type', 'Unknown'),
            'best_of': match_details.get('best_of', 1),
            'configured_at': match_details.get('configured_at'),
            'started_at': match_details.get('started_at')
        }
        
        # Получаем информацию о командах
        teams = match_details.get('teams', {})
        if len(teams) != 2:
            return None
        
        team_names = list(teams.keys())
        team1_data = teams[team_names[0]]
        team2_data = teams[team_names[1]]
        
        # Получаем карту из voting (если доступна)
        voting = match_details.get('voting', {})
        current_map = None
        if voting and 'map' in voting and 'pick' in voting['map']:
            picks = voting['map']['pick']
            if picks:
                current_map = picks[0] if isinstance(picks, list) else picks
        
        # Если карта не найдена в voting, пытаемся найти в других местах
        if not current_map:
            # Проверяем в results
            results = match_details.get('results', {})
            if results and 'stats' in results:
                current_map = results['stats'].get('map')
        
        print(f"🔍 Анализ матча {match_id}")
        print(f"   Команды: {team_names[0]} vs {team_names[1]}")
        print(f"   Карта: {current_map or 'TBD'}")
        print(f"   Статус: {match_info['status']}")
        
        # Получаем статистику игроков обеих команд
        print("📊 Получение статистики команд...")
        team1_stats = await get_team_players_stats(team1_data)
        await asyncio.sleep(1)  # Дополнительная задержка между командами
        team2_stats = await get_team_players_stats(team2_data)
        
        # Анализируем силу команд
        team1_strength = calculate_team_strength(team1_stats)
        team2_strength = calculate_team_strength(team2_stats)
        
        # Анализируем производительность на карте (если карта известна)
        map_analysis = {}
        if current_map:
            team1_map_perf = analyze_map_performance(team1_stats, current_map)
            team2_map_perf = analyze_map_performance(team2_stats, current_map)
            
            map_analysis = {
                'map_name': current_map,
                'team1_performance': team1_map_perf,
                'team2_performance': team2_map_perf,
                'winrate_diff': team1_map_perf['avg_winrate'] - team2_map_perf['avg_winrate']
            }
        
        # Составляем прогноз
        prediction = generate_match_prediction(team1_strength, team2_strength, map_analysis, team_names)
        
        analysis_result = {
            'match_info': match_info,
            'map_name': current_map,
            'teams': {
                team_names[0]: {
                    'name': team_names[0],
                    'players': team1_stats,
                    'strength': team1_strength
                },
                team_names[1]: {
                    'name': team_names[1],
                    'players': team2_stats,
                    'strength': team2_strength
                }
            },
            'map_analysis': map_analysis,
            'prediction': prediction,
            'analyzed_at': datetime.now().isoformat()
        }
        
        print("✅ Анализ матча завершен")
        return analysis_result
        
    except Exception as e:
        print(f"❌ Ошибка анализа матча: {e}")
        return None


def generate_match_prediction(team1_strength: Dict, team2_strength: Dict, 
                            map_analysis: Dict, team_names: List[str]) -> Dict[str, Any]:
    """
    Генерировать прогноз на основе анализа команд и карты
    """
    team1_name, team2_name = team_names
    
    # Базовый анализ силы команд
    hltv_diff = team1_strength['avg_hltv'] - team2_strength['avg_hltv']
    elo_diff = team1_strength['avg_elo'] - team2_strength['avg_elo']
    
    # Счетчики преимуществ
    team1_advantages = []
    team2_advantages = []
    
    # Анализ HLTV рейтингов
    if abs(hltv_diff) > 0.1:
        if hltv_diff > 0:
            team1_advantages.append(f"Превосходство по HLTV (+{hltv_diff:.3f})")
        else:
            team2_advantages.append(f"Превосходство по HLTV (+{abs(hltv_diff):.3f})")
    
    # Анализ ELO
    if abs(elo_diff) > 50:
        if elo_diff > 0:
            team1_advantages.append(f"Превосходство по ELO (+{int(elo_diff)})")
        else:
            team2_advantages.append(f"Превосходство по ELO (+{int(abs(elo_diff))})")
    
    # Анализ количества сильных игроков
    strong_diff = len(team1_strength['strong_players']) - len(team2_strength['strong_players'])
    if strong_diff > 0:
        team1_advantages.append(f"Больше сильных игроков (+{strong_diff})")
    elif strong_diff < 0:
        team2_advantages.append(f"Больше сильных игроков (+{abs(strong_diff)})")
    
    # Анализ карты (если доступен)
    map_favorite = None
    if map_analysis and 'winrate_diff' in map_analysis:
        winrate_diff = map_analysis['winrate_diff']
        if abs(winrate_diff) > 5:  # Значительная разница
            if winrate_diff > 0:
                team1_advantages.append(f"Лучше играет на карте (+{winrate_diff:.1f}%)")
                map_favorite = team1_name
            else:
                team2_advantages.append(f"Лучше играет на карте (+{abs(winrate_diff):.1f}%)")
                map_favorite = team2_name
    
    # Определяем фаворита
    favorite = None
    confidence = "low"
    
    total_team1_score = len(team1_advantages)
    total_team2_score = len(team2_advantages)
    
    # Добавляем веса для HLTV (более важный показатель)
    if abs(hltv_diff) > 0.2:
        if hltv_diff > 0:
            total_team1_score += 2
        else:
            total_team2_score += 2
    
    if total_team1_score > total_team2_score:
        favorite = team1_name
        score_diff = total_team1_score - total_team2_score
    elif total_team2_score > total_team1_score:
        favorite = team2_name
        score_diff = total_team2_score - total_team1_score
    else:
        favorite = None
        score_diff = 0
    
    # Определяем уровень уверенности
    if score_diff >= 4:
        confidence = "high"
    elif score_diff >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        'favorite': favorite,
        'confidence': confidence,
        'hltv_difference': hltv_diff,
        'elo_difference': elo_diff,
        'map_favorite': map_favorite,
        'team1_advantages': team1_advantages,
        'team2_advantages': team2_advantages,
        'analysis_factors': {
            'strong_players_diff': strong_diff,
            'avg_hltv_diff': hltv_diff,
            'avg_elo_diff': elo_diff,
            'map_winrate_diff': map_analysis.get('winrate_diff', 0) if map_analysis else 0
        }
    }


def format_match_analysis(analysis: Dict[str, Any]) -> str:
    """
    Форматировать результаты анализа матча для отображения
    """
    if not analysis:
        return "❌ Не удалось провести анализ матча"
    
    match_info = analysis.get('match_info', {})
    teams = analysis.get('teams', {})
    prediction = analysis.get('prediction', {})
    map_analysis = analysis.get('map_analysis', {})
    
    team_names = list(teams.keys())
    if len(team_names) != 2:
        return "❌ Ошибка: не найдено две команды"
    
    team1_name = team_names[0]
    team2_name = team_names[1]
    team1_data = teams[team1_name]
    team2_data = teams[team2_name]
    
    # Заголовок
    text = "🔍 **АНАЛИЗ ТЕКУЩЕГО МАТЧА**\n\n"
    
    # Основная информация о матче
    text += f"🎮 **Матч:** {team1_name} vs {team2_name}\n"
    if analysis.get('map_name'):
        text += f"🗺️ **Карта:** {analysis['map_name']}\n"
    else:
        text += f"🗺️ **Карта:** TBD\n"
    text += f"🏆 **Турнир:** {match_info.get('competition_name', 'Unknown')}\n"
    text += f"🌍 **Регион:** {match_info.get('region', 'Unknown')}\n\n"
    
    # Анализ силы команд
    text += "⚔️ **АНАЛИЗ КОМАНД**\n\n"
    
    # Команда 1
    team1_strength = team1_data.get('strength', {})
    text += f"👥 **{team1_name}**\n"
    text += f"├ Средний HLTV: **{team1_strength.get('avg_hltv', 0):.3f}**\n"
    text += f"├ Средний ELO: **{team1_strength.get('avg_elo', 0)}**\n"
    text += f"├ Средний уровень: **{team1_strength.get('avg_level', 0)}**\n"
    
    strong1 = team1_strength.get('strong_players', [])
    if strong1:
        text += f"├ Сильные игроки ({len(strong1)}):\n"
        for player in strong1:
            text += f"│  • {player['nickname']} (HLTV: {player['hltv']:.3f})\n"
    
    weak1 = team1_strength.get('weak_players', [])
    if weak1:
        text += f"└ Слабые игроки ({len(weak1)}):\n"
        for player in weak1:
            text += f"   • {player['nickname']} (HLTV: {player['hltv']:.3f})\n"
    else:
        text += f"└ Слабых игроков не выявлено\n"
    
    text += "\n"
    
    # Команда 2
    team2_strength = team2_data.get('strength', {})
    text += f"👥 **{team2_name}**\n"
    text += f"├ Средний HLTV: **{team2_strength.get('avg_hltv', 0):.3f}**\n"
    text += f"├ Средний ELO: **{team2_strength.get('avg_elo', 0)}**\n"
    text += f"├ Средний уровень: **{team2_strength.get('avg_level', 0)}**\n"
    
    strong2 = team2_strength.get('strong_players', [])
    if strong2:
        text += f"├ Сильные игроки ({len(strong2)}):\n"
        for player in strong2:
            text += f"│  • {player['nickname']} (HLTV: {player['hltv']:.3f})\n"
    
    weak2 = team2_strength.get('weak_players', [])
    if weak2:
        text += f"└ Слабые игроки ({len(weak2)}):\n"
        for player in weak2:
            text += f"   • {player['nickname']} (HLTV: {player['hltv']:.3f})\n"
    else:
        text += f"└ Слабых игроков не выявлено\n"
    
    text += "\n"
    
    # Анализ карты (если доступен)
    if map_analysis and map_analysis.get('map_name'):
        text += f"🗺️ **АНАЛИЗ КАРТЫ: {map_analysis['map_name']}**\n\n"
        
        team1_map = map_analysis.get('team1_performance', {})
        team2_map = map_analysis.get('team2_performance', {})
        
        text += f"📊 **{team1_name}** на карте:\n"
        text += f"├ Винрейт: **{team1_map.get('avg_winrate', 0):.1f}%**\n"
        text += f"├ Матчей на карте: {team1_map.get('total_matches', 0)}\n"
        text += f"└ Игроков с данными: {team1_map.get('players_with_data', 0)}/5\n\n"
        
        text += f"📊 **{team2_name}** на карте:\n"
        text += f"├ Винрейт: **{team2_map.get('avg_winrate', 0):.1f}%**\n"
        text += f"├ Матчей на карте: {team2_map.get('total_matches', 0)}\n"
        text += f"└ Игроков с данными: {team2_map.get('players_with_data', 0)}/5\n\n"
        
        winrate_diff = map_analysis.get('winrate_diff', 0)
        if abs(winrate_diff) > 3:
            better_team = team1_name if winrate_diff > 0 else team2_name
            text += f"🎯 **Преимущество на карте:** {better_team} (+{abs(winrate_diff):.1f}%)\n\n"
    
    # Прогноз
    text += "🎯 **ПРОГНОЗ**\n\n"
    
    favorite = prediction.get('favorite')
    confidence = prediction.get('confidence', 'low')
    
    if favorite:
        confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🟠"}.get(confidence, "🟠")
        confidence_text = {"high": "Высокая", "medium": "Средняя", "low": "Низкая"}.get(confidence, "Низкая")
        
        text += f"🏆 **Фаворит:** {favorite}\n"
        text += f"{confidence_emoji} **Уверенность:** {confidence_text}\n\n"
        
        # Преимущества фаворита
        if favorite == team1_name and prediction.get('team1_advantages'):
            text += f"📈 **Преимущества {favorite}:**\n"
            for adv in prediction['team1_advantages']:
                text += f"• {adv}\n"
        elif favorite == team2_name and prediction.get('team2_advantages'):
            text += f"📈 **Преимущества {favorite}:**\n"
            for adv in prediction['team2_advantages']:
                text += f"• {adv}\n"
    else:
        text += "⚖️ **Команды примерно равны по силе**\n"
        text += "🎲 Исход матча труднопредсказуем\n"
    
    text += f"\n🕐 Анализ выполнен: {datetime.fromisoformat(analysis['analyzed_at']).strftime('%H:%M:%S')}"
    
    return text


# ===== ОБРАБОТЧИКИ СОБЫТИЙ =====

@router.callback_query(F.data == "current_match_analysis")
async def show_current_match_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню анализа текущего матча"""
    # Проверяем, есть ли сохраненный анализ
    user_id = callback.from_user.id
    saved_analysis = await storage.get_cached_data(f"current_match_analysis_{user_id}")
    
    if saved_analysis:
        text = "🔍 **Анализ текущего матча**\n\n"
        text += "У вас есть сохраненный анализ матча.\n"
        text += "Выберите действие:"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Показать анализ", callback_data="show_saved_analysis")
        builder.button(text="🔗 Новый анализ", callback_data="enter_match_link")
        builder.button(text="🔙 Назад", callback_data="back_to_main")
        keyboard = builder.as_markup()
    else:
        text = "🔍 **Анализ текущего матча**\n\n"
        text += "Введите ссылку на матч FACEIT для получения детального анализа команд и прогноза.\n\n"
        text += "📊 **Что анализируется:**\n"
        text += "• Сила команд (средний HLTV, ELO)\n"
        text += "• Сильные и слабые игроки\n"
        text += "• Статистика команд на карте\n"
        text += "• Прогноз победителя\n\n"
        text += "Выберите действие:"
        keyboard = get_current_match_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "show_saved_analysis")
async def show_saved_analysis(callback: CallbackQuery):
    """Показать сохраненный анализ матча"""
    user_id = callback.from_user.id
    saved_analysis = await storage.get_cached_data(f"current_match_analysis_{user_id}")
    
    if saved_analysis:
        text = format_match_analysis(saved_analysis)
        keyboard = get_match_analysis_keyboard()
    else:
        text = "❌ Сохраненный анализ не найден.\n\nВведите ссылку на матч для нового анализа."
        keyboard = get_current_match_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "enter_match_link")
async def enter_match_link(callback: CallbackQuery, state: FSMContext):
    """Запросить ввод ссылки на матч"""
    text = "🔗 **Ввод ссылки на матч**\n\n"
    text += "Отправьте ссылку на матч FACEIT.\n\n"
    text += "📝 **Поддерживаемые форматы:**\n"
    text += "• https://www.faceit.com/en/cs2/room/1-abc123-def456\n"
    text += "• https://faceit.com/ru/cs2/room/1-abc123-def456\n\n"
    text += "⏱️ Анализ может занять 1-2 минуты из-за получения статистики всех игроков."
    
    keyboard = get_back_to_main_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(CurrentMatchStates.waiting_for_match_link)
    await callback.answer()


@router.message(StateFilter(CurrentMatchStates.waiting_for_match_link))
async def process_match_link(message: Message, state: FSMContext):
    """Обработать ссылку на матч и выполнить анализ"""
    match_url = message.text.strip()
    user_id = message.from_user.id
    
    # Извлекаем match_id из ссылки
    match_id = extract_match_id(match_url)
    
    if not match_id:
        await message.answer(
            "❌ **Неверная ссылка**\n\n"
            "Не удалось извлечь ID матча из ссылки.\n\n"
            "📝 **Поддерживаемые форматы:**\n"
            "• https://www.faceit.com/en/cs2/room/1-abc123-def456\n"
            "• https://faceit.com/ru/cs2/room/1-abc123-def456\n\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown"
        )
        return
    
    # Отправляем сообщение о начале анализа
    analyzing_msg = await message.answer(
        "🔄 **Выполняется анализ матча...**\n\n"
        "⏱️ Получение данных матча и статистики игроков\n"
        "📊 Это может занять 1-2 минуты",
        parse_mode="Markdown"
    )
    
    # Выполняем анализ
    try:
        analysis_result = await analyze_current_match(match_id)
        
        if analysis_result:
            # Сохраняем анализ в кэш
            await storage.set_cached_data(
                f"current_match_analysis_{user_id}", 
                analysis_result, 
                ttl_minutes=30
            )
            
            # Форматируем и отправляем результат
            text = format_match_analysis(analysis_result)
            keyboard = get_match_analysis_keyboard()
            
            await analyzing_msg.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            
        else:
            await analyzing_msg.edit_text(
                "❌ **Не удалось выполнить анализ**\n\n"
                "Возможные причины:\n"
                "• Матч не найден или недоступен\n"
                "• Ошибка API FACEIT\n"
                "• Недостаточно данных об игроках\n\n"
                "Попробуйте еще раз или выберите другой матч.",
                reply_markup=get_current_match_keyboard(),
                parse_mode="Markdown"
            )
        
    except Exception as e:
        print(f"Ошибка анализа матча: {e}")
        await analyzing_msg.edit_text(
            f"❌ **Ошибка при анализе матча**\n\n"
            f"Произошла техническая ошибка.\n"
            f"Попробуйте позже или обратитесь к разработчику.",
            reply_markup=get_current_match_keyboard(),
            parse_mode="Markdown"
        )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data == "detailed_team_analysis")
async def detailed_team_analysis(callback: CallbackQuery):
    """Показать детальный анализ команд"""
    user_id = callback.from_user.id
    saved_analysis = await storage.get_cached_data(f"current_match_analysis_{user_id}")
    
    if not saved_analysis:
        await callback.message.edit_text(
            "❌ Анализ не найден.\n\nВведите ссылку на матч для нового анализа.",
            reply_markup=get_current_match_keyboard()
        )
        await callback.answer()
        return
    
    teams = saved_analysis.get('teams', {})
    if len(teams) != 2:
        await callback.message.edit_text(
            "❌ Ошибка данных команд.",
            reply_markup=get_current_match_keyboard()
        )
        await callback.answer()
        return
    
    team_names = list(teams.keys())
    team1_name, team2_name = team_names
    team1_data = teams[team1_name]
    team2_data = teams[team2_name]
    
    text = "📊 **ДЕТАЛЬНЫЙ АНАЛИЗ КОМАНД**\n\n"
    
    # Детальный анализ каждой команды
    for team_name, team_data in [(team1_name, team1_data), (team2_name, team2_data)]:
        text += f"👥 **{team_name}**\n\n"
        
        players = team_data.get('players', [])
        strength = team_data.get('strength', {})
        
        text += f"📈 **Общие показатели:**\n"
        text += f"• Средний HLTV: **{strength.get('avg_hltv', 0):.3f}**\n"
        text += f"• Средний ELO: **{strength.get('avg_elo', 0)}**\n"
        text += f"• Средний уровень: **{strength.get('avg_level', 0)}**\n"
        text += f"• Общий винрейт: **{strength.get('avg_winrate', 0):.1f}%**\n\n"
        
        text += f"👥 **Игроки команды:**\n"
        
        # Сортируем игроков по HLTV рейтингу
        sorted_players = sorted(players, key=lambda p: p.get('hltv_rating', 0), reverse=True)
        
        for i, player in enumerate(sorted_players, 1):
            nickname = player.get('nickname', 'Unknown')
            hltv = player.get('hltv_rating', 0)
            elo = player.get('elo', 0)
            level = player.get('level', 0)
            winrate = player.get('winrate', 0)
            kd = player.get('kd_ratio', 0)
            adr = player.get('adr', 0)
            
            # Определяем категорию игрока
            if hltv >= 1.1:
                category = "🔥"
            elif hltv >= 1.0:
                category = "⭐"
            elif hltv >= 0.9:
                category = "✅"
            else:
                category = "⚠️"
            
            text += f"{category} **{nickname}**\n"
            text += f"   HLTV: {hltv:.3f} | K/D: {kd:.2f} | ADR: {adr:.1f}\n"
            text += f"   ELO: {elo} | LVL: {level} | WR: {winrate:.1f}%\n\n"
        
        text += "═" * 30 + "\n\n"
    
    # Сравнительный анализ
    text += "⚔️ **СРАВНИТЕЛЬНЫЙ АНАЛИЗ**\n\n"
    
    team1_strength = team1_data.get('strength', {})
    team2_strength = team2_data.get('strength', {})
    
    hltv_diff = team1_strength.get('avg_hltv', 0) - team2_strength.get('avg_hltv', 0)
    elo_diff = team1_strength.get('avg_elo', 0) - team2_strength.get('avg_elo', 0)
    
    if hltv_diff > 0:
        text += f"📈 **{team1_name}** сильнее по HLTV на **{hltv_diff:.3f}**\n"
    elif hltv_diff < 0:
        text += f"📈 **{team2_name}** сильнее по HLTV на **{abs(hltv_diff):.3f}**\n"
    else:
        text += f"⚖️ Команды равны по среднему HLTV\n"
    
    if abs(elo_diff) > 10:
        if elo_diff > 0:
            text += f"🏆 **{team1_name}** выше по ELO на **{int(elo_diff)}**\n"
        else:
            text += f"🏆 **{team2_name}** выше по ELO на **{int(abs(elo_diff))}**\n"
    
    strong1 = len(team1_strength.get('strong_players', []))
    strong2 = len(team2_strength.get('strong_players', []))
    
    text += f"\n🔥 Сильных игроков: **{team1_name}** {strong1} vs {strong2} **{team2_name}**\n"
    
    keyboard = get_match_analysis_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "detailed_map_analysis")
async def detailed_map_analysis(callback: CallbackQuery):
    """Показать детальный анализ карты"""
    user_id = callback.from_user.id
    saved_analysis = await storage.get_cached_data(f"current_match_analysis_{user_id}")
    
    if not saved_analysis:
        await callback.message.edit_text(
            "❌ Анализ не найден.\n\nВведите ссылку на матч для нового анализа.",
            reply_markup=get_current_match_keyboard()
        )
        await callback.answer()
        return
    
    map_analysis = saved_analysis.get('map_analysis', {})
    if not map_analysis or not map_analysis.get('map_name'):
        await callback.message.edit_text(
            "❌ **Анализ карты недоступен**\n\n"
            "Карта матча не определена или данных недостаточно.\n"
            "Возможно, матч еще не начался или карта будет выбрана позже.",
            reply_markup=get_match_analysis_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    map_name = map_analysis['map_name']
    team1_perf = map_analysis.get('team1_performance', {})
    team2_perf = map_analysis.get('team2_performance', {})
    
    teams = saved_analysis.get('teams', {})
    team_names = list(teams.keys())
    team1_name, team2_name = team_names
    
    text = f"🗺️ **ДЕТАЛЬНЫЙ АНАЛИЗ КАРТЫ: {map_name}**\n\n"
    
    # Анализ первой команды на карте
    text += f"📊 **{team1_name} на {map_name}:**\n"
    text += f"• Винрейт: **{team1_perf.get('avg_winrate', 0):.1f}%**\n"
    text += f"• Всего матчей: {team1_perf.get('total_matches', 0)}\n"
    text += f"• Игроков с данными: {team1_perf.get('players_with_data', 0)}/5\n"
    
    confidence1 = team1_perf.get('confidence_level', 'none')
    confidence_text1 = {
        'high': '🟢 Высокая',
        'medium': '🟡 Средняя', 
        'low': '🟠 Низкая',
        'very_low': '🔴 Очень низкая',
        'none': '❌ Нет данных'
    }.get(confidence1, '❌ Нет данных')
    
    text += f"• Достоверность: {confidence_text1}\n\n"
    
    # Лучший игрок команды на карте
    best1 = team1_perf.get('best_player')
    if best1:
        text += f"🌟 **Лучший игрок:** {best1['nickname']}\n"
        text += f"   Винрейт: {best1['winrate']:.1f}% ({best1['matches']} матчей)\n"
        text += f"   HLTV на карте: {best1.get('hltv', 0):.3f}\n\n"
    
    # Анализ второй команды на карте
    text += f"📊 **{team2_name} на {map_name}:**\n"
    text += f"• Винрейт: **{team2_perf.get('avg_winrate', 0):.1f}%**\n"
    text += f"• Всего матчей: {team2_perf.get('total_matches', 0)}\n"
    text += f"• Игроков с данными: {team2_perf.get('players_with_data', 0)}/5\n"
    
    confidence2 = team2_perf.get('confidence_level', 'none')
    confidence_text2 = {
        'high': '🟢 Высокая',
        'medium': '🟡 Средняя',
        'low': '🟠 Низкая', 
        'very_low': '🔴 Очень низкая',
        'none': '❌ Нет данных'
    }.get(confidence2, '❌ Нет данных')
    
    text += f"• Достоверность: {confidence_text2}\n\n"
    
    # Лучший игрок команды на карте
    best2 = team2_perf.get('best_player')
    if best2:
        text += f"🌟 **Лучший игрок:** {best2['nickname']}\n"
        text += f"   Винрейт: {best2['winrate']:.1f}% ({best2['matches']} матчей)\n"
        text += f"   HLTV на карте: {best2.get('hltv', 0):.3f}\n\n"
    
    # Сравнительный анализ
    text += "⚔️ **СРАВНЕНИЕ НА КАРТЕ**\n\n"
    
    winrate_diff = map_analysis.get('winrate_diff', 0)
    if abs(winrate_diff) > 3:
        better_team = team1_name if winrate_diff > 0 else team2_name
        worse_team = team2_name if winrate_diff > 0 else team1_name
        text += f"🎯 **{better_team}** имеет преимущество на карте\n"
        text += f"   Разница в винрейте: **+{abs(winrate_diff):.1f}%**\n\n"
        
        if abs(winrate_diff) > 10:
            text += "🔥 **Значительное преимущество!**\n"
        elif abs(winrate_diff) > 5:
            text += "⭐ **Заметное преимущество**\n"
        else:
            text += "✅ **Небольшое преимущество**\n"
    else:
        text += "⚖️ **Команды примерно равны на данной карте**\n"
        text += f"Разница в винрейте: {winrate_diff:+.1f}%\n"
    
    text += "\n📝 **Детальная статистика игроков по картам:**\n\n"
    
    # Показываем топ игроков на карте из каждой команды
    for team_name, team_perf in [(team1_name, team1_perf), (team2_name, team2_perf)]:
        performances = team_perf.get('all_performances', [])
        if performances:
            text += f"🏆 **{team_name}** - топ на карте:\n"
            sorted_perfs = sorted(performances, key=lambda x: (x['winrate'], x['hltv']), reverse=True)
            for i, perf in enumerate(sorted_perfs[:3], 1):
                text += f"{i}. {perf['nickname']}: {perf['winrate']:.1f}% ({perf['matches']}м)\n"
            text += "\n"
    
    keyboard = get_match_analysis_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "refresh_current_match")
async def refresh_current_match(callback: CallbackQuery):
    """Обновить анализ текущего матча"""
    user_id = callback.from_user.id
    saved_analysis = await storage.get_cached_data(f"current_match_analysis_{user_id}")
    
    if not saved_analysis:
        await callback.message.edit_text(
            "❌ Нет сохраненного анализа для обновления.\n\nВведите ссылку на матч.",
            reply_markup=get_current_match_keyboard()
        )
        await callback.answer()
        return
    
    match_id = saved_analysis.get('match_info', {}).get('match_id')
    if not match_id:
        await callback.message.edit_text(
            "❌ Не удалось найти ID матча для обновления.",
            reply_markup=get_current_match_keyboard()
        )
        await callback.answer()
        return
    
    # Отправляем сообщение об обновлении
    await callback.message.edit_text(
        "🔄 **Обновление анализа матча...**\n\n"
        "⏱️ Получение актуальных данных",
        parse_mode="Markdown"
    )
    
    try:
        # Выполняем новый анализ
        analysis_result = await analyze_current_match(match_id)
        
        if analysis_result:
            # Обновляем кэш
            await storage.set_cached_data(
                f"current_match_analysis_{user_id}",
                analysis_result,
                ttl_minutes=30
            )
            
            # Отправляем обновленный результат
            text = format_match_analysis(analysis_result)
            keyboard = get_match_analysis_keyboard()
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback.message.edit_text(
                "❌ **Не удалось обновить анализ**\n\n"
                "Матч может быть завершен или недоступен.",
                reply_markup=get_current_match_keyboard(),
                parse_mode="Markdown"
            )
    
    except Exception as e:
        print(f"Ошибка обновления анализа: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка при обновлении анализа**\n\n"
            "Попробуйте позже.",
            reply_markup=get_current_match_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.callback_query(F.data.in_(["main_menu", "back_to_main"]))
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()  # Очищаем состояние FSM
    
    user_id = callback.from_user.id
    user_data = await storage.get_user(user_id)
    
    text = "🎮 **Главное меню**\n\nВыберите нужный раздел:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()