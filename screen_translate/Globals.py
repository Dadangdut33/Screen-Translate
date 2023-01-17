import os

from .utils.Json import JsonHandler

# ---------------------------- #
# Dir Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_json: str = os.path.join(dir_project, "../json")
dir_log: str = os.path.join(dir_project, "../log")
dir_captured: str = os.path.join(dir_project, "../captured")
dir_assets: str = os.path.join(dir_project, "../assets")
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
        self.hotkeyCapTlPressed: bool = False
        self.hotkeySnipCapTlPressed: bool = False

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
        pass

    def lb_stop(self):
        pass

    def get_query(self):
        pass

    def insert_mw_q(self, text: str):
        pass

    def insert_mw_res(self, text: str):
        pass

    def clear_mw_q(self):
        pass

    def clear_mw_res(self):
        pass

    def insert_ex_q(self, text: str):
        pass

    def insert_ex_res(self, text: str):
        pass

    def clear_ex_q(self):
        pass

    def clear_ex_res(self):
        pass

    def update_ex_opac(self, opac: float):
        pass

    def update_mw_opac_slider(self, opac: float):
        pass

    def hotkeyCapTLCallback(self):
        """Callback for the hotkey to capture the screen"""
        self.hotkeyCapTlPressed = True

    def hotkeySnipCapTLCallback(self):
        """Callback for the hotkey to snip the screen"""
        self.hotkeySnipCapTlPressed = True


# --------------------- #
gClass: Globals = Globals()
