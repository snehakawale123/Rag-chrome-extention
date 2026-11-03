
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(request: ChatRequest):
    result = answer_question(request.question)
    return result