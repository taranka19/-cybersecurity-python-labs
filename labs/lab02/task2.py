"""Варіант 9: Аудитор безпеки HTTP-заголовків відповідей."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Список критичних заголовків безпеки
REQUIRED_SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
]

# Регулярний вираз для пошуку витоку версій (наприклад, Apache/2.4.49, PHP/7.4.3, 10.0)
VERSION_LEAK_REGEX = re.compile(r"\b\d+(\.\d+)+\b")


def setup_logger(log_level: str) -> logging.Logger:
    """Налаштування форматованого логера."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("HeaderAuditor")
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def evaluate_resource(
    item: dict[str, Any],
    strict: bool = False,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Аналіз окремого ресурсу: підрахунок Score, виявлення пропущених заголовків та витоків."""
    url = item.get("url", "unknown")
    headers = item.get("headers", {})

    # Нормалізуємо ключі заголовків до нижнього регістру для надійного пошуку
    normalized_headers = {k.lower(): v for k, v in headers.items()}

    present_headers: list[str] = []
    missing_headers: list[str] = []

    for req_header in REQUIRED_SECURITY_HEADERS:
        if req_header.lower() in normalized_headers:
            present_headers.append(req_header)
        else:
            missing_headers.append(req_header)
            if logger:
                logger.debug("На ресурсі %s відсутній заголовок: %s", url, req_header)

    # Розрахунок Score (базово 25 балів за кожен із 4 обов'язкових заголовків)
    score = len(present_headers) * 25

    # Пошук витоків версій ПЗ у Server та X-Powered-By
    leaks: list[tuple[str, str]] = []
    for check_key in ("Server", "X-Powered-By"):
        val = normalized_headers.get(check_key.lower())
        if val and VERSION_LEAK_REGEX.search(val):
            leaks.append((check_key, val))
            # У strict-режимі наявність витоку знижує загальний бал
            if strict:
                score = max(0, score - 10)

    # Визначення статусу та літерної шкали оцінки
    if score >= 90:
        grade = "A+" if score >= 95 else "A"
        status = "PASS"
    elif score >= 60:
        grade = "B" if score >= 75 else "C"
        status = "WARN"
    else:
        grade = "F"
        status = "FAIL"

    return {
        "url": url,
        "score": score,
        "grade": grade,
        "status": status,
        "missing_headers": missing_headers,
        "leaks": leaks,
    }


def export_to_csv(results: list[dict[str, Any]], output_path: Path) -> None:
    """Збереження результатів аудиту у форматі CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Target Resource",
                "Security Score",
                "Status",
                "Missing Security Headers",
                "Leaks",
            ]
        )
        for r in results:
            missing_str = (
                ", ".join(r["missing_headers"]) if r["missing_headers"] else "None"
            )
            leaks_str = (
                "; ".join(f"{header}: {val}" for header, val in r["leaks"])
                if r["leaks"]
                else "None"
            )
            writer.writerow(
                [
                    r["url"],
                    f"{r['score']}/100 ({r['grade']})",
                    r["status"],
                    missing_str,
                    leaks_str,
                ]
            )


def run_analyzer(argv: list[str]) -> None:
    """Головна точка входу для підкоманди analyze."""
    parser = argparse.ArgumentParser(
        description="Аудитор безпеки HTTP-заголовків відповідей",
    )
    parser.add_argument(
        "--headers-file",
        type=Path,
        required=True,
        help="Шлях до вхідного JSON-файлу з HTTP-заголовками",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("labs/lab02/data/headers_audit.csv"),
        help="Шлях для збереження підсумкового CSV-звіту",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Суворий режим (штраф за витоки версій софту)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Рівень логування (за замовчуванням: INFO)",
    )

    args = parser.parse_args(argv)
    logger = setup_logger(args.log_level)

    if not args.headers_file.exists():
        logger.error("Вхідний файл не знайдено: %s", args.headers_file)
        sys.exit(1)

    logger.info("Auditing HTTP response headers from %s...", args.headers_file)

    try:
        with args.headers_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        logger.error("Помилка читання JSON-файлу: %s", err)
        sys.exit(1)

    results = [
        evaluate_resource(item, strict=args.strict, logger=logger) for item in data
    ]

    # Виведення результатів аудиту в консоль
    print()
    header_line = f"{'Target Resource':<36} {'Security Score':<15} {'Status':<8} {'Missing Security Headers'}"
    print(header_line)
    print("-" * 90)

    all_leaks: list[tuple[str, str, str]] = []

    for r in results:
        missing_str = (
            ", ".join(r["missing_headers"]) if r["missing_headers"] else "None"
        )
        score_display = f"{r['score']}/100 ({r['grade']})"
        print(f"{r['url']:<36} {score_display:<15} {r['status']:<8} {missing_str}")

        for leak_hdr, leak_val in r["leaks"]:
            all_leaks.append((r["url"], leak_hdr, leak_val))

    # Виведення виявлених версій ПЗ
    if all_leaks:
        print("\n=== Server Software Leak Alerts ===")
        for url, header_name, header_val in all_leaks:
            print(
                f"[LEAK] {url} leaks version/tech stack in '{header_name}': {header_val}"
            )

    # Збереження звіту
    export_to_csv(results, args.output_csv)
    logger.info("Header audit report generated at %s", args.output_csv)
