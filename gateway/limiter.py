"""
Модуль ограничения скорости запросов (Rate Limiting) для LLM Gateway
Использует Redis для хранения счетчиков запросов с TTL
"""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from redis import Redis, ConnectionError as RedisConnectionError
from dotenv import load_dotenv
from .auth import verify_api_key

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Параметры rate limiting
RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))  # запросов
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))   # секунд

# Настройки Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Глобальная переменная для Redis клиента
redis_client: Optional[Redis] = None

# Fallback словарь для случаев когда Redis недоступен
fallback_storage = {}


def get_redis_client() -> Optional[Redis]:
    """
    Получение клиента Redis с обработкой ошибок подключения
    """
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Проверка подключения
            redis_client.ping()
            logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            return redis_client
        except (RedisConnectionError, Exception) as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using fallback storage.")
            redis_client = None
            return None
    
    return redis_client


def check_rate_limit_redis(api_key: str) -> tuple[bool, int, int]:
    """
    Проверка rate limit через Redis
    
    Args:
        api_key: API ключ для проверки
        
    Returns:
        tuple: (is_allowed, current_count, remaining_count)
    """
    redis = get_redis_client()
    if redis is None:
        return check_rate_limit_fallback(api_key)
    
    try:
        key = f"rate_limit:{api_key}"
        
        # Получение текущего счетчика
        current = redis.get(key)
        if current is None:
            current = 0
        else:
            current = int(current)
        
        # Проверка лимита
        if current >= RATE_LIMIT:
            remaining = 0
            return False, current, remaining
        
        # Инкремент счетчика
        new_count = redis.incr(key)
        
        # Установка TTL только для первого запроса
        if new_count == 1:
            redis.expire(key, RATE_WINDOW)
        
        remaining = max(0, RATE_LIMIT - new_count)
        return True, new_count, remaining
        
    except Exception as e:
        logger.error(f"Redis error in rate limiting: {e}. Falling back to memory storage.")
        return check_rate_limit_fallback(api_key)


def check_rate_limit_fallback(api_key: str) -> tuple[bool, int, int]:
    """
    Fallback проверка rate limit через словарь в памяти
    
    Args:
        api_key: API ключ для проверки
        
    Returns:
        tuple: (is_allowed, current_count, remaining_count)
    """
    import time
    
    current_time = time.time()
    
    if api_key not in fallback_storage:
        fallback_storage[api_key] = {
            'count': 0,
            'window_start': current_time
        }
    
    data = fallback_storage[api_key]
    
    # Проверка, не истек ли временной интервал
    if current_time - data['window_start'] >= RATE_WINDOW:
        data['count'] = 0
        data['window_start'] = current_time
    
    # Проверка лимита
    if data['count'] >= RATE_LIMIT:
        remaining = 0
        return False, data['count'], remaining
    
    # Инкремент счетчика
    data['count'] += 1
    remaining = max(0, RATE_LIMIT - data['count'])
    
    return True, data['count'], remaining


def check_rate_limit(api_key: str) -> dict:
    """
    Основная функция проверки rate limit
    
    Args:
        api_key: API ключ для проверки
        
    Returns:
        dict: Информация о rate limit
        
    Raises:
        HTTPException: При превышении лимита
    """
    is_allowed, current_count, remaining = check_rate_limit_redis(api_key)
    
    rate_limit_info = {
        "api_key": api_key[:8] + "...",
        "limit": RATE_LIMIT,
        "window_seconds": RATE_WINDOW,
        "current_count": current_count,
        "remaining": remaining,
        "allowed": is_allowed
    }
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for API key {api_key[:8]}...: {current_count}/{RATE_LIMIT}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Превышен лимит запросов: {current_count}/{RATE_LIMIT} за {RATE_WINDOW} секунд",
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(RATE_WINDOW),
                "Retry-After": str(RATE_WINDOW)
            }
        )
    
    logger.debug(f"Rate limit check passed for API key {api_key[:8]}...: {current_count}/{RATE_LIMIT}")
    return rate_limit_info


async def rate_limited(api_key: str = Depends(verify_api_key)) -> str:
    """
    FastAPI зависимость для проверки rate limit
    
    Args:
        api_key: API ключ (получается из зависимости verify_api_key)
        
    Returns:
        str: API ключ если проверка прошла успешно
        
    Raises:
        HTTPException: При превышении лимита
    """
    check_rate_limit(api_key)
    return api_key


def get_rate_limit_info(api_key: str) -> dict:
    """
    Получение информации о текущем состоянии rate limit без инкремента
    
    Args:
        api_key: API ключ
        
    Returns:
        dict: Информация о rate limit
    """
    redis = get_redis_client()
    
    if redis is not None:
        try:
            key = f"rate_limit:{api_key}"
            current = redis.get(key)
            current_count = int(current) if current else 0
            remaining = max(0, RATE_LIMIT - current_count)
            
            return {
                "api_key": api_key[:8] + "...",
                "limit": RATE_LIMIT,
                "window_seconds": RATE_WINDOW,
                "current_count": current_count,
                "remaining": remaining,
                "storage": "redis"
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info from Redis: {e}")
    
    # Fallback к памяти
    import time
    current_time = time.time()
    
    if api_key in fallback_storage:
        data = fallback_storage[api_key]
        if current_time - data['window_start'] < RATE_WINDOW:
            current_count = data['count']
        else:
            current_count = 0
    else:
        current_count = 0
    
    remaining = max(0, RATE_LIMIT - current_count)
    
    return {
        "api_key": api_key[:8] + "...",
        "limit": RATE_LIMIT,
        "window_seconds": RATE_WINDOW,
        "current_count": current_count,
        "remaining": remaining,
        "storage": "memory"
    }


def reset_rate_limit(api_key: str) -> bool:
    """
    Сброс rate limit для конкретного API ключа (для административных целей)
    
    Args:
        api_key: API ключ
        
    Returns:
        bool: True если сброс успешен
    """
    redis = get_redis_client()
    
    if redis is not None:
        try:
            key = f"rate_limit:{api_key}"
            redis.delete(key)
            logger.info(f"Rate limit reset for API key {api_key[:8]}... in Redis")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit in Redis: {e}")
    
    # Fallback к памяти
    if api_key in fallback_storage:
        del fallback_storage[api_key]
        logger.info(f"Rate limit reset for API key {api_key[:8]}... in memory")
    
    return True


def get_redis_health() -> dict:
    """
    Проверка состояния подключения к Redis
    
    Returns:
        dict: Информация о состоянии Redis
    """
    redis = get_redis_client()
    
    if redis is not None:
        try:
            redis.ping()
            return {
                "status": "connected",
                "host": REDIS_HOST,
                "port": REDIS_PORT,
                "db": REDIS_DB
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "host": REDIS_HOST,
                "port": REDIS_PORT
            }
    else:
        return {
            "status": "not_configured",
            "fallback": "memory_storage"
        }