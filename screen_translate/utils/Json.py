import json
import os
import logging
from typing import List

from notifypy import Notify

from screen_translate.components.MBox import Mbox
from screen_translate.Logging import logger
from screen_translate._version import __setting_version__

default_setting = {
    "version": __setting_version__,
    "checkUpdateOnStart": True,
    # ------------------ #
    # App settings
    "cached": True,
    "autoCopy": True,
    "offSetXYType": "No Offset",
    "offSetX": 0,
    "offSetY": 0,
    "offSetW": "auto",
    "offSetH": "auto",
    "snippingWindowGeometry": "auto",
    "saveHistory": True,
    "supress_alert": True,
    # ------------------ #
    # logging
    "keep_log": False,
    "log_level": "DEBUG",  # INFO DEBUG WARNING ERROR
    # ------------------ #
    # runtime option
    "engine": "Google Translate",
    "sourceLang": "Auto-Detect",
    "targetLang": "English",
    # ------------------ #
    # Capture
    "tesseract_loc": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "replaceNewLine": True,
    "replaceNewLineWith": " ",
    "captureLastValDelete": 0,
    "saveImg": True,
    # capture enhancement
    "enhance_with_cv2_Contour": True,
    "enhance_with_grayscale": False,
    "enhance_background": "Auto-Detect",
    "enhance_debugmode": False,
    # ------------------ #
    # mask window
    "mask_window_bg_color": "#FFFFFF",
    # ------------------ #
    # libre
    "libre_api_key": "",
    "libre_host": "libretranslate.de",
    "libre_port": "",
    "libre_https": True,
    # ------------------ #
    # hotkey
    "hk_cap_tl": "",
    "hk_cap_tl_delay": 1000,
    "hk_snip_cap_tl": "",
    "hk_snip_cap_tl_delay": 0,
    # ------------------ #
    # detached window
    "tb_mw_q_font": "TKDefaultFont",
    "tb_mw_q_font_bold": False,
    "tb_mw_q_font_size": 10,
    "tb_mw_q_font_color": "#000000",
    "tb_mw_q_bg_color": "#FFFFFF",
    "tb_mw_res_font": "TKDefaultFont",
    "tb_mw_res_font_bold": False,
    "tb_mw_res_font_size": 10,
    "tb_mw_res_font_color": "#000000",
    "tb_mw_res_bg_color": "#FFFFFF",
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
    "masking_window_color": "#555555",
}


def localNotify(title: str, msg: str):
    notification = Notify()
    notification.application_name = "Screen Translate"
    notification.title = title
    notification.message = msg
    notification.send()


