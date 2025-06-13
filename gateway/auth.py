import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Список допустимых ключей из переменной окружения
ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",")

# Схема безопасности для Bearer токенов
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Проверка API-ключа из заголовка Authorization: Bearer <key>
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API ключ не предоставлен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    # Проверка, что ключ находится в списке разрешённых
    if not ALLOWED_API_KEYS or api_key not in ALLOWED_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недопустимый API ключ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key