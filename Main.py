import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Literal

import keyboard
import requests
from PIL import Image, ImageDraw
from pystray import Icon as icon
from pystray import Menu as menu
from pystray import MenuItem as item

from screen_translate._globals import app_name, fj, gcl
from screen_translate._logging import logger
from screen_translate._path import dir_captured, dir_user_manual, path_logo_icon
from screen_translate._version import __version__
from screen_translate.components.custom.MBox import Mbox
from screen_translate.components.custom.Tooltip import CreateToolTip
from screen_translate.components.window.About import AboutWindow
from screen_translate.components.window.Capture_Snip import SnipWindow
from screen_translate.components.window.Capture_Window import CaptureWindow
from screen_translate.components.window.Ex_Query import QueryWindow
from screen_translate.components.window.Ex_Result import ResultWindow
from screen_translate.components.window.History import HistoryWindow
from screen_translate.components.window.Log import LogWindow
from screen_translate.components.window.Mask import MaskWindow
from screen_translate.components.window.Settings import SettingWindow
from screen_translate.utils.Helper import OpenUrl, get_opac_value, nativeNotify, startFile
from screen_translate.utils.ocr.Capture import captureFullScreen
from screen_translate.utils.Style import get_current_theme, get_theme_list, init_theme, set_ui_style
from screen_translate.utils.translate.language import engine_select_source_dict, engine_select_target_dict, engines
from screen_translate.utils.translate.Translate import translate


# ----------------------------------------------------------------
def console():
    logger.info("--- Welcome to Screen Translate ---")
    logger.info("Use The GUI Window to start capturing and translating")
    logger.info("You can minimize this window")
    logger.info("This window is for debugging purposes")


