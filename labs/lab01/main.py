"""Головний файл для послідовного запуску завдань Лабораторної роботи №1."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER  # noqa: E402
from labs.lab01.task1 import run_task1
from labs.lab01.task2 import run_task2
from labs.lab01.task3 import run_task3


def main() -> None:
    """Запуск усіх завдань лабораторної роботи."""

    print(f"  Студент: {STUDENT_NAME}")
    print(f"  Група:   {GROUP_NAME}")
    print(f"  Варіант: {VARIANT_NUMBER}")

    print("\n ЗАВДАННЯ 1 ")
    run_task1()

    print("\n ЗАВДАННЯ 2 ")
    run_task2()

    print("\n ЗАВДАННЯ 3 ")
    run_task3()


if __name__ == "__main__":
    main()
