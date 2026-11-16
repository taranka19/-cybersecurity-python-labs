"""Початкове заповнення бази з data/seed.json."""

from contextlib import closing
import json
import logging
import sqlite3
import sys

from labs.lab03.database import BASE_DIR, get_connection, initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

logger = logging.getLogger(__name__)
SEED_FILE = BASE_DIR / "data" / "seed.json"


def load_seed() -> tuple[list[dict], list[dict]]:
    """Прочитати seed.json і перевірити дані моделями Pydantic."""
    with open(SEED_FILE, encoding="utf-8") as f:
        data = json.load(f)

    categories = data["categories"]
    records = data["records"]

    for cat in categories:
        CategoryCreate(name=cat["name"])
        if not isinstance(cat["id"], int) or cat["id"] <= 0:
            raise ValueError(f"Некоректний id категорії: {cat['id']!r}")
    for rec in records:
        RecordCreate(**rec)

    category_ids = {cat["id"] for cat in categories}
    if any(rec["category_id"] not in category_ids for rec in records):
        raise ValueError("Запис посилається на неіснуючу категорію")
    return categories, records


def seed_data() -> int:
    """Заповнити порожню базу в одній транзакції; повернути код завершення."""
    initialize_database()

    try:
        categories, records = load_seed()
    except (OSError, KeyError, TypeError, ValueError) as e:
        print(f"Некоректні початкові дані: {e}")
        return 1

    with closing(get_connection()) as conn:
        try:
            with conn:
                total = conn.execute(
                    "SELECT (SELECT COUNT(*) FROM categories)"
                    " + (SELECT COUNT(*) FROM records)"
                ).fetchone()[0]
                if total > 0:
                    print(
                        "База вже містить дані. Заповнення пропущено, дані не змінено."
                    )
                    return 0

                conn.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c["id"], c["name"]) for c in categories],
                )
                conn.executemany(
                    "INSERT INTO records (code, title, category_id, value, status)"
                    " VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            r["code"],
                            r["title"],
                            r["category_id"],
                            r["value"],
                            r["status"],
                        )
                        for r in records
                    ],
                )
        except sqlite3.Error as e:
            logger.error("Помилка заповнення бази даних: %s", e)
            print("Помилка при додаванні даних. Усі зміни скасовано.")
            return 1

    print(f"Успішно додано {len(categories)} категорій та {len(records)} записів.")
    return 0


if __name__ == "__main__":
    sys.exit(seed_data())
