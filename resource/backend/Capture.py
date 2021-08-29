import pyautogui
import os
import pytesseract
import ctypes
from datetime import datetime

# Lang Code
from .LangCode import *

# Settings to capture all screens
from PIL import Image, ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# Get Path
dir_path = os.path.dirname(os.path.realpath(__file__))

def captureImg(coords, sourceLang, tesseract_Location, cached = False):
    """Capture Image and return text from it

    Args:
        coords (int): Coordinates and size of the screen to capture (x,y,w,h)
        sourceLang (string): The Language to be translated
        tesseract_Location (string): Tesseract .exe location
        cached (bool, optional): Cache/Save Image or not. Defaults to False.

    Returns:
        status, result: Success or Error, Result
    """
    # Language Code
    langCode = tesseract_Lang[sourceLang]

    is_Success = False
    wordsGet = ""
    try:
        # Capture the designated location
        captured = pyautogui.screenshot(region=(coords[0], coords[1], coords[2], coords[3]))
        pytesseract.pytesseract.tesseract_cmd = tesseract_Location
        
        # Get the text from the image 
        wordsGet = pytesseract.image_to_string(captured, langCode)

        if cached:
            captured.save(dir_path + r'\img_cache\captured_' + datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.png')
            
        is_Success = True
    except Exception as e:
        print("Error: " + str(e))
        wordsGet = str(e)
        if "is not installed or it's not in your PATH" in str(e):
            ctypes.windll.user32.MessageBoxW(0, "Invalid path location for tesseract.exe, please change it in the setting!", "Error: Tesseract Could not be Found", 0)
        elif "Failed loading language" in str(e):
            ctypes.windll.user32.MessageBoxW(0, "Language data not found! It could be that the language data is not installed! Please reinstall tesseract or download the language data and put it into Tesseract-OCR\\tessdata!\n\nThe official version that is used for this program is v5.0.0-alpha.20210811. You can download it from https://github.com/UB-Mannheim/tesseract/wiki or https://digi.bib.uni-mannheim.de/tesseract/", "Error: Failed Loading Language", 0)
        else:
            ctypes.windll.user32.MessageBoxW(0, e, "Error", 0)
    finally:
        return is_Success, wordsGet.strip()