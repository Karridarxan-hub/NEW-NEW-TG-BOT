"""
Хендлер для функционала сравнения игроков.
Включает FSM состояния, работу с данными пользователей и красивое отображение.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, List, Any, Optional
import asyncio

from storage import storage
from faceit_client import faceit_client


class ComparisonStates(StatesGroup):
    """FSM состояния для функционала сравнения игроков."""
    waiting_for_nickname = State()


router = Router()


async def get_comparison_keyboard(user_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Создает динамическую клавиатуру для меню сравнения.
    
    Args:
        user_data: Данные пользователя
        
    Returns:
        InlineKeyboardMarkup: Клавиатура меню сравнения
    """
    comparison_players = user_data.get('comparison_players', [])
    players_count = len(comparison_players)
    
    keyboard = []
    
    # Кнопка добавления себя в сравнение
    keyboard.append([InlineKeyboardButton(
        text="➕ Добавить себя в сравнение",
        callback_data="comparison_add_self"
    )])
    
    # Кнопка добавления нового игрока
    keyboard.append([InlineKeyboardButton(
        text="🔍 Добавить нового игрока",
        callback_data="comparison_add_player"
    )])
    
    # Кнопка сравнения (появляется только при 2 игроках)
    if players_count == 2:
        keyboard.append([InlineKeyboardButton(
            text="⚔️ Получить сравнение",
            callback_data="comparison_compare"
        )])
    
    # Кнопка очистки данных (если есть игроки)
    if players_count > 0:
        keyboard.append([InlineKeyboardButton(
            text="🗑️ Очистить данные",
            callback_data="comparison_clear"
        )])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="main_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def format_comparison_menu_text(user_data: Dict[str, Any]) -> str:
    """
    Форматирует текст меню сравнения с информацией о выбранных игроках.
    
    Args:
        user_data: Данные пользователя
        
    Returns:
        str: Форматированный текст меню
    """
    comparison_players = user_data.get('comparison_players', [])
    
    text = "🆚 <b>Сравнение игроков</b>\n\n"
    
    if not comparison_players:
        text += "📋 Список для сравнения пуст\n"
        text += "Добавьте игроков для начала сравнения"
    else:
        text += f"📋 Выбрано игроков: {len(comparison_players)}/2\n\n"
        
        for i, player in enumerate(comparison_players, 1):
            text += f"{i}. <b>{player['nickname']}</b>\n"
            text += f"   🎯 Уровень: {player.get('skill_level', 'N/A')}\n"
            text += f"   🏆 ELO: {player.get('faceit_elo', 'N/A')}\n\n"
        
        if len(comparison_players) == 2:
            text += "✅ Готово к сравнению!"
        else:
            text += f"⏳ Нужно еще {2 - len(comparison_players)} игрок(ов)"
    
    return text


