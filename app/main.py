import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine
from app.core.tasks import collect_tenders_once, hourly_parser
from app.routers.v1 import auth, pages, tenders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Создание таблиц БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Первичная загрузка тендеров ЕИС...")
    await collect_tenders_once(pages=2)

    logger.info("Запуск фонового парсера ЕИС...")
    task = asyncio.create_task(hourly_parser())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Фоновая задача парсинга остановлена")

    logger.info("Остановка приложения...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://eisals.ru", "http://eisals.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["eisals.ru", "www.eisals.ru", "localhost", "127.0.0.1"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "upgrade-insecure-requests; default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'"
    )
    return response


app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(tenders.router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "main backend",
        "version": settings.PROJECT_VERSION,
    }


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
