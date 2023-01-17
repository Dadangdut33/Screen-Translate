from .Detached import AbstractDetachedWindow

# Classes
class QueryWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        super().__init__(master, "Translation Query", "q")
