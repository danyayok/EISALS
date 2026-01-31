import uvicorn

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from starlette.responses import JSONResponse

from app.templates import templates
# from app.database import engine, Base
from app.routers.v1 import auth_pages, pages #, profile, tenders, analytics
from app.config import settings
# from app.parsers.eis_parser import EISParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Создание таблиц БД...")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    logger.info("Запуск парсера ЕИС...")
    # сюда закидывать всякие задачки и прочее


    yield

    logger.info("Остановка приложения...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # сюда домен в деве пофиг а так для безопасности только домен свой
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
# app.include_router(auth.router)
# app.include_router(profile.router)
# app.include_router(tenders.router)



@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "main backend",
        "version": settings.PROJECT_VERSION
    }


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found"}
    )


if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )