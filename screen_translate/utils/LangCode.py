import json
import os
from .Helper import get_similar_keys
from typing import List, Dict

# ---------------------------- #
# paths
dir_project: str = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
dir_user: str = os.path.join(dir_project, "user")
keys_path: str = os.path.join(dir_user, "keys.json")
if not os.path.exists(dir_user):
    os.makedirs(dir_user)


# Engines available
engineList = ["Google Translate", "MyMemoryTranslator", "Deepl", "PONS", "LibreTranslate", "None"]

# List of supported languages by Tesseract OCR
tesseract_lang = {
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
    "Chinese Simplified": "chi_sim",
    "Chinese Simplified (Vertical)": "chi_sim_vert",
    "Chinese Traditional": "chi_tra",
    "Chinese Traditional (Vertical)": "chi_tra_vert",
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
    "Japanese (Vertical)": "jpn_vert",
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

# List of supported languages by Google TL
google_lang = {
    "Auto": "auto",
    "Afrikaans": "af",
    "Amharic": "am",
    "Arabic": "ar",
    "Armenian": "hy",
    "Azerbaijani": "aze_cyrl",
    "Belarusian": "be",
    "Bengali": "bn",
    "Bosnian": "bs",
    "Bulgarian": "bg",
    "Catalan:Valencian": "cat",
    "Cebuano": "ceb",
    "Czech": "ces",
    "Chinese Simplified": "zh-CN",
    "Chinese Simplified (Vertical)": "zh-CN",
    "Chinese Traditional": "zh-TW",
    "Chinese Traditional (Vertical)": "zh-TW",
    "Corsican": "co",
    "Welsh": "cy",
    "Danish": "da",
    "German": "de",
    "Greek": "el",
    "English": "en",
    "Esperanto": "eo",
    "Estonian": "et",
    "Basque": "eu",
    "Persian": "fa",
    "Filipino": "tl",
    "Finnish": "fi",
    "French": "fr",
    "Irish": "ga",
    "Galician": "gl",
    "Gujarati": "gu",
    "Haitian": "ht",
    "Hebrew": "iw",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Icelandic": "is",
    "Italian": "it",
    "Javanese": "jw",
    "Japanese": "ja",
    "Japanese (Vertical)": "ja",
    "Kannada": "kn",
    "Georgian": "ka",
    "Kazakh": "kk",
    "Khmer": "km",
    "Korean": "ko",
    "Kurdish": "ku",
    "Lao": "lo",
    "Latin": "la",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Luxembourgish": "lb",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Macedonian": "mk",
    "Maltese": "mt",
    "Mongolian": "mn",
    "Maori": "mi",
    "Malay": "ms",
    "Burmese": "my",
    "Nepali": "ne",
    "Dutch": "nl",
    "Norwegian": "no",
    "Punjabi": "pa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Spanish": "es",
    "Albanian": "sq",
    "Serbian": "sr",
    "Sundanese": "su",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tamil": "ta",
    "Tatar": "tt",
    "Telugu": "te",
    "Tajik": "tg",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Uzbek": "uz",
    "Vietnamese": "vi",
    "Yiddish": "yi",
    "Yoruba": "yo",
}

# List of supported languages by MyMemoryTranslator
myMemory_lang = {
    "Auto": "auto",
    "Afrikaans": "af",
    "Albanian": "sq",
    "Amharic": "am",
    "Arabic": "ar",
    "Armenian": "hy",
    "Azerbaijani": "az",
    "Basque": "eu",
    "Belarusian": "be",
    "Bengali": "bn",
    "Bosnian": "bs",
    "Bulgarian": "bg",
    "Catalan:Valencian": "ca",
    "Cebuano": "ceb",
    "Chinese Simplified": "zh-CN",
    "Chinese Simplified (Vertical)": "zh-CN",
    "Chinese Traditional": "zh-TW",
    "Chinese Traditional (Vertical)": "zh-TW",
    "Corsican": "co",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Esperanto": "eo",
    "Estonian": "et",
    "Filipino": "fil",
    "Finnish": "fi",
    "French": "fr",
    "Galician": "gl",
    "Georgian": "ka",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Haitian": "ht",
    "Hausa": "ha",
    "Hawaiian": "haw",
    "Hebrew": "he",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Icelandic": "is",
    "Indonesian": "id",
    "Irish": "ga",
    "Italian": "it",
    "Japanese": "ja",
    "Japanese (Vertical)": "ja",
    "Javanese": "jw",
    "Kannada": "kn",
    "Kazakh": "kk",
    "Khmer": "km",
    "Korean": "ko",
    "Kurdish": "ku",
    "Lao": "lo",
    "Latin": "la",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Luxembourgish": "lb",
    "Macedonian": "mk",
    "Malay": "ms",
    "Malayalam": "ml",
    "Maltese": "mt",
    "Maori": "mi",
    "Marathi": "mr",
    "Mongolian": "mn",
    "Burmese": "my",
    "Nepali": "ne",
    "Norwegian": "no",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Samoan": "sm",
    "Serbian": "sr",
    "Spanish": "es",
    "Sundanese": "su",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tagalog": "tl",
    "Tajik": "tg",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Uzbek": "uz",
    "Vietnamese": "vi",
    "Welsh": "cy",
    "Xhosa": "xh",
    "Yiddish": "yi",
    "Yoruba": "yo",
}

# List of supported languages by Deepl
deepl_lang = {
    "Auto": "auto",
    "Bulgarian": "bg",
    "Chinese Simplified": "zh",
    "Chinese Simplified (Vertical)": "zh",
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
    "Japanese (Vertical)": "ja",
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

# List of supported languages by Pons
pons_lang = {
    "Arabic": "ar",
    "Bulgarian": "bg",
    "Chinese Simplified": "zh-cn",
    "Chinese Simplified (Vertical)": "zh-cn",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hungarian": "hu",
    "Italian": "it",
    "Latin": "la",
    "Norwegian": "no",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Turkish": "tr",
}

# List of supported languages by libretranslate
libre_lang = {
    "Auto": "auto",
    "English": "en",
    "Arabic": "ar",
    "Chinese Simplified": "zh",
    "Chinese Simplified (Vertical)": "zh",
    "Dutch": "nl",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Irish": "ga",
    "Italian": "it",
    "Japanese": "ja",
    "Japanese (Vertical)": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Vietnamese": "vi",
    "test": "a",
}

# ------------------ #
missingKey = False


def remove_auto_detect(lang_list: List) -> List:
    """Remove auto detect from the list"""
    for key in lang_list:
        if "auto" in key.lower():
            lang_list.remove(key)

    return lang_list


def verify_dict_data(keyList: List, keyDict: Dict, data: Dict):
    """Verify if the data is a dict"""
    global missingKey
    for key in keyList:
        if key not in data:
            data[key] = keyDict[key]
            missingKey = True

    return data


# if not yet created
if not os.path.exists(keys_path):
    key_save = {
        "tesseract_lang": tesseract_lang,
        "google_lang": google_lang,
        "myMemory_lang": myMemory_lang,
        "deepl_lang": deepl_lang,
        "pons_lang": pons_lang,
        "libre_lang": libre_lang,
    }

    with open(keys_path, "w") as f:
        json.dump(key_save, f, indent=4)

else:
    with open(keys_path, "r") as f:
        key_save = json.load(f)
        key_save = {
            "tesseract_lang": verify_dict_data(list(tesseract_lang.keys()), tesseract_lang, key_save["tesseract_lang"]),
            "google_lang": verify_dict_data(list(google_lang.keys()), google_lang, key_save["google_lang"]),
            "myMemory_lang": verify_dict_data(list(myMemory_lang.keys()), myMemory_lang, key_save["myMemory_lang"]),
            "deepl_lang": verify_dict_data(list(deepl_lang.keys()), deepl_lang, key_save["deepl_lang"]),
            "pons_lang": verify_dict_data(list(pons_lang.keys()), pons_lang, key_save["pons_lang"]),
            "libre_lang": verify_dict_data(list(libre_lang.keys()), libre_lang, key_save["libre_lang"]),
        }

        if missingKey:
            with open(keys_path, "w") as f:
                json.dump(key_save, f, indent=4)

        tesseract_lang = key_save["tesseract_lang"]
        google_lang = key_save["google_lang"]
        myMemory_lang = key_save["myMemory_lang"]
        deepl_lang = key_save["deepl_lang"]
        pons_lang = key_save["pons_lang"]
        libre_lang = key_save["libre_lang"]


# ------------------ #
# target
none_target = remove_auto_detect(list(tesseract_lang.keys()))
none_target.sort()

google_target = remove_auto_detect(list(google_lang.keys()))
google_target.sort()

myMemory_target = remove_auto_detect(list(myMemory_lang.keys()))
myMemory_target.sort()

deepl_target = remove_auto_detect(list(deepl_lang.keys()))
deepl_target.sort()

pons_target = remove_auto_detect(list(pons_lang.keys()))
pons_target.sort()

libre_target = remove_auto_detect(list(libre_lang.keys()))
libre_target.sort()

engine_select_target_dict = {
    "Google Translate": google_target,
    "MyMemoryTranslator": myMemory_target,
    "Deepl": deepl_target,
    "PONS": pons_target,
    "LibreTranslate": libre_target,
    "None": none_target,
}

# source
google_tesseract_compatible_source = list(google_lang.keys())
for lang in google_tesseract_compatible_source:
    if len(get_similar_keys(tesseract_lang, lang)) == 0:
        google_tesseract_compatible_source.remove(lang)
google_tesseract_compatible_source.sort()

myMemory_tesseract_compatible_source = list(myMemory_lang.keys())
for lang in myMemory_tesseract_compatible_source:
    if len(get_similar_keys(tesseract_lang, lang)) == 0:
        myMemory_tesseract_compatible_source.remove(lang)
myMemory_tesseract_compatible_source.sort()

deepl_tesseract_compatible_source = list(deepl_lang.keys())
for lang in deepl_tesseract_compatible_source:
    if len(get_similar_keys(tesseract_lang, lang)) == 0:
        deepl_tesseract_compatible_source.remove(lang)
deepl_tesseract_compatible_source.sort()

pons_tesseract_compatible_source = list(pons_lang.keys())
for lang in pons_tesseract_compatible_source:
    if len(get_similar_keys(tesseract_lang, lang)) == 0:
        pons_tesseract_compatible_source.remove(lang)
pons_tesseract_compatible_source.sort()

libre_tesseract_compatible_source = list(libre_lang.keys())
for lang in libre_tesseract_compatible_source:
    if len(get_similar_keys(tesseract_lang, lang)) == 0:
        libre_tesseract_compatible_source.remove(lang)
libre_tesseract_compatible_source.sort()


engine_select_source_dict = {
    "Google Translate": google_tesseract_compatible_source,
    "MyMemoryTranslator": myMemory_tesseract_compatible_source,
    "Deepl": deepl_tesseract_compatible_source,
    "PONS": pons_tesseract_compatible_source,
    "LibreTranslate": libre_tesseract_compatible_source,
    "None": none_target,  # no Auto
}
