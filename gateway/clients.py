import os
import httpx
from dotenv import load_dotenv

load_dotenv()

LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:12000/v1/chat/completions")

async def forward_to_llm(request_data: dict) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LLM_SERVER_URL, json=request_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": f"Ошибка при обращении к LLM-серверу: {str(e)}"}