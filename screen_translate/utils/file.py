import json
import os
from typing import Dict, List

import darkdetect
from loguru import logger

from screen_translate._path import dir_user, path_json_history, path_json_settings
from screen_translate._version import __setting_version__

from .helper import create_dir_if_gone, native_notify

default_setting = {
    "version": __setting_version__,
    "checkUpdateOnStart": True,
    # ------------------ #
    # App settings
    "keep_image": True,
    "auto_copy_captured": True,
    "auto_copy_translated": False,
    "save_history": True,
    "supress_no_text_alert": True,
    "run_on_startup": True,
    "theme": "sv-dark" if darkdetect.isDark() else "sv-light",
    # ------------------ #
    # logging
    "keep_log": False,
    "log_level": "DEBUG",  # INFO DEBUG WARNING ERROR
    "auto_scroll_log": True,
    "auto_refresh_log": True,
    # ------------------ #
    # capture window offsets
    "offSetXYType": "Custom Offset",
    "offSetX": "auto",
    "offSetY": "auto",
    "offSetW": "auto",
    "offSetH": "auto",
    # ------------------ #
    # snipping window geometry
    "snippingWindowGeometry": "auto",
    # ------------------ #
    # runtime option
    "engine": "Google Translate",
    "sourceLang": "English",
    "targetLang": "Japanese",
    # ------------------ #
    # Capture
    "tesseract_loc": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "tesseract_config": "",
    "tesseract_psm5_vertical": True,
    "replaceNewLine": True,
    "replaceNewLineWith": " ",
    "captureLastValDelete": 0,
    # window hide on capture
    "hide_mw_on_cap": False,
    "hide_ex_qw_on_cap": True,
    "hide_ex_resw_on_cap": True,
    # capture enhancement
    "enhance_background": "Auto-Detect",
    "enhance_with_cv2_Contour": True,
    "enhance_with_grayscale": False,
    "enhance_debugmode": False,
    # ------------------ #
    # mask window
    "mask_window_bg_color": "#FFFFFF",
    # ------------------ #
    # libre
    "libre_api_key": "",
    "libre_host": "translate.argosopentech.com",
    "libre_port": "",
    "libre_https": True,
    # ------------------ #
    # hotkey
    "hk_cap_window": "",
    "hk_cap_window_delay": 1000,
    "hk_snip_cap": "ctrl+alt+t",
    "hk_snip_cap_delay": 0,
    # ------------------ #
    # detached window
    "tb_mw_q_font": "TKDefaultFont",
    "tb_mw_q_font_bold": False,
    "tb_mw_q_font_size": 10,
    "tb_mw_res_font": "TKDefaultFont",
    "tb_mw_res_font_bold": False,
    "tb_mw_res_font_size": 10,
    "tb_ex_q_font": "TKDefaultFont",
    "tb_ex_q_font_bold": False,
    "tb_ex_q_font_size": 10,
    "tb_ex_q_font_color": "#FFFFFF",
    "tb_ex_q_bg_color": "#000000",
    "tb_ex_res_font": "TKDefaultFont",
    "tb_ex_res_font_bold": False,
    "tb_ex_res_font_size": 10,
    "tb_ex_res_font_color": "#FFFFFF",
    "tb_ex_res_bg_color": "#000000",
    "mask_window_color": "#555555",
}


