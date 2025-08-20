from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards import get_settings_keyboard, get_main_menu_keyboard
from storage import storage
import logging

logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков настроек
router = Router(name="settings_handler")


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Показать меню настроек"""
    user_id = callback.from_user.id
    
    try:
        # Получаем текущие настройки пользователя
        settings = await storage.get_user_settings(user_id) or {}
        
        notifications = settings.get('notifications', True)
        subscription_type = settings.get('subscription_type', 'standard')
        
        # Форматируем статусы
        notification_status = "Включены ✅" if notifications else "Выключены ❌"
        subscription_status = "Премиум ⭐" if subscription_type == 'premium' else "Стандарт 📦"
        
        settings_text = f"""
⚙️ **Настройки бота**

📱 **Текущие настройки:**
• Уведомления о матчах: {notification_status}
• Тип подписки: {subscription_status}

Используйте кнопки ниже для изменения настроек.
"""
        
        await callback.message.edit_text(
            settings_text,
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing settings for user {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке настроек", show_alert=True)

@router.callback_query(F.data == "settings_notifications")
async def show_notifications_settings(callback: CallbackQuery):
    """Показать настройки уведомлений"""
    user_id = callback.from_user.id
    
    try:
        # Получаем текущие настройки
        settings = await storage.get_user_settings(user_id) or {}
        notifications_enabled = settings.get('notifications', True)
        
        status_text = "включены ✅" if notifications_enabled else "выключены ❌"
        action_text = "Выключить" if notifications_enabled else "Включить"
        action_emoji = "🔕" if notifications_enabled else "🔔"
        callback_action = "disable" if notifications_enabled else "enable"
        
        notifications_text = f"""
🔔 **Настройки уведомлений**

📱 **Текущий статус:** Уведомления {status_text}

**Что включают уведомления:**
• Завершение ваших матчей
• Обновления статистики
• Важные изменения в боте

