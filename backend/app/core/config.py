from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/smartlawer"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
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
