# Лабораторна робота №2
**Тема:** Розробка консольних утиліт для задач кібербезпеки  
**Варіант 9:** Аудитор безпеки HTTP-заголовків відповідей

---

## 1. Встановлення залежностей

Усі команди виконуються з кореня репозиторію в активованому віртуальному середовищі:

pip install -r requirements.txt


2.
Структура вхідних даних
Каталог labs/lab02/data/ містить файли для аналізу та збереження результатів:

headers.json - вхідний JSON-файл із дампами HTTP-заголовків веб-ресурсів.

headers_audit.csv - результуючий CSV-звіт перевірки безпеки.

3. Приклади запуску
Завдання 1. Демонстрація ООП (User, Admin, Session, AuditLog)
Bash
python -m labs.lab02.main demo
Завдання 2. Аудит HTTP-заголовків відповідей
Базовий аудит зі збереженням у CSV:

Bash
    python -m labs.lab02.main analyze headers-file labs/lab02/data/headers.json output-csv labs/lab02/data/headers_audit.csv
Суворий режим (штраф за витік версій ПЗ) та розширене логування:

Bash
python -m labs.lab02.main analyze  headers-file labs/lab02/data/headers.json strict log-level DEBUG


4.
Опис CLI-параметрів (analyze)
headers-file (обов'язковий) - шлях до вхідного JSON-файлу із заголовками.

output-csv шлях для вивантаження звіту (за замовчуванням: labs/lab02/data/headers_audit.csv).

strict - прапорець активації суворого режиму оцінювання (знижує підсумковий бал за наявність версій у Server / X-Powered-By).

log-level - рівень деталізації журналу логування (DEBUG, INFO, WARNING, ERROR; дефолт: INFO).

5. 


Обробка помилок
Відсутній файл: при передачі неіснуючого шляху до headers-file утиліта фіксує помилку через logging.error та завершує процес із кодом 1.

Некоректний синтаксис JSON: пошкоджені файли безпечно перехоплюються через json.JSONDecodeError без критичного збою програми.

Невалідний email (Завдання 1): спроба встановити некоректну адресу викликає ValueError завдяки валідації регулярним виразом у @property.setter.

6. 

Перевірка якості коду (Ruff)
Bash
ruff check
ruff format check