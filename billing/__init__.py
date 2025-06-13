"""
Модуль биллинга для LLM Gateway
Обеспечивает учёт использования токенов и проверку лимитов для API-ключей
"""

from .models import ApiKeyUsage, ApiKeyLimits, get_db, init_database, get_global_limits
from .tracker import log_usage, get_usage_stats
from .limits import check_limits, get_remaining_limits

__version__ = "1.0.0"

__all__ = [
    "ApiKeyUsage",
    "ApiKeyLimits", 
    "get_db",
    "init_database",
    "get_global_limits",
    "log_usage",
    "get_usage_stats",
    "check_limits",
    "get_remaining_limits"
]