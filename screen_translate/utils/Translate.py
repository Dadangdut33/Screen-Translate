import asyncio
from typing import Literal

from screen_translate.Logging import logger
from screen_translate.Globals import fJson, gClass
from screen_translate.components.MBox import Mbox
from screen_translate.utils.Translator import google_tl, memory_tl, libre_tl, deepl_tl, pons_tl


def translate(query: str, to_lang: str, from_lang: str, engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]):
    """Translate text

    Args:
    ---
        query (str): Text to translate
        to_lang (str): Language to translate to
        from_lang (str): Language to translate from
        engine (Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]): Engine to use
    """
    gClass.lb_start()

    # If source and destination are the same
    if (from_lang) == (to_lang):
        gClass.lb_stop()
        logger.warn("Error Language is the same as source! Please choose a different language")
        Mbox("Error: Language target is the same as source", "Language target is the same as source! Please choose a different language", 2, gClass.mw)
        return

    # If langto not set
    if to_lang == "Auto-Detect":
        gClass.lb_stop()
        logger.warn("Error: Invalid Language Selected! Must specify language destination")
        Mbox("Error: Invalid Language Selected", "Must specify language destination", 2, gClass.mw)
        return

    # If the text is empty
    if len(query.strip()) < 1:
        gClass.lb_stop()
        logger.warn("Error: No text entered! Please enter some text")
        # If show alert is true then show a message box alert, else dont show any popup
        if fJson.settingCache["show_no_text_alert"]:
            Mbox("Error: No text entered", "Please enter some text", 2, gClass.mw)
        return

    # --------------------------------
    # Deepl
    if engine == "Deepl":
        loop = asyncio.get_event_loop() # deepl run separately because it is async
        loop.run_until_complete(deeplTl(query, to_lang, from_lang))
        return

    # --------------------------------
    # Google Translate
    if engine == "Google Translate":
        oldMethod = False
        if "- Alt" in from_lang or "- Alt" in to_lang:
            oldMethod = True
        success, result = google_tl(query, to_lang, from_lang, oldMethod=oldMethod)
    # --------------------------------
    # MyMemoryTranslator
    elif engine == "MyMemoryTranslator":
        success, result = memory_tl(query, to_lang, from_lang)
    # --------------------------------
    # PONS
    elif engine == "PONS":
        success, result = pons_tl(query, to_lang, from_lang)
    # --------------------------------
    # LibreTranslate
    elif engine == "LibreTranslate":
        success, result = libre_tl(
            query, to_lang, from_lang, https=fJson.settingCache["libre_https"], host=fJson.settingCache["libre_host"], port=fJson.settingCache["libre_port"], apiKeys=fJson.settingCache["libre_api_key"]
        )

    fill_tb_save_history(success, to_lang, from_lang, query, str(result), engine)


async def deeplTl(query: str, to_lang: str, from_lang: str):
    """Translate using deepl"""
    isSuccess, translateResult = await deepl_tl(query, to_lang, from_lang)
    fill_tb_save_history(isSuccess, to_lang, from_lang, query, str(translateResult), "Deepl")


def fill_tb_save_history(isSuccess: bool, to_lang: str, from_lang: str, query: str, result: str, engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]):
    """Save the text to history"""
    if isSuccess:
        # Fill the textbox
        gClass.insert_mw_res(result)
        gClass.insert_ex_res(result)

        if fJson.settingCache["saveHistory"]:
            # Write to History
            new_data = {"from": from_lang, "to": to_lang, "query": query, "result": result, "engine": engine}
            fJson.writeAdd_History(new_data)
            logger.info("TL saved to history")

        gClass.lb_stop()
    else:
        gClass.lb_stop()
        logger.info("Fail to translate and save to history")
        Mbox("Error: Translation Failed", result, 2)
