from tkinter import *
from ..Public import globalStuff, TextWithVar

# Classes
class Detached_Tl_Query():
    """Source TL Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Translation Query')
        self.root.geometry('500x150')
        self.root.wm_withdraw()
        self.root.attributes('-alpha', 1)

        # Top frame
        self.topFrame = Frame(self.root)
        self.topFrame.pack(side=TOP, fill=BOTH, expand=True)

        # self.topFrame2 = Frame(self.root)
        # self.topFrame2.pack(side=TOP, fill=X, expand=False)

        # Always on top checkbox
        self.menubar = Menu(self.root)
        self.alwaysOnTopVar = BooleanVar()
        self.topHidden = BooleanVar()
        self.alwaysOnTopVar.set(True)
        self.root.wm_attributes('-topmost', True)

        # Same method as in the capture window
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.topFrame, text="Stay on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.topHiddenCheck = Checkbutton(self.topFrame, text="Hide Top", variable=self.topHidden, command=self.show_top)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.filemenu.add_checkbutton(label="Hide Top", onvalue=True, offvalue=False, variable=self.topHidden, command=self.show_top)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        self.textBoxTlResult = TextWithVar(self.topFrame, textvariable=globalStuff.text_Box_Top_Var, height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True)
        self.textBoxTlResult.bind("<Key>", lambda event: globalStuff.allowedKey(event)) # Disable textbox input        
        self.textBoxTlResult.pack(side=LEFT, fill=BOTH, expand=True)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # show/hide top
    def show_top(self):
        if self.topHidden.get(): # IF ON THEN TURN IT OFF
            self.root.overrideredirect(False)
            self.topHidden.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.overrideredirect(True)
            self.topHidden.set(True)

    # Stay on top
    def always_on_top(self):
        if self.alwaysOnTopVar.get(): # IF ON THEN TURN IT OFF
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTopVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTopVar.set(True)

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()