Вы можете включить или выключить уведомления в любое время.
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{action_emoji} {action_text} уведомления", 
                callback_data=f"toggle_notifications_{callback_action}"
            )],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")]
        ])
        
        await callback.message.edit_text(
            notifications_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing notifications settings for user {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке настроек уведомлений", show_alert=True)

@router.callback_query(F.data.startswith("toggle_notifications_"))
async def toggle_notifications(callback: CallbackQuery):
    """Переключить состояние уведомлений"""
    user_id = callback.from_user.id
    action = callback.data.split("_")[-1]  # enable или disable
    
    try:
        # Устанавливаем новое состояние
        new_state = action == "enable"
        await storage.update_user_settings(user_id, {'notifications': new_state})
        
        # Показываем уведомление пользователю
        status_text = "включены ✅" if new_state else "выключены ❌"
        await callback.answer(f"Уведомления {status_text}", show_alert=True)
        
        # Обновляем настройки уведомлений
        await show_notifications_settings(callback)
        
        logger.info(f"User {user_id} {'enabled' if new_state else 'disabled'} notifications")
        
    except Exception as e:
        logger.error(f"Error toggling notifications for user {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при изменении настроек", show_alert=True)

@router.callback_query(F.data == "settings_subscription")
async def show_subscription_settings(callback: CallbackQuery):
    """Показать настройки подписки"""
    user_id = callback.from_user.id
    
    try:
        settings = await storage.get_user_settings(user_id) or {}
        subscription_type = settings.get('subscription_type', 'standard')
        is_premium = subscription_type == 'premium'
        
        if is_premium:
            subscription_text = """
⭐ **Управление подпиской**

🔥 **Текущий статус:** Премиум ⭐

✅ **Доступные функции:**
• Все базовые функции
• Детальная статистика по картам
• Анализ формы до 100 матчей
• Сравнение до 10 игроков
• Уведомления о матчах в реальном времени
• Приоритетная техподдержка

💎 **Ваша подписка активна!**
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Стандарт", callback_data="subscription_standard")],
                [InlineKeyboardButton(text="⭐ Премиум (активно)", callback_data="subscription_premium")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")]
            ])
        else:
            subscription_text = """
📦 **Управление подпиской**

📦 **Текущий статус:** Стандарт (бесплатно)

✅ **Доступные функции:**
• Базовая статистика игрока
• История последних 20 матчей
• Анализ формы до 20 матчей
• Сравнение до 3 игроков

⭐ **Премиум функции:**
• Детальная статистика по картам
• Анализ формы до 100 матчей
• Сравнение до 10 игроков
• Уведомления о матчах
• Приоритетная поддержка

💰 **Стоимость Премиум:** В разработке
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📦 Стандарт (активно)", callback_data="subscription_standard")],
                [InlineKeyboardButton(text="⭐ Премиум", callback_data="subscription_premium")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")]
            ])
        
        await callback.message.edit_text(
            subscription_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing subscription settings for user {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке настроек подписки", show_alert=True)

@router.callback_query(F.data == "subscription_standard")
async def show_standard_subscription(callback: CallbackQuery):
    """Показать информацию о стандартной подписке"""
    try:
        standard_text = """
📦 **Стандартная подписка (бесплатно)**

✅ **Включенные функции:**
• Базовая статистика игрока
• История последних 20 матчей
• Анализ формы до 20 матчей
• Сравнение до 3 игроков
• Общая статистика CS2
• Просмотр последнего матча

❌ **Недоступно в стандартной версии:**
• Детальная статистика по картам
• Расширенный анализ формы (100+ матчей)
• Уведомления о матчах
• Приоритетная поддержка
• Сравнение более 3 игроков

📦 Стандартная подписка активна по умолчанию для всех пользователей.
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Перейти на Премиум", callback_data="subscription_premium")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_subscription")]
        ])
        
        await callback.message.edit_text(
            standard_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing standard subscription: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "subscription_premium")
async def show_premium_subscription(callback: CallbackQuery):
    """Показать информацию о премиум подписке"""
    try:
        premium_text = """
⭐ **Премиум подписка**

🔥 **Все функции Стандарт +**

✅ **Дополнительные возможности:**
• Детальная статистика по всем картам
• Анализ формы до 100 матчей
• Сравнение до 10 игроков
• Уведомления о завершении матчей
• Трекинг текущих матчей в реальном времени
• Расширенная аналитика и метрики
• Приоритетная поддержка (ответ в течение 4 часов)

💰 **Стоимость:** В разработке
📅 **Период:** 30 дней
🔄 **Автопродление:** Да

🛠️ **Статус:** Функция находится в разработке
⏰ **Запуск:** Ожидается в следующих обновлениях

💡 Пока что все пользователи имеют доступ к базовому функционалу бесплатно.
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 В разработке", callback_data="subscription_development")],
            [InlineKeyboardButton(text="📦 Вернуться к Стандарт", callback_data="subscription_standard")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_subscription")]
        ])
        
        await callback.message.edit_text(
            premium_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing premium subscription: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "subscription_development")
async def show_development_status(callback: CallbackQuery):
    """Показать статус разработки премиум функций"""
    try:
        development_text = """
🔧 **Премиум подписка - В разработке**

🚧 **Что находится в разработке:**
• Интеграция с Telegram Stars для оплаты
• Система управления подписками
• Расширенные аналитические функции
• Уведомления в реальном времени
• Премиум статистика по картам

⏰ **Планируемые этапы:**
1️⃣ Завершение базового функционала
2️⃣ Интеграция платежной системы
3️⃣ Бета-тестирование премиум функций
4️⃣ Официальный запуск

📞 **Обратная связь:**
Ваше мнение важно для нас! Если у вас есть предложения по премиум функциям, свяжитесь с поддержкой.

💡 **На данный момент все функции доступны бесплатно.**
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться с поддержкой", callback_data="help_contact")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="subscription_premium")]
        ])
        
        await callback.message.edit_text(
            development_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing development status: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "help_contact")
async def show_contact_support(callback: CallbackQuery):
    """Показать информацию о связи с поддержкой"""
    try:
        contact_text = """
📞 **Связь с поддержкой**

👥 **Как связаться с нами:**
• Напишите свой вопрос в этом чате
• Используйте хэштег #поддержка

📅 **Время ответа:**
• Обычно: в течение 24 часов
• Премиум пользователи: в течение 4 часов

🔍 **Популярные вопросы:**
• Проблемы с поиском профиля
• Ошибки при получении статистики
• Предложения по улучшению бота
• Вопросы о премиум подписке

💬 **При обращении укажите:**
• Ваш FACEIT никнейм
• Описание проблемы
• Скриншот (если нужно)

🚀 Мы всегда готовы помочь!
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings")]
        ])
        
        await callback.message.edit_text(
            contact_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing contact support: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

