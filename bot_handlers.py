from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import re

from keyboards import *
from faceit_client import faceit_client
from storage import storage


class BotStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_custom_number = State()
    waiting_for_player_nickname = State()
    waiting_for_match_url = State()


router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли уже привязанный профиль
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if faceit_id:
        # Пользователь уже зарегистрирован
        user_data = storage.get_user(user_id)
        await message.answer(
            f"🎮 Добро пожаловать обратно, {user_data.get('nickname', 'Игрок')}!\n\n"
            f"Выберите нужный раздел:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Новый пользователь
        await message.answer(
            "🎮 Добро пожаловать в FACEIT CS2 статистику!\n\n"
            "Для начала работы введите ваш никнейм на FACEIT:",
            reply_markup=None
        )
        await state.set_state(BotStates.waiting_for_nickname)


@router.message(StateFilter(BotStates.waiting_for_nickname))
async def process_nickname(message: Message, state: FSMContext):
    """Обработка ввода никнейма"""
    nickname = message.text.strip()
    user_id = message.from_user.id
    
    if len(nickname) < 2:
        await message.answer("❌ Никнейм слишком короткий. Попробуйте еще раз:")
        return
    
    # Ищем игрока в FACEIT API
    await message.answer("🔍 Ищем ваш профиль на FACEIT...")
    
    player_data = await faceit_client.find_player_by_nickname(nickname)
    
    if not player_data:
        await message.answer(
            f"❌ Игрок с никнеймом '{nickname}' не найден на FACEIT.\n\n"
            f"Проверьте правильность написания и попробуйте еще раз:"
        )
        return
    
    # Сохраняем данные пользователя
    faceit_id = player_data['player_id']
    storage.set_user_faceit_data(user_id, faceit_id, nickname)
    
    await message.answer(
        f"✅ Профиль найден и привязан!\n\n"
        f"👤 Игрок: {player_data['nickname']}\n"
        f"🏆 Уровень: {player_data.get('games', {}).get('cs2', {}).get('skill_level', 'N/A')}\n"
        f"⚡ ELO: {player_data.get('games', {}).get('cs2', {}).get('faceit_elo', 'N/A')}\n\n"
        f"Выберите нужный раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите нужный раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "player_stats")
async def player_stats_menu(callback: CallbackQuery):
    """Меню статистики игрока"""
    await callback.message.edit_text(
        "📊 Статистика игрока\n\nВыберите тип статистики:",
        reply_markup=get_player_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "stats_overall")
async def show_overall_stats(callback: CallbackQuery):
    """Показать общую статистику"""
    user_id = callback.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль не привязан. Используйте /start для привязки профиля.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    await callback.message.edit_text("🔄 Загружаем статистику...")
    
    # Получаем данные игрока и статистику
    player_data = await faceit_client.get_player_details(faceit_id)
    stats_data = await faceit_client.get_player_stats(faceit_id)
    
    if not player_data or not stats_data:
        await callback.message.edit_text(
            "❌ Не удалось загрузить статистику. Попробуйте позже.",
            reply_markup=get_back_keyboard("player_stats")
        )
        return
    
    # Форматируем статистику
    formatted_stats = faceit_client.format_player_stats(player_data, stats_data)
    
    if not formatted_stats:
        await callback.message.edit_text(
            "❌ Нет доступной статистики для CS2.",
            reply_markup=get_back_keyboard("player_stats")
        )
        return
    
    # Рассчитываем до следующего уровня
    current_elo = formatted_stats['elo']
    current_level = formatted_stats['level']
    next_level_elo = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000][min(current_level, 9)]
    elo_to_next = max(0, next_level_elo - current_elo) if current_level < 10 else 0
    
    stats_text = f"""📊 **Общая статистика**
    
👤 **Игрок:** {formatted_stats['nickname']}
🏆 **Уровень:** {formatted_stats['level']}
⚡ **ELO:** {formatted_stats['elo']:,}
📈 **До следующего уровня:** {elo_to_next:,}

🎮 **Матчи:** {formatted_stats['matches']:,}
🏆 **Победы:** {formatted_stats['wins']:,}
📊 **Винрейт:** {formatted_stats['winrate']}%

💀 **K/D/A:** {formatted_stats['kills']:,}/{formatted_stats['deaths']:,}/{formatted_stats['assists']:,}
⚔️ **K/D:** {formatted_stats['kd_ratio']}
💥 **ADR:** {formatted_stats['adr']}
🎯 **Рейтинг игрока:** {formatted_stats['hltv_rating']}
📍 **KAST:** {formatted_stats['kast']}%

🎯 **Хедшоты:** {formatted_stats['headshots']}%
⚡ **Первые убийства:** {formatted_stats['first_kills']:,}
💀 **Первые смерти:** {formatted_stats['first_deaths']:,}
💡 **Флеш ассисты:** {formatted_stats['flash_assists']:,}
💣 **Урон гранатами:** {formatted_stats['utility_damage']:,}
🔥 **HE урон:** {formatted_stats['he_damage']:,}
🔥 **Урон молотов:** {formatted_stats['molotov_damage']:,}
😵‍💫 **Ослеплений:** {formatted_stats['enemies_flashed']:,}"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_keyboard("player_stats"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "stats_maps")
async def show_maps_stats(callback: CallbackQuery):
    """Показать статистику по картам"""
    await callback.message.edit_text(
        "🗺️ Статистика по картам\n\nВыберите карту:",
        reply_markup=get_maps_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("map_"))
async def show_map_stats(callback: CallbackQuery):
    """Показать статистику по конкретной карте"""
    user_id = callback.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    map_name = callback.data.replace("map_", "").replace("_", " ").title()
    
    if not faceit_id:
        await callback.message.edit_text(
            "❌ Профиль не привязан.",
            reply_markup=get_back_keyboard("stats_maps")
        )
        return
    
    await callback.message.edit_text("🔄 Загружаем статистику...")
    
    player_data = await faceit_client.get_player_details(faceit_id)
    stats_data = await faceit_client.get_player_stats(faceit_id)
    
    if not player_data or not stats_data:
        await callback.message.edit_text(
            "❌ Не удалось загрузить статистику.",
            reply_markup=get_back_keyboard("stats_maps")
        )
        return
    
    formatted_stats = faceit_client.format_player_stats(player_data, stats_data)
    
    if not formatted_stats or 'maps' not in formatted_stats:
        await callback.message.edit_text(
            "❌ Нет статистики по картам.",
            reply_markup=get_back_keyboard("stats_maps")
        )
        return
    
    # Ищем статистику по карте
    map_stats = None
    for map_key, stats in formatted_stats['maps'].items():
        if map_name.lower() in map_key.lower():
            map_stats = stats
            break
    
    if not map_stats or map_stats['matches'] == 0:
        await callback.message.edit_text(
            f"❌ Нет статистики по карте {map_name}.",
            reply_markup=get_back_keyboard("stats_maps")
        )
        return
    
    stats_text = f"""🗺️ **{map_name}**

🎮 **Матчи:** {map_stats['matches']:,}
🏆 **Победы:** {map_stats['wins']:,}
📊 **Винрейт:** {map_stats['winrate']}%

💀 **K/D/A:** {map_stats['kills']:,}/{map_stats['deaths']:,}/{map_stats['assists']:,}
⚔️ **K/D:** {map_stats['kd_ratio']}
💥 **ADR:** {map_stats['adr']}
🎯 **Рейтинг:** {map_stats['hltv_rating']}"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_keyboard("stats_maps"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "stats_session")
async def show_session_stats(callback: CallbackQuery):
    """Показать статистику за сессию"""
    user_id = callback.from_user.id
    session_data = storage.get_session(user_id)
    
    if not session_data['matches']:
        await callback.message.edit_text(
            "❌ Нет матчей в текущей сессии (последние 12 часов).",
            reply_markup=get_back_keyboard("player_stats")
        )
        return
    
    # Подсчитываем статистику сессии
    matches = session_data['matches']
    total_matches = len(matches)
    wins = sum(1 for match in matches if match.get('won', False))
    
    total_kills = sum(match.get('kills', 0) for match in matches)
    total_deaths = sum(match.get('deaths', 0) for match in matches)
    total_assists = sum(match.get('assists', 0) for match in matches)
    
    kd_ratio = round(total_kills / max(total_deaths, 1), 2)
    avg_adr = round(sum(match.get('adr', 0) for match in matches) / total_matches, 1) if total_matches > 0 else 0
    avg_hltv = round(sum(match.get('hltv_rating', 0) for match in matches) / total_matches, 2) if total_matches > 0 else 0
    winrate = round((wins / total_matches) * 100, 1) if total_matches > 0 else 0
    
    session_start = session_data['start_time'].strftime("%d.%m.%Y %H:%M")
    
    stats_text = f"""⏰ **Статистика за сессию**
📅 **Начало сессии:** {session_start}

🎮 **Матчи:** {total_matches}
🏆 **Победы:** {wins}
📊 **Винрейт:** {winrate}%

💀 **K/D/A:** {total_kills}/{total_deaths}/{total_assists}
⚔️ **K/D:** {kd_ratio}
💥 **Средний ADR:** {avg_adr}
🎯 **Средний рейтинг:** {avg_hltv}"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_keyboard("player_stats"),
        parse_mode="Markdown"
    )
    await callback.answer()


# ОТКЛЮЧЕНО: Этот обработчик конфликтует с profile_handler.py
# @router.callback_query(F.data == "profile")
# async def show_profile(callback: CallbackQuery):
#     """Показать профиль пользователя"""
#     user_id = callback.from_user.id
#     user_data = storage.get_user(user_id)
#     
#     if not user_data:
#         await callback.message.edit_text(
#             "❌ Профиль не найден. Используйте /start для привязки профиля.",
#             reply_markup=get_back_to_main_keyboard()
#         )
#         return
#     
#     linked_date = user_data.get('linked_at', datetime.now()).strftime("%d.%m.%Y")
#     settings = storage.get_user_settings(user_id)
#     
#     profile_text = f"""👤 **Ваш профиль**
# 
# 🎮 **Никнейм:** {user_data.get('nickname', 'Неизвестно')}
# 🆔 **FACEIT ID:** {user_data.get('faceit_id', 'Неизвестно')}
# 📅 **Привязан:** {linked_date}
# 
# ⚙️ **Настройки:**
# 🔔 Уведомления: {'Включены' if settings.get('match_notifications', True) else 'Выключены'}
# ⭐ Подписка: {settings.get('subscription_type', 'standard').title()}"""
#     
#     await callback.message.edit_text(
#         profile_text,
#         reply_markup=get_profile_keyboard(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()


# ОТКЛЮЧЕНО: Этот обработчик конфликтует с profile_handler.py
# @router.callback_query(F.data == "change_profile")
# async def change_profile(callback: CallbackQuery, state: FSMContext):
#     """Смена профиля"""
#     await callback.message.edit_text(
#         "🔄 Смена профиля\n\nВведите новый никнейм FACEIT:",
#         reply_markup=get_back_to_main_keyboard()
#     )
#     await state.set_state(BotStates.waiting_for_nickname)
#     await callback.answer()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Показать настройки"""
    await callback.message.edit_text(
        "⚙️ Настройки\n\nВыберите что хотите изменить:",
        reply_markup=get_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings_notifications")
async def settings_notifications(callback: CallbackQuery):
    """Настройки уведомлений"""
    user_id = callback.from_user.id
    settings = storage.get_user_settings(user_id)
    enabled = settings.get('match_notifications', True)
    
    status_text = "включены" if enabled else "выключены"
    
    await callback.message.edit_text(
        f"🔔 Уведомления о завершении матчей сейчас **{status_text}**.\n\n"
        f"Нажмите на кнопку ниже, чтобы изменить:",
        reply_markup=get_notifications_toggle_keyboard(enabled),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_notifications_"))
async def toggle_notifications(callback: CallbackQuery):
    """Переключить уведомления"""
    user_id = callback.from_user.id
    action = callback.data.split("_")[-1]
    new_status = action == "enable"
    
    storage.update_user_settings(user_id, {'match_notifications': new_status})
    
    status_text = "включены" if new_status else "выключены"
    
    await callback.message.edit_text(
        f"✅ Уведомления о матчах **{status_text}**.",
        reply_markup=get_back_keyboard("settings"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать помощь"""
    await callback.message.edit_text(
        "❓ Помощь\n\nВыберите интересующий раздел:",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_functions")
async def help_functions(callback: CallbackQuery):
    """Описание функций бота"""
    help_text = """📖 **Описание функций**

📊 **Статистика игрока** - детальная статистика по FACEIT
• Общая статистика - ELO, K/D, ADR, HLTV рейтинг
• По картам - статистика на каждой карте CS2  
• За сессию - статистика за последние 12 часов

📝 **История матчей** - просмотр последних матчей с результатами

📈 **Анализ формы** - сравнение статистики за разные периоды

🎮 **Последний матч** - детали последнего матча + автоуведомления

⚔️ **Сравнение игроков** - сравнение статистики между игроками

🔍 **Анализ матча** - анализ команд по ссылке на матч

👤 **Профиль** - управление привязанным профилем

⚙️ **Настройки** - уведомления и подписка"""
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_back_keyboard("help"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "help_rating")
async def help_rating(callback: CallbackQuery):
    """Объяснение рейтинга игрока"""
    rating_text = """⭐ **Как считается рейтинг игрока**

Рейтинг игрока - это комплексная оценка эффективности, учитывающая:

📊 **Компоненты рейтинга:**
• KPR (Kills per Round) - убийства за раунд
• DPR (Deaths per Round) - смерти за раунд  
• KAST - участие в раундах (%)
• ADR (Average Damage per Round) - урон за раунд
• Impact Rating - влияние на игру

📈 **Шкала рейтинга:**
• 1.30+ - Исключительно
• 1.15+ - Отлично  
• 1.00+ - Хорошо
• 0.85+ - Средне
• 0.85- - Плохо

Impact учитывает важность убийств (многофраги, клатчи, первые убийства)."""
    
    await callback.message.edit_text(
        hltv_text,
        reply_markup=get_back_keyboard("help"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "help_contact")
async def help_contact(callback: CallbackQuery):
    """Контакт с разработчиком"""
    contact_text = (
        "💬 **Связь с разработчиком**\n\n"
        "📧 **Email:** faceit.cs2.bot@gmail.com\n"
        "💬 **Telegram:** @cs2_faceit_support\n"
        "🐛 **GitHub Issues:** github.com/cs2-faceit-bot/issues\n\n"
        "📝 **О чем можно писать:**\n"
        "• Сообщения об ошибках\n"
        "• Предложения по улучшению\n"
        "• Вопросы по использованию\n"
        "• Проблемы с подключением FACEIT\n\n"
        "⚡ **Время ответа:** обычно в течение 24 часов\n\n"
        "🔔 При обращении укажите ваш Telegram ID: `{}`".format(callback.from_user.id)
    )
    
    await callback.message.edit_text(
        contact_text,
        reply_markup=get_back_keyboard("help"),
        parse_mode="Markdown"
    )
    await callback.answer()


# Обработчики для неопределенных callback'ов
@router.callback_query()
async def unknown_callback(callback: CallbackQuery):
    """Обработчик неизвестных callback'ов"""
    await callback.answer("❌ Неизвестная команда")


# Обработчик текстовых сообщений вне состояний
@router.message()
async def unknown_message(message: Message):
    """Обработчик неизвестных сообщений"""
    await message.answer(
        "❓ Не понимаю эту команду. Используйте меню для навигации:",
        reply_markup=get_main_menu_keyboard()
    )