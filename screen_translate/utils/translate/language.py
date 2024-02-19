import json
import os
from copy import deepcopy
from typing import Dict, List

from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES, PONS_CODES_TO_LANGUAGES
from loguru import logger

from screen_translate._path import dir_user, path_keys

from ..helper import create_dir_if_gone, get_similar_in_list

# ---------------------------- #
# paths
create_dir_if_gone(dir_user)

# Engines available
engines = ["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate", "None"]

# List of supported languages by Tesseract OCR
TESSERACT_KEY_VAL = {
    "Auto": "auto",
    "Afrikaans": "afr",
    "Amharic": "amh",
    "Arabic": "ara",
    "Assemese": "asm",
    "Azerbaijani": "aze_cyrl",
    "Belarusian": "bel",
    "Bengali": "ben",
    "Tibetan": "bod",
    "Bosnian": "bos",
    "Breton": "bre",
    "Bulgarian": "bul",
    "Catalan:Valencian": "cat",
    "Cebuano": "ceb",
    "Czech": "ces",
    "Chinese (simplified)": "chi_sim",
    "Chinese (simplified) - Vertical": "chi_sim_vert",
    "Chinese (traditional)": "chi_tra",
    "Chinese (traditional) - Vertical": "chi_tra_vert",
    "Cherokee": "chr",
    "Corsican": "cos",
    "Welsh": "cym",
    "Danish": "dan",
    "German": "deu",
    "Dzongkha": "dzo",
    "Greek": "ell",
    "English": "eng",
    "Esperanto": "epo",
    "Estonian": "est",
    "Basque": "eus",
    "Faroese": "fao",
    "Persian": "fas",
    "Filipino": "fil",
    "Finnish": "fin",
    "French": "fra",
    "Western Frisian": "fry",
    "Scottish Gaelic": "gla",
    "Irish": "gle",
    "Galician": "glg",
    "Gujarati": "guj",
    "Haitian": "hat",
    "Hebrew": "heb",
    "Hindi": "hin",
    "Coratian": "hrv",
    "Hungarian": "hun",
    "Armenian": "hye",
    "Inuktitut": "iku",
    "Indonesian": "ind",
    "Icelandic": "isl",
    "Italian": "ita",
    "Javanese": "jav",
    "Japanese": "jpn",
    "Japanese - Vertical": "jpn_vert",
    "Kannada": "kan",
    "Georgian": "kat",
    "Kazakh": "kaz",
    "Khmer": "khm",
    "Kirghiz": "kir",
    "Kurmanji": "kmr",
    "Korean": "kor",
    "Kurdish": "kur",
    "Lao": "lao",
    "Latin": "lat",
    "Latvian": "lav",
    "Lithuanian": "lit",
    "Luxembourgish": "ltz",
    "Malayalam": "mal",
    "Marathi": "mar",
    "Macedonian": "mkd",
    "Maltese": "mlt",
    "Mongolian": "mon",
    "Maori": "mri",
    "Malay": "msa",
    "Burmese": "mya",
    "Nepali": "nep",
    "Dutch": "nld",
    "Norwegian": "nor",
    "Occitan": "oci",
    "Oriya": "ori",
    "Punjabi": "pan",
    "Polish": "pol",
    "Portuguese": "por",
    "Pushto": "pus",
    "Quechua": "que",
    "Romanian": "ron",
    "Russian": "rus",
    "Sanskrit": "san",
    "Sinhala": "sin",
    "Slovak": "slk",
    "Slovenian": "slv",
    "Spanish": "spa",
    "Albanian": "sqi",
    "Serbian": "srp",
    "Sundanese": "sun",
    "Swahili": "swa",
    "Swedish": "swe",
    "Syriac": "syr",
    "Tamil": "tam",
    "Tatar": "tat",
    "Telugu": "tel",
    "Tajik": "tgk",
    "Tagalog": "tgl",
    "Thai": "tha",
    "Tigrinya": "tir",
    "Tonga": "ton",
    "Turkish": "tur",
    "Uighur": "uig",
    "Ukrainian": "ukr",
    "Urdu": "urd",
    "Uzbek": "uzb",
    "Uzbek - Cyrilic": "uzb_cyrl",
    "Vietnamese": "vie",
    "Yiddish": "yid",
    "Yoruba": "yor",
}

