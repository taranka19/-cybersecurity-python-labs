"""Головна точка входу лабораторної роботи №2 (підкоманди demo та analyze)."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from labs.lab02.task1 import Admin, Session, UserAccount
from labs.lab02.task2 import run_analyzer


def run_demo() -> None:
    """Сценарій демонстрації виконання Завдання 1 (ООП)."""

    print("ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: МОДЕЛЬ КОРИСТУВАЧА Й СЕСІЙ БЕЗПЕКИ")

    # 1. Створення адміністратора та перевірка прав
    print("\n[1] Створення об'єкта Admin (наслідування від User):")
    admin = Admin(
        username="admin_sec",
        email="sec_lead@company.local",
        permissions={"MANAGE_USERS", "READ_LOGS"},
    )
    admin.set_password("CorrectP@ssword2026!")
    account = UserAccount(user=admin)

    print(f"Інформація про користувача: {account['user']}")
    print(f"Чи є дозвіл 'READ_LOGS': {admin.has_permission('READ_LOGS')}")
    admin.grant_permission("DROP_DB")
    print(f"Після надання 'DROP_DB': {account['user']}")

    # 2. Невдалий вхід
    print("\n[2] Спроба автентифікації з невірним паролем:")
    success_wrong = account.login("admin_sec", "WrongPassword123", "192.168.1.45")
    print(
        f"Результат login: {success_wrong} | is_authenticated(): {account.is_authenticated()}"
    )

    # 3. Успішний вхід
    print("\n[3] Спроба автентифікації з правильним паролем:")
    success_ok = account.login("admin_sec", "CorrectP@ssword2026!", "192.168.1.45")
    print(
        f"Результат login: {success_ok} | is_authenticated(): {account.is_authenticated()}"
    )
    if account["session"]:
        print(f"Сесію відкрито з IP: {account['session'].ip}")

    # 4. Валідація email через @property
    print("\n[4] Валідація зміни email через @property setter:")
    invalid_email = "invalid..mail@"
    try:
        print(f"Спроба встановити некоректний email: '{invalid_email}'")
        admin.email = invalid_email
    except ValueError as exc:
        print(f"-> Успішно перехоплено очікуваний ValueError: {exc}")

    valid_email = "sec_admin_new@cybersec.org"
    admin.email = valid_email
    print(f"-> Встановлено валідний email: {admin.email}")

    # 5. Завершення сесії за таймаутом (імітація застарілої сесії)
    print("\n[5] Перевірка таймауту сесії (SESSION_TIMEOUT_SEC = 900):")
    expired_session = Session(ip="10.10.0.1")
    expired_session.last_activity = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    account["session"] = expired_session

    print(f"Сесія застаріла. is_authenticated() повертає: {account.is_authenticated()}")

    # 6. Вихід із системи (logout)
    print("\n[6] Виконання logout():")
    account.login("admin_sec", "CorrectP@ssword2026!", "192.168.1.45")
    account.logout()
    print(f"Після виклику logout(): is_authenticated() -> {account.is_authenticated()}")

    # 7. Виведення записів AuditLog
    print("\n[7] Фінальний вміст журналу аудиту (AuditLog / @dataclass):")
    records = account["audit"].show_all()
    for idx, rec in enumerate(records, start=1):
        formatted_time = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(
            f"  {idx}. [{formatted_time}] Користувач: {rec.username:<10} | Дія: {rec.action}"
        )

    print("ДЕМОНСТРАЦІЮ ЗАВЕРШЕНО ")


def main() -> None:
    """Головний диспетчер CLI-команд."""
    parser = argparse.ArgumentParser(
        description="CLI-утиліта Лабораторної роботи №2 (Кібербезпека)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Підкоманда demo
    subparsers.add_parser("demo", help="Запуск демонстрації Завдання 1 (ООП)")

    # Підкоманда analyze (Завдання 2)
    subparsers.add_parser(
        "analyze",
        help="Запуск аудитора безпеки HTTP-заголовків (Варіант 9)",
    )

    args, extra_args = parser.parse_known_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        run_analyzer(extra_args)
    else:
        parser.print_help(sys.stderr)


if __name__ == "__main__":
    main()
