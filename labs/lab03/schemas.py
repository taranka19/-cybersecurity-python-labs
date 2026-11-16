"""Pydantic-моделі запитів і відповідей."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import MAX_VALUE, MIN_VALUE

Status = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Тіло запиту для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40, description="Назва категорії")


class CategoryRead(CategoryCreate):
    """Категорія у відповіді."""

    id: int = Field(gt=0, description="Ідентифікатор категорії")


class RecordCreate(BaseModel):
    """Тіло запиту для створення запису (без id)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40, description="Унікальний код")
    title: str = Field(min_length=3, max_length=120, description="Назва знахідки")
    category_id: int = Field(gt=0, description="Ідентифікатор категорії")
    value: float = Field(
        ge=MIN_VALUE,
        le=MAX_VALUE,
        allow_inf_nan=False,
        description="Оцінка ризику (score), від 0 до 10 включно",
    )
    status: Status = Field(description="Стан опрацювання")


class RecordReplace(RecordCreate):
    """Тіло PUT: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді разом з id і назвою категорії."""

    id: int = Field(gt=0, description="Ідентифікатор запису")
    category_name: str = Field(description="Назва категорії")


class StudentRead(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int
