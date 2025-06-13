"""
Модуль отслеживания токенов для LLM Gateway
Поддерживает Redis и fallback на словарь в памяти
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from redis import Redis, ConnectionError as RedisConnectionError
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройки Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


class TokenTracker:
    """
    Класс для отслеживания использования токенов по API-ключам
    Поддерживает Redis и fallback на словарь в памяти
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.fallback_storage: Dict[str, Dict[str, Any]] = {}
        self._init_redis()
    
    def _init_redis(self) -> None:
        """Инициализация подключения к Redis"""
        try:
            self.redis_client = Redis(
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
            self.redis_client.ping()
            logger.info(f"TokenTracker: Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except (RedisConnectionError, Exception) as e:
            logger.warning(f"TokenTracker: Failed to connect to Redis: {e}. Using fallback storage.")
            self.redis_client = None
    
    def _get_redis_key(self, api_key: str) -> str:
        """Генерация ключа Redis для API ключа"""
        return f"token_usage:{api_key}"
    
    def _get_current_time(self) -> str:
        """Получение текущего времени в ISO формате"""
        return datetime.now(timezone.utc).isoformat()
    
    def _get_usage_from_redis(self, api_key: str) -> Dict[str, Any]:
        """Получение данных об использовании из Redis"""
        if self.redis_client is None:
            return self._get_usage_from_fallback(api_key)
        
        try:
            key = self._get_redis_key(api_key)
            data = self.redis_client.get(key)
            
            if data is None:
                return {
                    "used_tokens": 0,
                    "last_updated": self._get_current_time()
                }
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"TokenTracker: Error getting usage from Redis: {e}")
            return self._get_usage_from_fallback(api_key)
    
    def _get_usage_from_fallback(self, api_key: str) -> Dict[str, Any]:
        """Получение данных об использовании из fallback хранилища"""
        if api_key not in self.fallback_storage:
            self.fallback_storage[api_key] = {
                "used_tokens": 0,
                "last_updated": self._get_current_time()
            }
        return self.fallback_storage[api_key].copy()
    
    def _save_usage_to_redis(self, api_key: str, usage_data: Dict[str, Any]) -> bool:
        """Сохранение данных об использовании в Redis"""
        if self.redis_client is None:
            return self._save_usage_to_fallback(api_key, usage_data)
        
        try:
            key = self._get_redis_key(api_key)
            self.redis_client.set(key, json.dumps(usage_data))
            return True
        except Exception as e:
            logger.error(f"TokenTracker: Error saving usage to Redis: {e}")
            return self._save_usage_to_fallback(api_key, usage_data)
    
    def _save_usage_to_fallback(self, api_key: str, usage_data: Dict[str, Any]) -> bool:
        """Сохранение данных об использовании в fallback хранилище"""
        self.fallback_storage[api_key] = usage_data.copy()
        return True
    
    def get_usage(self, api_key: str) -> int:
        """
        Получение количества использованных токенов для API ключа
        
        Args:
            api_key: API ключ
            
        Returns:
            int: Количество использованных токенов
        """
        try:
            usage_data = self._get_usage_from_redis(api_key)
            return usage_data.get("used_tokens", 0)
        except Exception as e:
            logger.error(f"TokenTracker: Error getting usage for {api_key[:8]}...: {e}")
            return 0
    
    def increment_usage(self, api_key: str, tokens: int) -> bool:
        """
        Увеличение счетчика использованных токенов
        
        Args:
            api_key: API ключ
            tokens: Количество токенов для добавления
            
        Returns:
            bool: True если операция успешна
        """
        if tokens <= 0:
            logger.warning(f"TokenTracker: Invalid token count {tokens} for {api_key[:8]}...")
            return False
        
        try:
            usage_data = self._get_usage_from_redis(api_key)
            usage_data["used_tokens"] += tokens
            usage_data["last_updated"] = self._get_current_time()
            
            success = self._save_usage_to_redis(api_key, usage_data)
            
            if success:
                logger.info(f"TokenTracker: Incremented usage for {api_key[:8]}... by {tokens} tokens")
            else:
                logger.error(f"TokenTracker: Failed to increment usage for {api_key[:8]}...")
            
            return success
        except Exception as e:
            logger.error(f"TokenTracker: Error incrementing usage for {api_key[:8]}...: {e}")
            return False
    
    def check_limit(self, api_key: str, max_tokens: int) -> bool:
        """
        Проверка, не превышен ли лимит токенов
        
        Args:
            api_key: API ключ
            max_tokens: Максимальное количество токенов
            
        Returns:
            bool: True если лимит не превышен
        """
        try:
            current_usage = self.get_usage(api_key)
            is_within_limit = current_usage < max_tokens
            
            if not is_within_limit:
                logger.warning(f"TokenTracker: Token limit exceeded for {api_key[:8]}...: {current_usage}/{max_tokens}")
            else:
                logger.debug(f"TokenTracker: Token limit check passed for {api_key[:8]}...: {current_usage}/{max_tokens}")
            
            return is_within_limit
        except Exception as e:
            logger.error(f"TokenTracker: Error checking limit for {api_key[:8]}...: {e}")
            return True  # В случае ошибки разрешаем запрос
    
    def get_detailed_usage(self, api_key: str) -> Dict[str, Any]:
        """
        Получение детальной информации об использовании
        
        Args:
            api_key: API ключ
            
        Returns:
            dict: Детальная информация об использовании
        """
        try:
            usage_data = self._get_usage_from_redis(api_key)
            
            return {
                "api_key": api_key[:8] + "...",
                "used_tokens": usage_data.get("used_tokens", 0),
                "last_updated": usage_data.get("last_updated"),
                "storage_type": "redis" if self.redis_client is not None else "memory"
            }
        except Exception as e:
            logger.error(f"TokenTracker: Error getting detailed usage for {api_key[:8]}...: {e}")
            return {
                "api_key": api_key[:8] + "...",
                "used_tokens": 0,
                "last_updated": None,
                "error": str(e)
            }
    
    def reset_usage(self, api_key: str) -> bool:
        """
        Сброс счетчика использования для API ключа
        
        Args:
            api_key: API ключ
            
        Returns:
            bool: True если операция успешна
        """
        try:
            usage_data = {
                "used_tokens": 0,
                "last_updated": self._get_current_time()
            }
            
            success = self._save_usage_to_redis(api_key, usage_data)
            
            if success:
                logger.info(f"TokenTracker: Reset usage for {api_key[:8]}...")
            else:
                logger.error(f"TokenTracker: Failed to reset usage for {api_key[:8]}...")
            
            return success
        except Exception as e:
            logger.error(f"TokenTracker: Error resetting usage for {api_key[:8]}...: {e}")
            return False
    
    def reset_monthly_usage(self) -> Dict[str, Any]:
        """
        Сброс месячного использования для всех API ключей
        Используется для cron задач
        
        Returns:
            dict: Статистика сброса
        """
        reset_count = 0
        error_count = 0
        
        try:
            if self.redis_client is not None:
                # Сброс в Redis
                try:
                    pattern = "token_usage:*"
                    keys = self.redis_client.keys(pattern)
                    
                    for key in keys:
                        try:
                            api_key = key.replace("token_usage:", "")
                            if self.reset_usage(api_key):
                                reset_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            logger.error(f"TokenTracker: Error resetting key {key}: {e}")
                            error_count += 1
                            
                except Exception as e:
                    logger.error(f"TokenTracker: Error getting Redis keys: {e}")
                    error_count += 1
            
            # Сброс в fallback хранилище
            for api_key in list(self.fallback_storage.keys()):
                try:
                    if self.reset_usage(api_key):
                        reset_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"TokenTracker: Error resetting fallback key {api_key}: {e}")
                    error_count += 1
            
            result = {
                "reset_count": reset_count,
                "error_count": error_count,
                "timestamp": self._get_current_time(),
                "status": "completed"
            }
            
            logger.info(f"TokenTracker: Monthly reset completed: {reset_count} reset, {error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"TokenTracker: Error in monthly reset: {e}")
            return {
                "reset_count": reset_count,
                "error_count": error_count + 1,
                "timestamp": self._get_current_time(),
                "status": "error",
                "error": str(e)
            }
    
    def get_all_usage_stats(self) -> Dict[str, Any]:
        """
        Получение статистики использования для всех API ключей
        
        Returns:
            dict: Общая статистика
        """
        stats = {
            "total_keys": 0,
            "total_tokens": 0,
            "keys_usage": [],
            "storage_type": "redis" if self.redis_client is not None else "memory",
            "timestamp": self._get_current_time()
        }
        
        try:
            if self.redis_client is not None:
                # Статистика из Redis
                try:
                    pattern = "token_usage:*"
                    keys = self.redis_client.keys(pattern)
                    
                    for key in keys:
                        try:
                            api_key = key.replace("token_usage:", "")
                            usage_data = self._get_usage_from_redis(api_key)
                            
                            stats["total_keys"] += 1
                            stats["total_tokens"] += usage_data.get("used_tokens", 0)
                            stats["keys_usage"].append({
                                "api_key": api_key[:8] + "...",
                                "used_tokens": usage_data.get("used_tokens", 0),
                                "last_updated": usage_data.get("last_updated")
                            })
                        except Exception as e:
                            logger.error(f"TokenTracker: Error processing key {key}: {e}")
                            
                except Exception as e:
                    logger.error(f"TokenTracker: Error getting Redis stats: {e}")
            
            # Статистика из fallback хранилища
            for api_key, usage_data in self.fallback_storage.items():
                stats["total_keys"] += 1
                stats["total_tokens"] += usage_data.get("used_tokens", 0)
                stats["keys_usage"].append({
                    "api_key": api_key[:8] + "...",
                    "used_tokens": usage_data.get("used_tokens", 0),
                    "last_updated": usage_data.get("last_updated")
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"TokenTracker: Error getting all usage stats: {e}")
            stats["error"] = str(e)
            return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния TokenTracker
        
        Returns:
            dict: Информация о состоянии
        """
        health = {
            "status": "healthy",
            "redis_connected": False,
            "fallback_keys": len(self.fallback_storage),
            "timestamp": self._get_current_time()
        }
        
        if self.redis_client is not None:
            try:
                self.redis_client.ping()
                health["redis_connected"] = True
                health["redis_info"] = {
                    "host": REDIS_HOST,
                    "port": REDIS_PORT,
                    "db": REDIS_DB
                }
            except Exception as e:
                health["redis_error"] = str(e)
        
        return health


# Глобальный экземпляр TokenTracker
token_tracker = TokenTracker()