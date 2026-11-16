# Лабораторна робота №3 — Варіант 15

**Предметна область:** реєстр ризиків налаштування робочих станцій.
Категорії: `updates`, `permissions`, `protection`.
**Одиниця вимірювання:** `score` (навчальна оцінка ризику, від 0 до 10 включно), поріг 8.0.

## Встановлення залежностей

```bash
pip install -r requirements.txt
```

## Початкове заповнення бази

```bash
python -m labs.lab03.seed
```

## Запуск API

```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V15-TEST","title":"Навчальна знахідка","category_id":1,"value":7.5,"status":"new"}'
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V15-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V15-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
```