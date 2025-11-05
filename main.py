
from db_simple import create_tables
from ui import FacebookLogin
import tkinter as tk

if __name__ == "__main__":
    create_tables()  # ensure DB ready
    root = tk.Tk()
    FacebookLogin(root)
    root.mainloop()
