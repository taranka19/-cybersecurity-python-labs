"""Маршрути для роботи з категоріями."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status

import labs.lab03.repository as repo
from labs.lab03.routers import integrity_to_http
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
    operation_id="list_categories",
)
def list_categories():
    """Повернути всі категорії за зростанням id."""
    return repo.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    operation_id="create_category",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(cat: CategoryCreate):
    """Створити категорію; повторна назва повертає 409."""
    try:
        return repo.create_category(cat.name)
    except sqlite3.IntegrityError as e:
        raise integrity_to_http(
            e,
            unique_detail=f"Категорія з назвою '{cat.name}' вже існує.",
            fk_detail="Некоректне посилання.",
        ) from e


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    operation_id="delete_category",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(
    category_id: Annotated[
        int, Path(gt=0, description="Ідентифікатор категорії (додатне ціле)")
    ],
):
    """Видалити категорію без записів; інакше 409."""
    try:
        deleted = repo.delete_category(category_id)
    except sqlite3.IntegrityError as e:
        raise integrity_to_http(
            e,
            unique_detail="Неможливо видалити категорію.",
            fk_detail="Неможливо видалити категорію, яка містить пов'язані записи.",
            fk_status=status.HTTP_409_CONFLICT,
        ) from e
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
