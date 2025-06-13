#!/usr/bin/env python3
"""
Скрипт для тестирования системы биллинга LLM Gateway
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from billing.models import init_database, get_db
from billing.tracker import log_usage, get_usage_stats, get_system_stats
from billing.limits import check_limits, set_api_key_limits, get_remaining_limits


def test_database_init():
    """Тест инициализации базы данных"""
    print("🔧 Тестирование инициализации базы данных...")
    try:
        init_database()
        print("✅ База данных успешно инициализирована")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        return False


def test_usage_logging():
    """Тест логирования использования"""
    print("\n📊 Тестирование логирования использования...")
    
    test_api_key = "sk-test-key-1"
    
    # Логирование нескольких записей
    test_cases = [
        (100, 1),
        (250, 1),
        (500, 1),
        (75, 1)
    ]
    
    for tokens, requests in test_cases:
        success = log_usage(test_api_key, tokens, requests)
        if success:
            print(f"✅ Залогировано: {tokens} токенов, {requests} запросов")
        else:
            print(f"❌ Ошибка логирования: {tokens} токенов")
            return False
    
    return True


def test_usage_stats():
    """Тест получения статистики"""
    print("\n📈 Тестирование получения статистики...")
    
    test_api_key = "sk-test-key-1"
    
    try:
        stats = get_usage_stats(test_api_key, days=7)
        print(f"✅ Статистика получена для ключа {test_api_key[:8]}...")
        print(f"   Всего токенов: {stats['total']['tokens_used']}")
        print(f"   Всего запросов: {stats['total']['requests_count']}")
        print(f"   Сегодня токенов: {stats['today']['tokens_used']}")
        return True
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return False


def test_limits_checking():
    """Тест проверки лимитов"""
    print("\n🚦 Тестирование проверки лимитов...")
    
    test_api_key = "sk-test-key-1"
    
    try:
        # Проверка с небольшим количеством токенов
        limits_info = check_limits(test_api_key, 100)
        print(f"✅ Лимиты проверены для {limits_info['api_key']}")
        print(f"   Дневной лимит: {limits_info['daily']['limit']}")
        print(f"   Использовано сегодня: {limits_info['daily']['used']}")
        print(f"   Месячный лимит: {limits_info['monthly']['limit']}")
        print(f"   Использовано в месяце: {limits_info['monthly']['used']}")
        
        # Проверка остатков лимитов
        remaining = get_remaining_limits(test_api_key)
        print(f"   Осталось сегодня: {remaining['daily']['remaining']}")
        print(f"   Осталось в месяце: {remaining['monthly']['remaining']}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки лимитов: {e}")
        return False


def test_custom_limits():
    """Тест установки индивидуальных лимитов"""
    print("\n⚙️ Тестирование индивидуальных лимитов...")
    
    test_api_key = "sk-test-key-2"
    
    try:
        # Установка индивидуальных лимитов
        success = set_api_key_limits(
            test_api_key,
            daily_limit=1000,
            monthly_limit=25000,
            is_active=True
        )
        
        if success:
            print(f"✅ Индивидуальные лимиты установлены для {test_api_key[:8]}...")
            
            # Проверка новых лимитов
            remaining = get_remaining_limits(test_api_key)
            print(f"   Дневной лимит: {remaining['daily']['limit']}")
            print(f"   Месячный лимит: {remaining['monthly']['limit']}")
            return True
        else:
            print("❌ Ошибка установки индивидуальных лимитов")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования индивидуальных лимитов: {e}")
        return False


def test_system_stats():
    """Тест системной статистики"""
    print("\n🌐 Тестирование системной статистики...")
    
    try:
        stats = get_system_stats(period_days=7)
        print(f"✅ Системная статистика получена")
        print(f"   Всего токенов: {stats['total']['tokens_used']}")
        print(f"   Всего запросов: {stats['total']['requests_count']}")
        print(f"   Уникальных пользователей: {stats['total']['unique_users']}")
        print(f"   Сегодня токенов: {stats['today']['tokens_used']}")
        return True
    except Exception as e:
        print(f"❌ Ошибка получения системной статистики: {e}")
        return False


def test_limit_exceeded():
    """Тест превышения лимитов"""
    print("\n🚨 Тестирование превышения лимитов...")
    
    test_api_key = "sk-test-key-3"
    
    try:
        # Установка очень низких лимитов для тестирования
        set_api_key_limits(test_api_key, daily_limit=10, monthly_limit=50)
        
        # Попытка использовать больше лимита
        try:
            check_limits(test_api_key, 20)  # Больше дневного лимита
            print("❌ Превышение лимита не было обнаружено")
            return False
        except Exception as e:
            error_detail = str(e.detail) if hasattr(e, 'detail') else str(e)
            if "Превышен дневной лимит" in error_detail:
                print("✅ Превышение дневного лимита корректно обнаружено")
                return True
            else:
                print(f"❌ Неожиданная ошибка: {error_detail}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка тестирования превышения лимитов: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов системы биллинга LLM Gateway\n")
    
    tests = [
        ("Инициализация БД", test_database_init),
        ("Логирование использования", test_usage_logging),
        ("Получение статистики", test_usage_stats),
        ("Проверка лимитов", test_limits_checking),
        ("Индивидуальные лимиты", test_custom_limits),
        ("Системная статистика", test_system_stats),
        ("Превышение лимитов", test_limit_exceeded),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
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