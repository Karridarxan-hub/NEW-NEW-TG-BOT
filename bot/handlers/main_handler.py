from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging
import asyncio

from keyboards import (get_main_menu_keyboard, get_main_reply_keyboard, get_stats_reply_keyboard,
                      get_history_reply_keyboard, get_form_reply_keyboard, get_comparison_reply_keyboard,
                      get_help_reply_keyboard, get_profile_reply_keyboard)
from storage import storage
from faceit_client import faceit_client
from bot.handlers.profile_handler import ProfileStates

# Создаем роутер для основных обработчиков
router = Router(name="main_handler")

# Логгер
logger = logging.getLogger(__name__)

# FSM состояния для основных действий
class MainStates(StatesGroup):
    waiting_for_nickname = State()

# Обработчик команды /start
@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли уже привязанный профиль
    faceit_id = await storage.get_user_faceit_id(user_id)
    
    if faceit_id:
        # Пользователь уже зарегистрирован
        user_data = await storage.get_user(user_id)
        await message.answer(
            f"🎮 Добро пожаловать обратно, {user_data.get('nickname', 'Игрок')}!\n\n"
            f"Используйте кнопки внизу для навигации:",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        # Новый пользователь
        await message.answer(
            "🎮 Добро пожаловать в FACEIT CS2 статистику!\n\n"
            "Для начала работы введите ваш никнейм на FACEIT:",
            reply_markup=None
        )
        await state.set_state(MainStates.waiting_for_nickname)

# Обработка ввода никнейма
@router.message(StateFilter(MainStates.waiting_for_nickname))
async def process_nickname(message: Message, state: FSMContext):
    """Обработка ввода никнейма при регистрации"""
    nickname = message.text.strip()
    user_id = message.from_user.id
    
    # Валидация никнейма
    if len(nickname) < 2:
        await message.answer("❌ Никнейм слишком короткий. Попробуйте еще раз:")
        return
    
    if len(nickname) > 30:
        await message.answer("❌ Никнейм слишком длинный. Попробуйте еще раз:")
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
    await storage.save_user(user_id, faceit_id, nickname)
    
    # Очищаем состояние
    await state.clear()
    
    # Показываем главное меню
    await message.answer(
        f"✅ Профиль успешно привязан!\n\n"
        f"🎮 Игрок: {nickname}\n\n"
        f"Используйте кнопки внизу для навигации:",
        reply_markup=get_main_reply_keyboard()
    )

# Обработчик кнопки "Назад в главное меню"
@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    user_data = await storage.get_user(user_id)
    
    await callback.message.edit_text(
        f"🎮 Главное меню\n\n"
        f"Выберите нужный раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

# Обработчики для новых разделов главного меню

# История матчей - будет в новом обработчике

# Анализ формы  
@router.callback_query(F.data == "form_analysis")
async def show_form_analysis_menu(callback: CallbackQuery):
    """Показать меню анализа формы"""
    from keyboards import get_form_analysis_keyboard
    await callback.message.edit_text(
        "📈 **Анализ формы**\n\n"
        "Выберите период для сравнительного анализа:",
        parse_mode="Markdown", 
        reply_markup=get_form_analysis_keyboard()
    )
    await callback.answer()

# Сравнение игроков
@router.callback_query(F.data == "player_comparison")  
async def show_player_comparison_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню сравнения игроков"""
    from bot.handlers.comparison_handler import format_comparison_menu_text, get_comparison_keyboard
    
    user_data = await state.get_data()
    text = await format_comparison_menu_text(user_data)
    keyboard = await get_comparison_keyboard(user_data)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# Анализ текущего матча
@router.callback_query(F.data == "current_match_analysis")
async def show_current_match_analysis_menu(callback: CallbackQuery):
    """Показать меню анализа текущего матча"""
    from keyboards import get_current_match_analysis_keyboard
    await callback.message.edit_text(
        "🔍 **Анализ текущего матча**\n\n"
        "Введите ссылку на матч FACEIT для подробного анализа команд и прогноза.",
        parse_mode="Markdown",
        reply_markup=get_current_match_analysis_keyboard()
    )
    await callback.answer()

# Обработчик кнопки помощи
@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать справку"""
    from keyboards import get_help_keyboard
    await callback.message.edit_text(
        "❓ **Помощь по боту**\n\n"
        "🎮 **FACEIT CS2 Статистика Бот** - ваш персональный помощник для анализа статистики в CS2.\n\n"
        "Выберите интересующий раздел:",
        parse_mode="Markdown",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()

# =================== ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ===================

class FakeMessage:
    """Имитирует Message объект с поддержкой edit_text для reply handlers"""
    def __init__(self, original_message):
        self.original_message = original_message
    
    async def edit_text(self, text, parse_mode=None, reply_markup=None, disable_web_page_preview=None):
        """Имитируем edit_text отправкой нового сообщения"""
        try:
            await self.original_message.answer(
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in FakeMessage.edit_text: {e}")
            # Попытка без reply_markup если была ошибка
            try:
                await self.original_message.answer(text=text, parse_mode=parse_mode)
            except Exception as e2:
                logger.error(f"Second attempt failed: {e2}")
                # Самый простой вариант
                await self.original_message.answer(text)

class FakeCallback:
    """Имитирует CallbackQuery для совместимости reply и inline handlers"""
    def __init__(self, message, data=None):
        self.from_user = message.from_user
        self.message = FakeMessage(message)
        self.data = data  # Для handlers, которые используют callback.data
    
    async def answer(self, text="", show_alert=False):
        if text and show_alert:
            await self.message.original_message.answer(text)

# =================== ОБРАБОТЧИКИ REPLY-КНОПОК ===================

@router.message(F.text == "📊 Статистика")
async def handle_stats_button(message: Message):
    """Обработчик кнопки 'Статистика'"""
    await message.answer(
        "📊 **Статистика игрока**\n\n"
        "Выберите тип статистики:",
        parse_mode="Markdown",
        reply_markup=get_stats_reply_keyboard()
    )

@router.message(F.text == "📝 История")
async def handle_history_button(message: Message):
    """Обработчик кнопки 'История'"""
    await message.answer(
        "📝 **История матчей**\n\n"
        "Выберите количество матчей для просмотра:",
        parse_mode="Markdown",
        reply_markup=get_history_reply_keyboard()
    )

@router.message(F.text == "📈 Форма")
async def handle_form_button(message: Message):
    """Обработчик кнопки 'Форма'"""
    await message.answer(
        "📈 **Анализ формы**\n\n"
        "Выберите период для сравнения:",
        parse_mode="Markdown",
        reply_markup=get_form_reply_keyboard()
    )

@router.message(F.text == "🎮 Последний матч")
async def handle_last_match_button(message: Message):
    """Обработчик кнопки 'Последний матч'"""
    # Переадресуем к обработчику последнего матча
    from bot.handlers.last_match_handler import show_last_match
    
    # Используем общий FakeCallback класс
    fake_callback = FakeCallback(message)
    await show_last_match(fake_callback)

@router.message(F.text == "⚔️ Сравнение")
async def handle_comparison_button(message: Message, state: FSMContext):
    """Обработчик кнопки 'Сравнение' - только reply-кнопки"""
    from bot.handlers.comparison_handler import format_comparison_menu_text
    
    user_data = await state.get_data()
    text = await format_comparison_menu_text(user_data)
    
    await message.answer(
        text=text,
        reply_markup=get_comparison_keyboard_with_count(user_data),
        parse_mode="HTML"
    )

@router.message(F.text == "🔍 Анализ матча")
async def handle_current_match_button(message: Message):
    """Обработчик кнопки 'Анализ матча'"""
    # Переадресуем к обработчику анализа матча
    from bot.handlers.current_match_handler import show_current_match_menu
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс
    fake_callback = FakeCallback(message)
    await show_current_match_menu(fake_callback, state)

@router.message(F.text == "👤 Профиль")
async def handle_profile_button(message: Message):
    """Обработчик кнопки 'Профиль'"""
    user_id = message.from_user.id
    
    try:
        user_data = await storage.get_user(user_id)
        
        if not user_data:
            await message.answer(
                "❌ Профиль не найден! Сначала привяжите профиль через /start",
                parse_mode="Markdown"
            )
            return
        
        faceit_id = user_data.get('faceit_id')
        nickname = user_data.get('nickname')
        
        # Получаем детали игрока с FACEIT
        player_details = None
        try:
            player_details = await faceit_client.get_player_details(faceit_id)
        except Exception as e:
            logger.error(f"Error getting player details for {faceit_id}: {e}")
        
        # Извлекаем данные игрока
        if player_details:
            games = player_details.get('games', {})
            cs2_data = games.get('cs2', {})
            elo = cs2_data.get('faceit_elo', 0)
            level = cs2_data.get('skill_level', 0)
            region = player_details.get('country', 'Unknown')
        else:
            elo = 0
            level = 0
            region = 'Unknown'
        
        # Получаем настройки пользователя
        settings = await storage.get_user_settings(user_id) or {}
        notifications = "Включены ✅" if settings.get('notifications', True) else "Выключены ❌"
        
        # Форматируем даты
        created_at = user_data.get('created_at', 'Неизвестно')
        if created_at and created_at != 'Неизвестно':
            try:
                from datetime import datetime
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = created_dt.strftime('%d.%m.%Y %H:%M')
                else:
                    created_at = str(created_at)[:19]
            except:
                created_at = str(created_at)
        
        last_activity = user_data.get('last_activity', 'Неизвестно')
        if last_activity and last_activity != 'Неизвестно':
            try:
                from datetime import datetime
                if isinstance(last_activity, str):
                    activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    last_activity = activity_dt.strftime('%d.%m.%Y %H:%M')
                else:
                    last_activity = str(last_activity)[:19]
            except:
                last_activity = str(last_activity)
        
        # Формируем сообщение профиля
        profile_text = f"""👤 **Ваш профиль**

🎮 **Привязанный аккаунт:**
• Никнейм: {nickname}
• Профиль FACEIT: [Открыть профиль](https://www.faceit.com/en/players/{nickname})

📊 **Статистика FACEIT:**
• ELO: {elo} (Уровень {level})
• Регион: {region}

⚙️ **Настройки бота:**
• Уведомления о последних матчах: {notifications}"""
        
        await message.answer(
            profile_text,
            parse_mode="Markdown",
            reply_markup=get_profile_reply_keyboard(),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error showing profile for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке профиля",
            reply_markup=get_profile_reply_keyboard()
        )

@router.message(F.text == "🔄 Сменить профиль")
async def handle_change_profile_button(message: Message, state: FSMContext):
    """Обработчик кнопки 'Сменить профиль'"""
    await message.answer(
        "🔄 **Смена профиля**\n\n"
        "Введите новый никнейм FACEIT для привязки к вашему аккаунту:\n\n"
        "💡 *Убедитесь, что никнейм написан правильно*",
        parse_mode="Markdown"
    )
    await state.set_state(ProfileStates.waiting_for_new_nickname)

@router.message(F.text == "🔔 Уведомления")
async def handle_notifications_button(message: Message):
    """Обработчик кнопки 'Уведомления'"""
    user_id = message.from_user.id
    
    try:
        # Получаем текущие настройки
        settings = await storage.get_user_settings(user_id) or {}
        current_status = settings.get('notifications', True)
        
        # Переключаем статус
        new_status = not current_status
        settings['notifications'] = new_status
        
        # Сохраняем новые настройки
        await storage.update_user_settings(user_id, settings)
        
        # Формируем сообщение
        status_text = "включены ✅" if new_status else "выключены ❌"
        message_text = f"""🔔 **Уведомления о последних матчах**

Статус: **{status_text}**

{"Вы будете получать уведомления о завершенных матчах." if new_status else "Вы не будете получать уведомления о матчах."}"""
        
        await message.answer(
            message_text,
            parse_mode="Markdown",
            reply_markup=get_profile_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error toggling notifications for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при изменении настроек",
            reply_markup=get_profile_reply_keyboard()
        )

@router.message(F.text == "⭐ Подписка")
async def handle_subscription_button(message: Message):
    """Обработчик кнопки 'Подписка'"""
    await message.answer(
        "🚧 **Раздел в разработке**\n\n"
        "Функционал подписок будет доступен в ближайшее время.\n\n"
        "Следите за обновлениями!",
        parse_mode="Markdown",
        reply_markup=get_profile_reply_keyboard()
    )

@router.message(F.text == "❓ Помощь")
async def handle_help_button(message: Message):
    """Обработчик кнопки 'Помощь'"""
    await message.answer(
        "❓ **Помощь по боту**\n\n"
        "🎮 **FACEIT CS2 Статистика Бот** - ваш персональный помощник для анализа статистики в CS2.\n\n"
        "Выберите интересующий раздел:",
        parse_mode="Markdown",
        reply_markup=get_help_reply_keyboard()
    )

@router.message(F.text == "🔙 Назад")
async def handle_back_button(message: Message):
    """Обработчик кнопки 'Назад'"""
    user_id = message.from_user.id
    
    if await storage.get_user_faceit_id(user_id):
        user_data = await storage.get_user(user_id)
        await message.answer(
            f"🎮 Главное меню\n\n"
            f"Игрок: {user_data.get('nickname', 'Неизвестно')}\n\n"
            f"Используйте кнопки внизу для навигации:",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await message.answer(
            "❓ Сначала привяжите свой FACEIT профиль.\n"
            "Используйте команду /start"
        )

# =================== НЕДОСТАЮЩИЕ REPLY-ОБРАБОТЧИКИ ===================

# Обработчики для статистики
@router.message(F.text == "📊 Общая статистика")
async def handle_overall_stats_reply(message: Message):
    """Reply-обработчик общей статистики"""
    user_id = message.from_user.id
    
    try:
        # Получаем FACEIT ID пользователя
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_stats_reply_keyboard()
            )
            return
        
        # Отправляем сообщение о загрузке
        loading_msg = await message.answer("📊 Загружаем статистику...")
        
        # Получаем данные игрока и статистику
        player_details = await faceit_client.get_player_details(faceit_id)
        stats_data = await faceit_client.get_player_stats(faceit_id)
        
        if not stats_data or not player_details:
            await loading_msg.edit_text(
                "❌ Не удалось загрузить статистику.\n"
                "Проверьте подключение или попробуйте позже."
            )
            return
        
        # Форматируем статистику  
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        
        if not formatted_stats:
            await loading_msg.edit_text("❌ Ошибка обработки статистики.")
            return
        
        # Получаем данные пользователя
        user_data = await storage.get_user(user_id)
        nickname = user_data.get('nickname', 'Unknown') if user_data else 'Unknown'
        
        # Правильные пороги уровней FACEIT
        level_thresholds = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000]
        
        # Формируем статистику
        current_elo = formatted_stats.get('elo', 0)
        current_level = formatted_stats.get('level', 0)
        
        # Правильный расчет ELO до следующего уровня
        if current_level >= 10:
            elo_to_next_level = 0  # Максимальный уровень достигнут
        else:
            next_level_threshold = level_thresholds[current_level]  # current_level уже является индексом для следующего уровня
            elo_to_next_level = max(0, next_level_threshold - current_elo)
        
        stats_message = f"""📊 **Общая статистика игрока**

👤 **Игрок:** {nickname}
🎮 **Уровень:** {current_level} | **ELO:** {current_elo}
⬆️ **До след. уровня:** {elo_to_next_level if elo_to_next_level > 0 else 'Максимум'}
🌍 **Регион:** {formatted_stats.get('region', 'N/A')}

📈 **Игровые результаты:**
• **Карт сыграно:** {formatted_stats.get('matches', 0)}
• **Побед:** {formatted_stats.get('wins', 0)} ({formatted_stats.get('winrate', 0):.1f}%)
• **Лучшая серия:** {formatted_stats.get('longest_win_streak', 0)} побед

⚔️ **Средние показатели за матч:**
• **Убийства:** {formatted_stats.get('avg_kills_per_match', 0):.1f}
• **Смерти:** {formatted_stats.get('avg_deaths_per_match', 0):.1f}
• **Ассисты:** {formatted_stats.get('avg_assists_per_match', 0):.1f}
• **% HS:** {formatted_stats.get('avg_headshot_percentage', 0):.1f}%

💥 **Урон и эффективность:**
• **ADR:** {formatted_stats.get('adr', 0):.1f}
• **Ослеплений за игру:** {formatted_stats.get('avg_flash_assists_per_match', 0):.1f}
• **Урон гранатами за игру:** {formatted_stats.get('avg_grenade_damage_per_match', 0):.1f}
• **Урон молотовых за игру:** {formatted_stats.get('avg_molotov_damage_per_match', 0):.1f}

🔥 **Серии убийств:**
• **Эйсов (5к):** {formatted_stats.get('total_aces', 0)}
• **4к убийств:** {formatted_stats.get('total_quadro_kills', 0)}
• **3к убийств:** {formatted_stats.get('total_triple_kills', 0)}
• **Мульти-килл за раунд (3+):** {formatted_stats.get('multi_kills_per_round', 0):.3f}

🏆 **Клатчи:**
• **1v1:** {formatted_stats.get('clutch_1v1_total', 0)} ({formatted_stats.get('clutch_1v1_percentage', 0):.0f}% побед)
• **1v2:** {formatted_stats.get('clutch_1v2_total', 0)} ({formatted_stats.get('clutch_1v2_percentage', 0):.0f}% побед)

🎯 **Первые действия за матч:**
• **Первые убийства:** {formatted_stats.get('first_kills', 0)}
• **Первые смерти:** {formatted_stats.get('first_deaths', 0)}
• **Попыток энтри:** {formatted_stats.get('total_entry_attempts', 0)}
• **% успешных энтри:** {formatted_stats.get('entry_success_percentage', 0):.1f}%

_Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}_"""
        
        # Отправляем статистику
        await loading_msg.edit_text(
            stats_message,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_overall_stats_reply for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке статистики.\n"
            "Пожалуйста, попробуйте позже."
        )

@router.message(F.text == "🗺️ По картам") 
async def handle_maps_stats_reply(message: Message):
    """Reply-обработчик статистики по картам"""
    user_id = message.from_user.id
    
    try:
        # Получаем FACEIT ID пользователя
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_stats_reply_keyboard()
            )
            return
        
        # Отправляем сообщение о загрузке
        loading_msg = await message.answer("🗺️ Загружаем статистику по картам...")
        
        # Получаем данные игрока и статистику
        player_details = await faceit_client.get_player_details(faceit_id)
        stats_data = await faceit_client.get_player_stats(faceit_id)
        
        if not stats_data or not player_details:
            await loading_msg.edit_text("❌ Статистика по картам недоступна")
            return
        
        # Форматируем статистику
        formatted_stats = faceit_client.format_player_stats(player_details, stats_data)
        maps_stats = formatted_stats.get('maps', {})
        
        if not maps_stats:
            await loading_msg.edit_text(
                "❌ Данные по картам отсутствуют.\n"
                "Возможно, игрок не играл достаточно матчей."
            )
            return
        
        # Сортируем карты по количеству матчей
        sorted_maps = sorted(
            maps_stats.items(), 
            key=lambda x: x[1].get('matches', 0), 
            reverse=True
        )
        
        # Определяем список эмоджи для карт
        map_emojis = {
            'mirage': '🌋',
            'inferno': '🏭', 
            'dust2': '🌪️',
            'nuke': '🌌',
            'vertigo': '🏔️',
            'ancient': '🌿',
            'anubis': '🏺',
            'train': '🚂',
            'overpass': '🌉'
        }
        
        # Формируем сообщение
        message_text = "🗺️ **Статистика по картам**\n\n"
        
        # Используем карты из API (динамический список)
        if maps_stats:
            # Сортируем карты по количеству матчей (убывание)
            sorted_maps = sorted(
                maps_stats.items(), 
                key=lambda x: x[1].get('matches', 0), 
                reverse=True
            )
            
            for i, (map_name, map_data) in enumerate(sorted_maps, 1):
                # Определяем эмоджи для карты
                map_key = map_name.lower().replace(' ', '').replace('de_', '')
                map_emoji = map_emojis.get(map_key, '🗺️')
                
                message_text += f"**{map_emoji} {i}. {map_name}**\n"
                
                matches = map_data.get('matches', 0)
                if matches > 0:
                    # Есть данные - показываем статистику
                    wins = map_data.get('wins', 0)
                    winrate = map_data.get('winrate', 0)
                    kd_ratio = map_data.get('kd_ratio', 0)
                    adr = map_data.get('adr', 0)
                    
                    message_text += f"📊 Матчей: **{matches}** (🏆{wins})\n"
                    message_text += f"📈 Winrate: **{winrate:.1f}%**\n"
                    message_text += f"⚔️ K/D: **{kd_ratio:.3f}**\n"
                    message_text += f"💥 ADR: **{adr:.1f}**\n\n"
                else:
                    # Нет данных - показываем сообщение
                    message_text += f"📊 Нет данных по карте\n\n"
        else:
            message_text += "❌ Данные по картам недоступны\n"
        
        await loading_msg.edit_text(
            message_text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_maps_stats_reply for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке статистики по картам.\n"
            "Пожалуйста, попробуйте позже."
        )

@router.message(F.text == "⏰ За сессию")
async def handle_session_stats_reply(message: Message):
    """Reply-обработчик статистики за сессию"""
    user_id = message.from_user.id
    
    try:
        # Получаем FACEIT ID пользователя
        faceit_id = await storage.get_user_faceit_id(user_id)
        
        if not faceit_id:
            await message.answer(
                "❌ Профиль FACEIT не привязан!\n"
                "Используйте /start для привязки профиля.",
                reply_markup=get_stats_reply_keyboard()
            )
            return
        
        # Отправляем сообщение о загрузке
        loading_msg = await message.answer("⏰ Загружаем статистику сессии...")
        
        # Получаем последние 100 матчей для анализа сессий
        history_data = await faceit_client.get_player_history(faceit_id, limit=100)
        
        if not history_data or 'items' not in history_data:
            await loading_msg.edit_text("❌ Нет данных о последних матчах")
            return
        
        matches = history_data['items']
        
        # Группируем матчи в сессии (промежуток более 10 часов = новая сессия)
        sessions = []
        current_session = []
        
        for match in matches:
            finished_at = match.get('finished_at', 0)
            if not finished_at:
                continue
                
            # Нормализуем время
            if finished_at > 10**12:
                match_time = datetime.fromtimestamp(finished_at / 1000)
            else:
                match_time = datetime.fromtimestamp(finished_at)
            
            match['parsed_time'] = match_time
            
            # Если текущая сессия пуста, начинаем новую
            if not current_session:
                current_session = [match]
            else:
                # Проверяем разрыв между матчами
                last_match_time = current_session[-1]['parsed_time']
                time_diff = (last_match_time - match_time).total_seconds() / 3600  # в часах
                
                if time_diff <= 10:  # Матчи в рамках 10 часов - одна сессия
                    current_session.append(match)
                else:  # Больше 10 часов - новая сессия
                    sessions.append(current_session)
                    current_session = [match]
        
        # Добавляем последнюю сессию
        if current_session:
            sessions.append(current_session)
        
        if not sessions:
            await loading_msg.edit_text(
                "⏰ **Статистика сессии**\n\n"
                "Сессии не найдены.",
                parse_mode="Markdown"
            )
            return
        
        # Определяем цветовые индикаторы
        def get_color_indicator(value, good_threshold, is_percentage=False):
            if is_percentage:
                return "🟢" if value >= good_threshold else "🔴"
            else:
                return "🟢" if value >= good_threshold else "🔴"
        
        # Формируем сообщение со всеми сессиями
        message_text = "⏰ **Статистика по сессиям**\n\n"
        
        # Обрабатываем все сессии
        total_sessions = len(sessions)
        for i, session in enumerate(sessions, 1):
            # Показываем прогресс обработки
            if total_sessions > 3:  # Показываем прогресс только если сессий много
                try:
                    await loading_msg.edit_text(f"⏰ Анализируем сессии... {i}/{total_sessions}")
                except:
                    pass  # Игнорируем ошибки обновления сообщения
            
            # Анализируем статистику каждой сессии с детальными данными матчей
            session_stats = await analyze_session_stats_from_matches(session, faceit_id)
            
            # Рассчитываем длительность сессии
            session_start_time = session[-1]['parsed_time']
            session_end_time = session[0]['parsed_time']
            duration_hours = (session_end_time - session_start_time).total_seconds() / 3600
            
            # Определяем цветовые индикаторы для сессии
            adr_color = get_color_indicator(session_stats['avg_adr'], 75.0)  # ADR >= 75 = зеленый
            kd_color = get_color_indicator(session_stats['kd_ratio'], 1.0)
            wr_color = get_color_indicator(session_stats['winrate'], 50.0, True)
            
            # Форматируем дату сессии
            session_date = session_start_time.strftime('%d.%m.%Y')
            
            # Добавляем информацию о сессии в новом формате
            message_text += f"📅 {session_date} - {session_stats['total_matches']} матчей • Длительность: {duration_hours:.1f}ч\n"
            message_text += f"{adr_color} ADR: {session_stats['avg_adr']:.1f} {kd_color} K/D: {session_stats['kd_ratio']:.2f} | {wr_color} WR: {session_stats['winrate']:.1f}%\n"
            message_text += f"📊 Подробно: {session_stats['avg_kills']:.1f}/{session_stats['avg_deaths']:.1f}/{session_stats['avg_assists']:.1f}"
            
            # Добавляем информацию о качестве данных если есть проблемы
            if session_stats.get('failed_matches', 0) > 0:
                successful = session_stats.get('successful_matches', 0)
                total = session_stats['total_matches']
                message_text += f" ⚠️ ({successful}/{total})"
            
            message_text += "\n\n"
        
        # Добавляем общую информацию о качестве данных
        total_sessions_processed = len(sessions)
        message_text += f"_Обработано {total_sessions_processed} сессий_"
        
        await loading_msg.edit_text(
            message_text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_session_stats_reply for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке статистики сессии.\n"
            "Пожалуйста, попробуйте позже."
        )

# Обработчики для истории - удалены, будут в новом обработчике

# Обработчики для анализа формы
@router.message(F.text == "📊 Анализ 10 матчей")
async def handle_form_10_reply(message: Message):
    """Reply-обработчик анализа формы 10 матчей"""
    from bot.handlers.form_analysis_handler import analyze_form_fixed
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "form_10")
    await analyze_form_fixed(fake_callback, state)

@router.message(F.text == "📈 Анализ 20 матчей")
async def handle_form_20_reply(message: Message):
    """Reply-обработчик анализа формы 20 матчей"""
    from bot.handlers.form_analysis_handler import analyze_form_fixed
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "form_20")
    await analyze_form_fixed(fake_callback, state)

