from tkinter import *
from tkinter import ttk, colorchooser

from screen_translate.Mbox import Mbox
from screen_translate.Public import fJson, CreateToolTip

# Classes
class MaskingUI():
    """Mask Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Mask Window')
        self.root.geometry('600x160')
        self.root.wm_withdraw()
        self.root.overrideredirect(False)

        settings = fJson.readSetting()

        self.root.config(background=settings['Masking_Window']['color'])
        self.root.attributes('-alpha', settings['Masking_Window']['alpha'])
        self.currentOpacity = settings['Masking_Window']['alpha']

        # Top frame
        self.topFrame = Frame(self.root, background=settings['Masking_Window']['color'])
        self.topFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.visibleFrame = Frame(self.topFrame, background=settings['Masking_Window']['color'])
        self.visibleFrame.pack(side=TOP, fill=X, expand=False)

        self.behindSettingFrame = Frame(self.topFrame)
        self.behindSettingFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.settingFrame = Frame(self.behindSettingFrame)
        self.settingFrame.pack(side=TOP, fill=X, expand=False)

        self.settingFrame_2 = Frame(self.settingFrame)
        self.settingFrame_2.pack(side=TOP, fill=X, expand=False)

        # Label for the visible frame
        self.visibleFrameLabel = Label(self.visibleFrame, text="▶", font=("Arial", 16, "bold"), background=settings['Masking_Window']['color'], foreground="gray")
        self.visibleFrameLabel.pack(side=LEFT, fill=X, expand=False)
        self.visibleFrameLabel.bind("<Button-1>", self.toggle_Setting)
        CreateToolTip(self.visibleFrameLabel, "Show/Hide Setting")

        # Always on top checkbox
        self.alwaysOnTopVar = BooleanVar(self.root)
        self.alwaysOnTopVar.set(True)
        self.root.wm_attributes('-topmost', True)

        # Top hidden
        self.topHiddenVar = BooleanVar(self.root)
        self.topHiddenVar.set(False)
        self.root.wm_attributes('-topmost', True)

        # Show window setting
        self.showSetting = BooleanVar(self.root)
        self.showSetting.set(False)

        # Setting frame
        # Label for opacity slider
        self.opacityLabel = Label(self.settingFrame_2, text="Opacity: " + str(self.currentOpacity))
        self.opacityLabel.pack(padx=5, pady=5, side=LEFT)

        # Opacity slider
        self.opacitySlider = ttk.Scale(self.settingFrame_2, from_=0.0, to=1.0, orient=HORIZONTAL, length=150, command=self.sliderOpac, variable=self.currentOpacity)
        self.opacitySlider.set(self.currentOpacity)
        self.opacitySlider.pack(padx=5, pady=5, side=LEFT)

        # Reset button
        self.resetDefaultButton = ttk.Button(self.settingFrame_2, text="Reset to Default", command=self.reset_Default)
        self.resetDefaultButton.pack(padx=5, pady=5, side=LEFT)

        self.reset_To_Current_Button = ttk.Button(self.settingFrame_2, text="Reset to Current", command=self.reset_To_Current)
        self.reset_To_Current_Button.pack(padx=5, pady=5, side=LEFT)

        # Hint label
        self.hintLabel = Label(self.settingFrame_2, text="❓")
        self.hintLabel.pack(padx=5, pady=5, side=LEFT)
        CreateToolTip(self.hintLabel, "Changes you made here will not be saved unless you save it in the setting menu")

        # Textbox bg color Label
        self.windowColorVar = StringVar(self.root)
        self.windowColorVar.set(settings['Masking_Window']['color'])
        self.windowColorLabel = Label(self.settingFrame, text="Color : " + self.windowColorVar.get())
        self.windowColorLabel.pack(padx=5, pady=5, side=LEFT)
        self.windowColorLabel.bind("<Button-1>", self.windowColorChooser)
        CreateToolTip(self.windowColorLabel, "Click to change window color")

        # Button always on top
        self.alwaysOnTopButton = ttk.Checkbutton(self.settingFrame, variable=self.alwaysOnTopVar, text="Always on top", command=self.always_on_top)
        self.alwaysOnTopButton.pack(padx=5, pady=5, side=LEFT)

        # Button show/hide
        self.showButton = ttk.Checkbutton(self.settingFrame, variable=self.topHiddenVar, text="Hide Top (F12)", command=self.show_top)
        self.showButton.pack(padx=5, pady=5, side=LEFT)
        self.root.bind("<F12>", self.show_top)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.behindSettingFrame.pack_forget()
        self.showSetting.set(False)

    # show/hide top
    def show_top(self, event=None):
        if self.root.wm_overrideredirect():
            self.root.overrideredirect(False)
            self.topHiddenVar.set(False)
        else:
            self.root.overrideredirect(True)
            self.topHiddenVar.set(True)
            
    # Stay on top
    def always_on_top(self):
        if self.alwaysOnTopVar.get():
            self.root.wm_attributes('-topmost', True)
        else:
            self.root.wm_attributes('-topmost', False)

    # Show/Hide
    def show(self):
        self.root.attributes('-alpha', 0.8)
        self.opacitySlider.set(0.8)
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))

    # hide / show setting
    def toggle_Setting(self, event=None):
        if self.showSetting.get():
            self.behindSettingFrame.pack_forget()
            self.showSetting.set(False)
            self.visibleFrameLabel.config(text="▶")
        else:
            self.behindSettingFrame.pack(side=TOP, fill=BOTH, expand=True)
            self.showSetting.set(True)
            self.visibleFrameLabel.config(text="▼")

    def colorChange(self, color):
        self.root.configure(background=color)
        self.topFrame.configure(background=color)
        self.visibleFrame.configure(background=color)
        self.visibleFrameLabel.config(background=color)
        
    # Reset
    def reset_Default(self):
        """
        Show/Hide setting frame
        """
        # Ask for confirmation first
        if Mbox("Reset Default", "Are you sure you want to reset to default settings?", 3, parent=self.root):
            self.root.attributes('-alpha', 0.8)

            self.sliderOpac(0.8)
            self.windowColorVar.set(0.8)
            self.windowColorLabel.config(text="Color : #555555")
            self.colorChange("#555555")

    def reset_To_Current(self):
        """
        Reset to currently stored settings
        """
        # Ask for confirmation first
        if Mbox("Reset To Currently Saved", "Are you sure you want to reset to currently saved settings?", 3, parent=self.root):
            self.root.attributes('-alpha', 0.8)
            settings = fJson.readSetting()

            self.sliderOpac(settings['Masking_Window']['opacity'])
            self.windowColorVar.set(settings['Masking_Window']['color'])
            self.windowColorLabel.config(text="Color : " + self.windowColorVar.get())
            self.colorChange(self.windowColorVar.get())

    # Bg Color chooser
    def windowColorChooser(self, event=None):
        """window color chooser

        Args:
            event : Ignored. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=self.windowColorVar.get(), title="Choose a color")
        if colorGet[1] != None:
            self.windowColorVar.set(colorGet[1])
            self.windowColorLabel.config(text="Color : " + self.windowColorVar.get())
            self.root.config(background=self.windowColorVar.get())