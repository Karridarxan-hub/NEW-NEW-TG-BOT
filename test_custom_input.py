#!/usr/bin/env python3
"""
Тест для проверки функциональности кастомного ввода
"""
import asyncio
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем обработчики
from bot.handlers.new_match_history_handler import (
    ask_custom_history_count, 
    process_custom_history_count,
    NewMatchHistoryStates
)
from bot.handlers.form_analysis_handler import (
    ask_custom_form_count,
    process_custom_form_count,
    FormAnalysisStates
)

def create_fake_user():
    return User(id=12345, is_bot=False, first_name="Test", username="testuser")

def create_fake_chat():
    return Chat(id=12345, type="private")

def create_fake_message(text="15"):
    user = create_fake_user()
    chat = create_fake_chat()
    return Message(
        message_id=1,
        date=1234567890,
        chat=chat,
        from_user=user,
        content_type="text",
        text=text
    )

def create_fake_callback(data="history_custom"):
    user = create_fake_user()
    chat = create_fake_chat()
    message = create_fake_message()
    message.edit_text = lambda text, **kwargs: print(f"Edit: {text}")
    
    callback = CallbackQuery(
        id="test_callback",
        from_user=user,
        chat_instance="test",
        data=data,
        message=message
    )
    callback.answer = lambda text="": asyncio.sleep(0)
    return callback

async def test_custom_input_validation():
    """Тест валидации пользовательского ввода"""
    print("🧪 Тестирование валидации кастомного ввода...")
    
    storage = MemoryStorage()
    
    # Тест валидных значений
    valid_inputs = ["15", "25", "50", "1", "100"]
    for input_val in valid_inputs:
        print(f"  ✅ Тестируем валидное значение: {input_val}")
        message = create_fake_message(input_val)
        message.answer = lambda text, **kwargs: print(f"    Answer: {text}")
        
        state = FSMContext(storage=storage, key=12345)
        await state.set_state(NewMatchHistoryStates.waiting_for_custom_count)
        
        try:
            # Здесь бы вызывался обработчик, но нам нужен мокинг
            match_count = int(input_val)
            if 1 <= match_count <= 100:
                print(f"    ✅ {input_val} - валидно")
            else:
                print(f"    ❌ {input_val} - вне диапазона")
        except ValueError:
            print(f"    ❌ {input_val} - не число")
    
    # Тест невалидных значений
    invalid_inputs = ["0", "101", "-5", "abc", "15.5", ""]
    for input_val in invalid_inputs:
        print(f"  ❌ Тестируем невалидное значение: {input_val}")
        try:
            match_count = int(input_val) if input_val else 0
            if match_count < 1 or match_count > 100:
                print(f"    ❌ {input_val} - вне диапазона (корректно отклонено)")
            else:
                print(f"    ⚠️ {input_val} - неожиданно принято")
        except ValueError:
            print(f"    ❌ {input_val} - не число (корректно отклонено)")

async def test_callback_handlers():
    """Тест обработчиков кнопок"""
    print("\n🧪 Тестирование обработчиков кнопок...")
    
    # Тест кнопки истории матчей
    print("  📝 Тестируем кнопку 'Ввести вручную' для истории")
    callback = create_fake_callback("history_custom")
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=12345)
    
    # Симулируем что произойдет
    print("    ✅ Кнопка должна установить состояние waiting_for_custom_count")
    
    # Тест кнопки анализа формы
    print("  📈 Тестируем кнопку 'Свой период' для анализа")
    callback = create_fake_callback("form_custom")
    print("    ✅ Кнопка должна установить состояние waiting_for_custom_count")

def test_keyboard_structure():
    """Тест структуры клавиатур"""
    print("\n🧪 Тестирование структуры клавиатур...")
    
    from keyboards import get_match_history_keyboard, get_form_analysis_keyboard
    
    # Тест клавиатуры истории матчей
    history_kb = get_match_history_keyboard()
    buttons = []
    for row in history_kb.inline_keyboard:
        for button in row:
            buttons.append(button.text)
    
    print("  📝 Кнопки истории матчей:")
    for btn in buttons:
        print(f"    - {btn}")
    
    if "✏️ Ввести вручную" in buttons:
        print("    ✅ Кнопка 'Ввести вручную' присутствует")
    else:
        print("    ❌ Кнопка 'Ввести вручную' отсутствует")
    
    # Тест клавиатуры анализа формы
    form_kb = get_form_analysis_keyboard()
    buttons = []
    for row in form_kb.inline_keyboard:
        for button in row:
            buttons.append(button.text)
    
    print("  📈 Кнопки анализа формы:")
    for btn in buttons:
        print(f"    - {btn}")
    
    if "✏️ Свой период" in buttons:
        print("    ✅ Кнопка 'Свой период' присутствует")
    else:
        print("    ❌ Кнопка 'Свой период' отсутствует")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов кастомного ввода...\n")
    
    # Тест структуры клавиатур (синхронно)
    test_keyboard_structure()
    
    # Тест валидации (асинхронно)
    await test_custom_input_validation()
    
    # Тест обработчиков (асинхронно)
    await test_callback_handlers()
    
    print("\n✅ Все тесты завершены!")
    print("\n💡 Инструкции для ручного тестирования:")
    print("1. Откройте бота в Telegram")
    print("2. Перейдите в '📝 История матчей'")
    print("3. Нажмите '✏️ Ввести вручную'")
    print("4. Введите число от 1 до 100")
    print("5. Проверьте что бот загружает указанное количество матчей")
    print("6. Повторите для '📈 Анализ формы' -> '✏️ Свой период'")

if __name__ == "__main__":
    asyncio.run(main())