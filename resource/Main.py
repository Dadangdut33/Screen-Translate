import pyautogui
import asyncio
import backend.Translate as tl
import backend.Capture as capture
import backend.JsonHandling as fJson
from backend.LangCode import *
from tkinter import *
import tkinter.ttk as ttk
from Mbox import Mbox

def console():
    print("-" * 80)
    print("Welcome to Screen Translate")
    print("Use The GUI Window to start capturing and translating")
    print("This window is for debugging purposes")

# ----------------------------------------------------------------------
class CaptureUI():
    """Capture Window"""
    root = Tk()
    stayOnTop = True
    currOpacity = 0.8

    # Empty for padding purposes
    Label(root, text="").grid(row=0, column=0)
    Label(root, text="").grid(row=0, column=2)
    Label(root, text="").grid(row=0, column=3)
    Label(root, text="").grid(row=0, column=4)
    Label(root, text="").grid(row=0, column=5)
    Label(root, text="").grid(row=0, column=6)

    # Label for opacity slider
    opacityLabel = Label(root, text="Opacity: " + str(currOpacity))
    opacityLabel.grid(row=0, column=7, sticky='w')

    # Show/Hide
    def show(self):
        main_Menu.capUiHidden = False
        self.root.wm_deiconify()
    
    def on_closing(self):
        main_Menu.capUiHidden = True
        self.root.wm_withdraw()

    # Slider function
    root.attributes('-alpha', 0.8)
    def sliderOpac(self, x):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        self.currOpacity = x

        main_Menu.captureOpacityLabel.config(text="Capture UI Opacity: " + str(round(float(x), 2)))

    # Capture the text
    def getTextAndTranslate(self, offsetXY=["auto", "auto"]):
        if(main_Menu.capUiHidden): # If Hidden
            Mbox("Error: You need to generate the capture window", "Please generate the capture window first", 0)
            print("Error Need to generate the capture window! Please generate the capture window first")
            return
        if(main_Menu.CBLangFrom.current()) == (main_Menu.CBLangTo.current()): # If Selected type invalid
            Mbox("Error: Language target is the same as source", "Please choose a different language", 0)
            print("Error Language is the same as source! Please choose a different language")
            return
        if main_Menu.CBLangTo.get() == "Auto-Detect" or main_Menu.CBLangTo.current() == 0 or main_Menu.CBLangFrom.get() == "Auto-Detect" or main_Menu.CBLangFrom.current() == 0: # If Selected type invalid
            Mbox("Error: Invalid Language Selected", "Can't Use Auto Detect in Capture Mode", 0)
            print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
            return
        opacBefore = self.currOpacity
        self.root.attributes('-alpha', 0)
        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(
        ), self.root.winfo_width(), self.root.winfo_height()

        # X Y offset
        if offsetXY[0] == "auto":
            offsetX = pyautogui.size().width
            offsetY = pyautogui.size().height
        else:
            offsetX = offsetXY[0]
            offsetY = offsetXY[1]

        #  Alignment offset
        if offsetXY[1] == "auto":
            if(offsetX > offsetY):  # Horizontal alignment
                if(x < offsetX):
                    x += offsetX
            else:  # Vertical Alignment
                if(y < offsetY):
                    y += offsetY
        elif offsetXY[1] == "horizontal":
            if(x < offsetX):
                x += offsetX
        elif offsetXY[1] == "vertical":
            if(y < offsetY):
                y += offsetY

        # Capture screen
        w += 60 # added extra pixel cause sometimes it gets cut off
        h += 60
        coords = [x, y, w, h]
        tStatus, settings = fJson.readSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings == "File not Found":
                print("Error: " + settings)
                Mbox("Error: Please check your setting.json file", settings, 0)
                var1, var2 = fJson.setDefault()
                if var1 :
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 0)
        if settings['tesseract_loc'] == "":
            self.root.wm_withdraw()  # Hide the capture window
            x = Mbox("Error: Tesseract Not Set!",
                        "Please set tesseract_loc in Setting.json.\nYou can set this in setting menu or modify it manually in resource/backend/json/Setting.json", 0)
            self.root.wm_deiconify()  # Show the capture window
            return
        
        # Capture the screen
        language = main_Menu.CBLangFrom.get()
        is_Success, result = capture.captureImg(coords, language, settings['tesseract_loc'], settings['cached'])
        self.root.attributes('-alpha', opacBefore)
        
        print("Area Captured Successfully!\nText get: " + result) # Debug Print

        if is_Success == False or len(result) == 1:
            Mbox("Error", "Failed to Capture Text!", 0)
        else:
            main_Menu.root.deiconify()

            # Pass it to mainMenu
            main_Menu.textBoxTop.delete(1.0, END)
            main_Menu.textBoxTop.insert(END, result[:-1]) # Delete last character

            # Run the translate function
            main_Menu.translate(main_Menu, result[:-1])

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root.title('Text Capture Area')
        self.root.geometry('500x150')
        self.root.wm_attributes('-topmost', True)
        self.Hidden = False
        
        # Menubar
        def stay_on_top():
            if self.stayOnTop:
                self.root.wm_attributes('-topmost', False)
                self.stayOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.stayOnTop = True

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Disable Stay on Top", command=stay_on_top)
        menubar.add_cascade(label="Options", menu=filemenu)

        # Add to self.root
        self.root.config(menu=menubar)

        # Button
        captureBtn = Button(self.root, text="Capture And Translate", command=self.getTextAndTranslate)
        captureBtn.grid(row=0, column=1, sticky='e')

        # opacity slider # the slider will be added to main menu not here
        opacitySlider = ttk.Scale(self.root, from_=0.01, to=1.0, value=self.currOpacity, orient=HORIZONTAL, command=self.sliderOpac)
        opacitySlider.grid(row=0, column=4, sticky='e')

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