TESSERACT_LANG_LIST = list(TESSERACT_KEY_VAL.keys())
TESSERACT_LANG_LIST.sort()

# ---------------------
# Google Translate
# ---------------------
GOOGLE_KEY_VAL = deepcopy(GOOGLE_LANGUAGES_TO_CODES)
assert isinstance(GOOGLE_KEY_VAL, Dict)
GOOGLE_KEY_VAL = {key.capitalize(): value for key, value in GOOGLE_KEY_VAL.items()}  # up first case of every key
GOOGLE_KEY_VAL["Auto"] = "auto"
GOOGLE_KEY_VAL["Chinese (simplified) - Vertical"] = "zh-CN"
GOOGLE_KEY_VAL["Chinese (traditional) - Vertical"] = "zh-TW"
GOOGLE_KEY_VAL["Japanese - Vertical"] = "ja"

# ---------------------
# MyMemory | code from deep_translator is the same but some is not compatible.
# ---------------------
MYMEMORY_KEY_VAL = deepcopy(GOOGLE_KEY_VAL)
# remove key that gives error or invalid
MYMEMORY_KEY_VAL.pop("Aymara")
MYMEMORY_KEY_VAL.pop("Dogri")
MYMEMORY_KEY_VAL.pop("Javanese")
MYMEMORY_KEY_VAL.pop("Konkani")
MYMEMORY_KEY_VAL.pop("Krio")
MYMEMORY_KEY_VAL.pop("Oromo")

# ---------------------
# Pons
# ---------------------
PONS_KEY_VAL = deepcopy(PONS_CODES_TO_LANGUAGES)
PONS_KEY_VAL = {key.capitalize(): value for key, value in PONS_KEY_VAL.items()}  # up first case of every key
PONS_KEY_VAL["Auto"] = "auto"
PONS_KEY_VAL["Chinese (simplified) - Vertical"] = "zh-cn"
PONS_KEY_VAL["Chinese (traditional) - Vertical"] = "zh-cn"

# ---------------------
# deepl
# ---------------------
DEEPL_KEY_VAL = {
    "Auto": "auto",
    "Bulgarian": "bg",
    "Chinese (simplified)": "zh",
    "Chinese (simplified) - Vertical": "zh",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Estonian": "et",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Japanese - Vertical": "ja",
    "Korean": "ko",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Norwegian": "nb",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Spanish": "es",
    "Swedish": "sv",
    "Turkish": "tr",
    "Ukrainian": "uk",
}

# ---------------------
# deepl
# ---------------------
# List of supported languages by libreTranslate. Taken from LibreTranslate.com docs v1.5.1
LIBRE_KEY_VAL = {
    "Auto": "auto",
    "English": "en",
    "Albanian": "sq",
    "Arabic": "ar",
    "Azerbaijani": "az",
    "Bengali": "bn",
    "Bulgarian": "bg",
    "Catalan": "ca",
    "Chinese (simplified)": "zh",
    "Chinese (simplified) - Vertical": "zh",
    "Chinese (traditional)": "zt",
    "Chinese (traditional) - Vertical": "zt",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "Esperanto": "eo",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hebrew": "he",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Irish": "ga",
    "Italian": "it",
    "Japanese": "ja",
    "Japanese - Vertical": "ja",
    "Korean": "ko",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Malay": "ms",
    "Norwegian": "nb",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Serbian": "sr",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Spanish": "es",
    "Swedish": "sv",
    "Tagalog": "tl",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "vietnamese": "vi",
}

# ------------------ #
FOUND_MISSING_KEY = False


