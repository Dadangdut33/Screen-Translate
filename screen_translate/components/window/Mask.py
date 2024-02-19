import tkinter as tk
from tkinter import colorchooser

from screen_translate._globals import fj, gcl
from screen_translate._path import path_logo_icon
from screen_translate.components.custom.MBox import Mbox
from screen_translate.components.custom.Tooltip import CreateToolTip
from screen_translate.utils.Beep import beep


# Classes
class MaskWindow:
    """Mask Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title("Mask Window")
        self.root.geometry("600x160")
        self.root.wm_withdraw()
        gcl.mask = self  # type: ignore

        # ------------------ #
        self.currentOpacity = 1.0
        self.always_on_top = tk.IntVar()
        self.tooltip_disabled = tk.IntVar()
        self.hidden_top = tk.IntVar()
        self.clickThrough = tk.IntVar()

        # Top frame
        self.f_1 = tk.Frame(self.root, background=fj.setting_cache["mask_window_color"])
        self.f_1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fTooltip = CreateToolTip(self.f_1, "Right click for interaction menu", wrapLength=400)

        self.menuDropdown = tk.Menu(self.root, tearoff=0)
        self.menuDropdown.add_command(
            label=f"Color: {fj.setting_cache['mask_window_bg_color']}",
            command=lambda: self.windowColorChooser(),
            accelerator="Click to change color"
        )
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(
            label="Hide Title bar",
            command=lambda: self.toggle_hidden_top(False),
            onvalue=1,
            offvalue=0,
            variable=self.hidden_top,
            accelerator="Alt + T"
        )
        self.menuDropdown.add_checkbutton(
            label="Always On Top",
            command=lambda: self.toggle_always_on_top(False),
            onvalue=1,
            offvalue=0,
            variable=self.always_on_top,
            accelerator="Alt + O"
        )
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(
            label="Increase Opacity by 0.1", command=lambda: self.increase_opacity(), accelerator="Alt + Mouse Wheel Up"
        )
        self.menuDropdown.add_command(
            label="Decrease Opacity by 0.1", command=lambda: self.decrease_opacity(), accelerator="Alt + Mouse Wheel Down"
        )
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(
            label="Hide Tooltip",
            command=lambda: self.disable_tooltip(False),
            onvalue=1,
            offvalue=0,
            variable=self.tooltip_disabled,
            accelerator="Alt + X"
        )
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Keyboard Shortcut Keys", command=lambda: self.show_shortcut_keys())

        # ------------------------------------------------------------------------
        # Binds
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # rclick menu
        self.root.bind("<Button-3>", lambda event: self.menuDropdown.post(event.x_root, event.y_root))

        # keybinds
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_hidden_top())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.disable_tooltip())
        self.root.bind("<Alt-MouseWheel>", lambda event: self.change_opacity(event))

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    # Show/Hide
    def show(self):
        self.root.attributes("-alpha", 0.8)
        self.root.after(0, self.root.deiconify)

    def on_closing(self):
        self.root.wm_withdraw()

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

    def show_shortcut_keys(self):
        """
        Method to show shortcut keys.
        """
        Mbox(
            "Shortcut keys command for mask window (Must be focused)",
            "Alt + scroll to change opacity\nAlt + t to toggle title bar (remove title bar)\nAlt + o to toggle always on top\nAlt + x to toggle on/off this tooltip\n\nTips: If the window is missing because of low opacity, you can generate it again. It will set opacity to normal.",
            0,
        )

    # Bg Color chooser
    def windowColorChooser(self):
        """window color chooser

        Args:
            event : Ignored. Defaults to None.
        """
        colorGet = colorchooser.askcolor(color=fj.setting_cache["mask_window_bg_color"], title="Choose a color")
        if colorGet[1] != None:
            self.root["bg"] = colorGet[1]
            self.f_1["bg"] = colorGet[1]
            self.menuDropdown.entryconfig(0, label=f"Color: {colorGet[1]}")
            fj.save_setting_partial("mask_window_bg_color", colorGet[1])
            gcl.update_sw_setting()
