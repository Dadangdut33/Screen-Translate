from tkinter import *
from tkinter import ttk, colorchooser
from ..Public import globalStuff, TextWithVar

# Classes
class Detached_Tl_Query():
    """Source TL Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Translation Query')
        self.root.geometry('500x160')
        self.root.wm_withdraw()
        self.root.attributes('-alpha', 1)
        self.currentOpacity = 1.0

        # Top frame
        self.topFrame = Frame(self.root)
        self.topFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.tbFrame = Frame(self.topFrame)
        self.tbFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.settingFrame = Frame(self.topFrame)
        self.settingFrame.pack(side=TOP, fill=X, expand=False)

        self.settingFrame_2 = Frame(self.settingFrame)
        self.settingFrame_2.pack(side=TOP, fill=X, expand=False)

        # Always on top checkbox
        self.menubar = Menu(self.root)
        self.alwaysOnTopVar = BooleanVar()
        self.alwaysOnTopVar.set(True)

        # Top hidden
        self.topHiddenVar = BooleanVar()
        self.root.wm_attributes('-topmost', True)

        # Show window setting
        self.showSetting = BooleanVar()
        self.showSetting.set(False)

        # Setting frame
        # Label for opacity slider
        self.opacityLabel = Label(self.settingFrame_2, text="Opacity: " + str(self.currentOpacity))
        self.opacityLabel.pack(padx=5, pady=5, side=LEFT)

        # Opacity slider
        self.opacitySlider = ttk.Scale(self.settingFrame_2, from_=0.0, to=1.0, orient=HORIZONTAL, length=150, command=self.sliderOpac, variable=self.currentOpacity)
        self.opacitySlider.set(self.currentOpacity)
        self.opacitySlider.pack(padx=5, pady=5, side=LEFT)

        # Reset button
        self.resetButton =ttk. Button(self.settingFrame_2, text="Reset", command=self.reset)
        self.resetButton.pack(padx=5, pady=5, side=LEFT)

        # Textbox bg color
        self.textboxBgColor = StringVar()
        self.textboxBgColor.set('#FFFFFF')

        # Textbox fg color
        self.textboxFgColor = StringVar()
        self.textboxFgColor.set('#000000')

        # Textbox bg color Label
        self.textboxBgColorLabel = Label(self.settingFrame, text="Textbox BG color: " + self.textboxBgColor.get())
        self.textboxBgColorLabel.pack(padx=5, pady=5, side=LEFT)

        # Textbox bg color Chooser
        self.bgColorChooser = ttk.Button(self.settingFrame, text="...", command=self.bgColorChooser)
        self.bgColorChooser.pack(padx=5, pady=5, side=LEFT)

        # Textbox fg color Label
        self.textboxFgColorLabel = Label(self.settingFrame, text="Textbox FG color: " + self.textboxFgColor.get())
        self.textboxFgColorLabel.pack(padx=5, pady=5, side=LEFT)

        # Textbox fg color Chooser
        self.fgColorChooser = ttk.Button(self.settingFrame, text="...", command=self.fgColorChooser)
        self.fgColorChooser.pack(padx=5, pady=5, side=LEFT)

        # Menu bar
        # Same method as in the capture window
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.tbFrame, text="Stay on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.filemenu.add_checkbutton(label="Hide Top", onvalue=True, offvalue=False, variable=self.topHiddenVar, command=self.show_top)
        self.filemenu.add_checkbutton(label="Show Window Settings", onvalue=True, offvalue=False, variable=self.showSetting, command=self.toggle_Setting)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # Textbox in topframe2
        self.textBoxTlQuery = TextWithVar(self.tbFrame, textvariable=globalStuff.text_Box_Bottom_Var, height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True, background=self.textboxBgColor.get())
        self.textBoxTlQuery.bind("<Key>", lambda event: globalStuff.allowedKey(event)) # Disable textbox input        
        self.textBoxTlQuery.pack(side=LEFT, fill=BOTH, expand=True)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.settingFrame.pack_forget()
        self.showSetting.set(False)

    # show/hide top
    def show_top(self):
        if self.topHiddenVar.get(): # IF ON THEN TURN IT OFF
            self.root.overrideredirect(False)
            self.topHiddenVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.overrideredirect(True)
            self.topHiddenVar.set(True)

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
        self.root.attributes('-alpha', 1)
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x, from_=None):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))

        if from_ is not None:
            self.opacitySlider.set(x)

    # hide / show setting
    def toggle_Setting(self):
        if self.showSetting.get():
            self.settingFrame.pack_forget()
            self.showSetting.set(False)
        else:
            self.settingFrame.pack(side=TOP, fill=X, expand=False)
            self.showSetting.set(True)

    # Reset
    def reset(self):
        self.root.attributes('-alpha', 1)
        self.sliderOpac(1, "outside")
        self.textboxBgColor.set('#FFFFFF')
        self.textboxFgColor.set('#000000')
        self.textboxBgColorLabel.config(text="Textbox BG color: " + self.textboxBgColor.get())
        self.textboxFgColorLabel.config(text="Textbox FG color: " + self.textboxFgColor.get())
        self.textBoxTlQuery.config(background=self.textboxBgColor.get())
        self.textBoxTlQuery.config(foreground=self.textboxFgColor.get())

    # Bg Color chooser
    def bgColorChooser(self):
        colorGet = colorchooser.askcolor(color=self.textboxBgColor.get(), title="Choose a color")
        if colorGet[1] != None:
            self.textboxBgColor.set(colorGet[1])
            self.textboxBgColorLabel.config(text="Textbox BG color: " + self.textboxBgColor.get())
            self.textBoxTlQuery.config(background=self.textboxBgColor.get())
    
    # Fg Color chooser
    def fgColorChooser(self):
        colorGet = colorchooser.askcolor(color=self.textboxFgColor.get(), title="Choose a color")
        if colorGet[1] != None:
            self.textboxFgColor.set(colorGet[1])
            self.textboxFgColorLabel.config(text="Textbox FG color: " + self.textboxFgColor.get())
            self.textBoxTlQuery.config(foreground=self.textboxFgColor.get())