def remove_auto(lang_list: List):
    """Remove auto detect from the list"""
    try:
        lang_list.remove("Auto")
    except ValueError:
        pass

    return lang_list


def verify_dict_data(key_list: List, base_key_dict: Dict, data_read: Dict):
    """Verify if the data is a dict"""
    global FOUND_MISSING_KEY
    for key in key_list:
        if key not in data_read:
            data_read[key] = base_key_dict[key]
            FOUND_MISSING_KEY = True

    return data_read


def get_tesseract_lang_similar(similar_key: str, debug: bool = True):
    """Get similar language from Tesseract language list.
    This is used because we want to keep the original language name for the translation engine
    So everytime we want to set the tesseract language, we must call this function first to get the correct key

    Parameters
    ----------
    similar_key : str
        Similar language
    debug : bool, optional
        Print debug message, by default True
        
    Returns
    -------
    str
        Correct language key
    
    Raises
    ------
    ValueError
        If the similar_key is not found in the list
    """
    if debug:
        logger.debug(f"Getting similar key for {similar_key}")

    should_be_there = get_similar_in_list(TESSERACT_LANG_LIST, similar_key)
    if len(should_be_there) != 0:
        if debug:
            logger.debug(f"Found key {should_be_there[0]} while searching for {similar_key}")
            logger.debug(f"FULL KEY GET {should_be_there}")
        return should_be_there[0]
    # if not found
    raise ValueError(
        f"Fail to get whisper language from similar while searching for {similar_key}. "\
        "Please report this as a bug to https://github.com/Dadangdut33/Screen-Translate/issues"
    )


# if not yet created
if not os.path.exists(path_keys):
    key_save = {
        "tesseract_lang": TESSERACT_KEY_VAL,
        "google_lang": GOOGLE_KEY_VAL,
        "myMemory_lang": MYMEMORY_KEY_VAL,
        "deepl_lang": DEEPL_KEY_VAL,
        "pons_lang": PONS_KEY_VAL,
        "libre_lang": LIBRE_KEY_VAL,
    }

    logger.debug("Creating a new base file for the keys.")
    with open(path_keys, "w", encoding="utf-8") as f:
        json.dump(key_save, f, indent=4)

else:
    with open(path_keys, "r", encoding="utf-8") as f:
        key_save = json.load(f)
        key_save = {
            "tesseract_lang": verify_dict_data(list(TESSERACT_KEY_VAL.keys()),\
                                TESSERACT_KEY_VAL, key_save["tesseract_lang"]),
            "google_lang": verify_dict_data(list(GOOGLE_KEY_VAL.keys()), GOOGLE_KEY_VAL, key_save["google_lang"]),
            "myMemory_lang": verify_dict_data(list(MYMEMORY_KEY_VAL.keys()), MYMEMORY_KEY_VAL, key_save["myMemory_lang"]),
            "deepl_lang": verify_dict_data(list(DEEPL_KEY_VAL.keys()), DEEPL_KEY_VAL, key_save["deepl_lang"]),
            "pons_lang": verify_dict_data(list(PONS_KEY_VAL.keys()), PONS_KEY_VAL, key_save["pons_lang"]),
            "libre_lang": verify_dict_data(list(LIBRE_KEY_VAL.keys()), LIBRE_KEY_VAL, key_save["libre_lang"]),
        }

        if FOUND_MISSING_KEY:
            logger.warning("Some keys are missing. Saving the missing keys to the file.")
            with open(path_keys, "w", encoding="utf-8") as f:
                json.dump(key_save, f, indent=4)

        TESSERACT_KEY_VAL = key_save["tesseract_lang"]
        GOOGLE_KEY_VAL = key_save["google_lang"]
        MYMEMORY_KEY_VAL = key_save["myMemory_lang"]
        DEEPL_KEY_VAL = key_save["deepl_lang"]
        PONS_KEY_VAL = key_save["pons_lang"]
        LIBRE_KEY_VAL = key_save["libre_lang"]

