import pyautogui
import os
import pytesseract
from datetime import datetime

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
    status_Success = False
    try:
        # Capture the designated location
        captured = pyautogui.screenshot(region=(coords[0], coords[1], coords[2], coords[3]))
        pytesseract.pytesseract.tesseract_cmd = tesseract_Location
        
        # Get the text from the image 
        wordsGet = pytesseract.image_to_string(captured, sourceLang)

        if cached:
            captured.save(dir_path + r'\img_cache\captured_' + datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.png')
            
        status_Success = True
    except:
        wordsGet = ''
    finally:
        return status_Success, wordsGet