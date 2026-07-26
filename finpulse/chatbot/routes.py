"""
chatbot/routes.py

Exposes the LangGraph chatbot as a REST endpoint: POST /chat
"""

from fastapi import APIRouter
from pydantic import BaseModel

from chatbot.agent import ask_finpulse_bot

router = APIRouter(tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = ask_finpulse_bot(request.message)
    return {"reply": reply}
