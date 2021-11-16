# Internal
import tkinter as tk
import subprocess
import asyncio
import os
import time

# Ext
import webbrowser

# User Defined
from screen_translate.JsonHandling import JsonHandler
from screen_translate.LangCode import *
from screen_translate.Mbox import Mbox
from screeninfo import get_monitors

# ---------------------------------------------------------------
# Settings to capture all screens
from PIL import ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# Add try except to intercept connection error
try:
    from screen_translate.Translate import *
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

try:
    from screen_translate.Translate_Deepl import *
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

# ---------------------------------------------------------------
# --------------------- Public Classes --------------------------
# ---------------------------------------------------------------
class Global_Class: 
    """
    Class containing all the static variables for the UI. It also contains some methods
    for the stuff to works, such as the hotkey callback, the translate method, etc.
    
    Stored like this in order to allow other file to use the same thing without circular import error.
    """
    def __init__(self):
        # Create gimmick window to store global var
        self.gimmickWindow = tk.Tk()
        self.gimmickWindow.withdraw()

        # Reference main ui
        self.main = None
        self.main_Ui = None

        # Text box
        self.text_Box_Top_Var = tk.StringVar()
        self.text_Box_Bottom_Var = tk.StringVar()
        
        # Flag variables
        self.hotkeyCapTlPressed = False
        self.hotkeySnipCapTlPressed = False
        self.capUiHidden = True

        # Capture opacities
        self.curCapOpacity = 0.8
        self.captureSlider_Main = None
        self.captureSlider_Cap = None
        self.captureOpacityLabel_Main = None
        self.captureOpacityLabel_CapSetting = None

        # CB TL
        self.langTo = None
        self.langFrom = None # THis neeeds to change everytime the user changes the language and on innit
        self.engine = None
        self.mboxOpen = False
        
        # Version
        self.version = "1.8"
        self.versionType = "release"
        self.newVerStatusCache = None

        # Logo
        self.logoPath = None

        # Query box
        self.queryBg = None
        self.queryFg = None
        self.queryFont = None

        # Result box
        self.resultBg = None
        self.resultFg = None
        self.resultFont = None

    def hotkeyCapTLCallback(self):
        """Callback for the hotkey to capture the screen"""
        self.hotkeyCapTlPressed = True

    def hotkeySnipCapTLCallback(self):
        """Callback for the hotkey to snip the screen"""
        self.hotkeySnipCapTlPressed = True

    # Translate
    def translate(self):
        """Translate the text"""
        # Only check the langfrom and langto if it is translating
        if self.engine != "None":
            # If source and destination are the same
            if(self.langFrom) == (self.langTo):
                Mbox("Error: Language target is the same as source", "Please choose a different language", 2, self.main_Ui)
                print("Error Language is the same as source! Please choose a different language")
                return
            # If langto not set
            if self.langTo == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, self.main_Ui)
                print("Error: Invalid Language Selected! Must specify language destination")
                return

        # Get the text from the textbox
        query = self.text_Box_Top_Var.get()

        # Read settings
        try: 
            showAlert = fJson.readSetting()["show_no_text_alert"]
        except Exception as e:
            print("Error: Couldn't read show alert setting. Using default value")
            Mbox("Error: Could not read saveHistory setting", "Please do not edit Setting.json manually\n\n" + str(e), 2, self.main_Ui)
            showAlert = False

        # If the text is empty
        if(len(query) < 1):
            print("Error: No text entered! Please enter some text")
            # If show alert is true then show a message box alert, else dont show any popup
            if showAlert:
                Mbox("Error: No text entered", "Please enter some text", 2, self.main_Ui)
                
            return

        try:
            historyIsSaved = fJson.readSetting()['saveHistory']
        except Exception as e:
            print("Error: Could not read saveHistory setting", str(e))
            Mbox("Error: Could not read saveHistory setting", "Please do not edit Setting.json manually\n\n" + str(e), 2, self.main_Ui)
            historyIsSaved = True

        # Translate
        # --------------------------------
        # Google Translate
        if self.engine == "Google Translate":
            oldMethod = False
            if "- Alt" in self.langFrom or "- Alt" in self.langTo:
                oldMethod = True

            isSuccess, translateResult = google_tl(query, self.langTo, self.langFrom, oldMethod=oldMethod)
            self.fillTextBoxAndSaveHistory(isSuccess, query, translateResult, historyIsSaved)
        # --------------------------------
        # Deepl
        elif self.engine == "Deepl":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.getDeeplTl(query, self.langTo, self.langFrom, historyIsSaved))
        # --------------------------------
        # MyMemoryTranslator
        elif self.engine == "MyMemoryTranslator":
            isSuccess, translateResult = memory_tl(query, self.langTo, self.langFrom)
            self.fillTextBoxAndSaveHistory(isSuccess, query, translateResult, historyIsSaved)
        # --------------------------------
        # PONS
        elif self.engine == "PONS":
            isSuccess, translateResult = pons_tl(query, self.langTo, self.langFrom)
            self.fillTextBoxAndSaveHistory(isSuccess, query, translateResult, historyIsSaved)

        # --------------------------------
        # None
        elif self.engine == "None":
            pass
        # --------------------------------
        # Wrong opts
        else:
            print("Please select a correct engine")
            Mbox("Error: Engine Not Set!", "Please select a correct engine", 2, self.main_Ui)

    # Get Deepl TL
    async def getDeeplTl(self, text, langTo, langFrom, saveToHistory):
        """Get the translated text from deepl.com"""

        isSuccess, translateResult = await deepl_tl(text, langTo, langFrom)
        self.fillTextBoxAndSaveHistory(isSuccess, text, translateResult, saveToHistory)

    # Save to History
    def fillTextBoxAndSaveHistory(self, isSuccess, query, translateResult, saveToHistory):
        """Save the text to history"""
        if(isSuccess):
            self.text_Box_Bottom_Var.set(translateResult)
            if saveToHistory:
                # Write to History
                new_data = {
                    "from": self.langFrom,
                    "to": self.langTo,
                    "query": query,
                    "result": translateResult,
                    "engine": self.engine
                }
                fJson.writeAdd_History(new_data)
        else:
            Mbox("Error: Translation Failed", translateResult, 2, self.main_Ui)

    # Allowed keys
    def allowedKey(self, event):
        key = event.keysym

        # Allow 
        if key.lower() in ['left', 'right']: # Arrow left right
            return
        if (4 == event.state and key == 'a'): # Ctrl + a
            return
        if (4 == event.state and key == 'c'): # Ctrl + c
            return
        
        # If not allowed
        return "break"