async def get_player_comparison_stats(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает статистику игрока для сравнения из полного профиля.
    
    Args:
        player_data: Данные игрока от FACEIT API
        
    Returns:
        Dict[str, Any]: Статистика для сравнения
    """
    stats = {}
    
    # Основная информация
    stats['nickname'] = player_data.get('nickname', 'N/A')
    stats['skill_level'] = player_data.get('skill_level', 0)
    stats['faceit_elo'] = player_data.get('faceit_elo', 0)
    
    # Статистика из lifetime stats
    lifetime = player_data.get('lifetime', {})
    stats['matches'] = int(lifetime.get('Matches', 0))
    stats['wins'] = int(lifetime.get('Wins', 0))
    stats['winrate'] = round(stats['wins'] / max(stats['matches'], 1) * 100, 1)
    
    stats['avg_kills'] = float(lifetime.get('Average Kills', 0))
    stats['avg_deaths'] = float(lifetime.get('Average Deaths', 1))  # Избегаем деления на 0
    stats['avg_assists'] = float(lifetime.get('Average Assists', 0))
    stats['kd_ratio'] = round(stats['avg_kills'] / max(stats['avg_deaths'], 1), 2)
    
    stats['headshots_percent'] = float(lifetime.get('Average Headshots %', 0))
    
    # Дополнительная статистика
    stats['adr'] = float(lifetime.get('ADR', 0))
    stats['flash_assists'] = float(lifetime.get('Flash Assists', 0))
    stats['kast'] = float(lifetime.get('KAST', 0))
    stats['hltv_rating'] = float(lifetime.get('HLTV Rating 2.1', 0))
    
    # Статистика первых убийств/смертей
    stats['first_kills'] = float(lifetime.get('First Kills', 0))
    stats['first_deaths'] = float(lifetime.get('First Deaths', 0))
    
    # Статистика гранат
    stats['grenade_damage'] = float(lifetime.get('Grenade Damage', 0))
    stats['molotov_damage'] = float(lifetime.get('Molotov Damage', 0))
    stats['enemies_flashed'] = float(lifetime.get('Enemies Flashed', 0))
    
    return stats


def format_comparison_table(player1_stats: Dict[str, Any], player2_stats: Dict[str, Any]) -> str:
    """
    Форматирует сравнение двух игроков в виде красивой таблицы.
    
    Args:
        player1_stats: Статистика первого игрока
        player2_stats: Статистика второго игрока
        
    Returns:
        str: Форматированная таблица сравнения
    """
    p1_name = player1_stats['nickname']
    p2_name = player2_stats['nickname']
    
    text = f"⚔️ <b>Сравнение игроков</b>\n\n"
    text += f"<b>{p1_name}</b> 🆚 <b>{p2_name}</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Основная информация
    text += "🎯 <b>Основная информация:</b>\n"
    text += f"Уровень: <b>{player1_stats['skill_level']}</b> | <b>{player2_stats['skill_level']}</b>\n"
    text += f"ELO: <b>{player1_stats['faceit_elo']}</b> | <b>{player2_stats['faceit_elo']}</b>\n\n"
    
    # Статистика матчей
    text += "📊 <b>Статистика матчей:</b>\n"
    text += f"Матчи: <b>{player1_stats['matches']}</b> | <b>{player2_stats['matches']}</b>\n"
    text += f"Победы: <b>{player1_stats['wins']}</b> | <b>{player2_stats['wins']}</b>\n"
    text += f"Винрейт: <b>{player1_stats['winrate']}%</b> | <b>{player2_stats['winrate']}%</b>\n\n"
    
    # Основные показатели
    text += "💀 <b>Основные показатели:</b>\n"
    text += f"Ср. килы: <b>{player1_stats['avg_kills']:.1f}</b> | <b>{player2_stats['avg_kills']:.1f}</b>\n"
    text += f"Ср. смерти: <b>{player1_stats['avg_deaths']:.1f}</b> | <b>{player2_stats['avg_deaths']:.1f}</b>\n"
    text += f"Ср. ассисты: <b>{player1_stats['avg_assists']:.1f}</b> | <b>{player2_stats['avg_assists']:.1f}</b>\n"
    text += f"K/D: <b>{player1_stats['kd_ratio']}</b> | <b>{player2_stats['kd_ratio']}</b>\n"
    text += f"HS%: <b>{player1_stats['headshots_percent']:.1f}%</b> | <b>{player2_stats['headshots_percent']:.1f}%</b>\n\n"
    
    # Продвинутые показатели
    text += "📈 <b>Продвинутые показатели:</b>\n"
    text += f"ADR: <b>{player1_stats['adr']:.1f}</b> | <b>{player2_stats['adr']:.1f}</b>\n"
    text += f"Flash Assists: <b>{player1_stats['flash_assists']:.1f}</b> | <b>{player2_stats['flash_assists']:.1f}</b>\n"
    text += f"KAST: <b>{player1_stats['kast']:.1f}%</b> | <b>{player2_stats['kast']:.1f}%</b>\n"
    text += f"HLTV 2.1: <b>{player1_stats['hltv_rating']:.2f}</b> | <b>{player2_stats['hltv_rating']:.2f}</b>\n\n"
    
    # Статистика Entry
    text += "⚡ <b>Entry статистика:</b>\n"
    text += f"Первые килы: <b>{player1_stats['first_kills']:.1f}</b> | <b>{player2_stats['first_kills']:.1f}</b>\n"
    text += f"Первые смерти: <b>{player1_stats['first_deaths']:.1f}</b> | <b>{player2_stats['first_deaths']:.1f}</b>\n\n"
    
    # Статистика утилит
    text += "💥 <b>Статистика утилит:</b>\n"
    text += f"Урон гранат: <b>{player1_stats['grenade_damage']:.1f}</b> | <b>{player2_stats['grenade_damage']:.1f}</b>\n"
    text += f"Урон молотовов: <b>{player1_stats['molotov_damage']:.1f}</b> | <b>{player2_stats['molotov_damage']:.1f}</b>\n"
    text += f"Ослепления: <b>{player1_stats['enemies_flashed']:.1f}</b> | <b>{player2_stats['enemies_flashed']:.1f}</b>\n\n"
    
    # Определяем победителя по основным показателям
    winner_indicators = []
    if player1_stats['faceit_elo'] > player2_stats['faceit_elo']:
        winner_indicators.append(f"{p1_name} имеет выше ELO")
    elif player2_stats['faceit_elo'] > player1_stats['faceit_elo']:
        winner_indicators.append(f"{p2_name} имеет выше ELO")
        
    if player1_stats['kd_ratio'] > player2_stats['kd_ratio']:
        winner_indicators.append(f"{p1_name} имеет лучший K/D")
    elif player2_stats['kd_ratio'] > player1_stats['kd_ratio']:
        winner_indicators.append(f"{p2_name} имеет лучший K/D")
        
    if player1_stats['winrate'] > player2_stats['winrate']:
        winner_indicators.append(f"{p1_name} имеет выше винрейт")
    elif player2_stats['winrate'] > player1_stats['winrate']:
        winner_indicators.append(f"{p2_name} имеет выше винрейт")
    
    if winner_indicators:
        text += "🏆 <b>Основные преимущества:</b>\n"
        for indicator in winner_indicators:
            text += f"• {indicator}\n"
    
    return text


@router.callback_query(F.data == "comparison")
async def handle_comparison_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик главного меню сравнения игроков."""
    try:
        await state.clear()
        user_data = await state.get_data()
        
        text = await format_comparison_menu_text(user_data)
        keyboard = await get_comparison_keyboard(user_data)
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Произошла ошибка при загрузке меню сравнения")
        print(f"Error in comparison menu: {e}")


@router.callback_query(F.data == "comparison_add_self")
async def handle_add_self_to_comparison(callback: CallbackQuery, state: FSMContext):
    """Добавляет текущего пользователя в список для сравнения."""
    try:
        user_id = str(callback.from_user.id)
        user_data = await state.get_data()
        
        # Получаем никнейм пользователя из storage
        user_nickname = await storage.get(f"user:{user_id}:nickname")
        
        if not user_nickname:
            await callback.answer("❌ Сначала привяжите свой FACEIT аккаунт в настройках!")
            return
        
        comparison_players = user_data.get('comparison_players', [])
        
        # Проверяем, есть ли уже этот игрок в списке
        if any(player['nickname'] == user_nickname for player in comparison_players):
            await callback.answer("⚠️ Вы уже добавлены в список сравнения!")
            return
        
        # Проверяем лимит игроков
        if len(comparison_players) >= 2:
            await callback.answer("⚠️ Можно сравнивать только 2 игроков одновременно!")
            return
        
        # Получаем полный профиль игрока
        await callback.message.edit_text("⏳ Загружаю ваш профиль...")
        
        player_profile = await faceit_client.get_player_full_profile(user_nickname)
        if not player_profile:
            await callback.answer("❌ Не удалось загрузить ваш профиль FACEIT!")
            return
        
        # Добавляем игрока в список
        comparison_players.append({
            'nickname': user_nickname,
            'skill_level': player_profile.get('skill_level', 0),
            'faceit_elo': player_profile.get('faceit_elo', 0),
            'profile_data': player_profile
        })
        
        await state.update_data(comparison_players=comparison_players)
        
        # Обновляем меню
        text = await format_comparison_menu_text(await state.get_data())
        keyboard = await get_comparison_keyboard(await state.get_data())
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Вы добавлены в список сравнения!")
        
    except Exception as e:
        await callback.answer("Произошла ошибка при добавлении в сравнение")
        print(f"Error adding self to comparison: {e}")


@router.callback_query(F.data == "comparison_add_player")
async def handle_add_player_to_comparison(callback: CallbackQuery, state: FSMContext):
    """Запускает FSM для добавления нового игрока в сравнение."""
    try:
        user_data = await state.get_data()
        comparison_players = user_data.get('comparison_players', [])
        
        # Проверяем лимит игроков
        if len(comparison_players) >= 2:
            await callback.answer("⚠️ Можно сравнивать только 2 игроков одновременно!")
            return
        
        await state.set_state(ComparisonStates.waiting_for_nickname)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Отмена", callback_data="comparison")
        ]])
        
        await callback.message.edit_text(
            text="🔍 <b>Добавление игрока в сравнение</b>\n\n"
                 "Введите никнейм игрока FACEIT, которого хотите добавить для сравнения:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Произошла ошибка")
        print(f"Error in add player handler: {e}")


