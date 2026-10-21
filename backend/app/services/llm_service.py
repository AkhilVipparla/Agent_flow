from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.request_context import LLMCredentials, llm_config_error, llm_credentials


class LLMNotConfiguredError(RuntimeError):
    """Raised when no LLM credentials are available for the current request."""


@lru_cache(maxsize=1)
def _default_llm() -> ChatOpenAI:
    """Server-side default: Gemini via a local OpenAI-compatible proxy (gemini-web2api).

    The proxy ignores `tools`/`tool_choice` (it scrapes Gemini's web UI, which has
    no function-calling concept), so structured output must use `method="json_mode"`
    everywhere instead of the default tool-calling strategy — see each agent's
    `with_structured_output(..., method="json_mode")` call.
    """
    return ChatOpenAI(
        api_key=settings.gemini_api_key,
        base_url=settings.gemini_base_url,
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_tokens,
        timeout=120,
        max_retries=1,
    )


@lru_cache(maxsize=16)
def _user_llm(creds: LLMCredentials) -> ChatOpenAI:
    # Any OpenAI-compatible endpoint. Small cache: clients are cheap, and we
    # don't want to hold many visitors' keys in memory.
    return ChatOpenAI(
        api_key=creds.api_key,
        base_url=creds.base_url,
        model=creds.model,
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_tokens,
        timeout=60,
        # Free-tier keys are metered per minute. The client honours the provider's
        # retry-after hint, so a few retries ride out a rate limit instead of failing a step.
        max_retries=5,
    )


def llm_unavailable_reason() -> str | None:
    """Why research can't start for this request, or None if an LLM is available."""
    if llm_credentials.get() is not None:
        return None
    problem = llm_config_error.get()
    if problem:
        return problem
    if settings.require_user_llm_key:
        return "Add your LLM API key in Settings to run research."
    return None


def get_llm() -> ChatOpenAI:
    """The visitor's own LLM if they supplied credentials, else the server default."""
    creds = llm_credentials.get()
    if creds is not None:
        return _user_llm(creds)
    problem = llm_config_error.get()
    if problem:
        raise LLMNotConfiguredError(problem)
    if settings.require_user_llm_key:
        raise LLMNotConfiguredError("Add your LLM API key in Settings to run research.")
    return _default_llm()
