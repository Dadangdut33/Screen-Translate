import os
import tkinter as tk
import tkinter.ttk as ttk

from .MBox import Mbox
from screen_translate.Globals import gClass, path_logo_icon
from screen_translate.Logging import logger, current_log, dir_log
from screen_translate.utils.Helper import startFile, tb_copy_only

# Classes
class LogWindow:
    """Logger but shown in toplevel window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        gClass.lw = self  # type: ignore
        self.root = tk.Toplevel(master)
        self.root.title("Log")
        self.root.geometry("600x160")
        self.root.wm_withdraw()
        self.root.attributes("-alpha", 1)
        self.currentOpacity = 1.0

        # Frames
        self.firstFrame = ttk.Frame(self.root)
        self.firstFrame.pack(side=tk.TOP, fill=tk.BOTH, padx=5, expand=True)

        self.bottomFrame = ttk.Frame(self.root)
        self.bottomFrame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)

        # Scrollbar
        self.scrollbarY = ttk.Scrollbar(self.firstFrame, orient=tk.VERTICAL)
        self.scrollbarY.pack(side=tk.RIGHT, fill=tk.Y)

        self.tbLogger = tk.Text(self.firstFrame, height=5, width=100)
        self.tbLogger.bind("<Key>", lambda event: tb_copy_only(event))  # Disable textbox input
        self.tbLogger.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tbLogger.config(yscrollcommand=self.scrollbarY.set)
        self.scrollbarY.config(command=self.tbLogger.yview)

        # Other stuff
        self.btnClear = ttk.Button(self.bottomFrame, text="⚠ Clear", command=self.clearLog)
        self.btnClear.pack(side=tk.LEFT, padx=5, pady=5)

        self.btnRefresh = ttk.Button(self.bottomFrame, text="🔄 Refresh", command=lambda: self.updateLog)
        self.btnRefresh.pack(side=tk.LEFT, padx=5, pady=5)

        self.btnOpenDefaultLog = ttk.Button(self.bottomFrame, text="🗁 Open Log Folder", command=lambda: startFile(dir_log))
        self.btnOpenDefaultLog.pack(side=tk.LEFT, padx=5, pady=5)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()
        self.updateLog()

    def on_closing(self):
        self.root.wm_withdraw()

    def updateLog(self):
        self.tbLogger.delete(1.0, tk.END)
        try:
            content = open(current_log).read()
        except FileNotFoundError:
            logger.exception("Log file not found")
            content = "Log file not found"
        self.tbLogger.insert(tk.END, content)

    def clearLog(self):
        # Ask for confirmation first
        if Mbox("Confirmation", "Are you sure you want to clear the log?", 3, self.root):
            os.remove(current_log)
            logger.info("Log cleared")
            self.updateLog()
