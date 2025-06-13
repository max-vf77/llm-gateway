# Token Tracking в LLM Gateway

## Обзор

TokenTracker - это система отслеживания использования токенов по API-ключам с поддержкой Redis и fallback на память. Обеспечивает точный учёт потребления токенов для тарификации и контроля лимитов.

## Архитектура

### Компоненты

- **TokenTracker класс** - основной интерфейс для работы с токенами
- **Redis хранилище** - основное хранилище с персистентностью
- **Memory fallback** - резервное хранилище в памяти
- **Tariff система** - управление лимитами по тарифам

### Структура данных

```json
{
  "used_tokens": 1500,
  "last_updated": "2025-06-13T11:56:46.548995+00:00"
}
```

## Конфигурация

### Переменные окружения (.env)

```bash
# Redis для TokenTracker
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Тарифы по умолчанию
DEFAULT_MAX_TOKENS=50000
```

## Использование

### Основные операции

```python
from billing.token_tracker import token_tracker

# Получение использования
usage = token_tracker.get_usage("sk-api-key")
print(f"Использовано токенов: {usage}")

# Увеличение счётчика
success = token_tracker.increment_usage("sk-api-key", 150)

# Проверка лимита
within_limit = token_tracker.check_limit("sk-api-key", 10000)

# Сброс использования
token_tracker.reset_usage("sk-api-key")
```

### Детальная информация

```python
# Получение подробной статистики
details = token_tracker.get_detailed_usage("sk-api-key")
print(details)
# {
#   "api_key": "sk-api-...",
#   "used_tokens": 1500,
#   "last_updated": "2025-06-13T11:56:46.548995+00:00",
#   "storage_type": "redis"
# }
```

## Интеграция с API

### Автоматическое отслеживание

В `gateway/routes.py` TokenTracker интегрирован с основным потоком:

```python
# Проверка лимитов перед запросом
max_tokens = get_max_tokens(api_key)
if not token_tracker.check_limit(api_key, max_tokens):
    raise HTTPException(status_code=429, detail="Превышен лимит токенов")

# Логирование после ответа
token_tracker.increment_usage(api_key, actual_tokens)
```

### API эндпоинты

#### GET /tariff
Информация о тарифе и использовании токенов:

```json
{
  "tariff": {
    "max_tokens": 10000,
    "name": "Test Basic",
    "description": "Базовый тестовый тариф",
    "api_key": "sk-test-..."
  },
  "usage": {
    "used_tokens": 1500,
    "remaining_tokens": 8500,
    "usage_percentage": 15.0
  }
}
```

#### GET /usage
Комплексная статистика включает данные TokenTracker:

```json
{
  "tracker": {
    "api_key": "sk-test-...",
    "used_tokens": 1500,
    "last_updated": "2025-06-13T11:56:46.548995+00:00",
    "storage_type": "redis"
  }
}
```

## Система тарифов

### Предопределённые тарифы

```python
TARIFFS = {
    "sk-test-key-1": {
        "max_tokens": 10000,
        "name": "Test Basic",
        "description": "Базовый тестовый тариф"
    },
    "sk-enterprise-456": {
        "max_tokens": 5000000,
        "name": "Enterprise",
        "description": "Корпоративный тариф"
    }
}
```

### Управление тарифами

```python
from billing.tariffs import set_tariff, get_tariff, apply_tariff_plan

# Установка кастомного тарифа
set_tariff("sk-custom-key", max_tokens=25000, name="Custom Plan")

# Получение тарифа
tariff = get_tariff("sk-api-key")

# Применение готового плана
apply_tariff_plan("sk-api-key", "premium")  # 100,000 токенов
```

### Тарифные планы

- **basic**: 10,000 токенов
- **premium**: 100,000 токенов  
- **enterprise**: 1,000,000 токенов
- **unlimited**: 10,000,000 токенов

## Административные функции

### Массовый сброс

```python
# Сброс для всех ключей (для cron задач)
result = token_tracker.reset_monthly_usage()
print(f"Сброшено: {result['reset_count']}, ошибок: {result['error_count']}")
```

### Системная статистика

```python
# Общая статистика по всем ключам
stats = token_tracker.get_all_usage_stats()
print(f"Всего ключей: {stats['total_keys']}")
print(f"Всего токенов: {stats['total_tokens']}")
```

### Проверка состояния

```python
# Проверка здоровья системы
health = token_tracker.health_check()
print(f"Статус: {health['status']}")
print(f"Redis подключен: {health['redis_connected']}")
```

## Отказоустойчивость

### Redis недоступен

При недоступности Redis система автоматически:
1. Переключается на хранение в памяти
2. Логирует предупреждение
3. Продолжает работу без прерываний
4. Восстанавливает подключение при возможности

### Обработка ошибок

```python
try:
    token_tracker.increment_usage(api_key, tokens)
except Exception as e:
    logger.error(f"Token tracking error: {e}")
    # Система продолжает работу
```

## Мониторинг

### Логирование

TokenTracker логирует:
- Успешные операции (INFO)
- Превышения лимитов (WARNING)  
- Ошибки Redis (ERROR)
- Переключения на fallback (WARNING)

### Метрики для мониторинга

- Общее использование токенов
- Топ пользователей по потреблению
- Процент использования тарифных лимитов
- Доступность Redis
- Количество ключей в fallback хранилище

## Производительность

### Оптимизация Redis

```bash
# Настройки для токен трекинга
redis-cli CONFIG SET save "900 1 300 10 60 10000"
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Batch операции

Для высоконагруженных систем можно реализовать:
- Батчевое обновление токенов
- Кэширование в памяти с периодической синхронизацией
- Асинхронные операции записи

## Безопасность

### Защита данных

- API ключи маскируются в логах и ответах
- Данные хранятся только в Redis/памяти
- Нет персистентного хранения чувствительной информации

### Изоляция

- Каждый API ключ имеет изолированный счётчик
- Невозможно получить данные чужого ключа
- Автоматическая очистка при сбросе

## Расширение

### Дополнительные метрики

Можно добавить отслеживание:
- Типов запросов (completion, chat, etc.)
- Временных паттернов использования
- Географического распределения
- Качества ответов

### Интеграция с внешними системами

- Экспорт в системы мониторинга (Prometheus, Grafana)
- Уведомления при приближении к лимитам
- Интеграция с биллинговыми системами
- API для внешнего управления тарифами