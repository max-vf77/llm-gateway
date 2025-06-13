#!/bin/bash

# Примеры тестирования LLM Gateway API

echo "=== Тестирование LLM Gateway ==="
echo

# Базовый URL
BASE_URL="http://localhost:12000"

echo "1. Проверка состояния сервиса:"
curl -s "$BASE_URL/health" | jq .
echo

echo "2. Получение информации о сервисе:"
curl -s "$BASE_URL/" | jq .
echo

echo "3. Тест без API ключа (должен вернуть 403):"
curl -s -X POST "$BASE_URL/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 10}' | jq .
echo

echo "4. Тест с неверным API ключом (должен вернуть 403):"
curl -s -X POST "$BASE_URL/v1/completions" \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 10}' | jq .
echo

echo "5. Тест с валидным API ключом (попытка подключения к LLM серверу):"
curl -s -X POST "$BASE_URL/v1/completions" \
  -H "Authorization: Bearer sk-test-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Напиши короткий рассказ о роботе",
    "max_tokens": 200,
    "temperature": 0.8
  }' | jq .
echo

echo "=== Тестирование завершено ==="