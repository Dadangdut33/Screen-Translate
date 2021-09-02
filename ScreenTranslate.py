import pyautogui
import os
import webbrowser
import asyncio
from resource.LangCode import *
from tkinter import *
from tkinter import ttk
# from tkinter.tix import * # WHat does this even do??, error everytime on build cause of this
import tkinter.ttk as ttk
import resource.Capture as capture
import resource.JsonHandling as fJson
import subprocess
import pyperclip
from resource.Mbox import Mbox
from sys import exit

# Add try except to intercept connection error
try:
    import resource.Translate as tl
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

try:
    import resource.Translate_Deepl as tl_deepl
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

# Get dir path
dir_path = os.path.dirname(os.path.realpath(__file__))

# ----------------------------------------------------------------
# public func
def startfile(filename):
  try:
    os.startfile(filename)
  except:
    subprocess.Popen(['xdg-open', filename])

def OpenUrl(url):
    webbrowser.open_new(url)

def searchList(searchFor, theList):
    index = 0
    for lang in theList:
        if lang == searchFor:
            return index
        index += 1
    else:
        return 0

def fillList(dictFrom, listTo, insertFirst = "", insertSecond = ""):
    for item in dictFrom:
        if item == "Auto-Detect":
            continue
        listTo += [item]

    listTo.sort()
    if insertFirst != "":
        listTo.insert(0, insertFirst)
    if insertSecond != "":
        listTo.insert(1, insertSecond)

def offSetSettings(widthHeighOff, xyOffsetType, xyOff, custom = ""):
    offSetsGet = []
    x, y, w, h = 0, 0, 0, 0
    if widthHeighOff[0] == "auto":
        w = 60
    else:
        w = widthHeighOff[0]

    if widthHeighOff[1] == "auto":
        h = 60
    else:
        h = widthHeighOff[1]

    #  If offset is set
    if xyOffsetType.lower() != "no offset" or custom != "":
        offsetX = pyautogui.size().width
        offsetY = pyautogui.size().height
        
        # If auto
        if xyOff[0] == "auto":
            if(offsetX > offsetY): # Horizontal
                x = offsetX
            else:
                x = 0
        else: # if set manually
            x = xyOff[0]

        # If auto
        if xyOff[1] == "auto":
            if(offsetY > offsetX): # Vertical
                y = offsetY
            else:
                y = 0
        else: # if set manually
            y = xyOff[1]
    
    offSetsGet.append(x)
    offSetsGet.append(y)
    offSetsGet.append(w)
    offSetsGet.append(h)
    return offSetsGet

def getTheOffset(custom = ""):
    tStatus, settings = fJson.readSetting()

    offSetXY = settings["offSetXY"]
    offSetWH = settings["offSetWH"]
    xyOffSetType = settings["offSetXYType"]

    # If custom
    if custom != "":
        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY, custom)
    else: # if not
        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY)

    return offSets

def console():
    print("-" * 80)
    print("Welcome to Screen Translate")
    print("Use The GUI Window to start capturing and translating")
    print("This window is for debugging purposes")

# ----------------------------------------------------------------
# Public var
engines = engineList
optGoogle = []
fillList(google_Lang, optGoogle, "Auto-Detect")
optDeepl = []
fillList(deepl_Lang, optDeepl, "Auto-Detect")
optMyMemory = []
fillList(myMemory_Lang, optMyMemory, "Auto-Detect")
optPons = []
fillList(pons_Lang, optPons) # PONS HAVE NO AUTO DETECT

