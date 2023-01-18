import platform
import tkinter as tk
import tkinter.ttk as ttk

from screen_translate.utils.Beep import beep

from .Tooltip import CreateToolTip
from screen_translate.Globals import gClass, fJson, path_logo_icon
from screen_translate.components.MBox import Mbox

# Classes
class CaptureWindow:
    """Capture Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        gClass.cw = self  # type: ignore
        self.root = tk.Toplevel(master)
        self.root.title("Capture Window")
        self.root.geometry("600x150")
        self.root.wm_withdraw()
        self.root.attributes("-alpha", 0.8)

        # ------------------ #
        self.always_on_top = tk.IntVar()
        self.always_on_top.set(1)
        self.tooltip_disabled = tk.IntVar()
        self.hidden_top = tk.IntVar()
        self.clickThrough = tk.IntVar()
        self.cv2Contour = tk.IntVar()
        self.grayscale = tk.IntVar()
        self.bgType = tk.StringVar()
        self.debugMode = tk.IntVar()

        # Frame-1
        self.f_1 = tk.Frame(self.root)
        self.f_1.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.fTooltip = CreateToolTip(self.f_1, "Right click for interaction menu", wrapLength=400)

        # ----------------------------------------------------------------------
        # drag label
        self.lbl_drag = tk.Label(self.f_1, text="▶", font=("Arial", 16, "bold"), foreground="gray")
        self.lbl_drag.pack(side=tk.LEFT, fill=tk.X, expand=False)

        # Label for opacity slider
        self.lbl_opacity = ttk.Label(self.f_1, text="Opacity: 0.8")
        self.lbl_opacity.pack(padx=5, pady=5, side=tk.LEFT)

        # opacity slider
        self.slider_opacity = ttk.Scale(self.f_1, from_=0.25, to=1.0, value=0.8, orient=tk.HORIZONTAL, command=self.change_opacity)
        self.slider_opacity.pack(padx=5, pady=5, side=tk.LEFT)

        # Button
        assert gClass.mw is not None
        self.captureBtn = ttk.Button(self.f_1, text="Capture & Translate", command=gClass.mw.capwin_callback)
        self.captureBtn.pack(padx=5, pady=5, side=tk.LEFT)

        # menu
        self.menuDropdown = tk.Menu(self.root, tearoff=0)
        self.menuDropdown.add_checkbutton(label="Hide Title bar", command=lambda: self.toggle_hidden_top(False), onvalue=1, offvalue=0, variable=self.hidden_top, accelerator="Alt + T")
        if platform.system() == "Windows":
            self.menuDropdown.add_checkbutton(label="Click Through/Transparent", command=lambda: self.toggle_click_through(False), onvalue=1, offvalue=0, variable=self.clickThrough, accelerator="Alt + S")
        self.menuDropdown.add_checkbutton(label="Always On Top", command=lambda: self.toggle_always_on_top(False), onvalue=1, offvalue=0, variable=self.always_on_top, accelerator="Alt + O")

        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Increase Opacity by 0.1", command=lambda: self.increase_opacity(), accelerator="Alt + Mouse Wheel Up")
        self.menuDropdown.add_command(label="Decrease Opacity by 0.1", command=lambda: self.decrease_opacity(), accelerator="Alt + Mouse Wheel Down")

        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(
            label="Detect contour using CV2", command=lambda: beep() or fJson.savePartialSetting("enhance_with_cv2_Contour", self.cv2Contour.get()), onvalue=1, offvalue=0, variable=self.cv2Contour
        )
        self.menuDropdown.add_checkbutton(label="Grayscale", command=lambda: beep() or fJson.savePartialSetting("grayscale", self.grayscale.get()), onvalue=1, offvalue=0, variable=self.grayscale)
        self.bgTypeMenu = tk.Menu(self.menuDropdown, tearoff=0)
        self.menuDropdown.add_cascade(label="Background Type", menu=self.bgTypeMenu)
        self.bgTypeMenu.add_radiobutton(label="Auto-Detect", command=lambda: beep() or fJson.savePartialSetting("enhance_background", "Auto-Detect"), value="Auto-Detect", variable=self.bgType)
        self.bgTypeMenu.add_radiobutton(label="Light", command=lambda: beep() or fJson.savePartialSetting("enhance_background", "Light"), value="Light", variable=self.bgType)
        self.bgTypeMenu.add_radiobutton(label="Dark", command=lambda: beep() or fJson.savePartialSetting("enhance_background", "Dark"), value="Dark", variable=self.bgType)
        self.menuDropdown.add_checkbutton(label="Debug Mode", command=lambda: beep() or fJson.savePartialSetting("enhance_debugmode", self.debugMode.get()), onvalue=1, offvalue=0, variable=self.debugMode)

        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(label="Hide Tooltip", command=lambda: self.disable_tooltip(False), onvalue=1, offvalue=0, variable=self.tooltip_disabled, accelerator="Alt + X")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Keyboard Shortcut Keys", command=lambda: self.show_shortcut_keys())

        # ------------------------------------------------------------------------
        # Binds
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # rclick menu
        self.root.bind("<Button-3>", lambda event: self.menuDropdown.post(event.x_root, event.y_root))

        # keybinds
        if platform.system() == "Windows":
            self.root.bind("<Alt-KeyPress-s>", lambda event: self.toggle_click_through())
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_hidden_top())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.disable_tooltip())
        self.root.bind("<Alt-MouseWheel>", lambda event: self.change_opacity(event))

        # bind drag on label text
        self.lbl_drag.bind("<ButtonPress-1>", self.StartMove)
        self.lbl_drag.bind("<ButtonRelease-1>", self.StopMove)
        self.lbl_drag.bind("<B1-Motion>", self.OnMotion)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    def initVar(self):
        self.cv2Contour.set(fJson.settingCache["enhance_with_cv2_Contour"])
        self.grayscale.set(fJson.settingCache["enhance_with_grayscale"])
        self.bgType.set(fJson.settingCache["enhance_background"])
        self.debugMode.set(fJson.settingCache["enhance_debugmode"])

    # Show/Hide
    def show(self):
        self.initVar()
        self.root.wm_deiconify()
        self.root.attributes("-alpha", 0.8)
        if platform.system() == "Windows":
            self.clickThrough.set(0)
            self.root.wm_attributes("-transparentcolor", "")

    def on_closing(self):
        self.root.wm_withdraw()

    def StartMove(self, event):
        self.x = event.x
        self.y = event.y

    def StopMove(self, event):
        self.x = None
        self.y = None

    def OnMotion(self, event):
        x = event.x_root - self.x - self.lbl_drag.winfo_rootx() + self.lbl_drag.winfo_rootx()
        y = event.y_root - self.y - self.lbl_drag.winfo_rooty() + self.lbl_drag.winfo_rooty()
        self.root.geometry("+%s+%s" % (x, y))

    def show_shortcut_keys(self):
        """
        Method to show shortcut keys.
        """
        Mbox(
            "Shortcut keys command for detached window (Must be focused)",
            "Alt + scroll to change opacity\nAlt + t to toggle title bar (remove title bar)\nAlt + s to toggle click through or transparent window\nAlt + o to toggle always on top\nAlt + x to toggle on/off this tooltip\n\nTips: You can drag the window by dragging the ▶ label",
            0,
        )

    # disable tooltip
    def disable_tooltip(self, fromKeyBind=True):
        """
        Method to toggle tooltip.
        """
        beep()
        if fromKeyBind:
            self.tooltip_disabled.set(0 if self.tooltip_disabled.get() == 1 else 1)

        if self.tooltip_disabled.get() == 1:
            self.fTooltip.hidetip()
            self.fTooltip.opacity = 0
        else:
            self.fTooltip.showTip()
            self.fTooltip.opacity = self.currentOpacity

    # show/hide top
    def toggle_hidden_top(self, fromKeyBind=True):
        """
        Method to toggle hidden top.
        """
        beep()
        if fromKeyBind:
            self.hidden_top.set(0 if self.hidden_top.get() == 1 else 1)

        self.root.overrideredirect(True if self.hidden_top.get() == 1 else False)

    def toggle_click_through(self, fromKeyBind=True):
        """
        Method to toggle click through. Only on windows.
        """
        beep()
        if fromKeyBind:
            self.clickThrough.set(0 if self.clickThrough.get() == 1 else 1)

        if self.clickThrough.get() == 1:
            self.root.wm_attributes("-transparentcolor", self.root["bg"])
        else:
            self.root.wm_attributes("-transparentcolor", "")

    def toggle_always_on_top(self, fromKeyBind=True):
        """
        Method to toggle always on top.
        """

        beep()
        if fromKeyBind:
            self.always_on_top.set(0 if self.always_on_top.get() == 1 else 1)

        self.root.wm_attributes("-topmost", True if self.always_on_top.get() == 1 else False)

    def increase_opacity(self):
        """
        Method to increase the opacity of the window by 0.1.
        """
        self.currentOpacity += 0.075
        if self.currentOpacity > 1:
            self.currentOpacity = 1
        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity

    def decrease_opacity(self):
        """
        Method to decrease the opacity of the window by 0.1.
        """
        self.currentOpacity -= 0.075
        if self.currentOpacity < 0.025:
            self.currentOpacity = 0.025
        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity

    # opacity change
    def change_opacity(self, event):
        """
        Method to change the opacity of the window by scrolling.

        Args:
            event (event): event object
        """
        if event.delta > 0:
            self.currentOpacity += 0.025
        else:
            self.currentOpacity -= 0.025

        if self.currentOpacity > 1:
            self.currentOpacity = 1
        elif self.currentOpacity < 0.025:
            self.currentOpacity = 0.025

        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity
        self.lbl_opacity.config(text=f"Opacity: {round(self.currentOpacity, 3)}")
