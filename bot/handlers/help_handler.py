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
        "📊 **СТАТИСТИКА ИГРОКА - Полное руководство**\n\n"
        "**🎯 Как использовать:**\n"
        "1. Нажмите '📊 Статистика' в главном меню\n"
        "2. Выберите тип статистики:\n"
        "   • **Общая** - полный обзор аккаунта\n"
        "   • **По картам** - детали по каждой карте\n"
        "   • **За сессию** - последние 12 часов игры\n\n"
        "**📝 Что показывается:**\n"
        "• **ELO и уровень** FACEIT (1-10)\n"
        "• **K/D, K/R, ADR** - боевые показатели\n"
        "• **HLTV Rating** - общий рейтинг\n"
        "• **Винрейт** и количество матчей\n"
        "• **HS%** - процент хедшотов\n"
        "• **KAST%** - процент полезных раундов\n"
        "• **Топ-3 карты** по винрейту\n\n"
        "**💡 Полезные советы:**\n"
        "• Проверяйте статистику перед игрой\n"
        "• Сравнивайте с прошлыми периодами\n"
        "• Анализируйте слабые карты\n\n"
        "**⚠️ Важно знать:**\n"
        "• Данные обновляются после каждого матча\n"
        "• Сессия = матчи за последние 12 часов\n"
        "• Минимум 20 матчей для точной статистики"
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
        "📝 **ИСТОРИЯ МАТЧЕЙ - Детальный анализ**\n\n"
        "**🎯 Как использовать:**\n"
        "1. Выберите '📝 История матчей'\n"
        "2. Укажите количество (5/10/30 или своё)\n"
        "3. Получите детальный список\n\n"
        "**📊 Информация по каждому матчу:**\n"
        "• 🏆/❌ - победа или поражение\n"
        "• Карта и счет (например: Mirage 16-14)\n"
        "• K/D/A и рейтинг за матч\n"
        "• ADR и процент хедшотов\n"
        "• Изменение ELO (+25/-25)\n"
        "• Ссылка на матч в FACEIT\n\n"
        "**💡 Лайфхаки:**\n"
        "• Анализируйте паттерны поражений\n"
        "• Ищите карты с низким винрейтом\n"
        "• Отслеживайте прогресс K/D\n\n"
        "**📈 Индикаторы формы:**\n"
        "• 3+ победы подряд = 🔥 горячая серия\n"
        "• 3+ поражения = ❄️ кулдаун\n"
        "• Рейтинг >1.2 = отличная игра\n\n"
        "**⚠️ Примечание:**\n"
        "Данные берутся из FACEIT API в реальном времени"
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
        "⚔️ **СРАВНЕНИЕ ИГРОКОВ - Батл статистики**\n\n"
        "**🎯 Как использовать:**\n"
        "1. Нажмите '⚔️ Сравнение'\n"
        "2. Добавьте себя или введите ник\n"
        "3. Добавьте второго игрока\n"
        "4. Нажмите '📊 Сравнить!'\n\n"
        "**📊 Что сравнивается (15 параметров):**\n"
        "• **Основные:** ELO, уровень, матчи\n"
        "• **Боевые:** K/D, K/R, ADR\n"
        "• **Точность:** HS%, Clutches\n"
        "• **Эффективность:** KAST%, Rating\n"
        "• **Достижения:** Aces, 4K, 3K\n\n"
        "**📈📉➡️ Визуальные индикаторы:**\n"
        "• 📈 Зеленый = вы лучше\n"
        "• 📉 Красный = соперник лучше\n"
        "• ➡️ Серый = равные показатели\n\n"
        "**💡 Когда использовать:**\n"
        "• Поиск тиммейта схожего уровня\n"
        "• Анализ соперника перед игрой\n"
        "• Мотивация для улучшения\n\n"
        "**⚠️ Подсказка:**\n"
        "Используйте '➕ Добавить себя' для быстрого добавления"
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
        f"• Ваш Telegram ID: `{callback.from_user.id}`\n\n"
        "**🎁 Бонусы за репорты:**\n"
        "• Критический баг = месяц премиума\n"
        "• Полезная фича = 2 недели премиума\n"
        "• Мелкий баг = благодарность в боте"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_quick_start")
async def show_help_quick_start(callback: CallbackQuery):
    """Показать быстрый старт"""
    text = (
        "🚀 **БЫСТРЫЙ СТАРТ - За 3 минуты**\n\n"
        "**1️⃣ Привяжите аккаунт:**\n"
        "→ \"👤 Профиль\" → Введите ник FACEIT\n\n"
        "**2️⃣ Проверьте статистику:**\n"
        "→ \"📊 Статистика\" → \"Общая\"\n\n"
        "**3️⃣ Посмотрите последние матчи:**\n"
        "→ \"📝 История\" → \"10 матчей\"\n\n"
        "**✅ Готово! Теперь вы можете:**\n"
        "• Анализировать свою игру\n"
        "• Сравниваться с друзьями\n"
        "• Отслеживать прогресс\n"
        "• Получать уведомления о матчах\n\n"
        "**💡 Полезные советы для начала:**\n"
        "• Изучите статистику по картам\n"
        "• Сравните себя с игроками схожего уровня\n"
        "• Анализируйте форму после каждой сессии\n"
        "• Настройте уведомления в профиле"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help_faq")
async def show_help_faq(callback: CallbackQuery):
    """Показать часто задаваемые вопросы"""
    text = (
        "❓ **ЧАСТЫЕ ВОПРОСЫ**\n\n"
        "**Q:** Бот не находит мой профиль?\n"
        "**A:** Проверьте точность ника, регистр важен. "
        "Попробуйте скопировать ник прямо с FACEIT.\n\n"
        "**Q:** Статистика не обновляется?\n"
        "**A:** Подождите 2-3 минуты после матча. "
        "FACEIT API обновляется с небольшой задержкой.\n\n"
        "**Q:** Можно сменить привязанный аккаунт?\n"
        "**A:** Да, через \"👤 Профиль\" → \"🔄 Сменить профиль\"\n\n"
        "**Q:** Бот бесплатный?\n"
        "**A:** Да, все основные функции абсолютно бесплатны!\n\n"
        "**Q:** Как часто обновляются данные?\n"
        "**A:** В реальном времени из официального FACEIT API\n\n"
        "**Q:** Бот видит приватные профили?\n"
        "**A:** Нет, только публичные данные FACEIT\n\n"
        "**Q:** Можно ли сравнивать больше 2 игроков?\n"
        "**A:** Пока только 2, но планируется расширение\n\n"
        "**Q:** Что означают эмодзи в сравнении?\n"
        "**A:** 📈 лучше, 📉 хуже, ➡️ равно\n\n"
        "**Не нашли ответ?** Обращайтесь к @karriDD"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_help_navigation_keyboard()
    )
    await callback.answer()