import numpy as np
import pyautogui
import os
import pytesseract
import cv2
from screen_translate.Mbox import Mbox
from datetime import datetime

# Lang Code
from screen_translate.LangCode import *

# Settings to capture all screens
from PIL import ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# Public methods
from screen_translate.Public import startfile

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

def captureImg(coords, sourceLang, tesseract_Location, saveImg = False, enhance_WithCv2 = False, grayScale = False, background = None, debugmode = False):
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
        return False, "Error: Key Error"

    is_Success = False
    wordsGet = ""
    try:
        # Capture the designated location
        captured = pyautogui.screenshot(region=(coords[0], coords[1], coords[2], coords[3]))
        
        # Set tesseract_Location
        pytesseract.pytesseract.tesseract_cmd = tesseract_Location

        # Enhance with cv2 if selected
        if enhance_WithCv2:
            # Convert captured img to cv2 format
            open_cv_image = np.array(captured) 
            # Convert RGB to BGR 
            open_cv_image = open_cv_image[:, :, ::-1].copy()
            # Convert the image to gray scale
            grayImg = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

            # debug
            if debugmode and grayScale: cv2.imshow("Grayscale Image", grayImg)

            # Threshtype
            threshType = cv2.THRESH_BINARY_INV if background == "Light" else cv2.THRESH_BINARY
            # Performing OTSU threshold
            ret, thresh = cv2.threshold(grayImg, 0, 255, cv2.THRESH_OTSU | threshType)

            # debug
            if debugmode: cv2.imshow("Thresh Image", thresh)

            # Specify structure shape and kernel size. 
            # Kernel size increases or decreases the area 
            # of the rectangle to be detected.
            # A smaller value like (10, 10) will detect 
            # each word instead of a sentence.
            rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

            # Applying dilation on the threshold image
            dilation = cv2.dilate(thresh, rectKernel, iterations = 1)

            # debug
            if debugmode: cv2.imshow("Dilation Image", dilation)

            # Finding contours in the image based on dilation
            contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            # Create a copy of captured image
            imgCopy = grayImg if grayScale else open_cv_image.copy()

            # Looping through the identified contours
            # Then rectangular part is cropped and passed on
            # to pytesseract for extracting text from it
            for cnt in contours[::-1]:  # Reverse the array because it actually starts from the bottom
                x, y, w, h = cv2.boundingRect(cnt)
                # Drawing a rectangle on copied image
                if debugmode:
                    rect = cv2.rectangle(imgCopy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imshow("Rectangle drawn on image", rect)

                # Cropping the text block for giving input to OCR
                cropped = imgCopy[y:y + h, x:x + w]
                
                # Apply OCR on the cropped image
                text = pytesseract.image_to_string(cropped, langCode)

                # Append the text into wordsarr
                wordsGet += text.strip() + "\n"

            if saveImg:
                createPicDirIfGone()
                captured.save(os.path.join(img_captured_path, 'captured_' + datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.png'))
        else:
            if grayScale:
                # Convert captured img to cv2 format
                open_cv_image = np.array(captured) 
                # Convert RGB to BGR 
                open_cv_image = open_cv_image[:, :, ::-1].copy()

                # Convert the image to gray scale
                grayImg = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

                if debugmode and grayScale: cv2.imshow("Grayscale Image", grayImg)

            # Get the text from the image 
            wordsGet = pytesseract.image_to_string(grayImg, langCode)

            if saveImg:
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
        startfile(dir_path + r"\..\img_captured\Monitor(s) Captured View.png")
    except Exception as e:
        print("Error: " + str(e))
        if "Invalid argument" in str(e):
            Mbox("Error image is still opened", "Please close the previous image first!", 2)
        else:
            Mbox("Error", str(e), 2)