#!/usr/bin/env python3
"""
Тест интеграции нового обработчика анализа текущего матча
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_handler_import():
    """Тест импорта обработчика"""
    try:
        from bot.handlers.current_match_handler import router as current_match_router
        print("+ Роутер current_match_handler импортирован успешно")
        return True
    except ImportError as e:
        print(f"- Ошибка импорта current_match_handler: {e}")
        return False

def test_handlers_init():
    """Тест импорта из __init__.py в handlers"""
    try:
        from bot.handlers import current_match_router
        print("+ current_match_router импортирован из __init__.py успешно")
        return True
    except ImportError as e:
        print(f"- Ошибка импорта из __init__.py: {e}")
        return False

def test_all_handlers_import():
    """Тест импорта всех роутеров"""
    try:
        from bot.handlers import (
            main_router, 
            stats_router, 
            match_router, 
            settings_router, 
            match_history_router, 
            form_analysis_router, 
            last_match_router, 
            current_match_router
        )
        print("+ Все роутеры импортированы успешно")
        print(f"  - main_router: {type(main_router)}")
        print(f"  - current_match_router: {type(current_match_router)}")
        return True
    except ImportError as e:
        print(f"- Ошибка импорта роутеров: {e}")
        return False

def test_router_structure():
    """Тест структуры роутера"""
    try:
        from bot.handlers.current_match_handler import router
        
        # Проверяем, что это действительно роутер
        from aiogram import Router
        if not isinstance(router, Router):
            print(f"- router не является экземпляром Router: {type(router)}")
            return False
        
        print(f"+ router является корректным экземпляром Router")
        print(f"  - Имя роутера: {router.name}")
        return True
        
    except Exception as e:
        print(f"- Ошибка проверки структуры роутера: {e}")
        return False

def main():
    """Запуск всех тестов интеграции"""
    print("ТЕСТ ИНТЕГРАЦИИ ОБРАБОТЧИКА АНАЛИЗА ТЕКУЩЕГО МАТЧА")
    print("=" * 60)
    
    tests = [
        ("Импорт обработчика", test_handler_import),
        ("Импорт из __init__.py", test_handlers_init),
        ("Импорт всех роутеров", test_all_handlers_import),
        ("Структура роутера", test_router_structure),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"- Неожиданная ошибка: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ: {passed} пройдено, {failed} провалено")
    
    if failed == 0:
        print("Все тесты интеграции прошли успешно!")
        return True
    else:
        print("Есть проблемы с интеграцией!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)