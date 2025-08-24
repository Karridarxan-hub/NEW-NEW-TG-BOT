from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Статистика игрока", callback_data="player_stats")
    builder.button(text="📝 История матчей", callback_data="match_history")
    builder.button(text="📈 Анализ формы", callback_data="form_analysis")
    builder.button(text="🎮 Последний матч", callback_data="last_match")
    builder.button(text="⚔️ Сравнение игроков", callback_data="player_comparison")
    builder.button(text="🔍 Анализ текущего матча", callback_data="current_match_analysis")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="⚙️ Настройки", callback_data="settings")
    builder.button(text="❓ Помощь", callback_data="help")
    
    builder.adjust(3, 3, 3)
    return builder.as_markup()


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для статистики игрока"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_overall")],
        [InlineKeyboardButton(text="🗺️ Статистика по картам", callback_data="stats_maps")],
        [InlineKeyboardButton(text="⏰ Статистика за сессию", callback_data="stats_session")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_player_stats_keyboard() -> InlineKeyboardMarkup:
    """Меню статистики игрока"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Общая статистика", callback_data="stats_overall")
    builder.button(text="🗺️ Статистика по картам", callback_data="stats_maps")
    builder.button(text="⏰ Статистика за сессию", callback_data="stats_session")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 1, 1, 2)
    return builder.as_markup()


def get_match_history_keyboard() -> InlineKeyboardMarkup:
    """Меню истории матчей - новая упрощенная версия"""
    builder = InlineKeyboardBuilder()
    
    # 4 основные кнопки как просил пользователь
    builder.button(text="5 матчей", callback_data="history_5")
    builder.button(text="10 матчей", callback_data="history_10")
    builder.button(text="30 матчей", callback_data="history_30")
    builder.button(text="✏️ Ввести вручную", callback_data="history_custom")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    
    builder.adjust(2, 2, 1)  # 2 кнопки в первых двух рядах, 1 кнопка назад
    return builder.as_markup()


def get_form_analysis_keyboard() -> InlineKeyboardMarkup:
    """Меню анализа формы"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Анализ 10 матчей", callback_data="form_10")
    builder.button(text="📈 Анализ 20 матчей", callback_data="form_20")
    builder.button(text="📋 Анализ 50 матчей", callback_data="form_50")
    builder.button(text="✏️ Ввести вручную", callback_data="form_custom")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 1, 1, 1, 2)
    return builder.as_markup()


def get_player_comparison_keyboard(show_comparison: bool = False) -> InlineKeyboardMarkup:
    """Меню сравнения игроков"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ Добавить себя в сравнение", callback_data="comparison_add_self")
    builder.button(text="👤 Добавить нового игрока", callback_data="comparison_add_player")
    
    # Показываем кнопку сравнения только когда выбрано 2 игрока
    if show_comparison:
        builder.button(text="📊 Получить сравнение", callback_data="comparison_get")
    
    builder.button(text="🗑️ Очистить данные", callback_data="comparison_clear")
    
    if show_comparison:
        builder.adjust(1, 1, 1, 1)
    else:
        builder.adjust(1, 1, 1)
    
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔔 Уведомления о матчах", callback_data="settings_notifications")
    builder.button(text="⭐ Тип подписки", callback_data="settings_subscription")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 1, 2)
    return builder.as_markup()


def get_notifications_toggle_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    """Переключатель уведомлений (вкл/выкл)"""
    builder = InlineKeyboardBuilder()
    
    status_text = "✅ Включены" if enabled else "❌ Выключены"
    action = "disable" if enabled else "enable"
    
    builder.button(text=f"🔔 {status_text}", callback_data=f"toggle_notifications_{action}")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 2)
    return builder.as_markup()


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Меню типа подписки"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📦 Стандарт (бесплатно)", callback_data="subscription_standard")
    builder.button(text="⭐ Премиум (звезды)", callback_data="subscription_premium")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 1, 2)
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    return builder.as_markup()


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Универсальная кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=callback_data)
    return builder.as_markup()


def get_maps_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора карт CS2"""
    builder = InlineKeyboardBuilder()
    
    maps = [
        ("🌋 Mirage", "map_mirage"),
        ("🏭 Inferno", "map_inferno"),
        ("🌪️ Dust2", "map_dust2"),
        ("🚂 Train", "map_train"),
        ("🏰 Cache", "map_cache"),
        ("🌊 Overpass", "map_overpass"),
        ("🌌 Nuke", "map_nuke"),
        ("🏔️ Vertigo", "map_vertigo"),
        ("🌿 Ancient", "map_ancient")
    ]
    
    for map_name, callback in maps:
        builder.button(text=map_name, callback_data=callback)
    
    builder.button(text="🔙 Назад", callback_data="stats_maps")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(3, 3, 3, 2)
    return builder.as_markup()


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Меню профиля"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Сменить профиль", callback_data="change_profile")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 2)
    return builder.as_markup()


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Меню помощи"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📖 Описание бота", callback_data="help_description")
    builder.button(text="📖 Описание функций", callback_data="help_functions")
    builder.button(text="💬 Связаться с разработчиком", callback_data="help_contact")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(2, 1, 2)
    return builder.as_markup()