class JsonHandler:
    """
    Class to handle Create, Read, & Update of json files
    """
    def __init__(self, checkdirs: List[str]):
        self.setting_cache = {}
        create_dir_if_gone(dir_user)
        for checkdir in checkdirs:
            create_dir_if_gone(checkdir)

        self.create_default_if_none()

        # Load setting
        success, msg, data = self.load_setting()
        if success:
            self.setting_cache = data
            # verify loaded setting
            success, msg, data = self.verify_loaded_setting(data)
            if not success:
                self.setting_cache = default_setting
                native_notify("Error: Verifying setting file", f"Setting reverted to default. Details: {msg}")
                logger.warning(f"Error verifying setting file: {msg}")

            # verify setting version
            if self.setting_cache["version"] != __setting_version__:
                self.setting_cache = default_setting  # load default
                self.save_setting(self.setting_cache)  # save
                native_notify("Setting file is outdated", "Setting has been reverted to default setting.")
                logger.warning("Setting file is outdated. Setting has been reverted to default setting.")
        else:
            self.setting_cache = default_setting
            logger.error(f"Error loading setting file: {msg}")
            native_notify("Error Loading setting file", f"Details: {msg}")

    def create_default_if_none(self):
        """
        Create default json file if it doesn't exist
        """
        try:
            if not os.path.exists(path_json_settings):
                with open(path_json_settings, "w", encoding="utf-8") as f:
                    json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception(e)
            logger.error("Error creating default setting file")
            native_notify("Error creating default setting file", f"Details: {e}")

    # -------------------------------------------------
    # History Handler
    # -------------------------------------------------
    # Read History
    def read_history(self):
        """Read history

        Returns:
            bool: True if success, False if failed
            data: Data of the history
        """
        success = False
        data = None
        try:
            with open(path_json_history, "r", encoding="utf-8") as f:
                data = json.load(f)
                success = True
        except FileNotFoundError:  # If file not found create new History.json but empty
            with open(path_json_history, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                success = False
                data = {"tl_history": []}

        except Exception as e:
            data = str(e)
            logger.exception(e)
            native_notify("Error reading history", str(e))  # on uncaught error

        return success, data

    def write_add_history(self, new_data):
        """Write and or add history

        # Example of how the data should be written
            new_data = {
                # ID Will be auto generated here
                "from": "en",
                "to": "jp",
                "query": "apple",
                "result": "アップル",
                "engine": "deepl"
            }
        """
        success = False
        msg = ""
        try:
            # Get current history, ignore the status
            _, file_data = self.read_history()

            assert isinstance(file_data, Dict)

            # Rearrange ID and add new data
            c_id = 0
            for item in file_data["tl_history"]:
                item["id"] = c_id
                c_id += 1

            file_data["tl_history"].append(
                {
                    "id": c_id,
                    "from": new_data["from"],
                    "to": new_data["to"],
                    "query": new_data["query"],
                    "result": new_data["result"],
                    "engine": new_data["engine"]
                }
            )

            # Overwrite file
            with open(path_json_history, "w", encoding="utf-8") as f:
                json.dump(file_data, f, ensure_ascii=False, indent=4)
                success = True

        except Exception as e:
            msg = str(e)
            logger.exception(e)
            native_notify("Error updating history", str(e))

        return success, msg

    def clear_history(self):
        """Delete all history

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        success = False
        msg = ""
        try:
            with open(path_json_history, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}
                json.dump(file_data, f, ensure_ascii=False, indent=4)
                success = True
        except Exception as e:
            msg = str(e)
            logger.exception(e)
            native_notify("Error clearing history", str(e))

        return success, msg

    def delete_x_history(self, delete_indexes: List[int]):
        """Delete certain history

        Args:
            index (int): Index of the history to delete

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        success = False
        msg = ""
        try:
            # Get current history, ignore the status
            _, file_data = self.read_history()
            assert isinstance(file_data, Dict)

            # remove the id from the list
            for index in delete_indexes:
                file_data["tl_history"] = [item for item in file_data["tl_history"] if item["id"] != index]

            # Overwrite the ID and add the new data
            c_id = 0
            for item in file_data["tl_history"]:
                item["id"] = c_id
                c_id += 1

            # Overwrite file
            with open(path_json_history, "w", encoding="utf-8") as f:
                json.dump(path_json_history, f, ensure_ascii=False, indent=4)
                success = True
                msg = f"{len(delete_indexes)} selected history has been deleted successfully"

        except Exception as e:
            msg = str(e)
            logger.exception(e)
            native_notify("Error deleting history indexes", str(e))

        return success, msg

    # -------------------------------------------------
    # Settings handler
    # -------------------------------------------------
    def save_setting(self, data: Dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(path_json_settings, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.setting_cache = data
        except Exception as e:
            msg = str(e)
            logger.exception(e)
            native_notify("Error saving setting file", f"Reason: {msg}")

        return success, msg

    def save_setting_partial(self, key: str, value):
        """
        Save only a part of the setting
        """
        self.setting_cache[key] = value
        success, msg = self.save_setting(self.setting_cache)

        return success, msg

    def load_setting(self):
        """
        Load json file
        """
        success: bool = False
        msg: str = ""
        data: Dict = {}
        try:
            with open(path_json_settings, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = True
        except Exception as e:
            msg = str(e)
            logger.exception(e)

        return success, msg, data

    def verify_loaded_setting(self, data: Dict):
        """
        Verify loaded setting
        """
        success: bool = False
        msg: str = ""

        try:
            for key, _ in default_setting.items():
                if key not in data:
                    data[key] = default_setting[key]

            success = True
        except Exception as e:
            msg = str(e)

        return success, msg, data

    def get_setting(self):
        """
        Get setting value
        """
        return self.setting_cache

    def set_default(self):
        """
        Set default setting
        """
        self.setting_cache = default_setting
        success, msg = self.save_setting(self.setting_cache)

        return success, msg
