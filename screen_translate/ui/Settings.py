import json
from tkinter import colorchooser
import tkinter.ttk as ttk
import keyboard
from tkinter import *
from tkinter import filedialog

from tkfontchooser import askfont
from screen_translate.Public import CreateToolTip, fJson, _StoredGlobal
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
        self.listboxCat.insert(2, "OCR Engine/Enhance")
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
        self.checkVarAutoCopy = BooleanVar(self.root, value=True) # So its not error

        self.checkBTNAutoCopy = ttk.Checkbutton(self.content_Cap_1, text="Auto Copy Captured Text To Clipboard", variable=self.checkVarAutoCopy)
        self.checkBTNAutoCopy.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkBTNAutoCopy, "Copy the captured text to clipboard automatically")

        self.checkBTNSaved = ttk.Checkbutton(self.content_Cap_1, text="Save Captured Image", variable=self.checkVarImgSaved)
        self.checkBTNSaved.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkBTNSaved, "Save the captured image to img_captured folder")

        self.btnOpenImgFolder = ttk.Button(self.content_Cap_1, text="Open Captured Image Folder", command=lambda: startfile(dir_path + r"\..\..\img_captured"))
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
        CreateToolTip(self.labelCBOffsetNot, "The offset mode")

        self.CBOffSetChoice = ttk.Combobox(self.content_Cap_2_1, values=["No Offset", "Custom Offset"], state="readonly")
        self.CBOffSetChoice.pack(side=LEFT, padx=5, pady=5)
        self.CBOffSetChoice.bind("<<ComboboxSelected>>", self.CBOffSetChange)

        self.buttonCheckMonitorLayout = ttk.Button(self.content_Cap_2_1, text="Click to get A Screenshot of How The Program See Your Monitor", command=self.screenShotAndOpenLayout)
        self.buttonCheckMonitorLayout.pack(side=LEFT, padx=5, pady=5)

        self.hintLabelOffset = Label(self.content_Cap_2_1, text="❓")
        self.hintLabelOffset.pack(side=RIGHT, padx=5, pady=5)
        CreateToolTip(self.hintLabelOffset, "Set the offset for capturing image. Usually needed if on multiple monitor or if monitor scaling is not 100%")

        self.checkVarOffSetX = BooleanVar(self.root, value=True)
        self.checkVarOffSetY = BooleanVar(self.root, value=True)
        self.checkVarOffSetW = BooleanVar(self.root, value=True)
        self.checkVarOffSetH = BooleanVar(self.root, value=True)

        self.checkAutoOffSetX = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset X", variable=self.checkVarOffSetX, command=lambda: self.checkBtnOffset(self.spinnerOffSetX, self.spinValOffSetX, self.checkVarOffSetX, "x"))
        self.checkAutoOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetY = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset Y", variable=self.checkVarOffSetY, command=lambda: self.checkBtnOffset(self.spinnerOffSetY, self.spinValOffSetY, self.checkVarOffSetY, "y"))
        self.checkAutoOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetW = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset W", variable=self.checkVarOffSetW, command=lambda: self.checkBtnOffset(self.spinnerOffSetW, self.spinValOffSetW, self.checkVarOffSetW, "w"))
        self.checkAutoOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetH = ttk.Checkbutton(self.content_Cap_2_2, text="Auto Offset H", variable=self.checkVarOffSetH, command=lambda: self.checkBtnOffset(self.spinnerOffSetH, self.spinValOffSetH, self.checkVarOffSetH, "h"))
        self.checkAutoOffSetH.pack(side=LEFT, padx=5, pady=5)

        self.spinValOffSetX = IntVar(self.root)
        self.spinValOffSetY = IntVar(self.root)
        self.spinValOffSetW = IntVar(self.root)
        self.spinValOffSetH = IntVar(self.root)

        self.labelOffSetX = Label(self.content_Cap_2_3, text="Offset X :")
        self.labelOffSetX.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelOffSetX, "The X Coordinates offset of the capture window")

        self.spinnerOffSetX = ttk.Spinbox(self.content_Cap_2_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetX)
        self.spinnerOffSetX.pack(side=LEFT, padx=5, pady=5)

        self.validateDigits_Offset_X = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerOffSetX)), '%P')
        self.spinnerOffSetX.configure(validate='key', validatecommand=self.validateDigits_Offset_X)
        self.spinnerOffSetX.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetX))

        self.labelOffSetY = Label(self.content_Cap_2_4, text="Offset Y :")
        self.labelOffSetY.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelOffSetY, "Y Coordinates offset of the capture window")

        self.spinnerOffSetY = ttk.Spinbox(self.content_Cap_2_4, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetY)
        self.spinnerOffSetY.pack(side=LEFT, padx=5, pady=5)

        self.validateDigits_Offset_Y = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerOffSetY)), '%P')
        self.spinnerOffSetY.configure(validate='key', validatecommand=self.validateDigits_Offset_Y)
        self.spinnerOffSetY.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetY))

        self.labelOffSetW = Label(self.content_Cap_2_3, text="Offset W :")
        self.labelOffSetW.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelOffSetW, "Width offset of the capture window")

        self.spinnerOffSetW = ttk.Spinbox(self.content_Cap_2_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetW)
        self.spinnerOffSetW.pack(side=LEFT, padx=5, pady=5)

        self.validateDigits_Offset_W = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerOffSetW)), '%P')
        self.spinnerOffSetW.configure(validate='key', validatecommand=self.validateDigits_Offset_W)
        self.spinnerOffSetW.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, self.spinnerOffSetW))

        self.labelOffSetH = Label(self.content_Cap_2_4, text="Offset H :")
        self.labelOffSetH.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelOffSetH, "Height offset of the capture window")

        self.spinnerOffSetH = ttk.Spinbox(self.content_Cap_2_4, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetH)
        self.spinnerOffSetH.pack(side=LEFT, padx=8, pady=5)

        self.validateDigits_Offset_H = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerOffSetH)), '%P')
        self.spinnerOffSetH.configure(validate='key', validatecommand=self.validateDigits_Offset_H)
        self.spinnerOffSetH.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerOffSetH))

        # [Snippet offset]
        self.fLabelSnippet = LabelFrame(self.frameCapture, text="• Monitor Snippet Offset", width=750, height=55)
        self.fLabelSnippet.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fLabelSnippet.pack_propagate(0)

        self.content_Snippet_3_1 = Frame(self.fLabelSnippet)
        self.content_Snippet_3_1.pack(side=TOP, fill=X, expand=False)

        self.checkAutoSnippetVar = BooleanVar(self.root, value=True)

        self.checkAutoSnippet = ttk.Checkbutton(self.content_Snippet_3_1, text="Auto", 
                            variable=self.checkAutoSnippetVar, command=self.disableEnableSnipSpin)
        self.checkAutoSnippet.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkAutoSnippet, text="Auto detect the layout of the monitor (May not work properly)")
        
        self.labelSnippet_1 = Label(self.content_Snippet_3_1, text="Total Width:")
        self.labelSnippet_1.pack(side=LEFT, padx=(0,5), pady=0)
        CreateToolTip(self.labelSnippet_1, "Total width of the monitor")

        self.spinValSnippet_1 = IntVar(self.root)
        self.spinnerSnippet_1 = ttk.Spinbox(self.content_Snippet_3_1, from_=-100000, to=100000, width=7, textvariable=self.spinValSnippet_1)

        self.validateDigits_Snippet_1 = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerSnippet_1)), '%P')
        self.spinnerSnippet_1.configure(validate='key', validatecommand=self.validateDigits_Snippet_1)
        self.spinnerSnippet_1.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerSnippet_1))
        
        self.spinnerSnippet_1.pack(side=LEFT, padx=0, pady=(3,0))
        CreateToolTip(self.spinnerSnippet_1, "Total width of the monitor")

        self.labelSnippet_2 = Label(self.content_Snippet_3_1, text="Total Height:")
        self.labelSnippet_2.pack(side=LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.labelSnippet_2, "Total height of the monitor")

        self.spinValSnippet_2 = IntVar(self.root)
        self.spinnerSnippet_2 = ttk.Spinbox(self.content_Snippet_3_1, from_=-100000, to=100000, width=7, textvariable=self.spinValSnippet_2)

        self.validateDigits_Snippet_2 = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerSnippet_2)), '%P')
        self.spinnerSnippet_2.configure(validate='key', validatecommand=self.validateDigits_Snippet_2)
        self.spinnerSnippet_2.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerSnippet_2))
        
        self.spinnerSnippet_2.pack(side=LEFT, padx=0, pady=(3,0))
        CreateToolTip(self.spinnerSnippet_2, "Total height of the monitor")

        self.labelSnippet_3 = Label(self.content_Snippet_3_1, text="X Offset From Primary:")
        self.labelSnippet_3.pack(side=LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.labelSnippet_3, "X offset of the monitor from the primary monitor")

        self.spinValSnippet_3 = IntVar(self.root)
        self.spinnerSnippet_3 = ttk.Spinbox(self.content_Snippet_3_1, from_=-100000, to=100000, width=7, textvariable=self.spinValSnippet_3)

        self.validateDigits_Snippet_3 = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerSnippet_3)), '%P')
        self.spinnerSnippet_3.configure(validate='key', validatecommand=self.validateDigits_Snippet_3)
        self.spinnerSnippet_3.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerSnippet_3))
        
        self.spinnerSnippet_3.pack(side=LEFT, padx=0, pady=(3,0))
        CreateToolTip(self.spinnerSnippet_3, "X offset of the monitor from the primary monitor")

        self.labelSnippet_4 = Label(self.content_Snippet_3_1, text="Y Offset From Primary:")
        self.labelSnippet_4.pack(side=LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.labelSnippet_4, "Y offset of the monitor from the primary monitor")

        self.spinValSnippet_4 = IntVar(self.root)
        self.spinnerSnippet_4 = ttk.Spinbox(self.content_Snippet_3_1, from_=-100000, to=100000, width=7, textvariable=self.spinValSnippet_4)

        self.validateDigits_Snippet_4 = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerSnippet_4)), '%P')
        self.spinnerSnippet_4.configure(validate='key', validatecommand=self.validateDigits_Snippet_4)
        self.spinnerSnippet_4.bind("<MouseWheel>", lambda event: self.disableScrollWheel(event, theSpinner=self.spinnerSnippet_4))
        
        self.spinnerSnippet_4.pack(side=LEFT, padx=0, pady=(3,0))
        CreateToolTip(self.spinnerSnippet_4, "Y offset of the monitor from the primary monitor")
        
        self.hintLabelSnippet = Label(self.content_Snippet_3_1, text="❓")
        self.hintLabelSnippet.pack(side=RIGHT, padx=5, pady=5)
        CreateToolTip(self.hintLabelSnippet, 
        text="""If the snipping does not match the monitor, then you can manually set the height, width, and offsets.
        \rIf the offset is negative then you need to input (-) before it, if it's positive just leave it as normal
        \rTo get the offset, you need to identify your primary monitor position then you can calculate it by seeing wether the primary monitor is on the first position, in the top, in the middle, or etc.
        \rIf it is in the first position then you might not need any offset, if it's on the second from the left then you might need to add minus offset, etc.""")

        # ----------------------------------------------------------------------
        # OCR Engine
        self.frameOCREngine = Frame(self.mainFrameTop)
        self.frameOCREngine.pack(side=LEFT, fill=BOTH, padx=5, pady=5)

        self.fLabelOCR_1 = LabelFrame(self.frameOCREngine, text="• Tesseract OCR Settings", width=750, height=55)
        self.fLabelOCR_1.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelOCR_1.pack_propagate(0)
        self.content_Engine_1 = Frame(self.fLabelOCR_1)
        self.content_Engine_1.pack(side=TOP, fill=X, expand=False)

        self.labelTesseractPath = Label(self.content_Engine_1, text="Tesseract Path :")
        self.labelTesseractPath.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.content_Engine_1, "Tesseract.exe location")

        self.textBoxTesseractPath = ttk.Entry(self.content_Engine_1, width=70, xscrollcommand=True)
        self.textBoxTesseractPath.bind("<Key>", lambda event: _StoredGlobal.allowedKey(event)) # Disable textbox input
        self.textBoxTesseractPath.pack(side=LEFT, padx=5, pady=5, fill=X, expand=True)
        CreateToolTip(self.textBoxTesseractPath, "Tesseract.exe location")

        self.btnSearchTesseract = ttk.Button(self.content_Engine_1, text="...", command=self.searchTesseract)
        self.btnSearchTesseract.pack(side=LEFT, padx=5, pady=5)

        # [Ocr enhancement]
        self.fLabelOCR_2 = LabelFrame(self.frameOCREngine, text="• OCR Enhancement", width=750, height=55)
        self.fLabelOCR_2.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fLabelOCR_2.pack_propagate(0)

        self.content_Cap_3_1 = Frame(self.fLabelOCR_2)
        self.content_Cap_3_1.pack(side=TOP, fill=X, expand=False)

        self.checkVarCV2 = BooleanVar(self.root, value=True)
        self.checkVarGrayscale = BooleanVar(self.root, value=False)
        self.checkVarDebugmode = BooleanVar(self.root, value=False)

        self.labelCBBackground = Label(self.content_Cap_3_1, text="Background :")
        self.labelCBBackground.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelCBBackground, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.CBBackgroundType = ttk.Combobox(self.content_Cap_3_1, values=["Auto-Detect", 'Light', 'Dark'], state="readonly")
        self.CBBackgroundType.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.CBBackgroundType, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.checkCV2 = ttk.Checkbutton(self.content_Cap_3_1, text="Detect Contour using CV2", variable=self.checkVarCV2)
        self.checkCV2.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkCV2, text="Enhance the OCR by applying filters and outlining the contour of the words.")

        self.checkGrayscale = ttk.Checkbutton(self.content_Cap_3_1, text="Grayscale", variable=self.checkVarGrayscale)
        self.checkGrayscale.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkGrayscale, text="Enhance the OCR by making the captured picture grayscale on the character reading part.")

        self.checkDebugmode = ttk.Checkbutton(self.content_Cap_3_1, text="Debug Mode", variable=self.checkVarDebugmode)
        self.checkDebugmode.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkDebugmode, text="Enable debug mode.")
        
        self.hintLabelEnhance = Label(self.content_Cap_3_1, text="❓")
        self.hintLabelEnhance.pack(side=RIGHT, padx=5, pady=5)
        CreateToolTip(self.hintLabelEnhance, 
        text="""Options saved in this section are for the inital value on startup.
        \rYou can experiment with the option to increase the accuracy of tesseract OCR.
        \rThe saved picture will not be affected by the options.""")

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
        CreateToolTip(self.labelDefaultEngine, text="The default translation engine on program startup")

        self.CBDefaultEngine = ttk.Combobox(self.content_Tl_1, values=engines, state="readonly")
        self.CBDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.bind("<<ComboboxSelected>>", self.CBTLChange_setting)

        self.labelDefaultFrom = Label(self.content_Tl_1, text="Default From :")
        self.labelDefaultFrom.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelDefaultFrom, text="The default language to translate from on program startup")

        self.CBDefaultFrom = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelDefaultTo = Label(self.content_Tl_1, text="Default To :")
        self.labelDefaultTo.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelDefaultTo, text="The default language to translate to on program startup")

        self.CBDefaultTo = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultTo.pack(side=LEFT, padx=5, pady=5)

        self.saveToHistoryVar = BooleanVar(self.root, value=True)
        self.checkSaveToHistory = ttk.Checkbutton(self.content_Tl_2, variable=self.saveToHistoryVar, text="Save to History")
        self.checkSaveToHistory.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkSaveToHistory, text="Save the translation to history")

        self.showNoTextAlertVar = BooleanVar(self.root, value=True)
        self.checkShowNoTextAlert = ttk.Checkbutton(self.content_Tl_2, variable=self.showNoTextAlertVar, text="Show No Text Entered Alert")
        self.checkShowNoTextAlert.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.checkShowNoTextAlert, text="Show alert when no text is entered")

        # ----------------------------------------------------------------------
        # Hotkey
        self.frameHotkey = Frame(self.mainFrameTop)
        self.frameHotkey.pack(side=LEFT, fill=BOTH, padx=5, pady=5)
        
        self.fLabelHKCapTl = LabelFrame(self.frameHotkey, text="• Capture Hotkey Settings", width=750, height=55)
        self.fLabelHKCapTl.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelHKCapTl.pack_propagate(0)
        self.content_HKCapTl = Frame(self.fLabelHKCapTl)
        self.content_HKCapTl.pack(side=TOP, fill=X, expand=False)

        self.spinValHKCapTl = IntVar(self.root)

        self.labelHkCapTl = Label(self.content_HKCapTl, text="Time delay (ms) : ")
        self.labelHkCapTl.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHkCapTl, text="The time delay to capture when the hotkey is pressed")
        
        self.spinnerHKCapTlDelay = ttk.Spinbox(self.content_HKCapTl, from_=0, to=100000, width=20, textvariable=self.spinValHKCapTl)
        self.validateDigits_Delay = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerHKCapTlDelay)), '%P')
        self.spinnerHKCapTlDelay.configure(validate='key', validatecommand=self.validateDigits_Delay)
        self.spinnerHKCapTlDelay.pack(side=LEFT, padx=5, pady=5)
        
        self.buttonSetHKCapTl = ttk.Button(self.content_HKCapTl, text="Click to set the hotkey", command=self.setHKCapTl)
        self.buttonSetHKCapTl.pack(side=LEFT, padx=5, pady=5)
        
        self.buttonClearHKCapTl = ttk.Button(self.content_HKCapTl, text="Clear", command=self.clearHKCapTl)
        self.buttonClearHKCapTl.pack(side=LEFT, padx=5, pady=5)
        
        self.labelHKCapTl = Label(self.content_HKCapTl, text="Current hotkey : ")
        self.labelHKCapTl.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHKCapTl, text="Currently set hotkey for capturing")

        self.labelCurrentHKCapTl = Label(self.content_HKCapTl, text="")
        self.labelCurrentHKCapTl.pack(side=LEFT, padx=5, pady=5)


        # Snip and cap
        self.fLabelHKSnipCapTl = LabelFrame(self.frameHotkey, text="• Snip & Capture Hotkey Settings", width=750, height=55)
        self.fLabelHKSnipCapTl.pack(side=TOP, fill=X, expand=False, padx=5, pady=(0, 5))
        self.fLabelHKSnipCapTl.pack_propagate(0)
        self.content_HKSnipCapTl = Frame(self.fLabelHKSnipCapTl)
        self.content_HKSnipCapTl.pack(side=TOP, fill=X, expand=False)

        self.spinValHKSnipCapTl = IntVar(self.root)

        self.labelHkSnipCapTl = Label(self.content_HKSnipCapTl, text="Time delay (ms) : ")
        self.labelHkSnipCapTl.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHkCapTl, text="The time delay to activate snipping mode when the hotkey is pressed")
        
        self.spinnerHKSnipCapTlDelay = ttk.Spinbox(self.content_HKSnipCapTl, from_=0, to=100000, width=20, textvariable=self.spinValHKSnipCapTl)
        self.validateDigits_DelaySnip = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerHKSnipCapTlDelay)), '%P')
        self.spinnerHKSnipCapTlDelay.configure(validate='key', validatecommand=self.validateDigits_DelaySnip)
        self.spinnerHKSnipCapTlDelay.pack(side=LEFT, padx=5, pady=5)

        self.buttonHKSnipCapTl = ttk.Button(self.content_HKSnipCapTl, text="Click to set the hotkey", command=self.setHKSnipCapTl)
        self.buttonHKSnipCapTl.pack(side=LEFT, padx=5, pady=5)
        
        self.buttonClearHKSnipCapTl = ttk.Button(self.content_HKSnipCapTl, text="Clear", command=self.clearHKSnipCapTl)
        self.buttonClearHKSnipCapTl.pack(side=LEFT, padx=5, pady=5)
        
        self.labelHKSnipCapTl = Label(self.content_HKSnipCapTl, text="Current hotkey : ")
        self.labelHKSnipCapTl.pack(side=LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHKSnipCapTl, text="Currently set hotkey for snip & capture")

        self.labelCurrentHKSnipCapTl = Label(self.content_HKSnipCapTl, text="")
        self.labelCurrentHKSnipCapTl.pack(side=LEFT, padx=5, pady=5)

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

        self.queryBgVar = _StoredGlobal.queryBg
        self.queryBg = Label(self.fQueryContent_1, text="Textbox Bg Color : ")
        self.queryBg.pack(side=LEFT, padx=5, pady=5)
        self.queryBg.bind("<Button-1>", lambda event: self.bgColorChooser(label=self.queryBg, 
        theVar=self.queryBgVar, destination=_StoredGlobal.main.query_Detached_Window_UI))
        CreateToolTip(self.queryBg, "Click to choose query textbox background color")

        self.hintLabelQuery = Label(self.fQueryContent_1, text="❓")
        self.hintLabelQuery.pack(padx=5, pady=5, side=RIGHT)
        CreateToolTip(self.hintLabelQuery, "Click on the label to change the value of the settings")

        self.queryFgVar = _StoredGlobal.queryFg
        self.queryFg = Label(self.fQueryContent_2, text="Textbox Fg Color : ")
        self.queryFg.pack(side=LEFT, padx=5, pady=5)
        self.queryFg.bind("<Button-1>", lambda event: self.fgColorChooser(label=self.queryFg,
        theVar=self.queryFgVar, destination=_StoredGlobal.main.query_Detached_Window_UI))
        CreateToolTip(self.queryFg, "Click to choose query textbox foreground color")

        self.queryFontVar = _StoredGlobal.queryFont
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.queryFont = Label(self.fQueryContent_3, text="Textbox Font : ")
        self.queryFont.pack(side=LEFT, padx=5, pady=5)
        self.queryFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.queryFont,
        theVar=self.queryFontVar, theDict=self.queryFontDict, destination=_StoredGlobal.main.query_Detached_Window_UI))
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

        self.resultBgVar = _StoredGlobal.resultBg
        self.resultBg = Label(self.fResultContent_1, text="Textbox Bg Color : ")
        self.resultBg.pack(side=LEFT, padx=5, pady=5)
        self.resultBg.bind("<Button-1>", lambda event: self.bgColorChooser(label=self.resultBg,
        theVar=self.resultBgVar, destination=_StoredGlobal.main.result_Detached_Window_UI))
        CreateToolTip(self.resultBg, "Click to choose result textbox background color")

        self.hintLabelResult = Label(self.fResultContent_1, text="❓")
        self.hintLabelResult.pack(padx=5, pady=5, side=RIGHT)
        CreateToolTip(self.hintLabelResult, "Click on the label to change the value of the settings")

        self.resultFgVar = _StoredGlobal.resultFg
        self.resultFg = Label(self.fResultContent_2, text="Textbox Fg Color : ")
        self.resultFg.pack(side=LEFT, padx=5, pady=5)
        self.resultFg.bind("<Button-1>", lambda event: self.fgColorChooser(label=self.resultFg,
        theVar=self.resultFgVar, destination=_StoredGlobal.main.result_Detached_Window_UI))
        CreateToolTip(self.resultFg, "Click to choose result textbox foreground color")

        self.resultFontVar = _StoredGlobal.resultFont
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        self.resultFont = Label(self.fResultContent_3, text="Textbox Font : ")
        self.resultFont.pack(side=LEFT, padx=5, pady=5)
        self.resultFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.resultFont,
        theVar=self.resultFontVar, theDict=self.resultFontDict, destination=_StoredGlobal.main.result_Detached_Window_UI))
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
        CreateToolTip(self.checkUpdateBox, "Check for update on app start. You can also check manually by going to help in menubar")

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
        if str(theSpinner["state"]) == "disabled":
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
                self.showFrame(self.frameOCREngine)
            
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
        self.frameOCREngine.pack_forget()
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
            return

        # Restore Default Settings
        tStatus, settings = fJson.setDefault()
        if tStatus == True:
            # Unbind all hotkeys
            try:
                keyboard.unhook_all_hotkeys()
            except AttributeError:
                # No hotkeys to unbind
                pass
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
        except Exception:
            print("Error: Invalid Image Saving Options")
            Mbox("Error: Invalid Image Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarImgSaved.set(True)

        # Autocopy checkbox
        try:
            self.checkVarAutoCopy.set(settings['autoCopy'])
        except Exception:
            print("Error: Invalid Autocopy Options")
            Mbox("Error: Invalid Autocopy Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarAutoCopy.set(True)

        # Save to history checkbox
        try:
            self.saveToHistoryVar.set(settings['saveHistory'])
        except Exception:
            print("Error: Invalid History Saving Options")
            Mbox("Error: Invalid History Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.saveToHistoryVar.set(True)

        # Show no text alert checkbox
        try:
            self.showNoTextAlertVar.set(settings['show_no_text_alert'])
        except Exception:
            print("Error: Invalid Show No Text Alert Options")
            Mbox("Error: Invalid Show No Text Alert Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.showNoTextAlertVar.set(False)

        # Check for update checkbox
        try:
            self.checkUpdateVar.set(settings['checkUpdateOnStart'])
        except Exception:
            print("Error: Invalid Update Checking Options")
            Mbox("Error: Invalid Update Checking Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkUpdateVar.set(True)

        # Check for cv2 checkbox
        try:
            self.checkVarCV2.set(settings['enhance_Capture']['cv2_Contour'])
        except Exception:
            print("Error: Invalid OpenCV Options")
            Mbox("Error: Invalid OpenCV Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarCv2.set(True)

        # Check for grayscale
        try:
            self.checkVarGrayscale.set(settings['enhance_Capture']['grayscale'])
        except Exception:
            print("Error: Invalid Grayscale Options")
            Mbox("Error: Invalid Grayscale Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarGrayscale.set(True)

        # Check for debug
        try:
            self.checkVarDebugmode.set(settings['enhance_Capture']['debugmode'])
        except Exception:
            print("Error: Invalid Debug Options")
            Mbox("Error: Invalid Debug Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarDebugmode.set(False)

        # Check for snip offset
        try:
            if settings['snippingWindowGeometry'] == "auto":
                self.checkAutoSnippetVar.set(True)
                geometryStr = _StoredGlobal.main.snipper_UI.getScreenTotalGeometry()
            else:
                self.checkAutoSnippetVar.set(False)
                geometryStr = settings['snippingWindowGeometry']
            newStr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in geometryStr)
            geometryNum = [int(i) for i in newStr.split()]
            self.spinnerSnippet_1.set(geometryNum[0])
            self.spinnerSnippet_2.set(geometryNum[1])
            self.spinnerSnippet_3.set(geometryNum[2])
            self.spinnerSnippet_4.set(geometryNum[3])
        except Exception:
            print("Error: Invalid Snip Offset Options")
            Mbox("Error: Invalid Snip Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkAutoSnippetVar.set(True)

        # Update the spinner offset
        self.disableEnableSnipSpin()

        # Check for cb background
        try:
            self.CBBackgroundType.current(searchList(settings['enhance_Capture']['background'], ["Auto-Detect", "Light", "Dark"]))
        except Exception:
            print("Error: Invalid Background Options")
            Mbox("Error: Invalid Background Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.CBBackgroundType.current(0)
        
        # Set label value for query and result box
        # Query
        try:
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
        except Exception:
            print("Error: Invalid Font Options")
            Mbox("Error: Invalid Font Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.queryFontVar.set("{'family': 'Segoe UI', 'size': 10, 'weight': 'normal', 'slant': 'roman'}")
            self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
            self.queryBgVar.set("#ffffff")
            self.queryFgVar.set("#000000")
            self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
            self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
            self.queryFont.config(text="Textbox Font : " + "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict)

            # Result
            self.resultFontVar.set("{'family': 'Segoe UI', 'size': 10, 'weight': 'normal', 'slant': 'roman'}")
            self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
            self.resultBgVar.set("#ffffff")
            self.resultFgVar.set("#000000")
            self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
            self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())

        # Show current hotkey
        try:
            self.labelCurrentHKCapTl.config(text=settings['hotkey']['captureAndTl']['hk'])
            self.spinValHKCapTl.set(settings['hotkey']['captureAndTl']['delay'])

            self.labelCurrentHKSnipCapTl.config(text=settings['hotkey']['snipAndCapTl']['hk'])
            self.spinValHKSnipCapTl.set(settings['hotkey']['snipAndCapTl']['delay'])
        except KeyError:
            print("Error: Invalid Hotkey Options")

        # Store setting to localvar
        try:
            offSetXY = settings["offSetXY"]
            xyOffSetType = settings["offSetXYType"]
        except Exception:
            print("Error: Invalid Offset Options")
            Mbox("Error: Invalid Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            offSetXY = [0, 0]
            xyOffSetType = "No Offset"

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

        try:
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
        except Exception:
            print("Error: Invalid Offset Options")
            Mbox("Error: Invalid Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarOffSetW.set(False)
            self.checkVarOffSetH.set(False)

        self.CBTLChange_setting()
        try:
            self.CBDefaultEngine.current(searchList(settings['default_Engine'], engines))
            self.CBDefaultFrom.current(searchList(settings['default_FromOnOpen'], self.langOpt))
            self.CBDefaultTo.current(searchList(settings['default_ToOnOpen'], self.langOpt))
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, settings['tesseract_loc'])
        except Exception:
            print("Error: Invalid Engine Options")
            Mbox("Error: Invalid Engine Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.CBDefaultEngine.current(0)
            self.CBDefaultFrom.current(0)
            self.CBDefaultTo.current(0)
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, "C:/Program Files/Tesseract-OCR/tesseract.exe")

        _StoredGlobal.main.query_Detached_Window_UI.updateStuff()
        _StoredGlobal.main.result_Detached_Window_UI.updateStuff()
        print("Setting Loaded")
        # No need for mbox

    # Save settings
    def saveSettings(self):
        """
        Save settings to file
        """
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

        if self.checkAutoSnippetVar.get():
            snippingWindowGeometry = "auto"
        else:
            snippingWindowGeometry = f"{self.spinnerSnippet_1.get()}x{self.spinnerSnippet_2.get()}+{self.spinnerSnippet_3.get()}+{self.spinnerSnippet_4.get()}"

        settingToSave = {
            "cached": self.checkVarImgSaved.get(),
            "autoCopy": self.checkVarAutoCopy.get(),
            "offSetXYType": self.CBOffSetChoice.get(),
            "offSetXY": [x, y],
            "offSetWH": [w, h],
            "snippingWindowGeometry": snippingWindowGeometry,
            "tesseract_loc": self.textBoxTesseractPath.get().strip(),
            "default_Engine": self.CBDefaultEngine.get(),
            "default_FromOnOpen": self.CBDefaultFrom.get(),
            "default_ToOnOpen": self.CBDefaultTo.get(),
            "hotkey": {
                "captureAndTl": {
                    "hk": self.labelCurrentHKCapTl['text'],
                    "delay": self.spinValHKCapTl.get()
                },
                "snipAndCapTl": {
                    "hk": self.labelCurrentHKSnipCapTl['text'],
                    "delay": self.spinValHKSnipCapTl.get()
                },
            },
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
            "checkUpdateOnStart": self.checkUpdateVar.get(),
            "enhance_Capture" : {
                "cv2_Contour": self.checkVarCV2.get(),
                "grayscale": self.checkVarGrayscale.get(),
                "background": self.CBBackgroundType.get(),
                "debugmode": self.checkVarDebugmode.get()
            },
            "show_no_text_alert": self.showNoTextAlertVar.get()
        }

        # Unbind all hotkey
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            # No hotkeys to unbind
            pass
        # Bind hotkey
        if self.labelCurrentHKCapTl['text'] != '':
            keyboard.add_hotkey(self.labelCurrentHKCapTl['text'], _StoredGlobal.hotkeyCapTLCallback)

        if self.labelCurrentHKSnipCapTl['text'] != '':
            keyboard.add_hotkey(self.labelCurrentHKSnipCapTl['text'], _StoredGlobal.hotkeySnipCapTLCallback)

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
            theSpinner : [The spinner that is to be set]
            theSpinVal : [The variable that controls the spinner]
            theCheckVar : [The checkbox variable that controls the spinner]
            theReturnType : [The type of return value]
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
        """
        Search for tesseract by opening a file dialog
        """
        self.tesseract_path = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("tesseract.exe", "*.exe"),
        ))
        if self.tesseract_path != "":
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, self.tesseract_path)

    # ----------------------------------------------------------------
    # Hotkey
    def setHKCapTl(self):
        """
        Set the hotkey for capturing and translating
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHKCapTl.config(text=str(hotkey))

    def clearHKCapTl(self):
        """
        Clear the hotkey for capturing and translating
        """
        self.labelCurrentHKCapTl.config(text="")

    def setHKSnipCapTl(self):
        """
        Set the hotkey for snipping and translate
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHKSnipCapTl.config(text=str(hotkey))

    def clearHKSnipCapTl(self):
        """
        Clear the hotkey for snipping and translate
        """
        self.labelCurrentHKSnipCapTl.config(text="")

    # ----------------------------------------------------------------
    # Capture
    def screenShotAndOpenLayout(self):
        """
        Fully capture the window and open the image
        """
        captureAll()

    # ----------------------------------------------------------------
    # CB Settings
    def CBTLChange_setting(self, event = None):
        """Change the state of the CB when the default engine is changed

        Args:
            event: Ignored. Defaults to None
        """
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

    def CBOffSetChange(self, event = None):
        """Change the state of the CB when the default engine is changed

        Args:
            event: Ignored. Defaults to None.
        """
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
    def validateSpinbox(self, event, theSpinner):
        """Validate the spinbox

        Args:
            event: spinbox event
            theSpinner: the spinbox

        Returns:
            allowing the spinbox to be changed or not
        """
        if event == "":
            theSpinner.set(0)
            return False

        try:
            event = int(event)
            # Fetching minimum and maximum value of the spinbox
            minval = int(self.root.nametowidget(theSpinner).config('from')[4])
            maxval = int(self.root.nametowidget(theSpinner).config('to')[4])

            # check if the number is within the range
            if event not in range(minval, maxval):
                # if not, set the value to the nearest limit
                if event < minval:
                    theSpinner.set(minval)
                else:
                    theSpinner.set(maxval)
                return False

            # if all is well, return True
            return True
        except Exception: # Except means that number is not a digit
            return False

    # Bg Color chooser
    def bgColorChooser(self, event=None, label=None, theVar=None, destination=None):
        """Bg color chooser

        Args:
            event : Ignored. Defaults to None.
            label : The targeted label object. Defaults to None.
            theVar : The targeted var object. Defaults to None.
            destination : The targeted destination object, destination targeted is a UI window. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=theVar.get(), title="Choose a color")
        if colorGet[1] != None:
            theVar.set(colorGet[1])
            label.config(text="Textbox BG color: " + theVar.get())
            destination.updateStuff()
    
    # Fg Color chooser
    def fgColorChooser(self, event=None, label=None, theVar=None, destination=None):
        """Fg color chooser

        Args:
            event : Ignored. Defaults to None.
            label : The targeted label object. Defaults to None.
            theVar : The targeted var object. Defaults to None.
            destination : The targeted destination object, destination targeted is a UI window. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=theVar.get(), title="Choose a color")
        if colorGet[1] != None:
            theVar.set(colorGet[1])
            label.config(text="Textbox FG color: " + theVar.get())
            destination.updateStuff()

    # Font Chooser
    def fontChooser(self, event=None, label=None, theVar=None, theDict=None, destination=None):
        """Font chooser

        Args:
            event : Ignored. Defaults to None.
            label : The targeted label object. Defaults to None.
            theVar : The targeted var object. Defaults to None.
            destination : The targeted destination object, destination targeted is a UI window. Defaults to None.
        """
        fontGet = askfont(self.root, title="Choose a font", text="Preview プレビュー معاينة 预览", family=theDict['family'], size=theDict['size'], weight=theDict['weight'], slant=theDict['slant'])
        if fontGet:
            theVar.set(fontGet)
            theDict = json.loads(theVar.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % theDict
            label.configure(text='Textbox Font : ' + font_str)
            destination.updateStuff()
    
    # Update lbl
    def updateLbl(self):
        """
        Update the UI Font lbl
        """
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

    def disableEnableSnipSpin(self, event=None):
        """Disable/Enable the snip spinbox

        Args:
            event : Ignored. Defaults to None.
        """
        if not self.checkAutoSnippetVar.get(): # IF disabled then enable it
            self.spinnerSnippet_1.config(state=NORMAL)
            self.spinnerSnippet_2.config(state=NORMAL)
            self.spinnerSnippet_3.config(state=NORMAL)
            self.spinnerSnippet_4.config(state=NORMAL)
        else:
            self.spinnerSnippet_1.config(state=DISABLED)
            self.spinnerSnippet_2.config(state=DISABLED)
            self.spinnerSnippet_3.config(state=DISABLED)
            self.spinnerSnippet_4.config(state=DISABLED)
            geometryStr = _StoredGlobal.main.snipper_UI.getScreenTotalGeometry()
            newStr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in geometryStr)
            geometryNum = [int(i) for i in newStr.split()]
            self.spinnerSnippet_1.set(geometryNum[0])
            self.spinnerSnippet_2.set(geometryNum[1])
            self.spinnerSnippet_3.set(geometryNum[2])
            self.spinnerSnippet_4.set(geometryNum[3])