# ------------------ #
# for no translation done (Only OCR)
# no auto
TESSERACT_ONLY = remove_auto(list(TESSERACT_KEY_VAL.keys()))
TESSERACT_ONLY.sort()
# ------------------ #
# TARGET LANGUAGE

GOOGLE_TARGET = remove_auto(list(GOOGLE_KEY_VAL.keys()))
GOOGLE_TARGET.sort()

MYMEMORY_TARGET = remove_auto(list(MYMEMORY_KEY_VAL.keys()))
MYMEMORY_TARGET.sort()

DEEPL_TARGET = remove_auto(list(DEEPL_KEY_VAL.keys()))
DEEPL_TARGET.sort()

PONS_TARGET = remove_auto(list(PONS_KEY_VAL.keys()))
PONS_TARGET.sort()

LIBRE_TARGET = remove_auto(list(LIBRE_KEY_VAL.keys()))
LIBRE_TARGET.sort()

engine_select_target_dict = {
    "Google Translate": GOOGLE_TARGET,
    "MyMemoryTranslator": MYMEMORY_TARGET,
    "Deepl": DEEPL_TARGET,
    "PONS": PONS_TARGET,
    "LibreTranslate": LIBRE_TARGET,
    "None": TESSERACT_ONLY,
}

# ------------------ #
# SOURCE LANGUAGE

# --- GOOGLE --- | Filtering
to_remove = []
GOOGLE_TESSERACT_COMPATIBLE = GOOGLE_TARGET.copy()
for i, lang in enumerate(GOOGLE_TESSERACT_COMPATIBLE):
    is_it_there = get_similar_in_list(TESSERACT_ONLY, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
GOOGLE_TESSERACT_COMPATIBLE = [x for x in GOOGLE_TESSERACT_COMPATIBLE if x not in to_remove]

# --- MYMEMORY --- | Filtering
to_remove = []
MYMEMORY_TESSERACT_COMPATIBLE = MYMEMORY_TARGET.copy()
for i, lang in enumerate(MYMEMORY_TESSERACT_COMPATIBLE):
    is_it_there = get_similar_in_list(TESSERACT_ONLY, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
MYMEMORY_TESSERACT_COMPATIBLE = [x for x in MYMEMORY_TESSERACT_COMPATIBLE if x not in to_remove]

# --- DEEPL --- | Filtering
to_remove = []
DEEPL_TESSERACT_COMPATIBLE = DEEPL_TARGET.copy()
for i, lang in enumerate(DEEPL_TESSERACT_COMPATIBLE):
    is_it_there = get_similar_in_list(TESSERACT_ONLY, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
DEEPL_TESSERACT_COMPATIBLE = [x for x in DEEPL_TESSERACT_COMPATIBLE if x not in to_remove]

# --- PONS --- | Filtering
to_remove = []
PONS_TESSERACT_COMPATIBLE = PONS_TARGET.copy()
for i, lang in enumerate(PONS_TESSERACT_COMPATIBLE):
    is_it_there = get_similar_in_list(TESSERACT_ONLY, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
PONS_TESSERACT_COMPATIBLE = [x for x in PONS_TESSERACT_COMPATIBLE if x not in to_remove]

# --- LIBRE --- | Filtering
to_remove = []
LIBRE_TESSERACT_COMPATIBLE = LIBRE_TARGET.copy()
for i, lang in enumerate(LIBRE_TESSERACT_COMPATIBLE):
    is_it_there = get_similar_in_list(TESSERACT_ONLY, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)

# --- SOURCES ---
engine_select_source_dict = {
    "Google Translate": GOOGLE_TESSERACT_COMPATIBLE,
    "MyMemoryTranslator": MYMEMORY_TESSERACT_COMPATIBLE,
    "Deepl": DEEPL_TESSERACT_COMPATIBLE,
    "PONS": PONS_TESSERACT_COMPATIBLE,
    "LibreTranslate": LIBRE_TESSERACT_COMPATIBLE,
    "None": TESSERACT_ONLY,
}
