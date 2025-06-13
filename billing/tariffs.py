"""
Модуль тарификации для LLM Gateway
Определяет лимиты токенов для различных API ключей
"""

import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Тарифы по API ключам
# Формат: {api_key: {"max_tokens": int, "name": str, "description": str}}
TARIFFS: Dict[str, Dict[str, any]] = {
    # Тестовые ключи с ограниченными лимитами
    "sk-test-key-1": {
        "max_tokens": 10000,
        "name": "Test Basic",
        "description": "Базовый тестовый тариф"
    },
    "sk-test-key-2": {
        "max_tokens": 5000,
        "name": "Test Limited",
        "description": "Ограниченный тестовый тариф"
    },
    "sk-test-key-3": {
        "max_tokens": 1000,
        "name": "Test Minimal",
        "description": "Минимальный тестовый тариф"
    },
    
    # Продакшн ключи с большими лимитами
    "sk-prod-key-123": {
        "max_tokens": 1000000,
        "name": "Production Premium",
        "description": "Премиум тариф для продакшн использования"
    },
    "sk-enterprise-456": {
        "max_tokens": 5000000,
        "name": "Enterprise",
        "description": "Корпоративный тариф с максимальными лимитами"
    },
    
    # Демо ключи
    "sk-demo-789": {
        "max_tokens": 500,
        "name": "Demo",
        "description": "Демонстрационный тариф с минимальными лимитами"
    }
}

# Тариф по умолчанию для неизвестных ключей
DEFAULT_TARIFF = {
    "max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "50000")),
    "name": "Default",
    "description": "Тариф по умолчанию"
}


def get_tariff(api_key: str) -> Dict[str, any]:
    """
    Получение тарифа для API ключа
    
    Args:
        api_key: API ключ
        
    Returns:
        dict: Информация о тарифе
    """
    tariff = TARIFFS.get(api_key, DEFAULT_TARIFF.copy())
    
    # Добавляем API ключ в ответ (маскированный)
    tariff["api_key"] = api_key[:8] + "..." if len(api_key) > 8 else api_key
    
    logger.debug(f"Retrieved tariff for {api_key[:8]}...: {tariff['name']} ({tariff['max_tokens']} tokens)")
    return tariff


def get_max_tokens(api_key: str) -> int:
    """
    Получение максимального количества токенов для API ключа
    
    Args:
        api_key: API ключ
        
    Returns:
        int: Максимальное количество токенов
    """
    tariff = get_tariff(api_key)
    return tariff["max_tokens"]


def set_tariff(api_key: str, max_tokens: int, name: str = "Custom", description: str = "Custom tariff") -> bool:
    """
    Установка тарифа для API ключа
    
    Args:
        api_key: API ключ
        max_tokens: Максимальное количество токенов
        name: Название тарифа
        description: Описание тарифа
        
    Returns:
        bool: True если тариф установлен успешно
    """
    try:
        TARIFFS[api_key] = {
            "max_tokens": max_tokens,
            "name": name,
            "description": description
        }
        logger.info(f"Set tariff for {api_key[:8]}...: {name} ({max_tokens} tokens)")
        return True
    except Exception as e:
        logger.error(f"Error setting tariff for {api_key[:8]}...: {e}")
        return False


def remove_tariff(api_key: str) -> bool:
    """
    Удаление тарифа для API ключа (будет использоваться тариф по умолчанию)
    
    Args:
        api_key: API ключ
        
    Returns:
        bool: True если тариф удален успешно
    """
    try:
        if api_key in TARIFFS:
            del TARIFFS[api_key]
            logger.info(f"Removed tariff for {api_key[:8]}..., will use default")
            return True
        else:
            logger.warning(f"No tariff found for {api_key[:8]}... to remove")
            return False
    except Exception as e:
        logger.error(f"Error removing tariff for {api_key[:8]}...: {e}")
        return False