# ----------------------------------------------------------------------
# Classes
class CaptureUI():
    """Capture Window"""
    root = Tk()
    alwaysOnTop = BooleanVar()
    alwaysOnTop.set(True)
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
    def getTextAndTranslate(self, offSetXY=["auto", "auto"]):
        if(main_Menu.capUiHidden): # If Hidden
            Mbox("Error: You need to generate the capture window", "Please generate the capture window first", 2)
            print("Error Need to generate the capture window! Please generate the capture window first")
            return
        if(main_Menu.CBLangFrom.current()) == (main_Menu.CBLangTo.current()): # If Selected type invalid
            Mbox("Error: Language target is the same as source", "Please choose a different language", 2)
            print("Error Language is the same as source! Please choose a different language")
            return
        if main_Menu.CBLangTo.get() == "Auto-Detect" or main_Menu.CBLangTo.current() == 0 or main_Menu.CBLangFrom.get() == "Auto-Detect" or main_Menu.CBLangFrom.current() == 0: # If Selected type invalid
            Mbox("Error: Invalid Language Selected", "Can't Use Auto Detect in Capture Mode", 2)
            print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
            return
        
        # Hide the Capture Window so it can detect the words better
        opacBefore = self.currOpacity
        self.root.attributes('-alpha', 0)
        
        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()

        # Get settings
        tStatus, settings = fJson.readSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings[0] == "Setting file is not found":
                self.root.wm_withdraw()  # Hide the capture window

                # Show error
                print("Error: " + settings[0])
                print(settings[1])
                Mbox("Error: " + settings[0], settings[1], 2)
                
                # Set Default
                var1, var2 = fJson.setDefault()
                if var1 : # If successfully set default
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 2)
                else: # If error
                    print("Error: " + var2)
                    Mbox("An Error Occured", var2, 2)
                
                self.root.wm_deiconify()  # Show the capture window
                return # Reject
        
        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            self.root.wm_withdraw()  # Hide the capture window
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in resource/backend/json/Setting.json", 2)
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

        language = main_Menu.CBLangFrom.get()
        is_Success, result = capture.captureImg(coords, language, settings['tesseract_loc'], settings['cached'])
        self.root.attributes('-alpha', opacBefore)
        
        print("Area Captured Successfully!") # Debug Print
        print("Coordinates: " + str(coords)) # Debug Print

        if is_Success == False or len(result) == 1:
            print("But Failed to capture any text!")
            Mbox("Warning", "Failed to Capture Text!", 1)
        else:
            main_Menu.root.deiconify()

            # Pass it to mainMenu
            main_Menu.textBoxTop.delete(1.0, END)
            main_Menu.textBoxTop.insert(END, result[:-1]) # Delete last character

            if settings['autoCopy'] == True:
                print("Copying text to clipboard")
                pyperclip.copy(result[:-1].strip())
                print("Copied successfully to clipboard!")

            # Run the translate function
            main_Menu.translate(main_Menu, result[:-1])

    # Menubar
    def always_on_top(self):
        if self.alwaysOnTop.get(): # IF ON THEN TURN IT OFF
            self.root.wm_attributes('-topmost', True)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', False)

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root.title('Text Capture Area')
        self.root.geometry('500x150')
        self.root.wm_attributes('-topmost', True)
        self.Hidden = False
        self.root.wm_withdraw()
        
        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTop, command=self.always_on_top)
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

    # ----------------------------------------------------------------
    # Functions
    def show(self):
        self.refresh()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def deleteSelected():
        sel_Index = main_Menu.history.historyTreeView.focus()
        if sel_Index != "":
            x = Mbox("Confirmation", "Are you sure you want to the selected data?", 3)
            if x == False:
                Mbox("Canceled", "Action Canceled", 0)
                return

            dataRow = main_Menu.history.historyTreeView.item(sel_Index, 'values')

            status, statusText = fJson.deleteCertainHistory(int(dataRow[0]))
            if status == True:
                print("Success: " + statusText)
                Mbox("Success", statusText, 0)
            # Error already handled in jsonHandling

            # Refresh
            main_Menu.history.refresh()

    def deleteAll():
        x = Mbox("Confirmation", "Are you sure you want to delete all history?", 3)
        if x == False:
            Mbox("Canceled", "Action Canceled", 0)
            return

        status, statusText = fJson.deleteAllHistory()
        if status == True:
            print("Success: " + statusText)
            Mbox("Success", statusText, 0)
        # Error already handled in jsonHandling

        # Refresh
        main_Menu.history.refresh()


    def refresh(x = ""):
        status, data = fJson.readHistory()
        # Error already handled in jsonHandling
        if status == True:
            listData = []
            # convert json to list, then make it a list in list... 
            for item in data['tl_history']:
                addToList = [item['id'], item['from'], item['to'], item['query'], item['result'], item['engine']]

                listData.append(addToList)
    
            for i in main_Menu.history.historyTreeView.get_children():
                main_Menu.history.historyTreeView.delete(i)

            count = 0
            for record in listData:
                # Parent
                parentID = count
                main_Menu.history.historyTreeView.insert(parent='', index='end', text='', iid=count, values=(record[0], record[1] + "-" + record[2], record[3].replace("\n", " ")))
                
                count += 1
                # Child
                main_Menu.history.historyTreeView.insert(parent=parentID, index='end', text='', iid=count, values=(record[0], "Using " + record[5], record[4].replace("\n", " ")))

                count += 1
            # ------------------------------------------------------------
            print("History loaded")
        else:
            for i in main_Menu.history.historyTreeView.get_children():
                main_Menu.history.historyTreeView.delete(i)

    def copyToClipboard():
        sel_Index = main_Menu.history.historyTreeView.focus()
        if sel_Index != "":
            dataRow = main_Menu.history.historyTreeView.item(sel_Index, 'values')
            pyperclip.copy(dataRow[2].strip())

    def copyToTranslateMenu():
        sel_Index = main_Menu.history.historyTreeView.focus()
        if sel_Index != '':
            dataRow = main_Menu.history.historyTreeView.item(sel_Index, 'values')
            main_Menu.textBoxTop.delete(1.0, END)
            main_Menu.textBoxTop.insert(1.0, dataRow[2])

    def handle_click(event):
        if main_Menu.history.historyTreeView.identify_region(event.x, event.y) == "separator":
            return "break"

    # ----------------------------------------------------------------
    # Layout
    # frameOne
    firstFrame = Frame(root)
    firstFrame.pack(side=TOP, fill=BOTH, padx=5, expand=False)
    firstFrameScrollX = Frame(root)
    firstFrameScrollX.pack(side=TOP, fill=X, padx=5, expand=False)

    bottomFrame = Frame(root)
    bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=False)

    # elements
    # Treeview
    historyTreeView = ttk.Treeview(firstFrame, columns=('Id', 'From-To', 'Query'))
    historyTreeView['columns']=('Id', 'From-To', 'Query')

    # Scrollbar
    scrollbarY = Scrollbar(firstFrame, orient=VERTICAL)
    scrollbarY.pack(side=RIGHT, fill=Y)
    scrollbarX = Scrollbar(firstFrameScrollX, orient=HORIZONTAL)
    scrollbarX.pack(side=TOP, fill=X)

    scrollbarX.config(command=historyTreeView.xview)
    scrollbarY.config(command=historyTreeView.yview)
    historyTreeView.config(yscrollcommand=scrollbarY.set, xscrollcommand=scrollbarX.set)
    historyTreeView.bind('<Button-1>', handle_click)

    # Other stuff
    btnCopyToClipboard = Button(bottomFrame, text="Copy to Clipboard", command=copyToClipboard)
    btnCopyToTranslateBox = Button(bottomFrame, text="Copy to Translate Menu", command=copyToTranslateMenu)
    btnDeleteAll = Button(bottomFrame, text="Delete All", command=deleteAll)
    btnDeleteSelected = Button(bottomFrame, text="Delete Selected", command=deleteSelected)
    btnRefresh = Button(bottomFrame, text="Refresh", command=refresh)

    # ----------------------------------------------------------------
    def __init__(self):
        self.root.title("History")
        self.root.geometry("700x300")
        self.root.wm_attributes('-topmost', False) # Default False
        self.root.wm_withdraw()

        # Init element
        status, data = fJson.readHistory()

        # Error already handled in jsonHandling
        listData = []

        # convert json to list, then make it a list in list... 
        for item in data['tl_history']:
            addToList = [item['id'], item['from'], item['to'], item['query'], item['result'], item['engine']]

            listData.append(addToList)
 
        count = 0
        for record in listData:
            # Parent
            parentID = count
            self.historyTreeView.insert(parent='', index='end', text='', iid=count, values=(record[0], record[1] + "-" + record[2], record[3].replace("\n", " ")))
            
            count += 1
            # Child
            self.historyTreeView.insert(parent=parentID, index='end', text='', iid=count, values=(record[0], "Engine: " + record[5], record[4].replace("\n", " ")))

            count += 1

        self.historyTreeView.heading('#0', text='', anchor=CENTER)
        self.historyTreeView.heading('Id', text='Id', anchor=CENTER)
        self.historyTreeView.heading('From-To', text='From-To', anchor=CENTER)
        self.historyTreeView.heading('Query', text='Query', anchor="w")

        self.historyTreeView.column('#0', width=20, stretch=False)
        self.historyTreeView.column('Id', anchor=CENTER, width=50, stretch=True)
        self.historyTreeView.column('From-To', anchor=CENTER, width=150, stretch=False)
        self.historyTreeView.column('Query', anchor="w", width=10000, stretch=False) # Make the width ridiculuosly long so it can use the x scrollbar 

        self.historyTreeView.pack(side=TOP, padx=5, pady=5, fill=BOTH, expand=False)
        self.btnRefresh.pack(side=LEFT, fill=X, padx=10, pady=5, expand=False)
        self.btnCopyToClipboard.pack(side=LEFT, fill=X, padx=5, pady=5, expand=False)
        self.btnCopyToTranslateBox.pack(side=LEFT, fill=X, padx=5, pady=5, expand=False)
        self.btnDeleteSelected.pack(side=LEFT, fill=X, padx=5, pady=5, expand=False)
        self.btnDeleteAll.pack(side=LEFT, fill=X, padx=5, pady=5, expand=False)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

