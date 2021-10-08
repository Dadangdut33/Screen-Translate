import pyautogui
import os
import pytesseract
from .Mbox import Mbox
from datetime import datetime

# Lang Code
from .LangCode import *

# Settings to capture all screens
from PIL import Image, ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# Get Path
dir_path = os.path.dirname(os.path.realpath(__file__))
img_captured_path = os.path.join(dir_path, '../img_captured')

def createPicDirIfGone():
    # Will create the dir if not exists
    if not os.path.exists(img_captured_path):
        try:
            os.makedirs(img_captured_path)
        except Exception as e:
            print("Error: " + str(e))
            Mbox("Error: ", str(e), 2)
            raise

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
    try:
        langCode = tesseract_Lang[sourceLang]
    except KeyError as e:
        print("Error: Key Error\n" + str(e))
        Mbox("Key Error, On Assigning Language Code.\n" + str(e), "Error: Key Error", 2)

    is_Success = False
    wordsGet = ""
    try:
        # Capture the designated location
        captured = pyautogui.screenshot(region=(coords[0], coords[1], coords[2], coords[3]))
        pytesseract.pytesseract.tesseract_cmd = tesseract_Location
        
        # Get the text from the image 
        wordsGet = pytesseract.image_to_string(captured, langCode)

        if cached:
            createPicDirIfGone()
            captured.save(os.path.join(img_captured_path, 'captured_' + datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.png'))
            
        is_Success = True
    except Exception as e:
        print("Error: " + str(e))
        wordsGet = str(e)
        if "is not installed or it's not in your PATH" in str(e):
            Mbox("Error: Tesseract Could not be Found", "Invalid path location for tesseract.exe, please change it in the setting!", 2)
        elif "Failed loading language" in str(e):
            Mbox("Warning: Failed Loading Language", "Language data not found! It could be that the language data is not installed! Please reinstall tesseract or download the language data and put it into Tesseract-OCR\\tessdata!\n\nThe official version that is used for this program is v5.0.0-alpha.20210811. You can download it from https://github.com/UB-Mannheim/tesseract/wiki or https://digi.bib.uni-mannheim.de/tesseract/", 1)
        else:
            Mbox("Error", str(e), 2)
    finally:
        return is_Success, wordsGet.strip()

def captureAll():
    """Capture all screens and return the result"""
    # Capture all screens
    try:
        captured = pyautogui.screenshot()
        createPicDirIfGone()
        captured.save(os.path.join(img_captured_path, 'Monitor(s) Captured View'+ '.png'))
    except Exception as e:
        print("Error: " + str(e))
        Mbox("Error", str(e), 2)