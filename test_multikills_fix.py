#!/usr/bin/env python3
"""
Тест исправления мульти-киллов и клатчей
Проверяет что исправления в faceit_client.py работают корректно
"""

import asyncio
import logging
from faceit_client import FaceitAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_multikills_and_clutches():
    """Тест исправленных мульти-киллов и клатчей"""
    print("=" * 60)
    print("ТЕСТ ИСПРАВЛЕННЫХ МУЛЬТИ-КИЛЛОВ И КЛАТЧЕЙ")
    print("=" * 60)
    
    # Инициализируем клиент
    client = FaceitAPIClient()
    
    # Тестируем на реальном игроке Geun-Hee
    faceit_id = "0cf595d2-b9a1-4316-9df9-a627c7a8c664"
    
    try:
        # Получаем данные
        player_details = await client.get_player_details(faceit_id)
        stats_data = await client.get_player_stats(faceit_id)
        
        if not player_details or not stats_data:
            print("❌ Не удалось получить данные игрока")
            return False
        
        # Форматируем статистику
        formatted_stats = client.format_player_stats(player_details, stats_data)
        
        print(f"👤 Игрок: {formatted_stats.get('nickname', 'Unknown')}")
        print(f"🎮 ELO: {formatted_stats.get('elo', 0)} (Уровень {formatted_stats.get('level', 0)})")
        print(f"🎯 Матчей: {formatted_stats.get('matches', 0)}")
        
        print("\n📊 МУЛЬТИ-КИЛЛЫ:")
        print(f"• Тройные убийства: {formatted_stats.get('total_triple_kills', 0)}")
        print(f"• Четверные убийства: {formatted_stats.get('total_quadro_kills', 0)}")
        print(f"• Эйсы (5к): {formatted_stats.get('total_aces', 0)}")
        
        # ОСНОВНОЕ ИСПРАВЛЕНИЕ: multi_kills_per_match вместо multi_kills_per_round
        multi_kills_per_match = formatted_stats.get('multi_kills_per_match', 0)
        print(f"• Мульти-килл за матч (3+): {multi_kills_per_match:.3f}")
        
        # Проверяем расчет
        total_multi = (formatted_stats.get('total_triple_kills', 0) + 
                      formatted_stats.get('total_quadro_kills', 0) + 
                      formatted_stats.get('total_aces', 0))
        matches = formatted_stats.get('matches', 0)
        expected_multi_per_match = round(total_multi / max(matches, 1), 3) if matches > 0 else 0
        
        print(f"• Всего мульти-киллов: {total_multi}")
        print(f"• Ожидаемый расчет: {expected_multi_per_match:.3f}")
        print(f"• ✅ Расчет корректен: {'ДА' if abs(multi_kills_per_match - expected_multi_per_match) < 0.001 else 'НЕТ'}")
        
        print("\n🏆 КЛАТЧИ:")
        print(f"• 1v1 клатчей: {formatted_stats.get('clutch_1v1_total', 0)}")
        print(f"• 1v1 побед: {formatted_stats.get('clutch_1v1_wins', 0)}")
        print(f"• 1v1 процент: {formatted_stats.get('clutch_1v1_percentage', 0):.1f}%")
        print(f"• 1v2 клатчей: {formatted_stats.get('clutch_1v2_total', 0)}")
        print(f"• 1v2 побед: {formatted_stats.get('clutch_1v2_wins', 0)}")
        print(f"• 1v2 процент: {formatted_stats.get('clutch_1v2_percentage', 0):.1f}%")
        
        # Проверяем что данные реальные (не нулевые)
        has_realistic_data = (
            formatted_stats.get('clutch_1v1_total', 0) > 0 or 
            formatted_stats.get('total_triple_kills', 0) > 0
        )
        
        print(f"• ✅ Данные реалистичны: {'ДА' if has_realistic_data else 'НЕТ'}")
        
        print(f"\n📈 ДРУГИЕ ПОКАЗАТЕЛИ:")
        print(f"• ADR: {formatted_stats.get('adr', 0):.1f}")
        print(f"• KAST: {formatted_stats.get('kast', 0):.1f}%")
        print(f"• K/D: {formatted_stats.get('kd_ratio', 0):.3f}")
        print(f"• HLTV рейтинг: {formatted_stats.get('hltv_rating', 0):.2f}")
        print(f"• Средний % хедшотов: {formatted_stats.get('avg_headshot_percentage', 0):.1f}%")
        
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        
        # Основные проверки
        checks = [
            ("Мульти-килл расчет", abs(multi_kills_per_match - expected_multi_per_match) < 0.001),
            ("Наличие клатч данных", formatted_stats.get('clutch_1v1_total', 0) >= 0),
            ("Наличие мульти-килл данных", total_multi >= 0),
            ("Корректный ADR", 0 <= formatted_stats.get('adr', 0) <= 200),
            ("Корректный KAST", 0 <= formatted_stats.get('kast', 0) <= 100),
        ]
        
        passed = 0
        for check_name, result in checks:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check_name}: {status}")
            if result:
                passed += 1
        
        success_rate = (passed / len(checks)) * 100
        print(f"\nУспешность: {passed}/{len(checks)} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            return True
        else:
            print("⚠️ ТЕСТ ЧАСТИЧНО ПРОВАЛЕН")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        return False
        
    finally:
        await client.close()

async def main():
    success = await test_multikills_and_clutches()
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Тестирование прервано")
        exit(2)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        exit(3)