# ----------------------------------------------------------------------
class AppTray:
    """
    Tray app
    """
    def __init__(self):
        self.icon: icon = None  # type: ignore
        self.menu: menu = None  # type: ignore
        self.menu_items = None  # type: ignore
        gcl.tray = self  # type: ignore
        self.create_tray()

    # -- Tray icon
    def create_image(self, width, height, color1, color2):
        # Generate an image and draw a pattern
        image = Image.new("RGB", (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)

        return image

    # -- Create tray
    def create_tray(self):
        try:
            trayIco = Image.open(path_logo_icon)
        except Exception:
            trayIco = self.create_image(64, 64, "black", "white")

        self.menu_items = (
            item(f"{app_name} {__version__}", lambda *args: None, enabled=False),  # do nothing
            menu.SEPARATOR,
            item("Snip and Translate", self.snip_win),
            item("Open Capture Window", self.open_capture_window),
            menu.SEPARATOR,
            item(
                "Generate",
                menu(
                    item("Mask Window", self.open_mask),
                    item("Query Window", self.open_query),
                    item("Result Window", self.open_result),
                ),
            ),
            item(
                "View",
                menu(
                    item("settings", self.open_settings),
                    item("History", self.open_history),
                    item("Captured Images", self.open_history),
                    item("Log", self.open_log),
                ),
            ),
            item("Show Main Window", self.open_app),
            menu.SEPARATOR,
            item("Exit", self.exit_app),
            item("Hidden onclick", self.open_app, default=True, visible=False),  # onclick the icon will open_app
        )
        self.menu = menu(*self.menu_items)
        self.icon = icon("Screen Translate", trayIco, f"Screen Translate V{__version__}", self.menu)
        self.icon.run_detached()

    # -- Open app
    def open_app(self):
        assert gcl.mw is not None  # Show main window
        gcl.mw.show()

    def open_query(self):
        assert gcl.ex_qw is not None
        gcl.ex_qw.show()

    def open_result(self):
        assert gcl.ex_resw is not None
        gcl.ex_resw.show()

    def open_capture_window(self):
        assert gcl.cw is not None
        gcl.cw.show()

    def open_settings(self):
        assert gcl.sw is not None
        gcl.sw.show()

    def open_history(self):
        assert gcl.hw is not None
        gcl.hw.show()

    def open_log(self):
        assert gcl.lw is not None
        gcl.lw.show()

    def open_mask(self):
        assert gcl.mask is not None
        gcl.mask.show()

    def snip_win(self):
        assert gcl.mw is not None
        gcl.mw.start_snip_window()

    # -- Exit app by flagging runing false to stop main loop
    def exit_app(self):
        gcl.running = False


# ----------------------------------------------------------------------
class MainWindow:
    """Main Menu Window"""
    def __init__(self):
        # ----------------------------------------------
        # Debug console info

        # --- Declarations and Layout ---
        self.root = tk.Tk()
        self.root.title(app_name)
        self.root.geometry("900x300")
        self.root.wm_attributes("-topmost", False)  # Default False
        self.alwaysOnTop = False
        self.notified_hidden = False
        gcl.mw = self  # type: ignore

        # ----------------------------------------------
        # Styles
        init_theme()
        self.style = ttk.Style()
        gcl.style = self.style
        gcl.native_theme = get_current_theme()  # get first theme before changing
        gcl.theme_lists = list(get_theme_list())

        # rearrange some positions
        try:
            gcl.theme_lists.remove("sv")
        except Exception:  # sv theme is not available
            gcl.theme_lists.remove("sv-dark")
            gcl.theme_lists.remove("sv-light")

        gcl.theme_lists.insert(0, gcl.native_theme)  # add native theme to top of list
        logger.debug(f"Available Theme to use: {gcl.theme_lists}")
        gcl.theme_lists.insert(len(gcl.theme_lists), "custom")

        set_ui_style(fj.setting_cache["theme"])
        # ----------------------------------------------
        # Frames
        self.frame_1 = ttk.Frame(self.root)
        self.frame_1.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.frame_1.bind("<Button-1>", lambda event: self.root.focus_set())

        self.frame_2_tb_q = ttk.Frame(self.root)
        self.frame_2_tb_q.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.frame_3 = ttk.Frame(self.root)
        self.frame_3.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.frame_3.bind("<Button-1>", lambda event: self.root.focus_set())

        self.frame_4_tb_res = ttk.Frame(self.root)
        self.frame_4_tb_res.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # --- Top frame_1 ---
        # Button
        self.btn_translate = ttk.Button(self.frame_1, text="Translate", command=self.start_tl)
        self.btn_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_translate, "Translate the text in the top frame")

        self.btn_capture_translate = ttk.Button(self.frame_1, text="Capture & Translate", command=self.start_capture_window)
        self.btn_capture_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.btn_capture_translate,
            "Capture and translate the text inside capture area. Need to generate the capture UI first",
        )

        self.btn_snip_translate = ttk.Button(self.frame_1, text="Snip & Translate", command=self.start_snip_window)
        self.btn_snip_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_snip_translate, "Snip and translate the selected text.")

        # Opacity
        self.slider_capture_opac = ttk.Scale(
            self.frame_1, from_=0.0, to=1.0, value=0.8, orient=tk.HORIZONTAL, command=self.opac_change
        )
        self.slider_capture_opac.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_capture_opac = ttk.Label(self.frame_1, text="Capture Window Opacity: " + "0.8")
        self.lbl_capture_opac.pack(side=tk.LEFT, padx=5, pady=5)

        self.frame_status = ttk.Frame(self.frame_1)
        self.frame_status.pack(side=tk.RIGHT, fill=tk.X, expand=False)

        self.lb_status = ttk.Progressbar(self.frame_status, orient=tk.HORIZONTAL, length=120, mode="determinate")
        self.lb_status.pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Top frame_2 ---
        # TB
        # Translation Textbox (Query/Source)
        self.frame_tb_query_bg = ttk.Frame(self.frame_2_tb_q, style="Darker.TFrame")
        self.frame_tb_query_bg.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sb_query = ttk.Scrollbar(self.frame_tb_query_bg)
        self.sb_query.pack(side=tk.RIGHT, fill=tk.Y)

        self.tb_query = tk.Text(
            self.frame_tb_query_bg,
            height=5,
            width=100,
            relief=tk.FLAT,
            font=(fj.setting_cache["tb_mw_q_font"], fj.setting_cache["tb_mw_q_font_size"]),
            autoseparators=True,
            undo=True,
            maxundo=-1,
        )
        self.tb_query.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        self.tb_query.configure(yscrollcommand=self.sb_query.set)
        self.sb_query.configure(command=self.tb_query.yview)
        self.tb_query.bind("<KeyRelease>", self.tb_query_change)

        # --- Bottom frame_3 ---
        # Langoptions onstart
        self.lbl_engines = ttk.Label(self.frame_3, text="TL Engine:")
        self.lbl_engines.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.lbl_engines,
            'The provider use to translate the text. You can set it to "None" if you only want to use the OCR',
        )

        self.cb_tl_engine = ttk.Combobox(self.frame_3, values=engines, state="readonly")
        self.cb_tl_engine.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_tl_engine.bind("<<ComboboxSelected>>", self.cb_engine_change)

        self.lbl_source = ttk.Label(self.frame_3, text="From:")
        self.lbl_source.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_source, "Source Language (Text to be translated)")

        self.cb_sourceLang = ttk.Combobox(
            self.frame_3, values=engine_select_source_dict[fj.setting_cache["engine"]], state="readonly", width=29
        )
        self.cb_sourceLang.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_sourceLang.bind("<<ComboboxSelected>>", self.cb_source_change)

        self.lbl_target = ttk.Label(self.frame_3, text="To:")
        self.lbl_target.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_target, "Target Language (Results)")

        self.cb_targetLang = ttk.Combobox(
            self.frame_3, values=engine_select_target_dict[fj.setting_cache["engine"]], state="readonly", width=29
        )
        self.cb_targetLang.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_targetLang.bind("<<ComboboxSelected>>", self.cb_target_change)

        self.btn_swap = ttk.Button(self.frame_3, text="⮁ Swap", command=self.swapTl)
        self.btn_swap.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_clear = ttk.Button(self.frame_3, text="✕ Clear", command=self.clear_tb)
        self.btn_clear.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Bottom tk.Frame 2 ---
        # TB
        # Translation Textbox (Result)
        self.frame_tb_result_bg = ttk.Frame(self.frame_4_tb_res, style="Darker.TFrame")
        self.frame_tb_result_bg.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sb_result = ttk.Scrollbar(self.frame_tb_result_bg)
        self.sb_result.pack(side=tk.RIGHT, fill=tk.Y)

        self.tb_result = tk.Text(
            self.frame_tb_result_bg,
            height=5,
            width=100,
            relief=tk.FLAT,
            font=(fj.setting_cache["tb_mw_q_font"], fj.setting_cache["tb_mw_q_font_size"]),
            autoseparators=True,
            undo=True,
            maxundo=-1,
        )
        self.tb_result.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        self.tb_result.configure(yscrollcommand=self.sb_result.set)
        self.sb_result.configure(command=self.tb_result.yview)
        self.tb_result.bind("<KeyRelease>", self.tb_result_change)

        # --- Menubar ---
        # Menubar
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_checkbutton(label="Always on Top", command=self.always_on_top)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Hide", command=self.on_closing)
        self.filemenu.add_command(label="Exit Application", command=self.quit_app)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.filemenu2 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu2.add_command(label="Setting", command=self.open_Setting, accelerator="F2")  # Open Setting Window
        self.filemenu2.add_command(label="History", command=self.open_History, accelerator="F3")  # Open History Window
        self.filemenu2.add_command(
            label="Captured Image", command=self.open_Img_Captured, accelerator="F4"
        )  # Open Captured img folder
        self.filemenu2.add_command(label="Log", command=self.open_Log)  # Open Error Log
        self.menubar.add_cascade(label="View", menu=self.filemenu2)

        self.filemenu3 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu3.add_command(
            label="Capture Window", command=self.open_Capture_Screen, accelerator="F5"
        )  # Open Capture Screen Window
        self.filemenu3.add_command(
            label="Mask Window", command=self.open_Mask_Window, accelerator="Ctrl + Alt + F5"
        )  # Open Mask window
        self.filemenu3.add_command(label="Query Window", command=self.open_Query_Window, accelerator="F6")
        self.filemenu3.add_command(label="Result Window", command=self.open_Result_Window, accelerator="F7")
        self.menubar.add_cascade(label="Generate", menu=self.filemenu3)

        self.filemenu4 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu4.add_command(label="Tesseract", command=self.openTesLink)  # Open Tesseract Downloads
        self.filemenu4.add_command(label="Libretranslate", command=self.openLibreTlLink)  # Open Tesseract Downloads
        self.menubar.add_cascade(label="Get", menu=self.filemenu4)

        self.filemenu5 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu5.add_command(label="Tutorial", command=self.open_Tutorial)  # Open Mbox Tutorials
        self.filemenu5.add_command(label="FAQ", command=self.open_Faq)  # Open FAQ
        self.filemenu5.add_command(label="Known Bugs", command=self.open_KnownBugs)  # Open Knownbugs
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Open User Manual", command=self.open_UserManual)  # Open user manual folder
        self.filemenu5.add_command(
            label="Open GitHub Repo", command=lambda aurl="https://github.com/Dadangdut33/Screen-Translate": OpenUrl(aurl)
        )
        self.filemenu5.add_command(label="Open Changelog", command=self.open_Changelog)
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Contributor", command=self.open_Contributor)  # Open Contributor
        self.filemenu5.add_command(label="About STL", command=self.open_About, accelerator="F1")  # Open about frame
        self.menubar.add_cascade(label="Help", menu=self.filemenu5)

        # Add to self.root
        self.root.configure(menu=self.menubar)

        # Bind key shortcut
        self.root.bind("<F1>", self.open_About)
        self.root.bind("<F2>", self.open_Setting)
        self.root.bind("<F3>", self.open_History)
        self.root.bind("<F4>", self.open_Img_Captured)
        self.root.bind("<F5>", self.open_Capture_Screen)
        self.root.bind("<Control-Alt-F5>", self.open_Mask_Window)
        self.root.bind("<F6>", self.open_Query_Window)
        self.root.bind("<F7>", self.open_Result_Window)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # ------------------ on Start ------------------
        self.root.after(1000, self.isRunningPoll)
        self.onInit()

        # --- Logo ---
        try:
            self.root.iconbitmap(path_logo_icon)
        except tk.TclError:
            logger.warning("Error Loading icon: Logo not found!")
        except Exception as e:
            logger.warning("Error loading icon")
            logger.exception(e)

    def isRunningPoll(self):
        if not gcl.running:
            self.quit_app()

        self.root.after(1000, self.isRunningPoll)

    # --- Functions ---
    def onInit(self):
        self.cb_tl_engine.set(fj.setting_cache["engine"])
        self.cb_sourceLang.set(fj.setting_cache["sourceLang"])
        self.cb_targetLang.set(fj.setting_cache["targetLang"])
        if self.cb_tl_engine.get() == "None":
            self.cb_targetLang["state"] = "disabled"

        try:
            if fj.setting_cache["hk_cap_window"] != "":
                keyboard.add_hotkey(fj.setting_cache["hk_cap_window"], gcl.hk_cap_window_callback)
            if fj.setting_cache["hk_snip_cap"] != "":
                keyboard.add_hotkey(fj.setting_cache["hk_snip_cap"], gcl.hk_snip_mode_callback)
        except KeyError as e:
            logger.error("Error: Invalid Hotkey Options")
            logger.exception(e)

        self.hkPollThread = threading.Thread(target=self.hkPoll, daemon=True)
        self.hkPollThread.start()

        # detect if run from startup or not using sys, with -s as argument marking silent start (hide window)
        logger.info("Checking if run from startup...")
        logger.debug(sys.argv)
        if "-s" in sys.argv:
            logger.info("Run from startup, hiding window...")
            self.root.withdraw()

    def quit_app(self):
        gcl.running = False

        logger.info("Stopping tray...")
        if gcl.tray:
            gcl.tray.icon.stop()

        logger.info("Destroying windows...")
        gcl.sw.root.destroy()  # type: ignore  # setting window
        gcl.hw.root.destroy()  # type: ignore history window
        gcl.cw.root.destroy()  # type: ignore # capture window
        gcl.csw.root.destroy()  # type: ignore # capture snip window
        gcl.aw.root.destroy()  # type: ignore # about window
        gcl.lw.root.destroy()  # type: ignore # log window
        gcl.mask.root.destroy()  # type: ignore # mask window
        gcl.ex_qw.root.destroy()  # type: ignore # external query window
        gcl.ex_resw.root.destroy()  # type: ignore # external result window
        self.root.destroy()

        logger.info("Exiting...")
        try:
            sys.exit(0)
        except SystemExit:
            logger.info("Exit successful")
        except Exception:
            logger.error("Exit failed, killing process")
            os._exit(0)

    # Show window
    def show(self):
        self.root.after(0, self.root.deiconify)

    # On Close
    def on_closing(self):
        """
        Confirmation on close
        """
        # Only show notification once
        if not self.notified_hidden:
            nativeNotify("Hidden to tray", "The app is still running in the background.", path_logo_icon, app_name)
            self.notified_hidden = True

        self.root.withdraw()

    # Open Setting Window
    def open_Setting(self, event=None):
        assert gcl.sw is not None
        gcl.sw.show()

    # Open History Window
    def open_History(self, event=None):
        assert gcl.hw is not None
        gcl.hw.show()

    # Open result box
    def open_Result_Window(self, event=None):
        assert gcl.ex_resw is not None
        gcl.ex_resw.show()

    # Open query box
    def open_Query_Window(self, event=None):
        assert gcl.ex_qw is not None
        gcl.ex_qw.show()

    # Open About Window
    def open_About(self, event=None):
        assert gcl.aw is not None
        gcl.aw.show()

    # Open Capture Window
    def open_Capture_Screen(self, event=None):
        assert gcl.cw is not None
        gcl.cw.show()

    # Open mask window
    def open_Mask_Window(self, event=None):
        assert gcl.mask is not None
        gcl.mask.show()

    # Open captured image folder
    def open_Img_Captured(self, event=None):
        startFile(dir_captured)

    # Open log window
    def open_Log(self, event=None):
        assert gcl.lw is not None
        gcl.lw.show()

    # Hotkey
    def hkPoll(self):
        while gcl.running:
            if gcl.hk_cw_pressed and not gcl.cw_hidden:  # If the hotkey for capture and translate is pressed
                time.sleep(fj.setting_cache["hk_cap_window_delay"] / 1000)
                self.start_capture_window()
                gcl.hk_cw_pressed = False

            if gcl.hk_snip_pressed:  # If the hotkey for snip and translate is pressed
                time.sleep(fj.setting_cache["hk_snip_cap_delay"] / 1000)
                self.start_snip_window()
                gcl.hk_snip_pressed = False

            time.sleep(0.1)

    # Slider
    def opac_change(self, event):
        value = get_opac_value(event)
        self.lbl_capture_opac.configure(text=f"Capture Window Opacity: {round(value, 3)}")
        gcl.slider_cw_change(value, update_slider=True)

    def tb_query_change(self, event):
        gcl.insert_ex_q(self.tb_query.get(1.0, tk.END).strip())

    def tb_result_change(self, event):
        gcl.insert_ex_res(self.tb_result.get(1.0, tk.END).strip())

    # Menubar
    def always_on_top(self):
        self.alwaysOnTop = not self.alwaysOnTop
        self.root.wm_attributes("-topmost", self.alwaysOnTop)

    # ---------------------------------
    # Mbox
    # Tutorials
    def open_Tutorial(self):
        Mbox(
            "Tutorial",
            """1. *First*, make sure your screen scaling is 100%. If scaling is not 100%, the capturer won't work properly. If by any chance you don't want to set your monitor scaling to 100%, you can set the xy offset in the setting
        \r2. *Second*, you need to install tesseract, you can quickly go to the download link by pressing the download tesseract in menu bar
        \r3. *Then*, check the settings. Make sure tesseract path is correct
        \r4. *FOR MULTI MONITOR USER*, set offset in setting. If you have multiple monitor setup, you might need to set the offset in settings.
        \rWhat you should do in the setting window:\n- Check how the program see your monitors in settings by clicking that one button.\n- You can also see how the capture area captured your images by enabling save capture image in settings and then see the image in 'img_captured' directory
        \r\n------------------------------------------------------------------------------\nYou can check for visual tutorial in help -> open user manual if you are still confused.""",
            0,
            self.root,
        )

    # FAQ
    def open_Faq(self):
        Mbox(
            "FAQ",
            """Q : Do you collect the screenshot?\nA : No, no data is collected by me. Image and text captured will only be use for query and the captured image is only saved locally
        \rQ : Is this safe?\nA : Yes, it is safe, you can check the code on the github linked in the menubar, or open it yourself on your machine.
        \rQ : I could not capture anything, help!?\nA : You might need to check the captured image and see wether it actually capture the stuff that you targeted or not. If not, you might want to set offset in setting or change your monitor scaling to 100%
        """,
            0,
            self.root,
        )

    # Download tesseract
    def openTesLink(self):
        Mbox(
            "Info",
            "Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack",
            0,
            self.root,
        )
        logger.info(
            "Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack"
        )
        OpenUrl("https://github.com/UB-Mannheim/tesseract/wiki")

    def openLibreTlLink(self):
        Mbox(
            "Info",
            "You can follow the instruction on their github pages. It is recommended to build it with the models so you can use it fully offline.",
            0,
            self.root,
        )
        OpenUrl("https://github.com/LibreTranslate/LibreTranslate")

    # Open known bugs
    def open_KnownBugs(self):
        Mbox(
            "Known Bugs",
            """- Monitor scaling needs to be 100% or it won't capture accurately (You can fix this easily by setting offset or set your monitor scaling to 100%)""",
            0,
            self.root,
        )

    # Open user manual
    def open_UserManual(self):
        try:
            startFile(dir_user_manual)
        except Exception:
            OpenUrl("https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual")

    # Open contributor
    def open_Contributor(self):
        OpenUrl("https://github.com/Dadangdut33/Screen-Translate/graphs/contributors")

    # Open changelog
    def open_Changelog(self):
        try:
            startFile(dir_user_manual + r"\changelog.txt")
        except Exception:
            Mbox(
                "Error",
                "Changelog file not found\n\nProgram will now try open the one in the repository instead of the local copy.",
                0,
                self.root,
            )
            try:
                OpenUrl("https://github.com/Dadangdut33/Screen-Translate/blob/main/user_manual/Changelog.txt")
                # download
                req = requests.get(
                    "https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/user_manual/Changelog.txt"
                )
                with open(dir_user_manual + r"\changelog.txt", "wb") as f:
                    f.write(req.content)
            except Exception as e:
                logger.exception(e)
                Mbox("Error", str(e), 0, self.root)

    # -----------------------------------------------------------------
    # Widgets functions
    def swapTl(self):
        tmp = self.tb_query.get(1.0, tk.END).strip()
        self.tb_query.delete(1.0, tk.END)
        self.tb_query.insert(tk.END, self.tb_result.get(1.0, tk.END).strip())
        self.tb_result.delete(1.0, tk.END)
        self.tb_result.insert(tk.END, tmp)

        # swap cb but check first
        tmp = self.cb_sourceLang.get()
        if self.cb_targetLang.get() in self.cb_sourceLang["values"]:
            self.cb_sourceLang.set(self.cb_targetLang.get())

        if tmp in self.cb_targetLang["values"]:
            self.cb_targetLang.set(tmp)

        fj.save_setting_partial("sourceLang", self.cb_sourceLang.get())
        fj.save_setting_partial("targetLang", self.cb_targetLang.get())
        gcl.update_ex_cw_setting()

    # Clear TB
    def clear_tb(self):
        self.tb_query.delete(1.0, tk.END)
        self.tb_result.delete(1.0, tk.END)

    def cb_engine_change(self, _event=None):
        # save
        fj.save_setting_partial("engine", self.cb_tl_engine.get())
        self.cb_lang_update()

    def cb_lang_update(self):
        # update
        self.cb_sourceLang["values"] = engine_select_source_dict[self.cb_tl_engine.get()]
        self.cb_targetLang["values"] = engine_select_target_dict[self.cb_tl_engine.get()]

        if self.cb_sourceLang.get() not in self.cb_sourceLang["values"]:
            self.cb_sourceLang.current(0)

        if self.cb_targetLang.get() not in self.cb_targetLang["values"]:
            self.cb_targetLang.current(0)

        if self.cb_tl_engine.get() == "None":
            self.cb_targetLang["state"] = "disabled"
        else:
            self.cb_targetLang["state"] = "readonly"

        # save
        fj.save_setting_partial("sourceLang", self.cb_sourceLang.get())
        fj.save_setting_partial("targetLang", self.cb_targetLang.get())

        # update external
        gcl.update_ex_cw_setting()

    def cb_source_change(self, _event=None):
        fj.save_setting_partial("sourceLang", self.cb_sourceLang.get())
        # update external
        gcl.update_ex_cw_setting()

    def cb_target_change(self, _event=None):
        fj.save_setting_partial("targetLang", self.cb_targetLang.get())
        # update external
        gcl.update_ex_cw_setting()

    # -----------------------------------------------------------------
    def get_params(self):
        return self.cb_tl_engine.get(), self.cb_sourceLang.get(), self.cb_targetLang.get(), self.tb_query.get(1.0, tk.END)

    def param_check(
        self,
        engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate", "None"],
        from_lang: str,
        to_lang: str,
        query: str,
        withOCR: bool = True,
    ):
        logger.info("Checking params...")
        logger.debug(f"engine: {engine} | source: {from_lang} | to: {to_lang}")
        # If source and destination are the same
        if engine != "None" and ((from_lang) == (to_lang)):
            gcl.lb_stop()
            logger.warning("Error Language is the same as source! Please choose a different language")
            Mbox(
                "Error: Language target is the same as source",
                "Language target is the same as source! Please choose a different language",
                2,
                self.root,
            )
            return False

        if engine != "None" and from_lang == "Auto-Detect" and withOCR:
            gcl.lb_stop()
            logger.warning("Error: Invalid Language source! Must specify source langauge when using OCR")
            Mbox("Error: Invalid Source Language Selected", "Must specify source langauge when using OCR", 2, self.root)
            return False

        # If langto not set
        if to_lang == "Auto-Detect":
            gcl.lb_stop()
            logger.warning("Error: Invalid Language Selected! Must specify language destination")
            Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, self.root)
            return False

        # If the text is empty
        if len(query) == 0:
            gcl.lb_stop()
            logger.warning("Error: No text detected! Please select a text to translate")
            Mbox("Error: No text detected", "Please select a text to translate", 2, self.root)
            return False

        logger.info("Passed param check!")
        return True

    def start_tl(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query, False):  # type: ignore
            return

        if engine == "None":
            logger.warning("Error: No translation engine selected! Please select a translation engine if only translate!")
            Mbox("Error", "Please select a translation engine if only translate!", 0, self.root)
            return

        gcl.lb_start()
        try:
            tlThread = threading.Thread(target=translate, args=(query, from_lang, to_lang, engine), daemon=True)
            tlThread.start()
        except Exception as e:
            logger.exception(e)
            Mbox("Error", str(e), 0, self.root)
        gcl.lb_stop()

    def start_capture_window(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query):  # type: ignore
            return

        if gcl.cw_hidden:
            logger.warning("Capture window is not generated yet!")
            Mbox("Error", "Capture window is not generated yet!", 0, self.root)
            return

        assert gcl.cw is not None
        gcl.cw.start_capping()  # window hiding handled in the cw window

    def start_snip_window(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query):  # type: ignore
            return

        # ----------------- hide other window -----------------
        if fj.setting_cache["hide_mw_on_cap"]:
            assert gcl.mw is not None
            gcl.mw.root.attributes("-alpha", 0)

        assert gcl.ex_qw is not None
        prev_ex_qw_opac = gcl.ex_qw.currentOpacity
        if fj.setting_cache["hide_ex_qw_on_cap"]:
            gcl.ex_qw.root.attributes("-alpha", 0)

        assert gcl.ex_resw is not None
        prev_ex_resw_opac = gcl.ex_resw.currentOpacity
        if fj.setting_cache["hide_ex_resw_on_cap"]:
            gcl.ex_resw.root.attributes("-alpha", 0)

        # ----------------- start snipping -----------------
        success, imgObj = captureFullScreen()

        # ----------------- show other window -----------------
        if fj.setting_cache["hide_mw_on_cap"]:
            assert gcl.mw is not None
            gcl.mw.root.attributes("-alpha", 1)

        if fj.setting_cache["hide_ex_qw_on_cap"]:
            assert gcl.ex_qw is not None
            gcl.ex_qw.root.attributes("-alpha", prev_ex_qw_opac)

        if fj.setting_cache["hide_ex_resw_on_cap"]:
            assert gcl.ex_resw is not None
            gcl.ex_resw.root.attributes("-alpha", prev_ex_resw_opac)

        # check if snipping is successful
        if not success:
            Mbox("Error", f"Failed to start snipping mode.\nReason: {imgObj}", 0, self.root)
            return

        assert gcl.csw is not None
        gcl.csw.start_snipping(imgObj)


if __name__ == "__main__":
    console()

    tray = AppTray()  # Start tray app in the background
    mw = MainWindow()
    cw = CaptureWindow(mw.root)
    csw = SnipWindow(mw.root)
    ex_qw = QueryWindow(mw.root)
    ex_resw = ResultWindow(mw.root)
    mask = MaskWindow(mw.root)
    hw = HistoryWindow(mw.root)
    lw = LogWindow(mw.root)
    sw = SettingWindow(mw.root)
    aw = AboutWindow(mw.root)
    mw.root.mainloop()