@router.message(F.text == "📋 Анализ 50 матчей")
async def handle_form_50_reply(message: Message):
    """Reply-обработчик анализа формы 50 матчей"""
    from bot.handlers.form_analysis_handler import analyze_form_fixed
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "form_50")
    await analyze_form_fixed(fake_callback, state)

# Обработчики для сравнения игроков

def get_comparison_keyboard_with_count(user_data):
    """Получить reply-клавиатуру сравнения с учетом количества игроков"""
    comparison_players = user_data.get('comparison_players', []) if isinstance(user_data, dict) else []
    players_count = len(comparison_players)
    show_comparison = players_count == 2
    return get_comparison_reply_keyboard(show_comparison, players_count)
@router.message(F.text == "➕ Добавить себя")
async def handle_add_self_reply(message: Message, state: FSMContext):
    """Reply-обработчик добавления себя в сравнение"""
    from bot.handlers.comparison_handler import format_comparison_menu_text
    from storage import storage
    from faceit_client import faceit_client
    
    try:
        user_id = str(message.from_user.id)
        state_data = await state.get_data()
        
        # Получаем никнейм пользователя из storage
        user_data = await storage.get_user(int(user_id))
        user_nickname = user_data.get('nickname') if user_data else None
        
        if not user_nickname:
            await message.answer("❌ Сначала привяжите свой FACEIT аккаунт в настройках!")
            return
        
        comparison_players = state_data.get('comparison_players', []) if isinstance(state_data, dict) else []
        
        # Проверяем, есть ли уже этот игрок в списке
        if any(player['nickname'] == user_nickname for player in comparison_players):
            await message.answer("⚠️ Вы уже добавлены в список сравнения!")
            return
        
        # Проверяем лимит игроков
        if len(comparison_players) >= 2:
            await message.answer("⚠️ Можно сравнивать только 2 игроков одновременно!")
            return
        
        # Получаем полный профиль игрока
        loading_msg = await message.answer("⏳ Загружаю ваш профиль...")
        
        player_profile = await faceit_client.get_player_full_profile(user_nickname)
        if not player_profile:
            await loading_msg.edit_text("❌ Не удалось загрузить ваш профиль FACEIT!")
            return
        
        # Добавляем игрока в список
        # Извлекаем данные из правильной структуры
        player_stats = player_profile.get('stats', {})
        
        # Debug логирование (принудительный вывод)
        print(f"[REPLY DEBUG] Adding self to comparison: {user_nickname}")
        print(f"[REPLY DEBUG] Profile keys: {list(player_profile.keys())}")
        print(f"[REPLY DEBUG] Stats: nickname={player_stats.get('nickname')}, level={player_stats.get('level')}, elo={player_stats.get('elo')}")
        print(f"[REPLY DEBUG] Full stats object: {player_stats}")
        
        comparison_players.append({
            'nickname': player_stats.get('nickname', user_nickname),
            'skill_level': player_stats.get('level', 0),
            'faceit_elo': player_stats.get('elo', 0),
            'profile_data': player_stats  # Сохраняем только статистику, как в comparison_handler
        })
        
        await state.update_data(comparison_players=comparison_players)
        
        # Показываем обновленное меню с reply-клавиатурой
        updated_data = await state.get_data()
        text = await format_comparison_menu_text(updated_data)
        
        # Показываем чистое меню без лишних сообщений
        await loading_msg.edit_text(
            text=text,
            parse_mode="HTML"
        )
        
        # Отправляем обновленную reply-клавиатуру с подтверждением
        await message.answer(
            "✅ Вы добавлены в список сравнения!",
            reply_markup=get_comparison_keyboard_with_count(updated_data)
        )
        
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении в сравнение")
        print(f"Error adding self to comparison: {e}")