@router.message(ComparisonStates.waiting_for_nickname)
async def handle_player_nickname_input(message: Message, state: FSMContext):
    """Обрабатывает ввод никнейма игрока для добавления в сравнение."""
    try:
        nickname = message.text.strip()
        
        # Валидация никнейма
        if not nickname:
            await message.answer("❌ Пожалуйста, введите корректный никнейм!")
            return
        
        if len(nickname) < 3 or len(nickname) > 20:
            await message.answer("❌ Никнейм должен содержать от 3 до 20 символов!")
            return
        
        user_data = await state.get_data()
        comparison_players = user_data.get('comparison_players', [])
        
        # Проверяем, есть ли уже этот игрок в списке
        if any(player['nickname'].lower() == nickname.lower() for player in comparison_players):
            await message.answer("⚠️ Этот игрок уже добавлен в список сравнения!")
            return
        
        # Показываем индикатор загрузки
        loading_msg = await message.answer("⏳ Ищу игрока и загружаю его статистику...")
        
        # Получаем профиль игрока
        player_profile = await faceit_client.get_player_full_profile(nickname)
        
        if not player_profile:
            await loading_msg.edit_text("❌ Игрок с таким никнеймом не найден в FACEIT!")
            return
        
        # Добавляем игрока в список
        comparison_players.append({
            'nickname': player_profile.get('nickname', nickname),
            'skill_level': player_profile.get('skill_level', 0),
            'faceit_elo': player_profile.get('faceit_elo', 0),
            'profile_data': player_profile
        })
        
        await state.update_data(comparison_players=comparison_players)
        await state.clear()
        
        # Возвращаемся в меню сравнения
        text = await format_comparison_menu_text(await state.get_data())
        keyboard = await get_comparison_keyboard(await state.get_data())
        
        await loading_msg.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await message.delete()
        
    except Exception as e:
        await message.answer("Произошла ошибка при поиске игрока")
        print(f"Error processing nickname input: {e}")


