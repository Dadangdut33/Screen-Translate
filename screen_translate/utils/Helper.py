import os
import subprocess
import webbrowser
from notifypy import Notify, exceptions
from typing import Tuple

from screen_translate.Logging import logger


def upFirstCase(string: str):
    return string[0].upper() + string[1:]


def startFile(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        nativeNotify("Error", "Cannot find the file specified.", "", "Speech Translate")
    except Exception:
        try:
            subprocess.Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
            nativeNotify("Error", "Cannot find the file specified.", "", "Speech Translate")
        except Exception as e:
            logger.exception("Error: " + str(e))
            nativeNotify("Error", f"Uncaught error {str(e)}", "", "Speech Translate")


def OpenUrl(url: str):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error", "Cannot open the url specified.", "", "Speech Translate")


def nativeNotify(title: str, message: str, logo: str, app_name: str):
    """
    Native notification
    """
    notification = Notify()
    notification.application_name = app_name
    notification.title = title
    notification.message = message
    try:
        notification.icon = logo
    except exceptions:
        pass

    notification.send()


def tb_copy_only(event):
    key = event.keysym

    # Allow
    allowedEventState = [4, 8, 12]
    if key.lower() in ["left", "right"]:  # Arrow left right
        return
    if event.state in allowedEventState and key.lower() == "a":  # Ctrl + a
        return
    if event.state in allowedEventState and key.lower() == "c":  # Ctrl + c
        return

    # If not allowed
    return "break"


def hex_to_rgb(value: str):
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(rgb: Tuple):
    return "%02x%02x%02x" % rgb

def invert_color(hex_color: str):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex((255 - r, 255 - g, 255 - b))