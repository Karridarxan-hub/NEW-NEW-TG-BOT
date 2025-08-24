"""
Улучшенное сравнение игроков с детальной статистикой
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


def get_indicator(value1: float, value2: float, higher_is_better: bool = True) -> Tuple[str, str]:
    """
    Возвращает индикаторы для сравнения двух значений
    
    Args:
        value1: Первое значение
        value2: Второе значение
        higher_is_better: True если большее значение лучше, False если меньшее
    
    Returns:
        Кортеж с индикаторами для первого и второго значения
    """
    if value1 == value2:
        return "➡️", "➡️"
    
    if higher_is_better:
        if value1 > value2:
            return "📈", "📉"
        else:
            return "📉", "📈"
    else:
        if value1 < value2:
            return "📈", "📉"
        else:
            return "📉", "📈"


def format_value_with_indicator(value: float, indicator: str, decimals: int = 1) -> str:
    """Форматирует значение с индикатором"""
    if decimals == 0:
        return f"{indicator} <b>{int(value)}</b>"
    else:
        return f"{indicator} <b>{value:.{decimals}f}</b>"



def get_top_maps(player_stats: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Получает топ карты игрока по количеству матчей
    
    Args:
        player_stats: Статистика игрока
        limit: Количество карт для возврата
    
    Returns:
        Список топ карт с их статистикой
    """
    map_statistics = player_stats.get('stats', {}).get('map_statistics', {})
    
    if not map_statistics:
        return []
    
    # Сортируем карты по количеству матчей
    sorted_maps = sorted(
        map_statistics.items(),
        key=lambda x: x[1].get('matches', 0),
        reverse=True
    )[:limit]
    
    top_maps = []
    for map_name, map_data in sorted_maps:
        # Убираем префикс de_ для краткости
        display_name = map_name.replace('de_', '').capitalize()
        
        top_maps.append({
            'name': display_name,
            'matches': map_data.get('matches', 0),
            'winrate': map_data.get('winrate', 0),
            'kd_ratio': map_data.get('kd_ratio', 0),
            'adr': map_data.get('adr', 0),
            'rating': map_data.get('hltv_rating', 1.0)
        })
    
    return top_maps