@router.message(F.text == "👤 Добавить игрока")
async def handle_add_player_reply(message: Message, state: FSMContext):
    """Reply-обработчик добавления игрока в сравнение"""
    from bot.handlers.comparison_handler import ComparisonStates
    
    try:
        user_data = await state.get_data()
        comparison_players = user_data.get('comparison_players', []) if isinstance(user_data, dict) else []
        
        # Проверяем лимит игроков
        if len(comparison_players) >= 2:
            await message.answer("⚠️ Можно сравнивать только 2 игроков одновременно!")
            return
        
        await state.set_state(ComparisonStates.waiting_for_nickname)
        
        await message.answer(
            "🔍 <b>Добавление игрока в сравнение</b>\n\n"
            "Введите никнейм игрока FACEIT, которого хотите добавить для сравнения:",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer("Произошла ошибка")
        print(f"Error in add player handler: {e}")

@router.message(F.text == "🗑️ Очистить")
async def handle_clear_comparison_reply(message: Message, state: FSMContext):
    """Reply-обработчик очистки данных сравнения"""
    from bot.handlers.comparison_handler import format_comparison_menu_text
    
    try:
        await state.update_data(comparison_players=[])
        
        updated_data = await state.get_data()
        text = await format_comparison_menu_text(updated_data)
        
        await message.answer(
            text=text,
            reply_markup=get_comparison_keyboard_with_count(updated_data),
            parse_mode="HTML"
        )
        await message.answer("🗑️ Список игроков очищен!")
        
    except Exception as e:
        await message.answer("Произошла ошибка при очистке данных")
        print(f"Error clearing comparison: {e}")

@router.message(F.text == "📊 Сравнить!")
async def handle_compare_players_reply(message: Message, state: FSMContext):
    """Reply-обработчик сравнения игроков"""
    from bot.handlers.comparison_handler import get_player_comparison_stats, format_comparison_table
    
    try:
        user_data = await state.get_data()
        comparison_players = user_data.get('comparison_players', []) if isinstance(user_data, dict) else []
        
        if len(comparison_players) != 2:
            await message.answer("⚠️ Для сравнения нужно выбрать ровно 2 игроков!")
            return
        
        await message.answer("⏳ Анализирую статистику игроков...")
        
        # Используем улучшенное сравнение
        from bot.handlers.enhanced_comparison import format_enhanced_comparison
        
        # Получаем полную статистику игроков для сравнения
        # profile_data теперь содержит полную статистику из поля 'stats'
        player1_stats = comparison_players[0]['profile_data']
        player2_stats = comparison_players[1]['profile_data']
        
        # Форматируем улучшенное сравнение с полной статистикой
        comparison_text = format_enhanced_comparison(player1_stats, player2_stats)
        
        await message.answer(
            text=comparison_text,
            parse_mode="HTML"
        )
        await message.answer(
            "🔄 Хотите сделать новое сравнение?",
            reply_markup=get_comparison_keyboard_with_count(user_data)
        )
        
    except Exception as e:
        await message.answer("Произошла ошибка при сравнении игроков")
        print(f"Error comparing players: {e}")

async def analyze_session_stats_simple(session_matches, faceit_id: str):
    """Анализ статистики сессии на основе базовых данных истории"""
    total_matches = len(session_matches)
    wins = 0
    losses = 0
    match_results = []
    
    total_kills = 0
    total_deaths = 0  
    total_assists = 0
    total_adr = 0
    total_rating = 0
    matches_with_stats = 0
    
    for match in session_matches:
        # Определяем результат матча
        player_won = faceit_client._determine_player_result(match, faceit_id)
        
        if player_won is True:
            wins += 1
            match_results.append("🏆")
        elif player_won is False:
            losses += 1
            match_results.append("❌")
        else:
            match_results.append("❓")
        
        # Извлекаем базовую статистику из истории (если доступна)
        if 'stats' in match and match['stats']:
            stats = match['stats']
            # Суммируем статистику
            match_kills = int(stats.get('Kills', 0))
            match_deaths = int(stats.get('Deaths', 0))
            match_assists = int(stats.get('Assists', 0))
            match_adr = float(stats.get('ADR', 0))
            match_rating = float(stats.get('Player Rating', 0))
            
            total_kills += match_kills
            total_deaths += match_deaths
            total_assists += match_assists
            total_adr += match_adr
            total_rating += match_rating
            matches_with_stats += 1
    
    # Рассчитываем показатели
    winrate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    if matches_with_stats > 0:
        avg_kills = total_kills / matches_with_stats
        avg_deaths = total_deaths / matches_with_stats  
        avg_assists = total_assists / matches_with_stats
        avg_adr = total_adr / matches_with_stats
        avg_rating = total_rating / matches_with_stats
        kd_ratio = (total_kills / total_deaths) if total_deaths > 0 else 0
    else:
        # Если нет детальной статистики, используем приблизительные значения
        avg_kills = 16.0
        avg_deaths = 16.0
        avg_assists = 5.0
        avg_adr = 75.0
        avg_rating = 1.0
        kd_ratio = 1.0
    
    return {
        'total_matches': total_matches,
        'wins': wins,
        'losses': losses,
        'winrate': winrate,
        'kd_ratio': kd_ratio,
        'avg_kills': avg_kills,
        'avg_deaths': avg_deaths,
        'avg_assists': avg_assists,
        'avg_adr': avg_adr,
        'avg_rating': avg_rating,
        'match_results': match_results,
        'matches_with_stats': matches_with_stats
    }

async def analyze_session_stats_from_matches(session_matches, faceit_id: str):
    """Анализ статистики сессии на основе детальных данных матчей"""
    total_matches = len(session_matches)
    wins = 0
    losses = 0
    match_results = []
    
    # Агрегированная статистика
    total_kills = 0
    total_deaths = 0
    total_assists = 0
    total_rounds = 0
    total_damage = 0  # Для расчета ADR
    total_kast_rounds = 0
    total_first_kills = 0
    total_first_deaths = 0
    total_flash_assists = 0
    
    successful_matches = 0
    failed_matches = 0
    
    for match in session_matches:
        match_id = match.get('match_id')
        if not match_id:
            failed_matches += 1
            match_results.append("❓")
            continue
        
        # Определяем результат матча
        player_won = faceit_client._determine_player_result(match, faceit_id)
        
        if player_won is True:
            wins += 1
            match_results.append("🏆")
        elif player_won is False:
            losses += 1
            match_results.append("❌")
        else:
            match_results.append("❓")
        
        # Получаем детальную статистику игрока из матча
        try:
            player_match_stats = await faceit_client.get_player_stats_from_match(match_id, faceit_id)
            
            if player_match_stats:
                # Агрегируем статистику с проверками на корректность данных
                kills = player_match_stats.get('kills', 0)
                deaths = player_match_stats.get('deaths', 0)
                assists = player_match_stats.get('assists', 0)
                rounds = player_match_stats.get('rounds', 16)
                adr = player_match_stats.get('adr', 0.0)
                kast = player_match_stats.get('kast', 0.0)
                
                # Валидация данных
                if rounds <= 0 or rounds > 50:  # Нереалистичное количество раундов
                    rounds = 16  # Стандартное значение
                
                if adr < 0 or adr > 200:  # Нереалистичный ADR
                    adr = 0.0
                
                if kast < 0 or kast > 100:  # KAST должен быть процентом
                    kast = 0.0
                
                total_kills += kills
                total_deaths += deaths 
                total_assists += assists
                total_rounds += rounds
                
                # ADR рассчитываем из существующего ADR * количество раундов
                total_damage += (adr * rounds)
                
                # KAST рассчитываем приблизительно
                total_kast_rounds += (kast / 100.0 * rounds)
                
                # Дополнительные метрики
                total_first_kills += player_match_stats.get('first_kills', 0)
                total_first_deaths += player_match_stats.get('first_deaths', 0)
                total_flash_assists += player_match_stats.get('flash_assists', 0)
                
                successful_matches += 1
            else:
                failed_matches += 1
                logger.warning(f"No stats returned for match {match_id}")
                
        except asyncio.TimeoutError:
            failed_matches += 1
            logger.warning(f"Timeout getting stats for match {match_id}")
        except Exception as e:
            failed_matches += 1
            logger.error(f"Error processing match {match_id}: {e}")
    
    # Рассчитываем финальную статистику
    winrate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    if successful_matches > 0 and total_rounds > 0:
        # Рассчитываем средние показатели
        avg_kills = total_kills / successful_matches
        avg_deaths = total_deaths / successful_matches
        avg_assists = total_assists / successful_matches
        
        # K/D рассчитывается из общих kills/deaths
        kd_ratio = total_kills / max(total_deaths, 1)
        
        # ADR - средний урон за раунд по всем раундам
        avg_adr = total_damage / total_rounds if total_rounds > 0 else 0
        
        # KAST - процент раундов с участием
        avg_kast = (total_kast_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        # Убираем расчет рейтинга - он не нужен в новом формате
        
    elif successful_matches > 0:
        # Частичные данные - используем что есть, но с осторожностью
        avg_kills = total_kills / successful_matches if successful_matches > 0 else 16.0
        avg_deaths = total_deaths / successful_matches if successful_matches > 0 else 16.0
        avg_assists = total_assists / successful_matches if successful_matches > 0 else 5.0
        kd_ratio = total_kills / max(total_deaths, 1) if total_deaths > 0 else 1.0
        avg_adr = 75.0  # Fallback для ADR
        avg_kast = 70.0  # Fallback для KAST
    else:
        # Fallback значения если не удалось получить статистику
        avg_kills = 16.0
        avg_deaths = 16.0
        avg_assists = 5.0
        avg_adr = 75.0
        avg_kast = 70.0
        kd_ratio = 1.0
    
    return {
        'total_matches': total_matches,
        'wins': wins,
        'losses': losses,
        'winrate': winrate,
        'kd_ratio': kd_ratio,
        'avg_kills': avg_kills,
        'avg_deaths': avg_deaths,
        'avg_assists': avg_assists,
        'avg_adr': avg_adr,
        'avg_kast': avg_kast,
        'match_results': match_results,
        'successful_matches': successful_matches,
        'failed_matches': failed_matches,
        'matches_with_stats': successful_matches
    }

# Обработчик неизвестных сообщений (только когда нет активных FSM состояний)
# Reply-обработчик для кнопки "📖 Описание функций"
@router.message(F.text == "📖 Описание функций")
async def handle_functions_description_reply(message: Message):
    """Reply-обработчик для описания функций"""
    text = (
        "📖 **ОПИСАНИЕ ФУНКЦИЙ БОТА**\n\n"
        "Выберите функцию для подробной информации:\n\n"
        "**📊 Статистика игрока**\n"
        "└ Полная статистика: ELO, K/D, ADR, рейтинг\n"
        "└ По картам: детали для каждой карты\n"
        "└ За сессию: последние 12 часов игры\n\n"
        "**📝 История матчей**\n"
        "└ Просмотр 5/10/30 последних матчей\n"
        "└ Детальная статистика каждого матча\n"
        "└ Ссылки на матчи в FACEIT\n\n"
        "**⚔️ Сравнение игроков**\n"
        "└ Сравнение до 2 игроков\n"
        "└ 15+ параметров с индикаторами 📈📉\n"
        "└ Определение сильных/слабых сторон\n\n"
        "**📈 Анализ формы**\n"
        "└ Сравнение периодов (5 vs 20 матчей)\n"
        "└ Тренды показателей\n"
        "└ Индикаторы формы 🔥❄️\n\n"
        "**🎮 Последний матч**\n"
        "└ Детальная статистика матча\n"
        "└ Состав команд и их ELO\n"
        "└ Изменение рейтинга\n\n"
        "💡 **Совет:** Начните с привязки профиля через '👤 Профиль'"
    )
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_reply_keyboard()
    )

# Reply-обработчик для кнопки "💬 Связаться"
@router.message(F.text == "💬 Связаться")
async def handle_contact_reply(message: Message):
    """Reply-обработчик для связи с разработчиком"""
    contact_text = (
        "💬 **СВЯЗАТЬСЯ С РАЗРАБОТЧИКОМ**\n\n"
        "👨‍💻 **Разработчик:** @karriDD\n"
        "📱 **Telegram:** https://t.me/karriDD\n\n"
        "**📝 По каким вопросам обращаться:**\n"
        "• 🐛 Сообщения об ошибках\n"
        "• 💡 Предложения новых функций\n"
        "• ❓ Вопросы по использованию\n"
        "• 🤝 Сотрудничество и реклама\n"
        "• ⚡ Проблемы со скоростью работы\n\n"
        "**⏰ Время ответа:**\n"
        "• Обычно: 1-2 часа (9:00-22:00 МСК)\n"
        "• Критические баги: максимально быстро\n\n"
        "**📢 Что указать в сообщении:**\n"
        "• Ваш FACEIT никнейм\n"
        "• Описание проблемы/предложения\n"
        "• Скриншот ошибки (если есть)\n"
        f"• Ваш Telegram ID: `{message.from_user.id}`\n\n"
        "**🎁 Бонусы за репорты:**\n"
        "• Критический баг = месяц премиума\n"
        "• Полезная фича = 2 недели премиума\n"
        "• Мелкий баг = благодарность в боте"
    )
    
    await message.answer(
        contact_text,
        parse_mode="Markdown",
        reply_markup=get_help_reply_keyboard()
    )

@router.message(StateFilter(None))
async def unknown_message(message: Message, state: FSMContext):
    """Обработка неизвестных сообщений"""
    user_id = message.from_user.id
    
    # DEBUG: Проверяем состояние FSM
    current_state = await state.get_state()
    logger.warning(f"🔍 UNKNOWN MESSAGE от {user_id}: '{message.text}' (len={len(message.text or '')}) | FSM состояние: {current_state}")
    
    if await storage.get_user_faceit_id(user_id):
        await message.answer(
            "❓ Не понимаю эту команду.\n"
            "Используйте меню бота для навигации."
        )
    else:
        await message.answer(
            "❓ Сначала привяжите свой FACEIT профиль.\n"
            "Используйте команду /start"
        )