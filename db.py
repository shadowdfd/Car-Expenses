"""
Методы для работы с DB SQLite3 (connect - подключение, init_db - инициализация пустой базе данных)
"""

import sqlite3

DB_NAME = "cars.db"

class Database:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name, timeout=10)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def execute(self, query, params=()):
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def query(self, query, params=()):
        return self.conn.execute(query, params)

    def close(self):
        self.conn.close()
    
    def fetchall(self, query, params=()):
        return self.conn.execute(query, params).fetchall()

    def fetchone(self, query, params=()):
        return self.conn.execute(query, params).fetchone()

    def executemany(self, query, data):
        cur = self.conn.executemany(query, data)
        self.conn.commit()
        return cur

def init_db():
    """
    Инициализация пустой базы данных
    """
    db = Database()
    # Таблица пройденных ТО
    db.execute("""
    CREATE TABLE IF NOT EXISTS service_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER NOT NULL,
        service_date TEXT NOT NULL,
        mileage INTEGER NOT NULL,
        sto_id INTEGER,
        description TEXT,
        amount REAL NOT NULL,

        FOREIGN KEY (car_id) REFERENCES cars(id),
        FOREIGN KEY (sto_id) REFERENCES services(id)
    );
    """)

    # Таблица выполненных стандартных работ (связка)
    db.execute("""
    CREATE TABLE IF NOT EXISTS service_history_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_history_id INTEGER NOT NULL,
        service_task_id INTEGER NOT NULL,

        FOREIGN KEY (service_history_id) REFERENCES service_history(id) ON DELETE CASCADE,
        FOREIGN KEY (service_task_id) REFERENCES service_tasks(id),

        UNIQUE(service_history_id, service_task_id)
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manufacturer TEXT,
        name TEXT UNIQUE,
        year INTEGER,
        vin TEXT,
        plate_number TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        manufacturer_id INTEGER,
        type_id INTEGER,
        system_id INTEGER,
        article TEXT,
        original_article TEXT,
        FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id),
        FOREIGN KEY (type_id) REFERENCES part_types(id),
        FOREIGN KEY (system_id) REFERENCES car_systems(id)
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER NOT NULL,
        expense_type_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        comment TEXT
    )
    """)

    # Добавление таблицы типов расходов
    db.execute("""
    CREATE TABLE IF NOT EXISTS expense_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    # Добавление таблицы топлива
    db.execute("""
    CREATE TABLE IF NOT EXISTS fuel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER,
        liters REAL,
        price REAL,
        fuel_date TEXT
    )
    """)
    # Добавление таблицы покупок запчастей
    db.execute("""
    CREATE TABLE IF NOT EXISTS part_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        purchase_date TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        service_history_id INTEGER REFERENCES service_history(id) ON DELETE SET NULL
    );
    """)
    # Добавление таблицы производителей
    db.execute("""
    CREATE TABLE IF NOT EXISTS manufacturers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        country TEXT
    )
    """)
    
    # Добавление таблицы типов запчастей
    db.execute("""
    CREATE TABLE IF NOT EXISTS part_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)
    # Добавление таблицы систем автомобиля
    db.execute("""
    CREATE TABLE IF NOT EXISTS car_systems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)
    # Добавление таблицы СТО
    db.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Добавление таблицы задач по обслуживанию
    db.execute("""
    CREATE TABLE IF NOT EXISTS service_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER NOT NULL,
        abbr TEXT NOT NULL,
        name TEXT NOT NULL,
        interval_km INTEGER,
        interval_months INTEGER
    )
    """)        
    
    # Uncomment the following lines if you need to add new columns to the parts table
    #db.execute("ALTER TABLE parts ADD COLUMN type_id INTEGER")
    #db.execute("ALTER TABLE parts ADD COLUMN system_id INTEGER")

    # Uncomment the following lines if you need to add new columns to the parts table
    # db.execute("ALTER TABLE cars ADD COLUMN manufacturer TEXT")
    # db.execute("ALTER TABLE cars ADD COLUMN year INTEGER")
    # db.execute("ALTER TABLE cars ADD COLUMN vin TEXT")
    # db.execute("ALTER TABLE cars ADD COLUMN plate_number TEXT")

    # db.execute("ALTER TABLE parts ADD COLUMN article TEXT;")
    # db.execute("ALTER TABLE parts ADD COLUMN original_article TEXT;")

    # db.execute("ALTER TABLE expenses ADD COLUMN expense_type_id INTEGER;")
    # db.execute("ALTER TABLE service_tasks ADD COLUMN abbr TEXT NOT NULL DEFAULT '';")
    # db.execute("ALTER TABLE service_history ADD COLUMN amount REAL NOT NULL DEFAULT '0';")
    # db.execute("ALTER TABLE part_purchases ADD COLUMN service_history_id INTEGER REFERENCES service_history(id) ON DELETE SET NULL;")
        