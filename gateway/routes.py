from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import Dict, Any
from .auth import verify_api_key
from .client import forward_to_llm
import logging

# Создание роутера
router = APIRouter()

# Настройка логирования
logger = logging.getLogger(__name__)

@router.post("/v1/completions")
async def completions(
    request: Request, 
    api_key: str = Depends(verify_api_key)
) -> Dict[Any, Any]:
    """
    Обработка запросов на генерацию текста
    Проксирует запрос к серверу LLM после проверки API-ключа
    """
    try:
        # Получение JSON данных из запроса
        payload = await request.json()
        logger.info(f"Получен запрос от клиента с API ключом: {api_key[:8]}...")
        
        # Проксирование запроса к LLM серверу
        result = await forward_to_llm(payload)
        
        logger.info("Запрос успешно обработан")
        return result
        
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
            "health": "/health"
        }
    }