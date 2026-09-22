"""
SimpleCrud — metadata-driven UI + SQL builder 4.2+
"""
# SimpleCrud — UI + DB controller

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry                #need to install
from datetime import date
import re

from widgets.fk_combobox import FKCombobox
from widgets.form_grid import FormGrid

# ================= Simple CRUD Class =================
class SimpleCrud:
    def __init__(self, app, connection, carcombo, table, fields, tree, title,
                 on_total_changed=None, total_tree=None):
        """
        app    — ссылка на App,
        table  — имя таблицы,
        carcombo - Combobox с выбранным авто,
        fields — список полей БД (без id),
        tree   — Treeview,
        title  — человекочитаемое имя,
        connection — sqlite connection,
        filter - True - включен, "range" - для даты.
        total_tree — Treeview для закреплённой строки итогов (опционально)
        """
        self.conn = connection
        self.carcombo = carcombo
        self.app = app # ссылка на главное приложение
        self.table = table  # имя таблицы
        self.fields = fields # список полей БД
        """
                "name": "car_id",   - имя колонки в БД
                "label": "Автомобиль", - имя в UI
                "type": "fk", - тип (fk,float,calc)
                "annotation": None, - пояснение в форме
                "width": 35, - ширина поля
                "query": "SELECT id, manufacturer || ' ' || name || ' - ' || plate_number FROM cars ORDER BY manufacturer, name", - Запрос, только для fk
                "required": True, - обязательность
                "ref_table": "cars", - Имя таблицы, для фильтров если тип = fk
                "ref_id": "id", - имя столбца id, для фильтров если тип = fk
                "ref_label": "manufacturer || ' ' || name || ' - ' || plate_number"  - Поля, формат для UI, для фильтров если тип = fk
                "filter": True,
        """
        self.tree = tree # Treeview
        self.total_tree = total_tree  # Treeview для итогов
        self.title = title # человекочитаемое имя таблицы
        self.filter_widgets = {} #виджеты с фильтрами
        self.sort_column = None
        self.sort_reverse = False # текущая сортировка

        # 🆕 итоговое значение
        self._total = 0    # 🔒 приватное поле

        # 🆕 callback для App
        self.on_total_changed = on_total_changed

        self.version="CRUD 4.2+"

    def load(self):  # Загрузка данных в Treeview
        self.tree.delete(*self.tree.get_children())

        for col in self.tree["columns"]:
            self.tree.heading(
                col,
                command=lambda c=col: self._sort_by(c)
            )
            arrow = " ▲" if not self.sort_reverse else " ▼"
            if self.sort_column == col:
                self.tree.heading(col, text=col + arrow)
            else:
                self.tree.heading(col, text=col) 

        select_sql, join_sql = self._build_select()

        sql = f"""
            SELECT {select_sql}
            FROM {self.table} t
            {join_sql}
        """

        where = []
        params = []

        # ==========================
        # Глобальный фильтр по авто
        # ==========================

        if any(f["name"] == "car_id" for f in self.fields):
            selected_car = self.carcombo.get()
            if selected_car and self.app.filter_by_car.get():
                car_id = self.app.get_selected_car_id()
                where.append("t.car_id=?")
                params.append(car_id)

        # ==========================
        # 📅 Глобальный фильтр по дате
        # ==========================
        if any(f["type"] == "date" for f in self.fields):
            if self.app.filter_by_date.get():

                date_field = next(
                    f["name"] for f in self.fields
                    if f["type"] == "date"
                )

                date_from = self.app.date_from.get()
                date_to = self.app.date_to.get()

                where.append(f"{date_field} BETWEEN ? AND ?")
                params.extend([date_from, date_to])

        for field in self.fields:
            name = field["name"]

            if name not in self.filter_widgets:
                continue

            widget = self.filter_widgets[name]
            
            if field["type"] == "fk":
                idx = widget.current()
                if idx > 0:
                    val = widget._fk_data[idx][0]
                    where.append(f"{name}=?")
                    params.append(val)

            else:
                val = widget.get().strip()
                if val:
                    where.append(f"t.{name} LIKE ?")
                    params.append(f"%{val}%")

        if where:
            sql += " WHERE " + " AND ".join(where)

        order_sql = ""
        #print(self.sort_column) 
        if self.sort_column:
            direction = "DESC" if self.sort_reverse else "ASC"

            # Найдём описание поля
            field = next(
                (f for f in self.fields if f["label"] == self.sort_column),
                None
            )

            if field:
                #print(field["type"])
                if field["type"] == "fk":
                    alias = f"{field['name']}_ref"

                    label_expr = field["ref_label"]
                    label_expr = self._alias_expression(label_expr, alias)

                    order_sql = f" ORDER BY {label_expr} {direction}"

                    #order_sql = f" ORDER BY {alias}.{field['ref_label']} {direction}"

                elif field["type"] != "calc":
                    order_sql = f" ORDER BY t.{field['name']} {direction}"

        else:
            # дефолтная сортировка
            order_sql = f" ORDER BY {self.select_parts[1]} DESC"

        sql += order_sql

        #print(sql)

        rows = self.conn.fetchall(sql, params)

        for row in rows:
            self.tree.insert("", "end", values=row)

        # Зебра на строки
        self.stripe_rows(self.tree)

        # Обновляем закреплённую строку итогов
        totals = self._calculate_totals(
            "WHERE " + " AND ".join(where) if where else "",
            params
        )

        if totals:
            if totals:
                value = list(totals.values())[0]
                self.total = value
            else:
                self.total = 0

            values = [""]  # id пустой

            for field in self.fields:
                if field.get("sum"):
                    val = totals.get(field["name"], 0) or 0
                    values.append(f"{val:,.2f}".replace(",", " "))
                else:
                    values.append("")

            # Если есть отдельная таблица для итогов — используем её
            if self.total_tree:
                self.total_tree.delete(*self.total_tree.get_children())
                self.total_tree.insert("", "end", values=values, tags=("total",))
            else:
                # Иначе добавляем в основную таблицу (старое поведение)
                self.tree.insert("", "end", values=values, tags=("total",))
  
    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        """Установка итогового значения"""

        if value is None:
            value = 0

        # если не изменилось — ничего не делаем
        if value == self._total:
            return

        self._total = value

        # уведомляем App
        if self.on_total_changed:
            self.on_total_changed(self._total)

    def _sum_fields(self):
        return [
            f for f in self.fields
            if f.get("sum")
        ]

    def _calculate_totals(self, where_sql="", params=None):
        params = params or []

        sum_fields = self._sum_fields()
        if not sum_fields:
            return None

        sum_parts = []

        for f in sum_fields:

            if f["type"] == "calc":
                expr = f["calc_arg"]

                # добавляем alias t.
                expr = self._alias_expression(expr, "t")

                sum_parts.append(f"SUM({expr}) AS {f['name']}")

            else:
                sum_parts.append(f"SUM(t.{f['name']}) AS {f['name']}")

        sql = f"""
            SELECT {', '.join(sum_parts)}
            FROM {self.table} t
            {where_sql}
        """

        row = self.conn.execute(sql, params).fetchone()

        return dict(zip([f["name"] for f in sum_fields], row))

    def _sort_by(self, col): # Метод сортировки
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
        self.load()

    def _build_select(self):
        self.select_parts = ["t.id"]
        joins = []

        for field in self.fields:

            if field["type"] == "fk":
                alias = f"{field['name']}_ref"

                label_expr = field["ref_label"]

                if any(op in label_expr for op in ("||", " ", "+", "-", "*", "/")):
                    label_expr = self._alias_expression(label_expr, alias)
                else:
                    label_expr = f"{alias}.{label_expr}"

                self.select_parts.append(
                    f"{label_expr} AS {field['name']}"
                )

                joins.append(
                    f"LEFT JOIN {field['ref_table']} {alias} "
                    f"ON t.{field['name']} = {alias}.{field['ref_id']}"
                )
            elif field["type"] == "calc":
                """
                ROUND(pp.quantity * pp.price, 2) AS total,  calc_arg calc_precision
                """
                alias = "t"
                calc_expr = field["calc_arg"]
                
                if any(op in calc_expr for op in ("||", " ", "+", "-", "*", "/")):
                    calc_expr = self._alias_expression(calc_expr, alias)
                else:
                    calc_expr = f"{alias}.{calc_expr}"

                self.select_parts.append(f"ROUND({calc_expr}, {field["calc_precision"]}) AS {field["name"]}")

            else: #field["type"] != "calc":
                self.select_parts.append(f"t.{field['name']}")

        select_sql = ", ".join(self.select_parts)
        join_sql = " ".join(joins)

        return select_sql, join_sql

    def _alias_expression(self, expression, alias):
        """
        Добавляет alias перед всеми идентификаторами в выражении
        manufacturer || ' ' || name
        → alias.manufacturer || ' ' || alias.name
        """
        tokens = re.split(r"(\W)", expression)

        result = []
        for token in tokens:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                result.append(f"{alias}.{token}")
            else:
                result.append(token)

        return "".join(result)

    def build_filter_panel(self, parent):

        # Проверим — есть ли вообще фильтруемые поля
        if not any(field.get("filter") for field in self.fields):
            return

        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=5)
                # Иконка фильтров 
        self.app.image_label(frame, icon="filter", ttext=":", im_padx=10)

        for field in self.fields:
            if not field.get("filter"):
                continue

            lbl = ttk.Label(frame, text=field["label"])
            lbl.pack(side="left", padx=(5, 5))

            if field["type"] == "fk":
                data = self.conn.fetchall(field["query"])
                cb = FKCombobox(
                    frame,
                    fk_data=[(0, "Все")] + data,
                    state="readonly",
                    width=18
                )
                cb.set("Все")
                cb.pack(side="left", padx=2)
                cb.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_all())
                self.filter_widgets[field["name"]] = cb
            else:
                entry = ttk.Entry(frame, width=15)
                entry.pack(side="left", padx=2)
                entry.bind("<KeyRelease>", lambda e: self.app.refresh_all())
                self.filter_widgets[field["name"]] = entry
                
        ttk.Button(frame, image=self.app.icons["clear"], text="Сброс фильтров", command=self.reset_filters).pack(side="left", padx=(5, 5))

    def reset_filters(self):
        for field_name, widget in self.filter_widgets.items():

            # ==========================
            # FKCombobox
            # ==========================
            if isinstance(widget, FKCombobox):
                # если первый элемент = "Все"
                widget.current(0)
                continue

            # ==========================
            # ttk.Combobox
            # ==========================
            if isinstance(widget, ttk.Combobox):
                widget.set("")
                continue


            # ==========================
            # Entry
            # ==========================
            if isinstance(widget, ttk.Entry):
                widget.delete(0, "end")
                continue

        self.load()

    def _create_widget(self, parent, field, value=None, width=23): # Создание виджета для поля (Entry / Combobox)
        ftype = field["type"]

        if ftype == "fk":
            data = self.conn.execute(field["query"]).fetchall()
            cb = FKCombobox(
                parent,
                fk_data=data,                   
                #values=[r[1] for r in data],
                state="readonly",
                style="Form.TCombobox",
                width=width
            )
            if value is None and field["name"] == "car_id":
                value = self.carcombo.get()
            
            if value is not None:
                fid = next(
                    (mid for mid, name in data if name == value),
                    None
                )
                cb.set_by_id(fid)
            return cb
            
        elif ftype == "calc":
            var = tk.StringVar(value="0.00")
            entry = ttk.Entry(parent, textvariable=var, state="readonly", justify="right", style="Form.TEntry", width=width)
            entry.var = var # type: ignore
            return entry

        elif ftype == "date":
            entry = DateEntry(
                parent,
                date_pattern="yyyy-mm-dd",
                width=width,
                style="Form.TCombobox"
            )
            if value is not None:
                entry.set_date(value)                
            else:    
                entry.set_date(date.today())
            return entry

        elif ftype == "float":
            if not value and (field["name"] == "quantity" or field["name"] == "liters"): value = "1.0"
            var = tk.StringVar(value=value)
            entry = ttk.Entry(parent, textvariable=var, justify="right", style="Form.TEntry", width=width)
            entry.var = var # type: ignore
            return entry       
        
        else:
            # обычное текстовое поле
            var_2 = tk.StringVar(parent)

            # prefill при редактировании
            if value is not None:
                var_2.set(value)

            #messagebox.showinfo('Record_Id', var_2.get())

            # UX-мелочи ТОЛЬКО для abbr
            if field["name"] == "abbr":
                vcmd = (parent.register(self._limit_length(5)), "%P")

                entry = ttk.Entry(
                    parent,
                    textvariable=var_2,
                    validate="key",
                    validatecommand=vcmd,
                    style="Form.TEntry",
                    width=width
                )

                # авто UPPERCASE
                def to_upper(*_):
                    v = var_2.get()
                    if v != v.upper():
                        var_2.set(v.upper())

                var_2.trace_add("write", to_upper)

                return entry

            # обычный Entry без наворотов
            entry = ttk.Entry(parent, textvariable=var_2, style="Form.TEntry", width=width)
            entry.var = var_2 # type: ignore

            return entry

    def add(self): # Добавление записи
        
        self.wintitle = " - Добавление записи"
        self._open_form()

    def edit(self, event=None): # Редактирование записи
        item = self.tree.focus()
        if not item:
            return

        values = self.tree.item(item)["values"]
        self.wintitle = " - Редактирование записи"
        self._open_form(record_id=values[0], values=values[1:])

    def _open_form(self, record_id=None, values=None): # Открытие формы для добавления/редактирования записи
        
        #messagebox.showinfo('Record_Id', str(values[0]), )
        win = tk.Toplevel(self.app)
        win.transient(self.app)
        self.app.center_window(self.app,win)
        win.resizable(False, False)
        win.title(self.title+self.wintitle)

        widgets = {}

        form = FormGrid(win, 3)  # parent, количество колонок

        for i, field in enumerate(self.fields):
            lbl = ttk.Label(win, text=field["label"], style="Form.TLabel")
            
            value = values[i] if values else None
            if "width" in field:
                width = int(field["width"])
            else:
                width = 23
            #messagebox.showinfo('Record_Id', value)
            w = self._create_widget(win, field, value, width)
            if "annotation" in field and  field["annotation"] is not None:
                annot_lbl = ttk.Label(win, text=field["annotation"], style="Form_Com.TLabel")
                form.add(lbl, w, annot_lbl)
            else:
                form.add_12(lbl, w)
         
            widgets[field["name"]] = w

        def format_currency(value: float) -> str:
            return f"{value:,.2f}".replace(",", " ")  

        def recalc_total(*args):
            try:
                if "quantity" in widgets:
                    a = float(widgets.get("quantity", tk.StringVar()).get())
                elif "liters" in widgets:
                    a = float(widgets.get("liters", tk.StringVar()).get())
                else:
                    a = 0                   
                b = float(widgets.get("price", tk.StringVar()).get())
                widgets["total"].var.set(format_currency(a * b))
            except ValueError:
                widgets["total"].var.set("0.00")

        if ("quantity" in widgets or "liters" in widgets) and "price" in widgets:
            recalc_total()

        if "quantity" in widgets:
            widgets["quantity"].var.trace_add("write", recalc_total)
            widgets["quantity"].bind("<FocusOut>", lambda e: self.normalize(widgets["quantity"].var, widgets["quantity"], 1))
        if "liters" in widgets:
            widgets["liters"].var.trace_add("write", recalc_total)
            widgets["liters"].bind("<FocusOut>", lambda e: self.normalize(widgets["liters"].var, widgets["liters"], 1))
        if "price" in widgets:
            widgets["price"].var.trace_add("write", recalc_total)
            widgets["price"].bind("<FocusOut>", lambda e: self.normalize(widgets["price"].var, widgets["price"], 2))

        def save():
            names = []
            data = []

            for field in self.fields:
                widget = widgets[field["name"]]

                if field["type"] == "fk":
                    name = field["name"]
                    idx = widget.current()
                    if idx == -1:
                        val = None
                    else:
                        val = widget._fk_data[idx][0]
                elif field["type"] == "calc":
                    continue
                else:
                    name = field["name"]
                    val = widget.get().strip()

                if field.get("required") and not val:
                    messagebox.showerror(
                        "Ошибка",
                        f"Поле '{field['label']}' обязательно"
                    )
                    return
                names.append(name)
                data.append(val)

            if record_id is None:
                cols = ", ".join(name for name in names)
                ph = ", ".join("?" for _ in data)
                self.conn.execute(
                    f"INSERT INTO {self.table} ({cols}) VALUES ({ph})",
                    data
                )
            else:
                upd = ", ".join(f"{name}=?" for name in names)
                self.conn.execute(
                    f"UPDATE {self.table} SET {upd} WHERE id=?",
                    data + [record_id]
                )
            self.app.refresh_all()
            win.destroy()

        btn_frame = ttk.Frame(win)
        save_btn = ttk.Button(btn_frame, text="Сохранить", command=save, style="Form_Com.TButton")
        close_btn = ttk.Button(btn_frame, text="Отмена", command=win.destroy, style="Form_Com.TButton")
        save_btn.pack(side="right")
        close_btn.pack(side="right")
        form.button(btn_frame)

        mark_lbl = ttk.Label(win, text=self.version, font=("Segoe UI", 7), foreground="#636363")
        mark_lbl.grid(row=len(self.fields)+1, column=2, padx=5, pady=5, sticky="e")

    def delete(self): # Удаление записи
        item = self.tree.focus()
        if not item:
            return

        record_id = self.tree.item(item)["values"][0]
        record_name = self.tree.item(item)["values"][1]

        if not messagebox.askyesno(
            "Подтверждение",
            f"Удалить '{record_name}' из таблицы '{self.title}'?"
        ):
            return

        self.conn.execute(
                f"DELETE FROM {self.table} WHERE id=?",
                (record_id,)
        )

        self.app.refresh_all()

    def _limit_length(self, max_len): 
        def validate(value):
            return len(value) <= max_len
        return validate
    
    def stripe_rows(self, tree):
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

    def normalize(self, var, entry: ttk.Entry, precision=2): 
        try:
            val = float(var.get())
            var.set(f"{val:.{precision}f}")
            #entry.configure(style="TEntry")
        except ValueError:
            pass
    
