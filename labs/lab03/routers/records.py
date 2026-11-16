"""Маршрути для роботи із записами."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response, status

import labs.lab03.repository as repo
from labs.lab03.config import MAX_VALUE, MIN_VALUE
from labs.lab03.routers import integrity_to_http
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

router = APIRouter(prefix="/records", tags=["Records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису (додатне ціле)")]

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис із таким code вже існує"}}


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
    operation_id="list_records",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status_filter: Annotated[
        Status | None,
        Query(alias="status", description="Лише записи з цим статусом"),
    ] = None,
    min_value: Annotated[
        float | None,
        Query(ge=MIN_VALUE, le=MAX_VALUE, description="value >= min_value"),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Макс. кількість")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки пропустити")] = 0,
):
    """Фільтри поєднуються через AND; сортування за id зростання."""
    return repo.get_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів (атомарно)",
    operation_id="create_records_bulk",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    records: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
):
    """Додати від 1 до 100 записів: або всі, або жодного."""
    try:
        return repo.create_records_bulk([r.model_dump() for r in records])
    except sqlite3.IntegrityError as e:
        raise integrity_to_http(
            e,
            unique_detail="Дублікат code у пакеті або в базі даних.",
            fk_detail="Одна або декілька вказаних категорій не існують.",
        ) from e


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    operation_id="create_record",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(rec: RecordCreate):
    """Створити запис; неіснуюча категорія — 404, дублікат code — 409."""
    try:
        return repo.create_record(rec.model_dump())
    except sqlite3.IntegrityError as e:
        raise integrity_to_http(
            e,
            unique_detail=f"Запис із кодом '{rec.code}' вже існує.",
            fk_detail=f"Категорію з id={rec.category_id} не знайдено.",
        ) from e


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за id",
    operation_id="get_record",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId):
    """Повернути один запис."""
    rec = repo.get_record_by_id(record_id)
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено."
        )
    return rec


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    operation_id="replace_record",
    responses={**NOT_FOUND, **CONFLICT},
)
def update_record(record_id: RecordId, rec: RecordReplace):
    """Замінити всі змінювані поля; id не змінюється."""
    try:
        updated = repo.update_record(record_id, rec.model_dump())
    except sqlite3.IntegrityError as e:
        raise integrity_to_http(
            e,
            unique_detail=f"Запис із кодом '{rec.code}' вже існує.",
            fk_detail=f"Категорію з id={rec.category_id} не знайдено.",
        ) from e
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено."
        )
    return updated


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    operation_id="delete_record",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId):
    """Видалити запис; відповідь без тіла."""
    if not repo.delete_record(record_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
