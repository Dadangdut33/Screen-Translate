import os
import keyboard
import time
from sys import exit
from tkinter import *
import tkinter.ttk as ttk
import requests

# ----------------------------------------------------------------
# Var and methods
from screen_translate.Public import TextWithVar, fJson, globalStuff
from screen_translate.Public import startfile, optGoogle, optDeepl, optMyMemory, optPons, optNone, engines, searchList, OpenUrl
from screen_translate.Mbox import Mbox

# ----------------------------------------------------------------
# UI
from screen_translate.ui.History import HistoryUI
from screen_translate.ui.Settings import SettingUI
from screen_translate.ui.Capture_Window import CaptureUI

# Get dir path
dir_path = os.path.dirname(os.path.realpath(__file__))

# ----------------------------------------------------------------
def console():
    print("-" * 80)
    print("Welcome to Screen Translate")
    print("Use The GUI Window to start capturing and translating")
    print("This window is for debugging purposes")

# ----------------------------------------------------------------------
class main_Menu():
    """Main Menu Window"""
    def __init__(self):
        # ----------------------------------------------
        # Debug console info
        console()

        # --- Declarations and Layout ---
        self.root = Tk()
        self.root.title("Screen Translate")
        self.root.geometry("900x300")
        self.root.wm_attributes('-topmost', False) # Default False
        self.alwaysOnTop = False
        self.capUiHidden = True

        # --- Load settings ---
        tStatus, settings = fJson.loadSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings[0] == "Setting file is not found":
                # Show error
                print("Error: " + settings[0])
                print(settings[1])
                Mbox("Error: " + settings[0], settings[1], 2)

                # Set setting value to default, so program can run
                settings = fJson.default_Setting

                # Set Default (This time it writes the json file)
                var1, var2 = fJson.setDefault()
                if var1 : # If successfully set default
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 0)
                else: # If error
                    print("Error: " + var2)
                    Mbox("An Error Occured", var2, 2)

        # ----------------------------------------------        
        # Call the other frame
        self.capture_UI = CaptureUI()
        self.setting_UI = SettingUI()
        self.history = HistoryUI()

        # Frame
        self.topFrame1 = Frame(self.root)
        self.topFrame1.pack(side=TOP, fill=X, expand=False)

        self.topFrame2 = Frame(self.root)
        self.topFrame2.pack(side=TOP, fill=BOTH, expand=True)

        self.bottomFrame1 = Frame(self.root)
        self.bottomFrame1.pack(side=TOP, fill=X, expand=False)

        self.bottomFrame2 = Frame(self.root)
        self.bottomFrame2.pack(side=BOTTOM, fill=BOTH, expand=True)

        # Capture Opacity topFrame1
        self.captureOpacitySlider = ttk.Scale(self.topFrame1, from_=0.0, to=1.0, value=globalStuff.curCapOpacity, orient=HORIZONTAL, command=self.capture_UI.sliderOpac)
        print(globalStuff.captureOpacityLabel_Var.get())
        self.captureOpacityLabel = Label(self.topFrame1, text=globalStuff.captureOpacityLabel_Var.get())
        # self.captureOpacityLabel = Label(self.topFrame1, text="Capture Opacity: " + str(globalStuff.curCapOpacity))

        # Langoptions onstart
        self.langOpt = optGoogle

        self.labelEngines = Label(self.bottomFrame1, text="TL Engine:")
        self.CBTranslateEngine = ttk.Combobox(self.bottomFrame1, values=engines, state="readonly")

        self.labelLangFrom = Label(self.bottomFrame1, text="From:")
        self.CBLangFrom = ttk.Combobox(self.bottomFrame1, values=self.langOpt, state="readonly")

        self.labelLangTo = Label(self.bottomFrame1, text="To:")
        self.CBLangTo = ttk.Combobox(self.bottomFrame1, values=self.langOpt, state="readonly")

        self.translateOnly_Btn = Button()
        self.captureNTranslate_Btn = Button()
        self.clearBtn = Button()
        self.swapBtn = Button()

        # Translation Textbox topFrame2 & bottomFrame2
        self.textBoxTop = TextWithVar(self.topFrame2, textvariable=globalStuff.text_Box_Top_Var, height = 4, width = 100, font=("Segoe UI", 10), yscrollcommand=True)
        self.textBoxBottom = TextWithVar(self.bottomFrame2, textvariable=globalStuff.text_Box_Bottom_Var, borderwidth=1,  height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True)

        globalStuff.hotkeyPressed = False

        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", command=self.always_on_top)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit Application", command=self.root.quit)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        self.filemenu2 = Menu(self.menubar, tearoff=0)
        self.filemenu2.add_command(label="History", command=self.open_History) # Open History Window
        self.filemenu2.add_command(label="Setting", command=self.open_Setting) # Open Setting Window
        self.filemenu2.add_command(label="Captured", command=lambda: startfile(dir_path + r"\img_captured")) # Open Captured img folder
        self.menubar.add_cascade(label="View", menu=self.filemenu2)

        self.filemenu3 = Menu(self.menubar, tearoff=0)
        self.filemenu3.add_command(label="Capture Window", command=self.open_capture_screen) # Open Capture Screen Window
        self.menubar.add_cascade(label="Generate", menu=self.filemenu3)

        self.filemenu4 = Menu(self.menubar, tearoff=0)
        self.filemenu4.add_command(label="Tutorial", command=self.open_Tutorial) # Open Mbox Tutorials
        self.filemenu4.add_command(label="FAQ", command=self.open_Faq) # Open FAQ
        self.filemenu4.add_command(label="Known Bugs", command=self.open_KnownBugs) # Open Knownbugs
        self.filemenu4.add_command(label="About", command=self.open_About) # Open Mbox About
        self.filemenu4.add_command(label="Contributor", command=self.open_Contributor) # Open Contributor
        self.filemenu4.add_separator()
        self.filemenu4.add_command(label="Open User Manual", command=self.open_UserManual) # Open user manual folder
        self.filemenu4.add_command(label="Open GitHub Repo", command=lambda aurl="https://github.com/Dadangdut33/Screen-Translate":OpenUrl(aurl)) 
        self.filemenu4.add_command(label="Download Tesseract", command=self.openTesLink) # Open Mbox Downloads
        self.filemenu4.add_separator()
        self.filemenu4.add_command(label="Check Version", command=self.checkVersion) # Check version
        self.menubar.add_cascade(label="Help", menu=self.filemenu4)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # topFrame1
        self.translateOnly_Btn = Button(self.topFrame1, text="Translate", command=globalStuff.translate)
        self.captureNTranslate_Btn = Button(self.topFrame1, text="Capture And Translate", command=self.capture_UI.getTextAndTranslate)
        self.translateOnly_Btn.pack(side=LEFT, padx=5, pady=5)
        self.captureNTranslate_Btn.pack(side=LEFT, padx=5, pady=5)

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
        self.CBLangFrom.bind("<<ComboboxSelected>>", self.langChanged)

        self.labelLangTo.pack(side=LEFT, padx=5, pady=5)
        self.CBLangTo.current(searchList(settings['default_ToOnOpen'], self.langOpt)) # Default to English
        self.CBLangTo.pack(side=LEFT, padx=5, pady=5)
        self.CBLangTo.bind("<<ComboboxSelected>>", self.langChanged)

        # Button bottomFrame1
        self.clearBtn = Button(self.bottomFrame1, text="Clear", command=self.clearTB)
        self.swapBtn = Button(self.bottomFrame1, text="Swap", command=self.swapTl)
        self.swapBtn.pack(side=LEFT, padx=5, pady=5)
        self.clearBtn.pack(side=LEFT, padx=5, pady=5)

        # Translation Textbox topFrame2 bottomFrame
        self.textBoxTop.pack(padx=5, pady=5, fill=BOTH, expand=True)
        self.textBoxBottom.pack(padx=5, pady=5, fill=BOTH, expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Check setting again
        self.setting_UI.reset() # Reset

        # Bind hotkey
        if settings['capture_Hotkey'] != '':
            keyboard.add_hotkey(settings['capture_Hotkey'], globalStuff.hotkeyCallback)
        self.root.after(100, self.hotkeyPoll)
        self.langChanged() # Update the value in global var

        # Check opacityLabel
        self.root.after(100, self.checkOpacityLabel) # This needs better solution? idk


    # --- Functions ---
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
            OpenUrl("https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual")\

    def checkVersion(self):
        try:
            version = requests.get("https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/version_Release.txt").text
            print("Current Version : " + globalStuff.version)
            print("Latest Version  : " + version)
            print(version == globalStuff.version)
            if version != globalStuff.version:
                Mbox("New Version Available", "New version is available, you can download it from the github page manually.", 0)
            elif version == globalStuff.version:
                Mbox("No Update", "You are using the latest version", 0)
            else:
                Mbox("Error", "Error checking version", 0)
        except Exception as e:
            print("Failed to check version!")
            print("Error: " + str(e))

    def open_Contributor(self):
        Mbox("Contributor", "Thanks to:\n1. Dadangdut33 (Author)\n2. Laggykiller (Contributor)", 0)

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

        # Change the value of the global var
        globalStuff.langFrom = self.CBLangFrom.get()
        globalStuff.langTo = self.CBLangTo.get()

    def langChanged(self, event = None):
        # Change the value of the global var
        globalStuff.langFrom = self.CBLangFrom.get()
        globalStuff.langTo = self.CBLangTo.get()

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

        globalStuff.engine = curr_Engine
        # Translate
        if curr_Engine == "Google Translate":
            self.langOpt = optGoogle
            self.CBLangFrom['values'] = optGoogle
            self.CBLangFrom.current(searchList(previous_From, optGoogle))
            self.CBLangTo['values'] = optGoogle
            self.CBLangTo.current(searchList(previous_To, optGoogle))
            self.CBLangTo.config(state='readonly')
        elif curr_Engine == "Deepl":
            self.langOpt = optDeepl
            self.CBLangFrom['values'] = optDeepl
            self.CBLangFrom.current(searchList(previous_From, optDeepl))
            self.CBLangTo['values'] = optDeepl
            self.CBLangTo.current(searchList(previous_To, optDeepl))
            self.CBLangTo.config(state='readonly')
        elif curr_Engine == "MyMemoryTranslator":
            self.langOpt = optMyMemory
            self.CBLangFrom['values'] = optMyMemory
            self.CBLangFrom.current(searchList(previous_From, optMyMemory))
            self.CBLangTo['values'] = optMyMemory
            self.CBLangTo.current(searchList(previous_To, optMyMemory))
            self.CBLangTo.config(state='readonly')
        elif curr_Engine == "PONS":
            self.langOpt = optPons
            self.CBLangFrom['values'] = optPons
            self.CBLangFrom.current(searchList(previous_From, optPons))
            self.CBLangTo['values'] = optPons
            self.CBLangTo.current(searchList(previous_To, optPons))
            self.CBLangTo.config(state='readonly')
        elif curr_Engine == "None":
            self.langOpt = optNone
            self.CBLangFrom['values'] = optNone
            self.CBLangFrom.current(searchList(previous_From, optNone))
            self.CBLangTo['values'] = optNone
            self.CBLangTo.current(searchList(previous_To, optNone))
            self.CBLangTo.config(state='disabled')

        # Change the value of the global var
        globalStuff.langFrom = self.CBLangFrom.get()
        globalStuff.langTo = self.CBLangTo.get()

    def hotkeyPoll(self):
        if globalStuff.hotkeyPressed == True and self.capUiHidden == False:
            settings = fJson.readSetting()
            time.sleep(settings['capture_HotkeyDelay'] / 1000)
            self.capture_UI.getTextAndTranslate()
        globalStuff.hotkeyPressed = False
        self.root.after(100, self.hotkeyPoll)

    def checkOpacityLabel(self):
        self.captureOpacityLabel.config(text = globalStuff.captureOpacityLabel_Var.get())
        self.root.after(100, self.checkOpacityLabel)

    # Menubar
    def always_on_top(self):
        if self.alwaysOnTop:
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTop = False
        else:
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTop = True

if __name__ == '__main__':
    gui = main_Menu()
    gui.root.mainloop()