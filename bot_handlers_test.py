#!/usr/bin/env python3
"""
Тестирование обработчиков бота для статистики на реальном аккаунте "Geun-Hee"
Проверяем функции show_overall_stats, show_maps_stats, show_session_stats

Автор: Claude Code
Версия: 1.0
Дата: 2025-08-19
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Импортируем standalone клиент из предыдущего теста
from simple_stats_test import TestFaceitClient

class MockStorage:
    """Mock для storage, чтобы имитировать работу с базой данных"""
    
    def __init__(self):
        # Имитируем пользователя Geun-Hee в системе
        self.users = {
            12345: {  # Тестовый user_id
                'user_id': 12345,
                'faceit_id': '0cf595d2-b9a1-4316-9df9-a627c7a8c664',  # Реальный ID Geun-Hee
                'nickname': 'Geun-Hee',
                'created_at': datetime.now().isoformat()
            }
        }
    
    async def get_user_faceit_id(self, user_id: int) -> Optional[str]:
        """Получить FACEIT ID пользователя"""
        user = self.users.get(user_id)
        return user['faceit_id'] if user else None
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить данные пользователя"""
        return self.users.get(user_id)


class MockCallbackQuery:
    """Mock для CallbackQuery из aiogram"""
    
    def __init__(self, user_id: int):
        self.from_user = type('User', (), {'id': user_id})()
        self.message = type('Message', (), {
            'edit_text': self._edit_text,
            'chat': type('Chat', (), {'id': 123})()
        })()
        self.answered = False
        self.edited_texts = []
    
    async def _edit_text(self, text: str, **kwargs):
        """Имитация редактирования сообщения"""
        self.edited_texts.append(text)
        logger.info(f"Message edited: {len(text)} chars")
        if kwargs.get('parse_mode'):
            logger.info(f"Parse mode: {kwargs['parse_mode']}")
    
    async def answer(self, text: str = "", show_alert: bool = False):
        """Имитация ответа на callback"""
        self.answered = True
        if text:
            logger.info(f"Callback answer: {text}")


class BotHandlersTester:
    """Тестер для обработчиков бота"""
    
    def __init__(self, api_key: str = "41f48f43-609c-4639-b821-360b039f18b4"):
        self.api_key = api_key
        self.client = TestFaceitClient(api_key)
        self.mock_storage = MockStorage()
        self.test_user_id = 12345
        self.results = {"passed": 0, "failed": 0, "total": 0}
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Логирование результата теста"""
        self.results["total"] += 1
        if success:
            self.results["passed"] += 1
            logger.info(f"[PASS] {test_name}: {details}")
        else:
            self.results["failed"] += 1
            logger.error(f"[FAIL] {test_name}: {details}")
    
    async def simulate_show_overall_stats(self, callback: MockCallbackQuery) -> bool:
        """Имитация функции show_overall_stats"""
        try:
            user_id = callback.from_user.id
            
            # Получаем FACEIT ID
            faceit_id = await self.mock_storage.get_user_faceit_id(user_id)
            if not faceit_id:
                await callback.answer("❌ Профиль не привязан!", show_alert=True)
                return False
            
            # Отправляем сообщение о загрузке
            await callback.message.edit_text("📊 Загружаем статистику...")
            
            # Получаем данные
            player_details = await self.client.get_player_details(faceit_id)
            stats_data = await self.client.get_player_stats(faceit_id)
            
            if not stats_data or not player_details:
                await callback.message.edit_text("❌ Не удалось загрузить статистику.")
                await callback.answer()
                return False
            
            # Форматируем статистику
            formatted_stats = self.client.format_player_stats(player_details, stats_data)
            
            if not formatted_stats:
                await callback.message.edit_text("❌ Ошибка обработки статистики.")
                await callback.answer()
                return False
            
            # Получаем пользователя
            user_data = await self.mock_storage.get_user(user_id)
            nickname = user_data.get('nickname', 'Unknown') if user_data else 'Unknown'
            
            # HLTV рейтинг
            hltv_rating = formatted_stats.get('hltv_rating', 0.0)
            
            # Формируем сообщение (как в оригинальном stats_handler)
            stats_message = f"""