# ---------------------------------------------------------------
"""
TextWithVar, taken from: https://stackoverflow.com/questions/21507178/tkinter-text-binding-a-variable-to-widget-text-contents
"""
class TextWithVar(tk.Text):
    '''A text widget that accepts a 'textvariable' option'''
    def __init__(self, parent, *args, **kwargs):
        try:
            self._textvariable = kwargs.pop("textvariable")
        except KeyError:
            self._textvariable = None

        tk.Text.__init__(self, parent, *args, **kwargs)

        # if the variable has data in it, use it to initialize
        # the widget
        if self._textvariable is not None:
            self.insert("1.0", self._textvariable.get())

        # this defines an internal proxy which generates a
        # virtual event whenever text is inserted or deleted
        self.tk.eval('''
            proc widget_proxy {widget widget_command args} {

                # call the real tk widget command with the real args
                set result [uplevel [linsert $args 0 $widget_command]]

                # if the contents changed, generate an event we can bind to
                if {([lindex $args 0] in {insert replace delete})} {
                    event generate $widget <<Change>> -when tail
                }
                # return the result from the real widget command
                return $result
            }
            ''')

        # this replaces the underlying widget with the proxy
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(self)))

        # set up a binding to update the variable whenever
        # the widget changes
        self.bind("<<Change>>", self._on_widget_change)

        # set up a trace to update the text widget when the
        # variable changes
        if self._textvariable is not None:
            self._textvariable.trace("wu", self._on_var_change)

    def _on_var_change(self, *args):
        '''Change the text widget when the associated textvariable changes'''

        # only change the widget if something actually
        # changed, otherwise we'll get into an endless
        # loop
        text_current = self.get("1.0", "end-1c")
        var_current = self._textvariable.get()
        if text_current != var_current:
            self.delete("1.0", "end")
            self.insert("1.0", var_current)

    def _on_widget_change(self, event=None):
        '''Change the variable when the widget changes'''
        if self._textvariable is not None:
            self._textvariable.set(self.get("1.0", "end-1c"))

# ---------------------------------------------------------------
# Tooltip
""" 
Original from: https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
"""

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info', delay=250, wraplength=180, opacity=1.0, always_on_top=True):
        self.waittime = delay     #miliseconds
        self.wraplength = wraplength   #pixels
        self.widget = widget
        self.text = text
        self.opacity = opacity
        self.always_on_top = always_on_top
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Make it stay on top
        self.tw.wm_attributes('-topmost', self.always_on_top)
        # Make it a little transparent
        self.tw.wm_attributes('-alpha', self.opacity)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

