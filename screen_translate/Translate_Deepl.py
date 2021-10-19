from screen_translate.Mbox import Mbox
from screen_translate.LangCode import *

# ----------------------------------------------------------------
# Imports Library
try:
    from deepl_scraper_pp.deepl_tr import deepl_tr
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", str(e), 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", str(e), 2)


# ----------------------------------------------------------------
# Functions
# Deepl
async def deepl_tl(text, to_lang, from_lang="auto"):
    """Translate Using Deepl

    Args:
        text ([str]): Text to translate
        to_lang ([type]): Language to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".

    Returns:
        [type]: Translation result
    """
    is_Success = False
    res = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Deepl = deepl_Lang[to_lang]
        from_LanguageCode_Deepl =  deepl_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        res = await deepl_tr(text.strip(), from_LanguageCode_Deepl, to_LanguageCode_Deepl)
        is_Success = True
    except Exception as e:
        print(str(e))
        Mbox("Error", str(e), 2)
        res = str(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation get: " + res)
        return is_Success, res