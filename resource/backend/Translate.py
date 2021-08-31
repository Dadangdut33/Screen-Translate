from .Mbox import Mbox
from .LangCode import *

try:
    from deep_translator import GoogleTranslator
except ConnectionError as e:
    print("Error: No Internet Connection. Please Restart With Internet Connected", str(e))
    Mbox("Error: No Internet Connection", str(e), 2)
except Exception as e:
    print("Error", str(e))
    Mbox("Error", str(e), 2)
# For now only 2 translator, will add more later

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
        # OLD
        # url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}'.format(from_LanguageCode_Google, to_LanguageCode_Google, text)
        # r = requests.get(url)

        # New
        result = GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())
        is_Success = True
    except Exception as e:
        print(str(e))
        result = str(e)
        Mbox("Error", str(e), 2)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: "+ result)
        return is_Success, result