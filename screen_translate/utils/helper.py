import ctypes
import functools
import os
import subprocess
import webbrowser
from threading import Thread
from typing import Dict, List, Optional

import notifypy
from notifypy import Notify

from screen_translate._constants import APP_NAME
from screen_translate._logging import logger
from screen_translate._path import path_logo_png
from screen_translate._version import __version__

# pylint: disable=protected-access
notifypy.Notify._selected_notification_system = functools.partial(  # type: ignore
    notifypy.Notify._selected_notification_system, override_windows_version_detection=True
)

name_version = f"{APP_NAME} v{__version__}"


def kill_thread(thread: Optional[Thread]) -> bool:
    """Attempt to kill thread, credits: https://github.com/JingheLee/KillThread
    
    Parameters
    ----------
    thread : Thread
        Thread instance object.

    Returns
    -------
    bool
        True or False
    """
    try:
        if isinstance(thread, Thread):
            return ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread.ident),  # type: ignore
                ctypes.py_object(SystemExit)
            ) == 1

        return False
    except Exception as e:
        logger.exception(e)
        return False


def get_similar_in_list(_list: List, search_key: str):
    """Get similar item in a list by key.

    This will search wether search_key is in the list provided or not.
    The first search, it will search if the `search_key is in _list` (case insensitive).
    If not found then it will do another search but using the key of the list as the key to search in key_search
    (`key_search in _key_of_list`)

    Parameters
    ----------
    _list : List
        List to search
    key : str
        Key to search

    Returns
    -------
    List
        List of similar item
    """

    get = [k for k in _list if search_key.lower() in k.lower()]
    if len(get) == 0:
        # reverse search from the list
        get = [k for k in _list if k.lower() in search_key.lower()]
    return get


def up_first_case(string: str):
    """
    Uppercase the first letter of the string
    """
    return string.capitalize()


def create_dir_if_gone(dir_path: str):
    """
    Create the directory if it does not exist
    """
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            return True
        except Exception as e:
            logger.exception(e)
            native_notify("Error Creating Directory", f"Details: {e}")
            return False

    return True


def get_similar_keys(_dict: Dict, key: str):
    """
    Get similar keys from a dictionary
    """
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def start_file(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        native_notify("Error", "Cannot find the file specified.")
    except Exception:
        try:
            subprocess.Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
            native_notify("Error", "Cannot find the file specified.")
        except Exception as e:
            logger.exception(e)
            native_notify("Error", f"Uncaught error {str(e)}")


def open_url(url: str):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        logger.exception(e)
        native_notify("Error", "Cannot open the url specified.")


def native_notify(
    title: str,
    message: str,
):
    """
    Native notification
    """
    try:
        notification = Notify()
        notification.application_name = name_version
        notification.title = title
        notification.message = message

        if os.path.exists(path_logo_png):
            notification.icon = path_logo_png

        notification.send()
    except Exception as e:
        logger.exception(e)
        logger.error("Cannot send notification.")


def tb_copy_only(event):
    key = event.keysym

    # Allow
    allowed_state = [4, 8, 12]
    if key.lower() in ["left", "right"]:  # Arrow left right
        return
    if event.state in allowed_state and key.lower() == "a":  # Ctrl + a
        return
    if event.state in allowed_state and key.lower() == "c":  # Ctrl + c
        return

    # If not allowed
    return "break"


def get_opac_value(event):
    value = 1
    try:
        value = event.delta
        if value > 0:
            value += 0.025
        else:
            value -= 0.025

    except AttributeError:
        value = float(event)

    if value > 1:
        value = 1
    elif value < 0:
        value = 0

    return value
