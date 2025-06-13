"""
Модуль проверки лимитов использования API-ключей
"""

from datetime import date, datetime
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from fastapi import HTTPException, status
import logging

from .models import ApiKeyUsage, ApiKeyLimits, get_db, get_global_limits

# Настройка логирования
logger = logging.getLogger(__name__)


class LimitExceededException(HTTPException):
    """
    Исключение для случаев превышения лимитов
    """
    def __init__(self, detail: str, limit_type: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "3600"}  # Повторить через час
        )
        self.limit_type = limit_type


def get_api_key_limits(api_key: str, db: Session) -> Tuple[int, int]:
    """
    Получение лимитов для конкретного API-ключа
    
    Args:
        api_key: API ключ
        db: Сессия базы данных
        
    Returns:
        tuple: (daily_limit, monthly_limit)
    """
    # Попытка получить индивидуальные лимиты для ключа
    key_limits = db.query(ApiKeyLimits).filter(
        ApiKeyLimits.api_key == api_key,
        ApiKeyLimits.is_active == 1
    ).first()
    
    # Получение глобальных лимитов
    global_daily, global_monthly = get_global_limits()
    
    if key_limits:
        daily_limit = key_limits.daily_limit if key_limits.daily_limit is not None else global_daily
        monthly_limit = key_limits.monthly_limit if key_limits.monthly_limit is not None else global_monthly
    else:
        daily_limit = global_daily
        monthly_limit = global_monthly
    
    return daily_limit, monthly_limit


def get_current_usage(api_key: str, db: Session) -> Tuple[int, int]:
    """
    Получение текущего использования токенов за день и месяц
    
    Args:
        api_key: API ключ
        db: Сессия базы данных
        
    Returns:
        tuple: (daily_usage, monthly_usage)
    """
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Использование за сегодня
    daily_usage = db.query(func.sum(ApiKeyUsage.tokens_used)).filter(
        ApiKeyUsage.api_key == api_key,
        ApiKeyUsage.date == today
    ).scalar() or 0
    
    # Использование за текущий месяц
    monthly_usage = db.query(func.sum(ApiKeyUsage.tokens_used)).filter(
        ApiKeyUsage.api_key == api_key,
        extract('month', ApiKeyUsage.date) == current_month,
        extract('year', ApiKeyUsage.date) == current_year
    ).scalar() or 0
    
    return int(daily_usage), int(monthly_usage)


def check_limits(api_key: str, token_count: int = 0) -> Dict[str, any]:
    """
    Проверка лимитов использования для API-ключа
    
    Args:
        api_key: API ключ для проверки
        token_count: Количество токенов, которые планируется использовать
        
    Returns:
        dict: Информация о лимитах и использовании
        
    Raises:
        LimitExceededException: При превышении лимитов
    """
    db = get_db()
    try:
        # Получение лимитов для ключа
        daily_limit, monthly_limit = get_api_key_limits(api_key, db)
        
        # Получение текущего использования
        daily_usage, monthly_usage = get_current_usage(api_key, db)
        
        # Проверка дневного лимита
        if daily_usage + token_count > daily_limit:
            logger.warning(f"Daily limit exceeded for API key {api_key[:8]}...")
            raise LimitExceededException(
                detail=f"Превышен дневной лимит токенов. Использовано: {daily_usage}, лимит: {daily_limit}",
                limit_type="daily"
            )
        
        # Проверка месячного лимита
        if monthly_usage + token_count > monthly_limit:
            logger.warning(f"Monthly limit exceeded for API key {api_key[:8]}...")
            raise LimitExceededException(
                detail=f"Превышен месячный лимит токенов. Использовано: {monthly_usage}, лимит: {monthly_limit}",
                limit_type="monthly"
            )
        
        # Возврат информации о лимитах
        result = {
            "api_key": api_key[:8] + "...",
            "daily": {
                "used": daily_usage,
                "limit": daily_limit,
                "remaining": daily_limit - daily_usage,
                "will_use": token_count,
                "after_request": daily_usage + token_count
            },
            "monthly": {
                "used": monthly_usage,
                "limit": monthly_limit,
                "remaining": monthly_limit - monthly_usage,
                "will_use": token_count,
                "after_request": monthly_usage + token_count
            },
            "status": "ok"
        }
        
        logger.info(f"Limits check passed for API key {api_key[:8]}...")
        return result
        
    except LimitExceededException:
        raise
    except Exception as e:
        logger.error(f"Error checking limits for API key {api_key[:8]}...: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при проверке лимитов"
        )
    finally:
        db.close()


def get_remaining_limits(api_key: str) -> Dict[str, any]:
    """
    Получение информации об остатках лимитов для API-ключа
    
    Args:
        api_key: API ключ
        
    Returns:
        dict: Информация об остатках лимитов
    """
    db = get_db()
    try:
        daily_limit, monthly_limit = get_api_key_limits(api_key, db)
        daily_usage, monthly_usage = get_current_usage(api_key, db)
        
        return {
            "api_key": api_key[:8] + "...",
            "daily": {
                "limit": daily_limit,
                "used": daily_usage,
                "remaining": daily_limit - daily_usage,
                "percentage_used": round((daily_usage / daily_limit) * 100, 2) if daily_limit > 0 else 0
            },
            "monthly": {
                "limit": monthly_limit,
                "used": monthly_usage,
                "remaining": monthly_limit - monthly_usage,
                "percentage_used": round((monthly_usage / monthly_limit) * 100, 2) if monthly_limit > 0 else 0
            }
        }
    finally:
        db.close()


def is_api_key_active(api_key: str) -> bool:
    """
    Проверка активности API-ключа
    
    Args:
        api_key: API ключ для проверки
        
    Returns:
        bool: True если ключ активен, False если заблокирован
    """
    db = get_db()
    try:
        key_limits = db.query(ApiKeyLimits).filter(
            ApiKeyLimits.api_key == api_key
        ).first()
        
        # Если записи нет, считаем ключ активным (используются глобальные настройки)
        if not key_limits:
            return True
            
        return bool(key_limits.is_active)
    finally:
        db.close()


def set_api_key_limits(api_key: str, daily_limit: Optional[int] = None, 
                      monthly_limit: Optional[int] = None, is_active: bool = True) -> bool:
    """
    Установка индивидуальных лимитов для API-ключа
    
    Args:
        api_key: API ключ
        daily_limit: Дневной лимит (None для использования глобального)
        monthly_limit: Месячный лимит (None для использования глобального)
        is_active: Активность ключа
        
    Returns:
        bool: True если операция успешна
    """
    db = get_db()
    try:
        # Поиск существующей записи
        existing = db.query(ApiKeyLimits).filter(
            ApiKeyLimits.api_key == api_key
        ).first()
        
        if existing:
            # Обновление существующей записи
            existing.daily_limit = daily_limit
            existing.monthly_limit = monthly_limit
            existing.is_active = 1 if is_active else 0
            existing.updated_at = datetime.utcnow()
        else:
            # Создание новой записи
            new_limits = ApiKeyLimits(
                api_key=api_key,
                daily_limit=daily_limit,
                monthly_limit=monthly_limit,
                is_active=1 if is_active else 0
            )
            db.add(new_limits)
        
        db.commit()
        logger.info(f"Limits updated for API key {api_key[:8]}...")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting limits for API key {api_key[:8]}...: {str(e)}")
        return False
    finally:
        db.close()