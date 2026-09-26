from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/smartlawer"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )
    SKIP_STARTUP_MIGRATIONS: bool = False
    SECRET_KEY: str = "supersecretkey-dev-replace-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    AI_PROVIDER: str = "openai" # 'openai', 'openrouter' or 'gemini'
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_MODEL_VERSION: str = "v1"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_BATCH_SIZE: int = 64
    DOCLING_ENABLED: bool = False
    RETRIEVAL_CANDIDATE_K: int = 30
    RETRIEVAL_TOP_K: int = 6
    RRF_K: int = 60
    # V2 T13: limites operacionais configuráveis (§17).
    MAX_UPLOAD_MB: int = 50
    MAX_PDF_PAGES: int = 500
    # V2 T05: orçamento de contexto do planejamento de cobertura (§6.1/§17).
    PROMPT_BUDGET_TOKENS: int = 30000
    COVERAGE_MAX_BATCH_TOKENS: int = 8000
    COVERAGE_OVERLAP_BLOCKS: int = 2
    COVERAGE_MAX_BATCHES: int = 20
    RERANK_ENABLED: bool = False
    COHERE_API_KEY: str = ""
    COHERE_RERANK_MODEL: str = "rerank-3"
    CHAT_MODEL: str = "gpt-4-turbo"
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GENERATED_KEEP_LATEST: int = 10
    PRECEDENTS_AUTO_SEED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
