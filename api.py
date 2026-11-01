"""A porta pra outro sistema chamar o assistente.

    uvicorn api:app --port 8000
    POST /ask  {"question": "..."}  ->  {"answer": "...", "sources": [...], "passages": [...]}
"""
from fastapi import FastAPI
from pydantic import BaseModel

from rag import responder

app = FastAPI(title="tax-rag", description="国税庁タックスアンサー（確定申告）に基づく質問応答")


class Pergunta(BaseModel):
    question: str
    k: int = 5


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(p: Pergunta):
    r = responder(p.question, p.k)
    return {
        "answer": r["resposta"],
        "sources": r["fontes"],
        "passages": [{"id": t["id"], "title": t["title"], "url": t["url"], "score": round(t["score"], 3)}
                     for t in r["trechos"]],
    }
