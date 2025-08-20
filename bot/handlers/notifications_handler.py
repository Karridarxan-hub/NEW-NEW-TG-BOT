from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import logging

from keyboards import get_back_to_main_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "notifications")
async def show_notifications(callback: CallbackQuery, state: FSMContext):
    """Показать уведомления о матчах"""
    await state.clear()
    
    text = "🔔 **Система уведомлений**\n\n" \
           "Уведомления автоматически отправляются при завершении матчей.\n" \
           "Настроить уведомления можно в разделе 'Настройки'."
    
    await callback.message.edit_text(
        text, 
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()