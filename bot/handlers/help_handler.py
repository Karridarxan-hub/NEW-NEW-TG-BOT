"""
Обработчики для раздела помощи бота
Содержит подробную информацию о функциях бота и системе рейтингов
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

# Создаем роутер для обработчиков помощи
router = Router(name="help_handler")


def get_functions_help_keyboard() -> InlineKeyboardMarkup:
    """Меню разделов функций"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Статистика игрока", callback_data="help_func_stats")
    builder.button(text="📝 История матчей", callback_data="help_func_history")
    builder.button(text="📈 Анализ формы", callback_data="help_func_form")
    builder.button(text="🎮 Последний матч", callback_data="help_func_last")
    builder.button(text="⚔️ Сравнение игроков", callback_data="help_func_comparison")
    builder.button(text="🔍 Анализ текущего матча", callback_data="help_func_current")
    builder.button(text="👤 Профиль и ⚙️ Настройки", callback_data="help_func_profile")
    builder.button(text="🔙 Назад к помощи", callback_data="help")
    
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def get_help_navigation_keyboard() -> InlineKeyboardMarkup:
    """Навигация в разделах помощи"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📖 К разделам функций", callback_data="help_functions")
    builder.button(text="🔙 Назад к помощи", callback_data="help")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    
    builder.adjust(1, 2)
    return builder.as_markup()




@router.callback_query(F.data == "help")
async def show_help_main(callback: CallbackQuery):
    """Показать главное меню помощи"""
    from keyboards import get_help_keyboard
    
    text = (
        "❓ **Помощь по боту**\n\n"
        "🎮 **FACEIT CS2 Статистика Бот** - ваш персональный помощник для анализа игровой статистики.\n\n"
        "**Возможности бота:**\n"
        "• Детальная статистика игрока\n"
        "• Анализ последних матчей и формы\n"
        "• Сравнение с другими игроками\n"
        "• Анализ текущих матчей FACEIT\n"
        "• Статистика по картам и сессиям\n\n"
        "**Выберите раздел для получения подробной информации:**"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_description")
async def show_help_description(callback: CallbackQuery):
    """Описание бота и источников данных"""
    text = (
        "📖 **Описание бота**\n\n"
        "🎮 **FACEIT CS2 Статистика Бот** - это Telegram бот для анализа игровой статистики в Counter-Strike 2.\n\n"
        "**Откуда берутся данные:**\n"
        "• 🔗 **FACEIT API** - официальное API платформы FACEIT\n"
        "• 📊 **Реальные данные** - все статистики берутся напрямую с серверов FACEIT\n"
        "• ⚡ **Обновления в реальном времени** - данные всегда актуальны\n"
        "• 🔒 **Официальный доступ** - используем только публичные API\n\n"
        "**Что нужно для использования:**\n"
        "• 🎮 **Аккаунт FACEIT** - обязательно для получения статистики\n"
        "• 📱 **Telegram** - для взаимодействия с ботом\n"
        "• 🌐 **Интернет** - для доступа к данным FACEIT\n\n"
        "**Основные возможности:**\n"
        "• 📊 **Детальная статистика** - K/D, ADR, винрейт, ELO\n"
        "• 📝 **История матчей** - просмотр последних игр с подробностями\n"
        "• 📈 **Анализ формы** - сравнение текущих и прошлых результатов\n"
        "• ⚔️ **Сравнение игроков** - сопоставление статистики с друзьями\n"
        "• 🎮 **Последний матч** - детальный разбор последней игры\n\n"
        "**Безопасность:**\n"
        "• 🔐 Бот не имеет доступа к вашему паролю FACEIT\n"
        "• 📋 Используются только публичные данные профиля\n"
        "• 🛡️ Никаких изменений аккаунта не производится"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_functions")
async def show_help_functions(callback: CallbackQuery):
    """Показать меню описания функций"""
    text = (
        "📖 **Описание функций бота**\n\n"
        "Выберите раздел для получения подробной информации о том, как работает каждая функция:\n\n"
        "**Доступные разделы:**\n"
        "📊 **Статистика игрока** - общая, по картам, за сессию\n"
        "📝 **История матчей** - просмотр последних игр\n"
        "📈 **Анализ формы** - сравнение периодов\n"
        "🎮 **Последний матч** - детали последней игры\n"
        "⚔️ **Сравнение игроков** - сопоставление статистики\n"
        "🔍 **Анализ текущего матча** - живой анализ\n"
        "👤 **Профиль и настройки** - управление аккаунтом"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_functions_help_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_stats")
async def show_help_stats(callback: CallbackQuery):
    """Описание раздела статистики игрока"""
    text = (
        "📊 **Статистика игрока**\n\n"
        "**Общая статистика:**\n"
        "• 🎯 **Рейтинг игрока** - общая оценка эффективности\n"
        "• 📈 **K/D Ratio** - соотношение убийств к смертям\n"
        "• 💥 **ADR** - средний урон за раунд\n"
        "• 🎪 **KAST%** - процент полезных раундов\n"
        "• ⚡ **HS%** - процент хедшотов\n"
        "• 🏆 **ELO** - текущий рейтинг FACEIT\n"
        "• 📊 **Матчи** - сыграно/выиграно\n\n"
        "**Статистика по картам:**\n"
        "• Детальная статистика для каждой карты\n"
        "• Процент побед и средний рейтинг\n"
        "• Количество сыгранных матчей\n\n"
        "**Статистика за сессию:**\n"
        "• Статистика за текущую игровую сессию\n"
        "• Сравнение с общими показателями\n"
        "• Изменение ELO за сессию"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_history")
async def show_help_history(callback: CallbackQuery):
    """Описание раздела истории матчей"""
    text = (
        "📝 **История матчей**\n\n"
        "**Как получаются данные:**\n"
        "• Данные берутся из официального FACEIT API\n"
        "• Обновляются в реальном времени\n"
        "• Включают полную статистику каждого матча\n\n"
        "**Что показывается:**\n"
        "• 📅 **Дата и время** матча\n"
        "• 🗺️ **Карта** и результат\n"
        "• 📊 **Детальная статистика:**\n"
        "  - Убийства/смерти/ассисты\n"
        "  - Рейтинг за матч\n"
        "  - ADR и процент хедшотов\n"
        "  - KAST% и MVP раунды\n"
        "• 🏆 **Изменение ELO**\n"
        "• ⚔️ **Состав команд** и их статистика\n\n"
        "**Возможности:**\n"
        "• Просмотр от 1 до 20 последних матчей\n"
        "• Детальный анализ каждого матча\n"
        "• Статистика по картам из истории"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_form")
async def show_help_form(callback: CallbackQuery):
    """Описание раздела анализа формы"""
    text = (
        "📈 **Анализ формы**\n\n"
        "**Что сравнивается:**\n"
        "• Статистика за последние 10 матчей vs общая\n"
        "• Статистика за последние 5 матчей vs последние 20\n"
        "• Текущая сессия vs средние показатели\n\n"
        "**Метрики сравнения:**\n"
        "• 🎯 **Рейтинг игрока** - изменение эффективности\n"
        "• 📊 **K/D Ratio** - тренд убийств/смертей\n"
        "• 💥 **ADR** - изменение среднего урона\n"
        "• 🎪 **KAST%** - динамика полезности\n"
        "• ⚡ **HS%** - точность стрельбы\n"
        "• 🏆 **Win Rate** - процент побед\n\n"
        "**Индикаторы формы:**\n"
        "• 🔥 **Отличная форма** - все показатели растут\n"
        "• 📈 **Хорошая форма** - большинство показателей выше среднего\n"
        "• 📊 **Стабильная форма** - показатели на среднем уровне\n"
        "• 📉 **Спад формы** - показатели ниже среднего\n"
        "• ❄️ **Плохая форма** - большинство показателей падают"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_last")
async def show_help_last(callback: CallbackQuery):
    """Описание раздела последнего матча"""
    text = (
        "🎮 **Последний матч**\n\n"
        "**Что показывается:**\n"
        "• 📅 **Информация о матче:**\n"
        "  - Дата и время проведения\n"
        "  - Карта и режим игры\n"
        "  - Итоговый счет\n"
        "  - Длительность матча\n\n"
        "• 👤 **Ваша статистика:**\n"
        "  - K/D/A (убийства/смерти/ассисты)\n"
        "  - Рейтинг за матч\n"
        "  - ADR и общий урон\n"
        "  - Процент хедшотов\n"
        "  - KAST% и полезность\n"
        "  - Количество MVP раундов\n\n"
        "• ⚔️ **Команды:**\n"
        "  - Состав обеих команд\n"
        "  - ELO каждого игрока\n"
        "  - Статистика всех участников\n\n"
        "• 🏆 **Результат:**\n"
        "  - Победа/поражение\n"
        "  - Изменение ELO\n"
        "  - Влияние на общую статистику"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_comparison")
async def show_help_comparison(callback: CallbackQuery):
    """Описание раздела сравнения игроков"""
    text = (
        "⚔️ **Сравнение игроков**\n\n"
        "**Как работает:**\n"
        "• Добавьте до 2 игроков для сравнения\n"
        "• Введите их никнеймы FACEIT\n"
        "• Получите детальное сопоставление\n\n"
        "**Что сравнивается:**\n"
        "• 🏆 **Основные показатели:**\n"
        "  - ELO рейтинг и уровень\n"
        "  - Рейтинг эффективности\n"
        "  - K/D соотношение\n"
        "  - ADR и процент побед\n\n"
        "• 📊 **Детальная статистика:**\n"
        "  - Средние убийства за матч\n"
        "  - Процент хедшотов\n"
        "  - KAST% и полезность\n"
        "  - Количество сыгранных матчей\n\n"
        "• 📈 **Визуализация:**\n"
        "  - Сравнительные графики\n"
        "  - Процентные различия\n"
        "  - Сильные и слабые стороны\n\n"
        "**Полезно для:**\n"
        "• Поиска teammates\n"
        "• Анализа соперников\n"
        "• Оценки своего прогресса"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_current")
async def show_help_current(callback: CallbackQuery):
    """Описание раздела анализа текущего матча"""
    text = (
        "🔍 **Анализ текущего матча**\n\n"
        "**Как использовать:**\n"
        "• Введите ссылку на матч FACEIT\n"
        "• Или найдите матч по никнейму\n"
        "• Получите полный анализ команд\n\n"
        "**Анализ команд:**\n"
        "• 👥 **Состав команд:**\n"
        "  - ELO каждого игрока\n"
        "  - Средний ELO команды\n"
        "  - Рейтинг эффективности игроков\n"
        "  - Статистика на выбранной карте\n\n"
        "• 📊 **Сравнение:**\n"
        "  - Средний K/D команд\n"
        "  - ADR и процент побед\n"
        "  - Форма игроков\n"
        "  - Опыт на карте\n\n"
        "• 🎯 **Прогноз:**\n"
        "  - Вероятность победы команд\n"
        "  - Ключевые игроки\n"
        "  - Рекомендации по ставкам\n\n"
        "**Обновление данных:**\n"
        "• Данные обновляются в реальном времени\n"
        "• Актуальная статистика игроков\n"
        "• Учет последних изменений формы"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_func_profile")
async def show_help_profile(callback: CallbackQuery):
    """Описание разделов профиля и настроек"""
    text = (
        "👤 **Профиль и ⚙️ Настройки**\n\n"
        "**Профиль игрока:**\n"
        "• 🎮 **Основная информация:**\n"
        "  - Привязанный FACEIT аккаунт\n"
        "  - Текущий никнейм и ELO\n"
        "  - Статистика использования бота\n"
        "  - Дата регистрации\n\n"
        "• 📊 **Краткая статистика:**\n"
        "  - Ключевые показатели\n"
        "  - Текущий уровень\n"
        "  - Последняя активность\n\n"
        "**Настройки:**\n"
        "• 🔄 **Смена аккаунта:**\n"
        "  - Привязка нового FACEIT профиля\n"
        "  - Подтверждение смены\n\n"
        "• 📱 **Уведомления:**\n"
        "  - Настройка оповещений\n"
        "  - Частота обновлений\n\n"
        "• 🎨 **Отображение:**\n"
        "  - Формат вывода статистики\n"
        "  - Единицы измерения\n"
        "  - Язык интерфейса\n\n"
        "• 🔒 **Приватность:**\n"
        "  - Видимость профиля\n"
        "  - Доступ к статистике"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_contact")
async def show_help_contact(callback: CallbackQuery):
    """Показать контактную информацию"""
    text = (
        "💬 **Связаться с разработчиком**\n\n"
        "🚧 **В разработке**\n\n"
        "Раздел находится в стадии разработки.\n"
        "Скоро здесь появится информация для связи с разработчиком.\n\n"
        "**Планируемые способы связи:**\n"
        "• 📧 Email для обратной связи\n"
        "• 💬 Telegram канал с новостями\n"
        "• 🐛 Система сообщений об ошибках\n"
        "• 💡 Предложения по улучшению\n"
        "• 🆘 Техническая поддержка\n\n"
        "**Пока доступно:**\n"
        "• Используйте функции бота для анализа статистики\n"
        "• Сообщайте о проблемах через интерфейс бота\n"
        "• Следите за обновлениями в будущих версиях"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()