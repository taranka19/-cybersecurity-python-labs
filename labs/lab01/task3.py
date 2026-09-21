"""Завдання 3: Хешування, CSV-база та JSON-логування з винятками."""

import csv
import functools
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
CSV_FILE_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_FILE_PATH = os.path.join(DATA_DIR, "log.json")

MIN_PASSWORD_LENGTH = 13
HASH_SALT = str(VARIANT_NUMBER).zfill(5)


class ValidationError(Exception):
    """Власний виняток для валідації довжини пароля."""


def log_event(func):
    """Декоратор для фіксації подій у JSON-журналі."""

    @functools.wraps(func)
    def wrapper(username: str, password: str, *args, **kwargs):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_success = False
        try:
            result = func(username, password, *args, **kwargs)
            is_success = bool(result)
            return result
        finally:
            log_record = {
                "event": "login",
                "user": username,
                "result": "success" if is_success else "failure",
                "timestamp": timestamp,
                "args": [username, "***"],
                "kwargs": kwargs,
            }
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                history = []
                if os.path.exists(LOG_FILE_PATH):
                    with open(LOG_FILE_PATH, "r", encoding="utf-8") as file:
                        try:
                            history = json.load(file)
                        except json.JSONDecodeError:
                            history = []
                history.append(log_record)
                with open(LOG_FILE_PATH, "w", encoding="utf-8") as file:
                    json.dump(history, file, indent=4, ensure_ascii=False)
            except (IOError, OSError, PermissionError) as exc:
                print(f"[Помилка логування]: {exc}")

    return wrapper


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує хеш SHA-224 від конкатенації пароля та солі."""
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль занадто короткий. Мінімум {MIN_PASSWORD_LENGTH} символів."
        )

    salted_string = (password + salt).encode("utf-8")
    return hashlib.sha224(salted_string).hexdigest()


def create_user(username: str, password: str) -> tuple[str, str]:
    """Створює запис користувача з персональною сіллю"""
    return username, generate_hash(password, HASH_SALT)


def create_users(users_list: tuple[tuple[str, str], ...]) -> bool:
    """Записує список користувачів у файл data/users.csv з відловом винятків"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["username", "password_hash"])
            for username, raw_password in users_list:
                _, pwd_hash = create_user(username, raw_password)
                writer.writerow([username, pwd_hash])
        return True
    except (ValidationError, ValueError) as val_err:
        print(f"[Помилка валідації при створенні бази]: {val_err}")
    except (IOError, OSError, PermissionError) as file_err:
        print(f"[Помилка запису файлу бази]: {file_err}")
    return False


def read_users_db() -> list[dict[str, str]]:
    """Зчитує базу користувачів із CSV-файлу з відловом винятків."""
    users_db: list[dict[str, str]] = []
    try:
        if not os.path.exists(CSV_FILE_PATH):
            raise FileNotFoundError(f"Файл бази даних {CSV_FILE_PATH} не знайдено.")

        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                users_db.append(row)
    except (FileNotFoundError, IOError, OSError, PermissionError) as file_err:
        print(f"[Помилка зчитування бази користувачів]: {file_err}")
    return users_db


@log_event
def login(username: str, password: str) -> bool:
    """Перевіряє автентифікацію з обробкою винятків валідації."""
    try:
        if not username or not password:
            raise ValueError("Логін та пароль не можуть бути порожніми.")

        users_db = read_users_db()
        target_hash = generate_hash(password, HASH_SALT)
        for record in users_db:
            if (
                record["username"] == username
                and record["password_hash"] == target_hash
            ):
                return True
    except (ValidationError, ValueError) as val_err:
        print(f"[Помилка валідації при вході користувача {username}]: {val_err}")
    return False


users_to_register = (
    ("cloud_admin", "Secur3Pass2026!"),
    ("soc_analyst", "SOCAnalystPass#1"),
    ("threat_hunter", "HuntingThreats!9"),
    ("crypto_guru", "Sha224StrongKey_"),
    ("net_sentinel", "NetworkGuard2026"),
    ("audit_expert", "AuditReportPass9"),
    ("incident_mgr", "IncidentTeam123!"),
    ("cloud_master", "CloudStorageKey9"),
    ("forensic_cop", "EvidenceLockPass"),
    ("pentest_user", "PenetrationLab9!"),
)


def main() -> None:
    
    print("1. Формування CSV-бази користувачів")
    if create_users(users_to_register):
        print(f"Базу збережено у: {CSV_FILE_PATH}")

    print("\n2. Зчитування вмісту CSV-файлу:")
    users_db = read_users_db()
    if users_db:
        print(f"{'№':<3} | {'Username':<18} | {'SHA-224 Hash'}")
        for idx, entry in enumerate(users_db, start=1):
            print(f"{idx:<3} | {entry['username']:<18} | {entry['password_hash']}")

    print("\n3. Тестування автентифікації:")
    # Успішна авторизація
    user_ok = "cloud_admin"
    pass_ok = "Secur3Pass2026!"
    res_ok = login(user_ok, pass_ok)
    print(f"Вхід [{user_ok}] з вірним паролем: {'УСПІШНО' if res_ok else 'ВІДХИЛЕНО'}")

    # Неуспішна авторизація (невірний хеш)
    pass_bad = "WrongPassword_123!"
    res_bad = login(user_ok, pass_bad)
    print(f"Вхід [{user_ok}] з хибним паролем: {'УСПІШНО' if res_bad else 'ВІДХИЛЕНО'}")

    # Неуспішна авторизація (занадто короткий пароль)
    pass_short = "Short123!"
    res_short = login(user_ok, pass_short)
    print(
        f"Вхід [{user_ok}] з коротким паролем: {'УСПІШНО' if res_short else 'ВІДХИЛЕНО'}"
    )

    print(f"\nПодії авторизації зафіксовано у: {LOG_FILE_PATH}")


run_task3 = main

if __name__ == "__main__":
    main()