# ----------------------------------------------------------------------
class SettingUI():
    """Setting Window"""
    root = Tk()

    def show(self):
        self.reset()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def getCurrXYOFF(self = ""):
        if main_Menu.setting_UI.checkVarOffSetX.get():
            x = int(main_Menu.setting_UI.spinnerOffSetX.get())
        else: 
            x = "auto"
        if main_Menu.setting_UI.checkVarOffSetY.get():
            y = int(main_Menu.setting_UI.spinnerOffSetY.get())
        else:
            y = "auto"
        if main_Menu.setting_UI.checkVarOffSetW.get():
            w = int(main_Menu.setting_UI.spinnerOffSetW.get())
        else:
            w = "auto"
        if main_Menu.setting_UI.checkVarOffSetH.get():
            h = int(main_Menu.setting_UI.spinnerOffSetH.get())
        else:
            h = "auto"

        return [x, y, w, h]

    def checkBtnX():
        offSets = getTheOffset(main_Menu.setting_UI.getCurrXYOFF()[0])

        if main_Menu.setting_UI.root.getvar(name="checkVarOffSetX") == "1":
            main_Menu.setting_UI.spinnerOffSetX.config(state=DISABLED)
            main_Menu.setting_UI.spinValOffSetX.set(str(offSets[0]))
        else:
            main_Menu.setting_UI.spinnerOffSetX.config(state=NORMAL)

    def checkBtnY():
        offSets = getTheOffset(main_Menu.setting_UI.getCurrXYOFF()[1])

        if main_Menu.setting_UI.root.getvar(name="checkVarOffSetY") == "1":
            main_Menu.setting_UI.spinnerOffSetY.config(state=DISABLED)
            main_Menu.setting_UI.spinValOffSetY.set(str(offSets[1]))
        else:
            main_Menu.setting_UI.spinnerOffSetY.config(state=NORMAL)

    def checkBtnW():
        offSets = getTheOffset(main_Menu.setting_UI.getCurrXYOFF()[2])

        if main_Menu.setting_UI.root.getvar(name="checkVarOffSetW") == "1":
            main_Menu.setting_UI.spinnerOffSetW.config(state=DISABLED)
            main_Menu.setting_UI.spinValOffSetW.set(str(offSets[2]))
        else:
            main_Menu.setting_UI.spinnerOffSetW.config(state=NORMAL)

    def checkBtnH():
        offSets = getTheOffset(main_Menu.setting_UI.getCurrXYOFF()[3])

        if main_Menu.setting_UI.root.getvar(name="checkVarOffSetH") == "1":
            main_Menu.setting_UI.spinnerOffSetH.config(state=DISABLED)
            main_Menu.setting_UI.spinValOffSetH.set(str(offSets[3]))
        else:
            main_Menu.setting_UI.spinnerOffSetH.config(state=NORMAL)

    def screenShotAndOpenLayout():
        capture.captureAll()
        startfile(dir_path + r"\resource\img_cache\Monitor(s) Captured View.png")

    def restoreDefault(self):
        x = Mbox("Confirmation", "Are you sure you want to set the settings to default?\n\n**WARNING! CURRENTLY SAVED SETTING WILL BE OVERWRITTEN**", 3)
        if x == False:
            Mbox("Canceled", "Action Canceled", 0)
            return

        # Restore Default Settings
        tStatus, settings = fJson.setDefault()
        if tStatus == True:
            # Update the settings
            self.reset()
            
            # Tell success
            print("Restored Default Settings")
            Mbox("Success", "Successfully Restored Value to Default Settings", 0)

    def reset(self):
        tStatus, settings = fJson.readSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings[0] == "Setting file is not found":
                self.root.wm_withdraw()  # Hide setting

                # Show error
                print("Error: " + settings[0])
                print(settings[1])
                Mbox("Error: " + settings[0], settings[1], 2)
                
                settings = fJson.default_Setting

                # Set Default
                var1, var2 = fJson.setDefault()
                if var1 : # If successfully set default
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 1)
                else: # If error
                    print("Error: " + var2)
                    Mbox("An Error Occured", var2, 2)
                
                self.root.wm_deiconify()  # Show setting
        validTesseract = "tesseract" in settings['tesseract_loc'].lower()
        # If tesseract is not found
        if os.path.exists(settings['tesseract_loc']) == False or validTesseract == False:
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in resource/backend/json/Setting.json", 2)
        
        # Cache checkbox
        if settings['cached'] == True:
            self.root.setvar(name="checkVarCache", value=True)
            self.checkBTNCache.select()
        else:
            self.root.setvar(name="checkVarCache", value=False)
            self.checkBTNCache.deselect()

        # Autocopy checkbox
        if settings['autoCopy'] == True:
            self.root.setvar(name="checkVarAutoCopy", value=True)
            self.checkBTNAutoCopy.select()
        else:
            self.root.setvar(name="checkVarAutoCopy", value=False)
            self.checkBTNAutoCopy.deselect()

        # Store setting to localvar
        offSetXY = settings["offSetXY"]
        offSetWH = settings["offSetWH"]
        xyOffSetType = settings["offSetXYType"]

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

            self.checkAutoOffSetX.deselect()
            self.root.setvar(name="checkVarOffSetX", value=False)
            self.checkAutoOffSetY.deselect()
            self.root.setvar(name="checkVarOffSetY", value=False)

        elif xyOffSetType == "Custom Offset":
            self.CBOffSetChoice.current(1)
            self.spinValOffSetX.set(str(x))
            self.spinValOffSetY.set(str(y))
            self.checkAutoOffSetX.config(state=NORMAL)
            self.checkAutoOffSetY.config(state=NORMAL)

            if offSetXY[0] == "auto":
                self.checkAutoOffSetX.select()
                self.root.setvar(name="checkVarOffSetX", value=True)
                self.spinnerOffSetX.config(state=DISABLED)
            else:
                self.checkAutoOffSetX.deselect()
                self.root.setvar(name="checkVarOffSetX", value=False)
                self.spinnerOffSetX.config(state=NORMAL)

            if offSetXY[1] == "auto":
                self.checkAutoOffSetY.select()
                self.root.setvar(name="checkVarOffSetY", value=True)
                self.spinnerOffSetY.config(state=DISABLED)
            else:
                self.checkAutoOffSetY.deselect()
                self.root.setvar(name="checkVarOffSetY", value=False)
                self.spinnerOffSetY.config(state=NORMAL)
        else:
            self.CBOffSetChoice.current(0)
            print("Error: Invalid Offset Type")
            Mbox("Error: Invalid Offset Type", "Please do not modify the setting manually if you don't know what you are doing", 2)
        
        # W H
        self.spinValOffSetW.set(str(w))
        self.spinValOffSetH.set(str(h))

        if(settings["offSetWH"][0] == "auto"):
            self.checkAutoOffSetW.select()
            self.root.setvar(name="checkVarOffSetW", value=True)
            self.spinnerOffSetW.config(state=DISABLED)
        else:
            self.checkAutoOffSetW.deselect()
            self.root.setvar(name="checkVarOffSetW", value=False)
            self.spinnerOffSetW.config(state=NORMAL)
        
        if(settings["offSetWH"][1] == "auto"):
            self.checkAutoOffSetH.select()
            self.root.setvar(name="checkVarOffSetH", value=True)
            self.spinnerOffSetH.config(state=DISABLED)
        else:
            self.checkAutoOffSetH.deselect()
            self.root.setvar(name="checkVarOffSetH", value=False)
            self.spinnerOffSetH.config(state=NORMAL)
        
        self.CBTLChange_setting()
        self.CBDefaultEngine.current(searchList(settings['default_Engine'], engines))
        self.CBDefaultFrom.current(searchList(settings['default_FromOnOpen'], self.langOpt))
        self.CBDefaultTo.current(searchList(settings['default_ToOnOpen'], self.langOpt))
        self.textBoxTesseractPath.delete(1.0, END)
        self.textBoxTesseractPath.insert(1.0, settings['tesseract_loc'])

        print("Setting Loaded")
        # No need for mbox

    def saveSettings():
        # Check path tesseract
        tesseractPathInput = main_Menu.setting_UI.textBoxTesseractPath.get("1.0", END).strip().lower()
        validTesseract = "tesseract" in tesseractPathInput
        # # If tesseract is not found
        if os.path.exists(tesseractPathInput) == False or validTesseract == False:
            print("Tesseract Not Found Error")
            Mbox("Error: Tesseract not found", "Invalid Path Provided For Tesseract.exe!", 2)
            return

        print(main_Menu.setting_UI.checkVarOffSetX.get())
        if main_Menu.setting_UI.checkVarOffSetX.get():
            x = "auto"
        else: 
            x = int(main_Menu.setting_UI.spinnerOffSetX.get())
        if main_Menu.setting_UI.checkVarOffSetY.get():
            y = "auto"
        else:
            y = int(main_Menu.setting_UI.spinnerOffSetY.get())
        if main_Menu.setting_UI.checkVarOffSetW.get():
            w = "auto"
        else:
            w = int(main_Menu.setting_UI.spinnerOffSetW.get())
        if main_Menu.setting_UI.checkVarOffSetH.get():
            h = "auto"
        else:
            h = int(main_Menu.setting_UI.spinnerOffSetH.get())

        settingToSave = { 
            "cached": main_Menu.setting_UI.checkVarCache.get(),
            "autoCopy": main_Menu.setting_UI.checkVarAutoCopy.get(),
            "offSetXYType": main_Menu.setting_UI.CBOffSetChoice.get(),
            "offSetXY": [x, y],
            "offSetWH": [w, h],
            "tesseract_loc": main_Menu.setting_UI.textBoxTesseractPath.get("1.0", END).strip(),
            "default_Engine": main_Menu.setting_UI.CBDefaultEngine.get(),
            "default_FromOnOpen": main_Menu.setting_UI.CBDefaultFrom.get(),
            "default_ToOnOpen": main_Menu.setting_UI.CBDefaultTo.get()
        }

        print("-" * 50)
        print("Setting saved!")
        print(settingToSave)

        status, dataStatus = fJson.writeSetting(settingToSave)
        if status:
            print("-" * 50)
            print(dataStatus)
            Mbox("Success", dataStatus, 0)
        else:
            print("-" * 50)
            print(dataStatus)
            Mbox("Error", dataStatus, 2)

    def CBOffSetChange(self, event = ""):
        offSets = getTheOffset("Custom")
        xyOffSetType = self.CBOffSetChoice.get()

        # Check offset or not
        if xyOffSetType == "No Offset":
            # Select auto
            self.checkAutoOffSetX.select()
            self.checkAutoOffSetY.select()
            # Disable spinner and the selector, also set stuff in spinner to 0
            self.checkAutoOffSetX.config(state=DISABLED)
            self.checkAutoOffSetY.config(state=DISABLED)
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinValOffSetX.set("0")
            self.spinnerOffSetY.config(state=DISABLED)
            self.spinValOffSetY.set("0")
        else:
            # Disselect auto
            self.checkAutoOffSetX.select()
            self.checkAutoOffSetY.select()
            # Make checbtn clickable, but set auto which means spin is disabled
            self.checkAutoOffSetX.config(state=NORMAL)
            self.checkAutoOffSetY.config(state=NORMAL)
            self.spinValOffSetX.set(str(offSets[0]))
            self.spinValOffSetY.set(str(offSets[1]))
            self.spinnerOffSetX.config(state=DISABLED)
            self.spinnerOffSetY.config(state=DISABLED)

    def validateSpinBox(event):
        return event.isdigit()

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
        elif curr_Engine == "Deepl":
            self.langOpt = optDeepl
            self.CBDefaultFrom['values'] = optDeepl
            self.CBDefaultFrom.current(searchList(previous_From, optDeepl))
            self.CBDefaultTo['values'] = optDeepl
            self.CBDefaultTo.current(searchList(previous_To, optDeepl))
        elif curr_Engine == "MyMemoryTranslator":
            self.langOpt = optMyMemory
            self.CBDefaultFrom['values'] = optMyMemory
            self.CBDefaultFrom.current(searchList(previous_From, optMyMemory))
            self.CBDefaultTo['values'] = optMyMemory
            self.CBDefaultTo.current(searchList(previous_To, optMyMemory))
        elif curr_Engine == "PONS":
            self.langOpt = optPons
            self.CBDefaultFrom['values'] = optPons
            self.CBDefaultFrom.current(searchList(previous_From, optPons))
            self.CBDefaultTo['values'] = optPons
            self.CBDefaultTo.current(searchList(previous_To, optPons))

    # Frames
    s = ttk.Style()
    s.configure('TLabelframe.Label', font='arial 14 bold')

    firstFrame = ttk.LabelFrame(root, text="• Image / OCR Setting")
    firstFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
    firstFrameContent = Frame(firstFrame)
    firstFrameContent.pack(side=TOP, fill=X, expand=False)

    secondFrame = ttk.LabelFrame(root, text="• Monitor Capture Offset")
    secondFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
    secondFrameContent0 = Frame(secondFrame)
    secondFrameContent0.pack(side=TOP, fill=X, expand=False)
    secondFrameContent1 = Frame(secondFrame)
    secondFrameContent1.pack(side=TOP, fill=X, expand=False)
    secondFrameContent2 = Frame(secondFrame)
    secondFrameContent2.pack(side=TOP, fill=X, expand=False)
    secondFrameContent3 = Frame(secondFrame)
    secondFrameContent3.pack(side=TOP, fill=X, expand=False)
    secondFrameContent4 = Frame(secondFrame)
    secondFrameContent4.pack(side=TOP, fill=X, expand=False)

    thirdFrame = ttk.LabelFrame(root, text="• Translation Settings")
    thirdFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
    thirdFrameContent = Frame(thirdFrame)
    thirdFrameContent.pack(side=TOP, fill=X, expand=False)

    fourthFrame = ttk.LabelFrame(root, text="• Tesseract OCR Settings")
    fourthFrame.pack(side=TOP, fill=X, expand=False, padx=5, pady=5)
    fourthFrameContent = Frame(fourthFrame)
    fourthFrameContent.pack(side=TOP, fill=X, expand=False)

    bottomFrame = Frame(root)
    bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=False)

    # First Frame
    checkVarCache = BooleanVar(root, name="checkVarCache", value=True) # So its not error
    checkBTNCache = Checkbutton(firstFrameContent, text="Cached", variable=checkVarCache)
    checkVarAutoCopy = BooleanVar(root, name="checkVarCopyToClip", value=True) # So its not error
    checkBTNAutoCopy = Checkbutton(firstFrameContent, text="Auto Copy Captured Text To Clipboard", variable=checkVarAutoCopy)
    btnOpenCacheFolder = Button(firstFrameContent, text="Open Cache Folder", command=lambda: startfile(dir_path + r"\resource\img_cache"))

    # Second Frame
    CBOffSetChoice = ttk.Combobox(secondFrameContent0, values=["No Offset", "Custom Offset"], state="readonly")

    labelCBOffsetNot = Label(secondFrameContent0, text="Capture XY Offset :")
    labelOffSetX = Label(secondFrameContent2, text="Offset X :")
    labelOffSetY = Label(secondFrameContent3, text="Offset Y :")
    labelOffSetW = Label(secondFrameContent2, text="Offset W :")
    labelOffSetH = Label(secondFrameContent3, text="Offset H :")

    checkVarOffSetX = BooleanVar(root, name="checkVarOffSetX", value=True)
    checkVarOffSetY = BooleanVar(root, name="checkVarOffSetY", value=True)
    checkVarOffSetW = BooleanVar(root, name="checkVarOffSetW", value=True)
    checkVarOffSetH = BooleanVar(root, name="checkVarOffSetH", value=True)

    checkAutoOffSetX = Checkbutton(secondFrameContent1, text="Auto Offset X", variable=checkVarOffSetX, command=checkBtnX)
    checkAutoOffSetY = Checkbutton(secondFrameContent1, text="Auto Offset Y", variable=checkVarOffSetY, command=checkBtnY)
    checkAutoOffSetW = Checkbutton(secondFrameContent1, text="Auto Offset W", variable=checkVarOffSetW, command=checkBtnW)
    checkAutoOffSetH = Checkbutton(secondFrameContent1, text="Auto Offset H", variable=checkVarOffSetH, command=checkBtnH)

    spinValOffSetX = StringVar(root)
    spinValOffSetY = StringVar(root)
    spinValOffSetW = StringVar(root)
    spinValOffSetH = StringVar(root)

    validateDigits = (root.register(validateSpinBox), '%P')

    spinnerOffSetX = Spinbox(secondFrameContent2, from_=-100000, to=100000, width=20, textvariable=spinValOffSetX)
    spinnerOffSetX.configure(validate='key', validatecommand=validateDigits)
    spinnerOffSetY = Spinbox(secondFrameContent3, from_=-100000, to=100000, width=20, textvariable=spinValOffSetY)
    spinnerOffSetY.configure(validate='key', validatecommand=validateDigits)
    spinnerOffSetW = Spinbox(secondFrameContent2, from_=-100000, to=100000, width=20, textvariable=spinValOffSetW)
    spinnerOffSetW.configure(validate='key', validatecommand=validateDigits)
    spinnerOffSetH = Spinbox(secondFrameContent3, from_=-100000, to=100000, width=20, textvariable=spinValOffSetH)
    spinnerOffSetH.configure(validate='key', validatecommand=validateDigits)

    buttonCheckMonitorLayout = Button(secondFrameContent4, text="Click to get A Screenshot of How The Program See Your Monitor", command=screenShotAndOpenLayout)

    # Third frame
    langOpt = optGoogle

    CBDefaultEngine = ttk.Combobox(thirdFrameContent, values=engines, state="readonly")
    CBDefaultFrom = ttk.Combobox(thirdFrameContent, values=langOpt, state="readonly")
    CBDefaultTo = ttk.Combobox(thirdFrameContent, values=langOpt, state="readonly")
    labelDefaultEngine = Label(thirdFrameContent, text="Default Engine :")
    labelDefaultFrom = Label(thirdFrameContent, text="Default From :")
    labelDefaultTo = Label(thirdFrameContent, text="Default To :")

    # Fourth frame
    labelTesseractPath = Label(fourthFrameContent, text="Tesseract Path :")
    textBoxTesseractPath = Text(fourthFrameContent, width=77, height=1, xscrollcommand=True)

    # Bottom Frame
    btnSave = Button(bottomFrame, text="Save Settings", command=saveSettings)

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root.title("Setting")
        self.root.geometry("727x420") # When you see it
        self.root.wm_attributes('-topmost', False) # Default False
        self.root.wm_withdraw()

        # TL CB
        # Init element
        # 1
        self.checkBTNAutoCopy.pack(side=LEFT, padx=5, pady=5)
        self.checkBTNCache.pack(side=LEFT, padx=5, pady=5)
        self.btnOpenCacheFolder.pack(side=LEFT, padx=5, pady=5)

        # 2
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

        # 3
        self.labelDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultEngine.bind("<<ComboboxSelected>>", self.CBTLChange_setting)

        self.labelDefaultFrom.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelDefaultTo.pack(side=LEFT, padx=5, pady=5)
        self.CBDefaultTo.pack(side=LEFT, padx=5, pady=5)
        
        # 4
        self.labelTesseractPath.pack(side=LEFT, padx=5, pady=5)
        self.textBoxTesseractPath.pack(side=LEFT, padx=5, pady=5, fill=X, expand=True)

        # Bottom Frame
        self.btnSave.pack(side=RIGHT, padx=4, pady=5)
        btnReset = Button(self.bottomFrame, text="Reset To Currently Stored Setting", command=self.reset)
        btnReset.pack(side=RIGHT, padx=5, pady=5)  
        btnRestoreDefault = Button(self.bottomFrame, text="Restore Default", command=self.restoreDefault)
        btnRestoreDefault.pack(side=RIGHT, padx=5, pady=5)
        
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

