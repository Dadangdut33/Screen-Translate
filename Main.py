import os
import sys
import threading
import time
from typing import Literal
import keyboard
import tkinter as tk
import tkinter.ttk as ttk
import requests

from screen_translate.Globals import gClass, path_logo_icon, dir_captured, fJson, app_name, dir_user_manual
from screen_translate.Logging import logger
from screen_translate.utils.Helper import nativeNotify, startFile, OpenUrl
from screen_translate.utils.Capture import captureFullScreen
from screen_translate.utils.Translate import translate
from screen_translate.utils.LangCode import engine_select_source_dict, engine_select_target_dict, engineList

from screen_translate.components.MBox import Mbox
from screen_translate.components.Tooltip import CreateToolTip
from screen_translate.components.History import HistoryWindow
from screen_translate.components.Settings import SettingWindow
from screen_translate.components.Capture_Window import CaptureWindow
from screen_translate.components.Capture_Snip import SnipWindow
from screen_translate.components.Mask import MaskWindow
from screen_translate.components.About import AboutWindow
from screen_translate.components.Ex_Query import QueryWindow
from screen_translate.components.Ex_Result import ResultWindow
from screen_translate.components.Log import LogWindow


# ----------------------------------------------------------------
def console():
    logger.info("=" * 50)
    logger.info("--- Welcome to Screen Translate ---")
    logger.info("Use The GUI Window to start capturing and translating")
    logger.info("You can minimize this window")
    logger.info("This window is for debugging purposes")


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
        gClass.mw = self  # type: ignore

        # ----------------------------------------------
        # Frames
        self.frame_1 = tk.Frame(self.root)
        self.frame_1.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.frame_1.bind("<Button-1>", lambda event: self.root.focus_set())

        self.frame_2_tb_q = tk.Frame(self.root)
        self.frame_2_tb_q.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.frame_3 = tk.Frame(self.root)
        self.frame_3.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.frame_3.bind("<Button-1>", lambda event: self.root.focus_set())

        self.frame_4_tb_res = tk.Frame(self.root)
        self.frame_4_tb_res.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # --- Top frame_1 ---
        # Button
        self.btn_translate = ttk.Button(self.frame_1, text="Translate", command=self.start_tl)
        self.btn_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_translate, "Translate the text in the top frame")

        self.btn_capture_translate = ttk.Button(self.frame_1, text="Capture & Translate", command=self.start_capture_window)
        self.btn_capture_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_capture_translate, "Capture and translate the text inside capture area. Need to generate the capture UI first")

        self.btn_snip_translate = ttk.Button(self.frame_1, text="Snip & Translate", command=self.start_snip_window)
        self.btn_snip_translate.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_snip_translate, "Snip and translate the selected text.")

        # Opacity
        self.slider_capture_opac = ttk.Scale(self.frame_1, from_=0.0, to=1.0, orient=tk.HORIZONTAL, command=self.opac_change)
        self.slider_capture_opac.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_capture_opac = tk.Label(self.frame_1, text="Capture Window Opacity: " + "0.8")
        self.lbl_capture_opac.pack(side=tk.LEFT, padx=5, pady=5)

        self.frame_status = tk.Frame(self.frame_1)
        self.frame_status.pack(side=tk.RIGHT, fill=tk.X, expand=False)

        self.lb_status = ttk.Progressbar(self.frame_status, orient=tk.HORIZONTAL, length=120, mode="determinate")
        self.lb_status.pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Top frame_2 ---
        # TB
        # Translation Textbox (Query/Source)
        self.frame_tb_query_bg = tk.Frame(self.frame_2_tb_q, bg="#7E7E7E")
        self.frame_tb_query_bg.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sb_query = tk.Scrollbar(self.frame_tb_query_bg)
        self.sb_query.pack(side=tk.RIGHT, fill=tk.Y)

        self.tb_query = tk.Text(
            self.frame_tb_query_bg,
            height=5,
            width=100,
            relief=tk.FLAT,
            font=(fJson.settingCache["tb_mw_q_font"], fJson.settingCache["tb_mw_q_font_size"]),
            fg=fJson.settingCache["tb_mw_q_font_color"],
            bg=fJson.settingCache["tb_mw_q_bg_color"],
            yscrollcommand=self.sb_query.set,
        )
        self.tb_query.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        self.tb_query.config(yscrollcommand=self.sb_query.set)
        self.sb_query.config(command=self.tb_query.yview)
        self.tb_query.bind("<KeyRelease>", self.tb_query_change)

        # --- Bottom frame_3 ---
        # Langoptions onstart
        self.lbl_engines = tk.Label(self.frame_3, text="TL Engine:")
        self.lbl_engines.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_engines, 'The provider use to translate the text. You can set it to "None" if you only want to use the OCR')

        self.cb_tl_engine = ttk.Combobox(self.frame_3, values=engineList, state="readonly")
        self.cb_tl_engine.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_tl_engine.bind("<<ComboboxSelected>>", self.cb_engine_change)

        self.lbl_source = tk.Label(self.frame_3, text="From:")
        self.lbl_source.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_source, "Source Language (Text to be translated)")

        self.cb_from = ttk.Combobox(self.frame_3, values=engine_select_source_dict["Google Translate"], state="readonly", width=29)
        self.cb_from.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_from.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("sourceLang", self.cb_from.get()))

        self.lbl_to = tk.Label(self.frame_3, text="To:")
        self.lbl_to.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_to, "Target Language (Results)")

        self.cb_to = ttk.Combobox(self.frame_3, values=engine_select_target_dict["Google Translate"], state="readonly", width=29)
        self.cb_to.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_to.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("targetLang", self.cb_to.get()))

        self.btn_swap = ttk.Button(self.frame_3, text="⮁ Swap", command=self.swapTl)
        self.btn_swap.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_clear = ttk.Button(self.frame_3, text="✕ Clear", command=self.clear_tb)
        self.btn_clear.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Bottom tk.Frame 2 ---
        # TB
        # Translation Textbox (Result)
        self.frame_tb_result_bg = tk.Frame(self.frame_4_tb_res, bg="#7E7E7E")
        self.frame_tb_result_bg.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sb_result = tk.Scrollbar(self.frame_tb_result_bg)
        self.sb_result.pack(side=tk.RIGHT, fill=tk.Y)

        self.tb_result = tk.Text(
            self.frame_tb_result_bg,
            height=5,
            width=100,
            relief=tk.FLAT,
            font=(fJson.settingCache["tb_mw_q_font"], fJson.settingCache["tb_mw_q_font_size"]),
            fg=fJson.settingCache["tb_mw_q_font_color"],
            bg=fJson.settingCache["tb_mw_q_bg_color"],
            yscrollcommand=self.sb_query.set,
        )
        self.tb_result.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        self.tb_result.config(yscrollcommand=self.sb_result.set)
        self.sb_result.config(command=self.tb_result.yview)
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
        self.filemenu2.add_command(label="Captured Image", command=self.open_Img_Captured, accelerator="F4")  # Open Captured img folder
        self.filemenu2.add_command(label="Log", command=self.open_Log)  # Open Error Log
        self.menubar.add_cascade(label="View", menu=self.filemenu2)

        self.filemenu3 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu3.add_command(label="Capture Window", command=self.open_Capture_Screen, accelerator="F5")  # Open Capture Screen Window
        self.filemenu3.add_command(label="Mask Window", command=self.open_Mask_Window, accelerator="Ctrl + Alt + F5")  # Open Mask window
        self.filemenu3.add_command(label="Query Box", command=self.open_Query_Box, accelerator="F6")
        self.filemenu3.add_command(label="Result Box", command=self.open_Result_Box, accelerator="F7")
        self.menubar.add_cascade(label="Generate", menu=self.filemenu3)

        self.filemenu4 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu4.add_command(label="Tesseract", command=self.openTesLink)  # Open Tesseract Downloads
        self.filemenu4.add_command(label="Libretranslate", command=self.openLibreTlLink)  # Open Tesseract Downloads
        self.filemenu4.add_command(label="Icon source", command=self.openIconSource)
        self.menubar.add_cascade(label="Get", menu=self.filemenu4)

        self.filemenu5 = tk.Menu(self.menubar, tearoff=0)
        self.filemenu5.add_command(label="Tutorial", command=self.open_Tutorial)  # Open Mbox Tutorials
        self.filemenu5.add_command(label="FAQ", command=self.open_Faq)  # Open FAQ
        self.filemenu5.add_command(label="Known Bugs", command=self.open_KnownBugs)  # Open Knownbugs
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Open User Manual", command=self.open_UserManual)  # Open user manual folder
        self.filemenu5.add_command(label="Open GitHub Repo", command=lambda aurl="https://github.com/Dadangdut33/Screen-Translate": OpenUrl(aurl))
        self.filemenu5.add_command(label="Open Changelog", command=self.open_Changelog)
        self.filemenu5.add_separator()
        self.filemenu5.add_command(label="Contributor", command=self.open_Contributor)  # Open Contributor
        self.filemenu5.add_command(label="About STL", command=self.open_About, accelerator="F1")  # Open about frame
        self.menubar.add_cascade(label="Help", menu=self.filemenu5)

        # Add to self.root
        self.root.config(menu=self.menubar)

        # Bind key shortcut
        self.root.bind("<F1>", self.open_About)
        self.root.bind("<F2>", self.open_Setting)
        self.root.bind("<F3>", self.open_History)
        self.root.bind("<F4>", self.open_Img_Captured)
        self.root.bind("<F5>", self.open_Capture_Screen)
        self.root.bind("<Control-Alt-F5>", self.open_Mask_Window)
        self.root.bind("<F6>", self.open_Query_Box)
        self.root.bind("<F7>", self.open_Result_Box)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.onInit()

        # --- Logo ---
        try:
            self.root.iconbitmap(path_logo_icon)
        except tk.TclError:
            logger.warning("Error Loading icon: Logo not found!")
        except Exception as e:
            logger.warning("Error loading icon")
            logger.exception(e)

    # --- Functions ---
    def onInit(self):
        self.slider_capture_opac.set(0.8)
        self.cb_tl_engine.set(fJson.settingCache["engine"])
        self.cb_from.set(fJson.settingCache["sourceLang"])
        self.cb_to.set(fJson.settingCache["targetLang"])
        if self.cb_tl_engine.get() == "None":
            self.cb_to["state"] = "disabled"

        try:
            if fJson.settingCache["hk_cap_window"] != "":
                keyboard.add_hotkey(fJson.settingCache["hk_cap_window"], gClass.hk_cap_window_callback)
            if fJson.settingCache["hk_snip_cap"] != "":
                keyboard.add_hotkey(fJson.settingCache["hk_snip_cap"], gClass.hk_snip_mode_callback)
        except KeyError as e:
            logger.error("Error: Invalid Hotkey Options")
            logger.exception(e)

        self.hkPollThread = threading.Thread(target=self.hkPoll, daemon=True)
        self.hkPollThread.start()

    def quit_app(self):
        gClass.running = False

        logger.info("Destroying windows...")
        gClass.sw.root.destroy()  # type: ignore  # setting window
        gClass.hw.root.destroy()  # type: ignore history window
        gClass.cw.root.destroy()  # type: ignore # capture window
        gClass.csw.root.destroy()  # type: ignore # capture snip window
        gClass.aw.root.destroy()  # type: ignore # about window
        gClass.lw.root.destroy()  # type: ignore # log window
        gClass.mask.root.destroy()  # type: ignore # mask window
        gClass.ex_qw.root.destroy()  # type: ignore # external query window
        gClass.ex_resw.root.destroy()  # type: ignore # external result window
        self.root.destroy()

        logger.info("Exiting...")
        try:
            sys.exit(0)
        except SystemExit:
            logger.info("Exit successful")
        except:
            logger.error("Exit failed, killing process")
            os._exit(0)

    # On Close
    def on_closing(self):
        """
        Confirmation on close
        """
        # Only show notification once
        if not self.notified_hidden:
            nativeNotify("Hidden to tray", "The app is still running in the background.", app_name, path_logo_icon)
            self.notified_hidden = True

        self.root.withdraw()

    # Open Setting Window
    def open_Setting(self, event=None):
        assert gClass.sw is not None
        gClass.sw.show()

    # Open History Window
    def open_History(self, event=None):
        assert gClass.hw is not None
        gClass.hw.show()

    # Open result box
    def open_Result_Box(self, event=None):
        assert gClass.ex_resw is not None
        gClass.ex_resw.show()

    # Open query box
    def open_Query_Box(self, event=None):
        assert gClass.ex_qw is not None
        gClass.ex_qw.show()

    # Open About Window
    def open_About(self, event=None):
        assert gClass.aw is not None
        gClass.aw.show()

    # Open Capture Window
    def open_Capture_Screen(self, event=None):
        assert gClass.cw is not None
        gClass.cw.show()

    # Open mask window
    def open_Mask_Window(self, event=None):
        assert gClass.mask is not None
        gClass.mask.show()

    # Open captured image folder
    def open_Img_Captured(self, event=None):
        startFile(dir_captured)

    # Open log window
    def open_Log(self, event=None):
        assert gClass.lw is not None
        gClass.lw.show()

    # Hotkey
    def hkPoll(self):
        while gClass.running:
            if gClass.hk_cw_pressed and not gClass.cw_hidden:  # If the hotkey for capture and translate is pressed
                time.sleep(fJson.settingCache["hk_cap_window_delay"] / 1000)
                self.start_capture_window()
                gClass.hk_cw_pressed = False

            if gClass.hk_snip_pressed:  # If the hotkey for snip and translate is pressed
                time.sleep(fJson.settingCache["hk_snip_cap_delay"] / 1000)
                self.start_snip_window()
                gClass.hk_snip_pressed = False

            time.sleep(0.1)

    # Slider
    def opac_change(self, event):
        value = float(event)
        if value < 0.025:
            value = 0.025

        self.lbl_capture_opac.config(text=f"Capture Window Opacity: {round(value, 3)}")

        if gClass.cw is not None:
            gClass.cw.change_opacity(str(value), fromOutside=True)

    def tb_query_change(self, event):
        gClass.insert_ex_q(self.tb_query.get(1.0, tk.END).strip())

    def tb_result_change(self, event):
        gClass.insert_ex_res(self.tb_result.get(1.0, tk.END).strip())

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
        Mbox("Info", "Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack", 0, self.root)
        logger.info("Please download the v5.0.0-alpha.20210811 Version (the latest version might be okay too) and install all language pack")
        OpenUrl("https://github.com/UB-Mannheim/tesseract/wiki")

    def openLibreTlLink(self):
        Mbox("Info", "You can follow the instruction on their github pages. It is recommended to build it with the models so you can use it fully offline.", 0, self.root)
        OpenUrl("https://github.com/LibreTranslate/LibreTranslate")

    # Open icon source
    def openIconSource(self):
        OpenUrl("https://icons8.com/")

    # Open known bugs
    def open_KnownBugs(self):
        Mbox(
            "Known Bugs",
            """- Monitor scaling needs to be 100% or it won't capture accurately (You can fix this easily by setting offset or set your monitor scaling to 100%)
        \r- Chinese translation doesn't work with the original method (deep_translator library) I don't know why. So i provided an alternative and that's why there is an \"alt\" options for chinese when using google translate (You should use it when translating chinese using google translate).""",
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
            Mbox("Error", "Changelog file not found\n\nProgram will now try open the one in the repository instead of the local copy.", 0, self.root)
            try:
                OpenUrl("https://github.com/Dadangdut33/Screen-Translate/blob/main/user_manual/Changelog.txt")
                # download
                req = requests.get("https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/user_manual/Changelog.txt")
                with open(dir_user_manual + r"\changelog.txt", "wb") as f:
                    f.write(req.content)
            except Exception as e:
                print("Error: " + str(e))
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
        tmp = self.cb_from.get()
        if self.cb_to.get() in self.cb_from["values"]:
            self.cb_from.set(self.cb_to.get())

        if tmp in self.cb_to["values"]:
            self.cb_to.set(tmp)

    # Clear TB
    def clear_tb(self):
        self.tb_query.delete(1.0, tk.END)
        self.tb_result.delete(1.0, tk.END)

    def cb_engine_change(self, _event=None):
        # save
        fJson.savePartialSetting("engine", self.cb_tl_engine.get())
        self.cb_lang_update()

    def cb_lang_update(self):
        # update
        self.cb_from["values"] = engine_select_source_dict[self.cb_tl_engine.get()]
        self.cb_to["values"] = engine_select_target_dict[self.cb_tl_engine.get()]

        if self.cb_from.get() not in self.cb_from["values"]:
            self.cb_from.current(0)

        if self.cb_to.get() not in self.cb_to["values"]:
            self.cb_to.current(0)

        if self.cb_tl_engine.get() == "None":
            self.cb_to["state"] = "disabled"
        else:
            self.cb_to["state"] = "readonly"

        # save
        fJson.savePartialSetting("sourceLang", self.cb_from.get())
        fJson.savePartialSetting("targetLang", self.cb_to.get())

    # -----------------------------------------------------------------
    def get_params(self):
        return self.cb_tl_engine.get(), self.cb_from.get(), self.cb_to.get(), self.tb_query.get(1.0, tk.END)

    def param_check(self, engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate", "None"], from_lang: str, to_lang: str, query: str):
        logger.info("Checking params...")
        logger.debug(f"engine: {engine} | source: {from_lang} | to: {to_lang}")
        # If source and destination are the same
        if engine != "None" and ((from_lang) == (to_lang)):
            gClass.lb_stop()
            logger.warn("Error Language is the same as source! Please choose a different language")
            Mbox("Error: Language target is the same as source", "Language target is the same as source! Please choose a different language", 2, self.root)
            return False

        if engine != "None" and from_lang == "Auto-Detect":
            gClass.lb_stop()
            logger.warn("Error: Invalid Language source! Must specify source langauge when using OCR")
            Mbox("Error: Invalid Source Language Selected", "Must specify source langauge when using OCR", 2, self.root)
            return False

        # If langto not set
        if to_lang == "Auto-Detect":
            gClass.lb_stop()
            logger.warn("Error: Invalid Language Selected! Must specify language destination")
            Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, self.root)
            return False

        # If the text is empty
        if len(query) == 0:
            gClass.lb_stop()
            logger.warn("Error: No text detected! Please select a text to translate")
            Mbox("Error: No text detected", "Please select a text to translate", 2, self.root)
            return False

        logger.info("Passed param check!")
        return True

    def start_tl(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query):  # type: ignore
            return

        if engine == "None":
            logger.warn("Error: No translation engine selected! Please select a translation engine if only translate!")
            Mbox("Error", "Please select a translation engine if only translate!", 0, self.root)
            return

        gClass.lb_start()
        try:
            self.tlThread = threading.Thread(target=translate, args=(query, from_lang, to_lang, engine), daemon=True)
            self.tlThread.start()
        except Exception as e:
            logger.exception(e)
            Mbox("Error", str(e), 0, self.root)
        gClass.lb_stop()

    def start_capture_window(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query):  # type: ignore
            return

        if gClass.cw_hidden:
            logger.warning("Capture window is not generated yet!")
            Mbox("Error", "Capture window is not generated yet!", 0, self.root)
            return

        assert gClass.cw is not None
        gClass.cw.start_capping()

    def start_snip_window(self):
        engine, from_lang, to_lang, query = self.get_params()

        if not self.param_check(engine, from_lang, to_lang, query):  # type: ignore
            return

        success, imgObj = captureFullScreen()
        if not success:
            Mbox("Error", f"Failed to start snipping mode.\nReason: {imgObj}", 0, self.root)
            return

        assert gClass.csw is not None
        gClass.csw.start_snipping(imgObj)


if __name__ == "__main__":
    console()

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
