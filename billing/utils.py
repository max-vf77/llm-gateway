"""
Утилиты для управления API-ключами и тарифами в LLM Gateway
Независимый модуль без зависимостей от SQLAlchemy
"""

import os
import json
import secrets
import string
import re
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

# Путь к файлу с ключами
KEYS_FILE = Path(__file__).parent / "keys.json"


def load_keys() -> Dict[str, Dict[str, Any]]:
    """
    Загрузка API-ключей из файла keys.json
    
    Returns:
        dict: Словарь с API-ключами и их тарифами
    """
    try:
        if KEYS_FILE.exists():
            with open(KEYS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        else:
            # Создаем пустой файл если его нет
            save_keys({})
            return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка при загрузке ключей: {e}")
        return {}


def save_keys(data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Сохранение API-ключей в файл keys.json
    
    Args:
        data: Словарь с API-ключами и их тарифами
        
    Returns:
        bool: True если сохранение успешно
    """
    try:
        # Создаем директорию если её нет
        KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Ошибка при сохранении ключей: {e}")
        return False


def generate_api_key() -> str:
    """
    Генерация нового API-ключа в формате sk-xxxxx
    
    Returns:
        str: Новый API-ключ
    """
    # Генерируем случайную строку из букв и цифр
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(48))
    
    # Формируем ключ в стиле OpenAI
    api_key = f"sk-{random_part}"
    
    return api_key


def validate_key_format(key: str) -> bool:
    """
    Валидация формата API-ключа
    
    Args:
        key: API-ключ для проверки
        
    Returns:
        bool: True если формат корректный
    """
    if not isinstance(key, str):
        return False
    
    # Проверяем формат: sk- + 48 символов (буквы и цифры)
    pattern = r'^sk-[a-zA-Z0-9]{48}$'
    return bool(re.match(pattern, key))


def key_exists(key: str) -> bool:
    """
    Проверка существования API-ключа
    
    Args:
        key: API-ключ для проверки
        
    Returns:
        bool: True если ключ существует
    """
    keys = load_keys()
    return key in keys


def add_key(key: str, max_tokens: int, name: str = "", description: str = "") -> bool:
    """
    Добавление нового API-ключа
    
    Args:
        key: API-ключ
        max_tokens: Максимальное количество токенов
        name: Название тарифа
        description: Описание тарифа
        
    Returns:
        bool: True если ключ добавлен успешно
    """
    if not validate_key_format(key):
        print(f"Ошибка: Неверный формат ключа {key}")
        return False
    
    if key_exists(key):
        print(f"Ошибка: Ключ {key} уже существует")
        return False
    
    keys = load_keys()
    keys[key] = {
        "max_tokens": max_tokens,
        "name": name or "Custom",
        "description": description or "Пользовательский тариф",
        "created_at": datetime.now().isoformat()
    }
    
    return save_keys(keys)


def remove_key(key: str) -> bool:
    """
    Удаление API-ключа
    
    Args:
        key: API-ключ для удаления
        
    Returns:
        bool: True если ключ удален успешно
    """
    keys = load_keys()
    
    if key not in keys:
        print(f"Ошибка: Ключ {key} не найден")
        return False
    
    del keys[key]
    return save_keys(keys)


def update_key_limit(key: str, max_tokens: int) -> bool:
    """
    Обновление лимита токенов для API-ключа
    
    Args:
        key: API-ключ
        max_tokens: Новый лимит токенов
        
    Returns:
        bool: True если лимит обновлен успешно
    """
    keys = load_keys()
    
    if key not in keys:
        print(f"Ошибка: Ключ {key} не найден")
        return False
    
    keys[key]["max_tokens"] = max_tokens
    return save_keys(keys)


def get_key_info(key: str) -> Dict[str, Any]:
    """
    Получение информации об API-ключе
    
    Args:
        key: API-ключ
        
    Returns:
        dict: Информация о ключе или пустой словарь
    """
    keys = load_keys()
    return keys.get(key, {})


def list_all_keys() -> Dict[str, Dict[str, Any]]:
    """
    Получение списка всех API-ключей
    
    Returns:
        dict: Все API-ключи с их тарифами
    """
    return load_keys()


def get_keys_stats() -> Dict[str, Any]:
    """
    Получение статистики по API-ключам
    
    Returns:
        dict: Статистика ключей
    """
    keys = load_keys()
    
    if not keys:
        return {
            "total_keys": 0,
            "total_tokens": 0,
            "avg_tokens": 0,
            "min_tokens": 0,
            "max_tokens": 0
        }
    
    token_limits = [info["max_tokens"] for info in keys.values()]
    
    return {
        "total_keys": len(keys),
        "total_tokens": sum(token_limits),
        "avg_tokens": sum(token_limits) // len(token_limits),
        "min_tokens": min(token_limits),
        "max_tokens": max(token_limits)
    }


def backup_keys(backup_path: str = None) -> bool:
    """
    Создание резервной копии ключей
    
    Args:
        backup_path: Путь для резервной копии
        
    Returns:
        bool: True если резервная копия создана успешно
    """
    if backup_path is None:
        backup_path = str(KEYS_FILE.parent / "keys_backup.json")
    
    try:
        keys = load_keys()
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(keys, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return False


def restore_keys(backup_path: str) -> bool:
    """
    Восстановление ключей из резервной копии
    
    Args:
        backup_path: Путь к резервной копии
        
    Returns:
        bool: True если восстановление успешно
    """
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            print("Ошибка: Неверный формат резервной копии")
            return False
        
        return save_keys(data)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Ошибка при восстановлении ключей: {e}")
        return False