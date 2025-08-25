from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List, Dict, Any, Optional, Tuple
import logging
import asyncio
from datetime import datetime

from keyboards import get_form_reply_keyboard, get_main_reply_keyboard
from storage import storage
from faceit_client import faceit_client

# Создаем роутер для обработчиков анализа формы
router = Router(name="form_analysis_handler")

# Настройка логирования
logger = logging.getLogger(__name__)

# FSM состояния для анализа формы
class FormAnalysisStates(StatesGroup):
    waiting_for_custom_count = State()  # Восстанавливаем состояние для кастомного ввода

# Обработчик открытия меню анализа формы
@router.callback_query(F.data == "form_analysis")
async def show_form_analysis_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню анализа формы"""
    logger.info(f"🔍 Вызов меню анализа формы от пользователя {callback.from_user.id}")
    await state.clear()
    
    keyboard = get_form_reply_keyboard()
    logger.info(f"🔍 Создана Reply клавиатура для анализа формы")
    
    await callback.message.answer(
        "📈 <b>Анализ формы игрока</b>\n\n"
        "Выберите период для сравнения:\n"
        "• <i>10 vs 10</i> - последние 10 матчей против предыдущих 10\n"
        "• <i>20 vs 20</i> - последние 20 матчей против предыдущих 20\n"
        "• <i>50 vs 50</i> - последние 50 матчей против предыдущих 50",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики для фиксированного количества матчей
@router.callback_query(F.data.in_(["form_10", "form_20", "form_50"]))
async def analyze_form_fixed(callback: CallbackQuery, state: FSMContext):
    """Анализ формы для фиксированного количества матчей"""
    await state.clear()
    
    # Извлекаем количество матчей из callback_data
    match_count = int(callback.data.split("_")[1])
    
    await perform_form_analysis(callback, match_count)

# Обработчик для кнопки кастомного ввода
@router.callback_query(F.data == "form_custom")
async def ask_custom_form_count(callback: CallbackQuery, state: FSMContext):
    """Запросить у пользователя кастомный период для анализа формы"""
    logger.info(f"🎯 Пользователь {callback.from_user.id} нажал 'Свой период' (Inline callback) в form_analysis_handler")
    await state.clear()
    await state.set_state(FormAnalysisStates.waiting_for_custom_count)
    
    await callback.message.answer(
        "✏️ <b>Ввод периода для анализа</b>\n\n"
        "Введите количество матчей для каждого периода (от 5 до 100):\n\n"
        "💡 <i>Например: 25 (будет сравнение 25 vs 25 матчей)</i>\n\n"
        "⚠️ <i>Общее количество матчей будет в два раза больше</i>",
        parse_mode="HTML"
    )
    await callback.answer()



async def perform_form_analysis(callback, match_count: int):
    """Выполнить анализ формы игрока"""
    user_id = callback.from_user.id
    
    try:
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await callback.message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_form_reply_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.answer(
            f"🔄 Анализирую форму игрока...\n"
            f"Загружаю {match_count * 2} матчей для сравнения..."
        )
        
        # Получаем данные игрока
        player_details = await faceit_client.get_player_details(faceit_id)
        if not player_details:
            await callback.message.answer(
                "❌ Не удалось получить данные игрока.",
                reply_markup=get_form_reply_keyboard()
            )
            await callback.answer()
            return
        
        # Получаем историю матчей (нужно в два раза больше для сравнения)
        history_data = await faceit_client.get_player_history(faceit_id, limit=match_count * 2)
        
        if not history_data or not history_data.get("items"):
            await callback.message.answer(
                "❌ Не удалось загрузить историю матчей.",
                reply_markup=get_form_reply_keyboard()
            )
            await callback.answer()
            return
        
        matches = history_data["items"]
        
        if len(matches) < match_count * 2:
            available_matches = len(matches)
            adjusted_count = available_matches // 2
            
            if adjusted_count < 5:
                await callback.message.answer(
                    f"❌ Недостаточно матчей для анализа.\n"
                    f"Доступно: {available_matches}, нужно минимум 10.",
                    reply_markup=get_form_reply_keyboard()
                )
                await callback.answer()
                return
            
            match_count = adjusted_count
        
        # Разделяем матчи на два периода
        recent_matches = matches[:match_count]  # Последние N матчей
        previous_matches = matches[match_count:match_count * 2]  # Предыдущие N матчей
        
        await callback.message.answer(
            f"📊 Получаю детальную статистику матчей...\n"
            f"Период 1: {len(recent_matches)} матчей\n"
            f"Период 2: {len(previous_matches)} матчей"
        )
        
        # Анализируем оба периода
        recent_stats = await analyze_matches_period(recent_matches, faceit_id, "Текущий период")
        previous_stats = await analyze_matches_period(previous_matches, faceit_id, "Предыдущий период")
        
        # Формируем сообщение с результатами
        message_text = await format_form_analysis_result(
            recent_stats, previous_stats, match_count, 
            player_details.get('nickname', 'Unknown')
        )
        
        await callback.message.answer(
            message_text,
            reply_markup=None,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе формы для пользователя {user_id}: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при анализе формы.\n"
            "Попробуйте позже.",
            reply_markup=get_form_analysis_keyboard()
        )
    
    await callback.answer()

async def perform_form_analysis_from_message(message: Message, match_count: int):
    """Выполнить анализ формы игрока из сообщения (для кастомного ввода)"""
    user_id = message.from_user.id
    
    try:
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_form_reply_keyboard()
            )
            return
        
        loading_msg = await message.answer(
            f"🔄 Анализирую форму игрока...\n"
            f"Загружаю {match_count * 2} матчей для сравнения..."
        )
        
        # Получаем данные игрока
        player_details = await faceit_client.get_player_details(faceit_id)
        if not player_details:
            await loading_msg.edit_text(
                "❌ Не удалось получить данные игрока.",
                reply_markup=get_form_reply_keyboard()
            )
            return
        
        # Получаем историю матчей (нужно в два раза больше для сравнения)
        history_data = await faceit_client.get_player_history(faceit_id, limit=match_count * 2)
        
        if not history_data or not history_data.get("items"):
            await loading_msg.edit_text(
                "❌ Не удалось загрузить историю матчей.",
                reply_markup=get_form_reply_keyboard()
            )
            return
        
        matches = history_data["items"]
        
        if len(matches) < match_count * 2:
            available_matches = len(matches)
            adjusted_count = available_matches // 2
            
            if adjusted_count < 5:
                await loading_msg.edit_text(
                    f"❌ Недостаточно матчей для анализа.\n"
                    f"Доступно: {available_matches}, нужно минимум 10."
                )
                return
            
            match_count = adjusted_count
        
        # Разделяем матчи на два периода
        recent_matches = matches[:match_count]  # Последние N матчей
        previous_matches = matches[match_count:match_count * 2]  # Предыдущие N матчей
        
        await loading_msg.edit_text(
            f"📊 Получаю детальную статистику матчей...\n"
            f"Период 1: {len(recent_matches)} матчей\n"
            f"Период 2: {len(previous_matches)} матчей"
        )
        
        # Анализируем оба периода
        recent_stats = await analyze_matches_period(recent_matches, faceit_id, "Текущий период")
        previous_stats = await analyze_matches_period(previous_matches, faceit_id, "Предыдущий период")
        
        # Формируем сообщение с результатами
        message_text = await format_form_analysis_result(
            recent_stats, previous_stats, match_count, 
            player_details.get('nickname', 'Unknown')
        )
        
        await loading_msg.edit_text(
            message_text,
            reply_markup=None,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе формы для пользователя {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при анализе формы.\n"
            "Попробуйте позже."
        )

async def analyze_matches_period(matches: List[Dict], faceit_id: str, period_name: str) -> Dict[str, Any]:
    """Анализ статистики за определенный период матчей"""
    logger.info(f"Анализируем {period_name}: {len(matches)} матчей")
    
    # Инициализируем счетчики
    stats = {
        'total_matches': len(matches),
        'wins': 0,
        'losses': 0,
        'winrate': 0.0,
        'kills': 0,
        'deaths': 0,
        'assists': 0,
        'kd_ratio': 0.0,
        'headshots': 0,
        'headshot_percentage': 0.0,
        'total_damage': 0,
        'total_rounds': 0,
        'adr': 0.0,
        'flash_assists': 0,
        'kast_rounds': 0,
        'kast_percentage': 0.0,
        'player_rating': 0.0,
        'first_kills': 0,
        'first_deaths': 0,
        'detailed_matches': 0  # Количество матчей с детальной статистикой
    }
    
    if not matches:
        return stats
    
    # Определяем результаты матчей (быстро)
    for match in matches:
        player_result = faceit_client._determine_player_result(match, faceit_id)
        if player_result is True:
            stats['wins'] += 1
        elif player_result is False:
            stats['losses'] += 1
    
    # Параллельная загрузка детальной статистики матчей
    semaphore = asyncio.Semaphore(5)  # Ограничиваем до 5 одновременных запросов
    
    async def get_match_detailed_stats(match):
        """Получить детальную статистику одного матча"""
        match_id = match.get('match_id')
        if not match_id:
            return None
            
        async with semaphore:
            try:
                match_stats = await faceit_client.get_match_stats(match_id)
                if match_stats and 'rounds' in match_stats:
                    return extract_player_stats_from_match(match_stats, faceit_id)
                return None
            except Exception as e:
                logger.debug(f"Не удалось получить статистику матча {match_id}: {e}")
                return None
    
    # Запускаем параллельную загрузку
    tasks = [get_match_detailed_stats(match) for match in matches]
    detailed_stats_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Обрабатываем результаты
    for result in detailed_stats_results:
        if result and not isinstance(result, Exception):
            stats['detailed_matches'] += 1
            merge_player_stats(stats, result)
    
    # Рассчитываем итоговые показатели
    calculate_final_stats(stats)
    
    logger.info(f"{period_name} - детальная статистика получена для {stats['detailed_matches']} из {len(matches)} матчей")
    
    return stats

def extract_player_stats_from_match(match_stats: Dict, faceit_id: str) -> Optional[Dict]:
    """Извлекает статистику конкретного игрока из данных матча"""
    if not match_stats.get('rounds'):
        return None
    
    for round_data in match_stats['rounds']:
        for team in round_data.get('teams', []):
            for player in team.get('players', []):
                if player.get('player_id') == faceit_id:
                    player_stats = player.get('player_stats', {})
                    
                    return {
                        'kills': safe_int(player_stats.get('Kills', 0)),
                        'deaths': safe_int(player_stats.get('Deaths', 0)),
                        'assists': safe_int(player_stats.get('Assists', 0)),
                        'headshots': safe_int(player_stats.get('Headshots', 0)),
                        'damage': safe_int(player_stats.get('Damage', 0)),
                        'rounds': safe_int(round_data.get('round_stats', {}).get('Rounds', 0)),
                        'flash_assists': safe_int(player_stats.get('Flash Assists', 0)),
                        'first_kills': safe_int(player_stats.get('First Kills Round', 0)),
                        'first_deaths': safe_int(player_stats.get('First Deaths', 0)),
                        'kast': safe_int(player_stats.get('KAST', 0))
                    }
    
    return None

def merge_player_stats(total_stats: Dict, match_stats: Dict):
    """Объединяет статистику матча с общими показателями"""
    total_stats['kills'] += match_stats['kills']
    total_stats['deaths'] += match_stats['deaths']
    total_stats['assists'] += match_stats['assists']
    total_stats['headshots'] += match_stats['headshots']
    total_stats['total_damage'] += match_stats['damage']
    total_stats['total_rounds'] += match_stats['rounds']
    total_stats['flash_assists'] += match_stats['flash_assists']
    total_stats['first_kills'] += match_stats['first_kills']
    total_stats['first_deaths'] += match_stats['first_deaths']
    total_stats['kast_rounds'] += match_stats['kast']

def calculate_final_stats(stats: Dict):
    """Рассчитывает финальные показатели на основе собранных данных"""
    # Винрейт
    total_decided_matches = stats['wins'] + stats['losses']
    if total_decided_matches > 0:
        stats['winrate'] = (stats['wins'] / total_decided_matches) * 100
    
    # K/D соотношение
    if stats['deaths'] > 0:
        stats['kd_ratio'] = stats['kills'] / stats['deaths']
    else:
        stats['kd_ratio'] = stats['kills']  # Если смертей нет
    
    # Процент хедшотов
    if stats['kills'] > 0:
        stats['headshot_percentage'] = (stats['headshots'] / stats['kills']) * 100
    
    # ADR (Average Damage per Round)
    if stats['total_rounds'] > 0:
        stats['adr'] = stats['total_damage'] / stats['total_rounds']
    

async def format_form_analysis_result(
    recent_stats: Dict, 
    previous_stats: Dict, 
    match_count: int,
    nickname: str
) -> str:
    """Форматирует результат анализа формы"""
    
    message = f"📈 <b>Анализ формы игрока</b>\n"
    message += f"👤 <b>Игрок:</b> {nickname}\n"
    message += f"📊 <b>Сравнение:</b> {match_count} vs {match_count} матчей\n\n"
    
    # Период 1 (последние матчи)
    message += f"🟢 <b>Последние {match_count} матчей:</b>\n"
    message += format_period_stats(recent_stats)
    message += "\n"
    
    # Период 2 (предыдущие матчи)
    message += f"🟡 <b>Предыдущие {match_count} матчей:</b>\n"
    message += format_period_stats(previous_stats)
    message += "\n"
    
    # Сравнение изменений
    message += "📊 <b>Изменения в форме:</b>\n"
    message += format_comparison(recent_stats, previous_stats)
    
    # Добавляем информацию о качестве данных
    recent_coverage = (recent_stats['detailed_matches'] / recent_stats['total_matches']) * 100 if recent_stats['total_matches'] > 0 else 0
    previous_coverage = (previous_stats['detailed_matches'] / previous_stats['total_matches']) * 100 if previous_stats['total_matches'] > 0 else 0
    
    
    return message

def format_period_stats(stats: Dict) -> str:
    """Форматирует статистику периода"""
    text = f"• 🏆 Побед: {stats['wins']}/{stats['total_matches']} ({stats['winrate']:.1f}%)\n"
    
    # Показываем детальную статистику только если есть данные
    if stats['detailed_matches'] > 0:
        text += f"• ⚔️ K/D: {stats['kd_ratio']:.2f} "
        text += f"(K:{stats['kills']} D:{stats['deaths']} A:{stats['assists']})\n"
        text += f"• 🎯 Хедшоты: {stats['headshot_percentage']:.1f}%\n"
        text += f"• 💥 ADR: {stats['adr']:.1f}\n"
    else:
        text += "<i>Детальная статистика недоступна</i>\n"
    
    return text

def format_comparison(recent: Dict, previous: Dict) -> str:
    """Форматирует сравнение между периодами"""
    comparisons = []
    
    # Сравнение винрейта
    winrate_diff = recent['winrate'] - previous['winrate']
    winrate_emoji = "📈" if winrate_diff > 0 else "📉" if winrate_diff < 0 else "➡️"
    comparisons.append(f"• Винрейт: {winrate_emoji} {winrate_diff:+.1f}%")
    
    # Если есть детальная статистика для обоих периодов
    if recent['detailed_matches'] > 0 and previous['detailed_matches'] > 0:
        # K/D
        kd_diff = recent['kd_ratio'] - previous['kd_ratio']
        kd_emoji = "📈" if kd_diff > 0 else "📉" if kd_diff < 0 else "➡️"
        comparisons.append(f"• K/D: {kd_emoji} {kd_diff:+.3f}")
        
        # ADR
        adr_diff = recent['adr'] - previous['adr']
        adr_emoji = "📈" if adr_diff > 0 else "📉" if adr_diff < 0 else "➡️"
        comparisons.append(f"• ADR: {adr_emoji} {adr_diff:+.1f}")
        
        
        # Хедшоты
        hs_diff = recent['headshot_percentage'] - previous['headshot_percentage']
        hs_emoji = "📈" if hs_diff > 0 else "📉" if hs_diff < 0 else "➡️"
        comparisons.append(f"• Хедшоты: {hs_emoji} {hs_diff:+.1f}%")
        
    else:
        comparisons.append("<i>Недостаточно данных для детального сравнения</i>")
    
    return "\n".join(comparisons)

def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование значения в int"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(float(value.replace(',', '.')))
        except (ValueError, TypeError):
            return default
    if isinstance(value, float):
        return int(value)
    return default

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

# FSM обработчик для кастомного ввода периода анализа
@router.message(FormAnalysisStates.waiting_for_custom_count)
async def process_custom_form_count(message: Message, state: FSMContext):
    """Обработать введенное пользователем количество матчей для анализа формы"""
    user_text = message.text.strip()
    
    try:
        match_count = int(user_text)
        
        # Валидация диапазона (для анализа формы минимум 5 матчей за период)
        if match_count < 5 or match_count > 100:
            await message.answer(
                "❌ <b>Некорректное число</b>\n\n"
                "Количество матчей для каждого периода должно быть от 5 до 100.\n\n"
                "💡 <i>Например: 25 (будет анализ 25 vs 25 матчей)</i>\n\n"
                "Попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        # Очищаем состояние
        await state.clear()
        
        # Выполняем анализ формы через message
        await perform_form_analysis_from_message(message, match_count)
        
    except ValueError:
        await message.answer(
            "❌ <b>Некорректный ввод</b>\n\n"
            "Пожалуйста, введите число от 5 до 100.\n\n"
            "💡 <i>Например: 25</i>",
            parse_mode="HTML"
        )

# Reply-обработчик для кастомного ввода
@router.message(F.text == "✏️ Свой период")
async def handle_custom_form_input_reply(message: Message, state: FSMContext):
    """Reply-обработчик кастомного ввода анализа формы"""
    logger.info(f"🎯 Пользователь {message.from_user.id} нажал 'Свой период' (Reply) в form_analysis_handler")
    
    await state.clear()
    await state.set_state(FormAnalysisStates.waiting_for_custom_count)
    
    await message.answer(
        "✏️ <b>Ввод периода для анализа</b>\n\n"
        "Введите количество матчей для каждого периода (от 5 до 100):\n\n"
        "💡 <i>Например: 25 (будет сравнение 25 vs 25 матчей)</i>\n\n"
        "⚠️ <i>Общее количество матчей будет в два раза больше</i>",
        parse_mode="HTML"
    )