def get_last_match_keyboard() -> InlineKeyboardMarkup:
    """Меню последнего матча"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Обновить данные", callback_data="last_match_refresh")
    builder.button(text="📊 Детальная статистика", callback_data="last_match_detailed")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(2, 2)
    return builder.as_markup()


def get_current_match_analysis_keyboard() -> InlineKeyboardMarkup:
    """Меню анализа текущего матча"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔍 Поиск матча", callback_data="current_match_search")
    builder.button(text="📊 Анализ команд", callback_data="current_match_teams")
    builder.button(text="🗺️ Анализ карты", callback_data="current_match_map")
    builder.button(text="🔄 Обновить данные", callback_data="current_match_refresh")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_number_input_keyboard(min_val: int, max_val: int, callback_prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура для ввода числа"""
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с числами
    for i in range(min_val, min(max_val + 1, min_val + 10)):
        builder.button(text=str(i), callback_data=f"{callback_prefix}_{i}")
    
    if max_val > min_val + 9:
        builder.button(text="✏️ Ввести вручную", callback_data=f"{callback_prefix}_manual")
    
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    
    builder.adjust(5, 5 if max_val > min_val + 9 else 0, 1)
    return builder.as_markup()


def get_back_to_history_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата к истории матчей"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к истории", callback_data="match_history")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


# =================== НОВЫЕ REPLY КЛАВИАТУРЫ ДЛЯ UI/UX ===================

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Основная reply-клавиатура внизу экрана"""
    builder = ReplyKeyboardBuilder()
    
    # Первый ряд - основные функции
    builder.button(text="📊 Статистика")
    builder.button(text="📝 История")
    builder.button(text="📈 Форма")
    
    # Второй ряд - дополнительные функции
    builder.button(text="🎮 Последний матч")
    builder.button(text="⚔️ Сравнение")
    builder.button(text="🔍 Анализ матча")
    
    # Третий ряд - профиль и помощь
    builder.button(text="👤 Профиль")
    builder.button(text="❓ Помощь")
    
    builder.adjust(3, 3, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_stats_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура для статистики"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📊 Общая статистика")
    builder.button(text="🗺️ По картам")
    builder.button(text="⏰ За сессию")
    builder.button(text="🔙 Назад")
    
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_history_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура для истории матчей"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="5 матчей")
    builder.button(text="10 матчей")
    builder.button(text="30 матчей")
    builder.button(text="✏️ Ввести число")
    builder.button(text="🔙 Назад")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_form_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура для анализа формы"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📊 Анализ 10 матчей")
    builder.button(text="📈 Анализ 20 матчей")
    builder.button(text="📋 Анализ 50 матчей")
    builder.button(text="✏️ Свой период")
    builder.button(text="🔙 Назад")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_comparison_reply_keyboard(show_comparison: bool = False, players_count: int = 0) -> ReplyKeyboardMarkup:
    """Reply-клавиатура для сравнения игроков"""
    builder = ReplyKeyboardBuilder()
    
    # Показываем кнопки добавления только если меньше 2 игроков
    if players_count < 2:
        builder.button(text="➕ Добавить себя")
        builder.button(text="👤 Добавить игрока")
    
    # Показываем кнопку сравнения когда ровно 2 игрока
    if show_comparison:
        builder.button(text="📊 Сравнить!")
        
    builder.button(text="🗑️ Очистить")
    builder.button(text="🔙 Назад")
    
    # Настраиваем расположение кнопок в зависимости от количества
    if players_count < 2:
        if show_comparison:
            builder.adjust(2, 1, 1, 1)  # Добавить себя, Добавить игрока | Сравнить | Очистить | Назад
        else:
            builder.adjust(2, 1, 1)     # Добавить себя, Добавить игрока | Очистить | Назад
    else:
        if show_comparison:
            builder.adjust(1, 1, 1)     # Сравнить | Очистить | Назад
        else:
            builder.adjust(1, 1)        # Очистить | Назад
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)




def get_help_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура для помощи"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📖 Описание функций")
    builder.button(text="💬 Связаться")
    builder.button(text="🔙 Назад")
    
    builder.adjust(1, 1, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_profile_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура для профиля"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🔄 Сменить профиль")
    builder.button(text="🔔 Уведомления")
    builder.button(text="⭐ Подписка")
    builder.button(text="🔙 Назад")
    
    builder.adjust(1, 2, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)