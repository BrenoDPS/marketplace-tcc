from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/olist"

    # Cache de resposta SDUI. Desligado por padrao: ele e VARIAVEL DE
    # EXPERIMENTO (ver src/core/cache.py), e a aplicacao tem de continuar
    # correta sem ele. Frio x aquecido se faz com FLUSHALL, nao com flag.
    CACHE_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    # 60 s: um ensaio de plateau dura 5 a 15 min, entao o TTL nao expira no meio
    # e nao mascara a condicao "aquecida".
    CACHE_TTL_SECONDS: int = 60


settings = Settings()
