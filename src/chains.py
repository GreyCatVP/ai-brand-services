# src/chains.py
import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()
MODEL    = os.getenv("LLM_MODEL", "qwen/qwen-2.5-7b-instruct")

def _build_llm() -> ChatOpenAI:
    kwargs = dict(model=MODEL, temperature=0.2, timeout=60)
    if PROVIDER == "openrouter":
        return ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            **kwargs
        )
    elif PROVIDER == "openai":
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER: {PROVIDER}")

def _format_context(hits: List[Dict], max_chars: int = 5000) -> str:
    pieces, total = [], 0
    for i, h in enumerate(hits, 1):
        block = f"[{i}] Источник: {h['source']}\n{h['text'].strip()}\n"
        if total + len(block) > max_chars:
            break
        pieces.append(block); total += len(block)
    return "\n---\n".join(pieces) if pieces else "—"

def rag_answer(question: str, hits: List[Dict]) -> str:
    llm = _build_llm()
    context = _format_context(hits)
    sys = SystemMessage(content=(
        "Ты корпоративный ассистент. Отвечай кратко и по делу."
        " Используй КОНТЕКСТ ниже как единственный источник правды."
        " Если ответа нет в контексте — честно скажи об этом."
        " В конце добавь «Цитаты: [n] <имя файла>» по использованным фрагментам."
    ))
    usr = HumanMessage(content=(
        f"Вопрос: {question}\n\n"
        f"КОНТЕКСТ:\n{context}\n\n"
        "Дай ответ в 3–6 предложениях."
    ))
    resp = llm.invoke([sys, usr])
    return getattr(resp, "content", str(resp)).strip()
