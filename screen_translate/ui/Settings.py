import tkinter.ttk as ttk
import keyboard
from tkinter import *
from tkinter import filedialog
from ..Public import fJson, globalStuff
from ..Public import startfile, optGoogle, optDeepl, optMyMemory, optPons, optNone, engines, getTheOffset, offSetSettings, searchList
from ..Mbox import Mbox
from ..Capture import captureAll
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
        self.root.geometry("727x500") # When you see it
        self.root.wm_attributes('-topmost', False) # Default False
        self.root.wm_withdraw()

        # Frames

        self.firstFrame = LabelFrame(self.root, text="• Image / OCR Setting")
        self.firstFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.firstFrameContent = Frame(self.firstFrame)
        self.firstFrameContent.pack(side=TOP, fill=X, expand=False)

        self.secondFrame = LabelFrame(self.root, text="• Monitor Capture Offset")
        self.secondFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.secondFrameContent_0 = Frame(self.secondFrame)
        self.secondFrameContent_0.pack(side=TOP, fill=X, expand=False)
        self.secondFrameContent_1 = Frame(self.secondFrame)
        self.secondFrameContent_1.pack(side=TOP, fill=X, expand=False)
        self.secondFrameContent_2 = Frame(self.secondFrame)
        self.secondFrameContent_2.pack(side=TOP, fill=X, expand=False)
        self.secondFrameContent_3 = Frame(self.secondFrame)
        self.secondFrameContent_3.pack(side=TOP, fill=X, expand=False)
        self.secondFrameContent_4 = Frame(self.secondFrame)
        self.secondFrameContent_4.pack(side=TOP, fill=X, expand=False)

        self.thirdFrame = LabelFrame(self.root, text="• Translation Settings")
        self.thirdFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.thirdFrameContent = Frame(self.thirdFrame)
        self.thirdFrameContent.pack(side=TOP, fill=X, expand=False)

        self.fourthFrame = LabelFrame(self.root, text="• Tesseract OCR Settings")
        self.fourthFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fourthFrameContent = Frame(self.fourthFrame)
        self.fourthFrameContent.pack(side=TOP, fill=X, expand=False)

        self.fifthFrame = LabelFrame(self.root, text="• Hotkey Settings")
        self.fifthFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
        self.fifthFrameContent = Frame(self.fifthFrame)
        self.fifthFrameContent.pack(side=TOP, fill=X, expand=False)

        self.bottomFrame = Frame(self.root)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=False)

        # ----------------------------------------------------------------
        # First Frame
        self.checkVarImgSaved = BooleanVar(self.root, name="checkVarImg", value=True) # So its not error
        self.checkBTNSaved = ttk.Checkbutton(self.firstFrameContent, text="Save Captured Image", variable=self.checkVarImgSaved)
        self.checkVarAutoCopy = BooleanVar(self.root, name="checkVarCopyToClip", value=True) # So its not error
        self.checkBTNAutoCopy = ttk.Checkbutton(self.firstFrameContent, text="Auto Copy Captured Text To Clipboard", variable=self.checkVarAutoCopy)
        self.btnOpenImgFolder = ttk.Button(self.firstFrameContent, text="Open Captured Image Folder", command=lambda: startfile(dir_path + r"\..\..\img_captured"))

        self.checkBTNAutoCopy.pack(side=LEFT, padx=5, pady=5)
        self.checkBTNSaved.pack(side=LEFT, padx=5, pady=5)
        self.btnOpenImgFolder.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # Second Frame
        self.CBOffSetChoice = ttk.Combobox(self.secondFrameContent_0, values=["No Offset", "Custom Offset"], state="readonly")

        self.labelCBOffsetNot = Label(self.secondFrameContent_0, text="Capture XY Offset :")
        self.labelOffSetX = Label(self.secondFrameContent_2, text="Offset X :")
        self.labelOffSetY = Label(self.secondFrameContent_3, text="Offset Y :")
        self.labelOffSetW = Label(self.secondFrameContent_2, text="Offset W :")
        self.labelOffSetH = Label(self.secondFrameContent_3, text="Offset H :")

        self.checkVarOffSetX = BooleanVar(self.root, name="checkVarOffSetX", value=True)
        self.checkVarOffSetY = BooleanVar(self.root, name="checkVarOffSetY", value=True)
        self.checkVarOffSetW = BooleanVar(self.root, name="checkVarOffSetW", value=True)
        self.checkVarOffSetH = BooleanVar(self.root, name="checkVarOffSetH", value=True)

        self.checkAutoOffSetX = ttk.Checkbutton(self.secondFrameContent_1, text="Auto Offset X", variable=self.checkVarOffSetX, command=self.checkBtnX)
        self.checkAutoOffSetY = ttk.Checkbutton(self.secondFrameContent_1, text="Auto Offset Y", variable=self.checkVarOffSetY, command=self.checkBtnY)
        self.checkAutoOffSetW = ttk.Checkbutton(self.secondFrameContent_1, text="Auto Offset W", variable=self.checkVarOffSetW, command=self.checkBtnW)
        self.checkAutoOffSetH = ttk.Checkbutton(self.secondFrameContent_1, text="Auto Offset H", variable=self.checkVarOffSetH, command=self.checkBtnH)

        self.spinValOffSetX = StringVar(self.root)
        self.spinValOffSetY = StringVar(self.root)
        self.spinValOffSetW = StringVar(self.root)
        self.spinValOffSetH = StringVar(self.root)

        self.spinValHotkeyDelay = IntVar(self.root)

        self.validateDigits_Offset_X = (self.root.register(self.validateSpinBox_Offset_X), '%P')
        self.validateDigits_Offset_Y = (self.root.register(self.validateSpinBox_Offset_Y), '%P')
        self.validateDigits_Offset_W = (self.root.register(self.validateSpinBox_Offset_W), '%P')
        self.validateDigits_Offset_H = (self.root.register(self.validateSpinBox_Offset_H), '%P')
        self.validateDigits_Delay = (self.root.register(self.validateSpinBox_Delay), '%P')

        self.spinnerOffSetX = ttk.Spinbox(self.secondFrameContent_2, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetX)
        self.spinnerOffSetX.configure(validate='key', validatecommand=self.validateDigits_Offset_X)
        self.spinnerOffSetY = ttk.Spinbox(self.secondFrameContent_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetY)
        self.spinnerOffSetY.configure(validate='key', validatecommand=self.validateDigits_Offset_Y)
        self.spinnerOffSetW = ttk.Spinbox(self.secondFrameContent_2, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetW)
        self.spinnerOffSetW.configure(validate='key', validatecommand=self.validateDigits_Offset_W)
        self.spinnerOffSetH = ttk.Spinbox(self.secondFrameContent_3, from_=-100000, to=100000, width=20, textvariable=self.spinValOffSetH)
        self.spinnerOffSetH.configure(validate='key', validatecommand=self.validateDigits_Offset_H)

        self.buttonCheckMonitorLayout = ttk.Button(self.secondFrameContent_4, text="Click to get A Screenshot of How The Program See Your Monitor", command=self.screenShotAndOpenLayout)

        self.labelCBOffsetNot.pack(side=LEFT, padx=5, pady=5)
        self.CBOffSetChoice.pack(side=LEFT, padx=5, pady=5)
        self.CBOffSetChoice.bind("<<ComboboxSelected>>", self.CBOffSetChange)

        self.checkAutoOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.checkAutoOffSetH.pack(side=LEFT, padx=5, pady=5)

        self.labelOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetX.pack(side=LEFT, padx=5, pady=5)
        self.labelOffSetY.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetY.pack(side=LEFT, padx=5, pady=5)

        self.labelOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetW.pack(side=LEFT, padx=5, pady=5)
        self.labelOffSetH.pack(side=LEFT, padx=5, pady=5)
        self.spinnerOffSetH.pack(side=LEFT, padx=8, pady=5)

        self.buttonCheckMonitorLayout.pack(side=LEFT, padx=30, pady=5)

        # ----------------------------------------------------------------
        # Third frame
        self.langOpt = optGoogle

        self.CBDefaultEngine = ttk.Combobox(self.thirdFrameContent, values=engines, state="readonly")
        self.CBDefaultFrom = ttk.Combobox(self.thirdFrameContent, values=self.langOpt, state="readonly")
        self.CBDefaultTo = ttk.Combobox(self.thirdFrameContent, values=self.langOpt, state="readonly")
        self.labelDefaultEngine = Label(self.thirdFrameContent, text="Default Engine :")
        self.labelDefaultFrom = Label(self.thirdFrameContent, text="Default From :")
        self.labelDefaultTo = Label(self.thirdFrameContent, text="Default To :")

        self.labelDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.bind("<<ComboboxSelected>>", self.CBTLChange_setting)

        self.labelDefaultFrom.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelDefaultTo.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultTo.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # Fourth frame
        self.labelTesseractPath = Label(self.fourthFrameContent, text="Tesseract Path :")
        self.textBoxTesseractPath = ttk.Entry(self.fourthFrameContent, width=70, xscrollcommand=True)
        self.textBoxTesseractPath.bind("<Key>", lambda event: globalStuff.allowedKey(event)) # Disable textbox input
        self.btnSearchTesseract = ttk.Button(self.fourthFrameContent, text="...", command=self.searchTesseract)

        self.labelTesseractPath.pack(side=LEFT, padx=5, pady=5)
        self.textBoxTesseractPath.pack(side=LEFT, padx=5, pady=5, fill=X, expand=True)
        self.btnSearchTesseract.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # Fifth frame
        self.labelHotkeyDelay = Label(self.fifthFrameContent, text="Time delay (ms) : ")
        self.spinnerHotkeyDelay = ttk.Spinbox(self.fifthFrameContent, from_=0, to=100000, width=20, textvariable=self.spinValHotkeyDelay)
        self.spinnerHotkeyDelay.configure(validate='key', validatecommand=self.validateDigits_Delay)
        self.buttonSetHotkey = ttk.Button(self.fifthFrameContent, text="Click to set hotkey for capture", command=self.setHotkey)
        self.buttonClearHotkey = ttk.Button(self.fifthFrameContent, text="Clear", command=self.clearHotkey)
        self.labelHotkeyTip = Label(self.fifthFrameContent, text="Current hotkey : ")
        self.labelCurrentHotkey = Label(self.fifthFrameContent, text="")

        self.labelHotkeyDelay.pack(side=LEFT, padx=5, pady=5)
        self.spinnerHotkeyDelay.pack(side=LEFT, padx=5, pady=5)
        self.buttonSetHotkey.pack(side=LEFT, padx=5, pady=5)
        self.buttonClearHotkey.pack(side=LEFT, padx=5, pady=5)
        self.labelHotkeyTip.pack(side=LEFT, padx=5, pady=5)
        self.labelCurrentHotkey.pack(side=LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # Bottom Frame
        self.btnSave = ttk.Button(self.bottomFrame, text="Save Settings", command=self.saveSettings)
        self.btnSave.pack(side=RIGHT, padx=4, pady=5)
        self.btnReset = ttk.Button(self.bottomFrame, text="Reset To Currently Stored Setting", command=self.reset)
        self.btnReset.pack(side=RIGHT, padx=5, pady=5)
        self.btnRestoreDefault = ttk.Button(self.bottomFrame, text="Restore Default", command=self.restoreDefault)
        self.btnRestoreDefault.pack(side=RIGHT, padx=5, pady=5)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def searchTesseract(self):
        self.tesseract_path = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("tesseract.exe", "*.exe"),
        ))
        if self.tesseract_path != "":
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, self.tesseract_path)

    def show(self):
        fJson.loadSetting() # read settings every time it is opened
        self.reset()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def getCurrXYOFF(self = ""):
        if self.checkVarOffSetX.get():
            x = int(self.spinnerOffSetX.get())
        else:
            x = "auto"
        if self.checkVarOffSetY.get():
            y = int(self.spinnerOffSetY.get())
        else:
            y = "auto"
        if self.checkVarOffSetW.get():
            w = int(self.spinnerOffSetW.get())
        else:
            w = "auto"
        if self.checkVarOffSetH.get():
            h = int(self.spinnerOffSetH.get())
        else:
            h = "auto"

        return [x, y, w, h]

    def checkBtnOffSet(self):
        pass

    def checkBtnX(self):
        offSets = getTheOffset(self.getCurrXYOFF()[0])

        if self.root.getvar(name="checkVarOffSetX") == "1":
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinValOffSetX.set(str(offSets[0]))
        else:
            self.spinnerOffSetX.config(state=NORMAL)

    def checkBtnY(self):
        offSets = getTheOffset(self.getCurrXYOFF()[1])

        if self.root.getvar(name="checkVarOffSetY") == "1":
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetY.set(str(offSets[1]))
        else:
            self.spinnerOffSetY.config(state=NORMAL)

    def checkBtnW(self):
        offSets = getTheOffset(self.getCurrXYOFF()[2])

        if self.root.getvar(name="checkVarOffSetW") == "1":
            self.spinnerOffSetW.config(state=DISABLED)
            self.spinValOffSetW.set(str(offSets[2]))
        else:
            self.spinnerOffSetW.config(state=NORMAL)

    def checkBtnH(self):
        offSets = getTheOffset(self.getCurrXYOFF()[3])

        if self.root.getvar(name="checkVarOffSetH") == "1":
            self.spinnerOffSetH.config(state=DISABLED)
            self.spinValOffSetH.set(str(offSets[3]))
        else:
            self.spinnerOffSetH.config(state=NORMAL)

    def screenShotAndOpenLayout(self):
        captureAll()

    def setHotkey(self):
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHotkey.config(text=str(hotkey))

    def clearHotkey(self):
        self.labelCurrentHotkey.config(text="")

    def restoreDefault(self):
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
        settings = fJson.readSetting()

        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2, self.root)

        # Cache checkbox
        if settings['cached'] == True:
            self.checkVarImgSaved.set(True)
        else:
            self.checkVarImgSaved.set(False)

        # Autocopy checkbox
        if settings['autoCopy'] == True:
            self.checkVarAutoCopy.set(True)
        else:
            self.checkVarAutoCopy.set(False)

        # Show current hotkey
        self.labelCurrentHotkey.config(text=settings['capture_Hotkey'])

        # Store setting to localvar
        offSetXY = settings["offSetXY"]
        offSetWH = settings["offSetWH"]
        xyOffSetType = settings["offSetXYType"]

        self.spinValHotkeyDelay.set(settings["capture_HotkeyDelay"])

        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY)
        x = offSets[0]
        y = offSets[1]
        w = offSets[2]
        h = offSets[3]

        if xyOffSetType == "No Offset":
            self.CBOffSetChoice.current(0)
            self.checkAutoOffSetX.config(state=DISABLED)
            self.checkAutoOffSetY.config(state=DISABLED)
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinValOffSetX.set("0")
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetY.set("0")

            self.checkVarOffSetX.set(False)
            self.checkVarOffSetY.set(False)

        elif xyOffSetType == "Custom Offset":
            self.CBOffSetChoice.current(1)
            self.spinValOffSetX.set(str(x))
            self.spinValOffSetY.set(str(y))
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
        self.spinValOffSetW.set(str(w))
        self.spinValOffSetH.set(str(h))

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

        print("Setting Loaded")
        # No need for mbox

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
        if self.checkVarOffSetX.get():
            x = "auto"
        else:
            x = int(self.spinnerOffSetX.get())
        # y
        if self.checkVarOffSetY.get():
            y = "auto"
        else:
            y = int(self.spinnerOffSetY.get())
        # w
        if self.checkVarOffSetW.get():
            w = "auto"
        else:
            w = int(self.spinnerOffSetW.get())
        # h
        if self.checkVarOffSetH.get():
            h = "auto"
        else:
            h = int(self.spinnerOffSetH.get())

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
            "capture_HotkeyDelay": self.spinValHotkeyDelay.get()
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
            self.spinValOffSetX.set("0")
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetY.set("0")
        else:
            # Disselect auto
            self.checkVarOffSetX.set(True)
            self.checkVarOffSetY.set(True)
            # Make checbtn clickable, but set auto which means spin is disabled
            self.checkAutoOffSetX.config(state=NORMAL)
            self.checkAutoOffSetY.config(state=NORMAL)
            self.spinValOffSetX.set(str(offSets[0]))
            self.spinValOffSetY.set(str(offSets[1]))
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