import tkinter.ttk as ttk
from tkinter import *
from screen_translate.Public import CreateToolTip, fJson, getTheOffset, _StoredGlobal, searchList
from screen_translate.Mbox import Mbox
from screen_translate.Capture import captureImg
import pyperclip
import os

# Classes
class CaptureUI():
    """Capture Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Text Capture Area')
        self.root.geometry('600x150')
        self.root.wm_withdraw()

        _StoredGlobal.curCapOpacity = 0.8
        self.root.attributes('-alpha', 0.8)

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

        # What happen here is that we created a hidden checkbutton to control the variable because for some reason it JUST DOES NOT WORK properly i dont know why
        # If someone found a better solution to this problem, please let me know or just create a pull request.
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
        self.opacityLabel = Label(self.Frame_1, text="Opacity: " + str(_StoredGlobal.curCapOpacity))
        self.opacityLabel.pack(padx=5, pady=5, side=LEFT)

        # ----------------------------------------------------------------------
        # opacity slider
        self.opacitySlider = ttk.Scale(self.Frame_1, from_=0.0, to=1.0, value=_StoredGlobal.curCapOpacity, orient=HORIZONTAL, command=self.sliderOpac)
        self.opacitySlider.pack(padx=5, pady=5, side=LEFT)
        _StoredGlobal.captureSlider_Cap = self.opacitySlider

        # ----------------------------------------------------------------------
        # Button
        self.captureBtn = ttk.Button(self.Frame_1, text="Capture & Translate", command=self.getTextAndTranslate)
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
        self.Tooltip1 = CreateToolTip(self.captureGrayscaleCheck, "Enhance the OCR by making the captured picture grayscale on the character reading part.", opacity=0.8)

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
        self.Tooltip2 = CreateToolTip(self.detectContourCheck, "Enhance OCR by detecting the contour of the image", opacity=0.8)

        # ----------------------------------------------------------------------
        # Background type label
        self.bgTypeLabel = Label(self.Frame_3, text="Bg Type: ")
        self.bgTypeLabel.pack(padx=5, pady=5, side=LEFT)
        self.Tooltip3 = CreateToolTip(self.bgTypeLabel, "The background type of the target", opacity=0.8)

        # Background type combobox
        self.CBBgType = ttk.Combobox(self.Frame_3, values=["Auto-Detect", "Light", "Dark"], state="readonly")
        self.CBBgType.pack(padx=0, pady=5, side=LEFT)
        self.CBBgType.bind("<<ComboboxSelected>>", lambda e: _StoredGlobal.main.capture_UI_Setting.changeCbBg(self.CBBgType.get()))
        self.Tooltip4 = CreateToolTip(self.CBBgType, "The background type of the target", opacity=0.8)

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

        self.debugModeCheck = ttk.Checkbutton(self.Frame_3, text="Debug Mode", variable=self.debugModeVar, command=self.checkDebugmode) 
        self.debugModeCheck.pack(padx=5, pady=5, side=LEFT)
        self.Tooltip5 = CreateToolTip(self.debugModeCheck, text="Enable debug mode.", opacity=0.8)

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

    # Show/Hide
    def show(self):
        _StoredGlobal.capUiHidden = False
        self.root.wm_deiconify()
        self.sliderOpac(0.8, True)

    def on_closing(self):
        _StoredGlobal.capUiHidden = True
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x, fromOutside = False):
        """Slider control, can be called from outside of the UI class

        Args:
            x ([float]): x amount
            fromOutside (bool, optional): [description]. Defaults to False.
        """
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        _StoredGlobal.curCapOpacity = x

        # Change the label and the slider in main window
        _StoredGlobal.captureOpacityLabel_Main.config(text="Capture UI Opacity: " + str(round(float(x), 2)))
        _StoredGlobal.captureSlider_Main.config(value=x)

        # Change the label and slider in the capture settings window
        _StoredGlobal.captureOpacityLabel_CapSetting.config(text="Capture UI Opacity: " + str(round(float(x), 2)))
        _StoredGlobal.captureSlider_Cap.config(value=x)

        # Update tooltip opacity
        self.Tooltip1.opacity = x
        self.Tooltip2.opacity = x
        self.Tooltip3.opacity = x
        self.Tooltip4.opacity = x
        self.Tooltip5.opacity = x

        # If from is there, it means the slider is being slide from main window
        if fromOutside:
            self.opacitySlider.set(x)

    # Capture the text
    def getTextAndTranslate(self, snippedCoords = ""):
        """Capture the text and translate it

        Args:
            snippedCoords (str, optional): If method is by snipping and capture. Defaults to "".
        """
        theUI_IsHidden = _StoredGlobal.capUiHidden
        if snippedCoords != "":
            theUI_IsHidden = False
        
        if(theUI_IsHidden): # If Hidden
            Mbox("Error: You need to generate the capture window", "Please generate the capture window first", 2, self.root)
            print("Error Need to generate the capture window! Please generate the capture window first")
            return
        # Check for the lang from and langto only if it's on translation mode
        if _StoredGlobal.engine != "None":
            # If selected langfrom and langto is the same
            if(_StoredGlobal.langFrom) == (_StoredGlobal.langTo):
                Mbox("Error: Language target is the same as source", "Please choose a different language", 2, self.root)
                print("Error Language is the same as source! Please choose a different language")
                return
            # If selected langfrom is autodetect -> invalid
            if _StoredGlobal.langFrom == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Can't Use Auto Detect in Capture Mode", 2, self.root)
                print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
                return
            # If selected langto is autodetect -> also invalid
            if _StoredGlobal.langTo == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, self.root)
                print("Error: Invalid Language Selected! Must specify language destination")
                return

        # Hide the Capture Window so it can detect the words better
        opacBefore = _StoredGlobal.curCapOpacity
        self.root.attributes('-alpha', 0)

        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()

        # Get settings
        settings = fJson.readSetting()

        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            self.root.wm_withdraw()  # Hide the capture window
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2, self.root)
            self.root.wm_deiconify()  # Show the capture window

            return # Reject

        if snippedCoords == "": # IF Captured using the capture window
            # Offsets
            offSets = getTheOffset()
            x += offSets[0]
            y += offSets[1]
            w += offSets[2]
            h += offSets[3]

            # Store the coords
            coords = [x, y, w, h]
        else: # IF CAPTURED USING THE SNIPPING
            coords = snippedCoords

        # Set language
        language = _StoredGlobal.langFrom
        tesseract_loc = settings['tesseract_loc']
        willSaveImg = settings['cached']
        willDetectContour = self.detectContourVar.get()
        willCaptureGrayscale = self.captureGrayscaleVar.get()
        bgType = self.CBBgType.get()
        debugmode = self.debugModeVar.get()

        # Capture the img
        is_Success, result = captureImg(coords, language, tesseract_loc, willSaveImg, willDetectContour, willCaptureGrayscale, bgType, debugmode)
        
        # Set opac to before
        self.root.attributes('-alpha', opacBefore)

        print("Area Captured Successfully!") # Debug Print
        print("Coordinates: " + str(coords)) # Debug Print

        if is_Success == False or len(result) == 1:
            print("But Failed to capture any text!")
            if settings['show_no_text_alert']: Mbox("Warning", "Failed to Capture Text!", 1, self.root)
        else:
            # Pass it to mainMenu
            _StoredGlobal.text_Box_Top_Var.set(result[:-1]) # Delete last character

            if settings['autoCopy'] == True:
                print("Copying text to clipboard")
                pyperclip.copy(result[:-1].strip())
                print("Copied successfully to clipboard!")

            # Run the translate function
            _StoredGlobal.translate()

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
        """
        Change the combobox value. Only called from outside of its own class. Used to sync 2 UI
        """
        self.CBBgType.current(searchList(value, ["Auto-Detect", 'Light', 'Dark']))

    # Disable enable cb
    def disableEnableCb(self, outside=False):
        """Disable or enable combobox background type

        Args:
            outside (bool, optional): value True if called from outside of its own class. Defaults to False.
        """
        if self.detectContourVar.get(): # If disabled enable it
            self.CBBgType.config(state="readonly")
        else:
            self.CBBgType.config(state="disabled") # If enable disable it
    
        if not outside: self.detectContour() # If checked from the ui itself

    # Disable enable debugmode checkbox
    def disableEnableDebugMode(self, outside=False):
        """
        Disable the debug mode checkbox if both the contour detection and the background detection is disabled
        """
        if not self.detectContourVar.get() and not self.captureGrayscaleVar.get(): # If both are not checked then disable the debugmode checkbox
            self.debugModeCheck.config(state="disabled")
        else:
            self.debugModeCheck.config(state="normal")

    # Contour checkbox
    def detectContour(self):
        """
        Event handler for detect contour checkbox that will update the var in the capture UI Settings and check for disable/enable debug mode.
        """
        _StoredGlobal.main.capture_UI_Setting.detectContourVar.set(self.detectContourVar.get())
        _StoredGlobal.main.capture_UI_Setting.disableEnableCb(outside=True)
        self.disableEnableDebugMode()
        _StoredGlobal.main.capture_UI_Setting.disableEnableDebugMode()
        
    # Grayscale checkbox
    def captureGrayscale(self):
        """
        Event handler for capture grayscale checkbox that will update the var in the capture UI Settings and check for disable/enable debug mode.
        """
        _StoredGlobal.main.capture_UI_Setting.captureGrayscaleVar.set(self.captureGrayscaleVar.get())
        self.disableEnableDebugMode()
        _StoredGlobal.main.capture_UI_Setting.disableEnableDebugMode()

    # debugmode checkbox
    def checkDebugmode(self):
        """
        Event handler for debug mode checkbox that will update the var in the capture UI Settings and check for disable/enable debug mode.
        """
        _StoredGlobal.main.capture_UI_Setting.debugModeVar.set(self.debugModeVar.get())