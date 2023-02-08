import os
import ast
import shlex
from datetime import datetime
from typing import List

import numpy as np
import pyautogui
import pyperclip
import pytesseract
import cv2

from screen_translate.Logging import logger
from screen_translate.components.custom.MBox import Mbox
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
            logger.exception(e)
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
        config = fJson.settingCache["tesseract_config"] if fJson.settingCache["tesseract_config"] else ""
        if "--psm" not in config and fJson.settingCache["tesseract_psm5_vertical"] and "vertical" in sourceLang.lower():
            config += " --psm 5" # vertical on vertical text
        enhance_withCv2 = fJson.settingCache["enhance_with_cv2_Contour"]
        grayscale = fJson.settingCache["enhance_with_grayscale"]
        debugmode = fJson.settingCache["enhance_debugmode"]
        background = fJson.settingCache["enhance_background"]
        replaceNewLine = fJson.settingCache["replaceNewLine"]
        replacer = ast.literal_eval(shlex.quote(fJson.settingCache["replaceNewLineWith"]))  # set new text
        saveImg = fJson.settingCache["keep_image"]
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
            ret, thresh = cv2.threshold(grayImg, 0, 255, cv2.THRESH_OTSU | threshType)  #  must use grayImg

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
                text = pytesseract.image_to_string(cropped, langCode, config=config)

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

                result = pytesseract.image_to_string(grayImg, langCode, config=config)
            else:  # no enhancement
                result = pytesseract.image_to_string(captured, langCode, config=config)

            if saveImg:
                createPicDirIfGone()
                captured.save(saveName)

        result = result.strip().replace("\n", replacer) if replaceNewLine else result.strip()
        success = True
        logger.info("OCR success!")
        logger.info(f"Result length {len(result)}")

        if fJson.settingCache["auto_copy_captured"]:
            pyperclip.copy(result)
            logger.info("Copied captured text to clipboard!")

        if not fJson.settingCache["supress_no_text_alert"] and len(result) == 0:
            Mbox("No text detected", "No text detected in the image. Please try again.", 1)

        if debugmode:
            cv2.waitKey(0)
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        return success, result


def captureFullScreen():
    """Capture all screens and save the result"""
    # Capture all screens
    success = False
    capturedObj = None
    try:
        logger.info("Capturing full screen...")
        capturedObj = pyautogui.screenshot()  # type: ignore
        createPicDirIfGone()
        success = True
        logger.info("Captured full screen!")
    except Exception as e:
        logger.exception(e)
        success = False
        capturedObj = str(e)
    finally:
        return success, capturedObj


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
        logger.exception(e)
        if "Invalid argument" in str(e):
            Mbox("Error image is still opened", "Please close the previous image first!", 2)
        else:
            Mbox("Error", str(e), 2)
