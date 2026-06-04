from fastapi import APIRouter
from pydantic import BaseModel
from src.brain import route_question

router = APIRouter()

class Query(BaseModel):
    question: str
    mode: str = "full"

@router.post("/ask")
def ask(q: Query):
    print(f"[API] Incoming question: {q.question}")
    
    response = route_question(q.question)
    
    print(f"[API] Outgoing response: {response} | Type: {type(response)}")

    return {"response": response}