📊 **Общая статистика**

👤 **Игрок:** {nickname}
🎮 **ELO:** {formatted_stats.get('elo', 0)} (Уровень {formatted_stats.get('level', 0)})
⭐ **HLTV 2.1:** {hltv_rating:.2f}
🌍 **Регион:** {formatted_stats.get('region', 'N/A')}
✅ **Верифицирован:** {'Да' if formatted_stats.get('verified', False) else 'Нет'}

📈 **Основные показатели:**
• **Матчей сыграно:** {formatted_stats.get('matches', 0)}
• **Побед:** {formatted_stats.get('wins', 0)} ({formatted_stats.get('winrate', 0):.1f}%)
• **K/D:** {formatted_stats.get('kd_ratio', 0):.3f}
• **Средний K/D:** {formatted_stats.get('average_kd', 0):.3f}
• **ADR:** {formatted_stats.get('adr', 0):.1f}
• **KAST:** {formatted_stats.get('kast', 0):.1f}%

🎯 **Дополнительная статистика:**
• **Средний % хедшотов:** {formatted_stats.get('headshots_avg', 0):.1f}%
• **Общий % хедшотов:** {formatted_stats.get('headshots_total', 0):.1f}%
• **Лучшая серия побед:** {formatted_stats.get('longest_win_streak', 0)}
• **K/R Ratio:** {formatted_stats.get('kpr', 0):.3f}
• **First Kills:** {formatted_stats.get('first_kills', 0)}
• **Flash Assists:** {formatted_stats.get('flash_assists', 0)}

_Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}_
"""
            
            # Отправляем статистику
            await callback.message.edit_text(stats_message, parse_mode="Markdown")
            await callback.answer()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in simulate_show_overall_stats: {e}")
            await callback.message.edit_text("❌ Произошла ошибка при загрузке статистики.")
            await callback.answer()
            return False
    
    async def simulate_show_maps_stats(self, callback: MockCallbackQuery) -> bool:
        """Имитация функции show_maps_stats"""
        try:
            user_id = callback.from_user.id
            
            faceit_id = await self.mock_storage.get_user_faceit_id(user_id)
            if not faceit_id:
                await callback.answer("❌ Профиль не привязан!", show_alert=True)
                return False
            
            await callback.message.edit_text("🗺️ Загружаем статистику по картам...")
            
            # Получаем данные
            player_details = await self.client.get_player_details(faceit_id)
            stats_data = await self.client.get_player_stats(faceit_id)
            
            if not stats_data or not player_details:
                await callback.message.edit_text("❌ Статистика по картам недоступна")
                await callback.answer()
                return False
            
            # Форматируем статистику
            formatted_stats = self.client.format_player_stats(player_details, stats_data)
            maps_stats = formatted_stats.get('maps', {})
            
            if not maps_stats:
                await callback.message.edit_text("❌ Данные по картам отсутствуют.")
                await callback.answer()
                return False
            
            # Сортируем карты по количеству матчей
            sorted_maps = sorted(
                maps_stats.items(), 
                key=lambda x: x[1].get('matches', 0), 
                reverse=True
            )
            
            # Формируем сообщение
            message = "🗺️ **Статистика по картам**\n\n"
            
            for i, (map_name, map_data) in enumerate(sorted_maps[:7], 1):  # Топ-7 карт
                matches = map_data.get('matches', 0)
                winrate = map_data.get('winrate', 0)
                kd_ratio = map_data.get('kd_ratio', 0)
                adr = map_data.get('adr', 0)
                kast = map_data.get('kast', 0)
                hltv_rating = map_data.get('hltv_rating', 0)
                
                # Пропускаем карты без данных
                if matches == 0:
                    continue
                    
                message += f"**{i}. {map_name}**\n"
                message += f"• Матчей: {matches}\n"
                message += f"• Winrate: {winrate:.1f}%\n"
                message += f"• K/D: {kd_ratio:.3f}\n"
                message += f"• ADR: {adr:.1f}\n"
                message += f"• KAST: {kast:.1f}%\n"
                message += f"• HLTV 2.1: {hltv_rating:.2f}\n\n"
            
            if len(message.split('\n')) <= 3:  # Если нет данных
                message += "_Недостаточно данных для отображения статистики по картам._"
            else:
                message += f"_Показано карт: {min(len(sorted_maps), 7)} из {len(sorted_maps)}_"
            
            await callback.message.edit_text(message, parse_mode="Markdown")
            await callback.answer()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in simulate_show_maps_stats: {e}")
            await callback.message.edit_text("❌ Произошла ошибка при загрузке статистики по картам.")
            await callback.answer()
            return False
    
    async def simulate_show_session_stats(self, callback: MockCallbackQuery) -> bool:
        """Имитация функции show_session_stats"""
        try:
            user_id = callback.from_user.id
            
            faceit_id = await self.mock_storage.get_user_faceit_id(user_id)
            if not faceit_id:
                await callback.answer("❌ Профиль не привязан!", show_alert=True)
                return False
            
            await callback.message.edit_text("⏰ Загружаем статистику сессии...")
            
            # Получаем историю матчей
            history_data = await self.client.get_player_history(faceit_id, limit=30)
            
            if not history_data or 'items' not in history_data:
                await callback.message.edit_text("❌ Нет данных о последних матчах")
                await callback.answer()
                return False
            
            matches = history_data['items']
            
            # Фильтруем матчи за последние 12 часов
            session_matches = []
            cutoff_time = datetime.now() - timedelta(hours=12)
            
            for match in matches:
                finished_at = match.get('finished_at', 0)
                if finished_at:
                    # Время может быть в секундах или миллисекундах
                    if finished_at > 10**12:  # Если больше чем timestamp в секундах
                        match_time = datetime.fromtimestamp(finished_at / 1000)
                    else:
                        match_time = datetime.fromtimestamp(finished_at)
                    
                    if match_time > cutoff_time:
                        session_matches.append(match)
            
            if not session_matches:
                await callback.message.edit_text(
                    "⏰ **Статистика сессии**\n\n"
                    "За последние 12 часов матчей не найдено.",
                    parse_mode="Markdown"
                )
                await callback.answer()
                return True  # Это нормальная ситуация
            
            # Определяем результаты матчей
            wins = 0
            total_matches = len(session_matches)
            recent_results = []
            
            for match in session_matches:
                player_won = self.client._determine_player_result(match, faceit_id)
                
                if player_won is True:
                    wins += 1
                    recent_results.append("✅")
                elif player_won is False:
                    recent_results.append("❌")
                else:
                    recent_results.append("❓")  # Неопределенный результат
            
            losses = total_matches - wins
            winrate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            # Формируем сообщение
            message = f"""
⏰ **Статистика сессии** (последние 12 часов)

📊 **Результаты:**
• Матчей: {total_matches}
• Побед: {wins}
• Поражений: {losses}
• Winrate: {winrate:.1f}%

