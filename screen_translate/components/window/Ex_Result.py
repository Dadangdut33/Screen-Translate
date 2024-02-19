import tkinter as tk

from screen_translate.components.abstract.Detached import AbstractDetachedWindow


# Classes
class ResultWindow(AbstractDetachedWindow):
    """Result Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        super().__init__(master, "Translation Result", "res")
