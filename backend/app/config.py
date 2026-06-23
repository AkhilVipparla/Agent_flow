from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentflow"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "agentflow_docs"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.0
    groq_max_tokens: int = 4096

    # Search
    tavily_api_key: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "agentflow-ai"
    langsmith_tracing: bool = False

    # Agent limits
    max_retry_count: int = 2
    confidence_threshold: float = 0.7


settings = Settings()
