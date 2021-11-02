import tkinter.ttk as ttk
from tkinter import *
from screen_translate.Public import CreateToolTip, fJson, _StoredGlobal, searchList

# Classes
class CaptureUI_Setting():
    """Capture Window Settings"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Capture Area Settings')
        self.root.geometry('400x150')
        self.root.wm_withdraw()

        # ----------------------------------------------------------------------
        # Frame-1
        self.Frame_1 = Frame(self.root)
        self.Frame_1.pack(side=TOP, fill=X, expand=False)

        # Frame-2
        self.Frame_2 = Frame(self.root)
        self.Frame_2.pack(side=TOP, fill=X, expand=False)

        # Frame-3
        self.Frame_3 = Frame(self.root)
        self.Frame_3.pack(side=TOP, fill=X, expand=False)

        # ----------------------------------------------------------------------
        # Always on top checkbox
        self.menubar = Menu(self.root)
        self.alwaysOnTopVar = BooleanVar()
        self.alwaysOnTopVar.set(True)
        self.topHiddenVar = BooleanVar()
        self.root.wm_attributes('-topmost', True)

        # Menu bar
        # Same method as in the capture window
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.Frame_1, text="Stay on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.topHiddenCheck = Checkbutton(self.Frame_1, text="Hide Top", variable=self.topHiddenVar, command=self.show_top)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.filemenu.add_checkbutton(label="Hide Top", onvalue=True, offvalue=False, variable=self.topHiddenVar, command=self.show_top)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # ----------------------------------------------------------------------
        # Label for opacity slider
        self.opacityLabel = Label(self.Frame_1, text="Capture UI Opacity: " + str(_StoredGlobal.curCapOpacity))
        self.opacityLabel.pack(padx=5, pady=5, side=LEFT)
        _StoredGlobal.captureOpacityLabel_CapSetting = self.opacityLabel

        # ----------------------------------------------------------------------
        # opacity slider
        self.opacitySlider = ttk.Scale(self.Frame_1, from_=0.0, to=1.0, value=_StoredGlobal.curCapOpacity, orient=HORIZONTAL, command=self.opacChange)
        self.opacitySlider.pack(padx=5, pady=5, side=LEFT)
        _StoredGlobal.captureSlider_Cap = self.opacitySlider

        # ----------------------------------------------------------------------
        # Button
        self.captureBtn = ttk.Button(self.Frame_1, text="Capture And Translate", command=_StoredGlobal.main.capture_UI.getTextAndTranslate)
        self.captureBtn.pack(padx=5, pady=5, side=LEFT)

        # Read settings
        settings = fJson.readSetting()

        # ----------------------------------------------------------------------
        # Checkbutton for capture grayscale
        self.captureGrayscaleVar = BooleanVar(self.root)
        try:
            self.captureGrayscaleVar.set(settings["enhance_Capture"]['grayscale'])
        except Exception:
            self.captureGrayscaleVar.set(False)
            print("Error: Faild to load grayscale setting! Please do not modify settings manually") 
        
        self.captureGrayscaleCheck = ttk.Checkbutton(self.Frame_2, text="Grayscale Capture", variable=self.captureGrayscaleVar, command=self.captureGrayscale)
        self.captureGrayscaleCheck.pack(padx=5, pady=5, side=LEFT)
        CreateToolTip(self.captureGrayscaleCheck, "Enhance the OCR by making the captured picture grayscale on the character reading part.grayscale")

        # ----------------------------------------------------------------------
        # Checkbutton for enhance capture or not
        self.detectContourVar = BooleanVar(self.root)
        try:
            self.detectContourVar.set(settings["enhance_Capture"]['cv2_Contour'])
        except Exception:
            self.detectContourVar.set(False)
            print("Error: Faild to load enhance setting! Please do not modify settings manually")

        self.detectContourCheck = ttk.Checkbutton(self.Frame_2, text="Detect Contour Using CV2 ", variable=self.detectContourVar, command=self.disableEnableCb)
        self.detectContourCheck.pack(padx=5, pady=5, side=LEFT)
        CreateToolTip(self.detectContourCheck, "Enhance OCR by detecting the contour of the image")

        # ----------------------------------------------------------------------
        # Background type label
        self.bgTypeLabel = Label(self.Frame_3, text="Bg Type: ")
        self.bgTypeLabel.pack(padx=5, pady=5, side=LEFT)
        CreateToolTip(self.bgTypeLabel, "The background type of the target")

        # ----------------------------------------------------------------------
        # Background type combobox
        self.CBBgType = ttk.Combobox(self.Frame_3, values=["Auto-Detect", "Light", "Dark"], state="readonly")
        self.CBBgType.pack(padx=0, pady=5, side=LEFT)
        self.CBBgType.bind("<<ComboboxSelected>>", lambda e: _StoredGlobal.main.capture_UI.changeCbBg(self.CBBgType.get()))
        CreateToolTip(self.CBBgType, "The background type of the target")

        index = searchList(settings['enhance_Capture']['background'], ["Auto-Detect", "Light", "Dark"])
        self.CBBgType.current(index)

        # ----------------------------------------------------------------------
        # Checkbutton for debug mode
        self.debugModeVar = BooleanVar(self.root)
        try:
            self.debugModeVar.set(settings["enhance_Capture"]["debugmode"])
        except Exception:
            self.debugModeVar.set(False)
            print("Error: Failed to load debug mode setting! Please do not modify settings manually")

        self.debugModeCheck = ttk.Checkbutton(self.Frame_3, text="Debug Mode", variable=self.debugModeVar) # , command=self.debugMode
        self.debugModeCheck.pack(padx=5, pady=5, side=LEFT)
        CreateToolTip(self.debugModeCheck, text="Enable debug mode.")

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # show/hide top
    def show_top(self):
        if self.topHiddenVar.get(): # IF ON THEN TURN IT OFF
            self.root.overrideredirect(False)
            self.topHiddenVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.overrideredirect(True)
            self.topHiddenVar.set(True)

    # Slider
    def opacChange(self, val):
        _StoredGlobal.main.capture_UI.sliderOpac(val, fromOutside=True)

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Menubar
    def always_on_top(self):
        if self.alwaysOnTopVar.get(): # IF ON THEN TURN IT OFF
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTopVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTopVar.set(True)

    # ChangeCb
    def changeCbBg(self, value):
        self.CBBgType.current(searchList(value, ["Auto-Detect", 'Light', 'Dark']))

    # Disable enable cb
    def disableEnableCb(self, outside=False):
        if self.detectContourVar.get(): # If disabled enable it
            self.CBBgType.config(state="readonly")
        else:
            self.CBBgType.config(state="disabled") # If enable disable it
    
        if not outside: self.detectContour() # If checked from the ui itself

    # Disable enable debugmode checkbox
    def disableEnableDebugMode(self):
        if not self.detectContourVar.get() and not self.captureGrayscaleVar.get(): # If both are not checked then disable the debugmode checkbox
            self.debugModeCheck.config(state="disabled")
        else:
            self.debugModeCheck.config(state="normal")

    # Contour checkbox
    def detectContour(self):
        _StoredGlobal.main.capture_UI.detectContourVar.set(self.detectContourVar.get())
        _StoredGlobal.main.capture_UI.disableEnableCb(outside=True)
        self.disableEnableDebugMode()
        _StoredGlobal.main.capture_UI.disableEnableDebugMode()

    # Grayscale checkbox
    def captureGrayscale(self):
        _StoredGlobal.main.capture_UI.captureGrayscaleVar.set(self.captureGrayscaleVar.get())
        _StoredGlobal.main.capture_UI.disableEnableDebugMode()
        self.disableEnableDebugMode()
        _StoredGlobal.main.capture_UI.disableEnableDebugMode()

    # debugmode checkbox
    def debugMode(self):
        _StoredGlobal.main.capture_UI.debugModeVar.set(self.debugModeVar.get())