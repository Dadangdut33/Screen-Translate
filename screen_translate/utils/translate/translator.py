# pylint: disable=protected-access, redefined-outer-name, import-outside-toplevel, invalid-name
from typing import Dict

import requests
from loguru import logger

from ..helper import get_similar_keys, native_notify
from .language import DEEPL_KEY_VAL, GOOGLE_KEY_VAL, LIBRE_KEY_VAL, MYMEMORY_KEY_VAL, PONS_KEY_VAL


def no_connection_notify(
    customTitle: str = "No Internet Connection",
    customMessage:
    str = "Translation for engine other than your local LibreTranslate Deployment (If you have one)" \
        "will not work until you reconnect to the internet.",
):
    native_notify(customTitle, customMessage)


# Import the translator
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator, PonsTranslator
except Exception as e:
    GoogleTranslator = None
    MyMemoryTranslator = None
    PonsTranslator = None
    if "HTTPSConnectionPool" in str(e):
        no_connection_notify()
    else:
        no_connection_notify("Uncaught Error", str(e))
        logger.exception(e)

try:
    from PyDeepLX import PyDeepLX
except Exception as e:
    PyDeepLX = None
    no_connection_notify()
    logger.exception(e)


class Connections:
    """Translate Connections
    Attributes:
        GoogleTranslator (function): Google Translate
        MyMemoryTranslator (function): MyMemoryTranslator
        PonsTranslator (function): PonsTranslator
    """
    def __init__(self, GoogleTranslator, MyMemoryTranslator, PonsTranslator, deepl_tr):
        self.GoogleTranslator = GoogleTranslator
        self.MyMemoryTranslator = MyMemoryTranslator
        self.PonsTranslator = PonsTranslator
        self.deepl_tr = deepl_tr


con = Connections(GoogleTranslator, MyMemoryTranslator, PonsTranslator, PyDeepLX)


def google_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using Google Translate

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = GOOGLE_KEY_VAL[from_lang]
            LCODE_TO = GOOGLE_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = GOOGLE_KEY_VAL[get_similar_keys(GOOGLE_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for GOOGLE {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = GOOGLE_KEY_VAL[get_similar_keys(GOOGLE_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if con.GoogleTranslator is None:
            try:
                from deep_translator import GoogleTranslator
                con.GoogleTranslator = GoogleTranslator
            except Exception as e:
                logger.exception(e)
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        result = con.GoogleTranslator(source=LCODE_FROM, target=LCODE_TO, proxies=proxies).translate(text)
        is_success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))

    return is_success, result


def pons_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using PonsTranslator
    
    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = PONS_KEY_VAL[from_lang]
            LCODE_TO = PONS_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = PONS_KEY_VAL[get_similar_keys(PONS_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for PONS {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = PONS_KEY_VAL[get_similar_keys(PONS_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # --- Translate ---
    try:
        if con.PonsTranslator is None:
            try:
                from deep_translator import PonsTranslator
                con.PonsTranslator = PonsTranslator
            except Exception as e:
                logger.exception(e)
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        result = con.PonsTranslator(source=LCODE_FROM, target=LCODE_TO, proxies=proxies).translate(text)
        is_success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))

    return is_success, result


def memory_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using MyMemoryTranslator

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = MYMEMORY_KEY_VAL[from_lang]
            LCODE_TO = MYMEMORY_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = MYMEMORY_KEY_VAL[get_similar_keys(MYMEMORY_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for MYMEMORY {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = MYMEMORY_KEY_VAL[get_similar_keys(MYMEMORY_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if con.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                con.MyMemoryTranslator = MyMemoryTranslator
            except Exception as e:
                logger.exception(e)
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        result = con.MyMemoryTranslator(source=LCODE_FROM, target=LCODE_TO, proxies=proxies).translate(text)
        is_success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
    return is_success, result


def deepl_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using Deepl

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = DEEPL_KEY_VAL[from_lang]
            LCODE_TO = DEEPL_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = DEEPL_KEY_VAL[get_similar_keys(DEEPL_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for DEEPL {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = DEEPL_KEY_VAL[get_similar_keys(DEEPL_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # using PyDeepLX
    # --- Translate ---
    try:
        if con.deepl_tr is None:
            try:
                from PyDeepLX import PyDeepLX
                con.deepl_tr = PyDeepLX  # type: ignore
            except Exception as e:
                logger.exception(e)
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        result = con.deepl_tr.translate(text, LCODE_FROM, LCODE_TO, proxies=proxies)
        is_success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
    return is_success, result


# LibreTranslator
def libre_tl(
    text: str,
    from_lang: str,
    to_lang: str,
    proxies: Dict,
    debug_log: bool,
    libre_link: str,
    libre_api_key: str,
    **kwargs,
):
    """Translate Using LibreTranslate

    Args
    ----
        text (List[str]): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool): Debug Log. Defaults to False.
        libre_link (str): LibreTranslate Link
        libre_api_key (str): LibreTranslate API Key

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = LIBRE_KEY_VAL[from_lang]
            LCODE_TO = LIBRE_KEY_VAL[to_lang]
        except KeyError:
            try:
                LCODE_FROM = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for LIBRE LANG {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # shoot from API directly using requests
    # --- Translate ---
    try:
        req = {"q": text, "source": LCODE_FROM, "target": LCODE_TO, "format": "text"}
        libre_link += "/translate"

        if libre_api_key != "":
            req["api_key"] = libre_api_key

        response = requests.post(libre_link, json=req, proxies=proxies, timeout=5).json()
        if "error" in response:
            result = response["error"]
        else:
            result = response["translatedText"]
            is_success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct." \
            " If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. " \
                "If you use external server, make sure https is set to True."
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
    return is_success, result
