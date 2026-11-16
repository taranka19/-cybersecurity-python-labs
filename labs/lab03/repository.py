"""Шар доступу до даних: параметризовані SQL-запити без залежності від FastAPI."""

from contextlib import closing
import sqlite3
from typing import Any

from labs.lab03.database import get_connection

RECORD_SELECT = """
    SELECT r.id, r.code, r.title, r.category_id, r.value, r.status,
           c.name AS category_name
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""


def _connect() -> sqlite3.Connection:
    """Відкрити з'єднання, що повертає рядки як sqlite3.Row."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _fetch_record(conn: sqlite3.Connection, record_id: int) -> dict[str, Any] | None:
    """Прочитати запис з JOIN у межах наявного з'єднання."""
    row = conn.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


def _insert_record(conn: sqlite3.Connection, data: dict[str, Any]) -> int:
    """Додати запис без commit; повернути id."""
    cursor = conn.execute(
        "INSERT INTO records (code, title, category_id, value, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            data["code"],
            data["title"],
            data["category_id"],
            data["value"],
            data["status"],
        ),
    )
    return cursor.lastrowid


def create_category(name: str) -> dict[str, Any]:
    """Створити категорію."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        return {"id": cursor.lastrowid, "name": name}


def get_categories() -> list[dict[str, Any]]:
    """Список категорій за зростанням id."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT id, name FROM categories ORDER BY id ASC")
        return [dict(row) for row in rows.fetchall()]


def delete_category(category_id: int) -> bool:
    """Видалити категорію; False, якщо її немає. Непорожня дає IntegrityError."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        return cursor.rowcount > 0


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Додати запис і повернути його разом з category_name."""
    with closing(_connect()) as conn, conn:
        return _fetch_record(conn, _insert_record(conn, data))


def get_record_by_id(record_id: int) -> dict[str, Any] | None:
    """Отримати запис за id або None."""
    with closing(_connect()) as conn:
        return _fetch_record(conn, record_id)


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Записи з фільтрами (AND), сортування за id зростання."""
    conditions: list[str] = []
    params: list[Any] = []
    # SQL-фрагменти фіксовані в коді, значення передаються лише параметрами.
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    query = RECORD_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_connect()) as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def update_record(record_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Повністю замінити змінювані поля; None, якщо запису немає."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE records SET code = ?, title = ?, category_id = ?, "
            "value = ?, status = ? WHERE id = ?",
            (
                data["code"],
                data["title"],
                data["category_id"],
                data["value"],
                data["status"],
                record_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        return _fetch_record(conn, record_id)


def delete_record(record_id: int) -> bool:
    """Видалити запис; False, якщо його немає."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        return cursor.rowcount > 0


def create_records_bulk(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Додати пакет в одній транзакції: або всі записи, або жодного."""
    with closing(_connect()) as conn, conn:
        ids = [_insert_record(conn, rec) for rec in records]
        return [_fetch_record(conn, record_id) for record_id in ids]
