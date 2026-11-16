"""Маршрути API та спільне перетворення помилок SQLite на HTTP-помилки."""

import logging
import sqlite3

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def integrity_to_http(
    exc: sqlite3.IntegrityError,
    *,
    unique_detail: str,
    fk_detail: str,
    fk_status: int = status.HTTP_404_NOT_FOUND,
) -> HTTPException:
    """Розрізнити дублікат (409), зовнішній ключ і порушення інших обмежень (422)."""
    message = str(exc).upper()
    if "UNIQUE" in message:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=unique_detail)
    if "FOREIGN KEY" in message:
        return HTTPException(status_code=fk_status, detail=fk_detail)
    logger.error("Порушення обмеження бази даних: %s", exc)
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Дані порушують обмеження бази даних.",
    )
