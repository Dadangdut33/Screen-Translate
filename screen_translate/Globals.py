import os
import ast
import shlex
import arabic_reshaper
from typing import List, Optional
from tkinter import ttk

from .utils.Json import JsonHandler

# ---------------------------- #
# Dir Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_user: str = os.path.abspath(os.path.join(dir_project, "..", "user"))
dir_log: str = os.path.abspath(os.path.join(dir_project, "..", "log"))
dir_captured: str = os.path.abspath(os.path.join(dir_project, "..", "captured"))
dir_assets: str = os.path.abspath(os.path.join(dir_project, "..", "assets"))
dir_user_manual: str = os.path.abspath(os.path.join(dir_project, "..", "user_manual"))
dir_theme: str = os.path.abspath(os.path.join(dir_project, "..", "theme"))
# ---------------------------- #
# Target Paths
path_to_app_exe: str = os.path.abspath(os.path.join(dir_project, "..", "ScreenTranslate.exe"))
path_json_settings: str = os.path.join(dir_user, "settings.json")
path_json_history: str = os.path.join(dir_user, "history.json")
path_logo_icon: str = os.path.join(dir_assets, "logo.ico")
path_logo_png: str = os.path.join(dir_assets, "logo.png")
# ---------------------------- #
# name
app_name: str = "Screen Translate"
reg_key_name: str = f'"{path_to_app_exe}"' + " -s"
fJson: JsonHandler = JsonHandler(path_json_settings, path_json_history, dir_user, [dir_log, dir_captured])
reshape_lang_list = ["arabic", "urdu", "faroese"]
# ---------------------------- #
class Globals:
    """
    Class containing all the need *static* variables for the UI. It also contains some methods for the stuff to works.
    Stored like this in order to allow other file to use the same thing without circular import error.
    """

    # ----------------------------------------------------------------------
    def __init__(self):
        # Flags
        self.running: bool = True
        self.capturing: bool = True
        self.translating: bool = True
        self.hk_cw_pressed: bool = False
        self.hk_snip_pressed: bool = False
        self.cw_hidden: bool = True

        # ---------------------------- #
        self.native_theme: str = ""
        self.theme_lists: List[str] = []
        self.style: Optional[ttk.Style] = None

        # ---------------------------- #
        # classes
        self.tray = None  # tray
        """Tray app class"""
        self.mw = None
        """Main window class"""
        self.sw = None
        """Setting window class"""
        self.hw = None
        """History window class"""
        self.cw = None
        """Capture window class"""
        self.csw = None
        """Capture snip window class"""
        self.aw = None
        """About window class"""
        self.lw = None
        """Log window class"""
        self.mask = None
        """Mask window class"""
        self.ex_qw = None
        """External / Detached query window class"""
        self.ex_resw = None
        """External / Detached result window class"""

    def lb_start(self):
        assert self.mw is not None
        self.mw.lb_status.config(cursor="watch", mode="indeterminate")
        self.mw.lb_status.start(5)

    def lb_stop(self):
        assert self.mw is not None
        self.mw.lb_status.config(cursor="arrow", mode="determinate")
        self.mw.lb_status.stop()

    def slider_mw_change(self, value: float, update_slider: bool = False):
        assert self.mw is not None
        self.mw.lbl_capture_opac.config(text=f"Capture Window Opacity: {round(value, 3)}")
        if update_slider:
            self.mw.slider_capture_opac.config(value=value)

    def slider_cw_change(self, value: float, update_slider: bool = False):
        assert self.cw is not None
        self.cw.root.attributes("-alpha", value)
        self.cw.fTooltip.opacity = value
        self.cw.lbl_opacity.config(text=f"Opacity: {round(value, 3)}")
        if update_slider:
            self.cw.slider_opacity.config(value=value)

    def insert_mw_q(self, text: str):
        assert self.mw is not None
        if fJson.settingCache["sourceLang"].lower() in reshape_lang_list:
            text = arabic_reshaper.reshape(text)

        self.mw.tb_query.insert(1.0, text)

    def insert_mw_res(self, text: str):
        assert self.mw is not None
        if fJson.settingCache["targetLang"].lower() in reshape_lang_list:
            text = arabic_reshaper.reshape(text)

        self.mw.tb_result.insert(1.0, text)

    def clear_mw_q(self):
        assert self.mw is not None
        self.mw.tb_query.delete(1.0, "end")

    def clear_mw_res(self):
        assert self.mw is not None
        self.mw.tb_result.delete(1.0, "end")

    def insert_ex_q(self, text: str):
        assert self.ex_qw is not None
        text = text.strip()
        if fJson.settingCache["sourceLang"].lower() in reshape_lang_list:
            text = arabic_reshaper.reshape(text)
        text += ast.literal_eval(shlex.quote(fJson.settingCache["replaceNewLineWith"]))  # set new text

        self.ex_qw.labelText.config(text=text)
        self.ex_qw.check_height_resize()

    def insert_ex_res(self, text: str):
        assert self.ex_resw is not None
        text = text.strip()
        if fJson.settingCache["targetLang"].lower() in reshape_lang_list:
            text = arabic_reshaper.reshape(text)
        text += ast.literal_eval(shlex.quote(fJson.settingCache["replaceNewLineWith"]))  # set new text

        self.ex_resw.labelText.config(text=text)
        self.ex_resw.check_height_resize()

    def clear_ex_q(self):
        assert self.ex_qw is not None
        self.ex_qw.labelText.config(text="")

    def clear_ex_res(self):
        assert self.ex_resw is not None
        self.ex_resw.labelText.config(text="")

    def hk_cap_window_callback(self):
        """Callback for the hotkey to capture the screen"""
        self.hk_cw_pressed = True

    def hk_snip_mode_callback(self):
        """Callback for the hotkey to snip the screen"""
        self.hk_snip_pressed = True

    def update_mw_setting(self):
        """Update the main window parameter/setting"""
        assert self.mw is not None
        self.mw.cb_tl_engine.set(fJson.settingCache["engine"])
        self.mw.cb_sourceLang.set(fJson.settingCache["sourceLang"])
        self.mw.cb_targetLang.set(fJson.settingCache["targetLang"])
        self.mw.cb_lang_update()

    def update_ex_cw_setting(self):
        """Update the capture window parameter/setting"""
        assert self.cw is not None
        self.cw.bgType.set(fJson.settingCache["enhance_background"])
        self.cw.cv2Contour.set(fJson.settingCache["enhance_with_cv2_Contour"])
        self.cw.grayscale.set(fJson.settingCache["enhance_with_grayscale"])
        self.cw.debugMode.set(fJson.settingCache["enhance_debugmode"])
        self.cw.engine.set(fJson.settingCache["engine"])
        self.cw.sourceLang.set(fJson.settingCache["sourceLang"])
        self.cw.targetLang.set(fJson.settingCache["targetLang"])

    def update_sw_setting(self):
        """Update the setting window parameter/setting"""
        assert self.sw is not None

        self.sw.cb_OCR_bg.set(fJson.settingCache["enhance_background"])
        self.sw.cbtnInvoker(fJson.settingCache["enhance_with_cv2_Contour"], self.sw.cbtn_OCR_cv2contour)
        self.sw.cbtnInvoker(fJson.settingCache["enhance_with_grayscale"], self.sw.cbtn_OCR_grayscale)
        self.sw.cbtnInvoker(fJson.settingCache["enhance_debugmode"], self.sw.cbtn_OCR_debug)

        self.sw.entry_maskwindow_color.delete(0, "end")
        self.sw.entry_maskwindow_color.insert(0, fJson.settingCache["mask_window_color"])

    def update_mask_setting(self):
        assert self.mask is not None

        self.mask.root["bg"] = fJson.settingCache["mask_window_color"]
        self.mask.f_1["bg"] = fJson.settingCache["mask_window_color"]
        self.mask.menuDropdown.entryconfig(0, label=f"Color: {fJson.settingCache['mask_window_color']}")


# --------------------- #
gClass: Globals = Globals()
