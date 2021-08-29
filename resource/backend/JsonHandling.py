import json
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

# Default Setting
default_Setting = { 
    "cached": True,
    "offSetType": "auto",
    "offSetXY": ["auto", "auto"],
    "offSetWH": ["auto", "auto"],
    "tesseract_loc": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "default_Engine": "Google Translate",
    "default_FromOnOpen": "Auto-Detect",
    "default_ToOnOpen": "English"
}

# Read, Write, Append History
def write_History(new_data, filename):
    is_Success = False
    status = ""
    try: # datetime.now().strftime('%Y-%m-%d_%H%M%S')
        with open(dir_path + '/json/' + filename,'r+', encoding='utf-8') as f:
            # First we load existing data into a dict.
            file_data = json.load(f)
            
            # Join new_data with file_data inside emp_details
            file_data["tl_history"].append(new_data)
            
            # Sets file's current position at offset.
            f.seek(0)
            
            # convert back to json.
            json.dump(file_data, f, ensure_ascii=False, indent = 4)
            is_Success = True
            status = "no error"
    except FileNotFoundError:
        with open(dir_path + '/json/' + filename, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
            is_Success = True
            status = "no error"
    # Debug
    except Exception as e:
        status = e
        is_Success = False
    finally:
        return is_Success, status

# Read History
def readHistory():
    is_Success = False
    data = ""
    try:
        with open(dir_path + '/json/History.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            is_Success = True
    # Debug
    except Exception as e:
        data = e
    finally:
        return is_Success, data

# Settings
def writeSetting(data):
    is_Success = False
    status = ""
    try:
        with open(dir_path + '/json/Setting.json' , 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            status = "Setting has been changed successfully"
    except Exception as e:
        status = e
    finally:
        return is_Success, status

def setDefault():
    is_Success = False
    status = ""
    try:
        with open(dir_path + '/json/Setting.json' , 'w', encoding='utf-8') as f:
            json.dump(default_Setting, f, ensure_ascii=False, indent=4)
            status = "Successfuly set setting to default"
            is_Success = True
    except Exception as e:
        status = e
    finally:
        return is_Success, status

def readSetting():
    is_Success = False
    data = ""
    try:
        with open(dir_path + '/json/Setting.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            is_Success = True
    # Debug
    except FileNotFoundError:
        data = ["Setting file is not found", "Setting.json coould not be loaded please do not move or delete the setting file.\n\nProgram will now automatically create and set the setting to default value"]
    except Exception as e:
        data = [e]
    finally:
        return is_Success, data