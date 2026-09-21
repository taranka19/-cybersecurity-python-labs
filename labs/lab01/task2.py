"""Завдання 2: Багаторівнева система контролю доступу."""

users = {
    "cloud_architect": {
        "role": "cloud_security",
        "clearance": 4,
        "department": "Cloud",
        "active": True,
    },
    "devops_engineer": {
        "role": "devops",
        "clearance": 3,
        "department": "DevOps",
        "active": True,
    },
    "qa_tester": {
        "role": "quality_assurance",
        "clearance": 2,
        "department": "QA",
        "active": True,
    },
    "partner_access": {
        "role": "partner",
        "clearance": 2,
        "department": "Partnership",
        "active": True,
    },
    "migrated_user": {
        "role": "migrated",
        "clearance": 1,
        "department": "Migration",
        "active": False,
    },
}
resources = [
    ("cloud_configs", 4),
    ("deployment_pipelines", 3),
    ("test_environments", 2),
    ("partner_apis", 2),
    ("infrastructure_code", 4),
    ("shared_resources", 1),
    ("container_registry", 3),
    ("secrets_vault", 4),
    ("build_artifacts", 2),
    ("public_endpoints", 1),
]
security_levels = ("Development", "Staging", "Production", "Critical Infrastructure")
blocked_users = {"migrated_user", "container_breach", "pipeline_compromise"}


def print_resources() -> None:
    """Виводить ресурси із зіставленням назви рівня."""
    print("  Список ресурсів системи ")
    for res_name, level_num in resources:
        level_title = security_levels[level_num - 1]
        print(f"Ресурс: {res_name:<25} | Рівень: {level_title} ({level_num})")


def check_user_access(user: str, res_level: int) -> tuple[str, str]:
    """Перевіряє доступ користувача за ієрархією умов."""
    if user not in users:
        return "DENY", "User not found"

    if user in blocked_users:
        return "DENY", "User is blocked"

    if not users[user].get("active", False):
        return "DENY", "Account inactive"

    if users[user].get("clearance", 0) >= res_level:
        return "ALLOW", ""

    return "DENY", "Insufficient clearance"


def run_task2() -> None:
    """Основна функція виконання Завдання 2."""

    print_resources()

    print("\n Результати перевірки доступу ")
    test_users = list(users.keys()) + ["unknown_intruder"]

    for user in test_users:
        for res_name, res_lvl in resources:
            status, reason = check_user_access(user, res_lvl)
            if status == "ALLOW":
                print(f"user={user:<18} resource={res_name:<24} -> ALLOW")
            else:
                print(f"user={user:<18} resource={res_name:<24} -> DENY ({reason})")


if __name__ == "__main__":
    run_task2()
