import tkinter as tk

from screen_translate.components.abstract.Detached import AbstractDetachedWindow


# Classes
class QueryWindow(AbstractDetachedWindow):
    """Query Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        super().__init__(master, "Translation Query", "q")
