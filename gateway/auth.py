import os
from fastapi import Header, HTTPException, status
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Список допустимых ключей из переменной окружения
ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API ключ не предоставлен",
        )

    if x_api_key not in ALLOWED_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недопустимый API ключ",
        )

    return x_api_key