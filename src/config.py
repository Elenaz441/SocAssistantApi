from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GIGACHAT_API_KEY: str = None
    GIGACHAT_MODEL: str = "GigaChat-2"
    GIGACHAT_BASE_URL: str = "https://api.giga.chat/v1"

    MAX_CONCURRENT_REQUESTS: int = 2


settings = Settings()
