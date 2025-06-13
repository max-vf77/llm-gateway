"""
Модуль учёта использования токенов и запросов для API-ключей
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
import logging

from .models import ApiKeyUsage, get_db

# Настройка логирования
logger = logging.getLogger(__name__)


def log_usage(api_key: str, token_count: int, request_count: int = 1) -> bool:
    """
    Логирование использования токенов для API-ключа
    
    Args:
        api_key: API ключ
        token_count: Количество использованных токенов
        request_count: Количество запросов (по умолчанию 1)
        
    Returns:
        bool: True если логирование успешно
    """
    if token_count < 0:
        logger.warning(f"Negative token count {token_count} for API key {api_key[:8]}...")
        return False
        
    db = get_db()
    try:
        today = date.today()
        
        # Поиск существующей записи за сегодня
        existing_usage = db.query(ApiKeyUsage).filter(
            ApiKeyUsage.api_key == api_key,
            ApiKeyUsage.date == today
        ).first()
        
        if existing_usage:
            # Обновление существующей записи
            existing_usage.tokens_used += token_count
            existing_usage.requests_count += request_count
            existing_usage.updated_at = datetime.utcnow()
            logger.debug(f"Updated usage for API key {api_key[:8]}...: +{token_count} tokens")
        else:
            # Создание новой записи
            new_usage = ApiKeyUsage(
                api_key=api_key,
                date=today,
                tokens_used=token_count,
                requests_count=request_count
            )
            db.add(new_usage)
            logger.debug(f"Created new usage record for API key {api_key[:8]}...: {token_count} tokens")
        
        db.commit()
        logger.info(f"Logged {token_count} tokens for API key {api_key[:8]}...")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging usage for API key {api_key[:8]}...: {str(e)}")
        return False
    finally:
        db.close()


def get_usage_stats(api_key: str, days: int = 30) -> Dict[str, any]:
    """
    Получение статистики использования для API-ключа
    
    Args:
        api_key: API ключ
        days: Количество дней для анализа (по умолчанию 30)
        
    Returns:
        dict: Статистика использования
    """
    db = get_db()
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Получение записей за период
        usage_records = db.query(ApiKeyUsage).filter(
            ApiKeyUsage.api_key == api_key,
            ApiKeyUsage.date >= start_date,
            ApiKeyUsage.date <= end_date
        ).order_by(desc(ApiKeyUsage.date)).all()
        
        # Подсчёт общей статистики
        total_tokens = sum(record.tokens_used for record in usage_records)
        total_requests = sum(record.requests_count for record in usage_records)
        
        # Статистика по дням
        daily_stats = []
        for record in usage_records:
            daily_stats.append({
                "date": record.date.isoformat(),
                "tokens_used": record.tokens_used,
                "requests_count": record.requests_count,
                "avg_tokens_per_request": round(record.tokens_used / record.requests_count, 2) if record.requests_count > 0 else 0
            })
        
        # Статистика за сегодня
        today_record = next((r for r in usage_records if r.date == date.today()), None)
        today_tokens = today_record.tokens_used if today_record else 0
        today_requests = today_record.requests_count if today_record else 0
        
        # Статистика за текущий месяц
        current_month = date.today().month
        current_year = date.today().year
        
        monthly_tokens = db.query(func.sum(ApiKeyUsage.tokens_used)).filter(
            ApiKeyUsage.api_key == api_key,
            extract('month', ApiKeyUsage.date) == current_month,
            extract('year', ApiKeyUsage.date) == current_year
        ).scalar() or 0
        
        monthly_requests = db.query(func.sum(ApiKeyUsage.requests_count)).filter(
            ApiKeyUsage.api_key == api_key,
            extract('month', ApiKeyUsage.date) == current_month,
            extract('year', ApiKeyUsage.date) == current_year
        ).scalar() or 0
        
        return {
            "api_key": api_key[:8] + "...",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total": {
                "tokens_used": total_tokens,
                "requests_count": total_requests,
                "avg_tokens_per_request": round(total_tokens / total_requests, 2) if total_requests > 0 else 0
            },
            "today": {
                "tokens_used": today_tokens,
                "requests_count": today_requests,
                "avg_tokens_per_request": round(today_tokens / today_requests, 2) if today_requests > 0 else 0
            },
            "current_month": {
                "tokens_used": int(monthly_tokens),
                "requests_count": int(monthly_requests),
                "avg_tokens_per_request": round(monthly_tokens / monthly_requests, 2) if monthly_requests > 0 else 0
            },
            "daily_breakdown": daily_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats for API key {api_key[:8]}...: {str(e)}")
        return {
            "error": "Ошибка при получении статистики",
            "api_key": api_key[:8] + "..."
        }
    finally:
        db.close()


def get_top_users(limit: int = 10, period_days: int = 30) -> List[Dict[str, any]]:
    """
    Получение топа пользователей по использованию токенов
    
    Args:
        limit: Количество пользователей в топе
        period_days: Период для анализа в днях
        
    Returns:
        list: Список пользователей с их статистикой
    """
    db = get_db()
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days-1)
        
        # Группировка по API ключам и подсчёт суммарного использования
        top_users = db.query(
            ApiKeyUsage.api_key,
            func.sum(ApiKeyUsage.tokens_used).label('total_tokens'),
            func.sum(ApiKeyUsage.requests_count).label('total_requests'),
            func.count(ApiKeyUsage.id).label('active_days')
        ).filter(
            ApiKeyUsage.date >= start_date,
            ApiKeyUsage.date <= end_date
        ).group_by(
            ApiKeyUsage.api_key
        ).order_by(
            desc('total_tokens')
        ).limit(limit).all()
        
        result = []
        for user in top_users:
            avg_tokens_per_request = round(user.total_tokens / user.total_requests, 2) if user.total_requests > 0 else 0
            avg_tokens_per_day = round(user.total_tokens / user.active_days, 2) if user.active_days > 0 else 0
            
            result.append({
                "api_key": user.api_key[:8] + "...",
                "total_tokens": user.total_tokens,
                "total_requests": user.total_requests,
                "active_days": user.active_days,
                "avg_tokens_per_request": avg_tokens_per_request,
                "avg_tokens_per_day": avg_tokens_per_day
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting top users: {str(e)}")
        return []
    finally:
        db.close()


def get_system_stats(period_days: int = 30) -> Dict[str, any]:
    """
    Получение общей статистики системы
    
    Args:
        period_days: Период для анализа в днях
        
    Returns:
        dict: Общая статистика системы
    """
    db = get_db()
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days-1)
        
        # Общая статистика за период
        total_stats = db.query(
            func.sum(ApiKeyUsage.tokens_used).label('total_tokens'),
            func.sum(ApiKeyUsage.requests_count).label('total_requests'),
            func.count(func.distinct(ApiKeyUsage.api_key)).label('unique_users'),
            func.count(ApiKeyUsage.id).label('total_records')
        ).filter(
            ApiKeyUsage.date >= start_date,
            ApiKeyUsage.date <= end_date
        ).first()
        
        # Статистика за сегодня
        today_stats = db.query(
            func.sum(ApiKeyUsage.tokens_used).label('today_tokens'),
            func.sum(ApiKeyUsage.requests_count).label('today_requests'),
            func.count(func.distinct(ApiKeyUsage.api_key)).label('today_users')
        ).filter(
            ApiKeyUsage.date == date.today()
        ).first()
        
        # Статистика по дням
        daily_stats = db.query(
            ApiKeyUsage.date,
            func.sum(ApiKeyUsage.tokens_used).label('tokens'),
            func.sum(ApiKeyUsage.requests_count).label('requests'),
            func.count(func.distinct(ApiKeyUsage.api_key)).label('users')
        ).filter(
            ApiKeyUsage.date >= start_date,
            ApiKeyUsage.date <= end_date
        ).group_by(
            ApiKeyUsage.date
        ).order_by(
            desc(ApiKeyUsage.date)
        ).all()
        
        daily_breakdown = []
        for day in daily_stats:
            daily_breakdown.append({
                "date": day.date.isoformat(),
                "tokens": day.tokens,
                "requests": day.requests,
                "unique_users": day.users,
                "avg_tokens_per_request": round(day.tokens / day.requests, 2) if day.requests > 0 else 0
            })
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "total": {
                "tokens_used": int(total_stats.total_tokens or 0),
                "requests_count": int(total_stats.total_requests or 0),
                "unique_users": int(total_stats.unique_users or 0),
                "avg_tokens_per_request": round((total_stats.total_tokens or 0) / (total_stats.total_requests or 1), 2),
                "avg_requests_per_user": round((total_stats.total_requests or 0) / (total_stats.unique_users or 1), 2)
            },
            "today": {
                "tokens_used": int(today_stats.today_tokens or 0),
                "requests_count": int(today_stats.today_requests or 0),
                "unique_users": int(today_stats.today_users or 0)
            },
            "daily_breakdown": daily_breakdown
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {"error": "Ошибка при получении системной статистики"}
    finally:
        db.close()


def cleanup_old_records(days_to_keep: int = 365) -> int:
    """
    Очистка старых записей из базы данных
    
    Args:
        days_to_keep: Количество дней для хранения записей
        
    Returns:
        int: Количество удалённых записей
    """
    db = get_db()
    try:
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(ApiKeyUsage).filter(
            ApiKeyUsage.date < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old usage records")
        return deleted_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up old records: {str(e)}")
        return 0
    finally:
        db.close()