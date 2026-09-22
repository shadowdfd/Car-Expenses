# ================= CUSTOM WIDGETS =================
# Комбобокс для внешних ключей
from tkinter import ttk


class FKCombobox(ttk.Combobox):
    """Combobox с поддержкой внешних ключей"""
    def __init__(self, parent, *, fk_data, **kwargs):
        self._fk_data = fk_data
        self._id_index = {int(fid): i for i, (fid, _) in enumerate(fk_data)}
        values = [row[1] for row in fk_data]
        super().__init__(parent, values=values, **kwargs)
    
    def set_fk_data(self, data: list[tuple[Any, str]]):
        self._fk_data = data
        self['values'] = [item[1] for item in data]
    
    def get_fk_id(self):
        i = self.current()
        return self._fk_data[i][0] if i >= 0 else None
    
    def set_by_id(self, value, *, disable=False):
        if value is None:
            return
        idx = self._id_index.get(int(value))
        if idx is not None:
            self.current(idx)
            if disable:
                self.configure(state="disabled")