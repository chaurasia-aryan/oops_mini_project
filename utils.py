# utils.py
# Common UI elements and constants

import tkinter as tk

BG_COLOR = "#f0f2f5"
WHITE_COLOR = "#ffffff"
PRIMARY_COLOR = "#1877f2"
SEPARATOR_COLOR = "#dadde1"
FONT_FAMILY = "Helvetica"
FONT_BOLD = "Helvetica Bold"

# -------- Placeholder Entry --------
class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder, is_password=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.is_password = is_password
        self.config(font=("Arial", 12), fg="grey", relief="solid", bd=1)
        self.insert(0, placeholder)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg="black")
            if self.is_password:
                self.config(show="*")

    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg="grey")
            if self.is_password:
                self.config(show="")

    def get_value(self):
        val = self.get()
        return "" if val == self.placeholder else val
