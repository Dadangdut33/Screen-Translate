from .Detached import AbstractDetachedWindow

# Classes
class ResultWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        super().__init__(master, "Translation Result", "res")
