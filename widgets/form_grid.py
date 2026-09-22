# ================= CUSTOM WIDGETS =================
# Grid для форм

class FormGrid:
    def __init__(self, parent, cols=3):
        self.parent = parent
        self.row = 0
        self.cols = cols

    def add(self, label, widget, label_com=None):
        label.grid(row=self.row, column=0, sticky="e", padx=10, pady=5)
        widget.grid(row=self.row, column=1, sticky="w", padx=10, pady=5)
        if label_com:
            label_com.grid(row=self.row, column=2, sticky="w", padx=10, pady=5)        
        self.row += 1
    def add_12(self, label, widget):
        label.grid(row=self.row, column=0, sticky="e", padx=10, pady=5)
        widget.grid(row=self.row, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.row += 1
    def button(self, btn):
        btn.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        self.row += 1
    def two_button(self, btn1, btn2):
        btn1.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        btn2.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        self.row += 1
    def three_button(self, btn1, btn2, btn3):
        btn1.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        btn2.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        btn3.grid(row=self.row, column=0, columnspan=self.cols, padx=10, pady=5, sticky="e")
        self.row += 1