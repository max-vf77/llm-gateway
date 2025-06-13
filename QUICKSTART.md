# Быстрый старт LLM Gateway

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка переменных окружения
Отредактируйте файл `.env`:
```env
ALLOWED_API_KEYS=sk-test-key-1,sk-test-key-2,sk-prod-key-123
LLM_SERVER_URL=http://localhost:8080/v1/completions
```

## 3. Запуск сервера
```bash
python main.py
```

## 4. Тестирование
```bash
# Проверка состояния
curl http://localhost:12000/health

# Тест с API ключом
curl -X POST "http://localhost:12000/v1/completions" \
  -H "Authorization: Bearer sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 10}'
```

## 5. Документация API
- Swagger UI: http://localhost:12000/docs
- ReDoc: http://localhost:12000/redoc

## 6. Автоматическое тестирование
```bash
./test_examples.sh
```