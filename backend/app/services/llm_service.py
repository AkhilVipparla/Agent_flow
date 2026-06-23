from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
    )
