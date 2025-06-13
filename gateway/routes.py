from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import Dict, Any
from .auth import verify_api_key
from .client import forward_to_llm
from billing.limits import check_limits, LimitExceededException
from billing.tracker import log_usage
import logging

# Создание роутера
router = APIRouter()

# Настройка логирования
logger = logging.getLogger(__name__)


def estimate_token_count(payload: Dict[Any, Any]) -> int:
    """
    Оценка количества токенов в запросе
    Простая эвристика: ~4 символа = 1 токен
    """
    prompt = payload.get("prompt", "")
    max_tokens = payload.get("max_tokens", 100)
    
    # Оценка токенов в промпте (входящих)
    input_tokens = len(str(prompt)) // 4
    
    # Общая оценка: входящие + максимальные исходящие токены
    estimated_tokens = input_tokens + max_tokens
    
    return max(estimated_tokens, 1)  # Минимум 1 токен


def extract_actual_token_count(result: Dict[Any, Any]) -> int:
    """
    Извлечение фактического количества токенов из ответа LLM
    """
    # Стандартные поля для OpenAI-совместимых API
    if "usage" in result:
        usage = result["usage"]
        if "total_tokens" in usage:
            return usage["total_tokens"]
        elif "completion_tokens" in usage and "prompt_tokens" in usage:
            return usage["completion_tokens"] + usage["prompt_tokens"]
    
    # Если информации о токенах нет, используем оценку по длине ответа
    if "choices" in result and len(result["choices"]) > 0:
        choice = result["choices"][0]
        if "text" in choice:
            return len(choice["text"]) // 4
        elif "message" in choice and "content" in choice["message"]:
            return len(choice["message"]["content"]) // 4
    
    # Возвращаем минимальное значение если не удалось определить
    return 1


@router.post("/v1/completions")
async def completions(
    request: Request, 
    api_key: str = Depends(verify_api_key)
) -> Dict[Any, Any]:
    """
    Обработка запросов на генерацию текста
    Проксирует запрос к серверу LLM после проверки API-ключа и лимитов
    """
    try:
        # Получение JSON данных из запроса
        payload = await request.json()
        logger.info(f"Получен запрос от клиента с API ключом: {api_key[:8]}...")
        
        # Оценка количества токенов для проверки лимитов
        estimated_tokens = estimate_token_count(payload)
        logger.debug(f"Estimated tokens for request: {estimated_tokens}")
        
        # Проверка лимитов перед выполнением запроса
        try:
            limits_info = check_limits(api_key, estimated_tokens)
            logger.info(f"Limits check passed for API key {api_key[:8]}...")
        except LimitExceededException as e:
            logger.warning(f"Limits exceeded for API key {api_key[:8]}...: {e.detail}")
            raise e
        
        # Проксирование запроса к LLM серверу
        result = await forward_to_llm(payload)
        
        # Извлечение фактического количества токенов из ответа
        actual_tokens = extract_actual_token_count(result)
        logger.debug(f"Actual tokens used: {actual_tokens}")
        
        # Логирование использования токенов
        if log_usage(api_key, actual_tokens):
            logger.info(f"Usage logged: {actual_tokens} tokens for API key {api_key[:8]}...")
        else:
            logger.warning(f"Failed to log usage for API key {api_key[:8]}...")
        
        logger.info("Запрос успешно обработан")
        return result
        
    except LimitExceededException:
        # Повторно поднимаем исключение лимитов без изменений
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Проверка состояния сервиса
    """
    return {"status": "healthy", "service": "llm-gateway"}


@router.get("/usage")
async def get_usage(api_key: str = Depends(verify_api_key)):
    """
    Получение статистики использования для API-ключа
    """
    from billing.tracker import get_usage_stats
    from billing.limits import get_remaining_limits
    
    try:
        usage_stats = get_usage_stats(api_key)
        remaining_limits = get_remaining_limits(api_key)
        
        return {
            "usage": usage_stats,
            "limits": remaining_limits
        }
    except Exception as e:
        logger.error(f"Error getting usage for API key {api_key[:8]}...: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики использования"
        )


@router.get("/limits")
async def get_limits(api_key: str = Depends(verify_api_key)):
    """
    Получение информации о лимитах для API-ключа
    """
    from billing.limits import get_remaining_limits
    
    try:
        limits_info = get_remaining_limits(api_key)
        return limits_info
    except Exception as e:
        logger.error(f"Error getting limits for API key {api_key[:8]}...: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о лимитах"
        )


@router.get("/")
async def root():
    """
    Корневой эндпоинт с информацией о сервисе
    """
    return {
        "service": "LLM Gateway",
        "version": "1.0.0",
        "description": "Шлюз для проксирования запросов к серверу инференса LLM",
        "endpoints": {
            "completions": "/v1/completions",
            "usage": "/usage",
            "limits": "/limits",
            "health": "/health"
        }
    }