import tkinter.ttk as ttk
from tkinter import *
from ..Public import fJson, globalStuff
from ..Public import offSetSettings
from ..Mbox import Mbox
from ..Capture import captureImg
import pyperclip
import os

# Classes
class CaptureUI():
    """Capture Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Text Capture Area')
        self.root.geometry('500x150')
        globalStuff.capUiHidden = True
        self.root.wm_withdraw()

        globalStuff.curCapOpacity = 0.8
        self.root.attributes('-alpha', 0.8)

        # Top frame
        self.topFrame = Frame(self.root)
        self.topFrame.pack(side=TOP, fill=X, expand=False)

        # Label for opacity slider
        self.opacityLabel = Label(self.topFrame, text="Opacity: " + str(globalStuff.curCapOpacity))
        self.opacityLabel.pack(padx=5, pady=5, side=LEFT)

        # Always on top checkbox
        self.menubar = Menu(self.root)
        self.alwaysOnTopVar = BooleanVar()
        # What happen here is that we created a hidden checkbutton to control the variable because for some reason it JUST DOES NOT WORK properly i dont know why
        # If someone found a better solution to this problem, please let me know or just create a pull request.
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.topFrame, text="Always on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # Button
        captureBtn = Button(self.topFrame, text="Capture And Translate", command=self.getTextAndTranslate)
        captureBtn.pack(padx=5, pady=5, side=LEFT)

        # opacity slider # the slider will be added to main menu not here
        opacitySlider = ttk.Scale(self.topFrame, from_=0.0, to=1.0, value=globalStuff.curCapOpacity, orient=HORIZONTAL, command=self.sliderOpac)
        opacitySlider.pack(padx=5, pady=5, side=LEFT)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Show/Hide
    def show(self):
        globalStuff.capUiHidden = False
        self.root.wm_deiconify()

    def on_closing(self):
        globalStuff.capUiHidden = True
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        globalStuff.curCapOpacity = x

        globalStuff.captureOpacityLabel_Var.set("Capture UI Opacity: " + str(round(float(x), 2)))

    # Capture the text
    def getTextAndTranslate(self, offSetXY=["auto", "auto"]):
        if(globalStuff.capUiHidden): # If Hidden
            Mbox("Error: You need to generate the capture window", "Please generate the capture window first", 2)
            print("Error Need to generate the capture window! Please generate the capture window first")
            return
        # Check for the lang from and langto only if it's on translation mode
        if globalStuff.engine != "None":
            # If selected langfrom and langto is the same
            if(globalStuff.langFrom) == (globalStuff.langTo):
                Mbox("Error: Language target is the same as source", "Please choose a different language", 2)
                print("Error Language is the same as source! Please choose a different language")
                return
            # If selected langfrom is autodetect -> invalid
            if globalStuff.langFrom == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Can't Use Auto Detect in Capture Mode", 2)
                print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
                return
            # If selected langto is autodetect -> also invalid
            if globalStuff.langTo == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Must specify language destination", 2)
                print("Error: Invalid Language Selected! Must specify language destination")
                return

        # Hide the Capture Window so it can detect the words better
        opacBefore = globalStuff.curCapOpacity
        self.root.attributes('-alpha', 0)

        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()

        # Get settings
        settings = fJson.readSetting()

        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            self.root.wm_withdraw()  # Hide the capture window
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2)
            self.root.wm_deiconify()  # Show the capture window

            return # Reject

        # Store setting to localvar
        offSetXY = settings["offSetXY"]
        offSetWH = settings["offSetWH"]
        xyOffSetType = settings["offSetXYType"]

        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY)
        x += offSets[0]
        y += offSets[1]
        w += offSets[2]
        h += offSets[3]

        # Capture the screen
        coords = [x, y, w, h]

        language = globalStuff.langFrom
        is_Success, result = captureImg(coords, language, settings['tesseract_loc'], settings['cached'])
        self.root.attributes('-alpha', opacBefore)

        print("Area Captured Successfully!") # Debug Print
        print("Coordinates: " + str(coords)) # Debug Print

        if is_Success == False or len(result) == 1:
            print("But Failed to capture any text!")
            Mbox("Warning", "Failed to Capture Text!", 1)
        else:
            # Pass it to mainMenu
            globalStuff.text_Box_Top_Var.set(result[:-1]) # Delete last character

            if settings['autoCopy'] == True:
                print("Copying text to clipboard")
                pyperclip.copy(result[:-1].strip())
                print("Copied successfully to clipboard!")

            # Run the translate function
            globalStuff.translate()

    # Menubar
    def always_on_top(self):
        if self.alwaysOnTopVar.get(): # IF ON THEN TURN IT OFF
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTopVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTopVar.set(True)