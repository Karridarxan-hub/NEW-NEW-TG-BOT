from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging

from keyboards import (get_main_menu_keyboard, get_main_reply_keyboard, get_stats_reply_keyboard,
                      get_history_reply_keyboard, get_form_reply_keyboard, get_comparison_reply_keyboard,
                      get_settings_reply_keyboard, get_help_reply_keyboard, get_profile_reply_keyboard)
from storage import storage
from faceit_client import faceit_client

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

# История матчей
@router.callback_query(F.data == "match_history")
async def show_match_history_menu(callback: CallbackQuery):
    """Показать меню истории матчей"""
    from keyboards import get_match_history_keyboard
    await callback.message.edit_text(
        "📝 **История матчей**\n\n"
        "Выберите количество матчей для просмотра:",
        parse_mode="Markdown",
        reply_markup=get_match_history_keyboard()
    )
    await callback.answer()

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
async def show_player_comparison_menu(callback: CallbackQuery):
    """Показать меню сравнения игроков"""
    from keyboards import get_player_comparison_keyboard
    await callback.message.edit_text(
        "⚔️ **Сравнение игроков**\n\n"
        "Добавьте игроков для сравнения:\n"
        "_Максимум 2 игрока_",
        parse_mode="Markdown",
        reply_markup=get_player_comparison_keyboard()
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
async def handle_comparison_button(message: Message):
    """Обработчик кнопки 'Сравнение'"""
    await message.answer(
        "⚔️ **Сравнение игроков**\n\n"
        "Добавьте игроков для сравнения:",
        parse_mode="Markdown",
        reply_markup=get_comparison_reply_keyboard()
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
    await message.answer(
        "👤 **Профиль**\n\n"
        "Управление профилем:",
        parse_mode="Markdown",
        reply_markup=get_profile_reply_keyboard()
    )

@router.message(F.text == "⚙️ Настройки")
async def handle_settings_button(message: Message):
    """Обработчик кнопки 'Настройки'"""
    await message.answer(
        "⚙️ **Настройки**\n\n"
        "Выберите настройку:",
        parse_mode="Markdown",
        reply_markup=get_settings_reply_keyboard()
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
        hltv_rating = formatted_stats.get('hltv_rating', 0.0)
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
⭐ **HLTV Rating 2.1:** {hltv_rating:.3f}
🌍 **Регион:** {formatted_stats.get('region', 'N/A')}

📈 **Игровые результаты:**
• **Карт сыграно:** {formatted_stats.get('matches', 0)}
• **Побед:** {formatted_stats.get('wins', 0)} ({formatted_stats.get('winrate', 0):.1f}%)
• **Лучшая серия:** {formatted_stats.get('longest_win_streak', 0)} побед

⚔️ **Средние показатели за матч:**
• **Убийства:** {formatted_stats.get('avg_kills_per_match', 0):.1f}
• **Смерти:** {formatted_stats.get('avg_deaths_per_match', 0):.1f}
• **Ассисты:** {formatted_stats.get('avg_assists_per_match', 0):.1f}
• **Средний % HS:** {formatted_stats.get('avg_headshot_percentage', 0):.1f}%

💥 **Урон и эффективность:**
• **ADR:** {formatted_stats.get('adr', 0):.1f}
• **KAST:** {formatted_stats.get('kast', 0):.1f}%
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
        
        # Берем последнюю сессию (самую свежую)
        latest_session = sessions[0]
        
        # Анализируем статистику последней сессии
        session_stats = await analyze_session_stats_simple(latest_session, faceit_id)
        
        # Рассчитываем длительность сессии
        session_start_time = latest_session[-1]['parsed_time']
        session_end_time = latest_session[0]['parsed_time']
        duration_hours = (session_end_time - session_start_time).total_seconds() / 3600
        
        # Определяем цветовые индикаторы
        def get_color_indicator(value, good_threshold, is_percentage=False):
            if is_percentage:
                return "🟢" if value >= good_threshold else "🔴"
            else:
                return "🟢" if value >= good_threshold else "🔴"
        
        hltv_color = get_color_indicator(session_stats['avg_hltv'], 1.0)
        kd_color = get_color_indicator(session_stats['kd_ratio'], 1.0)
        wr_color = get_color_indicator(session_stats['winrate'], 50.0, True)
        
        # Формируем сообщение в новом формате
        session_date = session_start_time.strftime('%d.%m.%Y')
        
        message_text = f"""⏰ **Статистика последней сессии**

📅 {session_date} - {session_stats['total_matches']} матчей • Длительность: {duration_hours:.1f}ч
{hltv_color} HLTV: {session_stats['avg_hltv']:.2f} | {kd_color} K/D: {session_stats['kd_ratio']:.1f} | {wr_color} WR: {session_stats['winrate']:.1f}%
📊 Подробно: {session_stats['avg_kills']:.1f}/{session_stats['avg_deaths']:.1f}/{session_stats['avg_assists']:.1f} | ADR: {session_stats['avg_adr']:.1f}

📋 **Матчи сессии:**"""
        
        # Показываем детали матчей сессии
        for i, match in enumerate(latest_session[:5], 1):
            result_emoji = session_stats['match_results'][i-1] if i-1 < len(session_stats['match_results']) else "❓"
            map_name = match.get('map', 'Unknown')
            
            # Получаем счет
            score_info = ""
            if 'results' in match and 'score' in match['results']:
                score = match['results']['score']
                score_info = f" ({score.get('faction1', 0)}:{score.get('faction2', 0)})"
            
            time_str = match['parsed_time'].strftime('%H:%M')
            message_text += f"\n{i}. {result_emoji} {map_name}{score_info} - {time_str}"
        
        if len(latest_session) > 5:
            message_text += f"\n\n_Показано 5 из {len(latest_session)} матчей сессии_"
        
        message_text += f"\n\n_Всего найдено сессий: {len(sessions)}_"
        
        # Добавляем информацию о качестве данных
        if session_stats['matches_with_stats'] < session_stats['total_matches']:
            missing_stats = session_stats['total_matches'] - session_stats['matches_with_stats']
            message_text += f"\n\n_Детальная статистика доступна для {session_stats['matches_with_stats']} из {session_stats['total_matches']} матчей_"
        
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

# Обработчики для истории
@router.message(F.text == "5️⃣ Последние 5")
async def handle_history_5_reply(message: Message):
    """Reply-обработчик истории 5 матчей"""
    from bot.handlers.match_history_handler import show_match_history
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "history_5")
    await show_match_history(fake_callback, state)

@router.message(F.text == "🔟 Последние 10")
async def handle_history_10_reply(message: Message):
    """Reply-обработчик истории 10 матчей"""
    from bot.handlers.match_history_handler import show_match_history
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "history_10")
    await show_match_history(fake_callback, state)

@router.message(F.text == "3️⃣0️⃣ Последние 30")
async def handle_history_30_reply(message: Message):
    """Reply-обработчик истории 30 матчей"""
    from bot.handlers.match_history_handler import show_match_history
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "history_30")
    await show_match_history(fake_callback, state)

