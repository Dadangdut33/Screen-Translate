import requests
from screen_translate.Mbox import Mbox
from screen_translate.LangCode import *

# ----------------------------------------------------------------
# Imports Library
# Google Translate
try:
    from deep_translator import GoogleTranslator
except Exception as e:
    if "HTTPSConnectionPool" in str(e):
        GoogleTranslator = None
    else:
        print("Error", str(e))
        Mbox("Error", str(e), 2)

# ----------------------------------------------------------------
# MyMemory Translate
try:
    from deep_translator import MyMemoryTranslator
except ConnectionError as e:
    MyMemoryTranslator = None
except Exception as e:
    if "HTTPSConnectionPool" in str(e):
        MyMemoryTranslator = None
    else:
        print("Error", str(e))
        Mbox("Error", str(e), 2)

# ----------------------------------------------------------------
# Pons
try:
    from deep_translator import PonsTranslator
except Exception as e:
    if "HTTPSConnectionPool" in str(e):
        PonsTranslator = None
    else:
        print("Error", str(e))
        Mbox("Error", str(e), 2)

__all__ = ["google_tl", "memory_tl", "pons_tl", "libre_tl"]


# ----------------------------------------------------------------
class TlConns:
    """Translate Connections

    Attributes:
        google_tl (function): Google Translate
        memory_tl (function): MyMemoryTranslator
        pons_tl (function): PonsTranslator
    """
    def __init__(self, GoogleTranslator, MyMemoryTranslator, PonsTranslator):
        self.GoogleTranslator = GoogleTranslator
        self.MyMemoryTranslator = MyMemoryTranslator
        self.PonsTranslator = PonsTranslator
        
        if self.GoogleTranslator is None:
            self.connected = False
        else:
            self.connected = True

tlCons = TlConns(GoogleTranslator, MyMemoryTranslator, PonsTranslator)

# Reconnect
def reconnect():
    """Reconnect Translate Connections

    Returns:
        [type]: [description]
    """
    if not tlCons.connected:
        try:
            from deep_translator import GoogleTranslator
            from deep_translator import MyMemoryTranslator
            from deep_translator import PonsTranslator

            tlCons.GoogleTranslator = GoogleTranslator
            tlCons.MyMemoryTranslator = MyMemoryTranslator
            tlCons.PonsTranslator = PonsTranslator
            tlCons.connected = True

            print("Reconnected")
            Mbox("Reconnected", "Reconnected Successfully!", 1)

        except ConnectionError as e:
            print("Connection Error! Fail to reconnect!", str(e))
            Mbox("Connection Error! Fail to reconnect!", str(e), 2)
        except Exception as e:
            print("Error", str(e))
            Mbox("Error", str(e), 2)

def checkConns():
    """Check Translate Connections

    Returns:
        [boolean]: true or false. True if connected.
    """
    return tlCons.connected

# TL Functions
# Google
def google_tl(text, to_lang, from_lang="auto", oldMethod = False):
    """Translate Using Google Translate

    Args:
        text ([str]): Text to translate
        to_lang ([type]): Language to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".

    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code --- 
    try:
        to_LanguageCode_Google = google_Lang[to_lang]
        from_LanguageCode_Google =  google_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.GoogleTranslator is None:
            result = "Error: No Internet Connection. Please reconnect by pressing the signal button in main window."
            return is_Success, result

        if not oldMethod:
            result = tlCons.GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())
        else:
            url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}'.format(from_LanguageCode_Google, to_LanguageCode_Google, text.replace('\n', ' ').replace(' ', '%20').strip())
            result = requests.get(url).json()[0][0][0]        
        
        is_Success = True
    except Exception as e:
        print(str(e))
        result = str(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: "+ result)
        return is_Success, result

# My Mermory
def memory_tl(text, to_lang, from_lang="auto"):
    """Translate Using MyMemoryTranslator

    Args:
        text ([str]): Text to translate
        to_lang ([type]): Language to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".

    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code --- 
    try:
        to_LanguageCode_Memory = myMemory_Lang[to_lang]
        from_LanguageCode_Memory =  myMemory_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.MyMemoryTranslator is None:
            result = "Error: No Internet Connection. Please reconnect by pressing the signal button in main window."
            return is_Success, result

        result = tlCons.MyMemoryTranslator(source=from_LanguageCode_Memory, target=to_LanguageCode_Memory).translate(text.strip())
        is_Success = True
    except Exception as e:
        print(str(e))
        result = str(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: "+ result)
        return is_Success, result

# PonsTranslator
def pons_tl(text, to_lang, from_lang):
    """Translate Using PONS

    Args:
        text ([str]): Text to translate
        to_lang ([type]): Language to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".

    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code --- 
    try:
        to_LanguageCode_Pons = pons_Lang[to_lang]
        from_LanguageCode_Pons =  pons_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.PonsTranslator is None:
            result = "Error: No Internet Connection. Please reconnect by pressing the signal button in main window."
            return is_Success, result

        result = tlCons.PonsTranslator(source=from_LanguageCode_Pons, target=to_LanguageCode_Pons).translate(text.strip())
        is_Success = True
    except Exception as e:
        print(str(e))
        result = str(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: "+ result)
        return is_Success, result

# LibreTranslator
def libre_tl(text, to_lang, from_lang, https=False, host="localhost", port="5000"):
    """Translate Using LibreTranslate
        Args:
            text ([str]): Text to translate
            to_lang ([type]): Language to translate
            from_lang (str, optional): [Language From]. Defaults to "auto".
            host ([str]): Server hostname
            port ([str]): Server port

        Returns:
            [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Libre = libre_Lang[to_lang]
        from_LanguageCode_Libre = libre_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        request = {
            "q": text,
            "source": from_LanguageCode_Libre,
            "target": to_LanguageCode_Libre,
            "format": "text"
        }
        httpStr = "https" if https else "http"

        if port:
            adr = httpStr + "://" + host + ":" + port + "/translate"
        else:
            adr = httpStr + "://" + host + "/translate"

        response = requests.post(adr, request).json()
        if "error" in response:
            result = response["error"]
        else:
            result = response["translatedText"]
            is_Success = True
    except Exception as e:
        result = str(e)
        print(str(e))
        if 'NewConnectionError' in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct. If you are not hosting it yourself, please try again with an internet connection."
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: " + result)
        return is_Success, result