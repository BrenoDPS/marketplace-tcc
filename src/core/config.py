from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DEBUG: bool = True
    # Log de cada SQL executado. Separado do DEBUG de proposito: atrelado a ele,
    # o echo contaminou TODAS as medicoes de carga ate a Sprint 7 sem ninguem
    # notar (docs/performance.md §9). Ligue so para depurar consulta.
    SQL_ECHO: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/olist"

    # Cache de resposta SDUI. LIGADO por padrao desde a Sprint 8: o protocolo
    # da §3.3 mostrou que, com 1 worker, e ele que cumpre a meta de 200 ms a
    # partir de 250 usuarios (docs/performance.md §11.7). A aplicacao continua
    # correta com ele desligado — e assim que a suite de testes roda.
    CACHE_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    # 1 h: o catalogo so muda quando o ETL roda. Depois de recarregar o ETL com a
    # API no ar, esvaziar o cache (FLUSHALL) — senao a Home serve a amostra antiga
    # ate a chave expirar. Foi o TTL usado no protocolo.
    CACHE_TTL_SECONDS: int = 3600


settings = Settings()
