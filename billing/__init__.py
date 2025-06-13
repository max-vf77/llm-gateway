"""
Модуль биллинга для LLM Gateway
Обеспечивает учёт использования токенов и проверку лимитов для API-ключей
"""

from .models import ApiKeyUsage, ApiKeyLimits, get_db, init_database, get_global_limits
from .tracker import log_usage, get_usage_stats
from .limits import check_limits, get_remaining_limits
from .token_tracker import token_tracker
from .tariffs import get_tariff, get_max_tokens, set_tariff, get_all_tariffs

__version__ = "2.0.0"

__all__ = [
    "ApiKeyUsage",
    "ApiKeyLimits", 
    "get_db",
    "init_database",
    "get_global_limits",
    "log_usage",
    "get_usage_stats",
    "check_limits",
    "get_remaining_limits",
    "token_tracker",
    "get_tariff",
    "get_max_tokens",
    "set_tariff",
    "get_all_tariffs"
]