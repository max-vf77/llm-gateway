"""
Модели данных для системы биллинга LLM Gateway
Хранение статистики использования API-ключей в SQLite
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Date, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовый класс для моделей
Base = declarative_base()

# Путь к базе данных SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./billing.db")

# Создание движка базы данных
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ApiKeyUsage(Base):
    """
    Модель для хранения статистики использования API-ключей
    """
    __tablename__ = "api_key_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(255), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False, default=date.today)
    tokens_used = Column(BigInteger, default=0, nullable=False)
    requests_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ApiKeyUsage(api_key='{self.api_key[:8]}...', date='{self.date}', tokens={self.tokens_used})>"


class ApiKeyLimits(Base):
    """
    Модель для хранения лимитов API-ключей
    Позволяет настраивать индивидуальные лимиты для каждого ключа
    """
    __tablename__ = "api_key_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    daily_limit = Column(BigInteger, nullable=True)  # None означает использование глобального лимита
    monthly_limit = Column(BigInteger, nullable=True)  # None означает использование глобального лимита
    is_active = Column(Integer, default=1, nullable=False)  # 1 - активен, 0 - заблокирован
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ApiKeyLimits(api_key='{self.api_key[:8]}...', daily={self.daily_limit}, monthly={self.monthly_limit})>"


def get_db() -> Session:
    """
    Получение сессии базы данных
    """
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Сессия будет закрыта в вызывающем коде


def init_database():
    """
    Инициализация базы данных - создание всех таблиц
    """
    Base.metadata.create_all(bind=engine)


def get_global_limits() -> tuple[int, int]:
    """
    Получение глобальных лимитов из переменных окружения
    
    Returns:
        tuple: (daily_limit, monthly_limit)
    """
    daily_limit = int(os.getenv("API_DAILY_LIMIT", "50000"))
    monthly_limit = int(os.getenv("API_MONTHLY_LIMIT", "1000000"))
    return daily_limit, monthly_limit


# Инициализация базы данных при импорте модуля
init_database()