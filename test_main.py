import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from storage import storage
from faceit_client import faceit_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FSM состояния
class BotStates(StatesGroup):
    waiting_for_nickname = State()

# Создаем экземпляры бота и диспетчера
bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Создаем роутер
router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    logger.info(f"Получена команда /start от пользователя {user_id}")
    
    # Проверяем, есть ли уже привязанный профиль
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if faceit_id:
        # Уже есть профиль - показываем главное меню
        await message.answer(
            "🎮 <b>FACEIT CS2 Бот</b>\n\n"
            "Добро пожаловать! Ваш профиль уже привязан.\n"
            "Выберите нужную функцию из меню.",
            parse_mode="HTML"
        )
        await state.clear()
    else:
        # Нет профиля - просим ввести никнейм
        await message.answer(
            "🎮 <b>Добро пожаловать в FACEIT CS2 Бот!</b>\n\n"
            "Для начала работы введите ваш никнейм на FACEIT:",
            parse_mode="HTML"
        )
        logger.info(f"Устанавливаем состояние waiting_for_nickname для пользователя {user_id}")
        await state.set_state(BotStates.waiting_for_nickname)


# Добавляем обработчик для всех текстовых сообщений для диагностики
@router.message()
async def handle_all_messages(message: Message, state: FSMContext):
    """Диагностический обработчик для всех сообщений"""
    user_id = message.from_user.id
    text = message.text if message.text else "None"
    current_state = await state.get_state()
    
    logger.info(f"Получено сообщение от {user_id}: '{text}', текущее состояние: {current_state}")
    
    # Если в состоянии ожидания никнейма - обрабатываем
    if current_state == BotStates.waiting_for_nickname:
        await process_nickname_logic(message, state)
    else:
        await message.answer("❓ Используйте команду /start для начала работы.")


async def process_nickname_logic(message: Message, state: FSMContext):
    """Обработчик ввода никнейма"""
    user_id = message.from_user.id
    nickname = message.text.strip()
    
    logger.info(f"Пользователь {user_id} ввел никнейм: {nickname}")
    
    # Показываем, что обрабатываем запрос
    await message.answer("🔍 Ищем ваш профиль на FACEIT...")
    
    try:
        # Ищем игрока по никнейму
        player_data = await faceit_client.find_player_by_nickname(nickname)
        
        if not player_data:
            await message.answer(
                "❌ <b>Игрок не найден</b>\n\n"
                "Проверьте правильность написания никнейма и попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        # Сохраняем данные пользователя
        storage.set_user_faceit_data(
            user_id, 
            player_data.get('player_id'),
            player_data.get('nickname')
        )
        
        # Получаем уровень и ELO
        cs2_stats = player_data.get('games', {}).get('cs2', {})
        level = cs2_stats.get('skill_level', 'N/A')
        elo = cs2_stats.get('faceit_elo', 'N/A')
        country = player_data.get('country', 'Unknown')
        
        await message.answer(
            f"✅ <b>Профиль найден!</b>\n\n"
            f"👤 <b>Никнейм:</b> {player_data.get('nickname')}\n"
            f"🏆 <b>Уровень:</b> {level}\n"
            f"⚡ <b>ELO:</b> {elo}\n"
            f"🌍 <b>Страна:</b> {country}\n\n"
            f"🎮 Теперь вы можете использовать все функции бота!\n"
            f"Используйте команду /start для доступа к меню.",
            parse_mode="HTML"
        )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при поиске игрока {nickname}: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при поиске</b>\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML"
        )


# Регистрируем роутер
dp.include_router(router)

async def main():
    """Главная функция"""
    try:
        logger.info("🚀 Запуск тестового бота...")
        logger.info(f"🤖 Bot Token: {'*' * 20}{settings.bot_token[-10:]}")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())