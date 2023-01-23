import tkinter as tk
from .Detached import AbstractDetachedWindow

# Classes
class ResultWindow(AbstractDetachedWindow):
    """Result Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        super().__init__(master, "Translation Result", "res")
