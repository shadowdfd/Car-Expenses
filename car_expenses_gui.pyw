import tkinter as tk
import sys
import os
from pathlib import Path
from tkinter import ttk, messagebox, filedialog #, simpledialog
from tkcalendar import DateEntry                #need to install
from datetime import date, timedelta
#import pandas as pd                             #need to install
import csv
from datetime import datetime
from typing import Any
from styles import setup_styles
from simplecrud import SimpleCrud
from db import Database, init_db
from widgets.fk_combobox import FKCombobox
from widgets.form_grid import FormGrid          # Autogrid для форм

# Отчеты PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont 

# Графики пробега
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    plt = None
    FigureCanvasTkAgg = None


def resource_path(rel_path):      # Согласование путей ресурсов
    base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    return Path(base) / rel_path

APP_NAME = "Car expenses"
APP_VERSION = "1.0"
APP_AUTHOR = "Vadim Rodionov"

TABLES = {
    "expenses": {
        "title": "Расходы",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 40,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "expense_date",
                "label": "Дата",
                "type": "date",
                "width": 100,
                "anchor": "center",
                "required": True,
                "annotation": "Формат: ГГГГ-ММ-ДД",
            },
            {
                "db": "car_id",
                "label": "Автомобиль",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "cars",
                    "id": "id",
                    "lookup_field": "plate_number",
                    "display": "manufacturer || ' ' || name || ' - ' || plate_number",
                    "create_fields": ["plate_number"],
                },
                "annotation": None,
                "widget_width": 35,
            },
            {
                "db": "expense_type_id",
                "label": "Тип расхода",
                "type": "fk",
                "width": 200,
                "anchor": "w",
                "required": True,
                "filter": True,
                "ref": {
                    "table": "expense_types",
                    "id": "id",
                    "lookup_field": "name",
                    "display": "name",
                    "create_fields": "name",
                }
            },
            {
                "db": "amount",
                "label": "Сумма",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "sum": True,
                "annotation": "рублей"
            },
            {
                "db": "comment",
                "label": "Комментарий",
                "type": "str",
                "width": 200,
                "anchor": "w",
                "filter": True
            }
        ]
    },
    "service_history": {
        "title": "Обращения в сервис",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???                
            },
            {
                "db": "service_date",
                "label": "Дата",
                "type": "date",
                "width": 100,
                "anchor": "center",
                "required": True,
                "annotation": "Формат: ГГГГ-ММ-ДД",
                "widget_width": "18"
            },
            {
                "db": "car_id",
                "label": "Авто",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "cars",
                    "id": "id",
                    "lookup_field": "plate_number",
                    "display": "manufacturer || ' ' || name || ' - ' || plate_number",
                    "create_fields": ["plate_number"],
                },
                "annotation": None,
                "widget_width": 35,
            },
            {
                "db": "mileage",
                "label": "Пробег",
                "type": "float",
                "width": 200,
                "anchor": "w",
                "required": True,
                "annotation": "км"
            },
            {
                "db": "sto_id",
                "label": "СТО",
                "type": "fk",
                "width": 100,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "services",
                    "id": "id",
                    "lookup_field": "name",
                    "display": "name",
                    "create_fields": ["name"],
                },
                "annotation": None,
                "widget_width": 20,
            },
            {
                "db": "amount",
                "label": "Стоимость",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "sum": True,
                "annotation": "рублей"
            },
            {
                "db": "",
                "label": "Стандартные работы",
                "type": "ol",   # Only for custom load method
                "width": 200,
                "anchor": "center",
                "filter": True
            },            
            {
                "db": "description",
                "label": "Дополнительно",
                "type": "str",
                "width": 200,
                "anchor": "w",
                "filter": True
            }
        ]                             
    },
    "service_part_purchases":{
        "title": "Запчасти",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???                
            },
            {
                "db": "purchase_date",
                "label": "Дата покупки",
                "type": "date",
                "width": 100,
                "anchor": "center",
                "required": True,
                "annotation": "Формат: ГГГГ-ММ-ДД",
                "widget_width": "18"
            },
            {
                "db": "part_id",
                "label": "Запчасть",
                "type": "fk",
                "width": 700,
                "anchor": "w",
                "required": True,
                "ref": {
                    "table": "parts",
                    "id": "id",
                    "lookup_field": "article",
                    "display": "article || ' ' || name",
                    "create_fields": ["article"],
                },
                "annotation": None,
                "widget_width": 50,
            },
            {
                "db": "quantity",
                "label": "Количество",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": None
            },
            {
                "db": "price",
                "label": "Цена",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": "рублей"
            },
            {
                "db": "total",
                "label": "Сумма",
                "type": "calc",
                "width": 100,
                "anchor": "e",
                "sum": True,
                "calc_arg": "quantity * price",
                "calc_precision": 2,
                "annotation": "рублей"
            },
        ]
    },
    "fuel":{
        "title": "Заправки",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???                
            },
            {
                "db": "fuel_date",
                "label": "Дата заправки",
                "type": "date",
                "width": 100,
                "anchor": "center",
                "required": True,
                "annotation": "Формат: ГГГГ-ММ-ДД",
                "widget_width": "18"
            },
            {
                "db": "car_id",
                "label": "Автомобиль",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "cars",
                    "id": "id",
                    "lookup_field": "plate_number",
                    "display": "manufacturer || ' ' || name || ' - ' || plate_number",
                    "create_fields": ["plate_number"],
                },
                "annotation": None,
                "widget_width": 35,
            },
            {
                "db": "liters",
                "label": "Литры",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": None
            },
            {
                "db": "price",
                "label": "Цена",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": "рублей"
            },
            {
                "db": "total",
                "label": "Сумма",
                "type": "calc",
                "width": 100,
                "anchor": "e",
                "sum": True,
                "calc_arg": "liters * price",
                "calc_precision": 2,
                "annotation": "рублей"
            }
        ]
    },    
    "part_purchases":{
        "title": "Покупки запчастей",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???                
            },
            {
                "db": "purchase_date",
                "label": "Дата покупки",
                "type": "date",
                "width": 100,
                "anchor": "center",
                "required": True,
                "annotation": "Формат: ГГГГ-ММ-ДД",
                "widget_width": "18"
            },
            {
                "db": "car_id",
                "label": "Автомобиль",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "cars",
                    "id": "id",
                    "lookup_field": "plate_number",
                    "display": "manufacturer || ' ' || name || ' - ' || plate_number",
                    "create_fields": ["plate_number"],
                },
                "annotation": None,
                "widget_width": 35,
            },
            {
                "db": "part_id",
                "label": "Запчасть",
                "type": "fk",
                "width": 600,
                "anchor": "w",
                "required": True,
                "ref": {
                    "table": "parts",
                    "id": "id",
                    "lookup_field": "article",
                    "display": "article || ' ' || name",
                    "create_fields": ["article"],
                },
                "annotation": None,
                "widget_width": 50,
                "filter": True
            },
            {
                "db": "quantity",
                "label": "Количество",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": None
            },
            {
                "db": "price",
                "label": "Цена",
                "type": "float",
                "width": 100,
                "anchor": "e",
                "required": True,
                "annotation": "рублей"
            },
            {
                "db": "total",
                "label": "Сумма",
                "type": "calc",
                "width": 100,
                "anchor": "e",
                "sum": True,
                "calc_arg": "quantity * price",
                "calc_precision": 2,
                "annotation": "рублей"
            },
            {
                "db": "service_history_id",
                "label": "Id и дата ТО",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": False,
                "annotation": "если известно",
                "ref": {
                    "table": "service_history",
                    "id": "id",
                    "lookup_field": "service_date",
                    "display": "id || ' ' ||service_date",
                    "create_fields": ["service_date"],
                }
            }
        ]
    },
    "parts": {
        "title": "Запчасти",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "article",           # Имя поля в БД
                "label": "Артикул", # Имя столбца в таблице Treeview - UI
                "width": 100,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True,        # Обязательное поле
                "filter": True
            },
            {
                "db": "original_article",           # Имя поля в БД
                "label": "Ориг. артикул", # Имя столбца в таблице Treeview - UI
                "width": 100,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
                "filter": True
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Наименование", # Имя столбца в таблице Treeview - UI
                "width": 150,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True,        # Обязательное поле
                "filter": True,
                "widget_width": 45,
                "annotation": None
            },
            {
                "db": "manufacturer_id",
                "label": "Производитель",
                "type": "fk",
                "width": 150,
                "anchor": "center",
                "filter": True,
                "ref": {
                    "table": "manufacturers",
                    "id": "id",
                    "lookup_field": "name",
                    "display": "name",
                    "create_fields": "name",
                }
            },
            {
                "db": "type_id",
                "label": "Тип",
                "type": "fk",
                "width": 150,
                "anchor": "center",
                "filter": True,
                "ref": {
                    "table": "part_types",
                    "id": "id",
                    "lookup_field": "name",
                    "display": "name",
                    "create_fields": "name",
                }
            },
            {
                "db": "system_id",
                "label": "Система",
                "type": "fk",
                "width": 150,
                "annotation": "система автомобиля",
                "anchor": "center",
                "filter": True,
                "ref": {
                    "table": "car_systems",
                    "id": "id",
                    "lookup_field": "name",
                    "display": "name",
                    "create_fields": "name",
                }
            }
        ]
    },
    "cars": {
        "title": "Автомобили",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "manufacturer",           # Имя поля в БД
                "label": "Марка", # Имя столбца в таблице Treeview - UI
                "width": 100,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Модель",      # Имя столбца в таблице Treeview - UI
                "width": 100,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True          # Обязательное поле       
            },
            {
                "db": "year",           # Имя поля в БД
                "label": "Год выпуска",      # Имя столбца в таблице Treeview - UI
                "width": 100,            # Ширина столбца в таблице Treeview - UI
                "type": "int",          # тип поля
                "anchor": "center"          # Выравнивание в столбце в таблице Treeview - UI
            },
            {
                "db": "vin",           # Имя поля в БД
                "label": "VIN", # Имя столбца в таблице Treeview - UI
                "width": 150,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
            },
            {
                "db": "plate_number",           # Имя поля в БД
                "label": "Гос.Номер", # Имя столбца в таблице Treeview - UI
                "width": 150,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True          # Обязательное поле 
            }
        ]
    },
    "manufacturers": {
        "title": "Производитель",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Производитель", # Имя столбца в таблице Treeview - UI
                "width": 150,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            },
            {
                "db": "country",           # Имя поля в БД
                "label": "Страна", # Имя столбца в таблице Treeview - UI
                "width": 150,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "filter": True          
            }
        ]
    },
    "part_types": {
        "title": "Тип запчастей",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Тип запчасти", # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            }
        ]
    },
    "car_systems": {
        "title": "Система автомобиля",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Система автомобиля", # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            }
        ]
    },
    "services": {
        "title": "СТО/Сервис",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "СТО/Сервис", # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            }
        ]
    },    
    "expense_types": {
        "title": "Типы расходов",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "name",           # Имя поля в БД
                "label": "Тип расхода", # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True        # Обязательное поле
            }
        ]
    },
    "service_tasks": {
        "title": "Работы по регламенту",
        "columns": [
            {
                "db": "id",             # Имя поля в БД
                "label": "ID",          # Имя столбца в таблице Treeview - UI
                "width": 50,            # Ширина столбца в таблице Treeview - UI
                "anchor": "center",     # Выравнивание в столбце в таблице Treeview - UI
                "readonly": True        # ???
            },
            {
                "db": "abbr",           # Имя поля в БД
                "label": "Аббревиатура", # Имя столбца в таблице Treeview - UI
                "width": 80,            # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True,        # Обязательное поле
                "annotation": "5 знаков"
            },            
            {
                "db": "name",           # Имя поля в БД
                "label": "Вид работ",   # Имя столбца в таблице Treeview - UI
                "width": 300,           # Ширина столбца в таблице Treeview - UI
                "type": "str",          # тип поля
                "anchor": "w",          # Выравнивание в столбце в таблице Treeview - UI
                "required": True,       # Обязательное поле
                "filter": True,         # Добавить фильтр по полю
                "annotation": None,
                "widget_width": 40
            },            
            {
                "db": "interval_km",           # Имя поля в БД
                "label": "Интервал в км",   # Имя столбца в таблице Treeview - UI
                "width": 120,           # Ширина столбца в таблице Treeview - UI
                "type": "int",          # тип поля
                "anchor": "center",          # Выравнивание в столбце в таблице Treeview - UI
            },            
            {
                "db": "interval_months",        # Имя поля в БД
                "label": "Интервал в месяцах",  # Имя столбца в таблице Treeview - UI
                "width": 120,                   # Ширина столбца в таблице Treeview - UI
                "type": "int",                  # тип поля
                "anchor": "center",             # Выравнивание в столбце в таблице Treeview - UI
            },
                        {
                "db": "car_id",
                "label": "Автомобиль",
                "type": "fk",
                "width": 200,
                "anchor": "center",
                "required": True,
                "ref": {
                    "table": "cars",
                    "id": "id",
                    "lookup_field": "plate_number",
                    "display": "manufacturer || ' ' || name || ' - ' || plate_number",
                    "create_fields": ["plate_number"],
                },
                "annotation": None,
                "widget_width": 35,
            }
        ]
    }
}