@router.callback_query(F.data == "comparison_compare")
async def handle_compare_players(callback: CallbackQuery, state: FSMContext):
    """Выполняет сравнение двух выбранных игроков."""
    try:
        user_data = await state.get_data()
        comparison_players = user_data.get('comparison_players', [])
        
        if len(comparison_players) != 2:
            await callback.answer("⚠️ Для сравнения нужно выбрать ровно 2 игроков!")
            return
        
        await callback.message.edit_text("⏳ Анализирую статистику игроков...")
        
        # Получаем статистику для сравнения
        player1_stats = await get_player_comparison_stats(comparison_players[0]['profile_data'])
        player2_stats = await get_player_comparison_stats(comparison_players[1]['profile_data'])
        
        # Форматируем сравнение
        comparison_text = format_comparison_table(player1_stats, player2_stats)
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новое сравнение", callback_data="comparison_clear")],
            [InlineKeyboardButton(text="⬅️ Назад к меню", callback_data="comparison")]
        ])
        
        await callback.message.edit_text(
            text=comparison_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Произошла ошибка при сравнении игроков")
        print(f"Error comparing players: {e}")


@router.callback_query(F.data == "comparison_clear")
async def handle_clear_comparison(callback: CallbackQuery, state: FSMContext):
    """Очищает список игроков для сравнения."""
    try:
        await state.update_data(comparison_players=[])
        
        text = await format_comparison_menu_text(await state.get_data())
        keyboard = await get_comparison_keyboard(await state.get_data())
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("🗑️ Список игроков очищен!")
        
    except Exception as e:
        await callback.answer("Произошла ошибка при очистке данных")
        print(f"Error clearing comparison: {e}")