# Обработчики для анализа формы
@router.message(F.text == "🔟 vs 10 предыдущих")
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

@router.message(F.text == "2️⃣0️⃣ vs 20 предыдущих")
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

@router.message(F.text == "5️⃣0️⃣ vs 50 предыдущих")
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
@router.message(F.text == "➕ Добавить себя")
async def handle_add_self_reply(message: Message):
    """Reply-обработчик добавления себя в сравнение"""
    from bot.handlers.comparison_handler import handle_add_self_to_comparison
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "comparison_add_self")
    await handle_add_self_to_comparison(fake_callback, state)

@router.message(F.text == "👤 Добавить игрока")
async def handle_add_player_reply(message: Message):
    """Reply-обработчик добавления игрока в сравнение"""
    from bot.handlers.comparison_handler import handle_add_player_to_comparison
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # Создаем фейковое состояние FSM
    storage_memory = MemoryStorage()
    state = FSMContext(storage=storage_memory, key=message.bot.id)
    
    # Используем общий FakeCallback класс с данными
    fake_callback = FakeCallback(message, "comparison_add_player")
    await handle_add_player_to_comparison(fake_callback, state)

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
    total_hltv = 0
    matches_with_stats = 0
    
    for match in session_matches:
        # Определяем результат матча
        player_won = faceit_client._determine_player_result(match, faceit_id)
        
        if player_won is True:
            wins += 1
            match_results.append("🏆")
        elif player_won is False:
            losses += 1
            match_results.append("💔")
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
            match_hltv = float(stats.get('HLTV Rating', 0))
            
            total_kills += match_kills
            total_deaths += match_deaths
            total_assists += match_assists
            total_adr += match_adr
            total_hltv += match_hltv
            matches_with_stats += 1
    
    # Рассчитываем показатели
    winrate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    if matches_with_stats > 0:
        avg_kills = total_kills / matches_with_stats
        avg_deaths = total_deaths / matches_with_stats  
        avg_assists = total_assists / matches_with_stats
        avg_adr = total_adr / matches_with_stats
        avg_hltv = total_hltv / matches_with_stats
        kd_ratio = (total_kills / total_deaths) if total_deaths > 0 else 0
    else:
        # Если нет детальной статистики, используем приблизительные значения
        avg_kills = 16.0
        avg_deaths = 16.0
        avg_assists = 5.0
        avg_adr = 75.0
        avg_hltv = 1.0
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
        'avg_hltv': avg_hltv,
        'match_results': match_results,
        'matches_with_stats': matches_with_stats
    }

# Обработчик неизвестных сообщений  
@router.message()
async def unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    user_id = message.from_user.id
    
    if await storage.get_user_faceit_id(user_id):
        await message.answer(
            "❓ Не понимаю эту команду.\n"
            "Используйте кнопки внизу для навигации:",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await message.answer(
            "❓ Сначала привяжите свой FACEIT профиль.\n"
            "Используйте команду /start"
        )