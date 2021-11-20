import json
import os
from screen_translate.Mbox import Mbox
dir_path = os.path.dirname(os.path.realpath(__file__))
jsons_path = os.path.join(dir_path, '../json/')
history_json_path = os.path.join(dir_path, '../json/History.json')
setting_json_path = os.path.join(dir_path, '../json/Setting.json')

class JsonHandler:
    """
    [summary] 
        Create, Read, Update the json file
    [description]
        Returns: [type] -- [description]
    """
    settingsCache = None

    # Default Setting
    default_Setting = {
        "cached": True,
        "autoCopy": True,
        "offSetXYType": "No Offset",
        "offSetXY": [0, 0],
        "offSetWH": ["auto", "auto"],
        "snippingWindowGeometry": "auto",
        "tesseract_loc": "C:/Program Files/Tesseract-OCR/tesseract.exe",
        "default_Engine": "Google Translate",
        "default_FromOnOpen": "Auto-Detect",
        "default_ToOnOpen": "English",
        "captureLastValDelete": 0,
        "hotkey": {
            "captureAndTl": {
                "hk": "",
                "delay": 1000
            },
            "snipAndCapTl": {
                "hk": "",
                "delay": 0
            }
        },
        "Query_Box": {
            "font": {
                "family": "Segoe UI", 
                "size": 10, 
                "weight": "normal", 
                "slant": "roman", 
                "underline": 0, 
                "overstrike": 0
            },
            "bg": "#FFFFFF",
            "fg": "#000000",
        },
        "Result_Box": {
            "font": {
                "family": "Segoe UI", 
                "size": 10, 
                "weight": "normal", 
                "slant": "roman", 
                "underline": 0, 
                "overstrike": 0
            },
            "bg": "#FFFFFF",
            "fg": "#000000",
        },
        "Masking_Window": {
            "color": "#555555",
            "alpha": 0.8
        },
        "logging": {
            "enabled": False,
            "max_line": 25
        },
        "saveHistory": True,
        "checkUpdateOnStart": True,
        "enhance_Capture" : {
            "cv2_Contour": True,
            "grayscale": False,
            "background": "Auto-Detect",
            "debugmode": False
        },
        "show_no_text_alert": False
    }

    # -------------------------------------------------
    # Create dir if not exists
    def createDirIfGone(self):
        """
        Create the json directory if not exists
        """
        if not os.path.exists(jsons_path):
            try:
                os.makedirs(jsons_path)
            except Exception as e:
                print("Error: " + str(e))
                Mbox("Error: ", str(e), 2)

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
            newHistory = {
                "tl_history": []
            }
            countId = 0
            for item in file_data['tl_history']:
                old_data = {
                    "id": countId,
                    "from": item['from'],
                    "to": item['to'],
                    "query": item['query'],
                    "result": item['result'],
                    "engine": item['engine']
                }
                newHistory['tl_history'].append(old_data)
                countId += 1

            # Add the new data
            toAddNew = {
                "id": countId,
                "from": new_data['from'],
                "to": new_data['to'],
                "query": new_data['query'],
                "result": new_data['result'],
                "engine": new_data['engine']
            }

            newHistory['tl_history'].append(toAddNew)

            # Overwrite file
            self.createDirIfGone()
            with open(history_json_path,'w', encoding='utf-8') as f:
                json.dump(newHistory, f, ensure_ascii=False, indent = 4)
                is_Success = True
                status = "no error"

        except FileNotFoundError: # If file not found create new History.json with the new data provided
            # No need for popup for this one
            self.createDirIfGone()
            with open(history_json_path, 'w', encoding='utf-8') as f:
                toAddNew = {
                    "id": 0,
                    "from": new_data['from'],
                    "to": new_data['to'],
                    "query": new_data['query'],
                    "result": new_data['result'],
                    "engine": new_data['engine']
                }
                file_data = {
                    "tl_history": [toAddNew]
                }

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = "no error"
        except Exception as e:
            status = str(e)
            print("Error: " + str(e))
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
            self.createDirIfGone()
            with open(history_json_path, 'w', encoding='utf-8') as f:
                file_data = {
                    "tl_history": []
                }

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = "All of The History Data Have Been Deleted Successfully"
        except FileNotFoundError: # If file not found create new History.json but empty
            self.createDirIfGone()
            # No need for popup for this one
            with open(history_json_path, 'w', encoding='utf-8') as f:
                file_data = {
                    "tl_history": []
                }

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = r"Couldn't found History.Json, History now empty"
        except Exception as e:
            status = str(e)
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, status

    def deleteCertainHistory(self, index):
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
            file_data["tl_history"].pop(index)

            # Then
            # Overwrite the ID and add the new data
            newHistory = {
                "tl_history": []
            }

            countId = 0
            for item in file_data['tl_history']:
                old_data = {
                    "id": countId,
                    "from": item['from'],
                    "to": item['to'],
                    "query": item['query'],
                    "result": item['result'],
                    "engine": item['engine']
                }
                newHistory['tl_history'].append(old_data)
                countId += 1

            # Overwrite file
            self.createDirIfGone()
            with open(history_json_path,'w', encoding='utf-8') as f:
                json.dump(newHistory, f, ensure_ascii=False, indent = 4)
                is_Success = True
                status = "Selected History Has Been Deleted Successfully"
        except FileNotFoundError: # If file not found create new History.json but empty
            self.createDirIfGone()
            with open(history_json_path, 'w', encoding='utf-8') as f:
                file_data = {
                    "tl_history": []
                }

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = True
                status = r"Couldn't found History.Json, History now empty"
        except Exception as e:
            status = str(e)
            print("Error: " + str(e))
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
            self.createDirIfGone()
            with open(history_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                is_Success = True
        except FileNotFoundError: # If file not found create new History.json but empty
            self.createDirIfGone()
            with open(history_json_path, 'w', encoding='utf-8') as f:
                file_data = {
                    "tl_history": []
                }

                json.dump(file_data, f, ensure_ascii=False, indent=4)
                is_Success = False
                data = r"Couldn't found History.Json, History now empty"
                Mbox("Error", data, 2)
        except Exception as e:
            data = str(e)
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
        finally:
            return is_Success, data

    # -------------------------------------------------
    # Settings
    def writeSetting(self, data):
        """Write setting

        Args:
            data (dict): Data to write

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        is_Success = False
        status = ""
        try:
            self.createDirIfGone()
            with open(setting_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                status = "Setting has been changed successfully"
                is_Success = True
        except Exception as e:
            status = str(e)
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
        finally:
            self.settingsCache = data
            return is_Success, status

    def setDefault(self):
        """Set default setting

        Returns:
            bool: True if success, False if failed
            status: Status text of the operation
        """
        is_Success = False
        status = ""
        try:
            self.createDirIfGone()
            with open(setting_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.default_Setting, f, ensure_ascii=False, indent=4)
                status = "Successfully set setting to default"
                is_Success = True
        except Exception as e:
            status = str(e)
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
        finally:
            self.settingsCache = self.default_Setting
            return is_Success, status

    def loadSetting(self):
        """Load setting

        Returns:
            bool: True if success, False if failed
            data: The data of the setting
        """
        is_Success = False
        data = ""
        try:
            self.createDirIfGone()
            with open(setting_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                is_Success = True
        except FileNotFoundError as e:
            data = ["Setting file is not found", "Setting.json could not be loaded please do not move or delete the setting file.\n\nProgram will now automatically create and set the setting to default value"]
            # Not found popup handled in main
        except Exception as e:
            data = [str(e)]
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
        finally:
            self.settingsCache = data
            return is_Success, data

    def readSetting(self):
        """Read the currently loaded setting from the settings cache

        Returns:
            dict: The setting data
        """
        return self.settingsCache