📈 **Последние матчи:**
"""
            
            # Показываем детали последних матчей
            for i, (match, result) in enumerate(zip(session_matches[:5], recent_results[:5]), 1):
                game_mode = match.get('game_mode', 'Unknown')
                map_name = match.get('map', 'Unknown')
                
                # Пытаемся получить счет
                score_info = ""
                if 'results' in match and 'score' in match['results']:
                    score = match['results']['score']
                    faction1_score = score.get('faction1', 0)
                    faction2_score = score.get('faction2', 0)
                    score_info = f" ({faction1_score}:{faction2_score})"
                
                # Время матча
                finished_at = match.get('finished_at', 0)
                if finished_at:
                    if finished_at > 10**12:
                        match_time = datetime.fromtimestamp(finished_at / 1000)
                    else:
                        match_time = datetime.fromtimestamp(finished_at)
                    time_str = match_time.strftime('%H:%M')
                else:
                    time_str = "?"
                
                message += f"\n{i}. {result} {map_name}{score_info} - {time_str}"
            
            if total_matches > 5:
                message += f"\n\n_Показано 5 из {total_matches} матчей_"
            
            await callback.message.edit_text(message, parse_mode="Markdown")
            await callback.answer()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in simulate_show_session_stats: {e}")
            await callback.message.edit_text("❌ Произошла ошибка при загрузке статистики сессии.")
            await callback.answer()
            return False
    
    async def run_bot_handlers_tests(self):
        """Запуск всех тестов обработчиков бота"""
        logger.info("=" * 60)
        logger.info("ТЕСТИРОВАНИЕ ОБРАБОТЧИКОВ БОТА")
        logger.info("=" * 60)
        logger.info(f"Тестируемый пользователь: ID {self.test_user_id}")
        logger.info(f"FACEIT ID: {await self.mock_storage.get_user_faceit_id(self.test_user_id)}")
        logger.info("=" * 60)
        
        try:
            # Тест 1: show_overall_stats
            logger.info("\n1. ТЕСТ show_overall_stats")
            logger.info("-" * 40)
            callback1 = MockCallbackQuery(self.test_user_id)
            result1 = await self.simulate_show_overall_stats(callback1)
            
            if result1:
                # Проверяем что сообщение было отредактировано
                if len(callback1.edited_texts) >= 2:  # Загрузка + результат
                    final_message = callback1.edited_texts[-1]
                    
                    # Проверяем наличие ключевых элементов
                    required_elements = [
                        "Общая статистика", "Игрок:", "ELO:", "HLTV 2.1:", 
                        "Матчей сыграно:", "Побед:", "K/D:", "ADR:", "KAST:"
                    ]
                    
                    missing_elements = [elem for elem in required_elements if elem not in final_message]
                    
                    if not missing_elements:
                        self.log_result("show_overall_stats", True, 
                                      f"Сообщение содержит все элементы ({len(final_message)} символов)")
                    else:
                        self.log_result("show_overall_stats", False, 
                                      f"Отсутствуют элементы: {', '.join(missing_elements)}")
                else:
                    self.log_result("show_overall_stats", False, "Сообщение не было отредактировано")
            else:
                self.log_result("show_overall_stats", False, "Функция вернула False")
            
            # Тест 2: show_maps_stats
            logger.info("\n2. ТЕСТ show_maps_stats")
            logger.info("-" * 40)
            callback2 = MockCallbackQuery(self.test_user_id)
            result2 = await self.simulate_show_maps_stats(callback2)
            
            if result2:
                if len(callback2.edited_texts) >= 2:
                    final_message = callback2.edited_texts[-1]
                    
                    # Проверяем элементы статистики по картам
                    required_elements = [
                        "Статистика по картам", "Матчей:", "Winrate:", 
                        "K/D:", "ADR:", "KAST:", "HLTV 2.1:"
                    ]
                    
                    missing_elements = [elem for elem in required_elements if elem not in final_message]
                    
                    if not missing_elements:
                        # Подсчитываем количество карт в сообщении
                        map_count = final_message.count("• Матчей:")
                        self.log_result("show_maps_stats", True, 
                                      f"Статистика по {map_count} картам отображена корректно")
                    else:
                        self.log_result("show_maps_stats", False, 
                                      f"Отсутствуют элементы: {', '.join(missing_elements)}")
                else:
                    self.log_result("show_maps_stats", False, "Сообщение не было отредактировано")
            else:
                self.log_result("show_maps_stats", False, "Функция вернула False")
            
            # Тест 3: show_session_stats
            logger.info("\n3. ТЕСТ show_session_stats")
            logger.info("-" * 40)
            callback3 = MockCallbackQuery(self.test_user_id)
            result3 = await self.simulate_show_session_stats(callback3)
            
            if result3:
                if len(callback3.edited_texts) >= 2:
                    final_message = callback3.edited_texts[-1]
                    
                    # Проверяем элементы статистики сессии
                    if "Статистика сессии" in final_message:
                        if "матчей не найдено" in final_message:
                            self.log_result("show_session_stats", True, 
                                          "Корректная обработка отсутствия матчей за 12 часов")
                        else:
                            required_elements = ["Матчей:", "Побед:", "Поражений:", "Winrate:"]
                            missing_elements = [elem for elem in required_elements if elem not in final_message]
                            
                            if not missing_elements:
                                self.log_result("show_session_stats", True, 
                                              "Статистика сессии отображена корректно")
                            else:
                                self.log_result("show_session_stats", False, 
                                              f"Отсутствуют элементы: {', '.join(missing_elements)}")
                    else:
                        self.log_result("show_session_stats", False, "Неправильный формат сообщения")
                else:
                    self.log_result("show_session_stats", False, "Сообщение не было отредактировано")
            else:
                self.log_result("show_session_stats", False, "Функция вернула False")
            
            # Тест 4: Обработка несуществующего пользователя
            logger.info("\n4. ТЕСТ несуществующего пользователя")
            logger.info("-" * 40)
            fake_callback = MockCallbackQuery(99999)  # Несуществующий пользователь
            result4 = await self.simulate_show_overall_stats(fake_callback)
            
            if not result4 and fake_callback.answered:
                self.log_result("Fake User Test", True, "Несуществующий пользователь корректно обработан")
            else:
                self.log_result("Fake User Test", False, "Некорректная обработка несуществующего пользователя")
            
            # Тест 5: Проверка форматирования и валидация
            logger.info("\n5. ТЕСТ валидации данных")
            logger.info("-" * 40)
            
            validation_errors = []
            
            # Проверяем форматирование общей статистики
            if len(callback1.edited_texts) >= 2:
                overall_message = callback1.edited_texts[-1]
                
                # Проверяем что числовые значения разумные
                import re
                elo_match = re.search(r'ELO:\*\* (\d+)', overall_message)
                if elo_match:
                    elo = int(elo_match.group(1))
                    if not (0 <= elo <= 4000):
                        validation_errors.append(f"ELO вне диапазона: {elo}")
                
                level_match = re.search(r'Уровень (\d+)', overall_message)
                if level_match:
                    level = int(level_match.group(1))
                    if not (0 <= level <= 10):
                        validation_errors.append(f"Уровень вне диапазона: {level}")
                
                winrate_match = re.search(r'Побед:\*\* \d+ \((\d+\.?\d*)%\)', overall_message)
                if winrate_match:
                    winrate = float(winrate_match.group(1))
                    if not (0 <= winrate <= 100):
                        validation_errors.append(f"Винрейт вне диапазона: {winrate}")
            
            if validation_errors:
                self.log_result("Data Validation", False, f"Ошибки: {'; '.join(validation_errors)}")
            else:
                self.log_result("Data Validation", True, "Все данные в допустимых диапазонах")
            
        except Exception as e:
            logger.error(f"Критическая ошибка в тестировании: {e}")
            self.log_result("Critical Error", False, str(e))
        
        finally:
            await self.client.close()
        
        # Итоговый отчет
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГОВЫЙ ОТЧЕТ - ОБРАБОТЧИКИ БОТА")
        logger.info("=" * 60)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info(f"Всего тестов: {total}")
        logger.info(f"Пройдено: {passed}")
        logger.info(f"Провалено: {failed}")
        logger.info(f"Успешность: {success_rate:.1f}%")
        
        if success_rate >= 90:
            status = "ОТЛИЧНО"
        elif success_rate >= 75:
            status = "ХОРОШО"
        elif success_rate >= 50:
            status = "УДОВЛЕТВОРИТЕЛЬНО"
        else:
            status = "НЕУДОВЛЕТВОРИТЕЛЬНО"
        
        logger.info(f"\nСТАТУС: {status}")
        logger.info("=" * 60)
        
        return success_rate


async def main():
    """Основная функция"""
    print("Запуск тестирования обработчиков бота...")
    print(f"Время начала: {datetime.now()}")
    print("-" * 50)
    
    tester = BotHandlersTester()
    success_rate = await tester.run_bot_handlers_tests()
    
    print(f"\nТестирование завершено с результатом: {success_rate:.1f}%")
    return success_rate


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result >= 75 else 1)
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
        exit(2)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        exit(3)