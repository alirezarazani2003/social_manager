from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="AI Chat Service")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable is required!")


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "x-ai/grok-4.1-fast"


class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    try:
        messages = [{
            "role": "system",
            "content": (
                "شما یک دستیار هوشمند فارسی‌زبان هستید. "
                "فقط به زبان فارسی پاسخ دهید. "
                "هرگز اطلاعات ساختگی، نام نویسنده یا لینک کتاب واقعی نسازید. "
                "اگر اطلاعاتی ندارید، صادقانه بگویید که نمی‌دانید."
            )
        }]
        if request.history:
            for msg in request.history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        messages.append({
            "role": "user",
            "content": request.message
        })

        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": messages
            },
            timeout=60,
            proxies={"http": None, "https": None}
        )

        if response.status_code != 200:
            try:
                error_msg = response.json().get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text or "Unknown OpenRouter error"
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter error: {error_msg}"
            )

        ai_reply = response.json()["choices"][0]["message"]["content"]
        return ChatResponse(response=ai_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
