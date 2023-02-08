import os
import requests
from notifypy import Notify

from .LangCode import google_lang, libre_lang, myMemory_lang, deepl_lang, pons_lang
from .Helper import get_similar_keys
from screen_translate.Globals import path_logo_icon, app_name
from screen_translate.Logging import logger


def no_connection_notify(
    customTitle: str = "No Internet Connection",
    customMessage: str = "Translation for engine other than your local LibreTranslate Deployment (If you have one) will not work until you reconnect to the internet.",
):
    notification = Notify()
    notification.title = customTitle
    notification.message = customMessage
    notification.application_name = app_name
    if os.path.exists(path_logo_icon):
        notification.icon = path_logo_icon

    notification.send()


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
    from .Deepl_Scraper import deepl_tr
except Exception as e:
    deepl_tr = None
    no_connection_notify()
    logger.exception(e)


class tl_cons:
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


tlCons = tl_cons(GoogleTranslator, MyMemoryTranslator, PonsTranslator, deepl_tr)


def google_tl(text: str, from_lang: str, to_lang: str):
    """Translate Using Google Translate
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        oldMethod (bool, optional): Use old method. Defaults to False.
    Returns:
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Google = google_lang[to_lang]
            from_LanguageCode_Google = google_lang[from_lang]
        except KeyError as e:
            to_LanguageCode_Google = google_lang[get_similar_keys(google_lang, to_lang)[0]]
            from_LanguageCode_Google = google_lang[get_similar_keys(google_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"

    # --- Translate ---
    try:
        if tlCons.GoogleTranslator is None:
            try:
                from deep_translator import GoogleTranslator

                tlCons.GoogleTranslator = GoogleTranslator
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = tlCons.GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())
        is_Success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.debug("Query: " + text.strip())
        logger.debug(f"Translation Get: {result}")
        return is_Success, result


def pons_tl(text: str, from_lang: str, to_lang: str):
    """Translate Using PonsTranslator
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Pons = pons_lang[to_lang]
            from_LanguageCode_Pons = pons_lang[from_lang]
        except KeyError as e:
            to_LanguageCode_Pons = pons_lang[get_similar_keys(pons_lang, to_lang)[0]]
            from_LanguageCode_Pons = pons_lang[get_similar_keys(pons_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.PonsTranslator is None:
            try:
                from deep_translator import PonsTranslator

                tlCons.PonsTranslator = PonsTranslator
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = tlCons.PonsTranslator(source=from_LanguageCode_Pons, target=to_LanguageCode_Pons).translate(text.strip())
        is_Success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.debug("Query: " + text.strip())
        logger.debug("Translation Get: " + result)  # type: ignore
        return is_Success, result


def memory_tl(text: str, from_lang: str, to_lang: str):
    """Translate Using MyMemoryTranslator
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Memory = myMemory_lang[to_lang]
            from_LanguageCode_Memory = myMemory_lang[from_lang]
        except KeyError as e:
            to_LanguageCode_Memory = myMemory_lang[get_similar_keys(myMemory_lang, to_lang)[0]]
            from_LanguageCode_Memory = myMemory_lang[get_similar_keys(myMemory_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                tlCons.MyMemoryTranslator = MyMemoryTranslator
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = tlCons.MyMemoryTranslator(source=from_LanguageCode_Memory, target=to_LanguageCode_Memory).translate(text.strip())
        is_Success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.debug("Query: " + text.strip())
        logger.debug("Translation Get: " + result)  # type: ignore
        return is_Success, result


# LibreTranslator
def libre_tl(text: str, from_lang: str, to_lang: str, https: bool = False, host: str = "libretranslate.de", port: str = "", apiKeys: str = ""):
    """Translate Using LibreTranslate
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        https (bool, optional): Use https. Defaults to False.
        host (str, optional): Host. Defaults to "libretranslate.de".
        port (str, optional): Port. Defaults to "".
        apiKeys (str, optional): API Keys. Defaults to "".
    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Libre = libre_lang[to_lang]
            from_LanguageCode_Libre = libre_lang[from_lang]
        except KeyError as e:
            to_LanguageCode_Libre = libre_lang[get_similar_keys(libre_lang, to_lang)[0]]
            from_LanguageCode_Libre = libre_lang[get_similar_keys(libre_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        request = {"q": text, "source": from_LanguageCode_Libre, "target": to_LanguageCode_Libre, "format": "text"}
        httpStr = "https" if https else "http"
        if apiKeys != "":
            request["api_key"] = apiKeys

        if port != "":
            adr = httpStr + "://" + host + ":" + port + "/translate"
        else:
            adr = httpStr + "://" + host + "/translate"

        response = requests.post(adr, json=request).json()
        if "error" in response:
            result = response["error"]
        else:
            result = response["translatedText"]
            is_Success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct. If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. If you use external server, make sure https is set to True."
    finally:
        logger.info("-" * 50)
        logger.debug("Query: " + text.strip())
        logger.debug("Translation Get: " + result)
        return is_Success, result


def deepl_tl(text, from_lang, to_lang):
    """Translate Using Deepl

    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate

    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Deepl = deepl_lang[to_lang]
            from_LanguageCode_Deepl = deepl_lang[from_lang]
        except KeyError as e:
            to_LanguageCode_Deepl = deepl_lang[get_similar_keys(deepl_lang, to_lang)[0]]
            from_LanguageCode_Deepl = deepl_lang[get_similar_keys(deepl_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.deepl_tr is None:
            try:
                from .Deepl_Scraper import deepl_tr

                tlCons.deepl_tr = deepl_tr
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = tlCons.deepl_tr(text.strip(), from_LanguageCode_Deepl, to_LanguageCode_Deepl)
        is_Success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.debug("Query: " + text.strip())
        logger.debug(f"Translation get: {result}")
        return is_Success, result
