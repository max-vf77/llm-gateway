# Rate Limiting в LLM Gateway

## Обзор

Система rate limiting обеспечивает ограничение количества запросов от одного API-ключа в единицу времени. Это защищает сервис от злоупотреблений и обеспечивает справедливое распределение ресурсов.

## Конфигурация

### Переменные окружения (.env)

```bash
# Настройки rate limiting
RATE_LIMIT_REQUESTS=30    # Максимум запросов
RATE_LIMIT_WINDOW=60      # Временное окно в секундах

# Настройки Redis (опционально)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Принцип работы

### Алгоритм
- **Sliding Window**: Используется скользящее временное окно
- **Лимит**: 30 запросов за 60 секунд (по умолчанию)
- **Ключи Redis**: `rate_limit:{api_key}`
- **TTL**: Автоматическое истечение через 60 секунд

### Хранилище
1. **Основное**: Redis с автоматическим TTL
2. **Fallback**: Словарь в памяти при недоступности Redis

## Интеграция

### FastAPI зависимость

```python
from gateway.limiter import rate_limited

@router.post("/v1/completions")
async def completions(api_key: str = Depends(rate_limited)):
    # API ключ уже проверен на rate limit
    pass
```

### Ручная проверка

```python
from gateway.limiter import check_rate_limit

try:
    rate_info = check_rate_limit(api_key)
    print(f"Запросов: {rate_info['current_count']}/{rate_info['limit']}")
except HTTPException as e:
    print(f"Rate limit exceeded: {e.detail}")
```

## API эндпоинты

### GET /rate-limit
Получение текущего состояния rate limit для API-ключа.

**Заголовки:**
```
Authorization: Bearer sk-your-api-key
```

**Ответ:**
```json
{
  "api_key": "sk-your-...",
  "limit": 30,
  "window_seconds": 60,
  "current_count": 5,
  "remaining": 25,
  "storage": "redis"
}
```

## Обработка ошибок

### HTTP 429 Too Many Requests

При превышении лимита возвращается:

```json
{
  "detail": "Превышен лимит запросов: 30/30 за 60 секунд"
}
```

**Заголовки ответа:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 60
Retry-After: 60
```

## Администрирование

### Сброс лимитов

```python
from gateway.limiter import reset_rate_limit

# Сброс для конкретного ключа
success = reset_rate_limit("sk-some-key")
```

### Получение информации

```python
from gateway.limiter import get_rate_limit_info

info = get_rate_limit_info("sk-some-key")
print(f"Использовано: {info['current_count']}/{info['limit']}")
```

### Проверка состояния Redis

```python
from gateway.limiter import get_redis_health

health = get_redis_health()
print(f"Redis статус: {health['status']}")
```

## Мониторинг

### Логирование

Rate limiting логирует следующие события:
- Успешные проверки (DEBUG)
- Превышения лимитов (WARNING)
- Ошибки Redis (ERROR)

### Метрики

Рекомендуется отслеживать:
- Количество заблокированных запросов
- Процент использования лимитов
- Доступность Redis
- Топ пользователей по количеству запросов

## Настройка производительности

### Redis оптимизация

```bash
# Настройки Redis для rate limiting
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 256mb
```

### Fallback режим

При недоступности Redis система автоматически переключается на хранение в памяти:
- Данные сохраняются только до перезапуска
- Производительность остается высокой
- Логируется предупреждение

## Безопасность

### Защита от обхода

- Rate limiting применяется после проверки API-ключа
- Невозможно обойти через разные эндпоинты
- Лимиты привязаны к конкретному ключу

### DDoS защита

- Блокировка на уровне API-ключа
- Автоматическое восстановление через TTL
- Минимальная нагрузка на систему

## Расширение

### Кастомные лимиты

Можно реализовать индивидуальные лимиты:

```python
# В будущих версиях
CUSTOM_LIMITS = {
    "sk-premium-key": {"requests": 100, "window": 60},
    "sk-basic-key": {"requests": 10, "window": 60}
}
```

### Дополнительные метрики

- Лимиты по IP адресам
- Лимиты по типу запросов
- Адаптивные лимиты на основе нагрузки