from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentflow"

    # Qdrant — api_key is only needed for Qdrant Cloud; leave empty for local.
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "agentflow_docs"
    qdrant_api_key: str = ""
    # Embedded on-disk Qdrant (no server/Docker). When set, takes precedence over qdrant_url.
    qdrant_path: str = ""

    # Gemini — via a local OpenAI-compatible proxy (gemini-web2api), not the real Google API.
    gemini_api_key: str = "sk-gemini"
    gemini_base_url: str = "http://127.0.0.1:8081/v1"
    gemini_model: str = "gemini-3.5-flash"
    gemini_temperature: float = 0.0
    gemini_max_tokens: int = 4096

    # Search
    tavily_api_key: str = ""

    # Mock toggles — true keeps the service mocked (no external dependency).
    use_mock_sql: bool = True
    use_mock_vector_search: bool = True
    # "fastembed" (semantic, downloads BAAI/bge-small-en-v1.5 on first use) or
    # "hash" (offline keyword-overlap embeddings, no download). Changing this
    # requires re-uploading documents: vectors from different providers are not comparable.
    embedding_provider: str = "fastembed"
    use_mock_search: bool = True

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "agentflow-ai"
    langsmith_tracing: bool = False

    # Public-demo hardening. With require_user_llm_key, visitors must bring their own
    # key (the server default is never used). With require_customer_db, the SQL agent
    # only runs against a database the visitor supplied, never the app's own database.
    require_user_llm_key: bool = False
    require_customer_db: bool = False
    # Visitor-supplied hosts (LLM base URL, database) that resolve to loopback/private
    # addresses are rejected (SSRF guard) unless this is true. Local development only.
    allow_private_hosts: bool = False

    # Read-only database with sample business data that visitors can pick in Settings
    # instead of connecting their own. Empty disables the demo option. Must be a
    # separate database from database_url so no visitor data is exposed.
    demo_database_url: str = ""

    # Every request must carry a valid X-Visitor-Id (the browser sends one). When false,
    # requests without it share one "anonymous" owner (local development, tests).
    require_visitor_id: bool = False

    # Abuse protection (per client IP, in-memory, per process).
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_query_per_minute: int = 5
    rate_limit_query_per_hour: int = 30
    rate_limit_upload_per_hour: int = 20
    rate_limit_test_per_minute: int = 10
    # Trust X-Forwarded-For for the client IP. Enable only behind a proxy you control.
    trust_proxy_headers: bool = False
    max_concurrent_runs_per_visitor: int = 2
    max_upload_mb: int = 10

    # Agent limits
    max_retry_count: int = 1
    confidence_threshold: float = 0.7


settings = Settings()
