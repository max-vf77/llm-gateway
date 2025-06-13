# LLM Gateway

REST API-сервис на FastAPI, который служит шлюзом между клиентами и сервером инференса LLM (например, llama-cpp).

## Возможности

- ✅ Проверка API-ключей через заголовок `Authorization: Bearer <key>`
- ✅ Поддержка нескольких API-ключей
- ✅ Проксирование запросов к серверу LLM
- ✅ Обработка ошибок подключения и таймаутов
- ✅ Логирование запросов и ошибок
- ✅ CORS поддержка для веб-интерфейсов

## Структура проекта

```
llm-gateway/
├── main.py                         # Запуск FastAPI-приложения  
├── gateway/
│   ├── __init__.py
│   ├── routes.py                   # Обработка маршрута POST /v1/completions
│   ├── auth.py                     # Проверка API-ключей из .env
│   └── client.py                   # Проксирование запросов к серверу LLM
├── .env                            # Переменные окружения
├── requirements.txt                # Зависимости
└── README.md                       # Описание проекта
```

## Установка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Отредактируйте файл `.env`:

```env
# Список разрешённых API-ключей (разделённых запятой)
ALLOWED_API_KEYS=sk-test-key-1,sk-test-key-2,sk-prod-key-123

# URL сервера LLM для проксирования запросов
LLM_SERVER_URL=http://localhost:8080/v1/completions

# Настройки логирования
LOG_LEVEL=INFO
```

### 3. Запуск сервера

```bash
# Запуск через Python
python main.py

# Или через uvicorn
uvicorn main:app --host 0.0.0.0 --port 12000 --reload
```

Сервер будет доступен по адресу: `http://localhost:12000`

## API Endpoints

### POST /v1/completions

Основной эндпоинт для генерации текста. Проксирует запросы к серверу LLM.

**Заголовки:**
- `Authorization: Bearer <your-api-key>`
- `Content-Type: application/json`

**Пример запроса:**

```bash
curl -X POST "http://localhost:12000/v1/completions" \
  -H "Authorization: Bearer sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Привет! Как дела?",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### GET /health

Проверка состояния сервиса.

```bash
curl http://localhost:12000/health
```

### GET /

Информация о сервисе и доступных эндпоинтах.

```bash
curl http://localhost:12000/
```

## Безопасность

- API-ключи проверяются через заголовок `Authorization: Bearer <key>`
- Поддерживается несколько ключей в переменной `ALLOWED_API_KEYS`
- Все ошибки аутентификации логируются
- Чувствительная информация не выводится в логах

## Обработка ошибок

Сервис обрабатывает следующие типы ошибок:

- **401 Unauthorized** - API ключ не предоставлен
- **403 Forbidden** - Недопустимый API ключ  
- **400 Bad Request** - Ошибка в формате запроса
- **502 Bad Gateway** - Ошибка подключения к LLM серверу
- **504 Gateway Timeout** - Таймаут при обращении к LLM серверу

## Логирование

Сервис логирует:
- Входящие запросы (с маскированием API ключей)
- Ошибки подключения к LLM серверу
- HTTP ошибки и таймауты
- Успешные операции

## Разработка

### Запуск в режиме разработки

```bash
uvicorn main:app --host 0.0.0.0 --port 12000 --reload
```

### Документация API

FastAPI автоматически генерирует документацию:
- Swagger UI: `http://localhost:12000/docs`
- ReDoc: `http://localhost:12000/redoc`

## Примеры использования

### Простой запрос

```bash
curl -X POST "http://localhost:12000/v1/completions" \
  -H "Authorization: Bearer sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Напиши короткий рассказ о роботе",
    "max_tokens": 200,
    "temperature": 0.8
  }'
```

### Проверка здоровья сервиса

```bash
curl http://localhost:12000/health
```

### Получение информации о сервисе

```bash
curl http://localhost:12000/
```