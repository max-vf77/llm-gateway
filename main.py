from fastapi import FastAPI
from gateway.routes import router

app = FastAPI(title="LLM Gateway")

# Подключение маршрутов
app.include_router(router, prefix="/api")