# ----------------------------------------------------------------
# Screen
class MonitorInfo:
    def __init__(self):
        self.mInfoCache = {
            "totalX": 0,
            "totalY": 0,
            "primaryIn": None,
            "mData": None,
            "layoutType": None
        }
        self.mInfoCache = self.getScreenInfo() # Fill the cache

    def getWidthAndHeight(self):
        # Better solution for this case on getting the width and height 
        # get_monitors() are not accurate sometimes
        img = ImageGrab.grab()
        totalX = img.size[0]
        totalY = img.size[1]

        return totalX, totalY

    def getScreenInfo(self):
        """
        Get the primary screen size.
        """
        mData = []
        index = 0
        primaryIn = 0
        layoutType = None
        for m in get_monitors():
            mData.append(m)
            if m.is_primary:
                primaryIn = index

            # print(m)
            index += 1

        if self.mInfoCache['mData'] != mData:
            totalX, totalY = self.getWidthAndHeight()
        else:
            totalX = self.mInfoCache['totalX']
            totalY = self.mInfoCache['totalY']

        if totalX > totalY:
            layoutType = "horizontal"
        else:
            layoutType = "vertical"

        self.mInfoCache = {
            "totalX": totalX,
            "totalY": totalY,
            "primaryIn": primaryIn,
            "mData": mData,
            "layoutType": layoutType
        }

        return self.mInfoCache

# ---------------------------------------------------------------
# --------------------- Public Functions ------------------------
# ---------------------------------------------------------------
def startfile(filename):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except Exception:
        subprocess.Popen(['xdg-open', filename])


def fillList(dictFrom, listTo, insertFirst="", insertSecond=""):
    """
    Fill a list with extra additonal items if provided. Then sort it.
    """
    for item in dictFrom:
        if item == "Auto-Detect":
            continue
        listTo += [item]

    listTo.sort()
    if insertFirst != "":
        listTo.insert(0, insertFirst)
    if insertSecond != "":
        listTo.insert(1, insertSecond)

def getTheOffset(custom=None):
    """
    Get the offset of the monitor.
    """
    settings = fJson.readSetting()

    offSetXY = settings["offSetXY"]
    offSetWH = settings["offSetWH"]
    xyOffSetType = settings["offSetXYType"]

    # If custom
    if custom is not None:
        offSetXY = ["auto", "auto"] # When custom is set, then offset auto will be checked automatically.

        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY, custom)
    else:  # if not
        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY)

    return offSets

def offSetSettings(widthHeighOff, xyOffsetType, xyOff, custom=None):
    """
    Calculate the offset settings for the monitor.
    """
    x, y, w, h = 0, 0, 0, 0

    w = 60 if widthHeighOff[0] == "auto" else widthHeighOff[0]
    h = 60 if widthHeighOff[1] == "auto" else widthHeighOff[1]

    #  If offset is set
    if xyOffsetType.lower() != "no offset" or custom is not None:
        totalMonitor = len(get_monitors())
        totalX = 0
        totalY = 0
        index = 0
        primaryIn = 0
        mData = []
        for m in get_monitors():
            mData.append(m)
            totalX += abs(m.x)
            totalY += abs(m.y)
            if m.is_primary:
                primaryIn = index
            index += 1

        # If auto
        if xyOff[0] == "auto":
            if totalMonitor > 1:
                if(totalX > totalY):  # Horizontal
                    if primaryIn != 0: # Make sure its not the first monitor
                        x = abs(mData[primaryIn - 1].x)
                    else:
                        x = 0
                else:
                    x = 0
            else:
                x = 0
        else:  # if set manually
            x = xyOff[0]

        # If auto
        if xyOff[1] == "auto":
            if totalMonitor > 1:
                if(totalY > totalX):  # Vertical
                    if primaryIn != 0:
                        y = abs(mData[primaryIn - 1].y)
                    else:
                        y = 0
                else:
                    y = 0
            else:
                y = 0
        else:  # if set manually
            y = xyOff[1]

    offSetsGet = [x, y, w, h]
    return offSetsGet

def OpenUrl(url):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        print("Error: Unable to open URL")
        print("Details" + str(e))

def searchList(searchFor, theList):
    """ Used for CB Changing
    Search for item in list, exist or not. If it exist return the index
    else return 0. 
    """
    index = 0
    found = False
    for lang in theList:
        if lang == searchFor:
            found = True
            break
        index += 1
    
    if found:
        return index
    else:
        return 0

# ----------------------------------------------------------------------
# --------------------------  Public Var  ------------------------------
# ----------------------------------------------------------------------
"""Getting all the public variables to be used in other classes/files"""
# Public var
engines = engineList
optGoogle = []
fillList(google_Lang, optGoogle, "Auto-Detect")
optDeepl = []
fillList(deepl_Lang, optDeepl, "Auto-Detect")
optMyMemory = []
fillList(myMemory_Lang, optMyMemory, "Auto-Detect")
optPons = []
fillList(pons_Lang, optPons)  # PONS HAVE NO AUTO DETECT
optNone = []
fillList(tesseract_Lang, optNone)

# Create an object for the classes needed here
fJson = JsonHandler()
_StoredGlobal = Global_Class()
mInfo = MonitorInfo()