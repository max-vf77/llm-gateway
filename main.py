from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gateway.routes import router

# Создание FastAPI приложения
app = FastAPI(
    title="LLM Gateway",
    description="Шлюз для проксирования запросов к серверу инференса LLM",
    version="1.0.0"
)

# Настройка CORS для работы с веб-интерфейсами
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12000)