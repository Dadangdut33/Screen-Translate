import os

# Dir Paths
dir_project: str = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
dir_user: str = os.path.abspath(os.path.join(dir_project, "user"))
dir_log: str = os.path.abspath(os.path.join(dir_project, "log"))
dir_captured: str = os.path.abspath(os.path.join(dir_project, "captured"))
dir_assets: str = os.path.abspath(os.path.join(dir_project, "assets"))
dir_user_manual: str = os.path.abspath(os.path.join(dir_project, "user_manual"))
dir_theme: str = os.path.abspath(os.path.join(dir_project, "theme"))
# ---------------------------- #
# Target Paths
path_to_app_exe: str = os.path.abspath(os.path.join(dir_project, "ScreenTranslate.exe"))
path_json_settings: str = os.path.join(dir_user, "settings.json")
path_json_history: str = os.path.join(dir_user, "history.json")
path_logo_icon: str = os.path.join(dir_assets, "logo.ico")
path_logo_png: str = os.path.join(dir_assets, "logo.png")
path_beep: str = os.path.join(dir_assets, "beep.wav")
path_keys: str = os.path.join(dir_user, "keys.json")
