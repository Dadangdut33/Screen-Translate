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
from screen_translate.ui.About import AboutUI
from screen_translate.ui.Tl_From import Detached_Tl_Query
from screen_translate.ui.Tl_Result import Detached_Tl_Result

# ----------------------------------------------------------------
# Paths
dir_path = os.path.dirname(os.path.realpath(__file__))
dir_img_captured = dir_path + r"\img_captured"
dir_logo = dir_path + "/logo.ico"
globalStuff.logoPath = dir_logo.replace(".ico", ".png")

# ----------------------------------------------------------------
""" For future features
TODO: 
- Add more OCR options
- Add tl result window setting (color, background, font, etc)
- Change the layout of settings window, divide panel for some category
- Add disable history in setting
- Find better way to use the hotkey instead of checking it every 100ms
"""

# ----------------------------------------------------------------
def console():
    print("=" * 80)
    print("--- Welcome to Screen Translate ---")
    print(">> Use The GUI Window to start capturing and translating")
    print(">> You can minimize this window")
    print(">> This window is for debugging purposes")

# ----------------------------------------------------------------------
class main_Menu():
    """Main Menu Window"""
    def __init__(self):
        # ----------------------------------------------
        # Debug console info
        console()
        print(">> Checking app version")
        self.checkVersion(withPopup=False)

        # --- Declarations and Layout ---
        self.root = Tk()
        self.root.title("Screen Translate")
        self.root.geometry("900x300")
        self.root.wm_attributes('-topmost', False) # Default False
        self.alwaysOnTop = False
        globalStuff.capUiHidden = True
        globalStuff.main_Ui = self.root

        # --- Load settings ---
        tStatus, settings = fJson.loadSetting()
        if tStatus == False: # If error its probably file not found, thats why we only handle the file not found error
            if settings[0] == "Setting file is not found":
                # Show error
                print("Error: " + settings[0])
                print(settings[1])
                Mbox("Error: " + settings[0], settings[1], 2, self.root)

                # Set setting value to default, so program can run
                settings = fJson.default_Setting

                # Set Default (This time it writes the json file)
                var1, var2 = fJson.setDefault()
                if var1 : # If successfully set default
                    print("Default setting applied")
                    Mbox("Default setting applied", "Please change your tesseract location in setting if you didn't install tesseract on default C location", 0, self.root)
                else: # If error
                    print("Error: " + var2)
                    Mbox("An Error Occured", var2, 2, self.root)

        # ----------------------------------------------        
        # Call the other frame
        self.capture_UI = CaptureUI()
        self.setting_UI = SettingUI()
        self.history_UI = HistoryUI()
        self.about_UI = AboutUI()
        self.query_Detached_Window_UI = Detached_Tl_Query()
        self.result_Detached_Window_UI = Detached_Tl_Result()

        # Set hotkeyPressed as false
        globalStuff.hotkeyPressed = False

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
        self.captureOpacitySlider = ttk.Scale(self.topFrame1, from_=0.0, to=1.0, value=globalStuff.curCapOpacity, orient=HORIZONTAL, command=self.opacChange)
        globalStuff.captureSlider_Main = self.captureOpacitySlider

        self.captureOpacityLabel = Label(self.topFrame1, text="Capture UI Opacity: " + str(globalStuff.curCapOpacity))
        globalStuff.captureOpacityObject = self.captureOpacityLabel

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
        self.textBoxBottom = TextWithVar(self.bottomFrame2, textvariable=globalStuff.text_Box_Bottom_Var, height = 5, width = 100, font=("Segoe UI", 10), yscrollcommand=True)

        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", command=self.always_on_top)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit Application", command=self.on_closing)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        self.filemenu2 = Menu(self.menubar, tearoff=0)
        self.filemenu2.add_command(label="Setting", command=self.open_Setting, accelerator="F2") # Open Setting Window
        self.filemenu2.add_command(label="History", command=self.open_History, accelerator="F3") # Open History Window
        self.filemenu2.add_command(label="Captured", command=self.open_Img_Captured, accelerator="F4") # Open Captured img folder
        self.menubar.add_cascade(label="View", menu=self.filemenu2)

        self.filemenu3 = Menu(self.menubar, tearoff=0)
        self.filemenu3.add_command(label="Capture Window", command=self.open_Capture_Screen) # Open Capture Screen Window
        self.filemenu3.add_command(label="Query Box", command=self.open_Query_Box)
        self.filemenu3.add_command(label="Result Box", command=self.open_Result_Box)
        self.menubar.add_cascade(label="Generate", menu=self.filemenu3)

        self.filemenu4 = Menu(self.menubar, tearoff=0)
        self.filemenu4.add_command(label="Tesseract", command=self.openTesLink) # Open Tesseract Downloads
        self.filemenu4.add_command(label="Icon source", command=self.openIconSource)
        self.menubar.add_cascade(label="Get", menu=self.filemenu4)

        self.filemenu5 = Menu(self.menubar, tearoff=0)
        self.filemenu5.add_command(label="Tutorial", command=self.open_Tutorial) # Open Mbox Tutorials
        self.filemenu5.add_command(label="FAQ", command=self.open_Faq) # Open FAQ
        self.filemenu5.add_command(label="Known Bugs", command=self.open_KnownBugs) # Open Knownbugs
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Open User Manual", command=self.open_UserManual) # Open user manual folder
        self.filemenu5.add_command(label="Open GitHub Repo", command=lambda aurl="https://github.com/Dadangdut33/Screen-Translate":OpenUrl(aurl)) 
        self.filemenu5.add_command(label="Open Changelog", command=self.open_Changelog) 
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Check For Update", command=self.checkVersion) # Check version
        self.filemenu5.add_command(label="Contributor", command=self.open_Contributor) # Open Contributor
        self.filemenu5.add_command(label="About STL", command=self.open_About, accelerator="F1") # Open about frame
        self.menubar.add_cascade(label="Help", menu=self.filemenu5)

        # Add to self.root
        self.root.config(menu=self.menubar)
        self.root.bind("<F1>", self.open_About)
        self.root.bind("<F2>", self.open_Setting)
        self.root.bind("<F3>", self.open_History)
        self.root.bind("<F4>", self.open_Img_Captured)

        # topFrame1
        self.translateOnly_Btn = ttk.Button(self.topFrame1, text="Translate", command=globalStuff.translate)
        self.captureNTranslate_Btn = ttk.Button(self.topFrame1, text="Capture And Translate", command=self.capture_UI.getTextAndTranslate)
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
        self.clearBtn = ttk.Button(self.bottomFrame1, text="Clear", command=self.clearTB)
        self.swapBtn = ttk.Button(self.bottomFrame1, text="Swap", command=self.swapTl)
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
        # self.root.after(100, self.checkOpacityLabel) # This needs better solution? idk

        # --- Logo ---
        try:
            self.root.iconbitmap(dir_logo)
            self.setting_UI.root.iconbitmap(dir_logo)
            self.capture_UI.root.iconbitmap(dir_logo)
            self.history_UI.root.iconbitmap(dir_logo)
            self.about_UI.root.iconbitmap(dir_logo)
            self.query_Detached_Window_UI.root.iconbitmap(dir_logo)
            self.result_Detached_Window_UI.root.iconbitmap(dir_logo)
        except FileNotFoundError:
            print("Error loading icon: Logo not found!")
        except Exception as e:
            print("Error loading icon: " + str(e))

    # --- Functions ---
    # On Close
    def on_closing(self):
        """
        Confirmation on close
        """

        """ # This is not needed anymore
        if globalStuff.mboxOpen:
            Mbox("A message box is still opened", "Please close all message box first!", 0, self.root)
            return
        """

        # Confirmation on close
        if Mbox("Confirmation", "Are you sure you want to exit?", 3, self.root):
            self.root.destroy()
            exit()

    # Open Setting Window
    def open_Setting(self, event=None):
        self.setting_UI.show()
        
    # Open History Window
    def open_History(self, event=None):
        self.history_UI.show()

    # Open result box
    def open_Result_Box(self, event=None):
        self.result_Detached_Window_UI.show()

    # Open query box
    def open_Query_Box(self, event=None):
        self.query_Detached_Window_UI.show()

    # Open About Window
    def open_About(self, event=None):
        self.about_UI.show()

    # Open captured image folder
    def open_Img_Captured(self, event=None):
        startfile(dir_img_captured)

    # Hotkey
    def hotkeyPoll(self):
        if globalStuff.hotkeyPressed == True and globalStuff.capUiHidden == False:
            settings = fJson.readSetting()
            time.sleep(settings['capture_HotkeyDelay'] / 1000)
            self.capture_UI.getTextAndTranslate()
        globalStuff.hotkeyPressed = False
        self.root.after(100, self.hotkeyPoll)

    # Slider
    def opacChange(self, val):
        self.capture_UI.sliderOpac(val, "menu")

    # Menubar
    def always_on_top(self):
        if self.alwaysOnTop:
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTop = False
        else:
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTop = True

    # ---------------------------------
    # Mbox
    # Tutorials
    def open_Tutorial(self):
        Mbox("Tutorial", "1. *First*, make sure your screen scaling is 100%. If scaling is not 100%, the capturer won't work properly. If by any chance you don't want to set your monitor scaling to 100%, " +
        "you can set the xy offset in the setting" + "\n\n2. *Second*, you need to install tesseract, you can quickly go to the download link by pressing the download tesseract in menu bar\n\n" +
        "3. *Then*, check the settings. Make sure tesseract path is correct\n\n" +
        "4. *FOR MULTI MONITOR USER*, set offset in setting. If you have multiple monitor setup, you might need to set the offset in settings. \n\nWhat you shold do in the setting window:\n- Check how the program see your monitors in settings by clicking that one button.\n" +
        "- You can also see how the capture area captured your images by enabling save capture image in settingsand then see the image in 'img_captured' directory" +
        "\n\n\nYou can open the tutorial or user manual linked in menubar if you are still confused.", 0, self.root)

    # FAQ
    def open_Faq(self):
        Mbox("FAQ", "Q : Do you collect the screenshot?\nA : No, no data is collected by me. Image and text captured will only be use for query and the captured image is only saved locally\n\n" +
        "Q : Is this safe?\nA : Yes, it is safe, you can check the code on the github linked in the menubar, or open it yourself on your machine.\n\n" +
        "Q : I could not capture anything, help!?\nA : You might need to check the captured image and see wether it actually capture the stuff that you targeted or not. If not, you might " +
        "want to set offset in setting or change your monitor scaling to 100%", 0, self.root)

    # Download tesseract
    def openTesLink(self):
        Mbox("Info", "Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack", 0, self.root)
        print("Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack")
        OpenUrl("https://github.com/UB-Mannheim/tesseract/wiki")

    # Open icon source
    def openIconSource(self):
        OpenUrl("https://icons8.com/")

    # Open known bugs
    def open_KnownBugs(self):
        Mbox("Known Bugs", "- Monitor scaling needs to be 100% or it won't capture accurately\n\n- The auto offset is wrong if the resolution between monitor 1 and 2 is not the same. It's because the auto offset calculate only the primary monitor. In this case you have to set the offset manually.", 0, self.root)

    # Open user manual
    def open_UserManual(self):
        try:
            startfile(dir_path + r"\user_manual")
        except:
            OpenUrl("https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual")

    # Open contributor
    def open_Contributor(self):
        Mbox("Contributor", "Thanks to:\n1. Dadangdut33 (Author)\n2. Laggykiller (contributor)\n3. Mdika (contributor)", 0, self.root)

    # Open Capture Window
    def open_Capture_Screen(self):
        self.capture_UI.show()

    # Open changelog
    def open_Changelog(self):
        try:
            startfile(dir_path + r"\user_manual\changelog.txt")
        except:
            Mbox("Error", "Changelog file not found\n\nProgram will now try open the one in the repository instead of the local copy.", 0, self.root)
            try:
                OpenUrl("https://github.com/Dadangdut33/Screen-Translate/blob/main/user_manual/Changelog.txt")
            except Exception as e:
                print("Error: " + str(e))
                Mbox("Error", str(e), 0, self.root)

    # Check version
    def checkVersion(self, withPopup = True):
        try:
            version = requests.get("https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/version.txt").text
            # num_CurrentVersion = [int(i) for i in globalStuff.version.split('.')]
            # num_LatestVersion = [int(i) for i in version.split('.')]

            # If wip
            if globalStuff.versionType == "wip":
                globalStuff.newVerStatusCache = "Work in proggress"
                print(">> The current version that you are using is still in development.\n(+) Current Version : " + globalStuff.version + "\n(-) Latest Version  : " + version)
                if withPopup: Mbox("Your Version is newer than the latest version", "The current version that you are using is still in development.\n\nCurrent Version : " + globalStuff.version + "\nLatest Version  : " + version +
                    "\n\nThis build is probably still work in progress for further improvement", 0, self.root)

                return

            # If release
            if globalStuff.version != version:
                globalStuff.newVerStatusCache = "New version available!"
                print(">> A new version is available. Please update to the latest version.\n(-) Current Version : " + globalStuff.version + "\n(+) Latest Version  : " + version)
                if withPopup: 
                    Mbox("New Version Available", "A newer version is available. Please update to the latest version by going to the release section in the repository.\n\nCurrent Version : " + globalStuff.version + "\nLatest Version  : " + version, 0, self.root)
                    # Ask if user want to download the latest version or not
                    if Mbox("Download Latest Version", "Do you want to download the latest version?", 3, self.root):
                        OpenUrl("https://github.com/Dadangdut33/Screen-Translate/releases/latest")
            else:
                globalStuff.newVerStatusCache = "Version up to date!"
                print(">> You are using the latest version.\n(=) Current Version : " + globalStuff.version + "\n(=) Latest Version  : " + version)
                if withPopup: Mbox("Version Up to Date", "You are using the latest version.\nCurrent Version : " + globalStuff.version + "\nLatest Version  : " + version, 0, self.root)
        except Exception as e:
            print("Failed to check version!")
            print("Error: " + str(e))
            if withPopup: Mbox("Failed to check version!", "Failed to check version!\n\nError: " + str(e), 0, self.root)

    """
    # -----------------------------------------------------------------
    # Disabling and enabling widgets
    def disable_MainWin_Widgets(self):
        globalStuff.mboxOpen = True
        widget_Lists = self.root.winfo_children()

        menuBar = widget_Lists.pop() # Last element is the menubar
        for cat in range(1, len(menuBar.winfo_children()) + 1):
            self.menubar.entryconfigure(cat, state=DISABLED)
        
        for frames in widget_Lists:
            for child in frames.winfo_children():
                try:
                    child.configure(state='disabled')
                except Exception as e:
                    print("Error when disabling: " + str(e))

    # Enable widgets in main window
    def enable_MainWin_Widgets(self):
        widget_Lists = self.root.winfo_children()

        menuBar = widget_Lists.pop() # Last element is the menubar
        for cat in range(1, len(menuBar.winfo_children()) + 1):
            self.menubar.entryconfigure(cat, state=NORMAL)

        for frames in widget_Lists:
            for child in frames.winfo_children():
                try:
                    if (child.winfo_class() == 'TCombobox'):
                        child.configure(state='readonly')
                    else:
                        child.configure(state='normal')
                except Exception as e:
                    print("Error when enabling: " + str(e))

        globalStuff.mboxOpen = False
    """
    # -----------------------------------------------------------------
    # Widgets functions
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

if __name__ == '__main__':
    gui = main_Menu()
    gui.root.mainloop()