# ================== TOOLBAR ==================
class Toolbar(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def add_button(self, *, icon, command, tooltip=None, state="normal", text_name=None, side_str = 'left' ):
        btn = ttk.Button(
            self,
            image=self.app.icons[icon],
            command=command,
            state=state,
        )
        if text_name:
            btn.configure(text=" "+text_name+" ", compound="left")

        btn.pack(side=side_str, padx=2)

        if tooltip:
            self.app.tooltip(btn, tooltip)

        return btn

    def add_separator(self, side_str="left"):
        ttk.Separator(self, orient="vertical").pack(
            side=side_str, fill="y", padx=5
        )

# ================= GUI =================
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        init_db()        
        self.db = Database()   # ← одно соединение на всё приложение

        # флаг для показа приглашения на добавление авто (если нет ни одной записи)
        try:
            self._no_cars = self.db.fetchone("SELECT COUNT(*) FROM cars")[0] == 0
        except Exception:
            self._no_cars = True

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        setup_styles()   # ← ВАЖНО: до создания виджетов

        icon_path = resource_path("icons/saving_sm.png")
        icon = tk.PhotoImage(file=icon_path)
        
        # True — применить ко всем будущим Toplevel
        self.iconphoto(True, icon)

        self.title(f"{APP_NAME} - v{APP_VERSION}")
        self.geometry("1500x800")

        # Глобальные переменные
        self.car_var = tk.StringVar()                       # Переменная выбранного автомобиля
        self.hidden = False                                 # Состояние не основных справочников
        self.filter_by_car = tk.BooleanVar(value=True)      # Состояние фильтрации по авто
        self.filter_by_date = tk.BooleanVar(value=False)    # Состояние фильтрации по авто  

        self.sum_expenses_var = tk.StringVar(value="0")     # Затраты на расходы (страховка, кредит и прочее)
        self.sum_fuel_var = tk.StringVar(value="0")         # Затраты на топливо    
        self.sum_service_var = tk.StringVar(value="0")      # Затраты на ТО
        self.sum_parts_var = tk.StringVar(value="0")        # Затраты на запчасти
        self.sum_all_expenses_var = tk.StringVar(value="0") # Общие затраты на всё       

        # Иконки
        self.load_icons()

        self.tabs_config = {}

        # Главное окно
        self.create_widgets()

        # Обновить все таблицы и фильтры
        self.refresh_all()

        # Если еще нет автомобилей, предложить добавить первый
        if self._no_cars:
            self.after(100, self.prompt_add_first_car)

    def on_close(self):
        self.db.close()
        self.destroy()

    def prompt_add_first_car(self):
        try:
            cars_count = self.db.fetchone("SELECT COUNT(*) FROM cars")[0]
        except Exception:
            cars_count = 0

        if cars_count != 0:
            return

        add = messagebox.askyesno(
            "Первый автомобиль",
            "База данных создана. Добавить первый автомобиль сейчас?"
        )

        if add:
            # Открытие формы добавления
            self.cars_crud.add()

    # ---------- UI ----------
    def create_widgets(self):
        # ================= Верхняя панель =================
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0,0), padx=0)

        car_fr = ttk.Frame(top)
        car_fr.pack(side="left", padx=10, pady=10)

        # Иконка авто 
        self.image_label(car_fr, icon="car", im_padx=10)
        
        self.car_combo = ttk.Combobox(car_fr, textvariable=self.car_var, width=30)
        self.car_combo.pack(side="left", padx=10, pady=10)
      
        ttk.Checkbutton(
            car_fr,
            text="Фильтр по автомобилю",
            variable=self.filter_by_car,
            command=self.toggle_car_filter
        ).pack(side="left", padx=10, pady=10)

        self.car_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_all())

        tools_fr = ttk.Frame(top)
        tools_fr.pack(fill="x", padx=10, pady=10)
       
        totals = ttk.LabelFrame(self, text="Затраты (ВНИМАНИЕ! включенные фильтры учитываются!)")
        totals.pack(fill="x", padx=10, pady=5)

        self.image_label(totals, icon="insur", ttext=" : ", im_padx=0)
        ttk.Entry(totals, textvariable=self.sum_expenses_var, width=12, justify="right", state="readonly").pack(side="left", padx=(0,20))
        self.image_label(totals, icon="service", im_padx=0, ttext=" : ")
        ttk.Entry(totals, textvariable=self.sum_service_var, width=12, justify="right", state="readonly").pack(side="left", padx=(0,20))
        self.image_label(totals, icon="fuel", im_padx=0, ttext=" : ")
        ttk.Entry(totals, textvariable=self.sum_fuel_var, width=12, justify="right", state="readonly").pack(side="left", padx=(0,20))
        self.image_label(totals, icon="engine", im_padx=0, ttext=" : ")
        ttk.Entry(totals, textvariable=self.sum_parts_var, width=12, justify="right", state="readonly").pack(side="left", padx=(0,20))
        self.image_label(totals, icon="total", im_padx=0, im_pady=5, ttext=" : ")
        ttk.Entry(totals, textvariable=self.sum_all_expenses_var, width=12, justify="right", state="readonly", font=("Sergoe UI",10, "bold")).pack(side="left", padx=(0,20))

        
        # Фильтр по датам
        date_filter = ttk.Frame(self)
        date_filter.pack(fill="x", padx=10, pady=10)

        # Иконка календаря
        self.image_label(date_filter, icon="calendar", im_padx=10, ttext=" Фильтр по датам: ")

        ttk.Checkbutton(
            date_filter,
            text="Включен",
            variable=self.filter_by_date,
            command=self.refresh_all
        ).pack(side="left", padx=10)

        quick = ttk.Frame(date_filter)
        quick.pack(side="left", padx=10, pady=10)

        ttk.Button(quick, text="1М", width=4, command=lambda: self.set_quick_period(31)).pack(side="left", padx=2)
        ttk.Button(quick, text="3М", width=4, command=lambda: self.set_quick_period(31*3)).pack(side="left", padx=2)
        ttk.Button(quick, text="6М", width=4, command=lambda: self.set_quick_period(31*6)).pack(side="left", padx=2)
        ttk.Button(quick, text="1Г", width=4, command=lambda: self.set_quick_period(365)).pack(side="left", padx=2)

        ttk.Label(date_filter, text="Период: ").pack(side="left", padx=(5, 2))

        self.date_from = DateEntry(date_filter, width=12, date_pattern="yyyy-mm-dd")
        self.date_from.set_date("2000-01-01")
        self.date_from.pack(side="left", padx=2)

        ttk.Label(date_filter, text="-").pack(side="left", padx=(1, 1))

        self.date_to = DateEntry(date_filter, width=12, date_pattern="yyyy-mm-dd")
        self.date_to.set_date(date.today())        
        self.date_to.pack(side="left", padx=2)

        ttk.Button(date_filter, text="Применить", command=self.refresh_all).pack(side="left", padx=10)
        ttk.Button(date_filter, text="Сброс", command=self.reset_date_filter).pack(side="left")

        # ================= Notebook =================
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=True, fill="both", padx=10, pady=10)

        # ================= Вкладки =================
        self.main_tabs = [
            ("Расходы", "tab_expenses", self.build_expenses_tab, "coins"),
            ("ТО", "tab_service_history", self.build_service_history_tab, "service"),
            ("Топливо", "tab_fuel", self.build_fuel_tab, "fuel"),
            ("Покупки запчастей", "tab_part_purchases", self.build_part_purchases_tab, "buy"),
            ("Запчасти", "tab_parts", self.build_parts_tab, "engine"),
        ]

        self.reference_tabs = [
            ("Авто", "tab_cars", self.build_cars_tab, "car"),
            ("Производители", "tab_manufacturers", self.build_manufacturers_tab, "list"),
            ("Типы запчастей", "tab_part_types", self.build_part_types_tab, "list"),
            ("Системы автомобиля", "tab_car_systems", self.build_car_systems_tab, "list"),
            ("СТО", "tab_services", self.build_services_tab, "list"),
            ("Типы расходов", "tab_expenses_types", self.build_expense_types_tab, "list"),
            ("Станд. работы", "tab_service_tasks", self.build_service_tasks_tab, "wrench"),
        ]

        # Создание и добавление вкладок
        for text, attr, builder, icon_name in self.main_tabs + self.reference_tabs:
            frame = ttk.Frame(self.tabs)
            setattr(self, attr, frame)
            self.tabs.add(frame, text=text, image=self.icons[icon_name], compound="left")
            builder()

        # ================= Скрытие справочников =================
        def toggle_tabs():
            tab_list = self.reference_tabs
            if self.hidden:
                for text, attr, _, icon_name in tab_list:
                    self.tabs.add(getattr(self, attr), text=text, image=self.icons[icon_name], compound="left")
            else:
                for _, attr, _, _ in tab_list:
                    self.tabs.forget(getattr(self, attr))
            self.hidden = not self.hidden

        # Инструменты и настройки - Toolbar
        top_toolbar = Toolbar(tools_fr, self)
        top_toolbar.pack(pady=2, expand=1, fill="x")
        # Buttons
        top_toolbar.add_button(icon="books", command=toggle_tabs, tooltip="Показать справочники", text_name="Cправочники")
        top_toolbar.add_separator(side_str = "left")
        top_toolbar.add_button(icon="info", command=self.show_about, tooltip="О программе", side_str = "right")
        top_toolbar.add_separator(side_str = "right") 
        top_toolbar.add_button(icon="import", command=self.import_active_tab, tooltip="Импорт CSV", text_name="Импорт CSV", side_str = "right")
        top_toolbar.add_button(icon="export", command=self.export_active_tab, tooltip="Экспорт CSV", text_name="Экспорт CSV", side_str = "right")
        top_toolbar.add_button(icon="file-pdf", command=self.generate_pdf_report, tooltip="Экспорт PDF", text_name="Экспорт PDF", side_str = "right")        
        top_toolbar.add_separator(side_str = "right")
        top_toolbar.add_button(icon="report", command=self.generate_car_summary_report, tooltip="Общий отчёт по авто", side_str = "right")
        top_toolbar.add_button(icon="graph", command=self.generate_mileage_history_chart, tooltip="График пробега", side_str = "right")
        top_toolbar.add_button(icon="oil", command=self.generate_oil_change_report, tooltip="Отчет о замене масла", side_str = "right")
        top_toolbar.add_separator(side_str = "right")
        # Сразу скрываем справочники
        toggle_tabs()

    def get_active_tab_config(self):
        selected_tab_id = self.tabs.select()
        selected_tab = self.tabs.nametowidget(selected_tab_id)

        return self.tabs_config.get(selected_tab)

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            f"{APP_NAME} (версия {APP_VERSION})\n"
            f"Автор: {APP_AUTHOR}\n\n"
            "Программа для учёта расходов автомобиля,\n"
            "включая ТО, топливо, запчасти и прочие расходы.\n"
            "Поддерживает фильтрацию по авто и экспорты CSV/PDF."
        )

    def load_icons(self):
        icon_names = [
            "add", "edit", "delete", "filter",
            "car", "import", "export", "books",
            "insur", "service", "fuel", "engine",
            "expense", "total", "buy", "settings",
            "coins", "list", "wrench", "calendar","clear",
            "file-pdf", "report", "graph", "oil", "info"
        ]
        self.icons = {
            name: tk.PhotoImage(
                file=resource_path(f"icons/{name}.png")
            )
            for name in icon_names
        }

    def toggle_car_filter(self):
        state = "readonly" if self.filter_by_car.get() else "disabled"
        self.car_combo.configure(state=state)
        self.refresh_all()

    def reset_date_filter(self):
        self.date_from.set_date("2000-01-01")
        self.date_to.set_date(date.today())
        self.refresh_all()

    def get_date_filter(self):
        date_from = self.date_from.get().strip()
        date_to = self.date_to.get().strip()

        if not date_from and not date_to:
            return None, None

        if date_from and date_to and date_from > date_to:
            messagebox.showwarning(
                "Период дат",
                "Дата «С» больше даты «По»"
            )
            return None, None

        return date_from or None, date_to or None

    def set_quick_period(self, days):
        today = date.today()
        start = today - timedelta(days=days)

        self.date_from.set_date(start)
        self.date_to.set_date(today)

        self.filter_by_date.set(True)

        self.refresh_all()

    def tooltip(self, widget, text, delay=600):
        tip = tk.Toplevel(widget)
        tip.withdraw()
        tip.overrideredirect(True)

        label = ttk.Label(
            tip,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padding=(6, 3)
        )
        label.pack()

        after_id = None

        def show():
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            tip.geometry(f"+{x}+{y}")
            tip.deiconify()

        def on_enter(event):
            nonlocal after_id
            after_id = widget.after(delay, show)

        def on_leave(event):
            nonlocal after_id
            if after_id:
                widget.after_cancel(after_id)
                after_id = None
            tip.withdraw()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def image_label(self, parent, icon, ttext: str="", im_padx=2, im_pady=0, im_side = 'left' ):
        lbl = tk.Label(parent, image=self.icons[icon], bd=0)
        if ttext:
            lbl.configure(text=ttext, compound="left")
        #lbl.image = self.icons['filter']   # важно! чтобы не удалилось сборщиком мусора
        lbl.pack(side=im_side, padx=im_padx, pady=im_pady)    

    # ---------- TABLE ----------
    def create_table(self, parent, columns):
        """
        columns = [
            ("ID", 60, "center"),
            ("Название", 200, "w"),
            ("Страна", 120, "w"),
        ]
        """
        tree = ttk.Treeview(
            parent,
            columns=[c[0] for c in columns],
            show="headings"
        )

        tree.tag_configure("odd", background="#f0f0f0")
        tree.tag_configure("even", background="white")
        tree.tag_configure("total", background="#e6f3ff", font=("Arial", 9, "bold"))

        for i, (title, width, anchor) in enumerate(columns, start=1):
            tree.heading(f"#{i}", text=title, anchor="center")
            tree.column(
                f"#{i}",
                width=width,
                anchor=anchor,
                stretch=(i == len(columns))
            )
            tree.pack(fill="both", expand=True, padx=10, pady=10)

        return tree

    def build_tree(self, parent, table_key, with_scrollbar=True, with_total_row=False, height = 10):
        """Создаёт Treeview с опциональным скроллом и закреплённой строкой итогов"""
        config = TABLES[table_key]

        columns = []
        
        # Создаём Frame для таблицы со скроллом
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(frame, show="headings", height=height)

        # Вертикальный скроллбар
        if with_scrollbar:
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Упаковываем скролл и таблицу вместе
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            tree.pack(fill="both", expand=True)

        for col in config["columns"]:
            columns.append(col["label"])

        tree.tag_configure("odd", background="#f0f0f0")
        tree.tag_configure("even", background="white")
        tree.tag_configure("total", background="#e6f3ff", font=("Arial", 9, "bold"))

        tree["columns"] = columns

        for i, col in enumerate(config["columns"], start=1):
            tree.heading(col["label"], text=col["label"], anchor="center")
            tree.column(
                col["label"],
                width=col["width"],
                anchor=col["anchor"],
                stretch=(i == len(config["columns"]))
            )

        # Закреплённая строка итогов внизу
        total_tree = None
        if with_total_row:
            total_frame = ttk.Frame(parent)
            total_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            total_tree = ttk.Treeview(total_frame, show="", height=1)
            total_tree.pack(fill="x")
            
            total_tree["columns"] = columns
            
            for i, col in enumerate(config["columns"], start=1):
                total_tree.heading(col["label"], text=col["label"], anchor="center")
                total_tree.column(
                    col["label"],
                    width=col["width"],
                    anchor=col["anchor"],
                    stretch=(i == len(config["columns"]))
                )
            
            total_tree.tag_configure("total", background="#e6f3ff", font=("Arial", 9, "bold"))
            
            # Синхронизация ширины колонок при изменении размера
            def sync_columns(event=None):
                for i, col in enumerate(columns, start=1):
                    width = tree.column(col, "width")
                    total_tree.column(col, width=width)
            
            tree.bind("<ButtonRelease-1>", sync_columns)
            # Первоначальная синхронизация
            parent.after(100, sync_columns)

        return tree, total_tree if with_total_row else tree

    def stripe_rows(self, tree):
            for i, item in enumerate(tree.get_children()):
                tag = "even" if i % 2 == 0 else "odd"
                tree.item(item, tags=(tag,))

    def create_crud(self, table_key, tree, sum_command, total_tree=None):
        config = TABLES[table_key]

        fields = []

        for col in config["columns"]:
            if col["db"] == "id":
                continue

            field = {
                "name": col["db"],
                "label": col["label"],
                "type": col.get("type", "str"),
                "required": col.get("required", False),
                "sum": col.get("sum", False),
                "filter": col.get("filter", False),
                "annotation": col.get("annotation", None),
                "width": col.get("widget_width", 20)
            }
            if col.get("type") == "calc":
                field["calc_arg"] = col.get("calc_arg", "1 * 1")
                field["calc_precision"] = col.get("calc_precision", 1)
            elif col.get("type") == "fk":
                field["ref_table"] = col["ref"]["table"]
                field["ref_id"] = col["ref"]["id"]
                field["ref_label"] = col["ref"]["display"]
                field["query"] = (
                    f"SELECT {col['ref']['id']}, "
                    f"{col['ref']['display']} "
                    f"FROM {col['ref']['table']}"
                )

            fields.append(field)

        return SimpleCrud(
            app=self,
            connection=self.db,
            carcombo=self.car_combo,
            table=table_key,
            tree=tree,
            total_tree=total_tree,
            title=config["title"],
            fields=fields,
            on_total_changed=sum_command
        )

    def center_window(self, parent, win):
        parent.update_idletasks()
        win.update_idletasks()

        x = parent.winfo_x() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)

        win.geometry(f"+{x}+{y}")

    def create_dialog_window(self, parent, win, title: str):
        self.center_window(self, win)
        win.transient(parent)
        win.resizable(False, False)
        win.title(title)
        #win.attributes("-topmost", True)
        #win.geometry("360x180")

    # ---------- Expenses / Расходы ----------
    def build_expenses_tab(self):

        tab = self.tab_expenses                # !!!!!!!
        table_name = "expenses"                # !!!!

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица (с закреплённой строкой итогов)
        self.expenses_table, self.expenses_total = self.build_tree(tab, table_name, with_total_row=True)

        tree = self.expenses_table              # !!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.expenses_crud = self.create_crud(table_name, tree, self.expenses_update_sum, self.expenses_total)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.expenses_crud)

    def expenses_update_sum(self, total):
        self.sum_expenses_var.set(f"{total:.2f}")
        self.recalc_amount()

    # ------------ Service history / История ТО ----------------
    def build_service_history_tab(self):

        tab = self.tab_service_history                # !!!!!!!
        table_name = "service_history"                # !!!!

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        filters_fr = ttk.Frame(tab)
        filters_fr.pack(fill="x", padx=5, pady=5)

        # Таблица (с закреплённой строкой итогов)
        self.service_history_table, self.service_history_total = self.build_tree(tab, table_name, with_total_row=True)

        tree = self.service_history_table              # !!!!
        tree.bind("<<TreeviewSelect>>", lambda e: self.load_service_part_purchases())


        # Таблица запчастей (с закреплённой строкой итогов)
        self.parts_in_service_table, self.parts_in_service_total = self.build_tree(tab, "service_part_purchases", with_total_row=True, height=4)

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.service_history_crud = self.create_crud(table_name, tree, self.service_history_update_sum, self.service_history_total)

        # Toolbar
        toolbar = Toolbar(top, self)
        toolbar.pack(side="left", pady=2)
        # Buttons
        crud_item =  self.service_history_crud       
        toolbar.add_button(icon="add", command=self.add_service_history, tooltip="Добавить запись")
        toolbar.add_button(icon="edit", command=self.edit_service_history, tooltip="Редактировать запись")
        toolbar.add_button(icon="delete", command=self.delete_service_history, tooltip="Удалить запись (Del)")
        # toolbar.add_separator()
        # toolbar.add_button(icon="add", command=crud_item.add, tooltip="Добавить запись")
        # toolbar.add_button(icon="edit", command=crud_item.edit, tooltip="Редактировать запись")
        # toolbar.add_button(icon="delete", command=crud_item.delete, tooltip="Удалить запись (Del)")
        toolbar.add_separator()
        toolbar.add_button(icon="buy", command=self.buy_part_to_service_history, tooltip="Купить запчасть к ТО")
        toolbar.add_button(icon="wrench", command=self.add_part_to_service_history, tooltip="Добавить уже купленную запчасть")

        # Фильтры
        filters_fr = ttk.Frame(top)
        filters_fr.pack(fill="x", padx=5, pady=5)

        # Иконка фильтров 
        self.image_label(filters_fr, icon="filter", ttext=":", im_padx=10)

        # 🛠 Фильтр сервисы
        ttk.Label(filters_fr, text="СТО: ").pack(side="left", padx=(10, 0))
        self.services_cb = ttk.Combobox(filters_fr, state="readonly", width=18)
        self.services_cb.pack(side="left", padx=5)
        self.services_cb.bind("<<ComboboxSelected>>", lambda e: self.load_service_history())

        # 🛠 Фильтр работы
        ttk.Label(filters_fr, text="Работы: ").pack(side="left", padx=(10, 0))
        self.tasks_cb = ttk.Combobox(filters_fr, state="readonly", width=18)
        self.tasks_cb.pack(side="left", padx=5)
        self.tasks_cb.bind("<<ComboboxSelected>>", lambda e: self.load_service_history())

        # Reset filters button
        ttk.Button(filters_fr, text="Сброс", command=self.reset_history_filters, width=7).pack(side="left", padx=10)

        # Bind double-click to edit
        self.service_history_table.bind("<Double-1>", self.edit_service_history)
        
        # Шорткаты       
        top.bind("<Insert>", lambda e: self.add_service_history())
        self.service_history_table.bind("<Delete>", lambda e: self.delete_service_history())

        # Заполнение фильтров
        self.load_service_history_filters()

        # Context menu
        self.attach_context_menu(
            self.service_history_table,
            [
                ("Редактировать", self.edit_service_history),
                ("Удалить", self.delete_service_history),
                ("---", None),
                ("Добавить запчасть", self.add_part_to_service_history)
            ]
        )

    def load_service_part_purchases(self):
        


        item = self.service_history_table.focus()
        if not item:
            return

        service_history_id = self.service_history_table.item(item)["values"][0]
        print(f"Фокус id: {service_history_id}")
        car_id = self.get_selected_car_id()
        if not car_id:
            return
    
        self.parts_in_service_table.delete(*self.parts_in_service_table.get_children())

        where = []
        params = []

        # Автомобиль
        if self.filter_by_car.get():
            where.append("pp.car_id = ?")
            params.append(car_id)       

        where.append("pp.service_history_id = ?")
        params.append(service_history_id)            

        sql = """
            SELECT
                pp.id,
                pp.purchase_date,               
                c.manufacturer || ' ' || c.name || ' - ' || c.plate_number AS car,
                p.article || ' ' || p.name || ' ' || m.name AS part_display,
                pp.quantity,
                pp.price,
                ROUND(pp.quantity * pp.price, 2) AS total,
                pp.service_history_id,
                pp.id AS part_id
            FROM part_purchases pp
            JOIN cars c ON c.id = pp.car_id
            JOIN parts p ON p.id = pp.part_id
            LEFT JOIN manufacturers m ON m.id = p.manufacturer_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY pp.purchase_date DESC"            
            
        rows = self.db.fetchall(sql, params)

        for r in rows:
            self.parts_in_service_table.insert(
                "",
                "end",
                values=(r[0], r[1], r[3], r[4], r[5], r[6]),  # поля 1,2,4,5,6
            )
        
        # Зебра на строки
        self.stripe_rows(self.parts_in_service_table)

        # Обновляем закреплённую строку итогов
        total_cost = sum(float(r[6]) for r in rows)
        
        if self.parts_in_service_total:
            self.parts_in_service_total.delete(*self.parts_in_service_total.get_children())
            self.parts_in_service_total.insert("", "end",
                values=("", "", "", "", "", self.format_currency(total_cost)),
                tags=("total",)
            )

    def service_history_update_sum(self, total):
        self.sum_service_var.set(f"{total:.2f}")
        self.recalc_amount()

    def load_service_history_filters(self):
        
        car_id = self.get_selected_car_id()
        # Сервисы
        rows = self.db.fetchall(
            "SELECT id, name FROM  services ORDER BY name"
        )
        self._services = rows
        self.services_cb["values"] = ["Все"] + [r[1] for r in rows]
        self.services_cb.current(0)

        # Работы
        rows = self.db.fetchall(
            "SELECT id, abbr, name FROM service_tasks WHERE car_id=? ORDER BY name",((car_id,)))
        self._tasks = rows
        self.tasks_cb["values"] = ["Все"] + [r[1] for r in rows]
        self.tasks_cb.current(0)        

    def reset_history_filters(self):
        self.tasks_cb.current(0)
        self.services_cb.current(0)
        self.load_service_history()

    def load_service_history(self):
        
        car_id = self.get_selected_car_id()
        if not car_id:
            return
        
        where = []
        params = []

        self.service_history_table.delete(*self.service_history_table.get_children())

        # Автомобиль
        if self.filter_by_car.get():
            where.append("sh.car_id = ?")
            params.append(car_id)       

        # 📦 Серввис 
        idx = self.services_cb.current()
        if idx > 0:
            where.append("sh.sto_id = ?")
            params.append(self._services[idx - 1][0])

        # Работы 
        idx = self.tasks_cb.current()
        if idx > 0:
            where.append(f"""
                sh.id IN (
                    SELECT service_history_id
                    FROM service_history_tasks
                    WHERE service_task_id IN (?)                        
                )       
            """)
            params.append(self._tasks[idx - 1][0])

        # Период дат
        if self.filter_by_date.get():
            date_from, date_to = self.get_date_filter()

            if date_from:
                where.append("sh.service_date >= ?")
                params.append(date_from)

            if date_to:
                where.append("sh.service_date <= ?")
                params.append(date_to)

        sql = """
                SELECT
                    sh.id,
                    sh.service_date,
                    c.manufacturer || ' ' || c.name || ' - ' || c.plate_number AS car,
                    sh.mileage,
                    s.name,
                    printf('%.2f', sh.amount) AS amount,
                    GROUP_CONCAT(st.abbr, ', '),
                    sh.description
                FROM service_history sh
                LEFT JOIN cars c ON c.id = sh.car_id
                LEFT JOIN services s ON s.id = sh.sto_id
                LEFT JOIN service_history_tasks sht ON sht.service_history_id = sh.id
                LEFT JOIN service_tasks st ON st.id = sht.service_task_id
            """

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " GROUP BY sh.id"
        sql += " ORDER BY sh.service_date DESC;"

        rows = self.db.fetchall(sql, params)

        for r in rows:
            self.service_history_table.insert("", "end", values=r)

        # Строка итогов
        total_cost = sum(float(r[5]) for r in rows)

        self.sum_service_var.set(self.format_currency(total_cost))
        self.recalc_amount()

        # Зебра на строки
        self.stripe_rows(self.service_history_table)

        # Обновляем закреплённую строку итогов
        if self.service_history_total:
            self.service_history_total.delete(*self.service_history_total.get_children())
            self.service_history_total.insert("", "end",
                values=("","","", "","", self.sum_service_var.get(),"",""),
                tags=("total",)
            )

    def add_service_history(self):
        
        car_id = self.get_selected_car_id()

        win = tk.Toplevel(self)
        self.create_dialog_window(self, win, "Новое ТО")
        form = FormGrid(win, 3)  # parent, количество колонок

        # Дата
        date_lbl = ttk.Label(win, text="Дата", style="Form.TLabel")
        date_entry = DateEntry(
            win,
            date_pattern="yyyy-mm-dd",
            width=18,
            style="Form.TCombobox"
        )
        date_entry.set_date(date.today())
        date_com_lbl = ttk.Label(win, text="Формат: ГГГГ-ММ-ДД", style="Form_Com.TLabel")
        form.add(date_lbl, date_entry, date_com_lbl)

        # Пробег
        mileage_var = tk.StringVar()
        mileage_var.set(str('0'))        
        mileage_lbl=ttk.Label(win, text="Пробег", style="Form.TLabel")
        mileage_e = ttk.Entry(win, textvariable=mileage_var, justify="right", style="Form.TEntry")
        mileage_var.trace_add("write", lambda *_: self.validate_float(mileage_var,mileage_e)) # Проверка на число
        mileage_e.bind("<FocusOut>", lambda e: self.normalize(mileage_var, mileage_e, 0))    # Нормализация к формату
        mileage_com_lbl = ttk.Label(win, text="на момент ТО", style="Form_Com.TLabel")
        form.add(mileage_lbl, mileage_e, mileage_com_lbl)

        # СТО fk
        services = self.db.fetchall(
            "SELECT id, name FROM services ORDER BY name"
        )
        services_lbl = ttk.Label(win, text="СТО", style="Form.TLabel")
        services_cb = FKCombobox(
            win,
            fk_data=services,
            state="readonly",
            width=18,
            style="Form.TCombobox"
        )
        form.add(services_lbl, services_cb)

        # Стоимость
        amount_var = tk.StringVar()
        amount_var.set(str('0.00'))        
        amount_lbl = ttk.Label(win, text="Стоимость", style="Form.TLabel")
        amount_e = ttk.Entry(win, textvariable=amount_var, justify="right", style="Form.TEntry")
        amount_var.trace_add("write", lambda *_: self.validate_float(amount_var,amount_e)) # Проверка на число
        amount_e.bind("<FocusOut>", lambda e: self.normalize(amount_var, amount_e, 2))    # Нормализация к формату
        amount_com_lbl = ttk.Label(win, text="по заказ наряду", style="Form_Com.TLabel")        
        form.add(amount_lbl, amount_e, amount_com_lbl)

        # Работы по регламенту
        tasks_lbl = ttk.Label(win, text="Работы по регламенту", style="Form.TLabel")
        tasks_frame = ttk.Frame(win)
        form.add_12(tasks_lbl, tasks_frame)

        # Формируем Checkbox'ы
        tasks = self.db.fetchall(
            "SELECT id, abbr, name FROM service_tasks WHERE car_id = ? ORDER BY name"
        , (car_id,))

        task_vars = {}  # service_task_id -> BooleanVar

        for tid, abbr, name in tasks:
            var = tk.IntVar(value=0)  # 0 — выключен, 1 — включен
            cb = ttk.Checkbutton(
                tasks_frame,
                text=f"[{abbr}] {name}",
                variable=var
            )
            cb.pack(anchor="w")
            task_vars[tid] = var

        # Дополнительные работы
        description_lbl = ttk.Label(win, text="Дополнительные работы", style="Form.TLabel")
        description_e = tk.Text(win, height=8, width=50, font=("Sergoe UI", 8), )
        form.add_12(description_lbl, description_e)

        # Сохранение новой запчасти
        def save():
            service_id = services_cb.get_fk_id() # Получение id выбора производителя
            car_id = self.get_selected_car_id()  # get selected car_id

            # 1. Вставка ТО
            cur = self.db.execute("""
                INSERT INTO service_history
                (car_id, service_date, mileage, sto_id, amount, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                car_id,
                date_entry.get(),
                mileage_e.get(),
                service_id,
                amount_e.get(),
                description_e.get("1.0", tk.END)
            ))

            service_history_id = cur.lastrowid  # Получаем id последней записи

            # 2. Вставка выполненных работ
            for task_id, var in task_vars.items():
                if var.get():
                    self.db.execute("""
                        INSERT INTO service_history_tasks
                        (service_history_id, service_task_id)
                        VALUES (?, ?)
                    """, (service_history_id, task_id))

            win.destroy()
            self.refresh_all()

        #   Кнопки        
        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Сохранить", style="Form_Com.TButton", command=save)
        close_btn = ttk.Button(btn_frame, text="Отмена", style="Form_Com.TButton", command=win.destroy)
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        form.button(btn_frame)

    def edit_service_history(self, event=None):
        item = self.service_history_table.selection()
        if not item:
            return

        values = self.service_history_table.item(item, "values")           # type: ignore
        sh_id, s_date, _, mileage, service_name, amount , _ , description = values 

        car_id = self.get_selected_car_id()

        win = tk.Toplevel(self)
        self.create_dialog_window(self, win, "Редактор ТО")
        form = FormGrid(win, 3)  # parent, количество колонок

        # Дата
        date_lbl = ttk.Label(win, text="Дата", style="Form.TLabel")
        date_entry = DateEntry(
            win,
            date_pattern="yyyy-mm-dd",
            width=18,
            style="Form.TCombobox"
        )
        date_entry.set_date(s_date)
        date_com_lbl = ttk.Label(win, text="Формат: ГГГГ-ММ-ДД", style="Form_Com.TLabel")
        form.add(date_lbl, date_entry, date_com_lbl)
        
        # Пробег
        mileage_var = tk.StringVar()
        mileage_var.set(str(mileage))         
        mileage_lbl = ttk.Label(win, text="Пробег", style="Form.TLabel")
        mileage_e = ttk.Entry(win, textvariable=mileage_var, justify="right", style="Form.TEntry")
        mileage_var.trace_add("write", lambda *_: self.validate_float(mileage_var,mileage_e)) # Проверка на число
        mileage_e.bind("<FocusOut>", lambda e: self.normalize(mileage_var, mileage_e, 0))    # Нормализация к формату
        mileage_com_lbl = ttk.Label(win, text="на момент ТО", style="Form_Com.TLabel")       
        form.add(mileage_lbl, mileage_e, mileage_com_lbl)

        # СТО fk
        services = self.db.fetchall(
            "SELECT id, name FROM services ORDER BY name"
        )
        # Создание выпадающего списка для типа запчасти
        services_lbl = ttk.Label(win, text="СТО", style="Form.TLabel")
        services_cb = FKCombobox(
            win,
            fk_data=services,
            state="readonly",
            style="Form.TCombobox"
        )
        for ss_id, ss_name in services:
            if ss_name == service_name:
                services_cb.current(services.index((ss_id, ss_name)))
                break
        form.add(services_lbl, services_cb)

        # Стоимость
        amount_var = tk.StringVar()
        amount_var.set(str(amount))               
        amount_lbl = ttk.Label(win, text="Стоимость", style="Form.TLabel")
        amount_e = ttk.Entry(win, textvariable=amount_var, justify="right", style="Form.TEntry")
        amount_var.trace_add("write", lambda *_: self.validate_float(amount_var,amount_e)) # Проверка на число
        amount_e.bind("<FocusOut>", lambda e: self.normalize(amount_var, amount_e, 2))    # Нормализация к формату
        amount_com_lbl = ttk.Label(win, text="по заказ наряду", style="Form_Com.TLabel")        
        form.add(amount_lbl, amount_e, amount_com_lbl)

        # Работы по регламенту
        tasks_lbl = ttk.Label(win, text="Работы по регламенту", style="Form.TLabel")
        tasks_frame = ttk.Frame(win)
        form.add_12(tasks_lbl, tasks_frame)

        # Формируем Checkbox'ы
        tasks = self.db.fetchall(
            "SELECT id, abbr, name FROM service_tasks WHERE car_id = ? ORDER BY name"
        , (car_id,))

        done = set(
            r[0] for r in self.db.fetchall(
                "SELECT service_task_id FROM service_history_tasks WHERE service_history_id=?",
                (sh_id,)
            )
        )

        task_vars = {}  # service_task_id -> BooleanVar

        for tid, abbr, name in tasks:
            var = tk.BooleanVar()
            var.set(tid in done)
            cb = ttk.Checkbutton(
                tasks_frame,
                text=f"[{abbr}] {name}",
                variable=var
            )
            cb.pack(anchor="w")
            task_vars[tid] = var


        # Дополнительные работы
        description_lbl = ttk.Label(win, text="Дополнительные работы", style="Form.TLabel")
        description_e = tk.Text(win, height=6, width=40, font=("Sergoe UI", 8))
        description_e.insert("1.0", description)           
        form.add_12(description_lbl, description_e)

        # Сохранение новой запчасти
        def save():
            # --- 1. Чтение значений формы ---
            try:
                #car_id = self.get_selected_car_id() # car
                service_date = date_entry.get() # date
                mileage = int(mileage_var.get())   # mileage
                sto_id = services_cb.get_fk_id() # sto (может быть NULL)
                amount = amount_var.get()
                description = description_e.get("1.0", tk.END)  # description

            except Exception as e:
                messagebox.showerror(
                    "Ошибка",
                    f"Некорректно заполнены поля:\n{e}"
                )
                return

            # --- 2. Валидация ---
            if not service_date:
                messagebox.showerror("Ошибка", "Дата ТО обязательна")
                return

            if mileage <= 0:
                messagebox.showerror("Ошибка", "Пробег должен быть больше 0")
                return

            # --- 3. Сохранение в БД ---
            # === EDIT ===
            self.db.execute("""
                UPDATE service_history
                SET service_date=?,
                    mileage=?,
                    sto_id=?,
                    amount=?,
                    description=?
                WHERE id=?
            """, (
                service_date,
                mileage,
                sto_id,
                amount,
                description,
                sh_id
            ))

            # удаляем старые работы
            self.db.execute("""
                DELETE FROM service_history_tasks
                WHERE service_history_id=?
            """, (sh_id,))

            # --- 4. Сохранение стандартных работ ---
            for task_id, var in task_vars.items():
                if var.get():
                    self.db.execute("""
                        INSERT INTO service_history_tasks
                        (service_history_id, service_task_id)
                        VALUES (?, ?)
                    """, (sh_id, task_id))

            # --- 5. Обновление UI ---
            self.refresh_all()
            win.destroy()

        #   Кнопки        
        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Сохранить", style="Form_Com.TButton", command=save)
        close_btn = ttk.Button(btn_frame, text="Отмена", style="Form_Com.TButton", command=win.destroy)
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        form.button(btn_frame)
    
    def delete_service_history(self):
        tree = self.service_history_table
        item = tree.focus()

        if not item:
            messagebox.showwarning(
                "Удаление ТО",
                "Сначала выберите запись технического обслуживания"
            )
            return

        values = tree.item(item)["values"]
        service_history_id = values[0]
        service_date = values[1]
        car_name = values[2]

        if not messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить ТО от {service_date}\nАвто: {car_name}?"
        ):
            return

        # удаляем связанные стандартные работы
        self.db.execute("""
            DELETE FROM service_history_tasks
            WHERE service_history_id=?
        """, (service_history_id,))

        # удаляем связь купленных запчастей
        self.db.execute("""
            UPDATE part_purchases
            SET service_history_id = NULL
            WHERE service_history_id=?
        """, (service_history_id,))

        # удаляем само ТО
        self.db.execute("""
            DELETE FROM service_history
            WHERE id=?
        """, (service_history_id,))

        self.refresh_all()

    def buy_part_to_service_history(self):
        item = self.service_history_table.focus()
        if not item:
            return

        service_history_id = self.service_history_table.item(item)["values"][0]

        # Открываем окно покупки с предустановленным ТО
        self.add_part_purchase(service_history_id=service_history_id)
        
    def add_part_to_service_history(self):
        item = self.service_history_table.focus()
        if not item:
            return

        service_history_id = self.service_history_table.item(item)["values"][0]

        # Открываем окно покупки с предустановленным ТО
        self.add_purchases_part(service_history_id=service_history_id)

    # ---------- Fuel / Топливо----------
    def build_fuel_tab(self):

        tab = self.tab_fuel                # !!!!!!!
        table_name = "fuel"                # !!!!!!!

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

         # Таблица (с закреплённой строкой итогов)
        self.fuel_table, self.fuel_total = self.build_tree(tab, table_name, with_total_row=True)

        tree = self.fuel_table            # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }
        # Подключаем CRUD
        self.fuel_crud = self.create_crud(table_name, tree, self.fuel_update_sum, self.fuel_total)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.fuel_crud)

    def fuel_update_sum(self, total):
        self.sum_fuel_var.set(f"{total:.2f}")
        self.recalc_amount()

    # ---------- Purchases / Покупки запчастей ----------
    def build_part_purchases_tab(self):
        tab = self.tab_part_purchases                # !!!!!!!
        table_name = "part_purchases"                # !!!!!!!

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

         # Таблица (с закреплённой строкой итогов)
        self.part_purchases_table, self.part_purchases_total = self.build_tree(tab, table_name, with_total_row=True)

        tree = self.part_purchases_table             # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.part_purchases_crud = self.create_crud(table_name, tree, self.part_purchases_update_sum, self.part_purchases_total)

        # Toolbar - Дополнительные кнопки
        toolbar = Toolbar(top, self)
        toolbar.pack(side="left", pady=2)
        toolbar.add_button(icon="add", command=self.add_part_purchase, tooltip="Добавить покупку")
        toolbar.add_button(icon="edit", command=self.edit_part_purchase, tooltip="Редактировать")
        toolbar.add_button(icon="delete", command=self.delete_part_purchase, tooltip="Удалить запись")
        toolbar.add_separator()
        toolbar.add_button(icon="wrench", command=self.open_part_from_purchase, tooltip="Перейти к запчасти")
        toolbar.add_separator()

        # Фильтры
        filters_fr = ttk.Frame(top)
        filters_fr.pack(fill="x", padx=5, pady=5)

        # Иконка фильтров 
        self.image_label(filters_fr, icon="filter", ttext=":", im_padx=10)

        # 🛠 Фильтр по обращению на СТО
        ttk.Label(filters_fr, text="ТО: ").pack(side="left", padx=(10, 0))
        self.serv_cb = ttk.Combobox(filters_fr, state="readonly", width=30)
        self.serv_cb.pack(side="left", padx=5)
        self.serv_cb.bind("<<ComboboxSelected>>", lambda e: self.load_part_purchases())

        # Reset filters button
        ttk.Button(filters_fr, text="Сброс", command=self.reset_part_purchases_filters, width=7).pack(side="left", padx=10)

        # Bind double-click to edit
        self.part_purchases_table.bind("<Double-1>", self.edit_part_purchase)
        self.part_purchases_table.bind("<Delete>", lambda e: self.delete_part_purchase())        
        
        # Заполнение фильтров
        self.load_part_purchases_filters()
        
        # Context menu
        self.attach_context_menu(
            self.part_purchases_table,
            [
                ("Открыть запчасть", self.open_part_from_purchase),
                ("---", None),
                ("Редактировать", self.edit_part_purchase),
                ("Удалить", self.delete_part_purchase)
            ]
        )

    def load_part_purchases_filters(self):
        
        car_id = self.get_selected_car_id()

        # Работы
        sql = """
                SELECT 
                sh.id, 
                sh.service_date || ' / ' || s.name AS sname 
                FROM service_history sh 
                JOIN services s ON s.id = sto_id 
                WHERE sh.car_id = ? 
                ORDER BY sname DESC
            """
        rows = self.db.fetchall(sql, [car_id])
        self._serv = rows
        self.serv_cb["values"] = ["Все"] +[r[1] for r in rows] + ["Нет"]
        self.serv_cb.current(0)   

    def reset_part_purchases_filters(self):
        self.serv_cb.current(0)
        self.load_part_purchases_filters()

    def part_purchases_update_sum(self, total):
        self.sum_parts_var.set(f"{total:.2f}")
        self.recalc_amount()

    def load_part_purchases(self):

        car_id = self.get_selected_car_id()
        if not car_id:
            return
    
        self.part_purchases_table.delete(*self.part_purchases_table.get_children())

        where = []
        params = []

        # Автомобиль
        if self.filter_by_car.get():
            where.append("pp.car_id = ?")
            params.append(car_id)       

        # 📦 Серввис 
        idx = self.serv_cb.current()
        if self.serv_cb.get() == "Нет":
            where.append("pp.service_history_id is NULL")
        elif idx > 0:
            where.append("pp.service_history_id = ?")
            params.append(self._serv[idx - 1][0])


        # Период дат
        if self.filter_by_date.get():
            date_from, date_to = self.get_date_filter()

            if date_from:
                where.append("pp.purchase_date >= ?")
                params.append(date_from)

            if date_to:
                where.append("pp.purchase_date <= ?")
                params.append(date_to)

        sql = """
            SELECT
                pp.id,
                pp.purchase_date,               
                c.manufacturer || ' ' || c.name || ' - ' || c.plate_number AS car,
                p.article || ' ' || p.name || ' ' || m.name AS part_display,
                pp.quantity,
                pp.price,
                ROUND(pp.quantity * pp.price, 2) AS total,
                sh.service_date || ' / ' ||  s.name AS serviceday, 
                p.id AS part_id
            FROM part_purchases pp
            JOIN cars c ON c.id = pp.car_id
            JOIN parts p ON p.id = pp.part_id
            LEFT JOIN service_history sh ON sh.id = pp.service_history_id
            LEFT JOIN services s ON s.id = sh.sto_id
            JOIN manufacturers m ON m.id = p.manufacturer_id
        """
        #sh.service_date || ' / ' ||  s.name AS serviceday, 
        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY pp.purchase_date DESC"            

        rows = self.db.fetchall(sql, params)

        for r in rows:
            self.part_purchases_table.insert(
                "",
                "end",
                values=r[:-1],
                tags=(f"part:{r[-1]}",)
            )
        
        # Строка итогов
        total_cost = sum(float(r[6]) for r in rows)

        self.sum_parts_var.set(self.format_currency(total_cost))
        self.recalc_amount()
        
        # Обновляем закреплённую строку итогов
        if self.part_purchases_total:
            self.part_purchases_total.delete(*self.part_purchases_total.get_children())
            self.part_purchases_total.insert("", "end",
                values=("", "", "", "", "", "", self.sum_parts_var.get(), "", ""),
                tags=("total",)
            )

    def fetch_parts (self):
               
        sql = """
            SELECT
                p.id,
                p.article || ' ' || p.name || ' ' || m.name AS part_display
            FROM parts p
            LEFT JOIN manufacturers m ON m.id = p.manufacturer_id
            ORDER BY 2
            """

        return self.db.fetchall(sql)
    
    def fetch_purchases_parts (self):
        car_id = self.get_selected_car_id()       
        sql = """
            SELECT
                pp.id,
                p.article || ' ' || p.name || ' ' || m.name AS part_display
            FROM part_purchases pp
            JOIN parts p ON p.id = pp.part_id
            LEFT JOIN manufacturers m ON m.id = p.manufacturer_id
            WHERE pp.service_history_id IS NULL 
                AND pp.car_id = ?
            ORDER BY part_display
            """

        return self.db.fetchall(sql, [car_id])

    def add_purchases_part(self, service_history_id=None):

        if service_history_id:
           service_history_id_var = int(service_history_id)  # просто храним
        else: 
           service_history_id_var = None 

        win = tk.Toplevel(self)
        title = "Добавить запчасть"
        self.create_dialog_window(self, win, title)
        form = FormGrid(win, 3)  # parent, количество колонок

        # Дата покупки
        # date_lbl = ttk.Label(win, text="Дата", style="Form.TLabel")
        # date_entry = DateEntry(
        #     win,
        #     date_pattern="yyyy-mm-dd",
        #     width=18,
        #     style="Form.TCombobox"
        # )
        # date_entry.set_date(date.today())
        # date_com_lbl = ttk.Label(win, text="Формат: ГГГГ-ММ-ДД", style="Form_Com.TLabel")
        # if not already : 
        #     form.add(date_lbl, date_entry, date_com_lbl)

        # Запчасть
        part_lbl = ttk.Label(win, text="Запчасть", style="Form.TLabel")
        data = self.fetch_purchases_parts()
        part_combobox = FKCombobox(
            win,
            fk_data=data,
            state="readonly",
            width=35,
            style="Form.TCombobox"
        )
        form.add_12(part_lbl, part_combobox)

        # Предустановка запчасти из параметра preset
        # if preset and "part_id" in preset:
        #     part_combobox.set_by_id(preset["part_id"], disable=True)
        
        # Количество
        # quantity_var = tk.StringVar()
        # quantity_var.set(str('1.0'))        
        # quantity_lbl = ttk.Label(win, text="Количество", style="Form.TLabel")
        # quantity_e = ttk.Entry(win, width=20, justify="right", textvariable=quantity_var, style="Form.TEntry")
        # quantity_var.trace_add("write", lambda *_: self.validate_float(quantity_var,quantity_e)) # Проверка на число
        # quantity_e.bind("<FocusOut>", lambda e: self.normalize(quantity_var, quantity_e, 1))    # Нормализация к формату
        # #quantity_e.var = quantity_var
        # form.add(quantity_lbl, quantity_e)

        # # Цена
        # price_var = tk.StringVar()
        # price_var.set(str('0.00'))
        # price_lbl = ttk.Label(win, text="Цена", style="Form.TLabel")
        # price_e = ttk.Entry(win, justify="right", textvariable=price_var, style="Form.TEntry")
        # price_var.trace_add("write", lambda *_: self.validate_float(price_var, price_e)) # Проверка на число
        # price_e.bind("<FocusOut>", lambda e: self.normalize(price_var, price_e))    # Нормализация к формату
        # price_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        # form.add(price_lbl, price_e, price_com_lbl)

        # # Сумма
        # total = tk.StringVar()        
        # total_lbl = ttk.Label(win, text="Сумма", style="Form.TLabel")
        # total_entry = ttk.Entry(win, textvariable=total, state="readonly", justify="right", style="Form.TEntry")
        # total_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        # form.add(total_lbl, total_entry, total_com_lbl)

        # ID ТО
        # car_id = self.get_selected_car_id()
        # sh_id_lbl = ttk.Label(win, text="ID ТО", style="Form.TLabel")
        # service_history_data = self.db.fetchall("""
        #                                         SELECT 
        #                                         sh.id, 
        #                                         sh.service_date || ' / ' || s.name AS sname 
        #                                         FROM service_history sh 
        #                                         JOIN services s ON s.id = sto_id 
        #                                         WHERE sh.car_id = ? 
        #                                         ORDER BY sname DESC
        #     """, [car_id])
        # sh_id_combobox = FKCombobox(
        #     win,
        #     fk_data=service_history_data,
        #     style="Form.TCombobox",
        #     state="readonly",
        #     width=30
        # )
        # form.add_12(sh_id_lbl, sh_id_combobox)

        # Предустановка сервиса
        # for sh_id, sh_name in service_history_data:
        #     if sh_id == service_history_id_var:
        #         sh_id_combobox.current(service_history_data.index((sh_id, sh_name)))
        #         break

        # # Расчет суммы
        # self.recalc_mul(quantity_var,price_var,total)
        # price_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))
        # quantity_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))

        def save():
            purchase_id = part_combobox.get_fk_id()  # get selected part_id from combobox
       
       
            self.db.execute("""
                UPDATE part_purchases
                SET service_history_id=?
                WHERE id=?
            """, (
                service_history_id,
                purchase_id
            ))       
       
            win.destroy()
            self.refresh_all()

        #   Кнопки        
        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Добавить", style="Form_Com.TButton", command=save)
        close_btn = ttk.Button(btn_frame, text="Отмена", style="Form_Com.TButton", command=win.destroy)
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        form.button(btn_frame)

    def add_part_purchase(self, service_history_id=None ,preset=None):

        if service_history_id:
           service_history_id_var = int(service_history_id)  # просто храним
        else: 
           service_history_id_var = None 

        win = tk.Toplevel(self)
        title = "Покупка запчасти"
        self.create_dialog_window(self, win, title)
        form = FormGrid(win, 3)  # parent, количество колонок

        # Дата покупки
        date_lbl = ttk.Label(win, text="Дата", style="Form.TLabel")
        date_entry = DateEntry(
            win,
            date_pattern="yyyy-mm-dd",
            width=18,
            style="Form.TCombobox"
        )
        date_entry.set_date(date.today())
        date_com_lbl = ttk.Label(win, text="Формат: ГГГГ-ММ-ДД", style="Form_Com.TLabel")
        form.add(date_lbl, date_entry, date_com_lbl)

        # Запчасть
        part_lbl = ttk.Label(win, text="Запчасть", style="Form.TLabel")
        data = self.fetch_parts()
        part_combobox = FKCombobox(
            win,
            fk_data=data,
            state="readonly",
            width=35,
            style="Form.TCombobox"
        )
        form.add_12(part_lbl, part_combobox)

        # Предустановка запчасти из параметра preset
        if preset and "part_id" in preset:
            part_combobox.set_by_id(preset["part_id"], disable=True)
        
        # Количество
        quantity_var = tk.StringVar()
        quantity_var.set(str('1.0'))        
        quantity_lbl = ttk.Label(win, text="Количество", style="Form.TLabel")
        quantity_e = ttk.Entry(win, width=20, justify="right", textvariable=quantity_var, style="Form.TEntry")
        quantity_var.trace_add("write", lambda *_: self.validate_float(quantity_var,quantity_e)) # Проверка на число
        quantity_e.bind("<FocusOut>", lambda e: self.normalize(quantity_var, quantity_e, 1))    # Нормализация к формату
        #quantity_e.var = quantity_var
        form.add(quantity_lbl, quantity_e)

        # Цена
        price_var = tk.StringVar()
        price_var.set(str('0.00'))
        price_lbl = ttk.Label(win, text="Цена", style="Form.TLabel")
        price_e = ttk.Entry(win, justify="right", textvariable=price_var, style="Form.TEntry")
        price_var.trace_add("write", lambda *_: self.validate_float(price_var, price_e)) # Проверка на число
        price_e.bind("<FocusOut>", lambda e: self.normalize(price_var, price_e))    # Нормализация к формату
        price_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        form.add(price_lbl, price_e, price_com_lbl)

        # Сумма
        total = tk.StringVar()        
        total_lbl = ttk.Label(win, text="Сумма", style="Form.TLabel")
        total_entry = ttk.Entry(win, textvariable=total, state="readonly", justify="right", style="Form.TEntry")
        total_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        form.add(total_lbl, total_entry, total_com_lbl)

        # ID ТО
        car_id = self.get_selected_car_id()
        sh_id_lbl = ttk.Label(win, text="ID ТО", style="Form.TLabel")
        service_history_data = self.db.fetchall("""
                                                SELECT 
                                                sh.id, 
                                                sh.service_date || ' / ' || s.name AS sname 
                                                FROM service_history sh 
                                                JOIN services s ON s.id = sto_id 
                                                WHERE sh.car_id = ? 
                                                ORDER BY sname DESC
            """, [car_id])
        sh_id_combobox = FKCombobox(
            win,
            fk_data=service_history_data,
            style="Form.TCombobox",
            state="readonly",
            width=30
        )
        form.add_12(sh_id_lbl, sh_id_combobox)

        # Предустановка сервиса
        for sh_id, sh_name in service_history_data:
            if sh_id == service_history_id_var:
                sh_id_combobox.current(service_history_data.index((sh_id, sh_name)))
                break

        # Расчет суммы
        self.recalc_mul(quantity_var,price_var,total)
        price_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))
        quantity_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))

        def save():
            car_id = self.get_selected_car_id()  # get selected car_id
            part_id = part_combobox.get_fk_id()  # get selected part_id from combobox
            service_history_id = sh_id_combobox.get_fk_id()
            
            self.db.execute("""
                INSERT INTO part_purchases (car_id, part_id, quantity, price, purchase_date, service_history_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                car_id,
                part_id,
                float(quantity_var.get()),
                float(price_var.get()),
                date_entry.get(),
                service_history_id
            ))

            win.destroy()
            self.refresh_all()

        #   Кнопки        
        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Сохранить", style="Form_Com.TButton", command=save)
        close_btn = ttk.Button(btn_frame, text="Отмена", style="Form_Com.TButton", command=win.destroy)
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        form.button(btn_frame)

    def edit_part_purchase(self, event = None):
        item = self.part_purchases_table.selection()
        if not item:
            return

        values = self.part_purchases_table.item(item, "values")           # type: ignore
        purchase_id, purchase_date, car, part, quantity, price, total, sh_id_t = values

        win = tk.Toplevel(self)
        self.create_dialog_window(self, win, "Редактирование покупки запчасти")
        form = FormGrid(win, 3)  # parent, количество колонок
        
        # Автомобиль
        cars_lbl = ttk.Label(win, text="Автомобиль", style="Form.TLabel")
        cars = self.db.fetchall("SELECT id, manufacturer || ' ' || name || ' - ' || plate_number FROM cars ORDER BY manufacturer, name")
        car_combobox = FKCombobox(
            win,
            fk_data=cars,
            style="Form.TCombobox",
            state="readonly",
            width=30
        )
        # Предустановка автомобиляa
        for car_id, car_name in cars:
            if car_name == car:
                car_combobox.current(cars.index((car_id, car_name)))
                break
        form.add_12(cars_lbl, car_combobox)

        # Дата покупки
        date_lbl = ttk.Label(win, text="Дата", style="Form.TLabel")
        date_entry = DateEntry(
            win,
            date_pattern="yyyy-mm-dd",
            width=18,
            style="Form.TCombobox"
        )
        date_entry.set_date(purchase_date)
        date_com_lbl = ttk.Label(win, text="Формат: ГГГГ-ММ-ДД", style="Form_Com.TLabel")
        form.add(date_lbl, date_entry, date_com_lbl)

        # Запчасть
        part_lbl = ttk.Label(win, text="Запчасть", style="Form.TLabel")
        data = self.fetch_parts()
        part_combobox = FKCombobox(
            win,
            fk_data=data,
            state="readonly",
            width=35,
            style="Form.TCombobox"
        )
        form.add_12(part_lbl, part_combobox)
        
        # Предустановка запчасти
        for part_id, part_name in data:
            if part_name == part:
                part_combobox.current(data.index((part_id, part_name)))
                break
       
        # Количество
        quantity_var = tk.StringVar()
        quantity_var.set(quantity)        
        quantity_lbl = ttk.Label(win, text="Количество", style="Form.TLabel")
        quantity_e = ttk.Entry(win, width=20, justify="right", textvariable=quantity_var, style="Form.TEntry")
        quantity_var.trace_add("write", lambda *_: self.validate_float(quantity_var,quantity_e)) # Проверка на число
        quantity_e.bind("<FocusOut>", lambda e: self.normalize(quantity_var, quantity_e, 1))    # Нормализация к формату
        #quantity_e.var = quantity_var
        form.add(quantity_lbl, quantity_e)

        # Цена
        price_var = tk.StringVar()
        price_var.set(price)
        price_lbl = ttk.Label(win, text="Цена", style="Form.TLabel")
        price_e = ttk.Entry(win, justify="right", textvariable=price_var, style="Form.TEntry")
        price_var.trace_add("write", lambda *_: self.validate_float(price_var, price_e)) # Проверка на число
        price_e.bind("<FocusOut>", lambda e: self.normalize(price_var, price_e))    # Нормализация к формату
        price_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        form.add(price_lbl, price_e, price_com_lbl)
        
        # Сумма
        total = tk.StringVar()        
        total_lbl = ttk.Label(win, text="Сумма", style="Form.TLabel")
        total_entry = ttk.Entry(win, textvariable=total, state="readonly", justify="right", style="Form.TEntry")
        total_com_lbl = ttk.Label(win, text="рублей", style="Form_Com.TLabel")
        form.add(total_lbl, total_entry, total_com_lbl)

        # ID ТО
        sh_id_lbl = ttk.Label(win, text="ID ТО", style="Form.TLabel")
        service_history_data = self.db.fetchall("""
                                                SELECT 
                                                sh.id, 
                                                sh.service_date || ' / ' || s.name || ' / ' || c.manufacturer || ' ' || c.name || ' - ' || c.plate_number,
                                                sh.service_date || ' / ' || s.name AS sname
                                                FROM service_history sh 
                                                JOIN services s ON s.id = sto_id
                                                JOIN cars c ON c.id = sh.car_id
                                                ORDER BY sname DESC
                                                """)
        service_history_data.insert(0, (0, "Нет", "None"))
        sh_id_combobox = FKCombobox(
            win,
            fk_data=[row[:2] for row in service_history_data],
            style="Form.TCombobox",
            state="readonly",
            width=40
        )
        form.add_12(sh_id_lbl, sh_id_combobox)

        # Предустановка сервиса
        for sh_id, sh_name, sh_t_name in service_history_data:
            if sh_t_name == sh_id_t:
                sh_id_combobox.current(service_history_data.index((sh_id, sh_name, sh_t_name)))
                break


        # Расчет суммы
        self.recalc_mul(quantity_var,price_var,total)
        price_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))
        quantity_var.trace_add("write", lambda *args: self.recalc_mul(quantity_var, price_var, total))

        def save():
            if not self.valid_date(date_entry.get()):
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте YYYY-MM-DD.")
                return
            
            part_id = part_combobox.get_fk_id()  # get selected part_id from combobox
            car_id = car_combobox.get_fk_id()  # get selected car_id from combobox
            
            if sh_id_combobox.get_fk_id() > 0:
                try:
                    sh_id = sh_id_combobox.get_fk_id()
                except:
                    messagebox.showerror("Ошибка", "ID ТО должен быть ЦЕЛЫМ!")
                    return
            else:
                sh_id = None
                
            self.db.execute("""
                UPDATE part_purchases
                SET car_id=?, purchase_date=?, part_id=?, quantity=?, price=?, service_history_id=?
                WHERE id=?
            """, (
                car_id,
                date_entry.get(),
                part_id,
                float(quantity_var.get()),
                float(price_var.get()),
                sh_id,
                purchase_id
            ))
            win.destroy()
            self.refresh_all()

        def delete():
            if messagebox.askyesno("Удалить", "Удалить запись о покупке запчасти?"):
                self.db.execute("DELETE FROM part_purchases WHERE id=?", (purchase_id,))
            win.destroy()
            self.refresh_all()

        #   Кнопки        
        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Сохранить", style="Form_Com.TButton", command=save)
        close_btn = ttk.Button(btn_frame, text="Отмена", style="Form_Com.TButton", command=win.destroy)
        delete_btn = ttk.Button(btn_frame, text="Удалить", style="Form_Com.TButton", command=delete)
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        delete_btn.pack(side="right")
        form.button(btn_frame)

    def delete_part_purchase(self):
        tree = self.part_purchases_table
        item = tree.focus()

        if not item:
            messagebox.showwarning(
                "Удаление факта покупки",
                "Сначала выберите купленную запчасть"
            )
            return

        values = tree.item(item)["values"]
        part_purchase_id = values[0]
        purchase_date = values[1]
        car_name = values[2]

        if not messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить покупку от {purchase_date}\nАвто: {car_name}?"
        ):
            return

        # удаляем связанные стандартные работы
        self.db.execute("""
            DELETE FROM part_purchases
            WHERE id=?
        """, (part_purchase_id,))

        self.refresh_all()

    def open_part_from_purchase(self):
        
        sel = self.part_purchases_table.selection()
        if not sel:
            return

        values = self.part_purchases_table.item(sel[0], "values")

        # print(values[3])
        data = self.fetch_parts()
        for p_id, part_name in data:
            if part_name == values[3]:
                part_id = p_id
                break

        if not part_id:
            messagebox.showerror("Ошибка", "Не удалось определить запчасть")
            return

        # Переключаемся на вкладку запчастей
        self.tabs.select(self.tab_parts)

        # Обновляем таблицу (на случай фильтров)
        self.parts_crud.load()

        # Ищем строку с нужным ID
        for row in self.parts_table.get_children():
            values = self.parts_table.item(row, "values")
            if int(values[0]) == part_id:
                self.parts_table.selection_set(row)
                self.parts_table.see(row)
                self.parts_table.focus(row)
                return

        messagebox.showinfo("Не найдено", "Запчасть не найдена в справочнике")

    # ---------- Parts / Запчасти ----------
    def build_parts_tab(self):
        tab = self.tab_parts                # !!!!!!!
        table_name = "parts"                # !!!!!!!   

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)
      
        # Таблица
        self.parts_table, _ = self.build_tree(tab, table_name)
        #self.parts_table.pack(fill="both", expand=True, padx=10, pady=10) 

        tree = self.parts_table              # !!!!!!!
        # Double-click to edit

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.parts_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        toolbar = Toolbar(top, self)
        toolbar.pack(side="left", pady=2)
        # Buttons
        crud_item = self.parts_crud         
        toolbar.add_button(icon="add", command=crud_item.add, tooltip="Добавить запчасть (CTRL+N)")
        toolbar.add_button(icon="edit", command=crud_item.edit, tooltip="Редактировать запчасть")
        toolbar.add_button(icon="delete", command=crud_item.delete, tooltip="Удалить запчасть (DEL)")
        toolbar.add_separator()
        toolbar.add_button(icon="buy", command=self.buy_selected_part, tooltip="Купить запчасть")
        toolbar.add_separator()

        crud_item.build_filter_panel(top)

        # Double-click to edit
        tree.bind("<Double-1>", crud_item.edit)
        tree.bind("<Delete>", lambda e: crud_item.edit())

        self.attach_context_menu(
            tree,
            [
                ("Редактировать", crud_item.edit),
                ("Удалить", crud_item.delete),
                ("---", None),
                ("Купить", self.buy_selected_part)
            ]
        )  

    def add_part(self):   # Используется для buy_selected_part
        win = tk.Toplevel(self)
        win.title("Запчасть")
        win.geometry("300x200")
        win.resizable(False, False)

        # Название запчасти
        ttk.Label(win, text="Название").grid(row=0, column=0, padx=10, pady=10)
        entry = ttk.Entry(win)
        entry.grid(row=0, column=1, padx=10, pady=10)

        # --------------- Добавление производителя ----------------------------
        manufacturers = self.db.fetchall( # 
            "SELECT id, name FROM manufacturers ORDER BY name"
        )
        
        ttk.Label(win, text="Производитель").grid(row=1, column=0, padx=10, pady=10, sticky="e")

        manuf_cb = FKCombobox(
            win,
            fk_data=manufacturers,
            state="readonly"
        )
        manuf_cb.grid(row=1, column=1, padx=10, pady=10)

        # --------------- Добавление типа запчасти ----------------------------
        part_types = self.db.fetchall(
            "SELECT id, name FROM part_types ORDER BY name"
        )
        # Создание выпадающего списка для типа запчасти
        ttk.Label(win, text="Тип запчасти").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        part_type_cb = FKCombobox(
            win,
            fk_data=part_types,
            state="readonly"
        )
        part_type_cb.grid(row=2, column=1, padx=10, pady=10)

        # --------------- Добавление системы автомобиля ----------------------------
        car_systems = self.db.fetchall(
            "SELECT id, name FROM car_systems ORDER BY name"
        )
        # Создание выпадающего списка для системы автомобиля
        ttk.Label(win, text="Система автомобиля").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        
        system_cb = FKCombobox(
            win,
            fk_data=car_systems,
            state="readonly"
        ) 
        system_cb.grid(row=3, column=1, padx=10, pady=10)

        # Сохранение новой запчасти
        def save():
            manufacturer_id = manuf_cb.get_fk_id() # Получение id выбора производителя
            types_id = part_type_cb.get_fk_id() # Получение id выбора типа запчасти
            systems_id = system_cb.get_fk_id() # Получение id выбора системы автомобиля

            self.db.execute("INSERT INTO parts(name, manufacturer_id, type_id, system_id) VALUES(?, ?, ?, ?)", (entry.get(), manufacturer_id, types_id, systems_id))
            win.destroy()
            self.refresh_all()

        #   Кнопка сохранения
        ttk.Button(win, text="Сохранить", command=save).grid(row=4, column=1, padx=10, pady=10)

    def buy_selected_part(self):
        sel = self.parts_table.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите запчасть в таблице")
            return

        values = self.parts_table.item(sel[0], "values")
        part_id = values[0]

        self.add_part_purchase(
            preset={
                "part_id": part_id
            }
        )

    # ---------- Cars / Автомобили ----------
    def build_cars_tab(self):
 
        tab = self.tab_cars                # !!!!!!!
        table_name = "cars"                # !!!!!!!   

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.cars_table, _ = self.build_tree(tab, table_name)
#        self.cars_table.pack(fill="both", expand=True, padx=10, pady=10)      

        tree = self.cars_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.cars_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.cars_crud)

    def load_cars_combo(self):  # Загрузка автомобилей в комбобокс
        rows = self.db.fetchall(
            "SELECT id, manufacturer || ' ' || name || ' - ' || plate_number FROM cars ORDER BY manufacturer, name"
        )

        self._cars_combo_data = rows  # сохраняем соответствие id ↔ имя
        self.car_combo["values"] = [r[1] for r in rows]

        if rows and self.car_combo.get() == "":
            self.car_combo.current(0)

    def get_selected_car_id(self):
        idx = self.car_combo.current()
        if idx == -1:
            return None
        return self._cars_combo_data[idx][0]
    
    # ---------- Manufacturers / Производители запчастей ----------
    def build_manufacturers_tab(self):
        
        tab = self.tab_manufacturers                # !!!!!!!
        table_name = "manufacturers"                # !!!!!!!   

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.manufacturers_table, _ = self.build_tree(tab, table_name)
#        self.manufacturers_table.pack(fill="both", expand=True, padx=10, pady=10) 

        tree = self.manufacturers_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }
        # Подключаем CRUD
        self.manufacturers_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.manufacturers_crud)

   # ---------- Part types / Типы запчастей----------
    def build_part_types_tab(self):

        tab = self.tab_part_types                # !!!!!!!
        table_name = "part_types"                # !!!!!!!   


        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.part_types_table, _ = self.build_tree(tab, table_name)
#        self.part_types_table.pack(fill="both", expand=True, padx=10, pady=10) 

        tree = self.part_types_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.part_types_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.part_types_crud)

   # ---------- Car systems / Системы автомобиля----------
    def build_car_systems_tab(self):

        tab = self.tab_car_systems                # !!!!!!!
        table_name = "car_systems"                # !!!!!!!   

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.car_systems_table, _ = self.build_tree(tab, table_name)
#        self.car_systems_table.pack(fill="both", expand=True, padx=10, pady=10)         

        tree = self.car_systems_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.car_systems_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.car_systems_crud)

   # ---------- Services / Станции СТО ----------
    def build_services_tab(self):
        
        tab = self.tab_services                # !!!!!!!
        table_name = "services"                # !!!!!!!        

        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.services_table, _ = self.build_tree(tab, table_name)
        #self.services_table.pack(fill="both", expand=True, padx=10, pady=10)        

        tree = self.services_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.services_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.services_crud)

    # ---------- Ехpenses types / Типы расходов ----------
    def build_expense_types_tab(self):
        
        tab = self.tab_expenses_types            # !!!!!!!
        table_name = "expense_types"                # !!!!!!!
        
        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.expenses_types_table, _ = self.build_tree(tab, table_name)
#        self.expenses_types_table.pack(fill="both", expand=True, padx=10, pady=10)

        tree = self.expenses_types_table              # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.expenses_types_crud = self.create_crud(table_name, tree, None)

        # Toolbar
        self.build_simple_toolbar(top, tree, self.expenses_types_crud)

    # ---------- Service tasks / Стандартные работы ----------
    def build_service_tasks_tab(self):
        
        tab = self.tab_service_tasks            # !!!!!!!
        table_name = "service_tasks"            # !!!!!!!
        
        # Create a top frame for buttons
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=5, pady=5)

        # Таблица
        self.service_tasks_table, _ = self.build_tree(tab, table_name)
#        self.service_tasks_table.pack(fill="both", expand=True, padx=10, pady=10)

        tree = self.service_tasks_table    # !!!!!!!

        # Регистрируем соответствие Вкладка - таблица БД
        self.tabs_config[tab] = {
            "table_name": table_name,
            "tree": tree
        }

        # Подключаем CRUD
        self.service_tasks_crud = self.create_crud(table_name, tree, None)
        crud_item = self.service_tasks_crud         # !!!!!!!

        # Toolbar
        self.build_simple_toolbar(top, tree, self.service_tasks_crud)

    # ---------- Стандартный тулбар ----------
    def build_simple_toolbar(self, parent, tree, crud_item, filter_toolbar=True):
        
        # Toolbar
        toolbar = Toolbar(parent, self)
        toolbar.pack(side="left", pady=2)
        # Buttons   
        toolbar.add_button(icon="add", command=crud_item.add, tooltip="Добавить")
        toolbar.add_button(icon="edit", command=crud_item.edit, tooltip="Редактировать")
        toolbar.add_button(icon="delete", command=crud_item.delete, tooltip="Удалить (Del)")
        toolbar.add_separator()

        if filter_toolbar: 
            crud_item.build_filter_panel(parent)

        # Bind double-click to edit
        tree.bind("<Double-1>", crud_item.edit)
        tree.bind("<Delete>", lambda e: crud_item.delete())         

        # Context menu
        self.attach_context_menu(
            tree,
            [
                ("Редактировать", crud_item.edit),
                ("Удалить", crud_item.delete)
            ]
        )

    # ---------- Import / Export ----------

    def export_treeview_to_csv(self):
        config = self.get_active_tab_config()

        if not config:
            messagebox.showwarning("Экспорт", "Нет активной таблицы.")
            return

        table_name = config["table_name"]
        tree = config["tree"]
        table_meta = TABLES[table_name]

        pretty_name = table_name.replace("_", " ").title()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"{pretty_name}.csv",   # 👈 имя по умолчанию
            filetypes=[("CSV files", "*.csv")]
        )

        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";", quoting=csv.QUOTE_ALL)

                # 🔹 экспортируемые колонки (без id)
                export_columns = [
                    col for col in table_meta["columns"]
                    if col["db"] != "id"
                ]

                # 🔹 Заголовки
                headers = [col["label"] for col in export_columns]
                writer.writerow(headers)

                # 🔹 Данные
                for item in tree.get_children():
                    row_values = tree.item(item)["values"]
                    export_row = []

                    for value, col in zip(row_values, table_meta["columns"]):

                        if col["db"] == "id":
                            continue

                        # Если FK — преобразуем display → lookup_field
                        if col.get("type") == "fk" and value:
                            fk = col["ref"]

                            # 1️⃣ найти id по display
                            result = self.db.fetchone(
                                f'SELECT "{fk["id"]}" '
                                f'FROM "{fk["table"]}" '
                                f'WHERE {fk["display"]} = ?',
                                (value,)
                            )

                            if not result:
                                export_row.append("")
                                continue

                            fk_id = result[0]

                            # 2️⃣ получить lookup_field
                            lookup = self.db.fetchone(
                                f'SELECT "{fk["lookup_field"]}" '
                                f'FROM "{fk["table"]}" '
                                f'WHERE "{fk["id"]}" = ?',
                                (fk_id,)
                            )

                            export_row.append(lookup[0] if lookup else "")

                        else:
                            export_row.append(value)

                    writer.writerow(export_row)

            messagebox.showinfo("Экспорт", "Экспорт успешно завершён.")

        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))

    def export_active_tab(self):
        config = self.get_active_tab_config()

        if not config:
            messagebox.showwarning("Экспорт", "Нет активной таблицы.")
            return


        self.export_treeview_to_csv()

    def import_csv_to_table(self, table_name):
        
        def build_fk_config(table_key):
            config = TABLES[table_key]

            fk_fields = {}

            for col in config["columns"]:
                if col.get("type") == "fk":
                    fk_fields[col["db"]] = {
                        "table": col["ref"]["table"],
                        "id_field": col["ref"]["id"],
                        "lookup_field": col["ref"]["lookup_field"]
                    }

            return fk_fields
        
        def build_mapping(table_key):
            config = TABLES[table_key]

            mapping = {}

            for col in config["columns"]:
                if col["db"] != "id" and col["db"] != "":  # id не импортируем
                    mapping[col["label"]] = col["db"]

            return mapping    

        mapping = build_mapping(table_name)
        fk_fields = build_fk_config(table_name)

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )

        if not file_path:
            return

        try:
            with open(file_path, mode="r", encoding="utf-8-sig") as file:
                reader = csv.reader(file, delimiter=";")
                headers = next(reader)

                db_columns = []
                for h in headers:
                    if h not in mapping:
                        messagebox.showerror("Ошибка", f"Неизвестная колонка: {h}")
                        return
                    db_columns.append(mapping[h])

                placeholders = ", ".join(["?"] * len(db_columns))
                quoted_columns = [f'"{c}"' for c in db_columns]

                insert_query = f"""
                    INSERT INTO "{table_name}"
                    ({', '.join(quoted_columns)})
                    VALUES ({placeholders})
                """
                print(insert_query)
                rows_to_insert = []

                for row in reader:
                    new_row = []

                    for value, db_col in zip(row, db_columns):

                        # Если это FK поле
                        if db_col in fk_fields:
                            fk = fk_fields[db_col]

                            result = self.db.fetchone(
                                f'SELECT "{fk["id_field"]}" '
                                f'FROM "{fk["table"]}" '
                                f'WHERE "{fk["lookup_field"]}" = ?',
                                (value,)
                            )

                            if not result:
                                #print("Автосоздание")
                                # автосоздание
                                self.db.execute(
                                    f'INSERT INTO {fk["table"]} ({fk["lookup_field"]}) VALUES (?)',
                                    (value,)
                                )

                                new_id = self.db.fetchone(
                                    f'SELECT id FROM {fk["table"]} '
                                    f'WHERE {fk["lookup_field"]} = ?',
                                    (value,)
                                )[0]

                                new_row.append(new_id)
                            else:
                                #print(f"Поле найдено  {result[0]}")
                                new_row.append(result[0])
                        else:
                            new_row.append(value)
                    print(f"Новая строка  {new_row[0]}")
                    rows_to_insert.append(new_row)
                print(f"Запрос {insert_query} //n {rows_to_insert[0][0]} {rows_to_insert[0][1]} {rows_to_insert[0][2]} {rows_to_insert[0][3]} {rows_to_insert[0][4]} {rows_to_insert[0][5]} ")
                self.db.executemany(insert_query, rows_to_insert)

            messagebox.showinfo("Импорт", "Импорт успешно завершён")
            self.refresh_all()

        except Exception as e:
            messagebox.showerror("Ошибка импорта", str(e))

    def import_active_tab(self):
        config = self.get_active_tab_config()

        if not config:
            messagebox.showwarning("Импорт", "Нет активной таблицы.")
            return

        table_name = config["table_name"]

        self.import_csv_to_table(table_name)

    # ---------- Utils ----------
    def refresh_all(self):
        self.cars_crud.load()
        self.load_cars_combo()
        self.load_service_history()
        self.load_service_history_filters()
        self.load_part_purchases()
        self.load_part_purchases_filters()
        #self.part_purchases_crud.load() # - Запчасти        
        self.parts_crud.load()          # - Запчасти
        self.expenses_crud.load()       # - Расходы
        self.fuel_crud.load()           # - Топливо
        self.manufacturers_crud.load()  # - Производители
        self.part_types_crud.load()
        self.car_systems_crud.load()
        self.services_crud.load()
        self.service_tasks_crud.load()  # 
        self.expenses_types_crud.load()
        self.recalc_amount()
        self.load_service_part_purchases()

    def generate_pdf_report(self):
        """Универсальный экспорт активной таблицы в PDF с учётом фильтров"""
        config = self.get_active_tab_config()

        if not config:
            messagebox.showwarning("Экспорт PDF", "Нет активной таблицы.")
            return

        table_name = config["table_name"]
        tree = config["tree"]
        table_meta = TABLES[table_name]

        # Получить данные из Treeview (учитывает фильтры)
        data = []
        headers = []
        for col in table_meta["columns"]:
            if col["db"] != "id":
                headers.append(col["label"])
        data.append(headers)

        # Позиции суммируемых столбцов в итоговой таблице (без id)
        columns_without_id = [c for c in table_meta["columns"] if c["db"] != "id"]
        sum_positions = [i for i, c in enumerate(columns_without_id) if c.get("sum")]
        sum_values = [0.0] * len(sum_positions)

        for item in tree.get_children():
            row = tree.item(item)["values"]
            # Убрать id если есть
            if table_meta["columns"][0]["db"] == "id":
                row = row[1:]
            # Форматировать даты
            formatted_row = []
            columns = columns_without_id
            for idx, (value, col) in enumerate(zip(row, columns)):
                if col.get("type") == "date" and value:
                    value = self.format_date(value)
                formatted_row.append(value)

                if idx in sum_positions and value is not None and value != "":
                    try:
                        sum_values[sum_positions.index(idx)] += float(str(value).replace(" ", ""))
                    except ValueError:
                        pass

            data.append(formatted_row)

        if sum_positions:
            total_row = ["" for _ in headers]
            if headers:
                total_row[0] = "Итого"
            for pos_idx, col_idx in enumerate(sum_positions):
                total_row[col_idx] = self.format_currency(sum_values[pos_idx])
            data.append(total_row)

        if len(data) == 1:  # Только заголовки
            messagebox.showinfo("Экспорт PDF", "Нет данных для экспорта.")
            return

        # Получить информацию о фильтрах
        car_id = self.get_selected_car_id()
        car_info = ""
        if car_id:
            car_row = self.db.fetchone("SELECT manufacturer || ' ' || name || ' - ' || plate_number FROM cars WHERE id = ?", (car_id,))
            if car_row:
                car_info = f"Автомобиль: {car_row[0]}"

        date_info = ""
        if self.filter_by_date.get():
            date_from, date_to = self.get_date_filter()
            if date_from or date_to:
                date_info = f"Период: {self.format_date(date_from) or 'начало'} - {self.format_date(date_to) or 'конец'}"

        # Создать PDF
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"{table_name}_{car_row[0]}.pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if not file_path:
            return

        styles = self.get_pdf_styles()
        elements = []

        # Добавить информацию о фильтрах
        if car_info:
            elements.append(Paragraph(car_info, styles['info']))
        if date_info:
            elements.append(Paragraph(date_info, styles['info']))

        # Создать таблицу
        table = Table(data)
        table.setStyle(self.get_table_style(len(data) - 1))

        # Выравнивание по anchor из TABLES (align справа, слева, по центру)
        alignment_map = {
            "e": "RIGHT",
            "w": "LEFT",
            "center": "CENTER"
        }

        # При использовании data заголовки и строки уже учтены, но для выравнивания мы берем col-опции
        columns_without_id = [c for c in table_meta["columns"] if c["db"] != "id"]
        for idx, col in enumerate(columns_without_id):
            anchor = col.get("anchor", "center")
            table.setStyle(TableStyle([("ALIGN", (idx, 0), (idx, -1), alignment_map.get(anchor, "CENTER"))]))

        elements.append(table)

        title = f"Отчет: {table_meta['title']}"
        self.create_pdf_report(file_path, title, elements, styles)
        messagebox.showinfo("Экспорт PDF", "PDF отчет создан успешно.")
        os.startfile(file_path)

    def valid_date(  # Метод для проверки при сохранении
            self, 
            s: str, 
            widget=None,
            title="Ошибка",
            message="Неверный формат даты. Используйте YYYY-MM-DD."
    ) -> bool:
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except:
            messagebox.showerror(title, message)
            if widget:
                widget.focus_set()
            return False

    def attach_context_menu(self, tree, actions: list):
        menu = tk.Menu(tree, tearoff=0)

        for label, callback in actions:
            if label == "---":
                menu.add_separator()
            else:
                menu.add_command(label=label, command=callback)

        def popup(event):
            row = tree.identify_row(event.y)
            if row:
                tree.selection_set(row)
                menu.tk_popup(event.x_root, event.y_root)

        tree.bind("<Button-3>", popup)

    def validate_float(self, var, entry):
        try:
            if var.get().strip() == "":
                raise ValueError
            float(var.get())
            entry.configure(style="Form.TEntry")
            return True
        except ValueError:
            entry.configure(style="Error.TEntry")
            return False

    def validate_positive_float(   # Метод для проверки при сохранении
        self,
        var: tk.StringVar,
        widget=None,
        title="Ошибка",
        message="Значение должно быть положительным числом"
    ) -> bool:
        try:
            value = float(var.get())
            if value <= 0:
                raise ValueError
            return True
        except ValueError:
            messagebox.showerror(title, message)
            if widget:
                widget.focus_set()
            return False

    def normalize(self, var, entry: ttk.Entry, precision=2): 
        try:
            val = float(var.get())
            var.set(f"{val:.{precision}f}")
            #entry.configure(style="TEntry")
        except ValueError:
            pass

    def format_currency(self, value: float) -> str:
        return f"{value:,.2f}".replace(",", " ")

    def get_currency(self, var) -> float:
        return float(var.get().replace(" ", ""))

    def recalc_mul(self, var_a, var_b, result_var):
        try:
            a = float(var_a.get())
            b = float(var_b.get())
            result_var.set(self.format_currency(a * b))
        except ValueError:
            result_var.set("0.00")

    def recalc_amount(self):
        try:
            a = self.get_currency(self.sum_expenses_var)
            b = self.get_currency(self.sum_fuel_var)
            c = self.get_currency(self.sum_service_var)
            d = self.get_currency(self.sum_parts_var)
            self.sum_all_expenses_var.set(self.format_currency(a + b + c + d))
        except ValueError:
            self.sum_all_expenses_var.set("0.00")

    def format_date(self, date_str):
        """Форматирование даты из YYYY-MM-DD в ДД.ММ.ГГГГ"""
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%d.%m.%Y")
            except ValueError:
                return date_str
        return date_str

    # ---------- Отчеты в PDF и Графики ----------

    def get_oil_change_data(self):
        """Получение данных о заменах масла с учётом глобальных фильтров по авто и датам"""
        car_id = self.get_selected_car_id()
        
        where = []
        params = []
        
        # Фильтр по автомобилю
        if self.filter_by_car.get() and car_id:
            where.append("sh.car_id = ?")
            params.append(car_id)
        
        # Фильтр по датам
        if self.filter_by_date.get():
            date_from, date_to = self.get_date_filter()
            if date_from:
                where.append("sh.service_date >= ?")
                params.append(date_from)
            if date_to:
                where.append("sh.service_date <= ?")
                params.append(date_to)
        
        # Получаем данные о ТО с заменой масла
        # Замена масла определяется по работам с abbr содержащим 'MO' или 'M/O' (Motor Oil)
        # или по названию работы содержащему 'масло'
        sql = """
            SELECT
                sh.id,
                sh.service_date,
                sh.mileage,
                s.name,
                c.manufacturer || ' ' || c.name || ' - ' || c.plate_number AS car,
                c.manufacturer,
                c.name,
                c.plate_number,
                c.year,
                c.vin
            FROM service_history sh
            LEFT JOIN services s ON s.id = sh.sto_id
            LEFT JOIN cars c ON c.id = sh.car_id
            LEFT JOIN service_history_tasks sht ON sht.service_history_id = sh.id
            LEFT JOIN service_tasks st ON st.id = sht.service_task_id
            WHERE (
                LOWER(st.abbr) LIKE '%МД%'
            )
        """
        #             WHERE (
        #        LOWER(st.name) LIKE '%масла%' 
        #        OR LOWER(st.abbr) LIKE '%мд%'
        #        OR LOWER(st.abbr) LIKE '%mo%'
        #        OR LOWER(st.name) LIKE '%oil%'
        #    )
        if where:
            sql += " AND " + " AND ".join(where)
        
        sql += """
            GROUP BY sh.id
            ORDER BY sh.service_date ASC, sh.mileage ASC
        """
        
        rows = self.db.fetchall(sql, params)
        return rows

    def get_car_summary_data(self, car_id):
        """Сбор данных для обобщённого отчёта по автомобилю"""
        if not car_id:
            return None

        data = {}

        # Данные автомобиля
        car_row = self.db.fetchone("SELECT * FROM cars WHERE id = ?", (car_id,))
        if not car_row:
            return None
        data['car'] = car_row

        # Суммы по типам расходов
        expenses = self.db.fetchall("""
            SELECT et.name, SUM(e.amount) as total
            FROM expenses e
            JOIN expense_types et ON e.expense_type_id = et.id
            WHERE e.car_id = ?
            GROUP BY et.id, et.name
            ORDER BY et.name
        """, (car_id,))
        data['expenses_by_type'] = expenses
        data['total_expenses'] = sum(row[1] for row in expenses) if expenses else 0.0

        # Расходы на сервисы по СТО
        services = self.db.fetchall("""
            SELECT s.name, SUM(sh.amount) as total
            FROM service_history sh
            JOIN services s ON sh.sto_id = s.id
            WHERE sh.car_id = ?
            GROUP BY s.id, s.name
            ORDER BY s.name
        """, (car_id,))
        data['services_by_sto'] = services
        data['total_services'] = sum(row[1] for row in services) if services else 0.0

        # Расходы на топливо
        fuel_total = self.db.fetchone("SELECT SUM(liters * price) FROM fuel WHERE car_id = ?", (car_id,))[0] or 0.0
        data['total_fuel'] = fuel_total

        # Покупки запчастей по типам
        parts = self.db.fetchall("""
            SELECT pt.name, SUM(pp.quantity * pp.price) as total
            FROM part_purchases pp
            JOIN parts p ON pp.part_id = p.id
            JOIN part_types pt ON p.type_id = pt.id
            WHERE pp.car_id = ?
            GROUP BY pt.id, pt.name
            ORDER BY pt.name
        """, (car_id,))
        data['parts_by_type'] = parts
        data['total_parts'] = sum(row[1] for row in parts) if parts else 0.0

        # Итоговая сумма
        data['grand_total'] = data['total_expenses'] + data['total_services'] + data['total_fuel'] + data['total_parts']

        # Дни владения: MIN и MAX даты из всех таблиц
        dates = []
        for table, date_col in [
            ('expenses', 'expense_date'),
            ('service_history', 'service_date'),
            ('fuel', 'fuel_date'),
            ('part_purchases', 'purchase_date')
        ]:
            min_date = self.db.fetchone(f"SELECT MIN({date_col}) FROM {table} WHERE car_id = ?", (car_id,))[0]
            max_date = self.db.fetchone(f"SELECT MAX({date_col}) FROM {table} WHERE car_id = ?", (car_id,))[0]
            if min_date:
                dates.append(min_date)
            if max_date:
                dates.append(max_date)

        if dates:
            min_date = min(dates)
            max_date = max(dates)
            days_owned = (datetime.strptime(max_date, "%Y-%m-%d") - datetime.strptime(min_date, "%Y-%m-%d")).days + 1
            data['min_date'] = self.format_date(min_date)
            data['max_date'] = self.format_date(max_date)
            data['days_owned'] = days_owned
            data['cost_per_day'] = data['grand_total'] / days_owned if days_owned > 0 else 0.0
        else:
            data['days_owned'] = 0
            data['cost_per_day'] = 0.0

        # Последний пробег
        last_mileage = self.db.fetchone("SELECT MAX(mileage) FROM service_history WHERE car_id = ?", (car_id,))[0] or 0.0
        data['last_mileage'] = last_mileage
        data['cost_per_km'] = data['grand_total'] / last_mileage if last_mileage > 0 else 0.0

        return data

    def generate_car_summary_report(self):
        """Генерация обобщённого отчёта по автомобилю"""
        car_id = self.get_selected_car_id()
        if not car_id:
            messagebox.showwarning("Отчёт", "Выберите автомобиль для отчёта.")
            return

        data = self.get_car_summary_data(car_id)
        if not data:
            messagebox.showwarning("Отчёт", "Нет данных для выбранного автомобиля.")
            return

        # Диалог сохранения файла
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf")],
            initialfile=f"Отчет_общий_{data['car'][2]}_{data['car'][3]}.pdf",
            title="Сохранить отчёт"
        )

        if not file_path:
            return

        # Получение стилей
        styles = self.get_pdf_styles()

        # Формирование элементов отчета
        elements = []

        # # Заголовок
        # elements.append(Paragraph("ОБОБЩЁННЫЙ ОТЧЁТ ПО АВТОМОБИЛЮ", styles['title']))
        # elements.append(Spacer(1, 0.5*cm))

        # Информация об автомобиле
        car_info = [
            ["Марка:", data['car'][2]],           
            ["Модель:", data['car'][1]],
            ["Год выпуска:", str(data['car'][3])],
            ["VIN:", data['car'][4] or "не указан"],
            ["Гос. номер:", data['car'][5]],
        ]
        car_table = Table(car_info, colWidths=[4*cm, 10*cm])
        car_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial-Narrow'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            # Отступы в ячейках
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(car_table)
        elements.append(Spacer(1, 0.1*cm))

        # Расходы по типам
        if data['expenses_by_type']:
            elements.append(Paragraph("Расходы по типам", styles['subtitle']))
            exp_data = [["Тип расхода", "Сумма"]] + [[row[0], f"{row[1]:.2f} руб."] for row in data['expenses_by_type']]
            exp_table = Table(exp_data, colWidths=[8*cm, 4*cm])
            exp_table.setStyle(self.get_table_style())
            elements.append(exp_table)
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"Итого расходов: {data['total_expenses']:.2f} руб.", styles['info']))

        # Расходы на сервисы
        if data['services_by_sto']:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph("Расходы на сервисы по СТО", styles['subtitle']))
            serv_data = [["СТО", "Сумма"]] + [[row[0], f"{row[1]:.2f} руб."] for row in data['services_by_sto']]
            serv_table = Table(serv_data, colWidths=[8*cm, 4*cm])
            serv_table.setStyle(self.get_table_style())
            elements.append(serv_table)
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"Итого на сервисы: {data['total_services']:.2f} руб.", styles['info']))

        # Расходы на топливо
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("Расходы на топливо", styles['subtitle']))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(f"Расходы на топливо: {data['total_fuel']:.2f} руб.", styles['info']))

        # Покупки запчастей
        if data['parts_by_type']:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph("Покупки запчастей по типам", styles['subtitle']))
            parts_data = [["Тип запчасти", "Сумма"]] + [[row[0], f"{row[1]:.2f} руб."] for row in data['parts_by_type']]
            parts_table = Table(parts_data, colWidths=[8*cm, 4*cm])
            parts_table.setStyle(self.get_table_style())
            elements.append(parts_table)
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"Итого на запчасти: {data['total_parts']:.2f} руб.", styles['info']))

        # Итоги
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("ИТОГИ", styles['subtitle']))
        totals_data = [
            ["Общая сумма затрат:", f"{data['grand_total']:.2f} руб."],
            ["Эксплуатация:", f"{data['min_date']} - {data['max_date']}"],
            ["Дни владения:", str(data['days_owned'])],
            ["Стоимость содержания в день:", f"{data['cost_per_day']:.2f} руб."],
            ["Последний пробег:", f"{data['last_mileage']:.0f} км"],
            ["Стоимость 1 км пробега:", f"{data['cost_per_km']:.2f} руб."],
        ]
        totals_table = Table(totals_data, colWidths=[6*cm, 6*cm])
        totals_table.setStyle(self.get_table_style())
        elements.append(totals_table)

        # Генерация PDF
        title = f"ОБЩИЙ ОТЧЁТ по автомобилю на {date.today().strftime('%d.%m.%Y')}"
        if self.create_pdf_report(file_path, title, elements, styles):
            messagebox.showinfo("Отчёт", f"Отчёт успешно сохранён:\n{file_path}")
            os.startfile(file_path)

    def get_mileage_history_data(self):
        """Получение данных service_history (дата, пробег) по глобальным фильтрам"""
        car_id = self.get_selected_car_id()

        where = []
        params = []

        if self.filter_by_car.get() and car_id:
            where.append("sh.car_id = ?")
            params.append(car_id)

        if self.filter_by_date.get():
            date_from, date_to = self.get_date_filter()
            if date_from:
                where.append("sh.service_date >= ?")
                params.append(date_from)
            if date_to:
                where.append("sh.service_date <= ?")
                params.append(date_to)

        sql = """
            SELECT
                sh.service_date,
                sh.mileage
            FROM service_history sh
        """

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY sh.service_date ASC, sh.mileage ASC"

        rows = self.db.fetchall(sql, params)
        return rows

    def generate_mileage_history_chart(self):
        """Показать график пробега по дате и предложить сохранить изображение"""
        if plt is None or FigureCanvasTkAgg is None:
            messagebox.showerror(
                "График пробега",
                "Требуется библиотека matplotlib. Установите её: pip install matplotlib"
            )
            return

        data = self.get_mileage_history_data()
        if not data:
            messagebox.showinfo("График пробега", "Нет данных для формирования графика.")
            return

        x = []
        y = []
        for row in data:
            date_str, mileage = row
            try:
                x.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except Exception:
                continue
            try:
                y.append(float(mileage) if mileage is not None else 0.0)
            except Exception:
                y.append(0.0)

        if not x or not y:
            messagebox.showinfo("График пробега", "Нет корректных данных для построения графика.")
            return

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
        ax.plot(x, y, marker='o', linestyle='-', color='tab:blue')
        ax.set_title('История пробега автомобиля')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Пробег, км')
        ax.grid(True)
        fig.autofmt_xdate(rotation=45)

        # Окно предпросмотра
        win = tk.Toplevel(self)
        win.title('График пробега')
        win.geometry('900x600')

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)

        tool_frame = ttk.Frame(win)
        tool_frame.pack(fill='x', pady=5)

        def save_chart():
            filepath = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG изображения', '*.png'), ('JPEG изображения', '*.jpg;*.jpeg')],
                initialfile='График_пробега.png',
                title='Сохранить график'
            )
            if not filepath:
                return
            try:
                fig.savefig(filepath, bbox_inches='tight')
                messagebox.showinfo('Сохранение графика', f'График сохранен: {filepath}')
            except Exception as e:
                messagebox.showerror('Сохранение графика', f'Ошибка при сохранении: {e}')

        ttk.Button(tool_frame, text='Сохранить как изображение', command=save_chart).pack(side='left', padx=5)

    def create_pdf_report(self, file_path, title, elements, styles):
        """Создание PDF документа с заданными элементами
        
        Args:
            file_path: Путь сохранения файла
            title: Заголовок отчета
            elements: Список элементов для добавления в документ
            styles: стили для Колонтитула и заголовка
        """
        try:
            # Создание PDF документа (портретная ориентация)
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=1*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # Колонтитул
            elements.insert(0,Paragraph(f"ПО: {APP_NAME} v.{APP_VERSION} by {APP_AUTHOR}", styles['colontitle']))

            # Заголовок
            elements.insert(1,Paragraph(title, styles['title']))            
            
            # Генерация PDF
            doc.build(elements)
            return True

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет:\n{str(e)}")
            return False

    def get_pdf_styles(self):
        """Получение стилей для PDF отчетов
        
        Returns:
            dict: Словарь со стилями ParagraphStyle
        """
        # Регистрация шрифта с поддержкой кириллицы
        fonts_dir = resource_path('fonts')
        regular_font = fonts_dir / 'arial.ttf'
        bold_font = fonts_dir / 'arialbd.ttf'
        narrow_font = fonts_dir / 'ARIALN.TTF'
        narrow_bold_font = fonts_dir / 'ARIALNB.TTF'        

        pdfmetrics.registerFont(TTFont('Arial', str(regular_font)))
        pdfmetrics.registerFont(TTFont('Arial-Bold', str(bold_font)))
        pdfmetrics.registerFont(TTFont('Arial-Narrow', str(narrow_font)))
        pdfmetrics.registerFont(TTFont('Arial-Narrow-Bold', str(narrow_bold_font)))

        styles = getSampleStyleSheet()

        # Колонтитул
        colontitle_style = ParagraphStyle(
            'ColonTitle',
            parent=styles['Normal'],
            fontName='Arial-Narrow',
            fontSize=6,
            alignment=TA_RIGHT,
            spaceAfter=5,
            leading=22
        )

        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='Arial-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=10,
            leading=22
        )

        # Подзаголовок
        subtitle_style = ParagraphStyle(
            'CustomTitle1',
            parent=styles['Heading1'],
            fontName='Arial-Narrow-Bold',
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=5,
            leading=22
        )

        # Информация
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=5,
            leading=14
        )

        # Статистика - значение
        stats_value_style = ParagraphStyle(
            'StatsValueStyle',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=10,
            alignment=TA_LEFT,
            leading=12
        )

        # Статистика - метка
        stats_label_style = ParagraphStyle(
            'StatsLabelStyle',
            parent=styles['Normal'],
            fontName='Arial',
            fontSize=10,
            alignment=TA_RIGHT,
            leading=12
        )

        return {
            'colontitle': colontitle_style,
            'title': title_style,
            'subtitle': subtitle_style,
            'info': info_style,
            'stats_value': stats_value_style,
            'stats_label': stats_label_style,
            'base': styles
        }

    def get_table_style(self, table_data_rows=1):
        """Получение стиля таблицы для PDF отчетов
        
        Args:
            table_data_rows: Количество строк данных (для расчета стилей)
            
        Returns:
            TableStyle: Стиль таблицы
        """
        table_style = TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Narrow-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

            # Чередование цветов строк
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),

            # Сетка
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

            # Отступы в ячейках
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

            # Шрифт для данных
            ('FONTNAME', (0, 1), (-1, -1), 'Arial-Narrow'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ])
        return table_style

    def generate_oil_change_report(self):
        """Генерация PDF-отчета о заменах масла"""
        data = self.get_oil_change_data()

        if not data:
            messagebox.showinfo("Отчет", "Нет данных для формирования отчета.\nПроверьте фильтры.")
            return

        # Получаем информацию об автомобиле и периоде
        car_info = data[0][3] if data else "Все автомобили"
        date_from = self.date_from.get() if self.filter_by_date.get() else "Начала"
        date_to = self.date_to.get() if self.filter_by_date.get() else "Сегодня"

        # Диалог сохранения файла
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf")],
            initialfile=f"Отчет_замена_масла_{date_to}_{data[0][7]}.pdf",
            title="Сохранить отчет"
        )

        if not file_path:
            return

        # Получение стилей
        styles = self.get_pdf_styles()

        # Формирование элементов отчета
        elements = []

        # Информация об автомобиле и периоде
        # Формируем строку с автомобилем
        if self.filter_by_car.get() and self.car_var.get():
            car_text = f"Автомобиль: {self.car_var.get()}"
            car_detail_year = f"Год выпуска: {data[0][8]}"
            car_detail_vin = f"VIN: {data[0][9]}"

            elements.append(Paragraph(car_text, styles['info']))
            elements.append(Paragraph(car_detail_year, styles['info']))
            elements.append(Paragraph(car_detail_vin, styles['info']))
        else:
            car_text = "Автомобиль: Все автомобили"
            elements.append(Paragraph(car_text, styles['info']))

        period_text = f"Период: с {self.format_date(date_from)} по {self.format_date(date_to)}"
        elements.append(Paragraph(period_text, styles['info']))
        elements.append(Spacer(1, 0.3*cm))

        # Подготовка данных для таблицы
        table_data = [["№", "Дата", "Пробег (км)", "Интервал (км)", "Сервис"]]

        prev_mileage = None
        for idx, row in enumerate(data, start=1):
            service_date = row[1]
            mileage = row[2]
            service_name = row[3]

            # Расчет интервала
            if prev_mileage is not None:
                interval = mileage - prev_mileage
            else:
                interval = 0
            prev_mileage = mileage

            table_data.append([
                str(idx),
                self.format_date(service_date),
                str(int(mileage)) if mileage else "0",
                str(int(interval)) if interval else "—",
                str(service_name) if service_name else "не указано"
            ])

        # Создание таблицы
        table = Table(table_data, colWidths=[1.5*cm, 3*cm, 3*cm, 3*cm, 4*cm])
        table.setStyle(self.get_table_style())
        elements.append(table)

        # Итоговая статистика
        if len(data) > 1:
            total_replacements = len(data)
            first_mileage = data[0][2] if data[0][2] else 0
            last_mileage = data[-1][2] if data[-1][2] else 0
            total_mileage = last_mileage - first_mileage
            avg_interval = total_mileage / (total_replacements - 1) if total_replacements > 1 else 0

            elements.append(Spacer(1, 0.5*cm))

            stats_data = [
                [Paragraph("Всего замен:", styles['stats_label']), Paragraph(str(total_replacements), styles['stats_value'])],
                [Paragraph("Пробег за период:", styles['stats_label']), Paragraph(f"{int(total_mileage)} км", styles['stats_value'])],
                [Paragraph("Средний интервал:", styles['stats_label']), Paragraph(f"{int(avg_interval)} км", styles['stats_value'])],
            ]

            stats_table = Table(stats_data, colWidths=[5*cm, 3*cm])
            stats_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(stats_table)

        # Генерация PDF
        if self.create_pdf_report(file_path, "ОТЧЕТ О ЗАМЕНАХ МАСЛА", elements, styles):
            messagebox.showinfo("Отчет", f"Отчет успешно сохранен:\n{file_path}")
        os.startfile(file_path)

# ================= RUN =================
if __name__ == "__main__":
    init_db()
    App().mainloop()