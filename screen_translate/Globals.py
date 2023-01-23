import ast
import os
import shlex

from .utils.Json import JsonHandler

# ---------------------------- #
# Dir Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_json: str = os.path.join(dir_project, "../json")
dir_log: str = os.path.join(dir_project, "../log")
dir_captured: str = os.path.join(dir_project, "../captured")
dir_assets: str = os.path.join(dir_project, "../assets")
dir_user_manual: str = os.path.join(dir_project, "../user_manual")
# ---------------------------- #
# Target Paths
path_json_settings: str = os.path.join(dir_json, "settings.json")
path_json_history: str = os.path.join(dir_json, "history.json")
path_logo_icon: str = os.path.join(dir_assets, "logo.ico")
path_logo_png: str = os.path.join(dir_assets, "logo.png")
# ---------------------------- #
# name
app_name: str = "Screen Translate"
fJson: JsonHandler = JsonHandler(path_json_settings, path_json_history, dir_json, [dir_log, dir_captured])
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
        self.cw_hidden: bool = False

        # classes
        self.tray = None  # tray
        self.mw = None  # main window
        self.sw = None  # setting window
        self.hw = None  # history window
        self.cw = None  # capture window
        self.csw = None  # capture snip window
        self.aw = None  # about window
        self.lw = None  # log window
        self.mask = None  # mask window
        self.ex_qw = None  # external query window
        self.ex_resw = None  # external result window

    def lb_start(self):
        assert self.mw is not None
        self.mw.lb_status.config(cursor="watch", mode="indeterminate")
        self.mw.lb_status.start()

    def lb_stop(self):
        assert self.mw is not None
        self.mw.lb_status.config(cursor="arrow", mode="determinate")
        self.mw.lb_status.stop()

    def insert_mw_q(self, text: str):
        assert self.mw is not None
        self.mw.tb_query.insert(1.0, text)

    def insert_mw_res(self, text: str):
        assert self.mw is not None
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
        text += ast.literal_eval(shlex.quote(fJson.settingCache["replaceNewLineWith"]))  # set new text

        self.ex_qw.labelText.config(text=text)
        self.ex_qw.check_height_resize()

    def insert_ex_res(self, text: str):
        assert self.ex_resw is not None
        text = text.strip()
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


# --------------------- #
gClass: Globals = Globals()
