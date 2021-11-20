import os
from datetime import datetime
from time import localtime, strftime
from tkinter import *
from tkinter import ttk, filedialog

from screen_translate.Mbox import Mbox
from screen_translate.Public import _StoredGlobal, TextWithVar

dir_path = os.path.dirname(os.path.realpath(__file__))
initialDirPath = os.path.join(dir_path, '../../')

# Classes
class Log():
    """Source TL Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Log')
        self.root.geometry('600x160')
        self.root.wm_withdraw()
        self.root.attributes('-alpha', 1)
        self.currentOpacity = 1.0

        # Frames
        self.firstFrame = Frame(self.root)
        self.firstFrame.pack(side=TOP, fill=BOTH, padx=5, expand=True)

        self.bottomFrame = Frame(self.root)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=False)

        # Scrollbar
        self.scrollbarY = ttk.Scrollbar(self.firstFrame, orient=VERTICAL)
        self.scrollbarY.pack(side=RIGHT, fill=Y)
        
        # Logbox
        self.logVar = StringVar(self.root)
        self.logVar.set(f'[{strftime("%H:%M:%S", localtime())}] Ready!')
        _StoredGlobal.logVar = self.logVar

        self.tbLogger = TextWithVar(self.firstFrame, textvariable=self.logVar, height = 5, width = 100, yscrollcommand=True)
        self.tbLogger.bind("<Key>", lambda event: _StoredGlobal.allowedKey(event)) # Disable textbox input
        self.tbLogger.pack(side=LEFT, fill=BOTH, expand=True)
        self.tbLogger.config(yscrollcommand=self.scrollbarY.set)
        self.scrollbarY.config(command=self.tbLogger.yview)

        # Other stuff
        self.btnClear = ttk.Button(self.bottomFrame, text='⚠ Clear', command=self.clearLog)
        self.btnClear.pack(side=LEFT, padx=5, pady=5)

        self.btnSave = ttk.Button(self.bottomFrame, text='✉ Export Log', command=self.saveLog)
        self.btnSave.pack(side=LEFT, padx=5, pady=5)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def clearLog(self):
        # Ask for confirmation first
        if Mbox('Confirmation', 'Are you sure you want to clear the log?', 3, self.root):
            self.logVar.set('')

    def saveLog(self):
        # Get current timestamp
        dt_string = datetime.now().strftime("%d-%m-%Y %H_%M_%S")

        # use filedialog
        filename = filedialog.asksaveasfilename(initialdir=initialDirPath, initialfile=f"Log Export {dt_string}", title="Save file as", 
            defaultextension=".txt", filetypes=(
            ("Text file", "*.txt"), ("All files", "*.*"))
        )

        # Save the file
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.logVar.get())
            except Exception as e:
                Mbox('Error', 'Failed to save file: ' + str(e), 2, self.root)