def format_enhanced_comparison(player1_stats: Dict[str, Any], player2_stats: Dict[str, Any]) -> str:
    """
    Форматирует улучшенное сравнение двух игроков с индикаторами и детальной статистикой
    
    Args:
        player1_stats: Полная статистика первого игрока
        player2_stats: Полная статистика второго игрока
    
    Returns:
        str: Форматированное сравнение с визуальными индикаторами
    """
    # Извлекаем основные данные
    p1_name = player1_stats.get('nickname', 'Игрок 1')
    p2_name = player2_stats.get('nickname', 'Игрок 2')
    
    # Получаем статистику из профиля
    p1_stats = player1_stats.get('stats', {}) if 'stats' in player1_stats else player1_stats
    p2_stats = player2_stats.get('stats', {}) if 'stats' in player2_stats else player2_stats
    
    text = f"⚔️ <b>Детальное сравнение игроков</b>\n\n"
    text += f"<b>{p1_name}</b> 🆚 <b>{p2_name}</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Основная информация с индикаторами
    text += "🎯 <b>Основная информация:</b>\n"
    
    # Уровень
    level1 = p1_stats.get('level', p1_stats.get('skill_level', 0))
    level2 = p2_stats.get('level', p2_stats.get('skill_level', 0))
    text += f"Уровень: <b>{level1}</b> | <b>{level2}</b>\n"
    
    # ELO
    elo1 = p1_stats.get('elo', p1_stats.get('faceit_elo', 0))
    elo2 = p2_stats.get('elo', p2_stats.get('faceit_elo', 0))
    text += f"ELO: <b>{elo1}</b> | <b>{elo2}</b>\n\n"
    
    # Статистика матчей
    text += "📊 <b>Статистика матчей:</b>\n"
    
    # Матчи
    matches1 = p1_stats.get('matches', 0)
    matches2 = p2_stats.get('matches', 0)
    text += f"Матчи: <b>{matches1}</b> | <b>{matches2}</b>\n"
    
    # Победы (без индикаторов)
    wins1 = p1_stats.get('wins', 0)
    wins2 = p2_stats.get('wins', 0)
    text += f"Победы: <b>{wins1}</b> | <b>{wins2}</b>\n"
    
    # Винрейт с индикаторами
    winrate1 = p1_stats.get('winrate', 0)
    winrate2 = p2_stats.get('winrate', 0)
    ind1, ind2 = get_indicator(winrate1, winrate2)
    text += f"Винрейт: {format_value_with_indicator(winrate1, ind1)}% | {format_value_with_indicator(winrate2, ind2)}%\n\n"
    
    # Основные показатели
    text += "💀 <b>Основные показатели:</b>\n"
    
    # K/D с индикаторами
    kd1 = p1_stats.get('kd_ratio', p1_stats.get('average_kd', 0))
    kd2 = p2_stats.get('kd_ratio', p2_stats.get('average_kd', 0))
    ind1, ind2 = get_indicator(kd1, kd2)
    text += f"K/D: {format_value_with_indicator(kd1, ind1, 2)} | {format_value_with_indicator(kd2, ind2, 2)}\n"
    
    # K/R с индикаторами
    kpr1 = p1_stats.get('kpr', p1_stats.get('average_kpr', 0))
    kpr2 = p2_stats.get('kpr', p2_stats.get('average_kpr', 0))
    if kpr1 > 0 and kpr2 > 0:
        ind1, ind2 = get_indicator(kpr1, kpr2)
        text += f"K/R: {format_value_with_indicator(kpr1, ind1, 2)} | {format_value_with_indicator(kpr2, ind2, 2)}\n"
    
    # Headshots с индикаторами
    hs1 = p1_stats.get('avg_headshot_percentage', p1_stats.get('headshots_avg', 0))
    hs2 = p2_stats.get('avg_headshot_percentage', p2_stats.get('headshots_avg', 0))
    ind1, ind2 = get_indicator(hs1, hs2)
    text += f"HS%: {format_value_with_indicator(hs1, ind1)}% | {format_value_with_indicator(hs2, ind2)}%\n\n"
    
    # Урон и эффективность
    text += "💥 <b>Урон и эффективность:</b>\n"
    
    # ADR
    adr1 = p1_stats.get('adr', 0)
    adr2 = p2_stats.get('adr', 0)
    ind1, ind2 = get_indicator(adr1, adr2)
    text += f"ADR: {format_value_with_indicator(adr1, ind1)} | {format_value_with_indicator(adr2, ind2)}\n"
    
    # Ослепления за игру
    flash1 = p1_stats.get('avg_flash_assists_per_match', 0)
    flash2 = p2_stats.get('avg_flash_assists_per_match', 0)
    ind1, ind2 = get_indicator(flash1, flash2)
    text += f"Ослеплений за игру: {format_value_with_indicator(flash1, ind1)} | {format_value_with_indicator(flash2, ind2)}\n"
    
    # Урон гранатами за игру
    grenade1 = p1_stats.get('avg_grenade_damage_per_match', 0)
    grenade2 = p2_stats.get('avg_grenade_damage_per_match', 0)
    ind1, ind2 = get_indicator(grenade1, grenade2)
    text += f"Урон гранатами за игру: {format_value_with_indicator(grenade1, ind1)} | {format_value_with_indicator(grenade2, ind2)}\n"
    
    # Урон молотовых за игру
    molotov1 = p1_stats.get('avg_molotov_damage_per_match', 0)
    molotov2 = p2_stats.get('avg_molotov_damage_per_match', 0)
    ind1, ind2 = get_indicator(molotov1, molotov2)
    text += f"Урон молотовых за игру: {format_value_with_indicator(molotov1, ind1)} | {format_value_with_indicator(molotov2, ind2)}\n\n"
    
    # Серии убийств
    text += "🔥 <b>Серии убийств:</b>\n"
    
    # Эйсы
    aces1 = p1_stats.get('total_aces', 0)
    aces2 = p2_stats.get('total_aces', 0)
    ind1, ind2 = get_indicator(aces1, aces2)
    text += f"Эйсов (5к): {format_value_with_indicator(aces1, ind1, 0)} | {format_value_with_indicator(aces2, ind2, 0)}\n"
    
    # 4к убийств
    quadro1 = p1_stats.get('total_quadro_kills', 0)
    quadro2 = p2_stats.get('total_quadro_kills', 0)
    ind1, ind2 = get_indicator(quadro1, quadro2)
    text += f"4к убийств: {format_value_with_indicator(quadro1, ind1, 0)} | {format_value_with_indicator(quadro2, ind2, 0)}\n"
    
    # 3к убийств
    triple1 = p1_stats.get('total_triple_kills', 0)
    triple2 = p2_stats.get('total_triple_kills', 0)
    ind1, ind2 = get_indicator(triple1, triple2)
    text += f"3к убийств: {format_value_with_indicator(triple1, ind1, 0)} | {format_value_with_indicator(triple2, ind2, 0)}\n"
    
    # Мульти-килл за матч
    multi1 = p1_stats.get('multi_kills_per_match', 0)
    multi2 = p2_stats.get('multi_kills_per_match', 0)
    ind1, ind2 = get_indicator(multi1, multi2)
    text += f"Мульти-килл за матч (3+): {format_value_with_indicator(multi1, ind1, 3)} | {format_value_with_indicator(multi2, ind2, 3)}\n\n"
    
    # Клатчи
    text += "🏆 <b>Клатчи:</b>\n"
    
    # 1v1
    clutch1v1_total1 = p1_stats.get('clutch_1v1_total', 0)
    clutch1v1_pct1 = p1_stats.get('clutch_1v1_percentage', 0)
    clutch1v1_total2 = p2_stats.get('clutch_1v1_total', 0)
    clutch1v1_pct2 = p2_stats.get('clutch_1v1_percentage', 0)
    ind1, ind2 = get_indicator(clutch1v1_pct1, clutch1v1_pct2)
    text += f"1v1: {format_value_with_indicator(clutch1v1_total1, ind1, 0)} ({clutch1v1_pct1:.0f}% побед) | {format_value_with_indicator(clutch1v1_total2, ind2, 0)} ({clutch1v1_pct2:.0f}% побед)\n"
    
    # 1v2
    clutch1v2_total1 = p1_stats.get('clutch_1v2_total', 0)
    clutch1v2_pct1 = p1_stats.get('clutch_1v2_percentage', 0)
    clutch1v2_total2 = p2_stats.get('clutch_1v2_total', 0)
    clutch1v2_pct2 = p2_stats.get('clutch_1v2_percentage', 0)
    ind1, ind2 = get_indicator(clutch1v2_pct1, clutch1v2_pct2)
    text += f"1v2: {format_value_with_indicator(clutch1v2_total1, ind1, 0)} ({clutch1v2_pct1:.0f}% побед) | {format_value_with_indicator(clutch1v2_total2, ind2, 0)} ({clutch1v2_pct2:.0f}% побед)\n\n"
    
    
    return text


