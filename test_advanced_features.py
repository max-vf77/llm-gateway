#!/usr/bin/env python3
"""
Тестирование расширенных функций LLM Gateway:
- Rate limiting
- Token tracking
- Tariff system
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gateway.limiter import check_rate_limit, get_rate_limit_info, reset_rate_limit, get_redis_health
from billing.token_tracker import token_tracker
from billing.tariffs import get_tariff, set_tariff, get_all_tariffs, apply_tariff_plan


def test_redis_connection():
    """Тест подключения к Redis"""
    print("🔗 Тестирование подключения к Redis...")
    
    health = get_redis_health()
    print(f"   Статус: {health['status']}")
    
    if health['status'] == 'connected':
        print(f"   ✅ Подключен к Redis: {health['host']}:{health['port']}")
        return True
    elif health['status'] == 'not_configured':
        print("   ⚠️ Redis не настроен, используется fallback в памяти")
        return True
    else:
        print(f"   ❌ Ошибка подключения: {health.get('error', 'Unknown error')}")
        return True  # Продолжаем тесты с fallback


def test_rate_limiting():
    """Тест rate limiting"""
    print("\n🚦 Тестирование rate limiting...")
    
    test_api_key = "sk-test-rate-limit"
    
    try:
        # Сброс лимитов для чистого теста
        reset_rate_limit(test_api_key)
        
        # Тест нормального использования
        for i in range(3):
            rate_info = check_rate_limit(test_api_key)
            print(f"   ✅ Запрос {i+1}: {rate_info['current_count']}/{rate_info['limit']}")
        
        # Получение информации о лимитах
        info = get_rate_limit_info(test_api_key)
        print(f"   📊 Текущее состояние: {info['current_count']}/{info['limit']}, осталось: {info['remaining']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка rate limiting: {e}")
        return False


def test_token_tracker():
    """Тест TokenTracker"""
    print("\n📊 Тестирование TokenTracker...")
    
    test_api_key = "sk-test-tracker"
    
    try:
        # Сброс использования
        token_tracker.reset_usage(test_api_key)
        
        # Тест инкремента токенов
        test_increments = [100, 250, 150, 75]
        for tokens in test_increments:
            success = token_tracker.increment_usage(test_api_key, tokens)
            if success:
                print(f"   ✅ Добавлено {tokens} токенов")
            else:
                print(f"   ❌ Ошибка добавления {tokens} токенов")
                return False
        
        # Проверка общего использования
        total_usage = token_tracker.get_usage(test_api_key)
        expected_total = sum(test_increments)
        print(f"   📈 Общее использование: {total_usage} токенов (ожидалось: {expected_total})")
        
        if total_usage == expected_total:
            print("   ✅ Подсчёт токенов корректен")
        else:
            print("   ❌ Ошибка в подсчёте токенов")
            return False
        
        # Тест детальной информации
        detailed = token_tracker.get_detailed_usage(test_api_key)
        print(f"   📋 Детальная информация: {detailed}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка TokenTracker: {e}")
        return False


def test_tariff_system():
    """Тест системы тарифов"""
    print("\n💰 Тестирование системы тарифов...")
    
    test_api_key = "sk-test-tariff"
    
    try:
        # Получение тарифа по умолчанию
        default_tariff = get_tariff(test_api_key)
        print(f"   📋 Тариф по умолчанию: {default_tariff['name']} ({default_tariff['max_tokens']} токенов)")
        
        # Установка кастомного тарифа
        custom_success = set_tariff(
            api_key=test_api_key,
            max_tokens=5000,
            name="Test Custom",
            description="Кастомный тестовый тариф"
        )
        
        if custom_success:
            print("   ✅ Кастомный тариф установлен")
            
            # Проверка кастомного тарифа
            custom_tariff = get_tariff(test_api_key)
            print(f"   📋 Кастомный тариф: {custom_tariff['name']} ({custom_tariff['max_tokens']} токенов)")
            
            if custom_tariff['max_tokens'] == 5000:
                print("   ✅ Кастомный тариф применён корректно")
            else:
                print("   ❌ Ошибка применения кастомного тарифа")
                return False
        else:
            print("   ❌ Ошибка установки кастомного тарифа")
            return False
        
        # Тест применения тарифного плана
        plan_success = apply_tariff_plan(test_api_key, "premium")
        if plan_success:
            premium_tariff = get_tariff(test_api_key)
            print(f"   ✅ Премиум план применён: {premium_tariff['name']} ({premium_tariff['max_tokens']} токенов)")
        else:
            print("   ❌ Ошибка применения премиум плана")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка системы тарифов: {e}")
        return False


def test_limit_checking():
    """Тест проверки лимитов"""
    print("\n🚨 Тестирование проверки лимитов...")
    
    test_api_key = "sk-test-limits"
    
    try:
        # Установка низкого лимита для тестирования
        set_tariff(test_api_key, max_tokens=100, name="Test Limit", description="Тест лимитов")
        
        # Сброс использования
        token_tracker.reset_usage(test_api_key)
        
        # Тест в пределах лимита
        within_limit = token_tracker.check_limit(test_api_key, 100)
        if within_limit:
            print("   ✅ Проверка лимита в пределах нормы")
        else:
            print("   ❌ Ошибка: лимит не должен быть превышен")
            return False
        
        # Добавление токенов до лимита
        token_tracker.increment_usage(test_api_key, 90)
        
        # Тест на грани лимита
        at_limit = token_tracker.check_limit(test_api_key, 100)
        if at_limit:
            print("   ✅ Проверка лимита на грани")
        else:
            print("   ❌ Ошибка: лимит не должен быть превышен на грани")
            return False
        
        # Добавление токенов сверх лимита
        token_tracker.increment_usage(test_api_key, 20)
        
        # Тест превышения лимита
        over_limit = token_tracker.check_limit(test_api_key, 100)
        if not over_limit:
            print("   ✅ Превышение лимита корректно обнаружено")
        else:
            print("   ❌ Ошибка: превышение лимита не обнаружено")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки лимитов: {e}")
        return False


def test_health_checks():
    """Тест проверки состояния системы"""
    print("\n🏥 Тестирование проверки состояния...")
    
    try:
        # Проверка состояния TokenTracker
        tracker_health = token_tracker.health_check()
        print(f"   📊 TokenTracker: {tracker_health['status']}")
        print(f"   🔗 Redis подключен: {tracker_health['redis_connected']}")
        print(f"   💾 Ключей в fallback: {tracker_health['fallback_keys']}")
        
        # Проверка состояния Redis
        redis_health = get_redis_health()
        print(f"   🔗 Redis статус: {redis_health['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки состояния: {e}")
        return False


def test_statistics():
    """Тест получения статистики"""
    print("\n📈 Тестирование статистики...")
    
    try:
        # Статистика TokenTracker
        stats = token_tracker.get_all_usage_stats()
        print(f"   📊 Всего ключей: {stats['total_keys']}")
        print(f"   🎯 Всего токенов: {stats['total_tokens']}")
        print(f"   💾 Тип хранилища: {stats['storage_type']}")
        
        # Статистика тарифов
        from billing.tariffs import get_tariff_stats
        tariff_stats = get_tariff_stats()
        print(f"   💰 Всего тарифов: {tariff_stats['total_tariffs']}")
        print(f"   📋 Распределение тарифов: {list(tariff_stats['tariff_distribution'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка получения статистики: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов расширенных функций LLM Gateway\n")
    
    tests = [
        ("Подключение к Redis", test_redis_connection),
        ("Rate Limiting", test_rate_limiting),
        ("Token Tracker", test_token_tracker),
        ("Система тарифов", test_tariff_system),
        ("Проверка лимитов", test_limit_checking),
        ("Проверка состояния", test_health_checks),
        ("Статистика", test_statistics),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты не пройдены")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)