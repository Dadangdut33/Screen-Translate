import json
import os
from .Mbox import Mbox
from pathlib import Path
dir_path = os.path.dirname(os.path.realpath(__file__))
jsons_path = os.path.join(dir_path, '../json/')
history_json_path = os.path.join(dir_path, '../json/History.json')
setting_json_path = os.path.join(dir_path, '../json/Setting.json')

class JsonHandler:
    settingsCache = None

    # Default Setting
    default_Setting = {
        "cached": True,
        "autoCopy": True,
        "offSetXYType": "No Offset",
        "offSetXY": ["auto", "auto"],
        "offSetWH": ["auto", "auto"],
        "tesseract_loc": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        "default_Engine": "Google Translate",
        "default_FromOnOpen": "Auto-Detect",
        "default_ToOnOpen": "English",
        "capture_Hotkey": "",
        "capture_HotkeyDelay": 1000
    }

    # -------------------------------------------------
    # Create dir if not exists
    def createDirIfGone(self):
        # Will create the dir if not exists
        if not os.path.exists(jsons_path):
            try:
                os.makedirs(jsons_path)
            except Exception as e:
                print("Error: " + str(e))
                Mbox("Error: ", str(e), 2)

    # -------------------------------------------------
    # Write, Append, Delete, Read, History
    def writeAdd_History(self, new_data):
        """Example of how the data should be written
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
                    "to": item['to'],
                    "query": item['query'],
                    "result": item['result'],
                    "engine": item['engine']
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
        return self.settingsCache
