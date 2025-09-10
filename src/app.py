import os
from fastapi import FastAPI
from pydantic import BaseModel

from .modules.rag import RAGService

app = FastAPI(title="AI Brand Services")
rag = RAGService()  # загрузит/построит индекс при старте

class AskIn(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/seed")
def seed():
    rag.seed()
    return {"status": "ok", "message": "Демо-FAQ добавлены и проиндексированы."}

@app.post("/ask")
def ask(payload: AskIn):
    answer = rag.ask(payload.question)
    return {"answer": answer}
