"""
Визуальные стили оформления
"""
# styles.py
from tkinter import ttk

def setup_styles(theme="clam"):
    style = ttk.Style()
    #style.theme_use(theme)

    #style.theme_use("xpnative")
    
    # == Стиль полей с ошибкой
    style.configure("Error.TEntry", 
                    foreground="black",
                    padding=6,
                    font=("Segoe UI", 10))
    style.map(
        "Error.TEntry",
        fieldbackground=[("!disabled", "#ffdddd")]

    )        
    # == Стиль вкладок
    style.configure("TNotebook.Tab", 
                    font=("Segoe UI", 11),
                    padding=(5, 1) # (x, y)
                )
    style.map(
        "TNotebook.Tab",
            background=[
            ("selected", "#100163"),
            ("!selected", "#f0f0f0")    # Cтандартный цвет "#f0f0f0"
        ],
            foreground=[
            ("selected", "#000000"),
            ("!selected", "#1F1F1F")
        ]
    )
    # == Стиль заголовков таблиц
    style.configure(
        "Treeview.Heading",
        background="#e6e6e6",
        foreground="black",
        font=("Segoe UI", 10, "bold"),
        padding=6,
    )

    # ======= Стили виджетов форм
    style.configure(
        "Form.TEntry",
        padding=6,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Form.TCombobox",
        padding=6,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Form.TLabel",
        font=("Segoe UI", 10),
        foreground="#444"
    )
    style.configure(
        "Form_Com.TLabel",
        font=("Segoe UI", 8), 
        foreground="#706F6F"
    )
    style.configure(
        "Form_Com.TButton",
        font=("Segoe UI", 10), 
        foreground="#444"
    )    

    return style