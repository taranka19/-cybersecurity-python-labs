"""Завдання 1: Модель користувача, облікового запису та сесій безпеки."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

# Константа кількості ітерацій для PBKDF2
PBKDF2_ITERATIONS = 100_000

# Регулярний вираз для валідації email згідно з вимогами методички:
# - локальна частина починається з латинської літери;
# - загальна довжина локальної частини 3–64 символи (літери, цифри, _);
# - символ @;
# - доменне ім'я з принаймні однією крапкою.
EMAIL_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class User:
    """Базовий клас облікового запису користувача."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "user",
        active: bool = True,
    ) -> None:
        self.username = username
        self.role = role
        self.active = active

        self.__email: str = ""
        self.email = email  # Валідація через @property setter

        # Приватні поля для зберігання солі та хешу пароля
        self.__password_salt: bytes = b""
        self.__password_hash: bytes = b""

    @property
    def email(self) -> str:
        """Гетер для отримання email."""
        return self.__email

    @email.setter
    def email(self, new_email: str) -> None:
        """Сетер email із валідацією регулярним виразом."""
        if not EMAIL_REGEX.match(new_email):
            raise ValueError(f"Некоректний формат email: '{new_email}'")
        self.__email = new_email

    def set_password(self, password: str) -> None:
        """Безпечне збереження пароля через PBKDF2-HMAC-SHA256 з випадковою сіллю."""
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        """Перевірка пароля із захистом від timing attacks (hmac.compare_digest)."""
        if not self.__password_hash or not self.__password_salt:
            return False

        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, computed_hash)

    def deactivate(self) -> None:
        """Деактивація користувача."""
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}', status='{status}')"


class Admin(User):
    """Клас адміністратора, що наслідує User і має додаткові привілеї."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions: set[str] | list[str] | None = None,
    ) -> None:
        # Виклик батьківського конструктора через super()
        super().__init__(username=username, email=email, role=role, active=active)
        # Уникнення змінюваних аргументів за замовчуванням
        self.permissions: set[str] = (
            set(permissions) if permissions is not None else set()
        )

    def grant_permission(self, permission: str) -> None:
        """Надання нового дозволу."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Відкликання дозволу."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевірка наявності дозволу."""
        return permission in self.permissions

    def __str__(self) -> str:
        perms_str = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return f"{super().__str__()} | Permissions: [{perms_str}]"


class Session:
    """Облік активної сесії користувача у часовому поясі UTC."""

    def __init__(self, ip: str) -> None:
        self.ip = ip
        now_utc = datetime.now(timezone.utc)
        self.login_time = now_utc
        self.last_activity = now_utc

    def touch(self) -> None:
        """Оновлення мітки останньої активності."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевірка дійсності сесії з валідацією позитивного таймауту."""
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути строго більшим за 0.")
        now_utc = datetime.now(timezone.utc)
        return (now_utc - self.last_activity) <= timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Незмінний запис журналу аудиту подій безпеки."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал аудиту для фіксації подій безпеки."""

    def __init__(self) -> None:
        self.logs: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        """Додавання події з поточним часом UTC (паролі не записуються)."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.logs.append(record)

    def show_all(self) -> list[AuditRecord]:
        """Отримання всіх записів аудиту."""
        return list(self.logs)


class UserAccount:
    """Клас композиції (User + Session + AuditLog) зі спеціальними методами доступу."""

    SESSION_TIMEOUT_SEC = 900

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.user = user
        self.session = session
        self.audit = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Автентифікація користувача з перевіркою активності та пароля."""
        if self.user.username != username or not self.user.active:
            self.audit.add_log(username, "login_failure")
            return False

        if self.user.check_password(password):
            self.session = Session(ip=ip)
            self.session.touch()
            self.audit.add_log(username, "login_success")
            return True

        self.audit.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        """Перевірка автентифікації без подовження активності."""
        if self.session is None:
            return False
        return self.session.is_active(self.SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        """Завершення поточної сесії та фіксація події в аудиті."""
        if self.session is not None:
            self.session = None
            self.audit.add_log(self.user.username, "logout")

    def __getitem__(self, key: str) -> Any:
        """Безпечний доступ до дозволених компонентів об'єкта."""
        if key == "user":
            return self.user
        if key == "session":
            return self.session
        if key == "audit":
            return self.audit
        raise KeyError(f"Невідомий або недоступний ключ: '{key}'")

    def __setitem__(self, key: str, value: Any) -> None:
        """Оновлення компонентів із валідацією типів (заборона доступу до хешів)."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' повинно бути екземпляром User")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' повинно бути Session або None")
            self.session = value
        elif key == "audit":
            if not isinstance(value, AuditLog):
                raise TypeError("Значення для 'audit' повинно бути AuditLog")
            self.audit = value
        else:
            raise KeyError(f"Заборонено змінювати або невідомий атрибут: '{key}'")
