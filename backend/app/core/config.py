from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/smartlawer"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "supersecretkey-dev-replace-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
