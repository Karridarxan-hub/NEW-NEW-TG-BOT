from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import get_profile_keyboard, get_main_menu_keyboard
from storage import storage
from faceit_client import faceit_client
import logging

logger = logging.getLogger(__name__)

# Создаем роутер для обработчика профиля
router = Router(name="profile_handler")

# FSM состояния для смены профиля
class ProfileStates(StatesGroup):
    waiting_for_new_nickname = State()

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль пользователя"""
    user_id = callback.from_user.id
    
    try:
        user_data = await storage.get_user(user_id)
        
        if not user_data:
            await callback.answer("❌ Профиль не найден! Сначала привяжите профиль через /start", show_alert=True)
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
            avatar = player_details.get('avatar', '')
        else:
            elo = 0
            level = 0
            region = 'Unknown'
            avatar = ''
        
        # Получаем настройки пользователя для отображения
        settings = await storage.get_user_settings(user_id) or {}
        notifications = "Включены ✅" if settings.get('notifications', True) else "Выключены ❌"
        subscription_type = settings.get('subscription_type', 'standard')
        subscription_text = "Премиум ⭐" if subscription_type == 'premium' else "Стандарт 📦"
        
        # Форматируем даты
        created_at = user_data.get('created_at', 'Неизвестно')
        if created_at and created_at != 'Неизвестно':
            try:
                # Если это строка с датой ISO, преобразуем
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
                if isinstance(last_activity, str):
                    activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    last_activity = activity_dt.strftime('%d.%m.%Y %H:%M')
                else:
                    last_activity = str(last_activity)[:19]
            except:
                last_activity = str(last_activity)
        
        # Формируем сообщение профиля
        profile_text = f"""
👤 **Ваш профиль**

🎮 **FACEIT данные:**
• Никнейм: {nickname}
• ID: `{faceit_id}`
• ELO: {elo} (Уровень {level})
• Регион: {region}

⚙️ **Настройки бота:**
• Уведомления: {notifications}
• Подписка: {subscription_text}

📊 **Информация об аккаунте:**
• Дата регистрации: {created_at}
• Последняя активность: {last_activity}

Используйте кнопки ниже для управления профилем.
"""
        
        await callback.message.edit_text(
            profile_text,
            parse_mode="Markdown",
            reply_markup=get_profile_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing profile for user {user_id}: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке профиля", show_alert=True)

@router.callback_query(F.data == "change_profile")
async def request_new_nickname(callback: CallbackQuery, state: FSMContext):
    """Запросить новый никнейм для смены профиля"""
    try:
        await callback.message.edit_text(
            "🔄 **Смена профиля**\n\n"
            "Введите новый никнейм FACEIT для привязки к вашему аккаунту:\n\n"
            "💡 *Убедитесь, что никнейм написан правильно*"
        )
        await state.set_state(ProfileStates.waiting_for_new_nickname)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error requesting new nickname: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.message(ProfileStates.waiting_for_new_nickname)
async def process_new_nickname(message: Message, state: FSMContext):
    """Обработка нового никнейма для смены профиля"""
    nickname = message.text.strip()
    user_id = message.from_user.id
    
    try:
        # Валидация никнейма
        if len(nickname) < 2:
            await message.answer("❌ Никнейм слишком короткий (минимум 2 символа). Попробуйте еще раз:")
            return
        
        if len(nickname) > 30:
            await message.answer("❌ Никнейм слишком длинный (максимум 30 символов). Попробуйте еще раз:")
            return
        
        if not nickname.replace('_', '').replace('-', '').isalnum():
            await message.answer("❌ Никнейм может содержать только буквы, цифры, _ и -. Попробуйте еще раз:")
            return
        
        # Показываем сообщение о поиске
        search_msg = await message.answer("🔍 Ищем профиль на FACEIT...")
        
        # Ищем игрока в FACEIT API
        player_data = await faceit_client.find_player_by_nickname(nickname)
        
        if not player_data:
            await search_msg.edit_text(
                f"❌ Игрок с никнеймом '{nickname}' не найден на FACEIT.\n\n"
                f"Проверьте правильность написания и попробуйте еще раз:"
            )
            return
        
        # Получаем FACEIT ID из найденных данных
        faceit_id = player_data.get('player_id')
        if not faceit_id:
            await search_msg.edit_text(
                "❌ Ошибка при получении данных игрока. Попробуйте еще раз:"
            )
            return
        
        # Обновляем профиль пользователя
        await storage.save_user(user_id, faceit_id, nickname)
        
        # Очищаем состояние FSM
        await state.clear()
        
        # Подтверждение успешной смены
        success_text = f"""
✅ **Профиль успешно изменен!**

🎮 **Новый профиль:**
• Никнейм: {nickname}
• FACEIT ID: `{faceit_id}`

Теперь вся статистика будет отображаться для этого профиля.
"""
        
        await search_msg.edit_text(
            success_text,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        
        logger.info(f"User {user_id} changed profile to {nickname} ({faceit_id})")
        
    except Exception as e:
        logger.error(f"Error processing new nickname for user {user_id}: {e}")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при смене профиля. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

# Обработчик для отмены смены профиля (если пользователь нажмет кнопку во время FSM)
@router.callback_query(ProfileStates.waiting_for_new_nickname)
async def cancel_profile_change(callback: CallbackQuery, state: FSMContext):
    """Отмена смены профиля"""
    await state.clear()
    
    # Возвращаемся к профилю
    from aiogram.types import CallbackQuery
    fake_callback = CallbackQuery(
        id=callback.id,
        from_user=callback.from_user,
        chat_instance=callback.chat_instance,
        message=callback.message,
        data="profile"
    )
    await show_profile(fake_callback)