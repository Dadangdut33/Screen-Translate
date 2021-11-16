import json
from tkinter import *
from tkinter import ttk, colorchooser

from screen_translate.Mbox import Mbox
from screen_translate.Public import _StoredGlobal, TextWithVar, fJson, CreateToolTip
from tkfontchooser import askfont

# Classes
class Detached_Tl_Result():
    """Result TL Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('Translation Result')
        self.root.geometry('600x160')
        self.root.wm_withdraw()
        self.root.attributes('-alpha', 1)
        self.currentOpacity = 1.0

        settings = fJson.readSetting()

        # Top frame
        self.topFrame = Frame(self.root)
        self.topFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.tbFrame = Frame(self.topFrame)
        self.tbFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.settingFrame = Frame(self.topFrame)
        self.settingFrame.pack(side=TOP, fill=X, expand=False)

        self.settingFrame_2 = Frame(self.settingFrame)
        self.settingFrame_2.pack(side=TOP, fill=X, expand=False)

        # Always on top checkbox
        self.menubar = Menu(self.root)
        self.alwaysOnTopVar = BooleanVar()
        self.alwaysOnTopVar.set(True)

        # Top hidden
        self.topHiddenVar = BooleanVar()
        self.root.wm_attributes('-topmost', True)

        # Show window setting
        self.showSetting = BooleanVar()
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

        # Textbox bg color
        self.textboxBgColor = StringVar()
        self.textboxBgColor.set(settings['Result_Box']['bg'])
        _StoredGlobal.resultBg = self.textboxBgColor

        # Textbox fg color
        self.textboxFgColor = StringVar()
        self.textboxFgColor.set(settings['Result_Box']['fg'])
        _StoredGlobal.resultFg = self.textboxFgColor

        # Textbox bg color Label
        self.textboxBgColorLabel = Label(self.settingFrame, text="BG color: " + self.textboxBgColor.get())
        self.textboxBgColorLabel.pack(padx=5, pady=5, side=LEFT)
        self.textboxBgColorLabel.bind("<Button-1>", self.bgColorChooser)
        CreateToolTip(self.textboxBgColorLabel, "Click to change textbox background color")

        # Textbox fg color Label
        self.textboxFgColorLabel = Label(self.settingFrame, text="FG color: " + self.textboxFgColor.get())
        self.textboxFgColorLabel.pack(padx=5, pady=5, side=LEFT)
        self.textboxFgColorLabel.bind("<Button-1>", self.fgColorChooser)
        CreateToolTip(self.textboxFgColorLabel, "Click to change textbox foreground color")

        # textbox font label
        self.tbResultFont = StringVar()
        try:
            self.tbResultFont.set(settings['Result_Box']['font'])
            self.tbResultFontDict = json.loads(self.tbResultFont.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.tbResultFontDict
        except Exception as e:
            font_str = "Segoe UI 10 normal"
        _StoredGlobal.resultFont = self.tbResultFont
        
        self.tbFontLabel = Label(self.settingFrame, text="Font: " + font_str)
        self.tbFontLabel.pack(padx=5, pady=5, side=LEFT)
        self.tbFontLabel.bind("<Button-1>", self.fontChooser)
        CreateToolTip(self.tbFontLabel, "Click to change textbox font (Underline and strikethrough is ignored)")

        # Menu bar
        # Same method as in the capture window
        self.alwaysOnTopCheck_Hidden = Checkbutton(self.tbFrame, text="Stay on top", variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.alwaysOnTopCheck_Hidden.select()

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.alwaysOnTopVar, command=self.always_on_top)
        self.filemenu.add_checkbutton(label="Hide Top", onvalue=True, offvalue=False, variable=self.topHiddenVar, command=self.show_top)
        self.filemenu.add_checkbutton(label="Show Window Settings", onvalue=True, offvalue=False, variable=self.showSetting, command=self.toggle_Setting)
        self.menubar.add_cascade(label="Options", menu=self.filemenu)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # Textbox in topframe2
        self.textBoxTlResult = TextWithVar(self.tbFrame, textvariable=_StoredGlobal.text_Box_Bottom_Var, height = 5, width = 100, yscrollcommand=True, background=self.textboxBgColor.get())
        self.textBoxTlResult.bind("<Key>", lambda event: _StoredGlobal.allowedKey(event)) # Disable textbox input
        try:
            self.textBoxTlResult.config(font=(self.tbResultFontDict['family'], self.tbResultFontDict['size'], self.tbResultFontDict['weight'], self.tbResultFontDict['slant']))
        except Exception:
            self.textBoxTlResult.config(font=("Segoe UI", 10, "normal", "roman"))
        self.textBoxTlResult.pack(side=LEFT, fill=BOTH, expand=True)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.settingFrame.pack_forget()
        self.showSetting.set(False)

    # show/hide top
    def show_top(self):
        if self.topHiddenVar.get(): # IF ON THEN TURN IT OFF
            self.root.overrideredirect(False)
            self.topHiddenVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.overrideredirect(True)
            self.topHiddenVar.set(True)

    # Stay on top
    def always_on_top(self):
        if self.alwaysOnTopVar.get(): # IF ON THEN TURN IT OFF
            self.root.wm_attributes('-topmost', False)
            self.alwaysOnTopVar.set(False)
        else: # IF OFF THEN TURN IT ON
            self.root.wm_attributes('-topmost', True)
            self.alwaysOnTopVar.set(True)

    # Show/Hide
    def show(self):
        self.root.attributes('-alpha', 1)
        self.opacitySlider.set(1)
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Slider function
    def sliderOpac(self, x, from_=None):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))

        if from_ is not None:
            self.opacitySlider.set(x)

    # hide / show setting
    def toggle_Setting(self):
        """
        Show/Hide setting frame
        """
        if self.showSetting.get():
            self.settingFrame.pack_forget()
            self.showSetting.set(False)
        else:
            self.settingFrame.pack(side=TOP, fill=X, expand=False)
            self.showSetting.set(True)

    # Reset
    def reset_Default(self):
        """
        Reset the font settings of the window to default
        """
        # Ask for confirmation first
        if Mbox("Reset Default", "Are you sure you want to reset to default settings?", 3, parent=self.root):
            self.root.attributes('-alpha', 1)
            self.sliderOpac(1, "outside")
            self.textboxBgColor.set('#FFFFFF')
            self.textboxFgColor.set('#000000')
            self.textboxBgColorLabel.config(text="BG color: " + self.textboxBgColor.get())
            self.textboxFgColorLabel.config(text="FG color: " + self.textboxFgColor.get())
            self.textBoxTlResult.config(background=self.textboxBgColor.get())
            self.textBoxTlResult.config(foreground=self.textboxFgColor.get())

            self.tbResultFont.set({"family": "Segoe UI", "size": 10, "weight": "normal", "slant": "roman"})
            self.tbResultFontDict = json.loads(self.tbResultFont.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.tbResultFontDict
            self.tbFontLabel.configure(text='Font: ' + font_str)
            self.textBoxTlResult.config(font=(self.tbResultFontDict['family'], self.tbResultFontDict['size'], self.tbResultFontDict['weight'], self.tbResultFontDict['slant']))
            _StoredGlobal.main.setting_UI.updateLbl()

    def reset_To_Current(self):
        """
        Reset to currently stored settings
        """
        # Ask for confirmation first
        if Mbox("Reset To Currently Saved", "Are you sure you want to reset to currently saved settings?", 3, parent=self.root):
            self.root.attributes('-alpha', 1)
            self.sliderOpac(1, "outside")
            settings = fJson.readSetting()

            self.textboxBgColor.set(settings["Result_Box"]["bg"])
            self.textboxFgColor.set(settings["Result_Box"]["fg"])
            self.textboxBgColorLabel.config(text="BG color: " + self.textboxBgColor.get())
            self.textboxFgColorLabel.config(text="FG color: " + self.textboxFgColor.get())
            self.textBoxTlResult.config(background=self.textboxBgColor.get())
            self.textBoxTlResult.config(foreground=self.textboxFgColor.get())

            self.tbResultFont.set(settings["Result_Box"]["font"])
            self.tbResultFontDict = json.loads(self.tbResultFont.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.tbResultFontDict
            self.tbFontLabel.configure(text='Font: ' + font_str)
            self.textBoxTlResult.config(font=(self.tbResultFontDict['family'], self.tbResultFontDict['size'], self.tbResultFontDict['weight'], self.tbResultFontDict['slant']))
            _StoredGlobal.main.setting_UI.updateLbl()

    # Bg Color chooser
    def bgColorChooser(self, event=None):
        """Bg color chooser

        Args:
            event : Ignored. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=self.textboxBgColor.get(), title="Choose a color")
        if colorGet[1] != None:
            self.textboxBgColor.set(colorGet[1])
            self.textboxBgColorLabel.config(text="BG color: " + self.textboxBgColor.get())
            self.textBoxTlResult.config(background=self.textboxBgColor.get())
            _StoredGlobal.main.setting_UI.updateLbl()
    
    # Fg Color chooser
    def fgColorChooser(self, event=None):
        """Fg color chooser

        Args:
            event : Ignored. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=self.textboxFgColor.get(), title="Choose a color")
        if colorGet[1] != None:
            self.textboxFgColor.set(colorGet[1])
            self.textboxFgColorLabel.config(text="FG color: " + self.textboxFgColor.get())
            self.textBoxTlResult.config(foreground=self.textboxFgColor.get())
            _StoredGlobal.main.setting_UI.updateLbl()

    # Font Chooser
    def fontChooser(self, event=None):
        """Font chooser

        Args:
            event : Ignored. Defaults to None.
        """
        fontGet = askfont(self.root, title="Choose a font", text="Preview プレビュー معاينة 预览", family=self.tbResultFontDict['family'], size=self.tbResultFontDict['size'], weight=self.tbResultFontDict['weight'], slant=self.tbResultFontDict['slant'])
        if fontGet:
            self.tbResultFont.set(fontGet)
            self.tbResultFontDict = json.loads(self.tbResultFont.get().replace("'", '"'))
            self.textBoxTlResult.config(font=(self.tbResultFontDict['family'], self.tbResultFontDict['size'], self.tbResultFontDict['weight'], self.tbResultFontDict['slant']))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.tbResultFontDict
            self.tbFontLabel.configure(text='Font: ' + font_str)
            _StoredGlobal.main.setting_UI.updateLbl()

    def updateStuff(self):
        """
        Update the UI font labels and the text box
        """
        self.textboxBgColorLabel.config(text="BG color: " + self.textboxBgColor.get())
        self.textBoxTlResult.config(background=self.textboxBgColor.get())

        self.textboxFgColorLabel.config(text="FG color: " + self.textboxFgColor.get())
        self.textBoxTlResult.config(foreground=self.textboxFgColor.get())

        self.tbResultFontDict = json.loads(self.tbResultFont.get().replace("'", '"'))
        font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.tbResultFontDict
        self.tbFontLabel.configure(text='Font: ' + font_str)
        self.textBoxTlResult.config(font=(self.tbResultFontDict['family'], self.tbResultFontDict['size'], self.tbResultFontDict['weight'], self.tbResultFontDict['slant']))