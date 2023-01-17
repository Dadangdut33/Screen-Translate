import os
from datetime import datetime
from typing import List

import numpy as np
import pyautogui
import pytesseract
import cv2

from screen_translate.Logging import logger
from screen_translate.components.MBox import Mbox
from screen_translate.Globals import fJson, dir_captured
from .Helper import startFile
from .LangCode import tesseract_lang

# Settings to capture all screens
from PIL import ImageGrab
from functools import partial

ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)


def createPicDirIfGone():
    """
    Create the directory if it does not exist
    """
    # Will create the dir if not exists
    if not os.path.exists(dir_captured):
        try:
            os.makedirs(dir_captured)
        except Exception as e:
            logger.exception("Error: " + str(e))
            Mbox("Error: ", str(e), 2)


def ocrFromCoords(coords: List[int]):
    """Capture Image and return text from it

    Args:
        coords (int): Coordinates and size of the screen to capture (x,y,w,h)
        sourceLang (string): The Language to be translated
    Returns:
        status, result: Success or Error, Result
    """
    # Language Code
    try:
        sourceLang = fJson.settingCache["sourceLang"]
        langCode = tesseract_lang[sourceLang]
    except KeyError as e:
        logger.exception("Error: Key Error\n" + str(e))
        Mbox("Key Error, On Assigning Language Code.\n" + str(e), "Error: Key Error", 2)
        return False, "Error: Key Error"

    success = False
    result = ""
    try:
        # Capture the designated location
        captured = pyautogui.screenshot(region=(coords[0], coords[1], coords[2], coords[3]))  # type: ignore

        # Set variables
        pytesseract.pytesseract.tesseract_cmd = fJson.settingCache["tesseract_loc"]
        enhance_withCv2 = fJson.settingCache["enhance_with_cv2_Contour"]
        grayscale = fJson.settingCache["enhance_with_grayscale"]
        debugmode = fJson.settingCache["enhance_debugmode"]
        background = fJson.settingCache["enhance_background"]
        replaceNewLine = fJson.settingCache["replaceNewLine"]
        saveImg = fJson.settingCache["saveImg"]
        saveName = os.path.join(dir_captured, "ScreenTranslate_" + datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".png")

        # Enhance with cv2 if selected
        if enhance_withCv2:
            open_cv_image = np.array(captured)  # Convert captured img to cv2 format
            open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convert RGB to BGR
            grayImg = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)  # Convert the image to gray scale

            # Threshtype
            if background == "Auto-Detect":
                logger.info("Detecting background color...")
                is_light = np.mean(open_cv_image) > 127
                logger.debug(">> Image detected as light" if is_light else ">> Image detected as dark")
                threshType = cv2.THRESH_BINARY_INV if is_light else cv2.THRESH_BINARY
            else:
                is_light = background == "Light"
                threshType = cv2.THRESH_BINARY_INV if is_light else cv2.THRESH_BINARY

            # Performing OTSU threshold
            logger.info("Performing OTSU threshold...")
            ret, thresh = cv2.threshold(grayImg, 0, 255, cv2.THRESH_OTSU | threshType)  # TODO: CHECK what if use rgb img, because i forgor 💀

            # Specify structure shape and kernel size.
            # Kernel size increases or decreases the area
            # of the rectangle to be detected.
            # A smaller value like (10, 10) will detect
            # each word instead of a sentence.
            logger.info("Creating structuring element...")
            rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

            # Applying dilation on the threshold image
            logger.info("Applying dilation on the threshold image...")
            dilation = cv2.dilate(thresh, rectKernel, iterations=1)

            # debug
            if debugmode:
                if grayscale:
                    cv2.imshow("Grayscale Image", grayImg)
                cv2.imshow("Thresh Image (Auto - Light)" if is_light else "Thresh Image (Auto - Dark)", thresh)
                cv2.imshow("Dilated Image", dilation)

            # Finding contours in the image based on dilation
            contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            # Create a copy of captured image
            imgFinal = grayImg if grayscale else open_cv_image.copy()

            # Looping through the identified contours
            # Then rectangular part is cropped and passed on
            # to pytesseract for extracting text from it
            for cnt in contours[::-1]:  # Reverse the array because it actually starts from the bottom
                x, y, w, h = cv2.boundingRect(cnt)
                # Drawing a rectangle on copied image
                if debugmode:
                    rect = cv2.rectangle(imgFinal, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imshow("Rectangle drawn on image", rect)

                # Cropping the text block for giving input to OCR
                cropped = imgFinal[y : y + h, x : x + w]

                # Apply OCR on the cropped image
                text = pytesseract.image_to_string(cropped, langCode)

                # Append the text into wordsarr
                result += text.strip() + "\n"

            if saveImg:
                createPicDirIfGone()
                captured.save(saveName)
        else:
            if grayscale:  # grayscale only
                open_cv_image = np.array(captured)  # Convert captured img to cv2 format
                open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convert RGB to BGR
                grayImg = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)  # Convert the image to gray scale

                if debugmode:
                    cv2.imshow("Grayscale Image", grayImg)

                result = pytesseract.image_to_string(grayImg, langCode)
            else:  # no enhancement
                result = pytesseract.image_to_string(captured, langCode)

            if saveImg:
                createPicDirIfGone()
                captured.save(saveName)

        result = result.strip().replace("\n", " ") if replaceNewLine else result.strip()
        success = True
    except Exception as e:
        logger.exception("Error: " + str(e))
        result = str(e)
    finally:
        return success, result


def captureFullScreen():
    """Capture all screens and save the result"""
    # Capture all screens
    success = False
    saveName = os.path.join(dir_captured, "ScreenTranslate_" + datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".png")
    try:
        logger.info("Capturing full screen...")
        captured = pyautogui.screenshot()  # type: ignore
        createPicDirIfGone()
        captured.save(saveName)
        logger.info("Captured full screen!")
    except Exception as e:
        logger.exception("Error: " + str(e))
        success = False
        saveName = str(e)
    finally:
        return success, saveName


def seeFullWindow():
    """Capture all screens and save the result"""
    # Capture all screens
    try:
        logger.info("Capturing full screen...")
        captured = pyautogui.screenshot()  # type: ignore
        saveName = os.path.join(dir_captured, "Screentranslate_Full Captured Monitor(s) View.png")
        createPicDirIfGone()
        captured.save(saveName)
        startFile(saveName)
        logger.info("Captured full screen!")
    except Exception as e:
        logger.exception("Error: " + str(e))
        if "Invalid argument" in str(e):
            Mbox("Error image is still opened", "Please close the previous image first!", 2)
        else:
            Mbox("Error", str(e), 2)
