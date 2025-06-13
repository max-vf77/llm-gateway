import os
import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

# URL сервера LLM из переменной окружения
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8080/v1/completions")

# Настройка логирования
logger = logging.getLogger(__name__)

async def forward_to_llm(request_data: dict) -> dict:
    """
    Проксирование запроса к серверу LLM
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Отправка запроса к LLM серверу: {LLM_SERVER_URL}")
            
            response = await client.post(
                LLM_SERVER_URL,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Проверка статуса ответа
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"LLM сервер вернул ошибку {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ошибка LLM сервера: {response.text}"
                )
                
    except httpx.TimeoutException:
        logger.error("Таймаут при обращении к LLM серверу")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Таймаут при обращении к LLM серверу"
        )
    except httpx.ConnectError:
        logger.error(f"Не удалось подключиться к LLM серверу: {LLM_SERVER_URL}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось подключиться к LLM серверу"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP ошибка при обращении к LLM серверу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка при обращении к LLM серверу: {str(e)}"
        )