# ----------------------------------------------------------------
# Get Deepl TL
async def getDeeplTl(text, langTo, langFrom, TBottom):
    """Get the translated text from deepl.com"""

    isSuccess, translateResult = await tl_deepl.deepl_tl(text, langTo, langFrom)
    if(isSuccess):
        TBottom.delete(1.0, END)
        TBottom.insert(1.0, translateResult)
        # Write to History
        new_data = {
            "from": langFrom,
            "to": langTo,
            "query": text,
            "result": translateResult,
            "engine": "deepl"
        }
        fJson.writeAdd_History(new_data)
    else:
        Mbox("Error: Translation Failed", translateResult, 2)

# ----------------------------------------------------------------------
class main_Menu():
    """Main Menu Window"""
    # --- Functions ---
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
            Mbox("Error: Language target is the same as source", "Please choose a different language", 2)
            print("Error Language is the same as source! Please choose a different language")
            return
        if langToObj.get() == "Auto-Detect" or langToObj.current() == 0:
            Mbox("Error: Invalid Language Selected", "Please choose a valid language", 2)
            print("Error: Invalid Language Selected! Please choose a valid language")
            return

        # Get the text from the textbox
        if textOutside == "":
            text = self.textBoxTop.get(1.0, END)
        else:
            text = textOutside

        if(len(text) < 2):
            Mbox("Error: No text entered", "Please enter some text", 2)
            print("Error: No text entered! Please enter some text")
            return

        # Translate
        # --------------------------------
        # Google Translate
        if engine == "Google Translate":
            isSuccess, translateResult = tl.google_tl(text, langTo, langFrom)
            if(isSuccess):
                TBBot.delete(1.0, END)
                TBBot.insert(1.0, translateResult)

                # Write to History
                new_data = {
                    "from": langFrom,
                    "to": langTo,
                    "query": text,
                    "result": translateResult,
                    "engine": engine
                }
                fJson.writeAdd_History(new_data)
            else:
                Mbox("Error: Translation Failed", translateResult, 2)
        # --------------------------------
        # Deepl
        elif engine == "Deepl":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(getDeeplTl(text, langTo, langFrom, TBBot))
        # --------------------------------
        # MyMemoryTranslator
        elif engine == "MyMemoryTranslator":
            isSuccess, translateResult = tl.memory_tl(text, langTo, langFrom)
            if(isSuccess):
                TBBot.delete(1.0, END)
                TBBot.insert(1.0, translateResult)

                # Write to History
                new_data = {
                    "from": langFrom,
                    "to": langTo,
                    "query": text,
                    "result": translateResult,
                    "engine": engine
                }
                fJson.writeAdd_History(new_data)
            else:
                Mbox("Error: Translation Failed", translateResult, 2)
        # --------------------------------
        # PONS
        elif engine == "PONS":
            isSuccess, translateResult = tl.pons_tl(text, langTo, langFrom)
            if(isSuccess):
                TBBot.delete(1.0, END)
                TBBot.insert(1.0, translateResult)

                # Write to History
                new_data = {
                    "from": langFrom,
                    "to": langTo,
                    "query": text,
                    "result": translateResult,
                    "engine": engine
                }
                fJson.writeAdd_History(new_data)
            else:
                Mbox("Error: Translation Failed", translateResult, 2)
        # --------------------------------
        # Wrong opts
        else:
            print("Please select a correct engine")
            Mbox("Error: Engine Not Set!", "Please Please select a correct engine", 2)

    # On Close
    def on_closing(self):
        exit(0)
    
    # Open History Window
    def open_Setting(self):
        self.setting_UI.show()
    
    def open_History(self):
        self.history.show()
        pass

    def open_About(self):
        Mbox("About", "Screen-Translate is a program made inspired by VNR, Visual Novel OCR, and QTranslate.\n\nI (Dadangdut33) made this program in order to learn more about python and because i want to try creating an app similar to those i mention. " + 
        "\n\nThis program is completely open source, you can improve it if you want, you can also tell me if there are bugs. If you are confused on how to use it you can" + 
        " check the tutorial by pressing the tutorial in the menu bar", 0)

    def open_Tutorial(self):
        Mbox("Tutorial", "1. *First*, make sure your screen scaling is 100%. If scaling is not 100%, the capturer won't work properly. If by any chance you don't want to set your monitor scaling to 100%, " + 
        "you can set the xy offset in the setting" + "\n\n2. *Second*, you need to install tesseract, you can quickly go to the download link by pressing the download tesseract in menu bar\n\n" + 
        "3. *Then*, check the settings. Make sure tesseract path is correct\n\n" + 
        "4. *FOR MULTI MONITOR USER*, set offset in setting. If you have multiple monitor setup, you might need to set the offset in settings. \n\nWhat you shold do in the setting window:\n- Check how the program see your monitors in settings by clicking that one button.\n" + 
        "- You can also see how the capture area captured your images by enabling cache and then see the image in 'img_cache' directory" + 
        "\n\n\nYou can open the tutorial or user manual linked in menubar if you are still confused.", 0)

    def open_Faq(self):
        Mbox("FAQ", "Q: Do you collect the screenshot?\nA: No, no data is collected by me. Image and text captured will only be use for query and the cache is only saved locally\n\n" + 
        "Q: Is this safe?\nA: Yes, it is safe, you can check the code on the github linked, or open it yourself on your machine.\n\n" + 
        "Q: I could not capture anything, help!?\nA: You might need to check the cache image and see wether it actually capture the stuff that you targeted or not. If not, you might " + 
        "want to set offset in setting or change your monitor scaling to 100%", 0)

    def openTesLink(self):
        Mbox("Info", "Please download the v5.0.0-alpha.20210811 Version and install all language pack", 0)
        print("Please download the v5.0.0-alpha.20210811 Version and install all language pack")
        OpenUrl("https://github.com/UB-Mannheim/tesseract/wiki")

    def open_KnownBugs(self):
        Mbox("Known Bugs", "- Monitor scaling needs to be 100% or it won't capture accurately\n\n- The auto offset is wrong if the resolution between monitor 1 and 2 is not the same. It's because the auto offset calculate only the primary monitor. In this case you have to set the offset manually.", 0)

    def open_UserManual(self):
        try:
            startfile(dir_path + r"\user_manual")
        except:
            OpenUrl("https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual")

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

    def cbTLChange(self, event = ""):
        # In Main
        # Get the engine from the combobox
        curr_Engine = self.CBTranslateEngine.get()
        previous_From = self.CBLangFrom.get()
        previous_To = self.CBLangTo.get()

        # Translate
        if curr_Engine == "Google Translate":
            self.langOpt = optGoogle
            self.CBLangFrom['values'] = optGoogle
            self.CBLangFrom.current(searchList(previous_From, optGoogle))
            self.CBLangTo['values'] = optGoogle
            self.CBLangTo.current(searchList(previous_To, optGoogle))
        elif curr_Engine == "Deepl":
            self.langOpt = optDeepl
            self.CBLangFrom['values'] = optDeepl
            self.CBLangFrom.current(searchList(previous_From, optDeepl))
            self.CBLangTo['values'] = optDeepl
            self.CBLangTo.current(searchList(previous_To, optDeepl))
        elif curr_Engine == "MyMemoryTranslator":
            self.langOpt = optMyMemory
            self.CBLangFrom['values'] = optMyMemory
            self.CBLangFrom.current(searchList(previous_From, optMyMemory))
            self.CBLangTo['values'] = optMyMemory
            self.CBLangTo.current(searchList(previous_To, optMyMemory))
        elif curr_Engine == "PONS":
            self.langOpt = optPons
            self.CBLangFrom['values'] = optPons
            self.CBLangFrom.current(searchList(previous_From, optPons))
            self.CBLangTo['values'] = optPons
            self.CBLangTo.current(searchList(previous_To, optPons))


    # --- Declarations and Layout ---
    # Call the other frame
    capture_UI = CaptureUI()
    setting_UI = SettingUI()
    history = HistoryUI()

    root = Tk()
    alwaysOnTop = False
    capUiHidden = True

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

    # Langoptions onstart
    langOpt = optGoogle 

    labelEngines = Label(bottomFrame1, text="TL Engine:")
    CBTranslateEngine = ttk.Combobox(bottomFrame1, values=engines, state="readonly")

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

    # ----------------------------------------------------------------------
    def __init__(self):
        # ----------------------------------------------
        # Debug console info
        console()

        # ----------------------------------------------
        self.root.title("Screen Translate")
        self.root.geometry("900x300")
        self.root.wm_attributes('-topmost', False) # Default False
        tStatus, settings = fJson.readSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings[0] == "Setting file is not found":
                # Show error
                print("Error: " + settings[0])
                print(settings[1])
                Mbox("Error: " + settings[0], settings[1], 2)

                # Set setting value to default, so program can run
                settings = fJson.default_Setting

                # Set Default
                var1, var2 = fJson.setDefault()
                if var1 : # If successfully set default
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 0)
                else: # If error
                    print("Error: " + var2)
                    Mbox("An Error Occured", var2, 2)

        # Menubar
        def always_on_top():
            if self.alwaysOnTop:
                self.root.wm_attributes('-topmost', False)
                self.alwaysOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.alwaysOnTop = True

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Always on Top", command=always_on_top)
        filemenu.add_separator()
        filemenu.add_command(label="Exit Application", command=self.root.quit)
        menubar.add_cascade(label="Options", menu=filemenu)

        filemenu2 = Menu(menubar, tearoff=0)
        filemenu2.add_command(label="History", command=self.open_History) # Open History Window
        filemenu2.add_command(label="Setting", command=self.open_Setting) # Open Setting Window
        filemenu2.add_command(label="Cache", command=lambda: startfile(dir_path + r"\resource\img_cache")) # Open Setting Window
        menubar.add_cascade(label="View", menu=filemenu2)

        filemenu3 = Menu(menubar, tearoff=0)
        filemenu3.add_command(label="Capture Window", command=self.open_capture_screen) # Open Capture Screen Window
        menubar.add_cascade(label="Generate", menu=filemenu3)

        filemenu4 = Menu(menubar, tearoff=0)
        filemenu4.add_command(label="Tutorial", command=self.open_Tutorial) # Open Mbox Tutorials
        filemenu4.add_command(label="FAQ", command=self.open_Faq) # Open FAQ
        filemenu4.add_command(label="Known Bugs", command=self.open_KnownBugs) # Open Knownbugs
        filemenu4.add_command(label="About", command=self.open_About) # Open Mbox About
        filemenu4.add_separator()
        filemenu4.add_command(label="Open User Manual", command=self.open_UserManual) # Open Mbox Tutorials
        filemenu4.add_command(label="Open GitHub Repo", command=lambda aurl="https://github.com/Dadangdut33/Screen-Translate":OpenUrl(aurl)) # Open Mbox Tutorials
        filemenu4.add_command(label="Download Tesseract", command=self.openTesLink) # Open Mbox Tutorials
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

        # bottomFrame1
        self.labelEngines.pack(side=LEFT, padx=5, pady=5)
        self.CBTranslateEngine.current(searchList(settings['default_Engine'], engines))
        self.CBTranslateEngine.pack(side=LEFT, padx=5, pady=5)
        self.CBTranslateEngine.bind("<<ComboboxSelected>>", self.cbTLChange)

        self.cbTLChange() # Update the cb

        self.labelLangFrom.pack(side=LEFT, padx=5, pady=5)
        self.CBLangFrom.current(searchList(settings['default_FromOnOpen'], self.langOpt))
        self.CBLangFrom.pack(side=LEFT, padx=5, pady=5)

        self.labelLangTo.pack(side=LEFT, padx=5, pady=5)
        self.CBLangTo.current(searchList(settings['default_ToOnOpen'], self.langOpt)) # Default to English
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

        # Check setting on startup
        self.setting_UI.reset() # Reset

# ----------------------------------------------------------------
# main function
def main():
    main_Menu()
    main_Menu.root.mainloop()

if __name__ == '__main__':
    main()