class JsonHandler:
    """
    Class to handle Create, Read, & Update of json files
    """

    # -------------------------------------------------
    def __init__(self, settingPath: str, historyPath: str, jsonDir: str, checkdirs: list[str]):
        self.settingCache = {}
        self.settingPath = settingPath
        self.historyPath = historyPath
        self.jsonDir = jsonDir
        self.createDirectoryIfNotExist(self.jsonDir)  # setting dir
        for checkdir in checkdirs:
            self.createDirectoryIfNotExist(checkdir)
        self.createDefaultSettingIfNotExist()  # setting file

        # Load setting
        success, msg, data = self.loadSetting()
        if success:
            self.settingCache = data
            # verify loaded setting
            success, msg, data = self.verifyLoadedSetting(data)
            if not success:
                self.settingCache = default_setting
                Mbox("Error: Verifying setting file", "Setting reverted to default. Details: " + msg, 2)
                logger.warning("Error verifying setting file: " + msg)

            # verify setting version
            if self.settingCache["version"] != __setting_version__:
                self.settingCache = default_setting  # load default
                self.saveSetting(self.settingCache)  # save
                # notify
                Mbox("Setting file is outdated", "Setting has been reverted to default setting.", 2)
                logger.warning("Setting file is outdated. Setting has been reverted to default setting.")
        else:
            self.settingCache = default_setting
            logger.error("Error loading setting file: " + msg)
            Mbox("Error", "Error: Loading setting file. " + self.settingPath + "\nReason: " + msg, 2)

        # set logger level based on setting
        logger.setLevel(logging.getLevelName(self.settingCache["log_level"]))

    # Create dir if not exists
    def createDirectoryIfNotExist(self, path: str):
        """
        Create directory if it doesn't exist
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            logger.exception(e)
            localNotify("Error", "Error: Creating directory. " + path + "\nReason: " + str(e))

    def createDefaultSettingIfNotExist(self):
        """
        Create default json file if it doesn't exist
        """
        path = self.settingPath
        try:
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception("Error creating default setting file: " + str(e))
            localNotify("Error", "Error: Creating default setting file. " + path + "\nReason: " + str(e))

    # -------------------------------------------------
    # Write, Append, Delete, Read, History
    def writeAdd_History(self, new_data):
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
        is_Success = False
        status = ""
        try:
            # Get current history, ignore the status
            x, file_data = self.readHistory()

            # Overwrite the ID and add the new data
            newHistory = {"tl_history": []}
            countId = 0
            for item in file_data["tl_history"]:  # type: ignore
                old_data = {"id": countId, "from": item["from"], "to": item["to"], "query": item["query"], "result": item["result"], "engine": item["engine"]}  # type: ignore
                newHistory["tl_history"].append(old_data)
                countId += 1

            # Add the new data
            toAddNew = {"id": countId, "from": new_data["from"], "to": new_data["to"], "query": new_data["query"], "result": new_data["result"], "engine": new_data["engine"]}

            newHistory["tl_history"].append(toAddNew)

            # Overwrite file
            with open(self.historyPath, "w", encoding="utf-8") as f:
                json.dump(newHistory, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = "no error"

        except FileNotFoundError:  # If file not found create new History.json with the new data provided
            # No need for popup for this one
            with open(self.historyPath, "w", encoding="utf-8") as f:
                toAddNew = {"id": 0, "from": new_data["from"], "to": new_data["to"], "query": new_data["query"], "result": new_data["result"], "engine": new_data["engine"]}
                file_data = {"tl_history": [toAddNew]}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = "no error"
        except Exception as e:
            status = str(e)
            logger.exception(e)
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, status

    def deleteAllHistory(self):
        """Delete all history

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        is_Success = False
        status = ""
        try:
            with open(self.historyPath, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = "All of The History Data Have Been Deleted Successfully"
        except FileNotFoundError:  # If file not found create new History.json but empty
            # No need for popup for this one
            with open(self.historyPath, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = r"Couldn't found History.Json, History now empty"
        except Exception as e:
            status = str(e)
            logger.exception(e)
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, status

    def deleteCertainHistory(self, indexList: List[int]):
        """Delete certain history

        Args:
            index (int): Index of the history to delete

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        is_Success = False
        status = ""
        try:
            # Get current history, ignore the status
            x, file_data = self.readHistory()

            # Pop the selected value first
            for i in indexList:
                file_data["tl_history"].pop(i)  # type: ignore

            # Then
            # Overwrite the ID and add the new data
            newHistory = {"tl_history": []}

            countId = 0
            for item in file_data["tl_history"]:  # type: ignore
                old_data = {"id": countId, "from": item["from"], "to": item["to"], "query": item["query"], "result": item["result"], "engine": item["engine"]}  # type: ignore
                newHistory["tl_history"].append(old_data)
                countId += 1

            # Overwrite file
            with open(self.historyPath, "w", encoding="utf-8") as f:
                json.dump(newHistory, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = f"{len(indexList)} Selected History Has Been Deleted Successfully"
        except FileNotFoundError:  # If file not found create new History.json but empty
            with open(self.historyPath, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = r"Couldn't found History.Json, History now empty"
        except Exception as e:
            status = str(e)
            logger.exception(e)
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, status

    # Read History
    def readHistory(self):
        """Read history

        Returns:
            bool: True if success, False if failed
            data: Data of the history
        """
        is_Success = False
        data = ""
        try:
            with open(self.historyPath, "r", encoding="utf-8") as f:
                data = json.load(f)
                is_Success = True
        except FileNotFoundError:  # If file not found create new History.json but empty
            with open(self.historyPath, "w", encoding="utf-8") as f:
                file_data = {"tl_history": []}

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = False
                data = r"Couldn't found History.Json, History now empty"
                Mbox("Error", data, 2)

        except Exception as e:
            data = str(e)
            logger.exception(e)
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, data

    # -------------------------------------------------
    # Settings
    def saveSetting(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.settingPath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.settingCache = data
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def savePartialSetting(self, key: str, value):
        """
        Save only a part of the setting
        """
        self.settingCache[key] = value
        success, msg = self.saveSetting(self.settingCache)

        if not success:
            localNotify("Error saving setting file", "Reason: " + msg)
            logger.error("Error saving setting file: " + msg)

    def loadSetting(self):
        """
        Load json file
        """
        success: bool = False
        msg: str = ""
        data: dict = {}
        try:
            with open(self.settingPath, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def verifyLoadedSetting(self, data: dict):
        """
        Verify loaded setting
        """
        success: bool = False
        msg: str = ""
        try:
            # check each key
            for key in default_setting:
                if key not in data:
                    data[key] = default_setting[key]

            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def getSetting(self):
        """
        Get setting value
        """
        return self.settingCache
