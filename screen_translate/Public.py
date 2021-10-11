import tkinter as tk
import subprocess
import asyncio
import os
import pyautogui
import webbrowser
from .JsonHandling import JsonHandler
from .LangCode import *
from .Mbox import Mbox

# Add try except to intercept connection error
try:
    from .Translate import *
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

try:
    from .Translate_Deepl import *
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", e, 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", e, 2)

class global_Stuff: 
    def __init__(self):
        # Create gimmick window to store global var
        self.gimmickWindow = tk.Tk()
        self.gimmickWindow.withdraw()

        self.text_Box_Top_Var = tk.StringVar()
        self.text_Box_Bottom_Var = tk.StringVar()
        self.hotkeyPressed = False
        self.capUiHidden = False
        self.curCapOpacity = 0.8
        self.captureOpacityLabel_Var = tk.StringVar()
        self.captureOpacityLabel_Var.set("Capture UI Opacity: " + str(self.curCapOpacity))

        # CB TL
        self.langTo = None
        self.langFrom = None # THis neeeds to change everytime the user changes the language and on innit
        self.engine = None
        self.mboxOpen = False
        
        # Version
        self.version = "1.5.1"
        self.versionType = "wip"
        self.newVerStatusCache = None

        # Logo
        self.logoPath = None

    def hotkeyCallback(self):
        self.hotkeyPressed = True

        # Translate
    def translate(self):
        """Translate the text"""
        # Only check the langfrom and langto if it is translating
        if self.engine != "None":
            # If source and destination are the same
            if(self.langFrom) == (self.langTo):
                Mbox("Error: Language target is the same as source", "Please choose a different language", 2)
                print("Error Language is the same as source! Please choose a different language")
                return
            # If langto not set
            if self.langTo == "Auto-Detect":
                Mbox("Error: Invalid Language Selected", "Must specify language destination", 2)
                print("Error: Invalid Language Selected! Must specify language destination")
                return

        # Get the text from the textbox
        query = self.text_Box_Top_Var.get()

        if(len(query) < 1):
            Mbox("Error: No text entered", "Please enter some text", 2)
            print("Error: No text entered! Please enter some text")
            return

        # Translate
        # --------------------------------
        # Google Translate
        if self.engine == "Google Translate":
            isSuccess, translateResult = google_tl(query, self.langTo, self.langFrom)
            self.saveToHistory(isSuccess, query, translateResult)
        # --------------------------------
        # Deepl
        elif self.engine == "Deepl":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.getDeeplTl(query, self.langTo, self.langFrom))
        # --------------------------------
        # MyMemoryTranslator
        elif self.engine == "MyMemoryTranslator":
            isSuccess, translateResult = memory_tl(query, self.langTo, self.langFrom)
            self.saveToHistory(isSuccess, query, translateResult)
        # --------------------------------
        # PONS
        elif self.engine == "PONS":
            isSuccess, translateResult = pons_tl(query, self.langTo, self.langFrom)
            self.saveToHistory(isSuccess, query, translateResult)

        # --------------------------------
        # None
        elif self.engine == "None":
            pass
        # --------------------------------
        # Wrong opts
        else:
            print("Please select a correct engine")
            Mbox("Error: Engine Not Set!", "Please Please select a correct engine", 2)

    # Get Deepl TL
    async def getDeeplTl(self, text, langTo, langFrom):
        """Get the translated text from deepl.com"""

        isSuccess, translateResult = await deepl_tl(text, langTo, langFrom)
        self.saveToHistory(isSuccess, text, translateResult)

    # Save to History
    def saveToHistory(self, isSuccess, query, translateResult):
        """Save the text to history"""
        if(isSuccess):
            self.text_Box_Bottom_Var.set(translateResult)

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
            Mbox("Error: Translation Failed", translateResult, 2)

# ------------------------------
# TextWithVar, taken from: https://stackoverflow.com/questions/21507178/tkinter-text-binding-a-variable-to-widget-text-contents
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

""" tk_ToolTip_class101.py
gives a Tkinter widget a tooltip as the mouse is above the widget
tested with Python27 and Python34  by  vegaseat  09sep2014
www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter

Modified to include a delay time by Victor Zaccardo, 25mar16
"""

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 300     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
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

def startfile(filename):
    try:
        os.startfile(filename)
    except:
        subprocess.Popen(['xdg-open', filename])


def fillList(dictFrom, listTo, insertFirst="", insertSecond=""):
    for item in dictFrom:
        if item == "Auto-Detect":
            continue
        listTo += [item]

    listTo.sort()
    if insertFirst != "":
        listTo.insert(0, insertFirst)
    if insertSecond != "":
        listTo.insert(1, insertSecond)


def getTheOffset(custom=""):
    settings = fJson.readSetting()

    offSetXY = settings["offSetXY"]
    offSetWH = settings["offSetWH"]
    xyOffSetType = settings["offSetXYType"]

    # If custom
    if custom != "":
        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY, custom)
    else:  # if not
        offSets = offSetSettings(offSetWH, xyOffSetType, offSetXY)

    return offSets


def offSetSettings(widthHeighOff, xyOffsetType, xyOff, custom=""):
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
            if(offsetX > offsetY):  # Horizontal
                x = offsetX
            else:
                x = 0
        else:  # if set manually
            x = xyOff[0]

        # If auto
        if xyOff[1] == "auto":
            if(offsetY > offsetX):  # Vertical
                y = offsetY
            else:
                y = 0
        else:  # if set manually
            y = xyOff[1]

    offSetsGet.append(x)
    offSetsGet.append(y)
    offSetsGet.append(w)
    offSetsGet.append(h)
    return offSetsGet

def OpenUrl(url):
    try:
        webbrowser.open_new(url)
    except Exception as e:
        print("Error: Unable to open URL")
        print("Details" + str(e))

def searchList(searchFor, theList):
    index = 0
    for lang in theList:
        if lang == searchFor:
            return index
        index += 1
    else:
        return 0


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

# Create an object for the classes here
fJson = JsonHandler()
globalStuff = global_Stuff()