def get_all_tariffs() -> Dict[str, Dict[str, any]]:
    """
    Получение всех тарифов
    
    Returns:
        dict: Все тарифы с маскированными API ключами
    """
    masked_tariffs = {}
    
    for api_key, tariff in TARIFFS.items():
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
        masked_tariffs[masked_key] = tariff.copy()
        masked_tariffs[masked_key]["api_key"] = masked_key
    
    return masked_tariffs


def get_tariff_stats() -> Dict[str, any]:
    """
    Получение статистики по тарифам
    
    Returns:
        dict: Статистика тарифов
    """
    stats = {
        "total_tariffs": len(TARIFFS),
        "default_max_tokens": DEFAULT_TARIFF["max_tokens"],
        "tariff_distribution": {},
        "total_max_tokens": 0
    }
    
    # Группировка по названиям тарифов
    for tariff in TARIFFS.values():
        name = tariff["name"]
        if name not in stats["tariff_distribution"]:
            stats["tariff_distribution"][name] = {
                "count": 0,
                "total_tokens": 0,
                "avg_tokens": 0
            }
        
        stats["tariff_distribution"][name]["count"] += 1
        stats["tariff_distribution"][name]["total_tokens"] += tariff["max_tokens"]
        stats["total_max_tokens"] += tariff["max_tokens"]
    
    # Вычисление средних значений
    for name, data in stats["tariff_distribution"].items():
        if data["count"] > 0:
            data["avg_tokens"] = data["total_tokens"] // data["count"]
    
    return stats


def validate_api_key_tariff(api_key: str) -> Dict[str, any]:
    """
    Валидация и получение информации о тарифе для API ключа
    
    Args:
        api_key: API ключ
        
    Returns:
        dict: Результат валидации и информация о тарифе
    """
    try:
        tariff = get_tariff(api_key)
        
        validation_result = {
            "valid": True,
            "api_key": api_key[:8] + "...",
            "tariff": tariff,
            "has_custom_tariff": api_key in TARIFFS,
            "using_default": api_key not in TARIFFS
        }
        
        # Проверка корректности лимитов
        if tariff["max_tokens"] <= 0:
            validation_result["valid"] = False
            validation_result["error"] = "Invalid max_tokens value"
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating tariff for {api_key[:8]}...: {e}")
        return {
            "valid": False,
            "api_key": api_key[:8] + "...",
            "error": str(e)
        }


# Функции для работы с тарифными планами
def create_tariff_plan(plan_name: str, max_tokens: int, description: str = "") -> str:
    """
    Создание шаблона тарифного плана
    
    Args:
        plan_name: Название плана
        max_tokens: Максимальное количество токенов
        description: Описание плана
        
    Returns:
        str: ID созданного плана
    """
    plan_id = f"plan_{plan_name.lower().replace(' ', '_')}"
    
    # Сохранение плана в переменных окружения или конфигурации
    # В реальном проекте это может быть база данных
    logger.info(f"Created tariff plan: {plan_name} ({max_tokens} tokens)")
    
    return plan_id


def apply_tariff_plan(api_key: str, plan_name: str) -> bool:
    """
    Применение тарифного плана к API ключу
    
    Args:
        api_key: API ключ
        plan_name: Название плана
        
    Returns:
        bool: True если план применен успешно
    """
    # Предопределенные планы
    plans = {
        "basic": {"max_tokens": 10000, "description": "Базовый план"},
        "premium": {"max_tokens": 100000, "description": "Премиум план"},
        "enterprise": {"max_tokens": 1000000, "description": "Корпоративный план"},
        "unlimited": {"max_tokens": 10000000, "description": "Безлимитный план"}
    }
    
    if plan_name.lower() not in plans:
        logger.error(f"Unknown tariff plan: {plan_name}")
        return False
    
    plan = plans[plan_name.lower()]
    return set_tariff(
        api_key=api_key,
        max_tokens=plan["max_tokens"],
        name=plan_name.title(),
        description=plan["description"]
    )