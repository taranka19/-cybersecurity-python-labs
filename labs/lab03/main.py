"""Головна точка входу FastAPI-застосунку."""

from contextlib import asynccontextmanager
import logging
import sqlite3

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from labs.lab03.schemas import StudentRead
from shared.student import get_student_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Створити відсутні таблиці під час запуску (дані не змінюються)."""
    initialize_database()
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
    """Технічну помилку записати в лог, клієнту дати загальне повідомлення."""
    logger.error("Помилка SQLite: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера."},
    )


@app.get("/ping", tags=["System"], summary="Перевірка доступності API")
def ping():
    """Повернути {"status": "ok"}."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["System"],
    summary="Дані студента",
)
def student_info():
    """Повернути ПІБ, групу та номер варіанта з shared/student.py."""
    info = get_student_info()
    return {
        "student_name": info.get("name"),
        "group_name": info.get("group"),
        "variant_number": info.get("variant"),
    }
