import json
from tkinter import colorchooser
import tkinter.ttk as ttk
import keyboard
from tkinter import *
from tkinter import filedialog

from tkfontchooser import askfont
from screen_translate.Public import CreateToolTip, fJson, globalStuff
from screen_translate.Public import startfile, optGoogle, optDeepl, optMyMemory, optPons, optNone, engines, getTheOffset, searchList
from screen_translate.Mbox import Mbox
from screen_translate.Capture import captureAll
import os
# Get dir path
dir_path = os.path.dirname(os.path.realpath(__file__))

# ----------------------------------------------------------------------
class SettingUI():
    """Setting Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title("Setting")
        self.root.geometry("915x350")
        self.root.wm_attributes('-topmost', False) # Default False
        self.root.wm_withdraw()
        self.root.resizable(False, False)

        # ----------------------------------------------------------------------
        # Main frame
        self.mainFrameTop = Frame(self.root)
        self.mainFrameTop.pack(side=TOP, fill=BOTH, expand=True)

        self.mainFrameBot = Frame(self.root, bg="#7E7E7E")
        self.mainFrameBot.pack(side=BOTTOM, fill=X, pady=(5, 0), padx=5)
        
        # Left frame for categorization
        self.frameLeftBg = LabelFrame(self.mainFrameTop, text="Options", labelanchor=N)
        self.frameLeftBg.pack(side=LEFT, fill=Y, padx=5, pady=5)

        # Listbox for the category list
        self.listboxCat = Listbox(self.frameLeftBg, selectmode=SINGLE, exportselection=False)
        self.listboxCat.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        self.listboxCat.insert(1, "Capturing/Offset")
        self.listboxCat.insert(2, "OCR Engine")
        self.listboxCat.insert(3, "Translate")
        self.listboxCat.insert(4, "Hotkey")
        self.listboxCat.insert(5, "Query/Result Box")
        self.listboxCat.insert(6, "Other")

        # Bind the listbox to the function
        self.listboxCat.bind("<<ListboxSelect>>", self.onSelect)

        # ----------------------------------------------------------------------
        # Capturing/OCR
        self.frameCapture = Frame(self.mainFrameTop)
        self.frameCapture.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        # [Img/OCR Setting]
        self.fLabelCapture_1 = LabelFrame(self.frameCapture, text="• Capturing Setting", width=750, height=55)
        self.fLabelCapture_1.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelCapture_1.pack_propagate(0)
        self.content_Cap_1 = Frame(self.fLabelCapture_1)
        self.content_Cap_1.pack(side=TOP, fill=X, expand=False)

        self.checkVarImgSaved = BooleanVar(self.root, value=True) # So its not error
        self.checkBTNSaved = ttk.Checkbutton(self.content_Cap_1, text="Save Captured Image", variable=self.checkVarImgSaved)
        self.checkVarAutoCopy = BooleanVar(self.root, value=True) # So its not error
        self.checkBTNAutoCopy = ttk.Checkbutton(self.content_Cap_1, text="Auto Copy Captured Text To Clipboard", variable=self.checkVarAutoCopy)
        self.btnOpenImgFolder = ttk.Button(self.content_Cap_1, text="Open Captured Image Folder", command=lambda: startfile(dir_path + r"\..\..\img_captured"))

        self.checkBTNAutoCopy.pack(side=LEFT, padx=5, pady=5)
        self.checkBTNSaved.pack(side=LEFT, padx=5, pady=5)
        self.btnOpenImgFolder.pack(side=LEFT, padx=5, pady=5)

        # [Offset]
        self.fLabelCapture_2 = LabelFrame(self.frameCapture, text="• Monitor Capture Offset", width=750, height=150)
        self.fLabelCapture_2.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fLabelCapture_2.pack_propagate(0)
        self.content_Cap_2_1 = Frame(self.fLabelCapture_2)
        self.content_Cap_2_1.pack(side=TOP, fill=X, expand=False)
        self.content_Cap_2_2 = Frame(self.fLabelCapture_2)
        self.content_Cap_2_2.pack(side=TOP, fill=X, expand=False)
        self.content_Cap_2_3 = Frame(self.fLabelCapture_2)
        self.content_Cap_2_3.pack(side=TOP, fill=X, expand=False)
        self.content_Cap_2_4 = Frame(self.fLabelCapture_2)
        self.content_Cap_2_4.pack(side=TOP, fill=X, expand=False)

        self.labelCBOffsetNot = Label(self.content_Cap_2_1, text="Capture XY Offset :")
        self.labelCBOffsetNot.pack(side=LEFT, padx=5, pady=5)

        self.CBOffSetChoice = ttk.Combobox(self.content_Cap_2_1, values=["No Offset", "Custom Offset"], state="readonly")
        self.CBOffSetChoice.pack(side=LEFT, padx=5, pady=5)
        self.CBOffSetChoice.bind("<<ComboboxSelected>>", self.CBOffSetChange)

        self.buttonCheckMonitorLayout = ttk.Button(self.content_Cap_2_1, text="Click to get A Screenshot of How The Program See Your Monitor", command=self.screenShotAndOpenLayout)
        self.buttonCheckMonitorLayout.pack(side=LEFT, padx=5, pady=5)

        self.checkVarOffSetX = BooleanVar(self.root, value=True)
        self.checkVarOffSetY = BooleanVar(self.root, value=True)
        self.checkVarOffSetW = BooleanVar(self.root, value=True)
        self.checkVarOffSetH = BooleanVar(self.root, value=True)

        self.spinValOffSetX = IntVar(self.root)
        self.spinValOffSetY = IntVar(self.root)
        self.spinValOffSetW = IntVar(self.root)
        self.spinValOffSetH = IntVar(self.root)

        self.labelOffSetX = Label(self.content_Cap_2_3, text="Offset X :")
        self.labelOffSetY = Label(self.content_Cap_2_4, text="Offset Y :")
        self.labelOffSetW = Label(self.content_Cap_2_3, text="Offset W :")
        self.labelOffSetH = Label(self.content_Cap_2_4, text="Offset H :")

        self.validateDigits_Offset_X = (self.root.register(self.validateSpinBox_Offset_X), '%P')
        self.validateDigits_Offset_Y = (self.root.register(self.validateSpinBox_Offset_Y), '%P')
        self.validateDigits_Offset_W = (self.root.register(self.validateSpinBox_Offset_W), '%P')
        self.validateDigits_Offset_H = (self.root.register(self.validateSpinBox_Offset_H), '%P')
        self.validateDigits_Delay = (self.root.register(self.validateSpinBox_Delay), '%P')

        self.spinnerOffSetX = ttk.Spinbox(self.content_Cap_2_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetX)
        self.spinnerOffSetX.configure(validate='key', validatecommand=self.validateDigits_Offset_X)
        self.spinnerOffSetX.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetX))

        self.spinnerOffSetY = ttk.Spinbox(self.content_Cap_2_4, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetY)
        self.spinnerOffSetY.configure(validate='key', validatecommand=self.validateDigits_Offset_Y)
        self.spinnerOffSetY.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetY))

        self.spinnerOffSetW = ttk.Spinbox(self.content_Cap_2_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetW)
        self.spinnerOffSetW.configure(validate='key', validatecommand=self.validateDigits_Offset_W)
        self.spinnerOffSetW.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetW))

        self.spinnerOffSetH = ttk.Spinbox(self.content_Cap_2_4, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetH)
        self.spinnerOffSetH.configure(validate='key', validatecommand=self.validateDigits_Offset_H)
        self.spinnerOffSetH.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerOffSetH))

        self.checkAutoOffSetX = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset X", variable=self.checkVarOffSetX, command=lambda: self.checkBtnOffset(self.spinnerOffSetX, self.spinValOffSetX, self.checkVarOffSetX, "x"))
        self.checkAutoOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetY = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset Y", variable=self.checkVarOffSetY, command=lambda: self.checkBtnOffset(self.spinnerOffSetY, self.spinValOffSetY, self.checkVarOffSetY, "y"))
        self.checkAutoOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetW = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset W", variable=self.checkVarOffSetW, command=lambda: self.checkBtnOffset(self.spinnerOffSetW, self.spinValOffSetW, self.checkVarOffSetW, "w"))
        self.checkAutoOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetH = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset H", variable=self.checkVarOffSetH, command=lambda: self.checkBtnOffset(self.spinnerOffSetH, self.spinValOffSetH, self.checkVarOffSetH, "h"))
        self.checkAutoOffSetH.pack(side=LEFT, padx=5, pady=5)

        self.labelOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.labelOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.labelOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.labelOffSetH.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetH.pack(side=LEFT, padx=8, pady=5)

        # ----------------------------------------------------------------------
        # OCR Engine
        self.frameEngine = Frame(self.mainFrameTop)
        self.frameEngine.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        self.fLabelEngine_1 = LabelFrame(self.frameEngine, text="• Tesseract OCR Settings", width=750, height=55)
        self.fLabelEngine_1.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelEngine_1.pack_propagate(0)
        self.content_Engine_1 = Frame(self.fLabelEngine_1)
        self.content_Engine_1.pack(side=TOP, fill=X, expand=False)

        self.labelTesseractPath = Label(self.content_Engine_1, text="Tesseract Path :")
        self.labelTesseractPath.pack(side=LEFT, padx=5, pady=5)

        self.textBoxTesseractPath = ttk.Entry(self.content_Engine_1, width=70, xscrollcommand=True)
        self.textBoxTesseractPath.bind("<Key>", lambda event: globalStuff.allowedKey(event)) # Disable textbox input
        self.textBoxTesseractPath.pack(side=LEFT, padx=5, pady=5, fill=X, expand=True)

        self.btnSearchTesseract = ttk.Button(self.content_Engine_1, text="...", command=self.searchTesseract)
        self.btnSearchTesseract.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------------
        # Translate
        self.frameTranslate = Frame(self.mainFrameTop)
        self.frameTranslate.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        
        self.fLabelTl_1 = LabelFrame(self.frameTranslate, text="• Translation Settings", width=750, height=80)
        self.fLabelTl_1.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelTl_1.pack_propagate(0)

        self.content_Tl_1 = Frame(self.fLabelTl_1)
        self.content_Tl_1.pack(side=TOP, fill=X, expand=False)

        self.content_Tl_2 = Frame(self.fLabelTl_1)
        self.content_Tl_2.pack(side=TOP, fill=X, expand=False)

        self.langOpt = optGoogle
        self.labelDefaultEngine = Label(self.content_Tl_1, text="Default TL Engine :")
        self.labelDefaultEngine.pack(side=LEFT, padx=5, pady=5)

        self.CBDefaultEngine = ttk.Combobox(self.content_Tl_1, values=engines, state="readonly")
        self.CBDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.bind("<<ComboboxSelected>>", self.CBTLChange_setting)

        self.labelDefaultFrom = Label(self.content_Tl_1, text="Default From :")
        self.labelDefaultFrom.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultFrom = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelDefaultTo = Label(self.content_Tl_1, text="Default To :")
        self.labelDefaultTo.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultTo = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultTo.pack(side=LEFT, padx=5, pady=5)

        self.labelSaveToHistory = Label(self.content_Tl_2, text="Save to History :")
        self.labelSaveToHistory.pack(side=LEFT, padx=5, pady=5)

        self.saveToHistoryVar = BooleanVar(self.root, value=True)
        self.checkSaveToHistory = ttk.Checkbutton(self.content_Tl_2, variable=self.saveToHistoryVar)
        self.checkSaveToHistory.pack(side=LEFT, padx=5, pady=5)


        # ----------------------------------------------------------------------
        # Hotkey
        self.frameHotkey = Frame(self.mainFrameTop)
        self.frameHotkey.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        
        self.fLabelHotkey_1 = LabelFrame(self.frameHotkey, text="• Capture Hotkey Settings", width=750, height=55)
        self.fLabelHotkey_1.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelHotkey_1.pack_propagate(0)
        self.content_Hotkey_1 = Frame(self.fLabelHotkey_1)
        self.content_Hotkey_1.pack(side=TOP, fill=X, expand=False)

        self.spinValHotkeyDelay = IntVar(self.root)

        self.labelHotkeyDelay = Label(self.content_Hotkey_1, text="Time delay (ms) : ")
        self.labelHotkeyDelay.pack(side=LEFT, padx=5, pady=5)
        
        self.spinnerHotkeyDelay = ttk.Spinbox(self.content_Hotkey_1, from_=0, to=100000, width=20, textvariable=self.spinValHotkeyDelay)
        self.spinnerHotkeyDelay.configure(validate='key', validatecommand=self.validateDigits_Delay)
        self.spinnerHotkeyDelay.pack(side=LEFT, padx=5, pady=5)
        
        self.buttonSetHotkey = ttk.Button(self.content_Hotkey_1, text="Click to set hotkey for capture", command=self.setHotkey)
        self.buttonSetHotkey.pack(side=LEFT, padx=5, pady=5)
        
        self.buttonClearHotkey = ttk.Button(self.content_Hotkey_1, text="Clear", command=self.clearHotkey)
        self.buttonClearHotkey.pack(side=LEFT, padx=5, pady=5)
        
        self.labelHotkeyTip = Label(self.content_Hotkey_1, text="Current hotkey : ")
        self.labelHotkeyTip.pack(side=LEFT, padx=5, pady=5)

        self.labelCurrentHotkey = Label(self.content_Hotkey_1, text="")
        self.labelCurrentHotkey.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------------
        # Query/Result box
        self.frameQueryResult = Frame(self.mainFrameTop)
        self.frameQueryResult.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        self.fLabelQuery = LabelFrame(self.frameQueryResult, text="• Query Box", width=750, height=110)
        self.fLabelQuery.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelQuery.pack_propagate(0)

        self.fQueryContent_1 = Frame(self.fLabelQuery)
        self.fQueryContent_1.pack(side=TOP, fill=X, expand=False)

        self.fQueryContent_2 = Frame(self.fLabelQuery)
        self.fQueryContent_2.pack(side=TOP, fill=X, expand=False)

        self.fQueryContent_3 = Frame(self.fLabelQuery)
        self.fQueryContent_3.pack(side=TOP, fill=X, expand=False)

        self.queryBgVar = globalStuff.queryBg
        self.queryBg = Label(self.fQueryContent_1, text="Textbox Bg Color : ")
        self.queryBg.pack(side=LEFT, padx=5, pady=5)
        self.queryBg.bind("<Button-1>", lambda event: self.bgColorChooser(label=self.queryBg, 
        theVar=self.queryBgVar, destination=globalStuff.main.query_Detached_Window_UI))
        CreateToolTip(self.queryBg, "Click to choose query textbox background color")

        self.hintLabelQuery = Label(self.fQueryContent_1, text="❓")
        self.hintLabelQuery.pack(padx=5, pady=5, side=RIGHT)
        CreateToolTip(self.hintLabelQuery, "Click on the label to change the value of the settings")

        self.queryFgVar = globalStuff.queryFg
        self.queryFg = Label(self.fQueryContent_2, text="Textbox Fg Color : ")
        self.queryFg.pack(side=LEFT, padx=5, pady=5)
        self.queryFg.bind("<Button-1>", lambda event: self.fgColorChooser(label=self.queryFg,
        theVar=self.queryFgVar, destination=globalStuff.main.query_Detached_Window_UI))
        CreateToolTip(self.queryFg, "Click to choose query textbox foreground color")

        self.queryFontVar = globalStuff.queryFont
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.queryFont = Label(self.fQueryContent_3, text="Textbox Font : ")
        self.queryFont.pack(side=LEFT, padx=5, pady=5)
        self.queryFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.queryFont,
        theVar=self.queryFontVar, theDict=self.queryFontDict, destination=globalStuff.main.query_Detached_Window_UI))
        CreateToolTip(self.queryFont, "Click to choose query textbox font")

        self.fLabelResult = LabelFrame(self.frameQueryResult, text="• Result Box", width=750, height=110)
        self.fLabelResult.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fLabelResult.pack_propagate(0)

        self.fResultContent_1 = Frame(self.fLabelResult)
        self.fResultContent_1.pack(side=TOP, fill=X, expand=False)

        self.fResultContent_2 = Frame(self.fLabelResult)
        self.fResultContent_2.pack(side=TOP, fill=X, expand=False)

        self.fResultContent_3 = Frame(self.fLabelResult)
        self.fResultContent_3.pack(side=TOP, fill=X, expand=False)

        self.resultBgVar = globalStuff.resultBg
        self.resultBg = Label(self.fResultContent_1, text="Textbox Bg Color : ")
        self.resultBg.pack(side=LEFT, padx=5, pady=5)
        self.resultBg.bind("<Button-1>", lambda event: self.bgColorChooser(label=self.resultBg,
        theVar=self.resultBgVar, destination=globalStuff.main.result_Detached_Window_UI))
        CreateToolTip(self.resultBg, "Click to choose result textbox background color")

        self.hintLabelResult = Label(self.fResultContent_1, text="❓")
        self.hintLabelResult.pack(padx=5, pady=5, side=RIGHT)
        CreateToolTip(self.hintLabelResult, "Click on the label to change the value of the settings")

        self.resultFgVar = globalStuff.resultFg
        self.resultFg = Label(self.fResultContent_2, text="Textbox Fg Color : ")
        self.resultFg.pack(side=LEFT, padx=5, pady=5)
        self.resultFg.bind("<Button-1>", lambda event: self.fgColorChooser(label=self.resultFg,
        theVar=self.resultFgVar, destination=globalStuff.main.result_Detached_Window_UI))
        CreateToolTip(self.resultFg, "Click to choose result textbox foreground color")

        self.resultFontVar = globalStuff.resultFont
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        self.resultFont = Label(self.fResultContent_3, text="Textbox Font : ")
        self.resultFont.pack(side=LEFT, padx=5, pady=5)
        self.resultFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.resultFont,
        theVar=self.resultFontVar, theDict=self.resultFontDict, destination=globalStuff.main.result_Detached_Window_UI))
        CreateToolTip(self.resultFont, "Click to choose result textbox font")

        # ----------------------------------------------------------------------
        # Other
        self.frameOther = Frame(self.mainFrameTop)
        self.frameOther.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        self.fLabelOther = LabelFrame(self.frameOther, text="• Other Settings", width=750, height=55)
        self.fLabelOther.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelOther.pack_propagate(0)

        self.fOtherContent_1 = Frame(self.fLabelOther)
        self.fOtherContent_1.pack(side=TOP, fill=X, expand=False)

        # Checkbox for check for update
        self.checkUpdateVar = BooleanVar(self.root, value=True)
        self.checkUpdateBox = ttk.Checkbutton(self.fOtherContent_1, text="Check for update on app start", variable=self.checkUpdateVar)
        self.checkUpdateBox.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # Bottom Frame
        # Create a bottom frame to hold the buttons
        self.bottomFrame = Frame(self.mainFrameBot)
        self.bottomFrame.pack(side=BOTTOM, fill=X, pady=(1,0))

        # Create the buttons
        self.btnSave = ttk.Button(self.bottomFrame, text="Save Settings", command=self.saveSettings)
        self.btnSave.pack(side=RIGHT, padx=4, pady=5)
        
        self.btnReset = ttk.Button(self.bottomFrame, text="Reset To Currently Stored Setting", command=self.reset)
        self.btnReset.pack(side=RIGHT, padx=5, pady=5)

        self.btnRestoreDefault = ttk.Button(self.bottomFrame, text="Restore Default", command=self.restoreDefault)
        self.btnRestoreDefault.pack(side=RIGHT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.hideAllFrame()
        self.listboxCat.select_set(0)
        self.showFrame(self.frameCapture)

    # ----------------------------------------------------------------
    # Functions
    # ----------------------------------------------------------------
    def show(self):
        fJson.loadSetting() # read settings every time it is opened
        self.reset()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def disableScrollWheel(self, event=None, theSpinner=None):
        if theSpinner["state"] == "disabled":
            return 'break'

    def onSelect(self, event):
        """On Select for frame changing

        Args:
            event ([type]): Ignored click event
        """
        if self.listboxCat.curselection() != ():
            self.hideAllFrame()

            if self.listboxCat.curselection()[0] == 0:
                self.showFrame(self.frameCapture)
            
            elif self.listboxCat.curselection()[0] == 1:
                self.showFrame(self.frameEngine)
            
            elif self.listboxCat.curselection()[0] == 2:
                self.showFrame(self.frameTranslate)
            
            elif self.listboxCat.curselection()[0] == 3:
                self.showFrame(self.frameHotkey)

            elif self.listboxCat.curselection()[0] == 4:
                self.showFrame(self.frameQueryResult)

            elif self.listboxCat.curselection()[0] == 5:
                self.showFrame(self.frameOther)

    def hideAllFrame(self):
        """
        Hide all frames
        """
        self.frameCapture.pack_forget()
        self.frameEngine.pack_forget()
        self.frameTranslate.pack_forget()
        self.frameHotkey.pack_forget()
        self.frameQueryResult.pack_forget()
        self.frameOther.pack_forget()

    def showFrame(self, frame):
        """Change frame for each setting

        Args:
            frame ([type]): The frame that will be displayed
        """
        frame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

    def restoreDefault(self):
        """
        Restore default settings
        """
        x = Mbox("Confirmation", "Are you sure you want to set the settings to default?\n\n**WARNING! CURRENTLY SAVED SETTING WILL BE OVERWRITTEN**", 3, self.root)
        if x == False:
            Mbox("Canceled", "Action Canceled", 0, self.root)
            return

        # Restore Default Settings
        tStatus, settings = fJson.setDefault()
        if tStatus == True:
            # Update the settings
            self.reset()

            # Tell success
            print("Restored Default Settings")
            Mbox("Success", "Successfully Restored Value to Default Settings", 0, self.root)

    def reset(self):
        """
        Reset the settings to currently stored settings
        """
        status, settings = fJson.loadSetting()

        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2, self.root)

        # Cache checkbox
        try:
            self.checkVarImgSaved.set(settings['cached'])
        except Exception as e:
            print("Error: Invalid Image Saving Options")
            Mbox("Error: Invalid Image Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarImgSaved.set(True)

        # Autocopy checkbox
        try:
            self.checkVarAutoCopy.set(settings['autoCopy'])
        except Exception as e:
            print("Error: Invalid Autocopy Options")
            Mbox("Error: Invalid Autocopy Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarAutoCopy.set(True)

        # Save to history checkbox
        try:
            self.saveToHistoryVar.set(settings['saveHistory'])
        except Exception as e:
            print(e)
            print("Error: Invalid History Saving Options")
            Mbox("Error: Invalid History Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.saveToHistoryVar.set(True)

        # Check for update checkbox
        try:
            self.checkUpdateVar.set(settings['checkUpdateOnStart'])
        except Exception as e:
            print("Error: Invalid Update Checking Options")
            Mbox("Error: Invalid Update Checking Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkUpdateVar.set(True)

        # Set label value for query and result box
        # Query
        self.queryFontVar.set(settings['Query_Box']['font'])
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.queryBgVar.set(settings['Query_Box']['bg'])
        self.queryFgVar.set(settings['Query_Box']['fg'])
        query_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict
        self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
        self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
        self.queryFont.config(text="Textbox Font : " + query_font_str)

        # Result
        self.resultFontVar.set(settings['Result_Box']['font'])
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        self.resultBgVar.set(settings['Result_Box']['bg'])
        self.resultFgVar.set(settings['Result_Box']['fg'])
        result_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.resultFontDict
        self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
        self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())
        self.resultFont.config(text="Textbox Font : " + result_font_str)

        # Show current hotkey
        self.labelCurrentHotkey.config(text=settings['capture_Hotkey'])

        self.spinValHotkeyDelay.set(settings["capture_HotkeyDelay"])

        # Store setting to localvar
        offSetXY = settings["offSetXY"]
        xyOffSetType = settings["offSetXYType"]

        # Get offset
        x, y, w, h = getTheOffset()

        # If cb no offset
        if xyOffSetType == "No Offset":
            self.CBOffSetChoice.current(0)
            self.checkAutoOffSetX.config(state=DISABLED)
            self.checkAutoOffSetY.config(state=DISABLED)
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetX.set(0)
            self.spinValOffSetY.set(0)

            self.checkVarOffSetX.set(False)
            self.checkVarOffSetY.set(False)

        # If cb custom offset
        elif xyOffSetType == "Custom Offset":
            self.CBOffSetChoice.current(1)
            self.spinValOffSetX.set(x)
            self.spinValOffSetY.set(y)
            self.checkAutoOffSetX.config(state=NORMAL)
            self.checkAutoOffSetY.config(state=NORMAL)

            if offSetXY[0] == "auto":
                self.checkVarOffSetX.set(True)
                self.spinnerOffSetX.config(state=DISABLED)
            else:
                self.checkVarOffSetX.set(False)
                self.spinnerOffSetX.config(state=NORMAL)

            if offSetXY[1] == "auto":
                self.checkVarOffSetY.set(True)
                self.spinnerOffSetY.config(state=DISABLED)
            else:
                self.checkVarOffSetY.set(False)
                self.spinnerOffSetY.config(state=NORMAL)
        else:
            self.CBOffSetChoice.current(0)
            print("Error: Invalid Offset Type")
            Mbox("Error: Invalid Offset Type", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)

        # W H
        self.spinValOffSetW.set(w)
        self.spinValOffSetH.set(h)

        if(settings["offSetWH"][0] == "auto"):
            self.checkVarOffSetW.set(True)
            self.spinnerOffSetW.config(state=DISABLED)
        else:
            self.checkVarOffSetW.set(False)
            self.spinnerOffSetW.config(state=NORMAL)

        if(settings["offSetWH"][1] == "auto"):
            self.checkVarOffSetH.set(True)
            self.spinnerOffSetH.config(state=DISABLED)
        else:
            self.checkVarOffSetH.set(False)
            self.spinnerOffSetH.config(state=NORMAL)

        self.CBTLChange_setting()
        self.CBDefaultEngine.current(searchList(settings['default_Engine'], engines))
        self.CBDefaultFrom.current(searchList(settings['default_FromOnOpen'], self.langOpt))
        self.CBDefaultTo.current(searchList(settings['default_ToOnOpen'], self.langOpt))
        self.textBoxTesseractPath.delete(0, END)
        self.textBoxTesseractPath.insert(0, settings['tesseract_loc'])

        globalStuff.main.query_Detached_Window_UI.updateStuff()
        globalStuff.main.result_Detached_Window_UI.updateStuff()
        print("Setting Loaded")
        # No need for mbox

    # Save settings
    def saveSettings(self):
        # Check path tesseract
        tesseractPathInput = self.textBoxTesseractPath.get().strip().lower()
        # Get the exe name or the last / in tesseract path
        tesseractPath = tesseractPathInput.split("/")[-1]
        validTesseract = "tesseract" in tesseractPath.lower()
        # # If tesseract is not found
        if os.path.exists(tesseractPathInput) == False or validTesseract == False:
            print("Tesseract Not Found Error")
            Mbox("Error: Tesseract not found", "Invalid Path Provided For Tesseract.exe!", 2, self.root)
            return

        # Checking each checkbox for the offset of x,y,w,h
        # x
        x = int(self.spinnerOffSetX.get()) if self.checkVarOffSetX.get() == False else "auto"
        y = int(self.spinnerOffSetY.get()) if self.checkVarOffSetY.get() == False else "auto"
        w = int(self.spinnerOffSetW.get()) if self.checkVarOffSetW.get() == False else "auto"
        h = int(self.spinnerOffSetH.get()) if self.checkVarOffSetH.get() == False else "auto"

        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))

        settingToSave = {
            "cached": self.checkVarImgSaved.get(),
            "autoCopy": self.checkVarAutoCopy.get(),
            "offSetXYType": self.CBOffSetChoice.get(),
            "offSetXY": [x, y],
            "offSetWH": [w, h],
            "tesseract_loc": self.textBoxTesseractPath.get().strip(),
            "default_Engine": self.CBDefaultEngine.get(),
            "default_FromOnOpen": self.CBDefaultFrom.get(),
            "default_ToOnOpen": self.CBDefaultTo.get(),
            "capture_Hotkey": self.labelCurrentHotkey['text'],
            "capture_HotkeyDelay": self.spinValHotkeyDelay.get(),
            "Query_Box": {
                "font": {
                    "family": self.queryFontDict['family'],
                    "size": self.queryFontDict['size'],
                    "weight": self.queryFontDict['weight'],
                    "slant": self.queryFontDict['slant'],
                    "underline": self.queryFontDict['underline'],
                    "overstrike": self.queryFontDict['overstrike']
                },
                "bg": self.queryBgVar.get(),
                "fg": self.queryFgVar.get(),
            },
            "Result_Box": {
                "font": {
                    "family": self.resultFontDict['family'],
                    "size": self.resultFontDict['size'],
                    "weight": self.resultFontDict['weight'],
                    "slant": self.resultFontDict['slant'],
                    "underline": self.resultFontDict['underline'],
                    "overstrike": self.resultFontDict['overstrike']
                },
                "bg": self.resultBgVar.get(),
                "fg": self.resultFgVar.get(),
            },
            "saveHistory": self.saveToHistoryVar.get(),
            "checkUpdateOnStart": self.checkUpdateVar.get()
        }

        # Bind hotkey
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            # No hotkeys to unbind
            pass
        if self.labelCurrentHotkey['text'] != '':
            keyboard.add_hotkey(self.labelCurrentHotkey['text'], globalStuff.hotkeyCallback)

        print("-" * 50)
        print("Setting saved!")
        print(settingToSave)

        status, dataStatus = fJson.writeSetting(settingToSave)
        if status:
            print("-" * 50)
            print(dataStatus)
            Mbox("Success", dataStatus, 0, self.root)
        else:
            print("-" * 50)
            print(dataStatus)
            Mbox("Error", dataStatus, 2, self.root)

    # --------------------------------------------------
    # Offset capturing settings
    def checkBtnOffset(self, theSpinner, theSpinVal, theCheckVar, theReturnType):
        """Set the state & value for each spinner

        Args:
            theSpinner ([type]): [The spinner that is to be set]
            theSpinVal ([type]): [The variable that controls the spinner]
            theCheckVar ([type]): [The checkbox variable that controls the spinner]
            theReturnType ([type]): [The type of return value]
        """
        offType = theSpinner.get() if theCheckVar.get() else "auto" 
        offSets = getTheOffset(offType)

        ret = {"x": offSets[0], "y": offSets[1], "w": offSets[2], "h": offSets[3]}

        if theCheckVar.get():
            theSpinner.config(state=DISABLED)
            theSpinVal.set(ret[theReturnType])
        else:
            theSpinner.config(state=NORMAL)

    # ----------------------------------------------------------------
    # Engine
    # Search for tesseract
    def searchTesseract(self):
        self.tesseract_path = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("tesseract.exe", "*.exe"),
        ))
        if self.tesseract_path != "":
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, self.tesseract_path)

    # ----------------------------------------------------------------
    # Hotkey
    def setHotkey(self):
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHotkey.config(text=str(hotkey))

    def clearHotkey(self):
        self.labelCurrentHotkey.config(text="")

    # ----------------------------------------------------------------
    # Capture
    def screenShotAndOpenLayout(self):
        captureAll()

    # ----------------------------------------------------------------
    # CB Settings
    def CBTLChange_setting(self, event = ""):
        # In settings
        # Get the engine from the combobox
        curr_Engine = self.CBDefaultEngine.get()
        previous_From = self.CBDefaultFrom.get()
        previous_To = self.CBDefaultTo.get()

        # Translate
        if curr_Engine == "Google Translate":
            self.langOpt = optGoogle
            self.CBDefaultFrom['values'] = optGoogle
            self.CBDefaultFrom.current(searchList(previous_From, optGoogle))
            self.CBDefaultTo['values'] = optGoogle
            self.CBDefaultTo.current(searchList(previous_To, optGoogle))
            self.CBDefaultTo.config(state='readonly')
        elif curr_Engine == "Deepl":
            self.langOpt = optDeepl
            self.CBDefaultFrom['values'] = optDeepl
            self.CBDefaultFrom.current(searchList(previous_From, optDeepl))
            self.CBDefaultTo['values'] = optDeepl
            self.CBDefaultTo.current(searchList(previous_To, optDeepl))
            self.CBDefaultTo.config(state='readonly')
        elif curr_Engine == "MyMemoryTranslator":
            self.langOpt = optMyMemory
            self.CBDefaultFrom['values'] = optMyMemory
            self.CBDefaultFrom.current(searchList(previous_From, optMyMemory))
            self.CBDefaultTo['values'] = optMyMemory
            self.CBDefaultTo.current(searchList(previous_To, optMyMemory))
            self.CBDefaultTo.config(state='readonly')
        elif curr_Engine == "PONS":
            self.langOpt = optPons
            self.CBDefaultFrom['values'] = optPons
            self.CBDefaultFrom.current(searchList(previous_From, optPons))
            self.CBDefaultTo['values'] = optPons
            self.CBDefaultTo.current(searchList(previous_To, optPons))
            self.CBDefaultTo.config(state='readonly')
        elif curr_Engine == "None":
            self.langOpt = optNone
            self.CBDefaultFrom['values'] = optNone
            self.CBDefaultFrom.current(searchList(previous_From, optNone))
            self.CBDefaultTo['values'] = optNone
            self.CBDefaultTo.current(searchList(previous_To, optNone))
            self.CBDefaultTo.config(state='disabled')

    def CBOffSetChange(self, event = ""):
        offSets = getTheOffset("Custom")
        xyOffSetType = self.CBOffSetChoice.get()

        # Check offset or not
        if xyOffSetType == "No Offset":
            # Select auto
            self.checkVarOffSetX.set(False)
            self.checkVarOffSetY.set(False)
            # Disable spinner and the selector, also set stuff in spinner to 0
            self.checkAutoOffSetX.config(state=DISABLED)
            self.checkAutoOffSetY.config(state=DISABLED)
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetX.set(0)
            self.spinValOffSetY.set(0)
        else:
            # Disselect auto
            self.checkVarOffSetX.set(True)
            self.checkVarOffSetY.set(True)
            # Make checbtn clickable, but set auto which means spin is disabled
            self.checkAutoOffSetX.config(state=NORMAL)
            self.checkAutoOffSetY.config(state=NORMAL)
            self.spinValOffSetX.set(offSets[0])
            self.spinValOffSetY.set(offSets[1])
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinnerOffSetY.config(state=DISABLED)

    # ----------------------------------------------------------------
    # Spinbox validation
    def validateSpinBox_Offset_X(self, event):
        return self.spinboxValidation(event, 'x')

    def validateSpinBox_Offset_Y(self, event):
        return self.spinboxValidation(event, 'y')

    def validateSpinBox_Offset_W(self, event):
        return self.spinboxValidation(event, 'w')
    
    def validateSpinBox_Offset_H(self, event):
        return self.spinboxValidation(event, 'h')

    def validateSpinBox_Delay(self, event):
        if event == "":
            self.spinnerHotkeyDelay.set(0)
            return False

        if event.isdigit():
            # Check value no more than 200
            if int(event) > 100000:
                self.spinnerHotkeyDelay.set(100000)
                return False
            else:
                return event.isdigit()
        else:
            return False

    def spinboxValidation(self, event, type):
        typeDict = {'x': self.spinnerOffSetX, 'y': self.spinnerOffSetY, 'w': self.spinnerOffSetW, 'h': self.spinnerOffSetH}
        typeGet = typeDict[type]

        if event == "":
            typeGet.set(0)
            return False

        try:
            event = int(event)
            # Fetching minimum and maximum value of the spinbox
            minval = int(self.root.nametowidget(typeGet).config('from')[4])
            maxval = int(self.root.nametowidget(typeGet).config('to')[4])

            # check if the number is within the range
            if event not in range(minval, maxval):
                # if not, set the value to the nearest limit
                if event < minval:
                    typeGet.set(minval)
                else:
                    typeGet.set(maxval)
                return False

            # if all is well, return True
            return True
        except: # Except means that number is not a digit
            return False

    # Bg Color chooser
    def bgColorChooser(self, event=None, label=None, theVar=None, destination=None):
        colorGet = colorchooser.askcolor(color=theVar.get(), title="Choose a color")
        if colorGet[1] != None:
            theVar.set(colorGet[1])
            label.config(text="Textbox BG color: " + theVar.get())
            destination.updateStuff()
    
    # Fg Color chooser
    def fgColorChooser(self, event=None, label=None, theVar=None, destination=None):
        colorGet = colorchooser.askcolor(color=theVar.get(), title="Choose a color")
        if colorGet[1] != None:
            theVar.set(colorGet[1])
            label.config(text="Textbox FG color: " + theVar.get())
            destination.updateStuff()

    # Font Chooser
    def fontChooser(self, event=None, label=None, theVar=None, theDict=None, destination=None):
        fontGet = askfont(self.root, title="Choose a font", text="Preview プレビュー معاينة 预览", family=theDict['family'], size=theDict['size'], weight=theDict['weight'], slant=theDict['slant'])
        if fontGet:
            # print(globalStuff.queryFont.get())
            # print(theVar.get())
            theVar.set(fontGet)
            # print(globalStuff.queryFont.get())
            # print(theVar.get())
            theDict = json.loads(theVar.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % theDict
            label.configure(text='Textbox Font : ' + font_str)
            destination.updateStuff()
    
    # Update lbl
    def updateLbl(self):
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        query_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict
        self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
        self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
        self.queryFont.config(text="Textbox Font : " + query_font_str)

        # Result
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        result_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.resultFontDict
        self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
        self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())
        self.resultFont.config(text="Textbox Font : " + result_font_str)