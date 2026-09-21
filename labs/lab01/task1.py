"""Завдання 1: Комплексний аналізатор надійності паролів."""

import random

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

SPECIAL_CHARACTERS = set("!@#$%^&*()-_=+[]{}|;:,.<>?/~`")

passwords = [
    "Digital@F0r3nsics",
    "plain",
    "Encrypt10n@Key",
    "member",
    "Security@Audit2023",
    "regular",
    "Hack3r@D3fense",
    "ordinary",
    "Threat@Intel",
    "usual",
]
criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}
forbidden_passwords = {"plain", "member", "regular", "ordinary", "usual", "user"}


def check_criteria(pwd: str) -> dict[str, bool]:
    """Перевіряє наявність категорій символів."""
    return {
        "digit": any(c.isdigit() for c in pwd),
        "upper": any(c.isupper() for c in pwd),
        "lower": any(c.islower() for c in pwd),
        "special": any(c in SPECIAL_CHARACTERS for c in pwd),
    }


def get_strength(pwd: str, all_pwds: list[str]) -> str:
    """Визначає надійність пароля за правилами завдання."""
    if pwd.lower() in forbidden_passwords or len(pwd) < criteria["min_length"]:
        return "Заборонений"

    matches = check_criteria(pwd)
    has_all = (
        len(pwd) >= criteria["min_length"]
        and matches["digit"]
        and matches["upper"]
        and matches["special"]
    )
    is_unique = all_pwds.count(pwd) == 1

    if has_all and len(pwd) >= criteria["min_length"] + 4 and is_unique:
        return "Дуже сильний"

    if has_all and len(pwd) < criteria["min_length"] + 4:
        return "Сильний"

    has_any = (
        matches["digit"] or matches["upper"] or matches["lower"] or matches["special"]
    )

    if len(pwd) >= criteria["min_length"] and has_any:
        return "Середній"

    if has_any:
        return "Слабкий"

    return "Заборонений"


def run_task1() -> None:
    """Виконує дублювання паролів та виводить таблицю аналізу."""
    duplicated_passwords = passwords.copy()
    for _ in range(3):
        random_index = random.randint(0, len(passwords) - 1)
        duplicated_passwords.append(passwords[random_index])

    print(f"Студент: {STUDENT_NAME}  Група: {GROUP_NAME}  Варіант: {VARIANT_NUMBER}")
    print(f"{'№':<3}  {'Пароль':<20}  {'Довжина':<8}  {'Оцінка надійності':<16}")

    for index, pwd in enumerate(duplicated_passwords, start=1):
        status = get_strength(pwd, duplicated_passwords)
        print(f"{index:<3} | {pwd:<20} | {len(pwd):<8} | {status:<16}")


if __name__ == "__main__":
    run_task1()
