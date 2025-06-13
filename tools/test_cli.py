#!/usr/bin/env python3
"""
Простые тесты для CLI-утилиты управления API-ключами
"""

import os
import json
import tempfile
from pathlib import Path
from key_utils import (
    generate_api_key, validate_key_format, add_key, remove_key,
    update_key_limit, get_key_info, list_all_keys, get_keys_stats,
    backup_keys, restore_keys, KEYS_FILE
)


def test_generate_api_key():
    """Тест генерации API-ключа"""
    print("🧪 Тестирование генерации API-ключа...")
    
    key = generate_api_key()
    assert key.startswith('sk-'), f"Ключ должен начинаться с 'sk-': {key}"
    assert len(key) == 51, f"Длина ключа должна быть 51 символ: {len(key)}"
    assert validate_key_format(key), f"Неверный формат ключа: {key}"
    
    print(f"✅ Сгенерирован валидный ключ: {key[:12]}...{key[-4:]}")


def test_validate_key_format():
    """Тест валидации формата ключей"""
    print("🧪 Тестирование валидации формата ключей...")
    
    # Валидные ключи
    valid_keys = [
        "sk-" + "a" * 48,  # Стандартный ключ
        "sk-test-key-1",   # Тестовый ключ
        "sk-prod-key-123", # Продакшн ключ
        "sk-demo-basic"    # Демо ключ
    ]
    
    for key in valid_keys:
        assert validate_key_format(key), f"Ключ должен быть валидным: {key}"
    
    # Невалидные ключи
    invalid_keys = [
        "invalid-key",     # Не начинается с sk-
        "sk-",             # Слишком короткий
        "sk-test",         # Слишком короткий тестовый
        "",                # Пустая строка
        None               # None
    ]
    
    for key in invalid_keys:
        assert not validate_key_format(key), f"Ключ должен быть невалидным: {key}"
    
    print("✅ Валидация формата работает корректно")


def test_key_operations():
    """Тест операций с ключами"""
    print("🧪 Тестирование операций с ключами...")
    
    # Создаем временный файл для тестов
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    # Подменяем путь к файлу ключей
    original_keys_file = KEYS_FILE
    import key_utils
    key_utils.KEYS_FILE = Path(temp_file)
    
    try:
        # Тестируем добавление ключа
        test_key = "sk-test-cli-key"
        assert add_key(test_key, 50000, "CLI Test", "Тестовый ключ для CLI")
        
        # Проверяем, что ключ добавился
        key_info = get_key_info(test_key)
        assert key_info['max_tokens'] == 50000
        assert key_info['name'] == "CLI Test"
        
        # Тестируем обновление лимита
        assert update_key_limit(test_key, 75000)
        updated_info = get_key_info(test_key)
        assert updated_info['max_tokens'] == 75000
        
        # Тестируем статистику
        stats = get_keys_stats()
        assert stats['total_keys'] == 1
        assert stats['total_tokens'] == 75000
        
        # Тестируем удаление ключа
        assert remove_key(test_key)
        assert get_key_info(test_key) == {}
        
        print("✅ Операции с ключами работают корректно")
        
    finally:
        # Восстанавливаем оригинальный путь
        key_utils.KEYS_FILE = original_keys_file
        # Удаляем временный файл
        os.unlink(temp_file)


def test_backup_restore():
    """Тест резервного копирования и восстановления"""
    print("🧪 Тестирование резервного копирования...")
    
    # Создаем временные файлы
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_keys_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_backup_file = f.name
    
    # Подменяем путь к файлу ключей
    original_keys_file = KEYS_FILE
    import key_utils
    key_utils.KEYS_FILE = Path(temp_keys_file)
    
    try:
        # Создаем тестовые данные
        test_data = {
            "sk-test-backup-1": {
                "max_tokens": 10000,
                "name": "Backup Test 1",
                "description": "Тест резервного копирования"
            },
            "sk-test-backup-2": {
                "max_tokens": 20000,
                "name": "Backup Test 2",
                "description": "Тест резервного копирования 2"
            }
        }
        
        # Сохраняем тестовые данные
        with open(temp_keys_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        # Тестируем резервное копирование
        assert backup_keys(temp_backup_file)
        
        # Проверяем, что резервная копия создалась
        assert os.path.exists(temp_backup_file)
        
        with open(temp_backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert backup_data == test_data
        
        # Очищаем основной файл
        with open(temp_keys_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        
        # Тестируем восстановление
        assert restore_keys(temp_backup_file)
        
        # Проверяем, что данные восстановились
        restored_keys = list_all_keys()
        assert len(restored_keys) == 2
        assert "sk-test-backup-1" in restored_keys
        assert "sk-test-backup-2" in restored_keys
        
        print("✅ Резервное копирование и восстановление работают корректно")
        
    finally:
        # Восстанавливаем оригинальный путь
        key_utils.KEYS_FILE = original_keys_file
        # Удаляем временные файлы
        os.unlink(temp_keys_file)
        os.unlink(temp_backup_file)


def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов CLI-утилиты...")
    print("=" * 50)
    
    try:
        test_generate_api_key()
        print()
        
        test_validate_key_format()
        print()
        
        test_key_operations()
        print()
        
        test_backup_restore()
        print()
        
        print("=" * 50)
        print("🎉 Все тесты прошли успешно!")
        
    except AssertionError as e:
        print(f"❌ Тест провален: {e}")
        return 1
    except Exception as e:
        print(f"❌ Ошибка при выполнении тестов: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())