from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.database import close_db
from src.core.redis import close_redis
from src.features.home_contextual.router import router as home_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    try:
        await close_redis()
    finally:
        await close_db()


app = FastAPI(
    title="Olist SDUI Marketplace",
    version="0.1.0",
    description="Marketplace contextual adaptativo com Server-Driven UI",
    lifespan=lifespan,
)

app.include_router(home_router, prefix="/api/v1")
