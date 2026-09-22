# Car Expenses

Система учёта расходов на автомобиль с двумя версиями приложения: графическим интерфейсом GUI (этот репозиторий) и веб-приложением ([GitHub - shadowdfd/Car-Expenses-WEB](https://github.com/shadowdfd/Car-Expenses-WEB)).

[Скачать версию для Windows](https://github.com/shadowdfd/Car-Expenses/releases/tag/lastest)

### GUI приложение (Windows)

Десктопное приложение на базе Tkinter с расширенными возможностями визуализации и экспорта данных.

**Основной файл:** `car_expenses_gui.pyw`

**Функциональность:**

- Учёт расходов, топлива, покупок запчастей
- История технического обслуживания
- Генерация PDF-отчётов (ReportLab)
- Графики пробега (Matplotlib)
- Экспорт данных в Excel/CSV
- Справочники: автомобили, СТО, производители, типы запчастей
- Стандартные работы и интервалы обслуживания

**Запуск:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python car_expenses_gui.pyw
```

**Сборка exe:**

```bash
pyinstaller car_expenses.spec
```

Исполняемый файл появится в папке `dist/`

### ## База данных

**SQLite:** `cars.db`

Общая база данных может использоваться обеими версиями приложения.

**Таблицы:**

- `cars` - автомобили
- `expenses` - расходы
- `expense_types` - типы расходов
- `fuel` - заправки топлива
- `parts` - запчасти
- `part_purchases` - покупки запчастей
- `part_types` - типы запчастей
- `manufacturers` - производители
- `car_systems` - системы автомобиля
- `services` - СТО
- `service_tasks` - стандартные работы
- `service_history` - история ТО
- `service_history_tasks` - связь работ с записями ТО

**Инициализация БД (для веб-версии):**

```bash
python init_db.py
```

## Структура проекта

### GUI версия

- `car_expenses_gui.pyw` - главное приложение
- `car_expenses.spec` - конфигурация PyInstaller
- `simplecrud.py` - CRUD операции
- `db.py` - работа с базой данных
- `Backup.py` - резервное копирование
- `styles.py` - стили интерфейса
- `Themes.py` - темы оформления
- `widgets/` - кастомные виджеты
- `fonts/` - шрифты для PDF
- `icons/` - иконки приложения
- `icon.ico` - иконка приложения

## Зависимости

### GUI (requirements.txt)

- `tkcalendar` - виджет календаря
- `pandas` - работа с данными
- `reportlab` - генерация PDF
- `openpyxl` - экспорт в Excel
- `matplotlib` - графики
