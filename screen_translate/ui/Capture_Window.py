import tkinter.ttk as ttk
from tkinter import *
from screen_translate.Public import fJson, getTheOffset, globalStuff
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
        self.root.geometry('500x150')
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
        self.alwaysOnTopVar.set(True)
        self.topHiddenVar = BooleanVar()
        self.root.wm_attributes('-topmost', True)

        # What happen here is that we created a hidden checkbutton to control the variable because for some reason it JUST DOES NOT WORK properly i dont know why
        # If someone found a better solution to this problem, please let me know or just create a pull request.
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.topFrame, text="Stay on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.topHiddenCheck = Checkbutton(self.topFrame, text="Hide Top", variable=self.topHiddenVar, command=self.show_top)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.filemenu.add_checkbutton(label="Hide Top", onvalue=True, offvalue=False, variable=self.topHiddenVar, command=self.show_top)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # Button
        self.captureBtn = ttk.Button(self.topFrame, text="Capture And Translate", command=self.getTextAndTranslate)
        self.captureBtn.pack(padx=5, pady=5, side=LEFT)

        # opacity slider # the slider will be added to main menu not here
        self.opacitySlider = ttk.Scale(self.topFrame, from_=0.0, to=1.0, value=globalStuff.curCapOpacity, orient=HORIZONTAL, command=self.sliderOpac)
        self.opacitySlider.pack(padx=5, pady=5, side=LEFT)

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
        globalStuff.capUiHidden = False
        self.root.wm_deiconify()
        self.sliderOpac(0.8, "main")

    def on_closing(self):
        globalStuff.capUiHidden = True
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x, from_=None):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        globalStuff.curCapOpacity = x

        # Change the label and the slider in main window
        globalStuff.captureOpacityObject.config(text="Capture UI Opacity: " + str(round(float(x), 2)))
        globalStuff.captureSlider_Main.config(value=x)

        # If from is there, it means the slider is being slide from main window
        if from_ is not None:
            self.opacitySlider.set(x)

    # Capture the text
    def getTextAndTranslate(self, offSetXY=["auto", "auto"]):
        if(globalStuff.capUiHidden): # If Hidden
            Mbox("Error: You need to generate the capture window", "Please generate the capture window first", 2, self.root)
            print("Error Need to generate the capture window! Please generate the capture window first")
            return
        # Check for the lang from and langto only if it's on translation mode
        if globalStuff.engine != "None":
            # If selected langfrom and langto is the same
            if(globalStuff.langFrom) == (globalStuff.langTo):
                Mbox("Error: Language target is the same as source", "Please choose a different language", 2, self.root)
                print("Error Language is the same as source! Please choose a different language")
                return
            # If selected langfrom is autodetect -> invalid
            if globalStuff.langFrom == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Can't Use Auto Detect in Capture Mode", 2, self.root)
                print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
                return
            # If selected langto is autodetect -> also invalid
            if globalStuff.langTo == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, self.root)
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
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2, self.root)
            self.root.wm_deiconify()  # Show the capture window

            return # Reject

        # Offsets
        offSets = getTheOffset()
        x += offSets[0]
        y += offSets[1]
        w += offSets[2]
        h += offSets[3]

        # Store the coords
        coords = [x, y, w, h]

        # Set language
        language = globalStuff.langFrom

        # Capture the img
        is_Success, result = captureImg(coords, language, settings['tesseract_loc'], settings['cached'], settings['enhance_Capture']['cv2_Contour'], 
        settings['enhance_Capture']['grayscale'], settings['enhance_Capture']['backgroundIsLight'])
        
        # Set opac to before
        self.root.attributes('-alpha', opacBefore)

        print("Area Captured Successfully!") # Debug Print
        print("Coordinates: " + str(coords)) # Debug Print

        if is_Success == False or len(result) == 1:
            print("But Failed to capture any text!")
            Mbox("Warning", "Failed to Capture Text!", 1, self.root)
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
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTopVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTopVar.set(True)