# ----------------------------------------------------------------------
class HistoryUI():
    """History Window"""
    root = Tk()

    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root.title("Translation History")
        self.root.geometry("400x600")
        self.root.wm_attributes('-topmost', False) # Default False
        self.root.wm_withdraw()

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

# ----------------------------------------------------------------------
class main_Menu():
    """Main Menu Window"""
    console()

    # --- Declarations and Layout ---
    # Call the other frame
    capture_UI = CaptureUI()
    history = HistoryUI()

    root = Tk()
    stayOnTop = False
    capUiHidden = False

    # Frame
    topFrame1 = Frame(root)
    topFrame1.pack(side=TOP, fill=X, expand=False)

    topFrame2 = Frame(root)
    topFrame2.pack(side=TOP, fill=BOTH, expand=True)

    bottomFrame1 = Frame(root)
    bottomFrame1.pack(side=TOP, fill=X, expand=False)

    bottomFrame2 = Frame(root)
    bottomFrame2.pack(side=BOTTOM, fill=BOTH, expand=True)

    # Capture Opacity topFrame1
    captureOpacitySlider = ttk.Scale(topFrame1, from_=0.01, to=1.0, value=capture_UI.currOpacity, orient=HORIZONTAL, command=capture_UI.sliderOpac)
    captureOpacityLabel = Label(topFrame1, text="Capture UI Opacity: " + str(capture_UI.currOpacity))

    # Combobox bottomFrame1
    # Some function
    def searchList(self, searchFor, theList):
        index = 0
        for lang in theList:
            if lang == searchFor:
                return index
            index += 1

    def fillList(dictFrom, listTo, insertFirst, insertSecond = ""):
        for item in dictFrom:
            if item == "Auto-Detect":
                continue
            listTo += [item]

        listTo.sort()
        listTo.insert(0, insertFirst)
        if insertSecond != "":
            listTo.insert(1, insertSecond)
            
    optGoogle = []
    fillList(google_Lang, optGoogle, "Auto-Detect")
    optDeepl = []
    fillList(deepl_Lang, optDeepl, "Auto-Detect")
    langOpt = optGoogle

    engines = ["Google Translate", "Deepl"]

    labelEngines = Label(bottomFrame1, text="TL Engine:")
    CBTranslateEngine = ttk.Combobox(bottomFrame1, value=engines, state="readonly")

    labelLangFrom = Label(bottomFrame1, text="From:")
    CBLangFrom = ttk.Combobox(bottomFrame1, values=langOpt, state="readonly")

    labelLangTo = Label(bottomFrame1, text="To:")
    CBLangTo = ttk.Combobox(bottomFrame1, values=langOpt, state="readonly")

    translateOnly_Btn = Button()
    captureNTranslate_Btn = Button()
    clearBtn = Button()
    swapBtn = Button()

    # Translation Textbox topFrame2 & bottomFrame2
    textBoxTop = Text(topFrame2, height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True)
    textBoxBottom = Text(bottomFrame2, height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True)

    # --- Functions ---
    async def getDeeplTl(self, text, langTo, langFrom):
        """Get the translated text from deepl.com"""
        TBottom = self.textBoxBottom

        isSuccess, translateResult = await tl.deepl_tl(text, langTo, langFrom)
        if(isSuccess):
            TBottom.delete(1.0, END)
            TBottom.insert(1.0, translateResult)
        else:
            Mbox("Error: Translation Failed", translateResult, 0)

    # Translate
    def translate(self, textOutside = ""):
        """Translate the text"""
        # Get language
        langFromObj = self.CBLangFrom
        langToObj = self.CBLangTo
        langFrom = self.CBLangFrom.get()
        langTo = self.CBLangTo.get()

        # Get the engine from the combobox
        engine = self.CBTranslateEngine.get()

        # Get Textbox
        TBBot = self.textBoxBottom

        if(langFromObj.current()) == (langToObj.current()):
            Mbox("Error: Language target is the same as source", "Please choose a different language", 0)
            print("Error Language is the same as source! Please choose a different language")
            return
        if langToObj.get() == "Auto-Detect" or langToObj.current() == 0:
            Mbox("Error: Invalid Language Selected", "Please choose a valid language", 0)
            print("Error: Invalid Language Selected! Please choose a valid language")
            return

        # Get the text from the textbox
        if textOutside == "":
            text = self.textBoxTop.get(1.0, END)
        else:
            text = textOutside

        if(len(text) < 2):
            Mbox("Error: No text entered", "Please enter some text", 0)
            print("Error: No text entered! Please enter some text")
            return

        # Translate
        if engine == "Google Translate":
            isSuccess, translateResult = tl.google_tl(text, langTo, langFrom)
            if(isSuccess):
                TBBot.delete(1.0, END)
                TBBot.insert(1.0, translateResult)
            else:
                Mbox("Error: Translation Failed", translateResult, 0)
        elif engine == "Deepl":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.getDeeplTl(text, langTo, langFrom, TBBot))
        else:
            Mbox("Error: Engine Not Set!", "Please Please select a correct engine", 0)
            print("Please select a correct engine")

    # On Close
    def on_closing(self):
        exit(0)
    
    # Open History Window
    def open_History(self):
        self.history.show()

    # Open Capture Window
    def open_capture_screen(self):
        self.capture_UI.show()

    def swapTl(self):
        # Get Before
        topBefore = self.textBoxTop.get(1.0, END)
        botBefore = self.textBoxBottom.get(1.0, END)
        # Delete
        self.textBoxTop.delete(1.0, END)
        self.textBoxBottom.delete(1.0, END)
        # Insert
        if len(topBefore) > 1:
            self.textBoxBottom.insert(1.0, topBefore[:-1])
        if len(botBefore) > 1:
            self.textBoxTop.insert(1.0, botBefore[:-1])

        # The Comboboxes
        x, y = self.CBLangFrom.current(), self.CBLangTo.current()
        self.CBLangFrom.current(y)
        self.CBLangTo.current(x) 

    # Clear TB
    def clearTB(self):
        self.textBoxTop.delete(1.0, END)
        self.textBoxBottom.delete(1.0, END)

    def tbChange(self, event = ""):
        # Get the engine from the combobox
        engine = self.CBTranslateEngine.get()

        # Translate
        if engine == "Google Translate":
            self.langOpt = self.optGoogle
            self.CBLangFrom['values'] = self.optGoogle
            self.CBLangFrom.current(0)
            self.CBLangTo['values'] = self.optGoogle
            self.CBLangTo.current(self.searchList("English", self.optDeepl))
        elif engine == "Deepl":
            self.langOpt = self.optDeepl
            self.CBLangFrom['values'] = self.optDeepl
            self.CBLangFrom.current(0)
            self.CBLangTo['values'] = self.optDeepl
            self.CBLangTo.current(self.searchList("English", self.optDeepl))

    # ----------------------------------------------------------------------
    # __init__
    def __init__(self):
        self.root.title("Screen Translate - Main Menu")
        self.root.geometry("900x300")
        self.root.wm_attributes('-topmost', False) # Default False
        tStatus, settings = fJson.readSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings == "File not Found":
                print("Error: " + settings)
                Mbox("Error: Please check your setting.json file", settings, 0)
                var1, var2 = fJson.setDefault()
                if var1 :
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 0)
        if settings['tesseract_loc'] == "":
            x = Mbox("Error: Tesseract Not Set!",
                        "Please set tesseract_loc in Setting.json.\nYou can set this in setting menu or modify it manually in resource/backend/json/Setting.json", 0)

        # Menubar
        def stay_on_top():
            if self.stayOnTop:
                self.root.wm_attributes('-topmost', False)
                self.stayOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.stayOnTop = True

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Stay on Top", command=stay_on_top)
        filemenu.add_separator()
        filemenu.add_command(label="Exit Application", command=self.root.quit)
        menubar.add_cascade(label="Options", menu=filemenu)

        filemenu2 = Menu(menubar, tearoff=0)
        filemenu2.add_command(label="History", command=self.open_History) # Open History Window
        filemenu2.add_command(label="Setting") # Open Setting Window
        menubar.add_cascade(label="View", menu=filemenu2)

        filemenu3 = Menu(menubar, tearoff=0)
        filemenu3.add_command(label="Capture Window", command=self.open_capture_screen) # Open Capture Screen Window
        menubar.add_cascade(label="Generate", menu=filemenu3)

        filemenu4 = Menu(menubar, tearoff=0)
        filemenu4.add_command(label="Tutorials") # Open Mbox Tutorials
        filemenu4.add_command(label="FAQ") # Open Mbox Tutorials
        filemenu4.add_separator()
        filemenu4.add_command(label="About") # Open Mbox About
        menubar.add_cascade(label="Help", menu=filemenu4)

        # Add to self.root
        self.root.config(menu=menubar)

        # topFrame1
        translateOnly_Btn = Button(self.topFrame1, text="Translate", command=self.translate)
        captureNTranslate_Btn = Button(self.topFrame1, text="Capture And Translate", command=self.capture_UI.getTextAndTranslate)
        translateOnly_Btn.pack(side=LEFT, padx=5, pady=5)
        captureNTranslate_Btn.pack(side=LEFT, padx=5, pady=5)

        # topFrame1
        self.captureOpacitySlider.pack(side=LEFT, padx=5, pady=5)
        self.captureOpacityLabel.pack(side=LEFT, padx=5, pady=5)

        print(settings['default_Engine'])
        # bottomFrame1
        self.labelEngines.pack(side=LEFT, padx=5, pady=5)
        self.CBTranslateEngine.current(self.searchList(settings['default_Engine'], self.engines))
        self.CBTranslateEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBTranslateEngine.bind("<<ComboboxSelected>>", self.tbChange)

        self.tbChange() # Update the cb

        self.labelLangFrom.pack(side=LEFT, padx=5, pady=5)
        self.CBLangFrom.current(self.searchList(settings['default_FromOnOpen'], self.langOpt))
        self.CBLangFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelLangTo.pack(side=LEFT, padx=5, pady=5)
        self.CBLangTo.current(self.searchList(settings['default_ToOnOpen'], self.langOpt)) # Default to English
        self.CBLangTo.pack(side=LEFT, padx=5, pady=5)

        # Button bottomFrame1
        self.clearBtn = Button(self.bottomFrame1, text="Clear", command=self.clearTB)
        self.swapBtn = Button(self.bottomFrame1, text="Swap", command=self.swapTl)
        self.swapBtn.pack(side=LEFT, padx=5, pady=5)
        self.clearBtn.pack(side=LEFT, padx=5, pady=5)

        # Translation Textbox topFrame2 bottomFrame
        self.textBoxTop.pack(padx=5, pady=5, fill=BOTH, expand=True)
        self.textBoxBottom.pack(padx=5, pady=5, fill=BOTH, expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

main_Menu()
main_Menu.root.mainloop()