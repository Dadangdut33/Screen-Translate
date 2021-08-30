import requests 
import asyncio
from .LangCode import *
from deep_translator import GoogleTranslator
from deepl_scraper_pp.deepl_tr import deepl_tr

# For now only 2, will add more later

def google_tl(text, to_lang, from_lang="auto"):
    """Translate Using Google Translate

    Args:
        text ([str]): Text to translate
        to_lang ([type]): Language to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".

    Returns:
        [type]: Translation result
    """
    is_Success = False
    # --- Get lang code --- 
    try:
        to_LanguageCode_Google = google_Lang[to_lang]
        from_LanguageCode_Google =  google_Lang[from_lang]
    except KeyError as e:
        print("Error: " + e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        # OLD
        # url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}'.format(from_LanguageCode_Google, to_LanguageCode_Google, text)
        # r = requests.get(url)

        # New
        result = GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())
        is_Success = True
    except Exception as e:
        print(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: "+ result)
        return is_Success, result
        
    
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
    # --- Get lang code ---
    try:
        to_LanguageCode_Deepl = deepl_Lang[to_lang]
        from_LanguageCode_Deepl =  deepl_Lang[from_lang]
    except KeyError as e:
        print("Error: " + e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        res = await deepl_tr(text.strip(), from_LanguageCode_Deepl, to_LanguageCode_Deepl)
        is_Success = True
    except Exception as e:
        print(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation get: " + res)
        return is_Success, res