async def get_last_matches_comparison(player1_id: str, player2_id: str, matches_count: int = 10) -> Dict[str, Any]:
    """
    Получает сравнение последних N матчей двух игроков
    
    Args:
        player1_id: ID первого игрока
        player2_id: ID второго игрока
        matches_count: Количество матчей для сравнения
    
    Returns:
        Словарь со сравнительной статистикой последних матчей
    """
    from faceit_client import faceit_client
    
    try:
        # Получаем историю матчей для обоих игроков
        p1_history = await faceit_client.get_player_history(player1_id, limit=matches_count)
        p2_history = await faceit_client.get_player_history(player2_id, limit=matches_count)
        
        if not p1_history or not p2_history:
            return {}
        
        # Анализируем матчи
        p1_stats = await analyze_matches_stats(p1_history.get('items', []), player1_id)
        p2_stats = await analyze_matches_stats(p2_history.get('items', []), player2_id)
        
        return {
            'player1': p1_stats,
            'player2': p2_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting last matches comparison: {e}")
        return {}


async def analyze_matches_stats(matches: List[Dict], player_id: str) -> Dict[str, Any]:
    """
    Анализирует статистику списка матчей для игрока
    
    Args:
        matches: Список матчей
        player_id: ID игрока
    
    Returns:
        Агрегированная статистика матчей
    """
    from faceit_client import faceit_client
    
    stats = {
        'total_matches': len(matches),
        'wins': 0,
        'losses': 0,
        'total_kills': 0,
        'total_deaths': 0,
        'total_assists': 0,
        'total_adr': 0,
        'total_rating': 0,
        'matches_with_stats': 0
    }
    
    for match in matches:
        # Определяем результат
        player_won = faceit_client._determine_player_result(match, player_id)
        if player_won is True:
            stats['wins'] += 1
        elif player_won is False:
            stats['losses'] += 1
        
        # Пытаемся получить статистику матча
        match_id = match.get('match_id')
        if match_id:
            match_stats = await faceit_client.get_player_stats_from_match(match_id, player_id)
            if match_stats:
                stats['total_kills'] += match_stats.get('kills', 0)
                stats['total_deaths'] += match_stats.get('deaths', 0)
                stats['total_assists'] += match_stats.get('assists', 0)
                stats['total_adr'] += match_stats.get('adr', 0)
                stats['total_rating'] += faceit_client.calculate_hltv_rating(match_stats)  # Рейтинг игрока
                stats['matches_with_stats'] += 1
    
    # Рассчитываем средние
    if stats['matches_with_stats'] > 0:
        stats['avg_kills'] = stats['total_kills'] / stats['matches_with_stats']
        stats['avg_deaths'] = stats['total_deaths'] / stats['matches_with_stats']
        stats['avg_assists'] = stats['total_assists'] / stats['matches_with_stats']
        stats['avg_adr'] = stats['total_adr'] / stats['matches_with_stats']
        stats['avg_rating'] = stats['total_rating'] / stats['matches_with_stats']
        stats['kd_ratio'] = stats['total_kills'] / max(stats['total_deaths'], 1)
    
    stats['winrate'] = (stats['wins'] / stats['total_matches'] * 100) if stats['total_matches'] > 0 else 0
    
    return stats