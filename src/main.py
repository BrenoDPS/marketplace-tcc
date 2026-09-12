from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import close_db
from src.features.checkout.router import router as checkout_router
from src.features.home_contextual.router import router as home_router
from src.features.product_detail.router import router as product_detail_router

# Origens locais (Vite/React) liberadas apenas em desenvolvimento.
DEV_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_db()


app = FastAPI(
    title="Olist SDUI Marketplace",
    version="0.1.0",
    description="Marketplace contextual adaptativo com Server-Driven UI",
    lifespan=lifespan,
)

if settings.APP_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(home_router, prefix="/api/v1")
app.include_router(product_detail_router, prefix="/api/v1")
app.include_router(checkout_router, prefix="/api/v1")
